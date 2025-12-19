"""Job normalization utilities."""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from dateutil import parser as date_parser

from app.core.ids import make_job_id
from app.core.models import Job

logger = logging.getLogger(__name__)


def normalize_rss_entry(entry: Dict) -> Optional[Job]:
    """
    Normalize a raw RSS entry dict into a Job object.
    
    Args:
        entry: Raw entry dict with keys: source, title, url, company (optional),
               location (optional), published (optional), published_parsed (optional),
               raw_entry (optional)
    
    Returns:
        Job object or None if entry is invalid
    
    Examples:
        >>> from datetime import datetime, timezone
        >>> import time
        
        >>> # Valid entry with all fields
        >>> entry1 = {
        ...     "source": "linkedin_rss",
        ...     "title": "Software Engineer",
        ...     "url": "https://example.com/job/123",
        ...     "company": "Google",
        ...     "location": "San Francisco, CA",
        ...     "published": "2024-01-15T10:00:00Z",
        ...     "published_parsed": time.struct_time((2024, 1, 15, 10, 0, 0, 0, 15, 0))
        ... }
        >>> job1 = normalize_rss_entry(entry1)
        >>> assert job1 is not None
        >>> assert job1.title == "Software Engineer"
        >>> assert job1.company == "Google"
        >>> assert job1.source == "linkedin_rss"
        >>> assert job1.job_id is not None
        
        >>> # Entry with remote in title
        >>> entry2 = {
        ...     "source": "indeed_rss",
        ...     "title": "Remote Software Engineer",
        ...     "url": "https://example.com/job/456",
        ...     "company": "Company"
        ... }
        >>> job2 = normalize_rss_entry(entry2)
        >>> assert job2 is not None
        >>> assert job2.remote == True
        
        >>> # Entry missing required fields
        >>> entry3 = {
        ...     "source": "linkedin_rss",
        ...     "title": "Engineer",
        ...     # Missing url
        ... }
        >>> job3 = normalize_rss_entry(entry3)
        >>> assert job3 is None
    """
    # Extract required fields
    source = entry.get("source", "").strip()
    title = entry.get("title", "").strip()
    url = entry.get("url", "").strip()
    
    # Validate required fields
    if not source:
        logger.debug("Skipping entry without source")
        return None
    
    if not title:
        logger.debug("Skipping entry without title")
        return None
    
    if not url:
        logger.debug("Skipping entry without url")
        return None
    
    # Extract company (try provided, else parse from title)
    company = entry.get("company")
    if company:
        company = company.strip()
    else:
        # Try to extract from title patterns
        company = _extract_company_from_title(title)
    
    # If still no company, use a default (required field)
    if not company:
        company = "Unknown"
        logger.debug(f"No company found for entry, using 'Unknown': {title}")
    
    # Extract location (try provided, else parse from title)
    location = entry.get("location")
    if location:
        location = location.strip() or None
    else:
        # Try to extract from title patterns (conservative)
        location = _extract_location_from_title(title)
    
    # Parse posted_at (strict: try published_parsed, else parse published, else None)
    posted_at = _parse_posted_at(entry)
    
    # Set fetched_at to now UTC
    fetched_at = datetime.now(timezone.utc)
    
    # Determine remote flag (case-insensitive check in title/location)
    remote = _is_remote(title, location)
    
    # Extract description (optional)
    description = entry.get("description")
    if description:
        description = description.strip() or None
        if description:
            # Strip HTML tags if present
            import re
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\s+', ' ', description).strip() or None
    
    # Generate job_id
    job_id = make_job_id(company, title, url)
    
    # Create Job object
    try:
        job = Job(
            job_id=job_id,
            source=source,
            title=title,
            company=company,
            location=location,
            remote=remote,
            url=url,
            description=description,
            posted_at=posted_at,
            fetched_at=fetched_at,
            tags=[],  # Tags will be added later
            raw=entry.get("raw_entry") or entry,  # Store raw entry
        )
        return job
    except ValueError as e:
        logger.error(f"Error creating Job object: {e}", exc_info=True)
        return None


