"""RSS feed parser for job listings."""

import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import feedparser

from app.models import Job
from app.utils.dedupe import generate_job_id

logger = logging.getLogger(__name__)


def parse_rss_feed(feed_url: str) -> List[Job]:
    """
    Parse RSS feed and extract job listings.
    
    Returns list of Job objects from the feed.
    """
    jobs = []
    
    try:
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"RSS feed parse error for {feed_url}: {feed.bozo_exception}")
            return jobs
        
        for entry in feed.entries:
            try:
                job = _parse_rss_entry(entry, feed_url)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing RSS entry: {e}", exc_info=True)
                continue
        
        logger.info(f"Parsed {len(jobs)} jobs from RSS feed: {feed_url}")
        
    except Exception as e:
        logger.error(f"Error fetching RSS feed {feed_url}: {e}", exc_info=True)
    
    return jobs


def _parse_rss_entry(entry: dict, feed_url: str) -> Optional[Job]:
    """Parse a single RSS entry into a Job object."""
    # Extract title
    title = entry.get("title", "").strip()
    if not title:
        return None
    
    # Extract company - try multiple fields
    company = (
        entry.get("author", "") or
        entry.get("source", {}).get("title", "") or
        _extract_company_from_title(title) or
        _extract_company_from_url(entry.get("link", "")) or
        "Unknown"
    ).strip()
    
    # Extract URL
    url = entry.get("link", "").strip()
    
    # Extract description
    description = (
        entry.get("description", "") or
        entry.get("summary", "") or
        entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
    ).strip()
    
    # Extract location - try multiple fields
    location = (
        entry.get("location", "") or
        _extract_location_from_description(description) or
        ""
    ).strip()
    
    # Parse posted date
    posted_at = None
    if entry.get("published_parsed"):
        try:
            posted_at = datetime(*entry.published_parsed[:6])
        except (ValueError, TypeError):
            pass
    elif entry.get("updated_parsed"):
        try:
            posted_at = datetime(*entry.updated_parsed[:6])
        except (ValueError, TypeError):
            pass
    
    # Generate stable job_id
    source_id = entry.get("id", url)
    job_id = generate_job_id(
        title=title,
        company=company,
        source="rss",
        source_id=source_id,
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
        source="rss",
        source_id=source_id,
        raw_data={
            "feed_url": feed_url,
            "entry": dict(entry),
        },
    )


def _extract_company_from_title(title: str) -> Optional[str]:
    """Try to extract company name from job title (e.g., 'Software Engineer at Google')."""
    # Common patterns: "Title at Company", "Company - Title", "Title | Company"
    for separator in [" at ", " - ", " | "]:
        if separator in title:
            parts = title.split(separator, 1)
            if len(parts) == 2:
                # Could be either direction, try both
                if separator == " at ":
                    return parts[1].strip()
                else:
                    return parts[0].strip()
    return None


def _extract_company_from_url(url: str) -> Optional[str]:
    """Extract company name from URL domain."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. and extract first part
        domain = domain.replace("www.", "")
        parts = domain.split(".")
        if parts:
            return parts[0].capitalize()
    except Exception:
        pass
    return None


def _extract_location_from_description(description: str) -> Optional[str]:
    """Try to extract location from description text."""
    # Simple pattern matching for common location formats
    # This is a basic implementation - can be enhanced
    if not description:
        return None
    
    # Look for patterns like "Location: City, State" or "Remote" or "San Francisco, CA"
    description_lower = description.lower()
    
    if "remote" in description_lower:
        return "Remote"
    
    # Could add more sophisticated parsing here
    return None

