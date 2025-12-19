"""Main entry point for job aggregation pipeline."""

import logging
import sys
from typing import List

from app.config import Config
from app.export.sheets import GoogleSheetsExporter
from app.models import Job
from app.sources.greenhouse import fetch_greenhouse_jobs
from app.sources.lever import fetch_lever_jobs
from app.sources.rss import parse_rss_feed
from app.storage.database import JobDatabase
from app.utils.dedupe import deduplicate_jobs, generate_job_id
from app.utils.freshness import filter_by_freshness


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def collect_jobs() -> List[Job]:
    """Collect jobs from all configured sources."""
    all_jobs = []
    
    logger = logging.getLogger(__name__)
    
    # Collect from RSS feeds
    for feed_url in Config.RSS_FEEDS:
        logger.info(f"Fetching RSS feed: {feed_url}")
        jobs = parse_rss_feed(feed_url)
        all_jobs.extend(jobs)
    
    # Collect from Greenhouse boards
    for board_token in Config.GREENHOUSE_BOARDS:
        logger.info(f"Fetching Greenhouse board: {board_token}")
        jobs = fetch_greenhouse_jobs(board_token)
        all_jobs.extend(jobs)
    
    # Collect from Lever companies
    for company in Config.LEVER_COMPANIES:
        logger.info(f"Fetching Lever company: {company}")
        jobs = fetch_lever_jobs(company)
        all_jobs.extend(jobs)
    
    logger.info(f"Collected {len(all_jobs)} jobs from all sources")
    return all_jobs


def process_jobs(jobs: List[Job]) -> List[Job]:
    """Process jobs: de-duplicate and filter by freshness."""
    logger = logging.getLogger(__name__)
    
    # De-duplicate
    unique_jobs = deduplicate_jobs(jobs)
    logger.info(f"After de-duplication: {len(unique_jobs)} unique jobs")
    
    # Filter by freshness
    fresh_jobs = filter_by_freshness(unique_jobs, max_age_hours=Config.MAX_AGE_HOURS)
    logger.info(f"After freshness filter ({Config.MAX_AGE_HOURS}h): {len(fresh_jobs)} jobs")
    
    return fresh_jobs


def main():
    """Main pipeline execution."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting job aggregation pipeline")
    
    try:
        # Collect jobs from all sources
        all_jobs = collect_jobs()
        
        if not all_jobs:
            logger.warning("No jobs collected from any source")
            return
        
        # Process jobs (de-duplicate and filter)
        processed_jobs = process_jobs(all_jobs)
        
        if not processed_jobs:
            logger.warning("No jobs remaining after processing")
            return
        
        # Store in SQLite (truth source)
        db = JobDatabase()
        inserted, updated = db.upsert_jobs(processed_jobs)
        logger.info(f"Stored jobs in database: {inserted} new, {updated} updated")
        
        # Export to Google Sheets (if configured)
        if Config.GOOGLE_SHEETS_SPREADSHEET_ID:
            try:
                exporter = GoogleSheetsExporter()
                exporter.export_jobs(processed_jobs)
                logger.info("Exported jobs to Google Sheets")
            except Exception as e:
                logger.error(f"Failed to export to Google Sheets: {e}", exc_info=True)
        else:
            logger.info("Google Sheets export skipped (not configured)")
        
        logger.info("Job aggregation pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

