"""Turn raw SearchResults into JobPosting objects.

Responsibilities:
  * attribute a result URL to a known platform
  * extract the company slug from the URL (greenhouse/lever/ashby have it in
    the path; career sites fall back to the registered domain)
  * derive an initial title from the SERP title (later refined on enrichment)
  * discard obvious non-posting URLs (board landing pages, login, etc.)
"""
from __future__ import annotations

import re
import urllib.parse
from typing import Optional

from . import config
from .models import JobPosting
from .search import SearchResult


# URLs that are clearly not an individual posting.
_NON_POSTING_PATTERNS = re.compile(
    r"(/login|/sign[_-]?in|/privacy|/terms|/about|\.pdf$|/search\b|"
    r"/jobs/?$|/careers/?$|/job-board/?$)",
    re.IGNORECASE,
)


def detect_platform(url: str) -> Optional[str]:
    host = urllib.parse.urlparse(url).netloc.lower()
    path = urllib.parse.urlparse(url).path.lower()
    for platform in config.PLATFORMS:
        for token in platform.host_match:
            if token.endswith(".") and token in host:  # subdomain marker e.g. "jobs."
                return platform.name
            if token.startswith("/") and token in path:  # path marker e.g. "/careers/"
                return platform.name
            if token in host:
                return platform.name
    return None


def extract_company(url: str, platform: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    parts = [p for p in parsed.path.split("/") if p]

    if platform == "greenhouse":
        # boards.greenhouse.io/<company>/jobs/<id>
        # job-boards.greenhouse.io/<company>/jobs/<id>
        return _slug_to_name(parts[0]) if parts else ""
    if platform == "lever":
        # jobs.lever.co/<company>/<id>
        return _slug_to_name(parts[0]) if parts else ""
    if platform == "ashby":
        # jobs.ashbyhq.com/<company>/<id>
        return _slug_to_name(parts[0]) if parts else ""
    if platform == "workday":
        # <tenant>.wd<N>.myworkdayjobs.com/...  (enrichment refines this from
        # the API's hiringOrganization name)
        return _slug_to_name(host.split(".")[0])
    if platform == "jobs-subdomain":
        # jobs.<company>.com/...  -> take the registrable bit
        labels = host.split(".")
        if len(labels) >= 3 and labels[0] == "jobs":
            return _slug_to_name(labels[1])
        return _slug_to_name(labels[0])
    # careers / generic: use the registrable domain (drop www / careers prefix)
    labels = [l for l in host.split(".") if l not in ("www", "careers", "career")]
    if len(labels) >= 2:
        return _slug_to_name(labels[-2])
    return _slug_to_name(host)


def _slug_to_name(slug: str) -> str:
    slug = re.sub(r"[-_]+", " ", slug).strip()
    return slug.title()


def is_probable_posting(url: str) -> bool:
    if _NON_POSTING_PATTERNS.search(url):
        return False
    path = urllib.parse.urlparse(url).path.strip("/")
    # An individual posting almost always has at least one path segment.
    return bool(path)


def clean_title(raw_title: str) -> str:
    """Strip the company / board suffix Google appends to result titles.

    e.g. "AI Engineer - Acme Inc - Greenhouse" -> "AI Engineer"
    """
    title = raw_title.strip()
    for sep in (" - ", " — ", " | ", " · ", " at "):
        if sep in title:
            title = title.split(sep)[0].strip()
            break
    return title


def to_posting(result: SearchResult) -> Optional[JobPosting]:
    platform = detect_platform(result.url)
    if platform is None:
        return None
    if not is_probable_posting(result.url):
        return None
    company = extract_company(result.url, platform)
    return JobPosting(
        url=result.url.split("?")[0],  # drop tracking query params
        title=clean_title(result.title),
        platform=platform,
        company=company,
        snippet=result.snippet,
        source_query=result.query,
        metadata={"raw_title": result.title},
    )
