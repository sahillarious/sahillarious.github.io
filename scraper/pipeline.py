"""Orchestrates the full pipeline: discover -> dedup -> enrich -> filter -> sort.

    discover : gather candidate postings from the enabled sources
               - google  : run every (role x platform) Google query
               - workday : query each Workday board's CXS API directly
    dedup    : collapse by canonical URL
    enrich   : fetch description / location / posted-date
    filter   : seniority + location + recency (records drop_reason)
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from . import config, filters, workday
from .enrich import enrich
from .models import JobPosting
from .parser import to_posting
from .search import build_query, get_provider


@dataclass
class RunResult:
    kept: list[JobPosting] = field(default_factory=list)
    dropped: list[JobPosting] = field(default_factory=list)
    total_seen: int = 0

    @property
    def summary(self) -> str:
        lines = [
            f"  raw results seen : {self.total_seen}",
            f"  kept             : {len(self.kept)}",
            f"  dropped          : {len(self.dropped)}",
        ]
        reasons: dict[str, int] = {}
        for job in self.dropped:
            key = job.drop_reason.split(" (")[0].split(":")[0] if job.drop_reason else "other"
            reasons[key] = reasons.get(key, 0) + 1
        for reason, n in sorted(reasons.items(), key=lambda x: -x[1]):
            lines.append(f"      - {reason}: {n}")
        return "\n".join(lines)


def _discover_google(cfg, provider, result, seen_ids, postings) -> None:
    for role in cfg.roles:
        for platform in cfg.platforms:
            query = build_query(role, platform.site_filter)
            print(f"[google] {query}")
            for sr in provider.search(query, cfg.pages_per_query):
                result.total_seen += 1
                job = to_posting(sr)
                if job is None or job.id in seen_ids:
                    continue
                seen_ids.add(job.id)
                postings.append(job)


def _discover_workday(cfg, result, seen_ids, postings) -> None:
    print("[workday] searching boards directly via CXS API...")
    for job in workday.discover(cfg.roles):
        result.total_seen += 1
        if job.id in seen_ids:
            continue
        seen_ids.add(job.id)
        postings.append(job)


def run(cfg: config.RunConfig | None = None, *, provider=None) -> RunResult:
    cfg = cfg or config.RunConfig()
    result = RunResult()

    # ----- discover (one or more sources) + dedup ------------------------- #
    seen_ids: set[str] = set()
    postings: list[JobPosting] = []

    if "google" in cfg.sources:
        provider = provider or get_provider()
        _discover_google(cfg, provider, result, seen_ids, postings)
    if "workday" in cfg.sources:
        _discover_workday(cfg, result, seen_ids, postings)

    print(f"\n[parse] {len(postings)} unique candidate postings")

    # ----- pre-filter on title (seniority) -------------------------------- #
    # The title is final at discovery time, so drop obvious senior/lead/staff
    # roles now and avoid spending an enrichment request on each.
    to_enrich: list[JobPosting] = []
    for job in postings:
        ok, reason = filters.is_junior_role(job.title)
        if not ok:
            job.dropped, job.drop_reason = True, reason
            result.dropped.append(job)
        else:
            to_enrich.append(job)
    print(f"[pre-filter] {len(to_enrich)} pass seniority "
          f"({len(postings) - len(to_enrich)} senior roles skipped before enrich)")

    # ----- enrich (concurrent, bounded) ----------------------------------- #
    print(f"[enrich] fetching details ({config.MAX_ENRICH_WORKERS} workers)...")
    with ThreadPoolExecutor(max_workers=config.MAX_ENRICH_WORKERS) as pool:
        enriched = list(pool.map(enrich, to_enrich))

    # ----- full filter (location + recency + seniority re-check) ---------- #
    for job in enriched:
        filters.apply_filters(job, cfg)
        if job.dropped:
            result.dropped.append(job)
        else:
            result.kept.append(job)

    # Sort kept: most recent first, then company.
    result.kept.sort(
        key=lambda j: (j.date_posted or __import__("datetime").date.min, j.company),
        reverse=True,
    )
    return result
