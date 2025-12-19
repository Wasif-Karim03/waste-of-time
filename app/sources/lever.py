"""Lever API client for job listings."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import requests

from app.models import Job
from app.utils.dedupe import generate_job_id

logger = logging.getLogger(__name__)


def fetch_lever_jobs(company: str) -> List[Job]:
    """
    Fetch jobs from Lever API for a given company.
    
    Args:
        company: Lever company identifier (e.g., 'companyname')
    
    Returns:
        List of Job objects
    """
    jobs = []
    
    try:
        # Lever public API endpoint
        url = f"https://api.lever.co/v0/postings/{company}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        for job_data in data:
            try:
                job = _parse_lever_job(job_data, company)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing Lever job: {e}", exc_info=True)
                continue
        
        logger.info(f"Fetched {len(jobs)} jobs from Lever company: {company}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Lever jobs for {company}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error with Lever API: {e}", exc_info=True)
    
    return jobs


def _parse_lever_job(job_data: dict, company: str) -> Optional[Job]:
    """Parse a Lever job object into a Job."""
    # Extract required fields
    title = job_data.get("text", "").strip()
    if not title:
        return None
    
    # Company name
    company_name = (
        job_data.get("company", {}).get("name", "") or
        company.replace("-", " ").title() or
        "Unknown"
    ).strip()
    
    # Job ID and URL
    job_id_lever = job_data.get("id", "")
    url = job_data.get("hostedUrl", "").strip()
    
    # Location
    location = job_data.get("categories", {}).get("location", "")
    if isinstance(location, list):
        location = ", ".join(location).strip()
    elif isinstance(location, str):
        location = location.strip()
    else:
        location = ""
    
    # Description
    description = job_data.get("descriptionPlain", "").strip()
    if not description:
        description = job_data.get("description", "").strip()
    
    # Department/Team
    team = job_data.get("categories", {}).get("team", "")
    if isinstance(team, list):
        department = ", ".join(team).strip()
    elif isinstance(team, str):
        department = team.strip()
    else:
        department = ""
    
    # Employment type
    commitment = job_data.get("categories", {}).get("commitment", "")
    if isinstance(commitment, list):
        employment_type = ", ".join(commitment).strip()
    elif isinstance(commitment, str):
        employment_type = commitment.strip()
    else:
        employment_type = None
    
        # Posted date
        posted_at = None
        if job_data.get("createdAt"):
            try:
                # Lever uses Unix timestamp in milliseconds
                timestamp_ms = job_data["createdAt"]
                posted_at = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                # Convert to naive UTC for consistency with storage
                posted_at = posted_at.replace(tzinfo=None)
            except (ValueError, TypeError, OSError):
                pass
    
    # Generate stable job_id
    job_id = generate_job_id(
        title=title,
        company=company_name,
        source="lever",
        source_id=job_id_lever,
        url=url,
    )
    
    return Job(
        job_id=job_id,
        title=title,
        company=company_name,
        location=location or None,
        description=description or None,
        url=url or None,
        posted_at=posted_at,
        source="lever",
        source_id=job_id_lever,
        department=department or None,
        employment_type=employment_type,
        raw_data=job_data,
    )

