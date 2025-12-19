"""Main entry point for job aggregation pipeline."""

import argparse
import logging
import os
import sys

from app.config import get_settings
from app.connectors.greenhouse import fetch as fetch_greenhouse
from app.connectors.indeed_rss import fetch as fetch_indeed
from app.connectors.lever import fetch as fetch_lever
from app.connectors.linkedin_rss import fetch as fetch_linkedin
from app.connectors.glassdoor_rss import fetch as fetch_glassdoor
from app.connectors.handshake_rss import fetch as fetch_handshake
from app.core.freshness import filter_fresh
from app.core.ids import deduplicate_jobs
from app.core.keywords import sort_jobs, tag_job
from app.core.normalize import normalize_all
from app.storage.sheets_store import export_to_google_sheets
from app.storage.sqlite_store import init_db, load_recent, upsert_jobs


def setup_logging():
    """Configure logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Job aggregation pipeline - collect and process job listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.main
  python -m app.main --max-age-hours 48
  python -m app.main --export
  python -m app.main --dry-run
        """
    )
    
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=None,
        help="Override MAX_AGE_HOURS from config (default: use config value, typically 24)"
    )
    
    parser.add_argument(
        "--export",
        action="store_true",
        help="Force export to Google Sheets even if no new jobs were processed"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without writing to database or exporting to Sheets"
    )
    
    return parser.parse_args()


