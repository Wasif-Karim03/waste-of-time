"""Job ID generation and de-duplication utilities."""

import hashlib
from typing import List, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from app.core.models import Job


def canonicalize_url(url: str) -> str:
    """
    Canonicalize a URL by stripping tracking parameters, lowercasing host, and removing trailing slashes.
    
    Removes common tracking query parameters:
    - utm_* (utm_source, utm_medium, utm_campaign, etc.)
    - ref, src, source
    - fbclid, gclid, _ga, etc.
    
    Args:
        url: URL string to canonicalize
    
    Returns:
        Canonicalized URL string
    
    Examples:
        >>> canonicalize_url("https://Example.com/jobs/123/?utm_source=linkedin&ref=home")
        'https://example.com/jobs/123'
        
        >>> canonicalize_url("https://company.com/careers/")
        'https://company.com/careers'
        
        >>> canonicalize_url("https://site.com/job?id=123&utm_medium=email&src=newsletter")
        'https://site.com/job?id=123'
        
        >>> # Test stability
        >>> url1 = canonicalize_url("https://Example.com/jobs/?utm_source=test")
        >>> url2 = canonicalize_url("https://example.com/jobs/")
        >>> assert url1 == url2
        >>> assert url1 == "https://example.com/jobs"
    """
    if not url or not url.strip():
        return url
    
    # Parse URL
    parsed = urlparse(url.strip())
    
    # Lowercase the netloc (host)
    netloc = parsed.netloc.lower()
    
    # Remove trailing slash from path
    path = parsed.path.rstrip('/')
    
    # Parse and filter query parameters
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    
    # List of tracking parameter prefixes/names to remove
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'ref', 'src', 'source', 'referrer', 'referer',
        'fbclid', 'gclid', '_ga', '_gid', '_gac',
        'mc_cid', 'mc_eid', 'mkt_tok',
        'igshid', 'twclid',
    }
    
    # Remove tracking parameters
    filtered_params = {
        k: v for k, v in query_params.items()
        if k.lower() not in tracking_params and not k.lower().startswith('utm_')
    }
    
    # Rebuild query string
    query = urlencode(filtered_params, doseq=True) if filtered_params else ''
    
    # Reconstruct URL
    canonical = urlunparse((
        parsed.scheme.lower(),
        netloc,
        path,
        parsed.params,
        query,
        ''  # Remove fragment
    ))
    
    return canonical


def make_job_id(company: str, title: str, url: str) -> str:
    """
    Generate a stable job ID from company, title, and URL.
    
    Returns SHA256 hex digest of normalized strings. The inputs are:
    - Normalized (lowercased, stripped)
    - URL is canonicalized
    - Combined in a deterministic order
    
    Args:
        company: Company name
        title: Job title
        url: Job URL
    
    Returns:
        64-character SHA256 hex digest
    
    Examples:
        >>> # Test stability - same inputs produce same ID
        >>> id1 = make_job_id("Google", "Software Engineer", "https://google.com/jobs/123")
        >>> id2 = make_job_id("google", "software engineer", "https://google.com/jobs/123/")
        >>> assert id1 == id2
        
        >>> # Test that different jobs produce different IDs
        >>> id3 = make_job_id("Google", "Product Manager", "https://google.com/jobs/123")
        >>> assert id1 != id3
        
        >>> # Test URL canonicalization affects ID
        >>> id4 = make_job_id("Google", "Software Engineer", "https://google.com/jobs/123?utm_source=linkedin")
        >>> assert id1 == id4
        
        >>> # Test that order matters (should be deterministic)
        >>> id5 = make_job_id("Company", "Title", "https://example.com/job")
        >>> id6 = make_job_id("Company", "Title", "https://example.com/job")
        >>> assert id5 == id6
        >>> assert len(id5) == 64  # SHA256 produces 64 hex chars
    """
    # Normalize inputs
    company_norm = company.strip().lower() if company else ""
    title_norm = title.strip().lower() if title else ""
    url_norm = canonicalize_url(url) if url else ""
    
    # Combine in deterministic order
    combined = f"{company_norm}|{title_norm}|{url_norm}"
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return hash_obj.hexdigest()


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
    
    This is a legacy function. For new code, prefer make_job_id().
    
    Args:
        title: Job title
        company: Company name
        source: Source identifier
        source_id: Original ID from source (optional)
        url: Job URL (optional, used if source_id not available)
    
    Returns:
        Stable 16-character hex hash
    """
    # Use make_job_id if URL is available, otherwise fall back to old method
    if url:
        return make_job_id(company, title, url)[:16]
    
    # Fallback to old method for backward compatibility
    import json
    
    # Normalize inputs
    title = title.strip().lower()
    company = company.strip().lower()
    source = source.strip().lower()
    
    # Create a stable identifier string
    identifier = source_id if source_id else ""
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


def deduplicate_jobs(jobs: List[Job]) -> List[Job]:
    """
    Remove duplicate jobs based on job_id.
    
    Keeps the first occurrence of each job_id.
    
    Args:
        jobs: List of Job objects
    
    Returns:
        List of unique Job objects
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        if job.job_id not in seen:
            seen.add(job.job_id)
            unique_jobs.append(job)
    
    return unique_jobs
