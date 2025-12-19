"""Canonical Job schema and data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Job:
    """Canonical job schema for all sources."""
    
    job_id: str  # Stable hash-based identifier
    source: str  # Source identifier (e.g., 'linkedin_rss', 'indeed_rss', 'greenhouse', 'lever')
    title: str
    company: str
    location: Optional[str] = None
    remote: bool = False  # Whether job is remote
    url: Optional[str] = None
    description: Optional[str] = None  # Job description
    posted_at: Optional[datetime] = None  # UTC datetime
    fetched_at: Optional[datetime] = None  # UTC datetime when fetched
    tags: List[str] = field(default_factory=list)  # Tags/keywords
    raw: Optional[Dict] = None  # Raw source data
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.job_id:
            raise ValueError("job_id is required")
        if not self.source:
            raise ValueError("source is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.company:
            raise ValueError("company is required")

