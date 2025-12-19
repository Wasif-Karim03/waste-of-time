"""LinkedIn RSS feed connector."""

import logging
from typing import Dict, List

import feedparser
import requests

from app.config import Settings

logger = logging.getLogger(__name__)


def fetch(settings: Settings) -> List[Dict]:
    """
    Fetch raw job entries from LinkedIn RSS feeds.
    
    Args:
        settings: Settings object containing LINKEDIN_RSS_URLS
    
    Returns:
        List of raw entry dicts with keys:
        - source: str (always "linkedin_rss")
        - title: str
        - url: str
        - company: str (optional)
        - location: str (optional)
        - published: str (optional, ISO format string)
        - published_parsed: tuple (optional, time.struct_time)
        - raw_entry: dict (original feedparser entry)
    
    Examples:
        >>> from app.config import Settings
        >>> settings = Settings(LINKEDIN_RSS_URLS=["https://example.com/feed.xml"])
        >>> entries = fetch(settings)
        >>> # Returns list of dicts, each with required keys
        >>> assert isinstance(entries, list)
        >>> if entries:
        ...     assert "source" in entries[0]
        ...     assert "title" in entries[0]
        ...     assert "url" in entries[0]
    """
    entries = []
    
    if not settings.LINKEDIN_RSS_URLS:
        logger.info("No LinkedIn RSS URLs configured")
        return entries
    
    for feed_url in settings.LINKEDIN_RSS_URLS:
        if not feed_url or not feed_url.strip():
            continue
        
        feed_url = feed_url.strip()
        logger.info(f"Fetching LinkedIn RSS feed: {feed_url}")
        
        try:
            # Fetch RSS feed with User-Agent header
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed content
            feed = feedparser.parse(response.content)
            
            # Check for parse errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    f"LinkedIn RSS feed parse error for {feed_url}: {feed.bozo_exception}"
                )
                # Continue to next feed even if this one has parse errors
                # Some entries might still be valid
            
            # Process each entry
            for entry in feed.entries:
                try:
                    entry_dict = _extract_entry(entry, feed_url)
                    if entry_dict:
                        entries.append(entry_dict)
                except Exception as e:
                    logger.error(
                        f"Error processing LinkedIn RSS entry from {feed_url}: {e}",
                        exc_info=True
                    )
                    # Continue processing other entries
                    continue
            
            logger.info(
                f"Fetched {len([e for e in entries if e.get('source') == 'linkedin_rss'])} "
                f"entries from LinkedIn RSS feed: {feed_url}"
            )

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching LinkedIn RSS feed {feed_url}: {e}",
                exc_info=True
            )
            # Continue to next feed
            continue
        except Exception as e:
            logger.error(
                f"Unexpected error with LinkedIn RSS feed {feed_url}: {e}",
                exc_info=True
            )
            # Continue to next feed
            continue
    
    logger.info(f"Total LinkedIn RSS entries fetched: {len(entries)}")
    return entries


def _extract_entry(entry: Dict, feed_url: str) -> Dict:
    """
    Extract entry data from feedparser entry.
    
    Args:
        entry: feedparser entry dict
        feed_url: URL of the feed (for logging)
    
    Returns:
        Dict with required keys, or None if entry is invalid
    """
    # Extract title (required)
    title = entry.get("title", "").strip()
    if not title:
        logger.debug(f"Skipping entry without title from {feed_url}")
        return None
    
    # Extract URL (required)
    url = entry.get("link", "").strip()
    if not url:
        logger.debug(f"Skipping entry without URL from {feed_url}")
        return None
    
    # Extract company (optional)
    company = None
    # Try multiple fields for company
    company_candidates = [
        entry.get("author", ""),
        entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else "",
    ]
    for candidate in company_candidates:
        if candidate and candidate.strip():
            company = candidate.strip()
            break
    
    # Extract location (optional)
    location = None
    # Try multiple fields for location
    location_candidates = [
        entry.get("location", ""),
        entry.get("geo", {}).get("name", "") if isinstance(entry.get("geo"), dict) else "",
    ]
    for candidate in location_candidates:
        if candidate and candidate.strip():
            location = candidate.strip()
            break
    
    # Extract published date (optional)
    published = None
    published_parsed = None
    
    if entry.get("published"):
        published = entry["published"]
        published_parsed = entry.get("published_parsed")
    elif entry.get("updated"):
        published = entry["updated"]
        published_parsed = entry.get("updated_parsed")
    
    # Extract description (optional)
    description = None
    # Try multiple fields - feedparser uses different field names
    description_candidates = [
        entry.get("summary", ""),
        entry.get("description", ""),
        entry.get("content", [{}])[0].get("value", "") if entry.get("content") and isinstance(entry.get("content"), list) else "",
    ]
    for candidate in description_candidates:
        if candidate and candidate.strip():
            description = candidate.strip()
            break
    
    # If still no description, try to get from raw entry structure
    if not description:
        raw_entry = dict(entry)
        if raw_entry.get("summary_detail", {}).get("value"):
            description = raw_entry["summary_detail"]["value"].strip()
        elif raw_entry.get("description_detail", {}).get("value"):
            description = raw_entry["description_detail"]["value"].strip()
    
    # Strip HTML tags from description if present
    if description:
        import re
        # Remove HTML tags
        description = re.sub(r'<[^>]+>', '', description)
        # Clean up extra whitespace
        description = re.sub(r'\s+', ' ', description).strip()
    
    # Build entry dict
    entry_dict = {
        "source": "linkedin_rss",
        "title": title,
        "url": url,
        "company": company,
        "location": location,
        "description": description,
        "published": published,
        "published_parsed": published_parsed,
        "raw_entry": dict(entry),  # Store original entry for reference
    }
    
    return entry_dict


# Legacy function for backward compatibility
def fetch_linkedin_jobs(feed_urls: List[str]) -> List:
    """
    Legacy function for backward compatibility.
    
    Returns empty list. Use fetch(settings) instead.
    """
    logger.warning(
        "fetch_linkedin_jobs() is deprecated. Use fetch(settings) instead."
    )
    return []
