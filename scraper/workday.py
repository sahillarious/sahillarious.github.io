"""Direct Workday discovery via the public CXS API.

Google barely indexes Workday, so instead of `site:myworkdayjobs.com` we query
each company's Workday board directly. Every Workday board exposes an unauth'd
JSON search endpoint:

    POST https://<host>/wday/cxs/<tenant>/<site>/jobs
    body: {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "<role>"}

...which returns *all* matching postings on that board (not just what Google
crawled). We turn each result into a JobPosting; the rest of the pipeline
(enrich -> filter -> save) is shared with the Google source.
"""
from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass
from typing import Iterator, Optional

import requests

from . import config
from .enrich import parse_posted_on
from .models import JobPosting

_LOCALE_SEG = ("en-us", "en_us", "en", "en-gb", "en_gb")

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": config.USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
)


@dataclass(frozen=True)
class WorkdayBoard:
    host: str      # nvidia.wd5.myworkdayjobs.com
    tenant: str    # nvidia
    site: str      # NVIDIAExternalCareerSite

    @classmethod
    def from_url(cls, url: str) -> Optional["WorkdayBoard"]:
        url = url.strip()
        if not url or "myworkdayjobs.com" not in url:
            return None
        if "://" not in url:
            url = "https://" + url
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        tenant = host.split(".")[0]
        parts = [p for p in parsed.path.split("/") if p]
        if parts and parts[0].lower() in _LOCALE_SEG:
            parts = parts[1:]
        if not parts:
            return None
        return cls(host=host, tenant=tenant, site=parts[0])

    @property
    def cxs_jobs_url(self) -> str:
        return f"https://{self.host}/wday/cxs/{self.tenant}/{self.site}/jobs"

    def public_url(self, external_path: str) -> str:
        # externalPath looks like "/job/<loc>/<title>_<id>"
        return f"https://{self.host}/en-US/{self.site}{external_path}"


def load_boards(path: str = config.WORKDAY_BOARDS_FILE) -> list[WorkdayBoard]:
    boards: list[WorkdayBoard] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                board = WorkdayBoard.from_url(line)
                if board:
                    boards.append(board)
    except FileNotFoundError:
        print(f"  [workday] boards file not found: {path}")
    return boards


def _search_board(
    board: WorkdayBoard, role: str, max_results: int
) -> Iterator[JobPosting]:
    offset, page_size = 0, 20
    while offset < max_results:
        payload = {
            "appliedFacets": {},
            "limit": min(page_size, max_results - offset),
            "offset": offset,
            "searchText": role,
        }
        try:
            resp = _session.post(
                board.cxs_jobs_url, json=payload, timeout=config.REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"  [workday] {board.tenant}/{board.site} failed: {exc}")
            return

        postings = data.get("jobPostings", [])
        if not postings:
            return

        for item in postings:
            ext = item.get("externalPath")
            if not ext:
                continue
            yield JobPosting(
                url=board.public_url(ext),
                title=item.get("title", ""),
                platform="workday",
                company=_slug(board.tenant),
                location=item.get("locationsText", ""),
                date_posted=parse_posted_on(item.get("postedOn", "")),
                snippet=item.get("locationsText", ""),
                source_query=f"workday:{board.tenant} :: {role}",
                metadata={"workday_board": f"{board.tenant}/{board.site}"},
            )

        total = data.get("total", 0)
        offset += page_size
        if offset >= total:
            return
        time.sleep(config.REQUEST_DELAY)


def discover(
    roles: list[str],
    boards: Optional[list[WorkdayBoard]] = None,
    max_results_per_board: int = config.WORKDAY_MAX_RESULTS_PER_BOARD,
) -> list[JobPosting]:
    """Search every (board x role) and return de-duped candidate postings.

    Location/date come from the listing; the shared enrich stage later fills in
    the full description and refines fields via the per-job CXS endpoint.
    """
    boards = boards if boards is not None else load_boards()
    if not boards:
        print("  [workday] no boards configured -> nothing to search")
        return []

    seen: set[str] = set()
    out: list[JobPosting] = []
    for board in boards:
        board_count = 0
        for role in roles:
            for job in _search_board(board, role, max_results_per_board):
                if job.id in seen:
                    continue
                seen.add(job.id)
                out.append(job)
                board_count += 1
        print(f"  [workday] {board.tenant}/{board.site}: {board_count} candidates")
    return out


def check_boards(path: str = config.WORKDAY_BOARDS_FILE) -> None:
    """Validate each configured board hits a live CXS endpoint."""
    boards = load_boards(path)
    if not boards:
        print("No boards configured.")
        return
    print(f"Checking {len(boards)} Workday board(s) in {path}\n")
    for board in boards:
        try:
            resp = _session.post(
                board.cxs_jobs_url,
                json={"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""},
                timeout=config.REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                total = resp.json().get("total", "?")
                print(f"  OK    {board.tenant}/{board.site}  ({total} total jobs)")
            else:
                print(
                    f"  FAIL  {board.tenant}/{board.site}  HTTP {resp.status_code} "
                    f"(check tenant / wd cluster / site name)"
                )
        except requests.RequestException as exc:
            print(f"  ERR   {board.tenant}/{board.site}  {exc}")


def _slug(text: str) -> str:
    return text.replace("-", " ").replace("_", " ").title()
