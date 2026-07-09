"""Enrich a JobPosting with description, location, posted-date, etc.

Strategy per platform (preferring official/public JSON over HTML scraping):

  greenhouse -> boards-api.greenhouse.io/v1/boards/<co>/jobs/<id>
  lever      -> api.lever.co/v0/postings/<co>/<id>
  ashby      -> api.ashbyhq.com/posting-api/job-board/<co> (board, matched by id)
  others     -> fetch HTML, read schema.org/JobPosting JSON-LD, else meta tags

All fetchers are best-effort: on any failure the posting keeps whatever it
already has (title/snippet from the SERP) and is flagged in metadata.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from datetime import date, datetime
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from . import config
from .models import JobPosting


_session = requests.Session()
_session.headers.update({"User-Agent": config.USER_AGENT})

# Cache Ashby boards so we hit the API once per company, not once per job.
_ashby_board_cache: dict[str, dict[str, Any]] = {}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _path_parts(url: str) -> list[str]:
    return [p for p in urllib.parse.urlparse(url).path.split("/") if p]


def _html_to_text(html: str, limit: int = 5000) -> str:
    if not html:
        return ""
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def _parse_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)):
            # epoch — Lever uses ms, schema.org uses seconds; normalize.
            ts = value / 1000 if value > 1e12 else value
            return datetime.utcfromtimestamp(ts).date()
        return dateparser.parse(str(value)).date()
    except (ValueError, OverflowError, TypeError):
        return None


def _get(url: str, **kw) -> Optional[requests.Response]:
    try:
        resp = _session.get(url, timeout=config.REQUEST_TIMEOUT, **kw)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        return None


# --------------------------------------------------------------------------- #
# Platform: Greenhouse
# --------------------------------------------------------------------------- #
def _enrich_greenhouse(job: JobPosting) -> None:
    parts = _path_parts(job.url)
    if "jobs" not in parts:
        return
    company = parts[0]
    job_id = parts[parts.index("jobs") + 1] if parts.index("jobs") + 1 < len(parts) else None
    if not job_id:
        return
    api = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"
    resp = _get(api)
    if not resp:
        return
    try:
        data = resp.json()
    except ValueError:
        return
    job.title = data.get("title") or job.title
    job.location = (data.get("location") or {}).get("name", "") or job.location
    job.description = _html_to_text(data.get("content", "")) or job.description
    job.date_posted = (
        _parse_date(data.get("first_published"))
        or _parse_date(data.get("updated_at"))
        or job.date_posted
    )
    job.metadata["gh_internal_job_id"] = data.get("internal_job_id", "")


# --------------------------------------------------------------------------- #
# Platform: Lever
# --------------------------------------------------------------------------- #
def _enrich_lever(job: JobPosting) -> None:
    parts = _path_parts(job.url)
    if len(parts) < 2:
        return
    company, posting_id = parts[0], parts[1]
    api = f"https://api.lever.co/v0/postings/{company}/{posting_id}"
    resp = _get(api)
    if not resp:
        return
    try:
        data = resp.json()
    except ValueError:
        return
    job.title = data.get("text") or job.title
    cats = data.get("categories", {}) or {}
    job.location = cats.get("location", "") or job.location
    job.employment_type = cats.get("commitment", "") or job.employment_type
    job.description = (
        _html_to_text(data.get("description", "")) or job.description
    )
    job.date_posted = _parse_date(data.get("createdAt")) or job.date_posted
    job.metadata["lever_team"] = cats.get("team", "")


# --------------------------------------------------------------------------- #
# Platform: Ashby
# --------------------------------------------------------------------------- #
def _enrich_ashby(job: JobPosting) -> None:
    parts = _path_parts(job.url)
    if not parts:
        return
    company = parts[0]
    job_id = parts[1] if len(parts) > 1 else None

    board = _ashby_board_cache.get(company)
    if board is None:
        api = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
        resp = _get(api, params={"includeCompensation": "false"})
        board = {}
        if resp:
            try:
                payload = resp.json()
                for posting in payload.get("jobs", []):
                    board[posting.get("id")] = posting
            except ValueError:
                pass
        _ashby_board_cache[company] = board

    posting = board.get(job_id) if job_id else None
    if not posting:
        return
    job.title = posting.get("title") or job.title
    job.location = posting.get("location", "") or job.location
    job.employment_type = posting.get("employmentType", "") or job.employment_type
    job.description = (
        _html_to_text(posting.get("descriptionHtml", "")) or job.description
    )
    job.date_posted = _parse_date(posting.get("publishedDate")) or job.date_posted


# --------------------------------------------------------------------------- #
# Platform: Workday (public "CXS" career-experience JSON API)
# --------------------------------------------------------------------------- #
_LOCALE_RE = re.compile(r"^[a-z]{2}([-_][A-Za-z]{2})?$")
_REL_DATE_RE = re.compile(r"posted\s+(\d+)\+?\s+days?\s+ago", re.IGNORECASE)


def _workday_cxs_url(url: str) -> Optional[str]:
    """Map a Workday posting URL to its CXS job endpoint.

    https://nvidia.wd5.myworkdayjobs.com/en-US/CareerSite/job/Loc/Title_JR1
      -> https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/CareerSite/job/Loc/Title_JR1
    """
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if "myworkdayjobs.com" not in host:
        return None
    tenant = host.split(".")[0]
    parts = [p for p in parsed.path.split("/") if p]
    if parts and _LOCALE_RE.match(parts[0]):  # strip leading locale segment
        parts = parts[1:]
    if len(parts) < 2 or "job" not in parts:
        return None
    site = parts[0]
    job_path = "/".join(parts[1:])  # starts at "job/..."
    return f"https://{host}/wday/cxs/{tenant}/{site}/{job_path}"


def parse_posted_on(text: str) -> Optional[date]:
    """Parse Workday's human 'Posted ...' strings into a date.

    Handles 'Posted Today', 'Posted Yesterday', 'Posted 5 Days Ago',
    'Posted 30+ Days Ago'. Returns None if nothing recognizable.
    """
    from datetime import timedelta

    posted = str(text or "").lower()
    if "today" in posted:
        return date.today()
    if "yesterday" in posted:
        return date.today() - timedelta(days=1)
    m = _REL_DATE_RE.search(posted)
    if m:
        return date.today() - timedelta(days=int(m.group(1)))
    return None


def _parse_workday_date(info: dict) -> Optional[date]:
    # Prefer the explicit ISO date; fall back to the "Posted N Days Ago" string.
    return _parse_date(info.get("startDate")) or parse_posted_on(info.get("postedOn"))


def _enrich_workday(job: JobPosting) -> None:
    cxs = _workday_cxs_url(job.url)
    if not cxs:
        return
    resp = _get(cxs, headers={"Accept": "application/json"})
    if not resp:
        return
    try:
        data = resp.json()
    except ValueError:
        return
    info = data.get("jobPostingInfo", {}) or {}
    job.title = info.get("title") or job.title
    job.location = info.get("location", "") or job.location
    job.employment_type = info.get("timeType", "") or job.employment_type
    job.description = _html_to_text(info.get("jobDescription", "")) or job.description
    job.date_posted = _parse_workday_date(info) or job.date_posted

    org = (data.get("hiringOrganization") or {}).get("name")
    if org:
        job.company = org
    if info.get("remoteType"):
        job.metadata["workday_remote_type"] = info["remoteType"]
    if info.get("jobReqId"):
        job.metadata["workday_req_id"] = info["jobReqId"]


# --------------------------------------------------------------------------- #
# Generic HTML (career sites, jobs.* subdomains)
# --------------------------------------------------------------------------- #
def _enrich_generic(job: JobPosting) -> None:
    resp = _get(job.url)
    if not resp:
        return
    soup = BeautifulSoup(resp.text, "lxml")

    ld = _find_jobposting_jsonld(soup)
    if ld:
        job.title = ld.get("title") or job.title
        job.description = _html_to_text(ld.get("description", "")) or job.description
        job.date_posted = _parse_date(ld.get("datePosted")) or job.date_posted
        job.employment_type = (
            _coerce_str(ld.get("employmentType")) or job.employment_type
        )
        job.location = _jsonld_location(ld) or job.location
        return

    # Fallback: meta description + visible text.
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if meta and meta.get("content"):
        job.description = job.description or meta["content"][:5000]
    if not job.title:
        h1 = soup.find("h1")
        if h1:
            job.title = h1.get_text(" ", strip=True)


def _find_jobposting_jsonld(soup) -> Optional[dict]:
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        for node in _iter_jsonld_nodes(data):
            if isinstance(node, dict) and "JobPosting" in str(node.get("@type", "")):
                return node
    return None


def _iter_jsonld_nodes(data):
    if isinstance(data, list):
        for item in data:
            yield from _iter_jsonld_nodes(item)
    elif isinstance(data, dict):
        yield data
        if "@graph" in data:
            yield from _iter_jsonld_nodes(data["@graph"])


def _jsonld_location(ld: dict) -> str:
    loc = ld.get("jobLocation")
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    if isinstance(loc, dict):
        addr = loc.get("address", {})
        if isinstance(addr, dict):
            bits = [
                addr.get("addressLocality"),
                addr.get("addressRegion"),
                addr.get("addressCountry"),
            ]
            return ", ".join(b for b in bits if b)
    if ld.get("applicantLocationRequirements"):
        req = ld["applicantLocationRequirements"]
        if isinstance(req, dict):
            return req.get("name", "")
    return ""


def _coerce_str(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value) if value else ""


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
_ENRICHERS = {
    "greenhouse": _enrich_greenhouse,
    "lever": _enrich_lever,
    "ashby": _enrich_ashby,
    "workday": _enrich_workday,
}


def enrich(job: JobPosting) -> JobPosting:
    handler = _ENRICHERS.get(job.platform, _enrich_generic)
    try:
        handler(job)
    except Exception as exc:  # never let one bad page kill the run
        job.metadata["enrich_error"] = f"{type(exc).__name__}: {exc}"
    finally:
        time.sleep(config.REQUEST_DELAY)
    return job
