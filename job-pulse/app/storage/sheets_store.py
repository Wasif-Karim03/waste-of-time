"""Google Sheets storage for job dashboard."""

import logging
from pathlib import Path
from typing import List

from app.config import Settings
from app.core.keywords import score_job
from app.core.models import Job

logger = logging.getLogger(__name__)

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logger.warning("Google Sheets libraries not available. Install gspread and google-auth.")


def export_to_google_sheets(settings: Settings, jobs: List[Job]) -> None:
    """
    Export jobs to Google Sheets.
    
    Opens sheet by ID, selects tab EXPORT_SHEET_TAB (creates if missing),
    clears existing rows, and writes header + job rows.
    
    Columns: PostedAt, Score, Title, Company, Location, Remote, Source, URL, Tags
    
    Args:
        settings: Settings object with GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON
        jobs: List of Job objects to export
    
    Examples:
        >>> from app.config import Settings
        >>> from datetime import datetime, timezone
        >>> from app.core.ids import make_job_id
        >>> from app.core.models import Job
        >>> 
        >>> settings = Settings(
        ...     GOOGLE_SHEET_ID="test-id",
        ...     GOOGLE_SERVICE_ACCOUNT_JSON="credentials.json",
        ...     EXPORT_SHEET_TAB="Jobs"
        ... )
        >>> 
        >>> job = Job(
        ...     job_id=make_job_id("Company", "Engineer", "https://example.com"),
        ...     source="test",
        ...     title="Engineer",
        ...     company="Company",
        ...     fetched_at=datetime.now(timezone.utc)
        ... )
        >>> 
        >>> # Will skip if credentials don't exist
        >>> export_to_google_sheets(settings, [job])
    """
    # Check if export is configured
    if not settings.GOOGLE_SHEET_ID or not settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        logger.info("Skipping export: Google Sheets not configured (missing GOOGLE_SHEET_ID or GOOGLE_SERVICE_ACCOUNT_JSON)")
        return
    
    # Check if libraries are available
    if not GOOGLE_SHEETS_AVAILABLE:
        logger.warning("Skipping export: Google Sheets libraries not available")
        return
    
    # Check if credentials file exists
    creds_path = Path(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
    if not creds_path.exists():
        logger.warning(f"Skipping export: Credentials file not found: {creds_path}")
        return
    
    if not jobs:
        logger.info("No jobs to export")
        return
    
    try:
        # Authenticate with service account
        creds = Credentials.from_service_account_file(
            str(creds_path),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        spreadsheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
        
        # Get or create worksheet
        worksheet_name = settings.EXPORT_SHEET_TAB
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"Using existing worksheet: {worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            # Create worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=1000,
                cols=20
            )
            logger.info(f"Created worksheet: {worksheet_name}")
        
        # Prepare header
        headers = [
            "PostedAt",
            "Score",
            "Title",
            "Company",
            "Location",
            "Remote",
            "Source",
            "URL",
            "Tags",
        ]
        
        # Prepare rows
        rows = [headers]
        for job in jobs:
            # Calculate score
            score = score_job(job)
            
            # Format PostedAt as ISO string
            posted_at_str = job.posted_at.isoformat() if job.posted_at else ""
            
            # Format Tags as comma-separated string
            tags_str = ", ".join(job.tags) if job.tags else ""
            
            # Format Remote as Yes/No
            remote_str = "Yes" if job.remote else "No"
            
            # URL - Sheets will auto-link URLs, but we can also use HYPERLINK formula
            # For simplicity, just use the URL directly (Sheets will make it clickable)
            url_str = job.url or ""
            
            row = [
                posted_at_str,
                score,
                job.title,
                job.company,
                job.location or "",
                remote_str,
                job.source,
                url_str,
                tags_str,
            ]
            rows.append(row)
        
        # Clear existing data
        worksheet.clear()
        
        # Write new data
        worksheet.update(rows, value_input_option='RAW')
        
        logger.info(f"Exported {len(jobs)} jobs to Google Sheets (tab: {worksheet_name})")
        
    except gspread.exceptions.APIError as e:
        logger.error(f"Google Sheets API error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error exporting to Google Sheets: {e}", exc_info=True)
        raise


# Legacy class for backward compatibility
class SheetsStore:
    """Export jobs to Google Sheets (legacy class)."""
    
    def __init__(
        self,
        credentials_path: str = None,
        spreadsheet_id: str = None,
        worksheet_name: str = None,
    ):
        """Initialize Google Sheets exporter (legacy)."""
        logger.warning("SheetsStore class is deprecated. Use export_to_google_sheets() instead.")
        if not GOOGLE_SHEETS_AVAILABLE:
            raise ImportError(
                "Google Sheets libraries not available. "
                "Install: pip install gspread google-auth"
            )
        
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name or "Jobs"
    
    def export_jobs(self, jobs: List[Job]):
        """Export jobs to Google Sheets (legacy method)."""
        from app.config import Settings
        
        # Create a temporary settings object for compatibility
        settings = Settings(
            GOOGLE_SHEET_ID=self.spreadsheet_id,
            GOOGLE_SERVICE_ACCOUNT_JSON=self.credentials_path,
            EXPORT_SHEET_TAB=self.worksheet_name,
        )
        
        export_to_google_sheets(settings, jobs)
