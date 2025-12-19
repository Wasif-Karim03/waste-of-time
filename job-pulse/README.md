# Job Pulse

A real-time job aggregation pipeline that collects job listings from multiple sources (LinkedIn RSS, Indeed RSS, Greenhouse API, Lever API) without HTML scraping. Jobs are stored in SQLite as the truth source and can be exported to Google Sheets for dashboard viewing.

## Features

- **Multiple Sources**: LinkedIn RSS, Indeed RSS, Greenhouse API, Lever API
- **Web UI**: Simple browser interface for job search and CSV export
- **CSV Export**: Download search results as CSV files
- **Canonical Schema**: Unified `Job` dataclass for all sources
- **De-duplication**: Stable `job_id` hash prevents duplicate entries
- **Freshness Filter**: Only keeps jobs posted within `MAX_AGE_HOURS` (default: 24 hours)
- **Normalization**: Consistent formatting and timezone handling
- **Keyword Tagging**: Automatic tag extraction from job content
- **SQLite Storage**: Persistent database as truth source
- **Google Sheets Export**: Optional dashboard export
- **Clean Architecture**: Modular design with separate connectors, core, and storage modules
- **Configuration**: Environment-based configuration via `.env` file and `companies.yaml`

## Requirements

- Python 3.11+
- macOS (setup instructions below are for Mac)
- See `requirements.txt` for dependencies

## Installation (Mac)

### 1. Install Python 3.11+

Check if Python 3.11+ is installed:
```bash
python3 --version
```

If not installed, install via Homebrew:
```bash
brew install python@3.11
```

