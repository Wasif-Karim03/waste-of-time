"""Greenhouse API client for job listings."""

import logging
from datetime import datetime
from typing import List, Optional

import requests

from app.models import Job
from app.utils.dedupe import generate_job_id

logger = logging.getLogger(__name__)


def fetch_greenhouse_jobs(board_token: str) -> List[Job]:
    """
    Fetch jobs from Greenhouse API for a given board.
    
    Args:
        board_token: Greenhouse board token (e.g., 'companyname')
    
    Returns:
        List of Job objects
    """
    jobs = []
    
    try:
        # Greenhouse public API endpoint
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        for job_data in data.get("jobs", []):
            try:
                job = _parse_greenhouse_job(job_data, board_token)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing Greenhouse job: {e}", exc_info=True)
                continue
        
        logger.info(f"Fetched {len(jobs)} jobs from Greenhouse board: {board_token}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Greenhouse jobs for {board_token}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error with Greenhouse API: {e}", exc_info=True)
    
    return jobs


def _parse_greenhouse_job(job_data: dict, board_token: str) -> Optional[Job]:
    """Parse a Greenhouse job object into a Job."""
    # Extract required fields
    title = job_data.get("title", "").strip()
    if not title:
        return None
    
    # Company name from board token or metadata
    company = (
        job_data.get("company", {}).get("name", "") or
        board_token.replace("-", " ").title() or
        "Unknown"
    ).strip()
    
    # Job ID and URL
    job_id_greenhouse = str(job_data.get("id", ""))
    url = job_data.get("absolute_url", "").strip()
    
    # Location
    locations = job_data.get("locations", [])
    location = ", ".join([loc.get("name", "") for loc in locations if loc.get("name")]).strip()
    
    # Description (content)
    description = job_data.get("content", "").strip()
    
    # Department
    departments = job_data.get("departments", [])
    department = ", ".join([dept.get("name", "") for dept in departments if dept.get("name")]).strip()
    
    # Employment type
    employment_type = None
    # Greenhouse doesn't always provide this, but we can check metadata
    
    # Posted date
    posted_at = None
    if job_data.get("updated_at"):
        try:
            # Greenhouse uses ISO format
            posted_at = datetime.fromisoformat(job_data["updated_at"].replace("Z", "+00:00"))
            if posted_at.tzinfo:
                posted_at = posted_at.replace(tzinfo=None)  # Convert to naive UTC
        except (ValueError, TypeError):
            pass
    
    # Generate stable job_id
    job_id = generate_job_id(
        title=title,
        company=company,
        source="greenhouse",
        source_id=job_id_greenhouse,
        url=url,
    )
    
    return Job(
        job_id=job_id,
        title=title,
        company=company,
        location=location or None,
        description=description or None,
        url=url or None,
        posted_at=posted_at,
        source="greenhouse",
        source_id=job_id_greenhouse,
        department=department or None,
        employment_type=employment_type,
        raw_data=job_data,
    )

