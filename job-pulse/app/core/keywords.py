"""Keyword extraction and tagging utilities."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.models import Job


def tag_job(job: Job, keywords: List[str]) -> Job:
    """
    Tag a job by checking if keywords appear in title, company, or location.
    
    Returns a copy of the job with tags filled when keyword appears in title/company/location.
    Keywords are matched case-insensitively.
    
    Args:
        job: Job object to tag
        keywords: List of keywords to search for
    
    Returns:
        New Job object with tags populated (original job is not modified)
    
    Examples:
        >>> from datetime import datetime, timezone
        >>> from app.core.ids import make_job_id
        
        >>> job = Job(
        ...     job_id=make_job_id("Google", "Python Engineer", "https://example.com"),
        ...     source="test",
        ...     title="Python Engineer",
        ...     company="Google",
        ...     location="San Francisco, CA"
        ... )
        
        >>> # Tag with keywords that match
        >>> tagged = tag_job(job, ["python", "engineer", "google"])
        >>> assert "python" in tagged.tags
        >>> assert "engineer" in tagged.tags
        >>> assert "google" in tagged.tags
        >>> assert len(tagged.tags) == 3
        
        >>> # Tag with keywords that don't match
        >>> tagged2 = tag_job(job, ["java", "manager"])
        >>> assert len(tagged2.tags) == 0
        
        >>> # Tag with partial matches (case-insensitive)
        >>> tagged3 = tag_job(job, ["PYTHON", "Engineer", "GOOGLE"])
        >>> assert len(tagged3.tags) == 3
        
        >>> # Original job is not modified
        >>> assert len(job.tags) == 0
    """
    if not keywords:
        return replace(job, tags=[])
    
    # Normalize keywords to lowercase for matching
    keywords_lower = [kw.lower().strip() for kw in keywords if kw.strip()]
    
    matched_tags = []
    
    # Check title
    if job.title:
        title_lower = job.title.lower()
        for keyword in keywords_lower:
            if keyword in title_lower and keyword not in matched_tags:
                matched_tags.append(keyword)
    
    # Check company
    if job.company:
        company_lower = job.company.lower()
        for keyword in keywords_lower:
            if keyword in company_lower and keyword not in matched_tags:
                matched_tags.append(keyword)
    
    # Check location
    if job.location:
        location_lower = job.location.lower()
        for keyword in keywords_lower:
            if keyword in location_lower and keyword not in matched_tags:
                matched_tags.append(keyword)
    
    # Return a copy with tags filled
    return replace(job, tags=matched_tags)


def score_job(job: Job) -> int:
    """
    Calculate a simple deterministic score for a job.
    
    Scoring:
    - +3 points if tags are non-empty
    - +2 points if job is remote
    - +1 point if posted within 6 hours (compared to fetched_at)
    
    Args:
        job: Job object to score
    
    Returns:
        Integer score (0 or higher)
    
    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> from app.core.ids import make_job_id
        
        >>> now = datetime.now(timezone.utc)
        
        >>> # Job with tags, remote, and recent posting
        >>> job1 = Job(
        ...     job_id=make_job_id("Company", "Engineer", "https://example.com/1"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company",
        ...     remote=True,
        ...     tags=["python", "remote"],
        ...     posted_at=now - timedelta(hours=3),
        ...     fetched_at=now
        ... )
        >>> score1 = score_job(job1)
        >>> assert score1 == 6  # 3 (tags) + 2 (remote) + 1 (recent)
        
        >>> # Job with no tags, not remote, old posting
        >>> job2 = Job(
        ...     job_id=make_job_id("Company", "Manager", "https://example.com/2"),
        ...     source="test",
        ...     title="Manager",
        ...     company="Company",
        ...     remote=False,
        ...     tags=[],
        ...     posted_at=now - timedelta(hours=24),
        ...     fetched_at=now
        ... )
        >>> score2 = score_job(job2)
        >>> assert score2 == 0
        
        >>> # Job with tags only
        >>> job3 = Job(
        ...     job_id=make_job_id("Company", "Designer", "https://example.com/3"),
        ...     source="test",
        ...     title="Designer",
        ...     company="Company",
        ...     tags=["design"]
        ... )
        >>> score3 = score_job(job3)
        >>> assert score3 == 3
        
        >>> # Job with remote only
        >>> job4 = Job(
        ...     job_id=make_job_id("Company", "Writer", "https://example.com/4"),
        ...     source="test",
        ...     title="Writer",
        ...     company="Company",
        ...     remote=True
        ... )
        >>> score4 = score_job(job4)
        >>> assert score4 == 2
        
        >>> # Job posted exactly 6 hours ago (should not get +1)
        >>> job5 = Job(
        ...     job_id=make_job_id("Company", "Dev", "https://example.com/5"),
        ...     source="test",
        ...     title="Dev",
        ...     company="Company",
        ...     tags=["python"],
        ...     posted_at=now - timedelta(hours=6),
        ...     fetched_at=now
        ... )
        >>> score5 = score_job(job5)
        >>> assert score5 == 3  # Only tags, not recent enough
        
        >>> # Job posted 5 hours 59 minutes ago (should get +1)
        >>> job6 = Job(
        ...     job_id=make_job_id("Company", "Dev", "https://example.com/6"),
        ...     source="test",
        ...     title="Dev",
        ...     company="Company",
        ...     tags=["python"],
        ...     posted_at=now - timedelta(hours=5, minutes=59),
        ...     fetched_at=now
        ... )
        >>> score6 = score_job(job6)
        >>> assert score6 == 4  # Tags + recent
    """
    score = 0
    
    # +3 if tags are non-empty
    if job.tags:
        score += 3
    
    # +2 if remote
    if job.remote:
        score += 2
    
    # +1 if posted within 6 hours (compared to fetched_at)
    if job.posted_at and job.fetched_at:
        # Ensure both are timezone-aware
        posted_at = job.posted_at
        fetched_at = job.fetched_at
        
        # Handle naive datetimes (assume UTC)
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        else:
            posted_at = posted_at.astimezone(timezone.utc)
        
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        else:
            fetched_at = fetched_at.astimezone(timezone.utc)
        
        # Check if posted within 6 hours of fetched_at (less than 6 hours, not equal)
        time_diff = fetched_at - posted_at
        if time_diff < timedelta(hours=6):
            score += 1
    
    return score


def sort_jobs(jobs: List[Job]) -> List[Job]:
    """
    Sort jobs by score (descending) then by posted_at (descending).
    
    Jobs with higher scores come first. For jobs with the same score,
    more recently posted jobs come first.
    
    Args:
        jobs: List of Job objects to sort
    
    Returns:
        Sorted list of Job objects (original list is not modified)
    
    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> from app.core.ids import make_job_id
        
        >>> now = datetime.now(timezone.utc)
        
        >>> # Create jobs with different scores
        >>> job1 = Job(
        ...     job_id=make_job_id("Company1", "Engineer", "https://example.com/1"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company1",
        ...     tags=["python"],
        ...     posted_at=now - timedelta(hours=1)
        ... )
        
        >>> job2 = Job(
        ...     job_id=make_job_id("Company2", "Manager", "https://example.com/2"),
        ...     source="test",
        ...     title="Manager",
        ...     company="Company2",
        ...     remote=True,
        ...     posted_at=now - timedelta(hours=2)
        ... )
        
        >>> job3 = Job(
        ...     job_id=make_job_id("Company3", "Designer", "https://example.com/3"),
        ...     source="test",
        ...     title="Designer",
        ...     company="Company3",
        ...     posted_at=now - timedelta(hours=3)
        ... )
        
        >>> # Sort jobs
        >>> sorted_jobs = sort_jobs([job3, job1, job2])
        >>> # job1 should be first (score 3, most recent)
        >>> assert sorted_jobs[0].job_id == job1.job_id
        >>> # job2 should be second (score 2, more recent than job3)
        >>> assert sorted_jobs[1].job_id == job2.job_id
        >>> # job3 should be last (score 0)
        >>> assert sorted_jobs[2].job_id == job3.job_id
        
        >>> # Test with jobs having same score but different posted_at
        >>> job4 = Job(
        ...     job_id=make_job_id("Company4", "Dev", "https://example.com/4"),
        ...     source="test",
        ...     title="Dev",
        ...     company="Company4",
        ...     tags=["python"],
        ...     posted_at=now - timedelta(hours=5)
        ... )
        >>> job5 = Job(
        ...     job_id=make_job_id("Company5", "Dev", "https://example.com/5"),
        ...     source="test",
        ...     title="Dev",
        ...     company="Company5",
        ...     tags=["python"],
        ...     posted_at=now - timedelta(hours=1)
        ... )
        >>> sorted_same_score = sort_jobs([job4, job5])
        >>> # job5 should be first (same score, more recent)
        >>> assert sorted_same_score[0].job_id == job5.job_id
    """
    if not jobs:
        return []
    
    # Create a list of (score, posted_at, job) tuples for sorting
    # Use a sentinel datetime for jobs without posted_at (sort them last)
    sentinel = datetime.min.replace(tzinfo=timezone.utc)
    
    def get_sort_key(job: Job):
        score = score_job(job)
        posted_at = job.posted_at if job.posted_at else sentinel
        
        # Normalize to UTC for comparison
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        else:
            posted_at = posted_at.astimezone(timezone.utc)
        
        # Return tuple for sorting: (-score, -posted_at)
        # Negative for descending order
        # For datetime, we can't negate, so we'll use reverse=True and negate the timestamp
        posted_timestamp = posted_at.timestamp()
        return (-score, -posted_timestamp)
    
    # Sort by score (desc) then posted_at (desc)
    sorted_list = sorted(jobs, key=get_sort_key)
    
    return sorted_list


# Legacy functions for backward compatibility
def extract_keywords(job: Job) -> List[str]:
    """
    Extract keywords/tags from a job (legacy function).
    
    This is kept for backward compatibility. Prefer using tag_job() with explicit keywords.
    """
    keywords = []
    
    # Extract from title
    if job.title:
        title_lower = job.title.lower()
        # Common tech keywords
        tech_keywords = [
            'python', 'javascript', 'typescript', 'java', 'go', 'rust', 'c++', 'c#',
            'react', 'vue', 'angular', 'node', 'django', 'flask', 'fastapi',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'machine learning', 'ml', 'ai', 'data science', 'backend', 'frontend',
            'full stack', 'devops', 'sre', 'security', 'cybersecurity'
        ]
        
        for keyword in tech_keywords:
            if keyword in title_lower:
                keywords.append(keyword)
    
    # Extract from location/remote
    if job.remote:
        keywords.append('remote')
    
    if job.location:
        location_lower = job.location.lower()
        if 'remote' in location_lower:
            keywords.append('remote')
        if 'hybrid' in location_lower:
            keywords.append('hybrid')
    
    # Extract from source
    if job.source:
        keywords.append(job.source)
    
    # Remove duplicates and return
    return list(set(keywords))


def tag_jobs(jobs: List[Job], keywords: List[str] = None) -> List[Job]:
    """
    Add tags to a list of jobs.
    
    Args:
        jobs: List of Job objects
        keywords: Optional list of keywords to search for. If None, uses extract_keywords().
    
    Returns:
        List of Job objects with tags populated
    """
    if keywords is not None:
        return [tag_job(job, keywords) for job in jobs]
    else:
        # Legacy behavior: extract keywords automatically
        result = []
        for job in jobs:
            extracted = extract_keywords(job)
            result.append(replace(job, tags=extracted))
        return result