Or download from [python.org](https://www.python.org/downloads/).

### 2. Clone or Download Project

Navigate to your desired directory and create/clone the project:
```bash
cd ~/Desktop
# If you have the project files, navigate to the job-pulse directory
cd "Job Searching/job-pulse"
```

### 3. Create Virtual Environment

Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Add LinkedIn RSS feed URLs
- Add Indeed RSS feed URLs
- Add Greenhouse board tokens
- Add Lever company identifiers
- Configure Google Sheets (optional)

### 6. Google Sheets Setup (Optional)

If you want to export to Google Sheets:

1. Create a Google Cloud project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable the Google Sheets API
3. Create a service account and download the JSON credentials file
4. Save the credentials file as `credentials.json` in the project root
5. Create a Google Sheet and share it with the service account email (found in credentials.json)
6. Copy the spreadsheet ID from the URL and add it to `.env`

## Usage

### Option 1: Web UI (Recommended for CSV Export)

Start the web UI for easy job search and CSV export:

```bash
python run_ui.py
# Or: python -m app.ui
```

Then open your browser to: **http://127.0.0.1:5000**

1. Enter job role/keywords (e.g., "software engineer", "python developer")
2. Click "Search & Export CSV"
3. Download the CSV file with matching jobs

The UI searches all configured sources and filters jobs matching your keywords.

### Option 2: Command-Line Pipeline

Run the full pipeline from command line:

```bash
python -m app.main
```

The pipeline will:
1. Collect jobs from all configured sources
2. Normalize jobs (formatting, timezone handling)
3. Tag jobs with keywords
4. De-duplicate jobs using stable `job_id` hashes
5. Filter jobs by freshness (within `MAX_AGE_HOURS`)
6. Store jobs in SQLite database
7. Export jobs to Google Sheets (if configured)

### Command-Line Options

```bash
# Override max age hours
python -m app.main --max-age-hours 48

# Force export even if no new jobs
python -m app.main --export

# Dry-run mode (no database writes, no Sheets export)
python -m app.main --dry-run

# Combine options
python -m app.main --max-age-hours 72 --export
```

**Options:**
- `--max-age-hours N`: Override `MAX_AGE_HOURS` from config (default: 24)
- `--export`: Force export to Google Sheets even if no new jobs were processed
- `--dry-run`: Run pipeline without writing to database or exporting to Sheets (useful for testing)

### Automated Scheduling (macOS Cron)

Run the pipeline every 30 minutes using cron:

1. Open your crontab:
```bash
crontab -e
```

2. Add this line (adjust the path to your project):
```bash
*/30 * * * * cd /Users/your-username/Desktop/Job\ Searching/job-pulse && /usr/bin/python3 -m app.main >> /tmp/job-pulse.log 2>&1
```

3. Or with virtual environment:
```bash
*/30 * * * * cd /Users/your-username/Desktop/Job\ Searching/job-pulse && source venv/bin/activate && python -m app.main >> /tmp/job-pulse.log 2>&1
```

**Note:** On macOS, you may need to grant Terminal (or your terminal app) Full Disk Access in System Settings > Privacy & Security for cron to work properly.

### Recommended RSS URL Examples

For RSS feeds, use URLs with filters to get only recent jobs (last 24 hours):

**LinkedIn RSS:**
```
# Search for "software engineer" jobs posted in last 24 hours
https://www.linkedin.com/jobs/search/rss/?keywords=software%20engineer&f_TPR=r86400

# Search for "python developer" remote jobs
https://www.linkedin.com/jobs/search/rss/?keywords=python%20developer&f_WT=2&f_TPR=r86400

# Multiple locations
https://www.linkedin.com/jobs/search/rss/?keywords=backend%20engineer&location=San%20Francisco&f_TPR=r86400
```

**Indeed RSS:**
```
# Software engineer jobs posted in last 24 hours
https://www.indeed.com/rss?q=software+engineer&l=&sort=date&fromage=1

# Python developer remote jobs
https://www.indeed.com/rss?q=python+developer&l=remote&sort=date&fromage=1

# Full stack developer in specific location
https://www.indeed.com/rss?q=full+stack+developer&l=New+York&sort=date&fromage=1
```

**RSS URL Parameters:**
- `f_TPR=r86400` (LinkedIn): Filter to last 24 hours (86400 seconds)
- `fromage=1` (Indeed): Filter to jobs posted in last 24 hours
- `sort=date`: Sort by most recent first

**Safe Defaults:**
- `MAX_AGE_HOURS=24`: Only keep jobs posted within last 24 hours
- `LOG_LEVEL=INFO`: Standard logging level
- `SQLITE_PATH=./jobs.db`: Local database file
- Export only runs if `GOOGLE_SHEET_ID` and `GOOGLE_SERVICE_ACCOUNT_JSON` are configured

### Verify Installation

Test that the pipeline runs (even with empty connectors):
```bash
python -m app.main
```

You should see log output indicating the pipeline ran successfully, even if no jobs were collected (since connectors are not yet implemented).

## Configuration

### Environment Variables

- `SQLITE_PATH`: Path to SQLite database file (default: `./jobs.db`)
- `MAX_AGE_HOURS`: Maximum age of jobs to keep in hours (default: `24`)
- `KEYWORDS`: Comma-separated list of keywords for tagging jobs
- `LINKEDIN_RSS_URLS`: Comma-separated list of LinkedIn RSS feed URLs
- `INDEED_RSS_URLS`: Comma-separated list of Indeed RSS feed URLs
- `GREENHOUSE_BOARDS`: Comma-separated list of Greenhouse board slugs
- `LEVER_COMPANIES`: Comma-separated list of Lever company identifiers
- `GOOGLE_SHEET_ID`: Google Sheets spreadsheet ID (optional)
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Path to Google service account JSON file (optional)
- `EXPORT_SHEET_TAB`: Worksheet name for export (default: `Jobs`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

**Safe Defaults:**
- All optional fields have sensible defaults
- Export only runs if both `GOOGLE_SHEET_ID` and `GOOGLE_SERVICE_ACCOUNT_JSON` are set
- `MAX_AGE_HOURS=24` ensures only recent jobs are kept
- Database is created automatically if it doesn't exist

### Example `.env` file

```env
# Database
SQLITE_PATH=./jobs.db

# Freshness filter (hours) - default: 24
MAX_AGE_HOURS=24

# Keywords for tagging (comma-separated)
KEYWORDS=python,javascript,remote,backend,frontend

# LinkedIn RSS Feeds (comma-separated)
# Use f_TPR=r86400 for last 24 hours filter
LINKEDIN_RSS_URLS=https://www.linkedin.com/jobs/search/rss/?keywords=software%20engineer&f_TPR=r86400,https://www.linkedin.com/jobs/search/rss/?keywords=python%20developer&f_TPR=r86400

# Indeed RSS Feeds (comma-separated)
# Use fromage=1 for last 24 hours filter
INDEED_RSS_URLS=https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1,https://www.indeed.com/rss?q=python+developer&sort=date&fromage=1

# Greenhouse Boards (comma-separated board slugs)
GREENHOUSE_BOARDS=companyname,anothercompany

# Lever Companies (comma-separated company identifiers)
LEVER_COMPANIES=companyname,anothercompany

# Google Sheets (optional)
GOOGLE_SHEET_ID=your-spreadsheet-id-here
GOOGLE_SERVICE_ACCOUNT_JSON=credentials.json
EXPORT_SHEET_TAB=Jobs

# Logging
LOG_LEVEL=INFO
```

## Project Structure

```
job-pulse/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration management
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py        # Job dataclass schema
│   │   ├── ids.py           # Job ID generation & de-duplication
│   │   ├── freshness.py     # Freshness filter
│   │   ├── normalize.py      # Job normalization
│   │   └── keywords.py       # Keyword extraction & tagging
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── linkedin_rss.py  # LinkedIn RSS connector
│   │   ├── indeed_rss.py     # Indeed RSS connector
│   │   ├── greenhouse.py     # Greenhouse API connector
│   │   └── lever.py          # Lever API connector
│   └── storage/
│       ├── __init__.py
│       ├── sqlite_store.py   # SQLite storage
│       └── sheets_store.py   # Google Sheets export
├── .env.example
├── requirements.txt
└── README.md
```

## Job Schema

The canonical `Job` dataclass includes:

- `job_id`: Stable hash-based identifier
- `source`: Source identifier (`linkedin_rss`, `indeed_rss`, `greenhouse`, `lever`)
- `title`: Job title
- `company`: Company name
- `location`: Job location (optional)
- `remote`: Boolean indicating if job is remote
- `url`: Application URL (optional)
- `posted_at`: Posting timestamp in UTC (optional)
- `fetched_at`: Timestamp when job was fetched in UTC
- `tags`: List of keyword tags
- `raw`: Original source data (dict, optional)

## Pipeline Flow

1. **Collect**: Fetch jobs from all configured connectors
2. **Normalize**: Standardize formatting, timezones, and data quality
3. **Tag**: Extract keywords and add tags to jobs
4. **De-duplicate**: Remove duplicates using stable `job_id` hash
5. **Filter**: Keep only jobs within `MAX_AGE_HOURS`
6. **Store**: Save to SQLite database (truth source)
7. **Export**: Export to Google Sheets (if configured)

## De-duplication

Jobs are de-duplicated using a stable `job_id` hash generated from:
- Job title
- Company name
- Source identifier
- Source ID or URL

This ensures the same job from different sources or runs is identified correctly.

## Freshness Filter

Only jobs with a `posted_at` timestamp within `MAX_AGE_HOURS` are kept. Jobs without a timestamp are excluded (cannot verify freshness).

## Database

SQLite database stores all jobs with:
- Primary key on `job_id`
- Indexes on `source`, `company`, `posted_at`, and `created_at`
- Full job data including raw source data and tags

## Google Sheets Export

If configured, jobs are exported to Google Sheets with columns:
- Job ID, Title, Company, Location, Remote
- URL, Posted At, Source, Tags

The worksheet is cleared and repopulated on each export.

## Logging

Logging is configured at INFO level by default. Logs include:
- Source collection progress
- Normalization and tagging results
- De-duplication and filtering results
- Database operations
- Export operations
- Errors and warnings

## Development

### Running Tests

The pipeline is designed to run even with empty connectors. To test:
```bash
python -m app.main
```

### Implementing Connectors

Each connector module in `app/connectors/` should implement a `fetch_*_jobs()` function that:
- Takes source configuration as input
- Returns a list of `Job` objects
- Handles errors gracefully with logging

See existing connector modules for the expected interface.

## Troubleshooting

### Import Errors

If you get import errors, make sure:
- Virtual environment is activated: `source venv/bin/activate`
- Dependencies are installed: `pip install -r requirements.txt`
- You're running from the project root: `python -m app.main`

### Google Sheets Errors

- Verify credentials file exists and is valid JSON
- Check that service account email has access to the spreadsheet
- Ensure spreadsheet ID is correct in `.env`

### Database Errors

- Check file permissions for database directory
- Verify `DATABASE_PATH` in `.env` is correct

## License

MIT

