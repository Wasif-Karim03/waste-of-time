"""SQLite database storage for jobs."""

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from app.core.models import Job

logger = logging.getLogger(__name__)


def init_db(sqlite_path: str) -> None:
    """
    Initialize the SQLite database and create jobs table.
    
    Creates a jobs table with columns matching Job fields:
    - job_id (TEXT PRIMARY KEY)
    - source (TEXT NOT NULL)
    - title (TEXT NOT NULL)
    - company (TEXT NOT NULL)
    - location (TEXT)
    - remote (INTEGER, 0 or 1)
    - url (TEXT)
    - posted_at (TEXT ISO format)
    - fetched_at (TEXT ISO format)
    - tags (TEXT JSON)
    - raw (TEXT JSON)
    
    Args:
        sqlite_path: Path to SQLite database file
    
    Examples:
        >>> init_db("test.db")
        >>> # Table should be created
    """
    # Ensure directory exists
    db_file = Path(sqlite_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(sqlite_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                remote INTEGER NOT NULL DEFAULT 0,
                url TEXT,
                posted_at TEXT,
                fetched_at TEXT NOT NULL,
                tags TEXT,
                raw TEXT
            )
        """)
        
        # Create indexes for common queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posted_at ON jobs(posted_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fetched_at ON jobs(fetched_at)")
        
        conn.commit()
        logger.info(f"Database initialized at {sqlite_path}")
    finally:
        conn.close()


def upsert_jobs(sqlite_path: str, jobs: List[Job]) -> tuple[int, int]:
    """
    Insert or update jobs in the database.
    
    Uses ON CONFLICT to update existing jobs. Updates only if the new job
    has a newer fetched_at timestamp, or if tags/raw/posted_at are newer.
    
    Args:
        sqlite_path: Path to SQLite database file
        jobs: List of Job objects to upsert
    
    Returns:
        Tuple of (inserted_count, updated_count)
    
    Examples:
        >>> from datetime import datetime, timezone
        >>> from app.core.ids import make_job_id
        >>> from app.core.models import Job
        >>> 
        >>> init_db("test.db")
        >>> 
        >>> job = Job(
        ...     job_id=make_job_id("Company", "Engineer", "https://example.com"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company",
        ...     fetched_at=datetime.now(timezone.utc)
        ... )
        >>> 
        >>> inserted, updated = upsert_jobs("test.db", [job])
        >>> assert inserted == 1
        >>> assert updated == 0
        >>> 
        >>> # Upsert again - should update
        >>> inserted2, updated2 = upsert_jobs("test.db", [job])
        >>> assert inserted2 == 0
        >>> assert updated2 == 1
    """
    if not jobs:
        return 0, 0
    
    # Ensure database is initialized
    init_db(sqlite_path)
    
    conn = sqlite3.connect(sqlite_path)
    inserted = 0
    updated = 0
    
    try:
        for job in jobs:
            # Serialize data
            posted_at_str = job.posted_at.isoformat() if job.posted_at else None
            fetched_at_str = job.fetched_at.isoformat() if job.fetched_at else datetime.now(timezone.utc).isoformat()
            tags_json = json.dumps(job.tags) if job.tags else None
            raw_json = json.dumps(job.raw) if job.raw else None
            
            # Check if job exists
            cursor = conn.execute(
                "SELECT fetched_at FROM jobs WHERE job_id = ?",
                (job.job_id,)
            )
            existing = cursor.fetchone()
            is_new = existing is None
            
            if is_new:
                # New job - insert
                conn.execute("""
                    INSERT INTO jobs (
                        job_id, source, title, company, location, remote, url,
                        posted_at, fetched_at, tags, raw
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.job_id,
                    job.source,
                    job.title,
                    job.company,
                    job.location,
                    1 if job.remote else 0,
                    job.url,
                    posted_at_str,
                    fetched_at_str,
                    tags_json,
                    raw_json,
                ))
                inserted += 1
            else:
                # Existing job - check if we should update
                existing_fetched_at = existing[0]
                should_update = False
                
                if existing_fetched_at:
                    try:
                        existing_dt = datetime.fromisoformat(existing_fetched_at.replace('Z', '+00:00'))
                        new_dt = datetime.fromisoformat(fetched_at_str.replace('Z', '+00:00'))
                        # Update if new fetched_at is newer
                        should_update = new_dt > existing_dt
                    except (ValueError, TypeError):
                        # If parsing fails, update anyway
                        should_update = True
                else:
                    # No existing fetched_at, update
                    should_update = True
                
                if should_update:
                    # Update with ON CONFLICT
                    conn.execute("""
                        INSERT INTO jobs (
                            job_id, source, title, company, location, remote, url,
                            posted_at, fetched_at, tags, raw
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(job_id) DO UPDATE SET
                            source = excluded.source,
                            title = excluded.title,
                            company = excluded.company,
                            location = excluded.location,
                            remote = excluded.remote,
                            url = excluded.url,
                            posted_at = COALESCE(excluded.posted_at, jobs.posted_at),
                            fetched_at = excluded.fetched_at,
                            tags = excluded.tags,
                            raw = excluded.raw
                    """, (
                        job.job_id,
                        job.source,
                        job.title,
                        job.company,
                        job.location,
                        1 if job.remote else 0,
                        job.url,
                        posted_at_str,
                        fetched_at_str,
                        tags_json,
                        raw_json,
                    ))
                    updated += 1
        
        conn.commit()
        logger.info(f"Upserted {len(jobs)} jobs: {inserted} new, {updated} updated")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error upserting jobs: {e}", exc_info=True)
        raise
    finally:
        conn.close()
    
    return inserted, updated


def load_recent(sqlite_path: str, since_hours: int) -> List[Job]:
    """
    Load jobs fetched within the last since_hours.
    
    Args:
        sqlite_path: Path to SQLite database file
        since_hours: Number of hours to look back
    
    Returns:
        List of Job objects
    
    Examples:
        >>> from datetime import datetime, timezone
        >>> from app.core.ids import make_job_id
        >>> from app.core.models import Job
        >>> 
        >>> init_db("test.db")
        >>> 
        >>> job = Job(
        ...     job_id=make_job_id("Company", "Engineer", "https://example.com"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company",
        ...     fetched_at=datetime.now(timezone.utc)
        ... )
        >>> 
        >>> upsert_jobs("test.db", [job])
        >>> 
        >>> recent = load_recent("test.db", 24)
        >>> assert len(recent) >= 1
    """
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Calculate cutoff time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        cutoff_str = cutoff_time.isoformat()
        
        # Query jobs fetched since cutoff
        cursor = conn.execute("""
            SELECT * FROM jobs
            WHERE fetched_at >= ?
            ORDER BY fetched_at DESC
        """, (cutoff_str,))
        
        rows = cursor.fetchall()
        jobs = []
        
        for row in rows:
            try:
                job = _row_to_job(row)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error converting row to Job: {e}", exc_info=True)
                continue
        
        logger.info(f"Loaded {len(jobs)} jobs from last {since_hours} hours")
        return jobs
        
    finally:
        conn.close()


def _row_to_job(row: sqlite3.Row) -> Job:
    """
    Convert a database row to a Job object.
    
    Args:
        row: SQLite Row object
    
    Returns:
        Job object
    """
    # Parse posted_at
    posted_at = None
    if row["posted_at"]:
        try:
            posted_at = datetime.fromisoformat(row["posted_at"].replace('Z', '+00:00'))
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            else:
                posted_at = posted_at.astimezone(timezone.utc)
        except (ValueError, TypeError):
            pass
    
    # Parse fetched_at
    fetched_at = None
    if row["fetched_at"]:
        try:
            fetched_at = datetime.fromisoformat(row["fetched_at"].replace('Z', '+00:00'))
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            else:
                fetched_at = fetched_at.astimezone(timezone.utc)
        except (ValueError, TypeError):
            pass
    
    # Parse tags
    tags = []
    if row["tags"]:
        try:
            tags = json.loads(row["tags"])
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Parse raw
    raw = None
    if row["raw"]:
        try:
            raw = json.loads(row["raw"])
        except (json.JSONDecodeError, TypeError):
            pass
    
    return Job(
        job_id=row["job_id"],
        source=row["source"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        remote=bool(row["remote"]),
        url=row["url"],
        posted_at=posted_at,
        fetched_at=fetched_at,
        tags=tags,
        raw=raw,
    )
