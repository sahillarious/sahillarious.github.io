"""Central configuration for the job-scraping pipeline.

Everything tunable lives here so the rest of the code stays declarative.
Override secrets / runtime knobs via environment variables (.env supported).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    from dotenv import load_dotenv

    # Load .env from the current working directory AND from next to this
    # package, so a key works whether you put .env in the repo root or in
    # scraper/ (next to .env.example). cwd wins on conflicts.
    _pkg_env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_pkg_env):
        load_dotenv(_pkg_env)
    load_dotenv()  # cwd / nearest .env (override=False, so cwd does not clobber)
except ImportError:  # dotenv is optional
    pass


# --------------------------------------------------------------------------- #
# Roles we search for. Each becomes a quoted phrase in the Google query.
# --------------------------------------------------------------------------- #
ROLES: list[str] = [
    "AI Engineer",
    "Machine Learning Engineer",
    "Forward Deployed Engineer",
]


# --------------------------------------------------------------------------- #
# Platforms / site: operators we discover postings through.
#   - `name`        : canonical platform label stored on each posting
#   - `site_filter` : the raw `site:` clause injected into the Google query
#   - `host_match`  : substrings used to attribute a result URL to this platform
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Platform:
    name: str
    site_filter: str
    host_match: tuple[str, ...]


PLATFORMS: list[Platform] = [
    Platform("greenhouse", "site:greenhouse.io", ("greenhouse.io",)),
    Platform("ashby", "site:ashbyhq.com", ("ashbyhq.com",)),
    Platform("lever", "site:lever.co", ("lever.co",)),
    Platform("workday", "site:myworkdayjobs.com", ("myworkdayjobs.com",)),
    Platform("jobs-subdomain", "site:jobs.*", ("jobs.",)),
    Platform(
        "careers",
        "(site:careers.* OR site:*/careers/* OR site:*/career/*)",
        ("careers.", "/careers/", "/career/"),
    ),
]


# --------------------------------------------------------------------------- #
# Query construction
# --------------------------------------------------------------------------- #
# Extra keyword appended to every query (the user's examples all use "remote").
QUERY_SUFFIX: str = "remote"

# Google `tbs=qdr:` recency token used at search time to pre-narrow results.
#   h48 = last 48h, d = last 24h, w = last week, m = last month.
# We deliberately cast a slightly wider net here (w) and let the date filter
# enforce the strict "< MAX_AGE_DAYS" rule after enrichment.
SEARCH_RECENCY: str = os.getenv("SEARCH_RECENCY", "w")

# How many result pages to pull per (role, platform) query.
PAGES_PER_QUERY: int = int(os.getenv("PAGES_PER_QUERY", "2"))
RESULTS_PER_PAGE: int = 10


# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #
# Max posting age in days (jobs older than this are dropped).
MAX_AGE_DAYS: int = int(os.getenv("MAX_AGE_DAYS", "3"))

# Title tokens that mark a role as too senior -> dropped.
SENIORITY_EXCLUDE: tuple[str, ...] = (
    "senior", "sr.", "sr ", "staff", "principal", "lead", "manager",
    "director", "head of", "vp", "vice president", "president",
    "architect", "distinguished", "fellow",
    " ii", " iii", " iv", " v ", "level 3", "l3", "l4", "l5", "l6",
)

# Title tokens that *positively* mark junior / new-grad (optional boost,
# not strictly required — see filters.is_junior_role).
SENIORITY_INCLUDE: tuple[str, ...] = (
    "junior", "jr.", "jr ", "new grad", "new-grad", "newgrad", "grad",
    "entry", "entry-level", "entry level", "associate", "early career",
    "early-career", "university", "campus", "intern",  # keep intern? see note
    " i ", "level 1", "l1",
)

# If True, a role must contain an explicit junior/new-grad token to pass.
# If False, anything that is NOT senior passes (more recall, less precision).
REQUIRE_EXPLICIT_JUNIOR: bool = (
    os.getenv("REQUIRE_EXPLICIT_JUNIOR", "false").lower() == "true"
)

# Location filter: keep only US / US-state / US-city / US-remote postings.
# Strings here are matched case-insensitively against the posting location.
US_REMOTE_TOKENS: tuple[str, ...] = (
    "united states", "u.s.", "u.s.a", "usa", "us only", "us-based",
    "remote (us", "remote - us", "remote, us", "remote us", "us remote",
)

# US state names + 2-letter abbreviations (abbreviations matched as whole words).
US_STATES: dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC", "washington dc": "DC", "washington d.c.": "DC",
}

# Major US cities (helps when a posting lists only a city).
US_CITIES: tuple[str, ...] = (
    "new york", "san francisco", "los angeles", "chicago", "boston",
    "seattle", "austin", "denver", "atlanta", "dallas", "houston",
    "san jose", "san diego", "washington", "philadelphia", "phoenix",
    "miami", "portland", "minneapolis", "pittsburgh", "nashville",
    "raleigh", "charlotte", "salt lake city", "palo alto", "mountain view",
    "menlo park", "sunnyvale", "santa clara", "brooklyn", "cambridge",
    "bellevue", "redmond", "irvine", "san mateo", "oakland",
)

# Non-US signals -> if present (and no US signal) the posting is dropped.
NON_US_TOKENS: tuple[str, ...] = (
    "united kingdom", "uk only", "london", "berlin", "paris", "amsterdam",
    "dublin", "toronto", "vancouver", "canada", "bangalore", "india",
    "singapore", "australia", "sydney", "germany", "france", "spain",
    "remote (emea", "remote - emea", "emea", "apac", "latam",
    "tel aviv", "israel", "munich", "barcelona", "warsaw", "lisbon",
)


# --------------------------------------------------------------------------- #
# Networking / politeness
# --------------------------------------------------------------------------- #
USER_AGENT: str = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
# Seconds to sleep between outbound requests (be a good citizen / avoid blocks).
REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "2.0"))
MAX_ENRICH_WORKERS: int = int(os.getenv("MAX_ENRICH_WORKERS", "4"))


# --------------------------------------------------------------------------- #
# Search backend
# --------------------------------------------------------------------------- #
# "serper" (recommended, reliable, needs SERPER_API_KEY) or "google_html"
# (free, scrapes google.com directly, fragile / gets rate-limited).
SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "auto")
SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")


# --------------------------------------------------------------------------- #
# Discovery sources
# --------------------------------------------------------------------------- #
# Which discovery front-ends to run. Comma-separated: "google", "workday".
#   google  -> Google (via Serper) across all PLATFORMS site: filters
#   workday -> query each company's Workday board CXS API directly (keyless,
#              far better Workday coverage than Google indexes)
SOURCES: list[str] = [
    s.strip() for s in os.getenv("SOURCES", "google").split(",") if s.strip()
]

# File listing Workday boards to search (one board URL per line; # = comment).
WORKDAY_BOARDS_FILE: str = os.getenv(
    "WORKDAY_BOARDS_FILE",
    os.path.join(os.path.dirname(__file__), "data", "workday_boards.txt"),
)
# Max postings to pull per (board x role) before moving on.
WORKDAY_MAX_RESULTS_PER_BOARD: int = int(
    os.getenv("WORKDAY_MAX_RESULTS_PER_BOARD", "40")
)


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
JSON_FILENAME: str = "jobs.json"
EXCEL_FILENAME: str = "jobs.xlsx"
DROPPED_JSON_FILENAME: str = "jobs_dropped.json"
DROPPED_EXCEL_FILENAME: str = "jobs_dropped.xlsx"


@dataclass
class RunConfig:
    """A snapshot of all knobs for a single pipeline run (easy to override)."""

    roles: list[str] = field(default_factory=lambda: list(ROLES))
    platforms: list[Platform] = field(default_factory=lambda: list(PLATFORMS))
    sources: list[str] = field(default_factory=lambda: list(SOURCES))
    max_age_days: int = MAX_AGE_DAYS
    pages_per_query: int = PAGES_PER_QUERY
    require_explicit_junior: bool = REQUIRE_EXPLICIT_JUNIOR
    search_recency: str = SEARCH_RECENCY
    output_dir: str = OUTPUT_DIR
