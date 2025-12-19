# Job Aggregation Pipeline

A real-time job aggregation pipeline that collects job listings from multiple sources (RSS feeds, Greenhouse API, Lever API) without HTML scraping. Jobs are stored in SQLite as the truth source and can be exported to Google Sheets for dashboard viewing.

## Features

- **Multiple Sources**: RSS feeds, Greenhouse API, Lever API (Gmail support planned)
- **Canonical Schema**: Unified `Job` dataclass for all sources
- **De-duplication**: Stable `job_id` hash prevents duplicate entries
- **Freshness Filter**: Only keeps jobs posted within `MAX_AGE_HOURS` (default: 24 hours)
- **SQLite Storage**: Persistent database as truth source
- **Google Sheets Export**: Optional dashboard export
- **Clean Architecture**: Modular design with separate source, storage, and export modules
- **Configuration**: Environment-based configuration via `.env` file

## Requirements

- Python 3.11+
- See `requirements.txt` for dependencies

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Edit `.env` with your configuration:
   - Add RSS feed URLs
   - Add Greenhouse board tokens
   - Add Lever company identifiers
   - Configure Google Sheets (optional)

5. For Google Sheets export, you'll need:
   - A Google Cloud project with Sheets API enabled
   - A service account JSON credentials file
   - Share your spreadsheet with the service account email

## Usage

Run the pipeline:
```bash
python -m app.main
```

The pipeline will:
1. Collect jobs from all configured sources
2. De-duplicate jobs using stable `job_id` hashes
3. Filter jobs by freshness (within `MAX_AGE_HOURS`)
4. Store jobs in SQLite database
5. Export jobs to Google Sheets (if configured)

## Configuration

### Environment Variables

- `DATABASE_PATH`: Path to SQLite database file (default: `jobs.db`)
- `MAX_AGE_HOURS`: Maximum age of jobs to keep in hours (default: `24`)
- `RSS_FEEDS`: Comma-separated list of RSS feed URLs
- `GREENHOUSE_BOARDS`: Comma-separated list of Greenhouse board tokens
- `LEVER_COMPANIES`: Comma-separated list of Lever company identifiers
- `GOOGLE_SHEETS_CREDENTIALS_PATH`: Path to Google service account JSON file
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Google Sheets spreadsheet ID
- `GOOGLE_SHEETS_WORKSHEET_NAME`: Worksheet name (default: `Jobs`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Example `.env` file

```env
DATABASE_PATH=jobs.db
MAX_AGE_HOURS=24

RSS_FEEDS=https://jobs.example.com/rss,https://careers.another.com/feed.xml

GREENHOUSE_BOARDS=companyname,anothercompany

LEVER_COMPANIES=companyname,anothercompany

GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=1abc123def456ghi789
GOOGLE_SHEETS_WORKSHEET_NAME=Jobs

LOG_LEVEL=INFO
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── models.py            # Job dataclass schema
│   ├── config.py            # Configuration management
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── rss.py           # RSS feed parser
│   │   ├── greenhouse.py    # Greenhouse API client
│   │   └── lever.py         # Lever API client
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py      # SQLite storage
│   ├── export/
│   │   ├── __init__.py
│   │   └── sheets.py        # Google Sheets export
│   └── utils/
│       ├── __init__.py
│       ├── dedupe.py         # De-duplication logic
│       └── freshness.py      # Freshness filter
├── .env.example
├── requirements.txt
└── README.md
```

## Job Schema

The canonical `Job` dataclass includes:

- `job_id`: Stable hash-based identifier
- `title`: Job title
- `company`: Company name
- `location`: Job location (optional)
- `description`: Job description (optional)
- `url`: Application URL (optional)
- `posted_at`: Posting timestamp (optional)
- `source`: Source identifier (`rss`, `greenhouse`, `lever`)
- `source_id`: Original ID from source (optional)
- `department`: Department/team (optional)
- `employment_type`: Employment type (optional)
- `salary_range`: Salary range (optional)
- `raw_data`: Original source data (dict)

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
- Full job data including raw source data

## Google Sheets Export

If configured, jobs are exported to Google Sheets with columns:
- Job ID, Title, Company, Location, URL
- Posted At, Source, Department, Employment Type
- Description

The worksheet is cleared and repopulated on each export.

## Logging

Logging is configured at INFO level by default. Logs include:
- Source collection progress
- De-duplication and filtering results
- Database operations
- Export operations
- Errors and warnings

## Future Enhancements

- Gmail integration for job postings
- Additional source integrations
- Webhook notifications
- Scheduled runs
- Advanced filtering options

## License

MIT