def main():
    """Main pipeline execution."""
    # Parse command-line arguments
    args = parse_args()
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load Settings
    settings = get_settings()
    
    # Override max_age_hours if provided via CLI
    if args.max_age_hours is not None:
        if args.max_age_hours <= 0:
            logger.error(f"Invalid --max-age-hours: {args.max_age_hours}. Must be positive.")
            sys.exit(1)
        settings.MAX_AGE_HOURS = args.max_age_hours
        logger.info(f"Using --max-age-hours override: {args.max_age_hours}")
    
    # Log dry-run mode
    if args.dry_run:
        logger.info("DRY-RUN MODE: No database writes or Sheets export will be performed")
    
    logger.info("Starting job aggregation pipeline")
    
    # Track statistics
    stats = {
        "fetched": 0,
        "normalized": 0,
        "fresh": 0,
        "inserted": 0,
        "updated": 0,
        "exported": 0,
    }
    
    try:
        # Initialize database (skip in dry-run)
        if not args.dry_run:
            logger.info(f"Initializing database: {settings.SQLITE_PATH}")
            init_db(settings.SQLITE_PATH)
        else:
            logger.info(f"[DRY-RUN] Would initialize database: {settings.SQLITE_PATH}")
        
        # Fetch raw items from each enabled connector
        all_raw_items = []
        
        # LinkedIn RSS
        if settings.LINKEDIN_RSS_URLS:
            logger.info(f"Fetching LinkedIn RSS: {len(settings.LINKEDIN_RSS_URLS)} feeds")
            raw_items = fetch_linkedin(settings)
            all_raw_items.extend(raw_items)
            logger.info(f"Fetched {len(raw_items)} LinkedIn RSS entries")
        
        # Indeed RSS
        if settings.INDEED_RSS_URLS:
            logger.info(f"Fetching Indeed RSS: {len(settings.INDEED_RSS_URLS)} feeds")
            raw_items = fetch_indeed(settings)
            all_raw_items.extend(raw_items)
            logger.info(f"Fetched {len(raw_items)} Indeed RSS entries")
        
        # Greenhouse
        if settings.GREENHOUSE_BOARDS:
            logger.info(f"Fetching Greenhouse: {len(settings.GREENHOUSE_BOARDS)} boards")
            raw_items = fetch_greenhouse(settings)
            all_raw_items.extend(raw_items)
            logger.info(f"Fetched {len(raw_items)} Greenhouse entries")
        
        # Lever
        if settings.LEVER_COMPANIES:
            logger.info(f"Fetching Lever: {len(settings.LEVER_COMPANIES)} companies")
            raw_items = fetch_lever(settings)
            all_raw_items.extend(raw_items)
            logger.info(f"Fetched {len(raw_items)} Lever entries")
        
        # Glassdoor RSS
        if settings.GLASSDOOR_RSS_URLS:
            logger.info(f"Fetching Glassdoor RSS: {len(settings.GLASSDOOR_RSS_URLS)} feeds")
            raw_items = fetch_glassdoor(settings)
            all_raw_items.extend(raw_items)
            logger.info(f"Fetched {len(raw_items)} Glassdoor RSS entries")
        
        # Handshake RSS
        if settings.HANDSHAKE_RSS_URLS:
            logger.info(f"Fetching Handshake RSS: {len(settings.HANDSHAKE_RSS_URLS)} feeds")
            raw_items = fetch_handshake(settings)
            all_raw_items.extend(raw_items)
            logger.info(f"Fetched {len(raw_items)} Handshake RSS entries")
        
        stats["fetched"] = len(all_raw_items)
        
        if not all_raw_items:
            logger.warning("No raw items fetched from any source")
            _print_summary(stats)
            return
        
        # Normalize all to Job objects
        logger.info(f"Normalizing {len(all_raw_items)} raw items")
        jobs = normalize_all(all_raw_items)
        stats["normalized"] = len(jobs)
        
        # TEMPORARY: Log first 5 jobs for freshness validation
        if jobs:
            print("\n" + "=" * 60)
            print("TEMPORARY: First 5 jobs for freshness validation")
            print("=" * 60)
            for j in jobs[:5]:
                print(f"Title: {j.title}")
                print(f"Posted at: {j.posted_at}")
                print(f"URL: {j.url}")
                print(f"Source: {j.source}")
                print("-" * 60)
            print("=" * 60 + "\n")
        
        if not jobs:
            logger.warning("No jobs after normalization")
            _print_summary(stats)
            return
        
        # Tag jobs with keywords
        if settings.KEYWORDS:
            logger.info(f"Tagging jobs with {len(settings.KEYWORDS)} keywords")
            jobs = [tag_job(job, settings.KEYWORDS) for job in jobs]
        else:
            logger.info("No keywords configured, skipping tagging")
        
        # Filter fresh (<= MAX_AGE_HOURS)
        logger.info(f"Filtering jobs by freshness (max age: {settings.MAX_AGE_HOURS} hours)")
        fresh_jobs = filter_fresh(jobs, settings.MAX_AGE_HOURS)
        stats["fresh"] = len(fresh_jobs)
        
        if not fresh_jobs:
            logger.warning("No fresh jobs remaining after filtering")
            _print_summary(stats)
            return
        
        # Dedupe by job_id (set)
        logger.info("Deduplicating jobs by job_id")
        unique_jobs = deduplicate_jobs(fresh_jobs)
        logger.info(f"After deduplication: {len(unique_jobs)} unique jobs (removed {len(fresh_jobs) - len(unique_jobs)} duplicates)")
        
        if not unique_jobs:
            logger.warning("No unique jobs remaining after deduplication")
            _print_summary(stats)
            return
        
        # Upsert into SQLite (skip in dry-run)
        if not args.dry_run:
            logger.info(f"Upserting {len(unique_jobs)} jobs into SQLite")
            inserted, updated = upsert_jobs(settings.SQLITE_PATH, unique_jobs)
            stats["inserted"] = inserted
            stats["updated"] = updated
        else:
            logger.info(f"[DRY-RUN] Would upsert {len(unique_jobs)} jobs into SQLite")
            stats["inserted"] = len(unique_jobs)  # Estimate for dry-run
            stats["updated"] = 0
        
        # Load recent and sort by score desc then posted_at desc
        if not args.dry_run:
            logger.info("Loading recent jobs for export")
            recent_jobs = load_recent(settings.SQLITE_PATH, since_hours=settings.MAX_AGE_HOURS)
            logger.info(f"Loaded {len(recent_jobs)} recent jobs")
        else:
            # In dry-run, use the current unique_jobs as "recent"
            logger.info("[DRY-RUN] Using current jobs for export (no database read)")
            recent_jobs = unique_jobs
        
        if recent_jobs:
            sorted_jobs = sort_jobs(recent_jobs)
            logger.info(f"Sorted {len(sorted_jobs)} jobs by score and posted_at")
        else:
            sorted_jobs = []
        
        # Export to Google Sheets (optional, skip in dry-run)
        if args.dry_run:
            if sorted_jobs:
                logger.info(f"[DRY-RUN] Would export {len(sorted_jobs)} jobs to Google Sheets")
            else:
                logger.info("[DRY-RUN] No jobs to export")
        elif args.export or sorted_jobs:
            # Export if --export flag is set OR if we have sorted jobs
            jobs_to_export = sorted_jobs if sorted_jobs else recent_jobs
            if jobs_to_export:
                logger.info("Exporting to Google Sheets")
                try:
                    export_to_google_sheets(settings, jobs_to_export)
                    stats["exported"] = len(jobs_to_export)
                    logger.info(f"Exported {len(jobs_to_export)} jobs to Google Sheets")
                except Exception as e:
                    logger.error(f"Failed to export to Google Sheets: {e}", exc_info=True)
            else:
                if args.export:
                    logger.info("--export flag set but no jobs available to export")
                else:
                    logger.info("No jobs to export")
        else:
            logger.info("No jobs to export")
        
        # Print summary
        _print_summary(stats)
        logger.info("Job aggregation pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        _print_summary(stats)
        sys.exit(1)


def _print_summary(stats: dict) -> None:
    """Print a short summary of pipeline execution."""
    print("\n" + "=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    print(f"Fetched:        {stats['fetched']:>6}")
    print(f"Normalized:     {stats['normalized']:>6}")
    print(f"Fresh:          {stats['fresh']:>6}")
    print(f"Inserted:       {stats['inserted']:>6}")
    print(f"Updated:        {stats['updated']:>6}")
    print(f"Exported:       {stats['exported']:>6}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
