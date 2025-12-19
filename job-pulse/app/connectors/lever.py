"""Lever API connector."""

import logging
from typing import Dict, List

import requests

from app.config import Settings

logger = logging.getLogger(__name__)


def fetch(settings: Settings) -> List[Dict]:
    """
    Fetch raw job entries from Lever API.
    
    Args:
        settings: Settings object containing LEVER_COMPANIES
    
    Returns:
        List of raw entry dicts with keys:
        - source: str (always "lever")
        - title: str
        - url: str (hostedUrl)
        - company: str
        - location: str (optional)
        - createdAt: int (milliseconds epoch timestamp)
        - raw: dict (original API response)
    
    Examples:
        >>> from app.config import Settings
        >>> settings = Settings(LEVER_COMPANIES=["companyname"])
        >>> entries = fetch(settings)
        >>> # Returns list of dicts, each with required keys
        >>> assert isinstance(entries, list)
        >>> if entries:
        ...     assert "source" in entries[0]
        ...     assert "title" in entries[0]
        ...     assert "url" in entries[0]
        ...     assert "createdAt" in entries[0]
    """
    entries = []
    
    if not settings.LEVER_COMPANIES:
        logger.info("No Lever companies configured")
        return entries
    
    for company in settings.LEVER_COMPANIES:
        if not company or not company.strip():
            continue
        
        company = company.strip()
        logger.info(f"Fetching Lever company: {company}")
        
        try:
            # Call Lever API
            url = f"https://api.lever.co/v0/postings/{company}?mode=json"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process each job (Lever API returns a list directly)
            for job_data in data:
                try:
                    entry_dict = _extract_entry(job_data, company)
                    if entry_dict:
                        entries.append(entry_dict)
                except Exception as e:
                    logger.error(
                        f"Error processing Lever job from {company}: {e}",
                        exc_info=True
                    )
                    # Continue processing other jobs
                    continue
            
            logger.info(
                f"Fetched {len([e for e in entries if e.get('source') == 'lever' and e.get('company') == company])} "
                f"entries from Lever company: {company}"
            )
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching Lever company {company} (10s timeout)")
            # Continue to next company
            continue
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching Lever company {company}: {e}",
                exc_info=True
            )
            # Continue to next company
            continue
        except Exception as e:
            logger.error(
                f"Unexpected error with Lever API for {company}: {e}",
                exc_info=True
            )
            # Continue to next company
            continue
    
    logger.info(f"Total Lever entries fetched: {len(entries)}")
    return entries


def _extract_entry(job_data: Dict, company: str) -> Dict:
    """
    Extract entry data from Lever API job object.
    
    Args:
        job_data: Lever job dict from API
        company: Company identifier
    
    Returns:
        Dict with required keys, or None if job is invalid
    """
    # Extract title (required)
    title = job_data.get("text", "").strip()
    if not title:
        logger.debug(f"Skipping Lever job without title from {company}")
        return None
    
    # Extract URL (required) - use hostedUrl
    url = job_data.get("hostedUrl", "").strip()
    if not url:
        logger.debug(f"Skipping Lever job without URL from {company}")
        return None
    
    # Extract location (optional)
    location = None
    categories = job_data.get("categories", {})
    if isinstance(categories, dict):
        location_field = categories.get("location")
        if location_field:
            if isinstance(location_field, list):
                location_names = [loc.strip() for loc in location_field if loc and loc.strip()]
                location = ", ".join(location_names).strip() or None
            elif isinstance(location_field, str):
                location = location_field.strip() or None
    
    # Extract createdAt (required) - milliseconds epoch timestamp
    createdAt = job_data.get("createdAt")
    if createdAt is None:
        logger.debug(f"Skipping Lever job without createdAt from {company}")
        return None
    
    # Extract description (optional)
    description = None
    # Lever API may have descriptionTextHtml, descriptionPlain, or lists.content fields
    if job_data.get("descriptionPlain"):
        description = job_data["descriptionPlain"].strip()
    elif job_data.get("descriptionTextHtml"):
        # Strip HTML tags for plain text
        import re
        description = re.sub(r'<[^>]+>', '', job_data["descriptionTextHtml"]).strip()
    elif job_data.get("lists"):
        # Try to extract from lists content
        lists = job_data.get("lists", [])
        if isinstance(lists, list) and lists:
            content_parts = []
            for item in lists:
                if isinstance(item, dict) and item.get("content"):
                    content_parts.append(str(item["content"]).strip())
            if content_parts:
                description = "\n".join(content_parts).strip()
    
    # Build entry dict
    entry_dict = {
        "source": "lever",
        "title": title,
        "url": url,
        "company": company,
        "location": location,
        "description": description,
        "createdAt": createdAt,  # milliseconds epoch timestamp
        "raw": job_data,  # Store original API response
    }
    
    return entry_dict


# Legacy function for backward compatibility
def fetch_lever_jobs(companies: List[str]) -> List:
    """
    Legacy function for backward compatibility.
    
    Returns empty list. Use fetch(settings) instead.
    """
    logger.warning(
        "fetch_lever_jobs() is deprecated. Use fetch(settings) instead."
    )
    return []
