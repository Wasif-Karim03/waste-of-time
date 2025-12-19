"""Configuration management via .env and defaults."""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration."""
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "jobs.db")
    
    # Freshness filter
    MAX_AGE_HOURS: int = int(os.getenv("MAX_AGE_HOURS", "24"))
    
    # RSS Sources (comma-separated URLs)
    RSS_FEEDS: List[str] = [
        url.strip() 
        for url in os.getenv("RSS_FEEDS", "").split(",") 
        if url.strip()
    ]
    
    # Greenhouse API
    GREENHOUSE_BOARDS: List[str] = [
        board.strip()
        for board in os.getenv("GREENHOUSE_BOARDS", "").split(",")
        if board.strip()
    ]
    
    # Lever API
    LEVER_COMPANIES: List[str] = [
        company.strip()
        for company in os.getenv("LEVER_COMPANIES", "").split(",")
        if company.strip()
    ]
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH: str = os.getenv(
        "GOOGLE_SHEETS_CREDENTIALS_PATH", 
        "credentials.json"
    )
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv(
        "GOOGLE_SHEETS_SPREADSHEET_ID", 
        ""
    )
    GOOGLE_SHEETS_WORKSHEET_NAME: str = os.getenv(
        "GOOGLE_SHEETS_WORKSHEET_NAME", 
        "Jobs"
    )
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

