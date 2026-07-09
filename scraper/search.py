"""Search backends that turn a Google query string into result URLs.

Two providers are shipped:

  SerperProvider     -> calls https://serper.dev (Google SERP API). Reliable,
                        respects `tbs`, needs SERPER_API_KEY. Recommended.

  GoogleHTMLProvider -> scrapes https://www.google.com/search directly with
                        requests + BeautifulSoup. Free, but Google aggressively
                        rate-limits / CAPTCHAs automated traffic, so treat this
                        as best-effort / dev-only.

`get_provider()` auto-selects: Serper if a key is configured, else HTML.
Each provider yields lightweight `SearchResult`s; mapping them to platforms /
companies happens later in parser.py.
"""
from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

import requests

from . import config


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str = ""
    query: str = ""


def build_query(role: str, site_filter: str) -> str:
    """Compose the raw Google query string for one (role, platform)."""
    parts = [f'"{role}"', site_filter]
    if config.QUERY_SUFFIX:
        parts.append(config.QUERY_SUFFIX)
    return " ".join(parts)


class SearchProvider:
    def search(self, query: str, pages: int) -> Iterator[SearchResult]:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Serper.dev (recommended)
# --------------------------------------------------------------------------- #
class SerperProvider(SearchProvider):
    ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {"X-API-KEY": api_key, "Content-Type": "application/json"}
        )

    def search(self, query: str, pages: int) -> Iterator[SearchResult]:
        for page in range(1, pages + 1):
            payload = {
                "q": query,
                "num": config.RESULTS_PER_PAGE,
                "page": page,
                "gl": "us",
                "hl": "en",
            }
            if config.SEARCH_RECENCY:
                payload["tbs"] = f"qdr:{config.SEARCH_RECENCY}"
            try:
                resp = self.session.post(
                    self.ENDPOINT, json=payload, timeout=config.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
                data = resp.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"  [serper] query failed (page {page}): {exc}")
                return
            organic = data.get("organic", [])
            if not organic:
                return
            for item in organic:
                link = item.get("link")
                if not link:
                    continue
                yield SearchResult(
                    url=link,
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    query=query,
                )
            time.sleep(config.REQUEST_DELAY)


# --------------------------------------------------------------------------- #
# Direct Google HTML scrape (fallback / dev-only)
# --------------------------------------------------------------------------- #
class GoogleHTMLProvider(SearchProvider):
    ENDPOINT = "https://www.google.com/search"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": config.USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def search(self, query: str, pages: int) -> Iterator[SearchResult]:
        from bs4 import BeautifulSoup  # local import keeps bs4 optional for serper

        for page in range(pages):
            params = {
                "q": query,
                "num": config.RESULTS_PER_PAGE,
                "start": page * config.RESULTS_PER_PAGE,
                "hl": "en",
                "gl": "us",
            }
            if config.SEARCH_RECENCY:
                params["tbs"] = f"qdr:{config.SEARCH_RECENCY}"
            try:
                resp = self.session.get(
                    self.ENDPOINT, params=params, timeout=config.REQUEST_TIMEOUT
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(f"  [google_html] request failed (page {page}): {exc}")
                return

            if "did not match any documents" in resp.text:
                return
            if _looks_blocked(resp.text):
                print(
                    "  [google_html] Google returned a CAPTCHA / block page. "
                    "Switch to SERPER_API_KEY for reliable results."
                )
                return

            soup = BeautifulSoup(resp.text, "lxml")
            found = False
            for result in _parse_google_html(soup):
                found = True
                result.query = query
                yield result
            if not found:
                return
            time.sleep(config.REQUEST_DELAY)


def _looks_blocked(html: str) -> bool:
    markers = ("Our systems have detected unusual traffic", "g-recaptcha", "/sorry/")
    return any(m in html for m in markers)


def _parse_google_html(soup) -> Iterable[SearchResult]:
    """Extract organic results from a Google SERP page.

    Google's markup is unstable; we look for anchors wrapping an <h3> and
    unwrap the `/url?q=` redirect Google sometimes uses.
    """
    seen: set[str] = set()
    for a in soup.select("a:has(h3)"):
        href = a.get("href", "")
        url = _clean_google_href(href)
        if not url or url in seen:
            continue
        if not url.startswith("http"):
            continue
        seen.add(url)
        h3 = a.find("h3")
        title = h3.get_text(" ", strip=True) if h3 else ""
        # Snippet: nearest following text block (best-effort).
        snippet = ""
        container = a.find_parent("div")
        if container:
            snippet = container.get_text(" ", strip=True)[:300]
        yield SearchResult(url=url, title=title, snippet=snippet)


def _clean_google_href(href: str) -> str:
    if href.startswith("/url?"):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        return qs.get("q", [""])[0]
    if href.startswith("http"):
        return href
    return ""


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def get_provider(name: Optional[str] = None) -> SearchProvider:
    name = (name or config.SEARCH_PROVIDER or "auto").lower()

    if name in ("auto", "serper") and config.SERPER_API_KEY:
        return SerperProvider(config.SERPER_API_KEY)

    if name == "serper" and not config.SERPER_API_KEY:
        raise RuntimeError(
            "SEARCH_PROVIDER=serper but SERPER_API_KEY is not set. "
            "Get a free key at https://serper.dev or use google_html."
        )

    if name == "auto":
        print(
            "  [search] No SERPER_API_KEY found -> falling back to direct "
            "Google HTML scraping (fragile). Set SERPER_API_KEY for reliability."
        )
    return GoogleHTMLProvider()