def normalize_greenhouse(raw: Dict) -> Optional[Job]:
    """
    Normalize a raw Greenhouse entry dict into a Job object.
    
    Args:
        raw: Raw Greenhouse entry dict with keys: source, title, url, company,
             location (optional), updated_at (optional), created_at (optional),
             raw (optional)
    
    Returns:
        Job object or None if entry is invalid
    
    Examples:
        >>> # Valid Greenhouse entry
        >>> entry1 = {
        ...     "source": "greenhouse",
        ...     "title": "Software Engineer",
        ...     "url": "https://boards.greenhouse.io/company/jobs/123",
        ...     "company": "company",
        ...     "location": "San Francisco, CA",
        ...     "updated_at": "2024-01-15T10:00:00Z",
        ...     "created_at": "2024-01-10T08:00:00Z"
        ... }
        >>> job1 = normalize_greenhouse(entry1)
        >>> assert job1 is not None
        >>> assert job1.title == "Software Engineer"
        >>> assert job1.company == "company"
        >>> assert job1.source == "greenhouse"
        >>> assert job1.job_id is not None
        >>> # Should prefer updated_at if it's a real posting timestamp
        >>> assert job1.posted_at is not None
        
        >>> # Entry with only created_at
        >>> entry2 = {
        ...     "source": "greenhouse",
        ...     "title": "Product Manager",
        ...     "url": "https://boards.greenhouse.io/company/jobs/456",
        ...     "company": "company",
        ...     "created_at": "2024-01-15T10:00:00Z"
        ... }
        >>> job2 = normalize_greenhouse(entry2)
        >>> assert job2 is not None
        >>> assert job2.posted_at is not None
        
        >>> # Entry missing required fields
        >>> entry3 = {
        ...     "source": "greenhouse",
        ...     "title": "Engineer"
        ...     # Missing url
        ... }
        >>> job3 = normalize_greenhouse(entry3)
        >>> assert job3 is None
    """
    # Extract required fields
    source = raw.get("source", "").strip()
    title = raw.get("title", "").strip()
    url = raw.get("url", "").strip()
    company = raw.get("company", "").strip()
    
    # Validate required fields
    if not source:
        logger.debug("Skipping Greenhouse entry without source")
        return None
    
    if not title:
        logger.debug("Skipping Greenhouse entry without title")
        return None
    
    if not url:
        logger.debug("Skipping Greenhouse entry without url")
        return None
    
    if not company:
        company = "Unknown"
        logger.debug(f"No company found for Greenhouse entry, using 'Unknown': {title}")
    
    # Extract location (optional)
    location = raw.get("location")
    if location:
        location = location.strip() or None
    
    # Parse posted_at (prefer updated_at if it's a real posting timestamp, else created_at)
    posted_at = _parse_greenhouse_posted_at(raw)
    
    # Set fetched_at to now UTC
    fetched_at = datetime.now(timezone.utc)
    
    # Determine remote flag (case-insensitive check in title/location)
    remote = _is_remote(title, location)
    
    # Extract description (optional)
    description = raw.get("description")
    if description:
        description = description.strip() or None
    
    # Generate job_id
    job_id = make_job_id(company, title, url)
    
    # Create Job object
    try:
        job = Job(
            job_id=job_id,
            source=source,
            title=title,
            company=company,
            location=location,
            remote=remote,
            url=url,
            description=description,
            posted_at=posted_at,
            fetched_at=fetched_at,
            tags=[],  # Tags will be added later
            raw=raw.get("raw") or raw,  # Store raw entry
        )
        return job
    except ValueError as e:
        logger.error(f"Error creating Job object from Greenhouse entry: {e}", exc_info=True)
        return None


