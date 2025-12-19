"""CSV export functionality for jobs."""

import csv
import io
from typing import List

from app.core.models import Job


def export_jobs_to_csv(jobs: List[Job]) -> str:
    """
    Export jobs to CSV format string.
    
    Args:
        jobs: List of Job objects to export
    
    Returns:
        CSV content as string
    
    Examples:
        >>> from datetime import datetime, timezone
        >>> from app.core.ids import make_job_id
        >>> from app.core.models import Job
        >>> 
        >>> job = Job(
        ...     job_id=make_job_id("Company", "Engineer", "https://example.com"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company",
        ...     fetched_at=datetime.now(timezone.utc)
        ... )
        >>> 
        >>> csv_content = export_jobs_to_csv([job])
        >>> assert "title" in csv_content
        >>> assert "company" in csv_content
        >>> assert "Engineer" in csv_content
    """
    if not jobs:
        return ""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        "title",
        "company",
        "remote?",
        "URL",
        "tags",
    ]
    writer.writerow(headers)
    
    # Write job rows
    for job in jobs:
        # Format Tags as comma-separated string
        tags_str = ", ".join(job.tags) if job.tags else ""
        
        # Format Remote as Yes/No
        remote_str = "Yes" if job.remote else "No"
        
        # URL
        url_str = job.url or ""
        
        row = [
            job.title,
            job.company,
            remote_str,
            url_str,
            tags_str,
        ]
        writer.writerow(row)
    
    return output.getvalue()


def export_jobs_to_csv_file(jobs: List[Job], filepath: str) -> None:
    """
    Export jobs to CSV file.
    
    Args:
        jobs: List of Job objects to export
        filepath: Path to output CSV file
    """
    csv_content = export_jobs_to_csv(jobs)
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        f.write(csv_content)

