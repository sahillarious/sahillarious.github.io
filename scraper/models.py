"""Data model for a single scraped job posting."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Optional


@dataclass
class JobPosting:
    """One job posting flowing through the pipeline.

    Fields are populated progressively:
      * search stage  -> url, title, platform, company (guess), snippet
      * enrich stage  -> description, location, date_posted, employment_type
      * filter stage  -> sets `dropped` + `drop_reason` instead of removing,
                         so we can audit why something was excluded.
    """

    # --- always present after search ---
    url: str
    title: str
    platform: str
    company: str = ""
    snippet: str = ""

    # --- populated during enrichment ---
    description: str = ""
    location: str = ""
    date_posted: Optional[date] = None
    employment_type: str = ""

    # --- bookkeeping / metadata ---
    source_query: str = ""
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    # --- filter audit trail ---
    dropped: bool = False
    drop_reason: str = ""

    @property
    def id(self) -> str:
        """Stable de-dup key derived from the canonical URL."""
        return hashlib.sha1(self.url.strip().lower().encode()).hexdigest()[:16]

    @property
    def age_days(self) -> Optional[int]:
        if self.date_posted is None:
            return None
        return (date.today() - self.date_posted).days

    def to_record(self) -> dict[str, Any]:
        """Flat, serialization-friendly dict (for JSON / Excel rows)."""
        d = asdict(self)
        d["id"] = self.id
        d["age_days"] = self.age_days
        d["date_posted"] = self.date_posted.isoformat() if self.date_posted else ""
        d["scraped_at"] = self.scraped_at.isoformat()
        # Flatten metadata into a compact string for spreadsheet cells.
        d["metadata"] = "; ".join(f"{k}={v}" for k, v in self.metadata.items())
        return d


# Column order used for the Excel / JSON export.
EXPORT_COLUMNS: list[str] = [
    "company",
    "title",
    "platform",
    "location",
    "date_posted",
    "age_days",
    "employment_type",
    "url",
    "description",
    "snippet",
    "source_query",
    "scraped_at",
    "metadata",
    "id",
]