def normalize_lever(raw: Dict) -> Optional[Job]:
    """
    Normalize a raw Lever entry dict into a Job object.
    
    Args:
        raw: Raw Lever entry dict with keys: source, title, url, company,
             location (optional), createdAt (milliseconds epoch), raw (optional)
    
    Returns:
        Job object or None if entry is invalid
    
    Examples:
        >>> # Valid Lever entry
        >>> entry1 = {
        ...     "source": "lever",
        ...     "title": "Software Engineer",
        ...     "url": "https://jobs.lever.co/company/job-id",
        ...     "company": "company",
        ...     "location": "San Francisco, CA",
        ...     "createdAt": 1705315200000  # milliseconds epoch
        ... }
        >>> job1 = normalize_lever(entry1)
        >>> assert job1 is not None
        >>> assert job1.title == "Software Engineer"
        >>> assert job1.company == "company"
        >>> assert job1.source == "lever"
        >>> assert job1.job_id is not None
        >>> assert job1.posted_at is not None
        
        >>> # Entry missing required fields
        >>> entry2 = {
        ...     "source": "lever",
        ...     "title": "Engineer",
        ...     # Missing url
        ... }
        >>> job2 = normalize_lever(entry2)
        >>> assert job2 is None
    """
    # Extract required fields
    source = raw.get("source", "").strip()
    title = raw.get("title", "").strip()
    url = raw.get("url", "").strip()
    company = raw.get("company", "").strip()
    
    # Validate required fields
    if not source:
        logger.debug("Skipping Lever entry without source")
        return None
    
    if not title:
        logger.debug("Skipping Lever entry without title")
        return None
    
    if not url:
        logger.debug("Skipping Lever entry without url")
        return None
    
    if not company:
        company = "Unknown"
        logger.debug(f"No company found for Lever entry, using 'Unknown': {title}")
    
    # Extract location (optional)
    location = raw.get("location")
    if location:
        location = location.strip() or None
    
    # Parse posted_at from createdAt (milliseconds epoch)
    posted_at = _parse_lever_posted_at(raw)
    
    # Set fetched_at to now UTC
    fetched_at = datetime.now(timezone.utc)
    
    # Determine remote flag (case-insensitive check in title/location)
    remote = _is_remote(title, location)
    
    # Extract description (optional)
    description = raw.get("description")
    if description:
        description = description.strip() or None
    
    # Generate job_id
    job_id = make_job_id(company, title, url)
    
    # Create Job object
    try:
        job = Job(
            job_id=job_id,
            source=source,
            title=title,
            company=company,
            location=location,
            remote=remote,
            url=url,
            description=description,
            posted_at=posted_at,
            fetched_at=fetched_at,
            tags=[],  # Tags will be added later
            raw=raw.get("raw") or raw,  # Store raw entry
        )
        return job
    except ValueError as e:
        logger.error(f"Error creating Job object from Lever entry: {e}", exc_info=True)
        return None


def normalize_all(raw_items: List[Dict]) -> List[Job]:
    """
    Normalize a list of raw entry dicts into Job objects.
    
    Automatically routes to the appropriate normalizer based on source.
    
    Args:
        raw_items: List of raw entry dicts
    
    Returns:
        List of Job objects (invalid entries are skipped)
    
    Examples:
        >>> entries = [
        ...     {
        ...         "source": "linkedin_rss",
        ...         "title": "Engineer",
        ...         "url": "https://example.com/1",
        ...         "company": "Company1"
        ...     },
        ...     {
        ...         "source": "greenhouse",
        ...         "title": "Manager",
        ...         "url": "https://example.com/2",
        ...         "company": "Company2"
        ...     },
        ...     {
        ...         "source": "lever",
        ...         "title": "Designer",
        ...         "url": "https://example.com/3",
        ...         "company": "Company3",
        ...         "createdAt": 1705315200000
        ...     }
        ... ]
        >>> jobs = normalize_all(entries)
        >>> assert len(jobs) == 3
        >>> assert all(job.job_id is not None for job in jobs)
    """
    jobs = []
    
    for entry in raw_items:
        try:
            source = entry.get("source", "").strip().lower()
            
            if source == "greenhouse":
                job = normalize_greenhouse(entry)
            elif source == "lever":
                job = normalize_lever(entry)
            else:
                # Default to RSS entry normalizer
                job = normalize_rss_entry(entry)
            
            if job:
                jobs.append(job)
        except Exception as e:
            logger.error(f"Error normalizing entry: {e}", exc_info=True)
            continue
    
    logger.info(f"Normalized {len(jobs)} jobs from {len(raw_items)} raw entries")
    return jobs


