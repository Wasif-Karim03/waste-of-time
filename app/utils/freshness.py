"""Freshness filter utilities."""

from datetime import datetime, timedelta, timezone
from typing import List

from app.models import Job
from app.config import Config


def filter_by_freshness(jobs: List[Job], max_age_hours: int = None) -> List[Job]:
    """
    Filter jobs to keep only those posted within MAX_AGE_HOURS.
    
    Jobs without posted_at are excluded (cannot verify freshness).
    """
    if max_age_hours is None:
        max_age_hours = Config.MAX_AGE_HOURS
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    
    fresh_jobs = []
    for job in jobs:
        if job.posted_at is None:
            # Skip jobs without posted_at timestamp
            continue
        
        # Convert posted_at to UTC for comparison
        if job.posted_at.tzinfo is None:
            # Assume UTC if naive datetime
            posted_utc = job.posted_at.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            posted_utc = job.posted_at.astimezone(timezone.utc)
        
        if posted_utc >= cutoff_time:
            fresh_jobs.append(job)
    
    return fresh_jobs

