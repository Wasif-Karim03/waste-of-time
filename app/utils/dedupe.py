"""De-duplication utilities using stable job_id hash."""

import hashlib
import json
from typing import Optional

from app.models import Job


def generate_job_id(
    title: str,
    company: str,
    source: str,
    source_id: Optional[str] = None,
    url: Optional[str] = None,
) -> str:
    """
    Generate stable job_id hash from job attributes.
    
    Uses a combination of title, company, source, and source_id/url
    to create a deterministic hash that identifies the same job
    across different runs.
    """
    # Normalize inputs
    title = title.strip().lower()
    company = company.strip().lower()
    source = source.strip().lower()
    
    # Create a stable identifier string
    # Prefer source_id if available, otherwise use URL
    identifier = source_id if source_id else (url or "")
    identifier = identifier.strip().lower()
    
    # Combine into a stable string
    components = {
        "title": title,
        "company": company,
        "source": source,
        "identifier": identifier,
    }
    
    # Create deterministic JSON string (sorted keys)
    stable_string = json.dumps(components, sort_keys=True, separators=(',', ':'))
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(stable_string.encode('utf-8'))
    return hash_obj.hexdigest()[:16]  # Use first 16 chars for readability


def deduplicate_jobs(jobs: list[Job]) -> list[Job]:
    """
    Remove duplicate jobs based on job_id.
    
    Keeps the first occurrence of each job_id.
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        if job.job_id not in seen:
            seen.add(job.job_id)
            unique_jobs.append(job)
    
    return unique_jobs

