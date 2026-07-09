"""Job-apply automation pipeline — scraping + filtering backend.

Public API:
    from scraper.pipeline import run
    from scraper.config import RunConfig
"""
from .models import JobPosting  # noqa: F401

__all__ = ["JobPosting"]
__version__ = "0.1.0"