def _parse_posted_at(entry: Dict) -> Optional[datetime]:
    """
    Parse posted_at from RSS entry (strict: try published_parsed, else parse published, else None).
    
    Args:
        entry: Entry dict with published_parsed and/or published
    
    Returns:
        datetime in UTC or None
    """
    # Try published_parsed first (time.struct_time)
    if entry.get("published_parsed"):
        try:
            struct_time = entry["published_parsed"]
            # Convert struct_time to datetime
            posted_at = datetime(*struct_time[:6], tzinfo=timezone.utc)
            return posted_at
        except (ValueError, TypeError, IndexError) as e:
            logger.debug(f"Error parsing published_parsed: {e}")
    
    # Try parsing published string with dateutil
    if entry.get("published"):
        try:
            published_str = entry["published"]
            posted_at = date_parser.parse(published_str)
            
            # Ensure timezone-aware (assume UTC if naive)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            else:
                posted_at = posted_at.astimezone(timezone.utc)
            
            return posted_at
        except (ValueError, TypeError, date_parser.ParserError) as e:
            logger.debug(f"Error parsing published string: {e}")
    
    # Strict: return None if neither works
    return None


def _parse_greenhouse_posted_at(raw: Dict) -> Optional[datetime]:
    """
    Parse posted_at from Greenhouse entry (prefer updated_at if real posting timestamp, else created_at).
    
    Args:
        raw: Greenhouse entry dict with updated_at and/or created_at
    
    Returns:
        datetime in UTC or None
    """
    updated_at = raw.get("updated_at")
    created_at = raw.get("created_at")
    
    # Prefer updated_at if available (it's usually the posting timestamp)
    # But if updated_at is very recent (within last hour) and created_at is older,
    # updated_at might just be a metadata update, so prefer created_at
    if updated_at:
        try:
            updated_dt = date_parser.parse(updated_at)
            
            # Ensure timezone-aware
            if updated_dt.tzinfo is None:
                updated_dt = updated_dt.replace(tzinfo=timezone.utc)
            else:
                updated_dt = updated_dt.astimezone(timezone.utc)
            
            # If created_at exists and is significantly older, use created_at
            # (updated_at might be a metadata update, not the posting time)
            if created_at:
                try:
                    created_dt = date_parser.parse(created_at)
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                    else:
                        created_dt = created_dt.astimezone(timezone.utc)
                    
                    # If created_at is more than 1 day older, it's likely the real posting time
                    from datetime import timedelta
                    if created_dt < updated_dt - timedelta(days=1):
                        return created_dt
                except (ValueError, TypeError, date_parser.ParserError):
                    pass
            
            return updated_dt
        except (ValueError, TypeError, date_parser.ParserError) as e:
            logger.debug(f"Error parsing Greenhouse updated_at: {e}")
    
    # Fall back to created_at
    if created_at:
        try:
            created_dt = date_parser.parse(created_at)
            
            # Ensure timezone-aware
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            else:
                created_dt = created_dt.astimezone(timezone.utc)
            
            return created_dt
        except (ValueError, TypeError, date_parser.ParserError) as e:
            logger.debug(f"Error parsing Greenhouse created_at: {e}")
    
    # Return None if neither works
    return None


def _parse_lever_posted_at(raw: Dict) -> Optional[datetime]:
    """
    Parse posted_at from Lever entry (createdAt is milliseconds epoch timestamp).
    
    Args:
        raw: Lever entry dict with createdAt (milliseconds epoch)
    
    Returns:
        datetime in UTC or None
    """
    createdAt = raw.get("createdAt")
    
    if createdAt is None:
        return None
    
    try:
        # Convert milliseconds epoch to datetime
        # createdAt is in milliseconds, so divide by 1000
        timestamp_seconds = createdAt / 1000.0
        posted_at = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        return posted_at
    except (ValueError, TypeError, OSError) as e:
        logger.debug(f"Error parsing Lever createdAt: {e}")
        return None


