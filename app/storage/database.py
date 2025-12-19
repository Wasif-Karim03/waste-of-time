"""SQLite database storage for jobs."""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.config import Config
from app.models import Job

logger = logging.getLogger(__name__)


class JobDatabase:
    """SQLite database for storing jobs as truth source."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_db_exists()
        self._create_tables()
    
    def _ensure_db_exists(self):
        """Ensure database file and directory exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self):
        """Create jobs table if it doesn't exist."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    posted_at TEXT,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    department TEXT,
                    employment_type TEXT,
                    salary_range TEXT,
                    raw_data TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_posted_at ON jobs(posted_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)")
            
            conn.commit()
            logger.info("Database tables initialized")
        finally:
            conn.close()
    
    def upsert_job(self, job: Job) -> bool:
        """
        Insert or update a job in the database.
        
        Returns True if job was inserted (new), False if updated (existing).
        """
        conn = self._get_connection()
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            # Check if job exists
            cursor = conn.execute(
                "SELECT job_id FROM jobs WHERE job_id = ?",
                (job.job_id,)
            )
            exists = cursor.fetchone() is not None
            
            # Serialize raw_data
            raw_data_json = json.dumps(job.raw_data) if job.raw_data else None
            
            # Serialize posted_at
            posted_at_str = job.posted_at.isoformat() if job.posted_at else None
            
            if exists:
                # Update existing job
                conn.execute("""
                    UPDATE jobs SET
                        title = ?,
                        company = ?,
                        location = ?,
                        description = ?,
                        url = ?,
                        posted_at = ?,
                        source = ?,
                        source_id = ?,
                        department = ?,
                        employment_type = ?,
                        salary_range = ?,
                        raw_data = ?,
                        updated_at = ?
                    WHERE job_id = ?
                """, (
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    posted_at_str,
                    job.source,
                    job.source_id,
                    job.department,
                    job.employment_type,
                    job.salary_range,
                    raw_data_json,
                    now,
                    job.job_id,
                ))
                conn.commit()
                return False
            else:
                # Insert new job
                conn.execute("""
                    INSERT INTO jobs (
                        job_id, title, company, location, description, url,
                        posted_at, source, source_id, department, employment_type,
                        salary_range, raw_data, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.job_id,
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    posted_at_str,
                    job.source,
                    job.source_id,
                    job.department,
                    job.employment_type,
                    job.salary_range,
                    raw_data_json,
                    now,
                    now,
                ))
                conn.commit()
                return True
        finally:
            conn.close()
    
    def upsert_jobs(self, jobs: List[Job]) -> tuple[int, int]:
        """
        Insert or update multiple jobs.
        
        Returns (inserted_count, updated_count).
        """
        inserted = 0
        updated = 0
        
        for job in jobs:
            is_new = self.upsert_job(job)
            if is_new:
                inserted += 1
            else:
                updated += 1
        
        logger.info(f"Upserted {len(jobs)} jobs: {inserted} new, {updated} updated")
        return inserted, updated
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs from database."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM jobs ORDER BY posted_at DESC, created_at DESC")
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                job = self._row_to_job(row)
                jobs.append(job)
            
            return jobs
        finally:
            conn.close()
    
    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get a job by job_id."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_job(row)
            return None
        finally:
            conn.close()
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        # Parse posted_at
        posted_at = None
        if row["posted_at"]:
            try:
                posted_at = datetime.fromisoformat(row["posted_at"])
            except (ValueError, TypeError):
                pass
        
        # Parse raw_data
        raw_data = {}
        if row["raw_data"]:
            try:
                raw_data = json.loads(row["raw_data"])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return Job(
            job_id=row["job_id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            url=row["url"],
            posted_at=posted_at,
            source=row["source"],
            source_id=row["source_id"],
            department=row["department"],
            employment_type=row["employment_type"],
            salary_range=row["salary_range"],
            raw_data=raw_data,
        )
    
    def get_fresh_jobs(self, max_age_hours: int) -> List[Job]:
        """Get jobs posted within max_age_hours."""
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cutoff_str = cutoff_time.isoformat()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE posted_at >= ? ORDER BY posted_at DESC",
                (cutoff_str,)
            )
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                job = self._row_to_job(row)
                jobs.append(job)
            
            return jobs
        finally:
            conn.close()

