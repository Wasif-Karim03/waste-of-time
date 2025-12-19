"""Greenhouse API connector."""

import logging
from typing import Dict, List

import requests

from app.config import Settings

logger = logging.getLogger(__name__)


def fetch(settings: Settings) -> List[Dict]:
    """
    Fetch raw job entries from Greenhouse API.
    
    Args:
        settings: Settings object containing GREENHOUSE_BOARDS
    
    Returns:
        List of raw entry dicts with keys:
        - source: str (always "greenhouse")
        - title: str
        - url: str
        - company: str (board slug)
        - location: str (optional)
        - updated_at: str (optional, ISO format)
        - created_at: str (optional, ISO format)
        - raw: dict (original API response)
    
    Examples:
        >>> from app.config import Settings
        >>> settings = Settings(GREENHOUSE_BOARDS=["companyname"])
        >>> entries = fetch(settings)
        >>> # Returns list of dicts, each with required keys
        >>> assert isinstance(entries, list)
        >>> if entries:
        ...     assert "source" in entries[0]
        ...     assert "title" in entries[0]
        ...     assert "url" in entries[0]
    """
    entries = []
    
    if not settings.GREENHOUSE_BOARDS:
        logger.info("No Greenhouse boards configured")
        return entries
    
    for board_slug in settings.GREENHOUSE_BOARDS:
        if not board_slug or not board_slug.strip():
            continue
        
        board_slug = board_slug.strip()
        logger.info(f"Fetching Greenhouse board: {board_slug}")
        
        try:
            # Call Greenhouse API
            url = f"https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Process each job
            for job_data in data.get("jobs", []):
                try:
                    entry_dict = _extract_entry(job_data, board_slug)
                    if entry_dict:
                        entries.append(entry_dict)
                except Exception as e:
                    logger.error(
                        f"Error processing Greenhouse job from {board_slug}: {e}",
                        exc_info=True
                    )
                    # Continue processing other jobs
                    continue
            
            logger.info(
                f"Fetched {len([e for e in entries if e.get('source') == 'greenhouse' and e.get('company') == board_slug])} "
                f"entries from Greenhouse board: {board_slug}"
            )
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching Greenhouse board {board_slug} (10s timeout)")
            # Continue to next board
            continue
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching Greenhouse board {board_slug}: {e}",
                exc_info=True
            )
            # Continue to next board
            continue
        except Exception as e:
            logger.error(
                f"Unexpected error with Greenhouse API for {board_slug}: {e}",
                exc_info=True
            )
            # Continue to next board
            continue
    
    logger.info(f"Total Greenhouse entries fetched: {len(entries)}")
    return entries


def _extract_entry(job_data: Dict, board_slug: str) -> Dict:
    """
    Extract entry data from Greenhouse API job object.
    
    Args:
        job_data: Greenhouse job dict from API
        board_slug: Board slug (used as company name)
    
    Returns:
        Dict with required keys, or None if job is invalid
    """
    # Extract title (required)
    title = job_data.get("title", "").strip()
    if not title:
        logger.debug(f"Skipping Greenhouse job without title from {board_slug}")
        return None
    
    # Extract URL (required)
    url = job_data.get("absolute_url", "").strip()
    if not url:
        logger.debug(f"Skipping Greenhouse job without URL from {board_slug}")
        return None
    
    # Extract location (optional)
    locations = job_data.get("locations", [])
    location = None
    if locations:
        location_names = [loc.get("name", "").strip() for loc in locations if loc.get("name")]
        location = ", ".join(location_names).strip() or None
    
    # Extract dates (optional)
    updated_at = job_data.get("updated_at")
    created_at = job_data.get("created_at")
    
    # Extract description (optional)
    description = None
    # Greenhouse API may have content or description fields
    if job_data.get("content"):
        description = job_data["content"].strip()
    elif job_data.get("description"):
        description = job_data["description"].strip()
    
    # Build entry dict
    entry_dict = {
        "source": "greenhouse",
        "title": title,
        "url": url,
        "company": board_slug,
        "location": location,
        "description": description,
        "updated_at": updated_at,
        "created_at": created_at,
        "raw": job_data,  # Store original API response
    }
    
    return entry_dict


# Legacy function for backward compatibility
def fetch_greenhouse_jobs(board_tokens: List[str]) -> List:
    """
    Legacy function for backward compatibility.
    
    Returns empty list. Use fetch(settings) instead.
    """
    logger.warning(
        "fetch_greenhouse_jobs() is deprecated. Use fetch(settings) instead."
    )
    return []
