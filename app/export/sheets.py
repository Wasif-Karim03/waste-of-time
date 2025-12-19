"""Google Sheets export for job dashboard."""

import logging
from typing import List, Optional

from app.config import Config
from app.models import Job

logger = logging.getLogger(__name__)

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logger.warning("Google Sheets libraries not available. Install gspread or google-api-python-client.")


class GoogleSheetsExporter:
    """Export jobs to Google Sheets."""
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        worksheet_name: Optional[str] = None,
    ):
        """Initialize Google Sheets exporter."""
        if not GOOGLE_SHEETS_AVAILABLE:
            raise ImportError(
                "Google Sheets libraries not available. "
                "Install: pip install google-api-python-client google-auth"
            )
        
        self.credentials_path = credentials_path or Config.GOOGLE_SHEETS_CREDENTIALS_PATH
        self.spreadsheet_id = spreadsheet_id or Config.GOOGLE_SHEETS_SPREADSHEET_ID
        self.worksheet_name = worksheet_name or Config.GOOGLE_SHEETS_WORKSHEET_NAME
        
        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID must be set")
        
        self._service = None
        self._ensure_worksheet()
    
    def _get_service(self):
        """Get Google Sheets API service."""
        if self._service is None:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self._service = build('sheets', 'v4', credentials=creds)
        return self._service
    
    def _ensure_worksheet(self):
        """Ensure worksheet exists, create if not."""
        service = self._get_service()
        
        try:
            # Get spreadsheet metadata
            spreadsheet = service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            
            if self.worksheet_name not in sheet_names:
                # Create worksheet
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': self.worksheet_name
                        }
                    }
                }]
                
                body = {'requests': requests}
                service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
                logger.info(f"Created worksheet: {self.worksheet_name}")
        except HttpError as e:
            logger.error(f"Error ensuring worksheet exists: {e}")
            raise
    
    def export_jobs(self, jobs: List[Job]):
        """Export jobs to Google Sheets, replacing existing data."""
        if not jobs:
            logger.info("No jobs to export")
            return
        
        service = self._get_service()
        
        # Prepare data
        headers = [
            "Job ID",
            "Title",
            "Company",
            "Location",
            "URL",
            "Posted At",
            "Source",
            "Department",
            "Employment Type",
            "Description",
        ]
        
        rows = [headers]
        for job in jobs:
            posted_at_str = ""
            if job.posted_at:
                posted_at_str = job.posted_at.strftime("%Y-%m-%d %H:%M:%S")
            
            # Truncate description for Sheets (limit cell size)
            description = (job.description or "")[:50000]  # Sheets limit is ~50k chars
            
            row = [
                job.job_id,
                job.title,
                job.company,
                job.location or "",
                job.url or "",
                posted_at_str,
                job.source,
                job.department or "",
                job.employment_type or "",
                description,
            ]
            rows.append(row)
        
        # Clear existing data and write new data
        range_name = f"{self.worksheet_name}!A1"
        
        try:
            # Clear existing data
            service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.worksheet_name}!A:Z"
            ).execute()
            
            # Write new data
            body = {
                'values': rows
            }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Exported {len(jobs)} jobs to Google Sheets")
            
        except HttpError as e:
            logger.error(f"Error exporting to Google Sheets: {e}")
            raise

