"""Handshake RSS feed connector.

Note: Handshake may not provide public RSS feeds. This connector attempts
to find RSS feeds but may not work. Handshake is primarily a student/university
platform, so API access may require institutional credentials.
"""

import logging
from typing import Dict, List

import feedparser
import requests

from app.config import Settings

logger = logging.getLogger(__name__)


def fetch(settings: Settings) -> List[Dict]:
    """
    Fetch raw job entries from Handshake RSS feeds.
    
    Note: Handshake typically requires university/institutional access.
    This connector will try URLs but may return empty results.
    
    Args:
        settings: Settings object containing HANDSHAKE_RSS_URLS
    
    Returns:
        List of raw entry dicts with keys:
        - source: str (always "handshake_rss")
        - title: str
        - url: str
        - company: str (optional)
        - location: str (optional)
        - published: str (optional, ISO format string)
        - published_parsed: tuple (optional, time.struct_time)
        - raw_entry: dict (original feedparser entry)
    """
    entries = []
    
    if not settings.HANDSHAKE_RSS_URLS:
        logger.info("No Handshake RSS URLs configured")
        return entries
    
    for feed_url in settings.HANDSHAKE_RSS_URLS:
        if not feed_url or not feed_url.strip():
            continue
        
        feed_url = feed_url.strip()
        logger.info(f"Fetching Handshake RSS feed: {feed_url}")
        
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
                    f"Handshake RSS feed parse error for {feed_url}: {feed.bozo_exception}"
                )
            
            # Process each entry
            for entry in feed.entries:
                try:
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
                    
                    entry_dict = {
                        "source": "handshake_rss",
                        "title": entry.get("title", "").strip(),
                        "url": entry.get("link", "").strip(),
                        "company": None,
                        "location": None,
                        "description": description,
                        "published": entry.get("published", ""),
                        "published_parsed": entry.get("published_parsed"),
                        "raw_entry": dict(entry),
                    }
                    
                    # Extract company/location from title if available
                    title = entry_dict["title"]
                    if " at " in title:
                        parts = title.split(" at ", 1)
                        if len(parts) == 2:
                            entry_dict["company"] = parts[1].strip()
                    
                    if entry_dict["title"] and entry_dict["url"]:
                        entries.append(entry_dict)
                    else:
                        logger.warning(f"Skipping Handshake entry missing title or URL")
                        
                except Exception as e:
                    logger.error(
                        f"Error processing Handshake RSS entry from {feed_url}: {e}",
                        exc_info=True
                    )
                    continue
            
            logger.info(
                f"Fetched {len([e for e in entries if e.get('source') == 'handshake_rss'])} "
                f"entries from Handshake RSS feed: {feed_url}"
            )

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching Handshake RSS feed {feed_url}: {e}",
                exc_info=True
            )
            continue
        except Exception as e:
            logger.error(
                f"Unexpected error with Handshake RSS feed {feed_url}: {e}",
                exc_info=True
            )
            continue
    
    logger.info(f"Total Handshake RSS entries fetched: {len(entries)}")
    return entries

