# How to Add Indeed RSS Feeds

## ✅ Good News: Indeed RSS Connector Already Exists!

The Indeed RSS connector is already built and integrated into the system. You just need to:
1. Find Indeed RSS feed URLs
2. Add them to your `.env` file

---

## 📋 Step-by-Step Guide

### Step 1: Find Indeed RSS Feed URLs

#### Method 1: From Indeed Search Results (Recommended)

1. **Go to Indeed.com**: https://www.indeed.com

2. **Search for jobs** (e.g., "software engineer")

3. **Apply filters**:
   - Location (e.g., "San Francisco, CA" or leave empty for all)
   - Job type (Full-time, Part-time, etc.)
   - Date posted (e.g., "Last 24 hours" or "Last 7 days")

4. **Copy the search URL** from your browser's address bar
   - Example: `https://www.indeed.com/jobs?q=software+engineer&l=San+Francisco%2C+CA&sort=date&fromage=1`

5. **Convert to RSS format**:
   - Replace `/jobs?` with `/rss?`
   - Example RSS URL: `https://www.indeed.com/rss?q=software+engineer&l=San+Francisco%2C+CA&sort=date&fromage=1`

#### Method 2: RSS Feed Parameters

Indeed RSS feeds use these parameters:
- `q` = Search query (job title/keywords)
- `l` = Location (optional, e.g., "San+Francisco%2C+CA" or leave empty)
- `sort=date` = Sort by date (recommended)
- `fromage=1` = Jobs posted in last 24 hours
  - `fromage=3` = Last 3 days
  - `fromage=7` = Last 7 days
  - `fromage=30` = Last 30 days

**Example RSS URLs:**

```
# Software engineer jobs, last 24 hours, anywhere
https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1

# Software engineer in San Francisco, last 7 days
https://www.indeed.com/rss?q=software+engineer&l=San+Francisco%2C+CA&sort=date&fromage=7

# Data scientist jobs, remote, last 3 days
https://www.indeed.com/rss?q=data+scientist&l=Remote&sort=date&fromage=3

# Python developer in New York, last 24 hours
https://www.indeed.com/rss?q=python+developer&l=New+York%2C+NY&sort=date&fromage=1
```

#### Method 3: Test RSS URL

Before adding to `.env`, test the RSS URL:
1. Open the RSS URL in your browser
2. You should see XML/RSS feed content (not HTML)
3. If you see HTML or an error, the URL is invalid

---

### Step 2: Create/Edit `.env` File

1. **Navigate to the project root**:
   ```bash
   cd "/Users/wasifkarim/Desktop/Job Searching/job-pulse"
   ```

