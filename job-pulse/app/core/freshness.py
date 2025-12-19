"""Freshness filter utilities."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.core.models import Job

logger = logging.getLogger(__name__)


def is_fresh(posted_at: datetime, now_utc: datetime, max_age_hours: int) -> bool:
    """
    Check if a job posting is fresh (within max_age_hours of now_utc).
    
    Args:
        posted_at: Job posting datetime (timezone-aware UTC or naive treated as UTC)
        now_utc: Current time in UTC (must be timezone-aware)
        max_age_hours: Maximum age in hours
    
    Returns:
        True if job is fresh (posted within max_age_hours), False otherwise
    
    Raises:
        ValueError: If now_utc is not timezone-aware
    
    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> now = datetime.now(timezone.utc)
        >>> recent = now - timedelta(hours=12)
        >>> old = now - timedelta(hours=48)
        
        >>> # Fresh job (12 hours old, max 24 hours)
        >>> assert is_fresh(recent, now, 24) == True
        
        >>> # Old job (48 hours old, max 24 hours)
        >>> assert is_fresh(old, now, 24) == False
        
        >>> # Exactly at the boundary
        >>> boundary = now - timedelta(hours=24)
        >>> assert is_fresh(boundary, now, 24) == True
        
        >>> # Just over the boundary
        >>> over_boundary = now - timedelta(hours=24, seconds=1)
        >>> assert is_fresh(over_boundary, now, 24) == False
        
        >>> # Naive datetime treated as UTC
        >>> naive_recent = datetime.now()
        >>> naive_recent_utc = naive_recent.replace(tzinfo=timezone.utc)
        >>> assert is_fresh(naive_recent, naive_recent_utc + timedelta(hours=1), 2) == True
    """
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware (UTC)")
    
    # Handle naive posted_at (treat as UTC but log warning)
    if posted_at.tzinfo is None:
        logger.warning(
            f"Naive datetime detected for posted_at: {posted_at}. "
            "Treating as UTC. Consider using timezone-aware datetimes."
        )
        posted_at_utc = posted_at.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC if not already
        posted_at_utc = posted_at.astimezone(timezone.utc)
    
    # Calculate cutoff time
    cutoff_time = now_utc - timedelta(hours=max_age_hours)
    
    # Job is fresh if posted_at >= cutoff_time
    return posted_at_utc >= cutoff_time


def filter_fresh(jobs: List[Job], max_age_hours: int) -> List[Job]:
    """
    Filter jobs to keep only those posted within max_age_hours.
    
    Jobs without posted_at are excluded (cannot verify freshness).
    Jobs with naive posted_at are treated as UTC with a warning logged.
    
    Args:
        jobs: List of Job objects
        max_age_hours: Maximum age in hours
    
    Returns:
        List of fresh Job objects (posted within max_age_hours)
    
    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> from app.core.models import Job
        >>> from app.core.ids import make_job_id
        
        >>> now = datetime.now(timezone.utc)
        >>> recent_time = now - timedelta(hours=12)
        >>> old_time = now - timedelta(hours=48)
        
        >>> # Create test jobs
        >>> job1 = Job(
        ...     job_id=make_job_id("Company1", "Engineer", "https://example.com/1"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company1",
        ...     posted_at=recent_time
        ... )
        >>> job2 = Job(
        ...     job_id=make_job_id("Company2", "Manager", "https://example.com/2"),
        ...     source="test",
        ...     title="Manager",
        ...     company="Company2",
        ...     posted_at=old_time
        ... )
        >>> job3 = Job(
        ...     job_id=make_job_id("Company3", "Designer", "https://example.com/3"),
        ...     source="test",
        ...     title="Designer",
        ...     company="Company3",
        ...     posted_at=None  # No timestamp
        ... )
        
        >>> # Filter with 24 hour max age
        >>> fresh = filter_fresh([job1, job2, job3], 24)
        >>> assert len(fresh) == 1
        >>> assert fresh[0].job_id == job1.job_id
        
        >>> # Filter with 72 hour max age
        >>> fresh_all = filter_fresh([job1, job2, job3], 72)
        >>> assert len(fresh_all) == 2
        >>> assert job3 not in fresh_all  # Jobs without posted_at are excluded
    """
    if not jobs:
        return []
    
    now_utc = datetime.now(timezone.utc)
    fresh_jobs = []
    
    for job in jobs:
        if job.posted_at is None:
            # Skip jobs without posted_at timestamp
            continue
        
        if is_fresh(job.posted_at, now_utc, max_age_hours):
            fresh_jobs.append(job)
    
    return fresh_jobs


def filter_by_freshness(jobs: List[Job], max_age_hours: Optional[int] = None) -> List[Job]:
    """
    Filter jobs to keep only those posted within MAX_AGE_HOURS.
    
    Legacy function for backward compatibility. Prefer using filter_fresh().
    
    Jobs without posted_at are excluded (cannot verify freshness).
    
    Args:
        jobs: List of Job objects
        max_age_hours: Maximum age in hours (defaults to Config.MAX_AGE_HOURS)
    
    Returns:
        List of fresh Job objects
    """
    from app.config import Config
    
    if max_age_hours is None:
        max_age_hours = Config.MAX_AGE_HOURS
    
    return filter_fresh(jobs, max_age_hours)
