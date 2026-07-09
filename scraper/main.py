"""CLI entry point.

    python -m scraper.main                      # full run, default settings
    python -m scraper.main --source workday     # Workday boards only (keyless)
    python -m scraper.main --source both        # Google + Workday
    python -m scraper.main --roles "AI Engineer" "ML Engineer"
    python -m scraper.main --platforms greenhouse lever
    python -m scraper.main --max-age-days 3 --pages 2 --require-junior
    python -m scraper.main --provider serper    # force a search backend
    python -m scraper.main --dry-run            # discover only, no enrich/save
    python -m scraper.main --check-workday      # validate configured Workday boards
"""
from __future__ import annotations

import argparse
import sys

from . import config, workday
from .pipeline import run
from .search import get_provider
from .storage import save_all, save_dropped

_SOURCE_MAP = {"google": ["google"], "workday": ["workday"], "both": ["google", "workday"]}


def _build_run_config(args) -> config.RunConfig:
    cfg = config.RunConfig()
    if args.source:
        cfg.sources = _SOURCE_MAP[args.source]
    if args.roles:
        cfg.roles = args.roles
    if args.platforms:
        wanted = {p.lower() for p in args.platforms}
        cfg.platforms = [p for p in config.PLATFORMS if p.name in wanted]
        if not cfg.platforms:
            sys.exit(
                f"No platforms matched {sorted(wanted)}. "
                f"Available: {[p.name for p in config.PLATFORMS]}"
            )
    if args.max_age_days is not None:
        cfg.max_age_days = args.max_age_days
    if args.pages is not None:
        cfg.pages_per_query = args.pages
    if args.require_junior:
        cfg.require_explicit_junior = True
    if args.output_dir:
        cfg.output_dir = args.output_dir
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Job posting scraper pipeline")
    parser.add_argument(
        "--source", choices=["google", "workday", "both"], default=None,
        help="Discovery source(s). Default: from SOURCES env / config (google)",
    )
    parser.add_argument("--roles", nargs="+", help="Role phrases to search for")
    parser.add_argument(
        "--platforms", nargs="+",
        help=f"(google source) subset of: {[p.name for p in config.PLATFORMS]}",
    )
    parser.add_argument("--max-age-days", type=int, help="Max posting age (days)")
    parser.add_argument("--pages", type=int, help="(google) result pages per query")
    parser.add_argument(
        "--require-junior", action="store_true",
        help="Require an explicit junior/new-grad marker in the title",
    )
    parser.add_argument(
        "--provider", choices=["auto", "serper", "google_html"], default=None,
        help="Google search backend (default: auto)",
    )
    parser.add_argument("--output-dir", help="Where to write jobs.json / jobs.xlsx")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Discover only; skip enrichment and file output",
    )
    parser.add_argument(
        "--no-dropped", action="store_true",
        help="Don't write the filtered-out postings audit file",
    )
    parser.add_argument(
        "--check-workday", action="store_true",
        help="Validate the configured Workday boards and exit",
    )
    args = parser.parse_args(argv)

    if args.check_workday:
        workday.check_boards()
        return 0

    cfg = _build_run_config(args)
    provider = get_provider(args.provider) if "google" in cfg.sources else None

    print("=" * 64)
    print("Job scraper pipeline")
    print(f"  sources   : {cfg.sources}")
    print(f"  roles     : {cfg.roles}")
    if "google" in cfg.sources:
        print(f"  platforms : {[p.name for p in cfg.platforms]}")
        print(f"  provider  : {type(provider).__name__} | pages/query: {cfg.pages_per_query}")
    if "workday" in cfg.sources:
        print(f"  wd boards : {len(workday.load_boards())} configured")
    print(f"  max age   : {cfg.max_age_days}d")
    print("=" * 64)

    if args.dry_run:
        candidates = []
        if "workday" in cfg.sources:
            candidates += workday.discover(cfg.roles)
        if "google" in cfg.sources:
            from .search import build_query
            from .parser import to_posting

            for role in cfg.roles:
                for platform in cfg.platforms:
                    q = build_query(role, platform.site_filter)
                    print(f"[dry-run] {q}")
                    for sr in provider.search(q, cfg.pages_per_query):
                        job = to_posting(sr)
                        if job:
                            candidates.append(job)
        for job in candidates:
            print(f"   {job.platform:12} {job.company:22} {job.title[:50]:50} {job.location}")
        print(f"\n[dry-run] {len(candidates)} candidate postings (no enrich, no save)")
        return 0

    result = run(cfg, provider=provider)

    print("\n" + "-" * 64)
    print("Results")
    print(result.summary)

    if result.kept:
        json_path, xlsx_path = save_all(result.kept, cfg.output_dir)
        print(f"\n  saved kept JSON : {json_path}")
        print(f"  saved kept XLSX : {xlsx_path}")
    else:
        print("\n  No postings passed the filters — no kept files written.")

    if result.dropped and not args.no_dropped:
        d_json, d_xlsx = save_dropped(result.dropped, cfg.output_dir)
        print(f"  saved dropped   : {d_json}")
        print(f"  saved dropped   : {d_xlsx}  (drop_reason in column A)")
    print("-" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