2. **Create `.env` file** (if it doesn't exist):
   ```bash
   touch .env
   ```

3. **Open `.env` file** in your text editor

4. **Add Indeed RSS URLs**:

   ```env
   # Indeed RSS Feed URLs (comma-separated)
   INDEED_RSS_URLS=https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1,https://www.indeed.com/rss?q=data+scientist&sort=date&fromage=1
   ```

   **Format:**
   - Multiple URLs separated by commas
   - No spaces around commas
   - Each URL on one line (or use `\` for line continuation)

   **Example with multiple feeds:**
   ```env
   INDEED_RSS_URLS=https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1,https://www.indeed.com/rss?q=software+engineer&l=San+Francisco%2C+CA&sort=date&fromage=7,https://www.indeed.com/rss?q=data+scientist&sort=date&fromage=1,https://www.indeed.com/rss?q=python+developer&sort=date&fromage=1
   ```

---

### Step 3: Restart the UI Server

After adding Indeed RSS URLs to `.env`:

1. **Stop the current server** (if running):
   ```bash
   pkill -f "python.*run_ui"
   ```

2. **Start the server again**:
   ```bash
   cd "/Users/wasifkarim/Desktop/Job Searching/job-pulse"
   source .venv/bin/activate
   python run_ui.py
   ```

3. **Test the search** - Indeed jobs should now appear in results!

---

## 📝 Complete `.env` File Example

Here's what a complete `.env` file might look like:

```env
# Time window (hours)
MAX_AGE_HOURS=48

# Keywords (optional, comma-separated)
KEYWORDS=software engineer,python,data scientist

# Indeed RSS Feeds (comma-separated)
INDEED_RSS_URLS=https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1,https://www.indeed.com/rss?q=data+scientist&sort=date&fromage=1

# LinkedIn RSS Feeds (optional)
# LINKEDIN_RSS_URLS=

# Glassdoor RSS Feeds (optional)
# GLASSDOOR_RSS_URLS=

# Handshake RSS Feeds (optional)
# HANDSHAKE_RSS_URLS=

# SQLite Database Path
SQLITE_PATH=./jobs.db

# Google Sheets Export (optional)
# GOOGLE_SHEET_ID=
# GOOGLE_SERVICE_ACCOUNT_JSON=
# EXPORT_SHEET_TAB=Jobs
```

---

## 🔍 Tips for Best Results

### 1. Use Multiple Feeds for Better Coverage

Create different feeds for:
- Different job roles (software engineer, data scientist, product manager)
- Different locations (San Francisco, New York, Remote)
- Different time ranges (24h, 7d, 30d)

### 2. URL Encoding

When copying URLs, Indeed automatically URL-encodes them. Common encodings:
- Space = `+` or `%20`
- Comma = `%2C`
- `&` = `%26` (but usually stays as `&`)

**Example:**
- Location: "San Francisco, CA"
- Encoded: `San+Francisco%2C+CA`

### 3. Date Filters

Use `fromage` parameter to control how recent jobs are:
- `fromage=1` = Last 24 hours (recommended for fresh jobs)
- `fromage=3` = Last 3 days
- `fromage=7` = Last 7 days
- `fromage=30` = Last 30 days

**Note:** The system also applies its own time window filter (24h, 48h, 1 week, etc.) from the UI, so you can use broader `fromage` values and let the UI filter further.

### 4. Remote Jobs

For remote jobs, use:
```
https://www.indeed.com/rss?q=software+engineer&l=Remote&sort=date&fromage=1
```

---

## ✅ Verify It's Working

After adding Indeed RSS URLs and restarting the server:

1. **Check server logs** when you search:
   ```
   INFO Fetching Indeed RSS: 2 feeds
   INFO Fetched X entries from Indeed RSS feed: ...
   ```

2. **Search in the UI** - Indeed jobs should appear in results

3. **Check CSV export** - Indeed jobs should have `Source: indeed_rss` in the CSV

---

## 🐛 Troubleshooting

### Problem: No Indeed jobs appearing

**Check:**
1. ✅ RSS URLs are correctly formatted in `.env`
2. ✅ URLs are comma-separated (no spaces)
3. ✅ Server was restarted after editing `.env`
4. ✅ RSS URLs are valid (test in browser)

**Test RSS URL:**
```bash
curl "YOUR_RSS_URL_HERE" | head -20
```
Should return XML, not HTML.

### Problem: RSS feed returns HTML instead of XML

**Solution:** 
- Make sure you're using `/rss?` not `/jobs?`
- Check that the URL parameters are correct
- Indeed may have changed their RSS format - try a different search

### Problem: Jobs from Indeed not matching keywords

**Solution:**
- Indeed job titles may not always contain exact keywords
- The system matches keywords in title/company/location
- Try broader keywords or check the actual job titles in Indeed

---

## 📚 Additional Resources

- **Indeed Help**: https://www.indeed.com/help
- **RSS Format**: Indeed RSS feeds use standard RSS 2.0 format
- **URL Encoding**: Use URL encoder tools if needed (https://www.urlencoder.org/)

---

## 🎯 Quick Start (Copy-Paste Ready)

1. **Create `.env` file** in `job-pulse/` directory
2. **Add this line**:
   ```env
   INDEED_RSS_URLS=https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1
   ```
3. **Restart server**
4. **Search in UI** - Indeed jobs should appear!

---

That's it! Indeed RSS is now integrated. 🎉