def _extract_company_from_title(title: str) -> Optional[str]:
    """
    Light parsing of company from title patterns (conservative).
    
    Patterns:
    - "Title at Company"
    - "Title - Company"
    - "Company - Title"
    
    Args:
        title: Job title string
    
    Returns:
        Company name or None if pattern not found
    """
    if not title:
        return None
    
    # Common separators
    for separator in [" at ", " - ", " | "]:
        if separator in title:
            parts = title.split(separator, 1)
            if len(parts) == 2:
                part1, part2 = parts[0].strip(), parts[1].strip()
                
                # Conservative: only extract if one part looks like a job title
                # (contains common job words) and the other doesn't
                job_words = [
                    "engineer", "developer", "manager", "analyst", "designer",
                    "director", "lead", "senior", "junior", "intern", "specialist"
                ]
                
                part1_has_job_word = any(word in part1.lower() for word in job_words)
                part2_has_job_word = any(word in part2.lower() for word in job_words)
                
                if part1_has_job_word and not part2_has_job_word:
                    # part2 is likely the company
                    return part2
                elif part2_has_job_word and not part1_has_job_word:
                    # part1 is likely the company
                    return part1
                elif separator == " at ":
                    # "Title at Company" pattern - second part is company
                    return part2
    
    return None


def _extract_location_from_title(title: str) -> Optional[str]:
    """
    Light parsing of location from title patterns (conservative).
    
    Looks for location in parentheses or after certain patterns.
    
    Args:
        title: Job title string
    
    Returns:
        Location string or None if pattern not found
    """
    if not title:
        return None
    
    # Look for location in parentheses (conservative: only if it looks like location)
    if "(" in title and ")" in title:
        import re
        matches = re.findall(r'\(([^)]+)\)', title)
        for match in matches:
            match_lower = match.lower()
            # Check if it looks like a location
            location_indicators = [
                "remote", "hybrid", "ca", "ny", "tx", "fl", "city", "state",
                "san francisco", "new york", "los angeles", "chicago", "boston"
            ]
            if any(indicator in match_lower for indicator in location_indicators):
                return match.strip()
    
    return None


def _is_remote(title: Optional[str], location: Optional[str]) -> bool:
    """
    Determine if job is remote based on title and location (case-insensitive).
    
    Args:
        title: Job title
        location: Job location
    
    Returns:
        True if "remote" appears in title or location
    """
    remote_keyword = "remote"
    
    if title and remote_keyword in title.lower():
        return True
    
    if location and remote_keyword in location.lower():
        return True
    
    return False


# Legacy functions for backward compatibility
def normalize_job(job: Job) -> Job:
    """
    Normalize a job object (legacy function).
    
    Ensures consistent formatting, timezone handling, and data quality.
    
    Args:
        job: Job object to normalize
    
    Returns:
        Normalized Job object
    """
    # Normalize strings
    job.title = job.title.strip() if job.title else ""
    job.company = job.company.strip() if job.company else ""
    job.location = job.location.strip() if job.location else None
    
    # Ensure fetched_at is set to UTC now if not set
    if job.fetched_at is None:
        job.fetched_at = datetime.now(timezone.utc)
    elif job.fetched_at.tzinfo is None:
        # Assume UTC if naive
        job.fetched_at = job.fetched_at.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        job.fetched_at = job.fetched_at.astimezone(timezone.utc)
    
    # Normalize posted_at to UTC
    if job.posted_at is not None:
        if job.posted_at.tzinfo is None:
            # Assume UTC if naive
            job.posted_at = job.posted_at.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            job.posted_at = job.posted_at.astimezone(timezone.utc)
    
    # Normalize tags
    if job.tags:
        job.tags = [tag.strip().lower() for tag in job.tags if tag.strip()]
    
    return job


def normalize_jobs(jobs: List[Job]) -> List[Job]:
    """
    Normalize a list of jobs (legacy function).
    
    Args:
        jobs: List of Job objects
    
    Returns:
        List of normalized Job objects
    """
    return [normalize_job(job) for job in jobs]
