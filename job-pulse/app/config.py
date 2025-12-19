"""Configuration management via .env and defaults."""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def parse_comma_list(value: Optional[str]) -> List[str]:
    """
    Parse a comma-separated string into a list of trimmed, non-empty strings.
    
    Args:
        value: Comma-separated string or None
    
    Returns:
        List of trimmed strings, empty list if value is None or empty
    """
    if not value:
        return []
    
    return [item.strip() for item in value.split(",") if item.strip()]


def load_companies_yaml(project_root: Path) -> Dict[str, Optional[List[str]]]:
    """
    Load companies.yaml file if it exists.
    
    Args:
        project_root: Path to project root directory
    
    Returns:
        Dict with 'greenhouse_boards' and 'lever_companies' keys.
        Values are None if key not found in YAML, empty list if key exists but is empty,
        or list of strings if key exists with values.
    """
    yaml_path = project_root / "companies.yaml"
    
    if not yaml_path.exists():
        return {"greenhouse_boards": None, "lever_companies": None}
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            logger.warning(f"companies.yaml does not contain a dictionary, ignoring")
            return {"greenhouse_boards": None, "lever_companies": None}
        
        # Extract lists, ensuring they are lists of strings
        greenhouse_boards: Optional[List[str]] = None
        lever_companies: Optional[List[str]] = None
        
        if "greenhouse_boards" in data:
            boards = data["greenhouse_boards"]
            if isinstance(boards, list):
                greenhouse_boards = [str(item).strip() for item in boards if item and str(item).strip()]
            else:
                logger.warning(f"greenhouse_boards in companies.yaml is not a list, ignoring")
        
        if "lever_companies" in data:
            companies = data["lever_companies"]
            if isinstance(companies, list):
                lever_companies = [str(item).strip() for item in companies if item and str(item).strip()]
            else:
                logger.warning(f"lever_companies in companies.yaml is not a list, ignoring")
        
        gh_count = len(greenhouse_boards) if greenhouse_boards is not None else 0
        lev_count = len(lever_companies) if lever_companies is not None else 0
        logger.info(f"Loaded companies.yaml: {gh_count} Greenhouse boards, {lev_count} Lever companies")
        return {
            "greenhouse_boards": greenhouse_boards,
            "lever_companies": lever_companies,
        }
        
    except yaml.YAMLError as e:
        logger.warning(f"Error parsing companies.yaml: {e}, ignoring file")
        return {"greenhouse_boards": None, "lever_companies": None}
    except Exception as e:
        logger.warning(f"Error reading companies.yaml: {e}, ignoring file")
        return {"greenhouse_boards": None, "lever_companies": None}


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Freshness filter
    MAX_AGE_HOURS: int = 24
    
    # Keywords for filtering/tagging
    KEYWORDS: List[str] = field(default_factory=list)
    
    # RSS Sources
    LINKEDIN_RSS_URLS: List[str] = field(default_factory=list)
    INDEED_RSS_URLS: List[str] = field(default_factory=list)
    GLASSDOOR_RSS_URLS: List[str] = field(default_factory=list)
    HANDSHAKE_RSS_URLS: List[str] = field(default_factory=list)
    
    # API Sources
    GREENHOUSE_BOARDS: List[str] = field(default_factory=list)
    LEVER_COMPANIES: List[str] = field(default_factory=list)
    
    # SQLite Storage
    SQLITE_PATH: str = "./jobs.db"
    
    # Google Sheets Export (optional)
    GOOGLE_SHEET_ID: Optional[str] = None
    GOOGLE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    EXPORT_SHEET_TAB: str = "Jobs"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Create Settings instance from environment variables and companies.yaml.
        
        Loads from environment variables first, then overrides with companies.yaml
        if present (for greenhouse_boards and lever_companies).
        
        Returns:
            Settings instance with values from environment and companies.yaml
        
        Raises:
            ValueError: If required fields for enabled features are missing
        """
        # Load from environment variables
        greenhouse_boards = parse_comma_list(os.getenv("GREENHOUSE_BOARDS"))
        lever_companies = parse_comma_list(os.getenv("LEVER_COMPANIES"))
        
        # Load companies.yaml if it exists (overrides env vars)
        project_root = Path(__file__).parent.parent
        companies_config = load_companies_yaml(project_root)
        
        # Override with YAML values if present (None means key not in YAML, so don't override)
        if companies_config["greenhouse_boards"] is not None:
            greenhouse_boards = companies_config["greenhouse_boards"]
            logger.info("Using greenhouse_boards from companies.yaml (overriding env vars)")
        
        if companies_config["lever_companies"] is not None:
            lever_companies = companies_config["lever_companies"]
            logger.info("Using lever_companies from companies.yaml (overriding env vars)")
        
        settings = cls(
            MAX_AGE_HOURS=int(os.getenv("MAX_AGE_HOURS", "24")),
            KEYWORDS=parse_comma_list(os.getenv("KEYWORDS")),
            LINKEDIN_RSS_URLS=parse_comma_list(os.getenv("LINKEDIN_RSS_URLS")),
            INDEED_RSS_URLS=parse_comma_list(os.getenv("INDEED_RSS_URLS")),
            GLASSDOOR_RSS_URLS=parse_comma_list(os.getenv("GLASSDOOR_RSS_URLS")),
            HANDSHAKE_RSS_URLS=parse_comma_list(os.getenv("HANDSHAKE_RSS_URLS")),
            GREENHOUSE_BOARDS=greenhouse_boards,
            LEVER_COMPANIES=lever_companies,
            SQLITE_PATH=os.getenv("SQLITE_PATH", "./jobs.db"),
            GOOGLE_SHEET_ID=os.getenv("GOOGLE_SHEET_ID") or None,
            GOOGLE_SERVICE_ACCOUNT_JSON=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or None,
            EXPORT_SHEET_TAB=os.getenv("EXPORT_SHEET_TAB", "Jobs"),
        )
        
        # Validate only when features are enabled
        settings.validate()
        
        return settings
    
    def validate(self) -> None:
        """
        Validate settings and raise errors for missing required fields.
        
        Only validates features that are enabled (e.g., Google Sheets export
        only if both SHEET_ID and credentials are provided).
        
        Raises:
            ValueError: If required fields for enabled features are missing
        """
        errors = []
        
        # Validate Google Sheets export (only if partially configured)
        has_sheet_id = bool(self.GOOGLE_SHEET_ID)
        has_credentials = bool(self.GOOGLE_SERVICE_ACCOUNT_JSON)
        
        if has_sheet_id and not has_credentials:
            errors.append(
                "Google Sheets export is partially configured: "
                "GOOGLE_SHEET_ID is set but GOOGLE_SERVICE_ACCOUNT_JSON is missing. "
                "Please provide the path to your Google service account JSON file."
            )
        
        if has_credentials and not has_sheet_id:
            errors.append(
                "Google Sheets export is partially configured: "
                "GOOGLE_SERVICE_ACCOUNT_JSON is set but GOOGLE_SHEET_ID is missing. "
                "Please provide the Google Sheet ID."
            )
        
        # Validate credentials file exists if provided
        if has_credentials:
            creds_path = Path(self.GOOGLE_SERVICE_ACCOUNT_JSON)
            if not creds_path.exists():
                errors.append(
                    f"Google service account JSON file not found: {creds_path}. "
                    "Please check the GOOGLE_SERVICE_ACCOUNT_JSON path."
                )
        
        # Validate SQLite path directory exists or can be created
        sqlite_path = Path(self.SQLITE_PATH)
        sqlite_dir = sqlite_path.parent
        if sqlite_dir != Path(".") and not sqlite_dir.exists():
            try:
                sqlite_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(
                    f"Cannot create SQLite database directory {sqlite_dir}: {e}. "
                    "Please check permissions or provide a valid SQLITE_PATH."
                )
        
        # Validate MAX_AGE_HOURS is positive
        if self.MAX_AGE_HOURS <= 0:
            errors.append(
                f"MAX_AGE_HOURS must be positive, got {self.MAX_AGE_HOURS}. "
                "Please set a positive integer value."
            )
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
    
    def is_google_sheets_enabled(self) -> bool:
        """
        Check if Google Sheets export is fully configured.
        
        Returns:
            True if both GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON are set
        """
        return bool(self.GOOGLE_SHEET_ID and self.GOOGLE_SERVICE_ACCOUNT_JSON)


# Global settings instance (lazy-loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance, creating it if necessary.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


# For backward compatibility, create a Config class that acts as a namespace
class _ConfigMeta(type):
    """Metaclass to make Config attributes accessible as class attributes."""
    
    def __getattr__(cls, name: str):
        """Get attribute from settings."""
        settings = get_settings()
        
        # Map old names to new names
        name_mapping = {
            "DATABASE_PATH": "SQLITE_PATH",
            "LINKEDIN_RSS_FEEDS": "LINKEDIN_RSS_URLS",
            "INDEED_RSS_FEEDS": "INDEED_RSS_URLS",
            "GOOGLE_SHEETS_CREDENTIALS_PATH": "GOOGLE_SERVICE_ACCOUNT_JSON",
            "GOOGLE_SHEETS_SPREADSHEET_ID": "GOOGLE_SHEET_ID",
            "GOOGLE_SHEETS_WORKSHEET_NAME": "EXPORT_SHEET_TAB",
        }
        
        # Use mapped name if available, otherwise use original
        settings_attr = name_mapping.get(name, name)
        
        if hasattr(settings, settings_attr):
            value = getattr(settings, settings_attr)
            # Handle special cases
            if name == "GOOGLE_SHEETS_CREDENTIALS_PATH":
                return value or "credentials.json"
            elif name == "GOOGLE_SHEETS_SPREADSHEET_ID":
                return value or ""
            return value
        
        # Handle LOG_LEVEL and LOG_FORMAT specially
        if name == "LOG_LEVEL":
            return os.getenv("LOG_LEVEL", "INFO")
        elif name == "LOG_FORMAT":
            return os.getenv(
                "LOG_FORMAT",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        
        raise AttributeError(f"'{cls.__name__}' object has no attribute '{name}'")


class Config(metaclass=_ConfigMeta):
    """Legacy Config class for backward compatibility."""
    pass
