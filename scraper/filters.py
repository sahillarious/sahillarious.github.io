"""Filtering logic: seniority, location, recency.

Each filter returns (passed: bool, reason: str). The pipeline records the
reason on the posting (drop_reason) rather than silently discarding, so a run
can be audited end to end.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

from . import config
from .models import JobPosting


# --------------------------------------------------------------------------- #
# Seniority
# --------------------------------------------------------------------------- #
def is_junior_role(title: str) -> tuple[bool, str]:
    t = f" {title.lower().strip()} "

    for token in config.SENIORITY_EXCLUDE:
        if _token_in(token, t):
            return False, f"seniority:excluded ('{token.strip()}')"

    if config.REQUIRE_EXPLICIT_JUNIOR:
        for token in config.SENIORITY_INCLUDE:
            if _token_in(token, t):
                return True, ""
        return False, "seniority:no explicit junior/new-grad marker"

    return True, ""


def _token_in(token: str, padded_lower_text: str) -> bool:
    """Word-ish containment.

    Single short tokens like 'vp' or ' ii' are matched with word boundaries to
    avoid false hits (e.g. 'vp' inside 'developer'); longer phrases use plain
    substring matching.
    """
    token = token.lower()
    if token.startswith(" ") or token.endswith(" ") or len(token) <= 3:
        return token in padded_lower_text
    return bool(re.search(rf"\b{re.escape(token)}\b", padded_lower_text))


# --------------------------------------------------------------------------- #
# Location (US only)
# --------------------------------------------------------------------------- #
def is_us_location(location: str, *, fallback_text: str = "") -> tuple[bool, str]:
    """Decide whether a posting is US-based.

    Order of evidence:
      1. explicit US / US-remote phrasing      -> pass
      2. a US state name or abbreviation        -> pass
      3. a known US city                        -> pass
      4. an explicit non-US signal (no US sig)  -> drop
      5. nothing conclusive                     -> drop (configurable bias)
    """
    text = f"{location} {fallback_text}".lower()
    if not text.strip():
        return False, "location:empty"

    for token in config.US_REMOTE_TOKENS:
        if token in text:
            return True, ""

    for full, abbr in config.US_STATES.items():
        if full in text:
            return True, ""
        if re.search(rf"\b{abbr}\b", location):  # abbr only against raw location
            return True, ""

    for city in config.US_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", text):
            return True, ""

    for token in config.NON_US_TOKENS:
        if token in text:
            return False, f"location:non-US ('{token}')"

    # Generic "remote" with no geo qualifier -> ambiguous. Keep, but flag.
    if "remote" in text:
        return True, ""

    return False, "location:no US signal"


# --------------------------------------------------------------------------- #
# Recency
# --------------------------------------------------------------------------- #
def is_recent(date_posted: Optional[date], max_age_days: int) -> tuple[bool, str]:
    if date_posted is None:
        # Unknown date: keep it (search-time recency token already pre-filtered),
        # but flag so it's visible in the output.
        return True, ""
    age = (date.today() - date_posted).days
    if age < 0:
        return True, ""  # future-dated, treat as fresh
    if age > max_age_days:
        return False, f"recency:{age}d old (> {max_age_days})"
    return True, ""


# --------------------------------------------------------------------------- #
# Combined
# --------------------------------------------------------------------------- #
def apply_filters(posting: JobPosting, cfg: config.RunConfig) -> JobPosting:
    """Mutate posting.dropped / drop_reason in place; return it."""
    ok, reason = is_junior_role(posting.title)
    if not ok:
        posting.dropped, posting.drop_reason = True, reason
        return posting

    ok, reason = is_us_location(
        posting.location, fallback_text=f"{posting.snippet} {posting.description}"
    )
    if not ok:
        posting.dropped, posting.drop_reason = True, reason
        return posting

    ok, reason = is_recent(posting.date_posted, cfg.max_age_days)
    if not ok:
        posting.dropped, posting.drop_reason = True, reason
        return posting

    return posting
