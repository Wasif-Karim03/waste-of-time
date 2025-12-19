# Job Search UI Guide

## Quick Start

1. **Start the UI:**
   ```bash
   cd job-pulse
   source .venv/bin/activate
   python run_ui.py
   ```

2. **Open browser:**
   Go to: http://127.0.0.1:5000

3. **Search for jobs:**
   - Enter job role/keywords (e.g., "software engineer", "python developer")
   - Separate multiple keywords with commas
   - Click "Search & Export CSV"

4. **Download CSV:**
   - Once search completes, click "Download CSV File"
   - CSV includes: PostedAt, Score, Title, Company, Location, Remote, Source, URL, Tags

## How It Works

1. **Searches all sources:**
   - Greenhouse boards (from `companies.yaml`)
   - Lever companies (from `companies.yaml`)
   - LinkedIn RSS feeds (from `.env`)
   - Indeed RSS feeds (from `.env`)

2. **Filters jobs:**
   - Only jobs posted within last 24 hours (fresh jobs)
   - Only jobs matching your search keywords (in title, company, or tags)
   - Removes duplicates

3. **Exports to CSV:**
   - Sorts jobs by score (highest first)
   - Exports as CSV file
   - File name includes search terms and timestamp

## CSV Columns

- **PostedAt**: When job was posted (ISO format)
- **Score**: Job relevance score (higher = better match)
- **Title**: Job title
- **Company**: Company name
- **Location**: Job location
- **Remote**: Yes/No
- **Source**: Data source (greenhouse, lever, linkedin_rss, indeed_rss)
- **URL**: Link to job posting
- **Tags**: Matching keywords (comma-separated)

## Tips

- Use specific keywords for better results (e.g., "python backend engineer" vs "engineer")
- Multiple keywords: "python, remote, backend" will find jobs matching any of these
- CSV opens in Excel, Google Sheets, or any spreadsheet app
- URL column is clickable in most spreadsheet apps

