"""Canonical Job schema and data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    """Canonical job schema for all sources."""
    
    job_id: str  # Stable hash-based identifier
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[datetime] = None
    source: str = ""  # 'rss', 'greenhouse', 'lever', etc.
    source_id: Optional[str] = None  # Original ID from source
    department: Optional[str] = None
    employment_type: Optional[str] = None  # 'full-time', 'part-time', etc.
    salary_range: Optional[str] = None
    raw_data: dict = field(default_factory=dict)  # Store original data
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.job_id:
            raise ValueError("job_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.company:
            raise ValueError("company is required")

