"""Offline sanity check for parser + filters (no network calls).

Run:  python -m scraper.selftest
Exits non-zero if any assertion fails.
"""
from __future__ import annotations

from datetime import date, timedelta

from . import config
from .filters import is_junior_role, is_recent, is_us_location
from .models import JobPosting
from .parser import detect_platform, extract_company, to_posting
from .search import SearchResult


def _check(name: str, got, want) -> bool:
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")
    return ok


def main() -> int:
    passed = True

    print("platform detection:")
    cases = [
        ("https://boards.greenhouse.io/acme/jobs/12345", "greenhouse"),
        ("https://jobs.lever.co/acme/abc-123", "lever"),
        ("https://jobs.ashbyhq.com/acme/uuid-1", "ashby"),
        ("https://acme.wd5.myworkdayjobs.com/en-US/Careers/job/US-CA/Eng_JR1", "workday"),
        ("https://jobs.acme.com/posting/9", "jobs-subdomain"),
        ("https://careers.acme.com/job/9", "careers"),
        ("https://www.acme.com/careers/9", "careers"),
        ("https://example.com/blog", None),
    ]
    for url, want in cases:
        passed &= _check(url, detect_platform(url), want)

    print("\ncompany extraction:")
    passed &= _check(
        "greenhouse", extract_company("https://boards.greenhouse.io/openai/jobs/1", "greenhouse"), "Openai"
    )
    passed &= _check(
        "lever", extract_company("https://jobs.lever.co/scale-ai/x", "lever"), "Scale Ai"
    )
    passed &= _check(
        "jobs-subdomain", extract_company("https://jobs.netflix.com/jobs/1", "jobs-subdomain"), "Netflix"
    )
    passed &= _check(
        "workday", extract_company("https://nvidia.wd5.myworkdayjobs.com/x/job/y_1", "workday"), "Nvidia"
    )

    print("\nworkday cxs url mapping:")
    from .enrich import _workday_cxs_url
    passed &= _check(
        "cxs url",
        _workday_cxs_url("https://nvidia.wd5.myworkdayjobs.com/en-US/Careers/job/US-CA/Eng_JR1"),
        "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/Careers/job/US-CA/Eng_JR1",
    )

    print("\nseniority filter:")
    seniority_cases = [
        ("AI Engineer", True),
        ("Junior Machine Learning Engineer", True),
        ("New Grad Software Engineer", True),
        ("Senior AI Engineer", False),
        ("Staff ML Engineer", False),
        ("Lead Forward Deployed Engineer", False),
        ("VP of Engineering", False),
        ("Machine Learning Engineer II", False),
        ("Principal Architect", False),
    ]
    for title, want in seniority_cases:
        passed &= _check(title, is_junior_role(title)[0], want)

    print("\nseniority filter (REQUIRE_EXPLICIT_JUNIOR=true):")
    config.REQUIRE_EXPLICIT_JUNIOR = True
    passed &= _check("AI Engineer (no marker)", is_junior_role("AI Engineer")[0], False)
    passed &= _check("Junior AI Engineer", is_junior_role("Junior AI Engineer")[0], True)
    config.REQUIRE_EXPLICIT_JUNIOR = False

    print("\nlocation filter:")
    location_cases = [
        ("San Francisco, CA", True),
        ("New York, NY, United States", True),
        ("Remote (US)", True),
        ("Austin, Texas", True),
        ("Remote", True),  # ambiguous remote kept
        ("London, UK", False),
        ("Bangalore, India", False),
        ("Toronto, Canada", False),
        ("Remote - EMEA", False),
    ]
    for loc, want in location_cases:
        passed &= _check(loc, is_us_location(loc)[0], want)

    print("\nrecency filter (max=3d):")
    today = date.today()
    passed &= _check("today", is_recent(today, 3)[0], True)
    passed &= _check("2 days", is_recent(today - timedelta(days=2), 3)[0], True)
    passed &= _check("5 days", is_recent(today - timedelta(days=5), 3)[0], False)
    passed &= _check("unknown", is_recent(None, 3)[0], True)

    print("\nend-to-end parse:")
    sr = SearchResult(
        url="https://boards.greenhouse.io/openai/jobs/777?gh_src=abc",
        title="AI Engineer - OpenAI - Greenhouse",
        snippet="We are hiring an AI Engineer...",
        query='"AI Engineer" site:greenhouse.io remote',
    )
    job = to_posting(sr)
    passed &= _check("parsed not None", job is not None, True)
    if job:
        passed &= _check("company", job.company, "Openai")
        passed &= _check("title cleaned", job.title, "AI Engineer")
        passed &= _check("url stripped", job.url, "https://boards.greenhouse.io/openai/jobs/777")
        passed &= _check("platform", job.platform, "greenhouse")

    print("\n" + ("ALL PASS" if passed else "SOME FAILED"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
