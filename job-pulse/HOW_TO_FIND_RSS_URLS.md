# How to Find Valid RSS Feed URLs

## Current Status
✅ **User-Agent headers added** - RSS connectors now use proper browser headers
✅ **Better error messages** - Now getting HTTP 404 instead of parse errors (means URLs are wrong, not blocked)

## Step 2: Find Valid RSS Feed URLs

### Option A: LinkedIn RSS Feeds (Most Reliable Method)

LinkedIn **does not provide public RSS feeds** for job searches anymore. However, you can:

#### Method 1: Use LinkedIn Job Search API (If Available)
- LinkedIn may require API access (often requires business account)
- Check: https://www.linkedin.com/developers/

#### Method 2: Skip LinkedIn RSS, Use Greenhouse/Lever Instead
- **Recommended:** Use Greenhouse and Lever APIs (they're free and work reliably)
- Add company board slugs to `companies.yaml` (see Option B below)

---

### Option B: Greenhouse API (✅ RECOMMENDED - Easiest & Most Reliable)

Greenhouse is **free** and **doesn't require authentication**. Most tech companies use it.

#### How to Find Greenhouse Board Slugs:

1. **Find a company's careers page:**
   - Go to a company website (e.g., `example.com`)
   - Look for "Careers" or "Jobs" link
   - Or search: "company name careers" on Google

2. **Check if they use Greenhouse:**
   - Look at the URL: `boards.greenhouse.io/COMPANYNAME/jobs/...`
   - The `COMPANYNAME` part is the board slug

3. **Example Companies:**
   - Stripe: `stripe`
   - GitHub: `github`
   - Airbnb: `airbnb`
   - Dropbox: `dropbox`
   - Shopify: `shopify`

4. **Test the API:**
   ```bash
   curl https://boards-api.greenhouse.io/v1/boards/stripe/jobs
   ```
   If it returns JSON, it works!

5. **Add to companies.yaml:**
   ```yaml
   greenhouse_boards:
     - stripe
     - github
     - shopify
   ```

---

### Option C: Lever API (✅ RECOMMENDED - Also Free & Reliable)

Lever is another popular ATS (Applicant Tracking System) used by many companies.

#### How to Find Lever Company Identifiers:

1. **Find a company's careers page:**
   - Same process as Greenhouse

2. **Check if they use Lever:**
   - Look at the URL: `jobs.lever.co/COMPANYNAME`
   - The `COMPANYNAME` part is the identifier

3. **Example Companies:**
   - Netflix: `netflix`
   - Reddit: `reddit`
   - Twitch: `twitch`

4. **Test the API:**
   ```bash
   curl "https://api.lever.co/v0/postings/netflix?mode=json"
   ```
   If it returns JSON array, it works!

5. **Add to companies.yaml:**
   ```yaml
   lever_companies:
     - netflix
     - reddit
   ```

---

### Option D: Indeed RSS Feeds (Tricky)

Indeed RSS feeds exist but are **difficult to construct correctly**.

#### How to Find Indeed RSS URLs:

1. **Search on Indeed.com:**
   - Go to https://www.indeed.com
   - Search for jobs (e.g., "python developer")
   - Apply filters (location, date posted, etc.)

2. **Get the Search URL:**
   - Copy the URL from your browser
   - It will look like: `https://www.indeed.com/jobs?q=python+developer&l=&sort=date&fromage=1`

3. **Convert to RSS:**
   - Add `/rss` at the end: `https://www.indeed.com/jobs/rss?q=python+developer&l=&sort=date&fromage=1`
   - OR replace `/jobs` with `/rss`: `https://www.indeed.com/rss?q=python+developer&l=&sort=date&fromage=1`

4. **Test in Browser:**
   - Open the RSS URL in your browser
   - You should see XML/RSS feed
   - If you see HTML or error, the URL format is wrong

5. **Update .env:**
   ```env
   INDEED_RSS_URLS=https://www.indeed.com/rss?q=python+developer&l=&sort=date&fromage=1
   ```

**Note:** Indeed RSS feeds may still have parsing issues. Greenhouse/Lever APIs are more reliable.

---

## Quick Start Guide (Recommended Path)

### Step 1: Test Greenhouse API

```bash
# Test a few companies
curl https://boards-api.greenhouse.io/v1/boards/stripe/jobs | head -20
curl https://boards-api.greenhouse.io/v1/boards/github/jobs | head -20
```

If these return JSON, you're good!

### Step 2: Create/Update companies.yaml

```bash
cd /Users/wasifkarim/Desktop/Job\ Searching/job-pulse
```

Create or edit `companies.yaml`:
```yaml
greenhouse_boards:
  - stripe
  - github
  - shopify
  - dropbox

lever_companies:
  - netflix
  - reddit
```

### Step 3: Test the Pipeline

```bash
source .venv/bin/activate
python -m app.main --dry-run
```

You should see:
```
INFO Fetching Greenhouse: 4 boards
INFO Fetched X Greenhouse entries
INFO Normalized X jobs
```

---

## Finding More Companies

### Search for Companies Using Greenhouse:
- Google: "site:boards.greenhouse.io careers"
- Visit: https://www.greenhouse.io/customers (shows companies using Greenhouse)

### Search for Companies Using Lever:
- Google: "site:jobs.lever.co careers"
- Visit: https://www.lever.co/customers (shows companies using Lever)

---

## Testing Your URLs

### Test Greenhouse:
```bash
curl https://boards-api.greenhouse.io/v1/boards/COMPANYNAME/jobs | python -m json.tool | head -50
```

### Test Lever:
```bash
curl "https://api.lever.co/v0/postings/COMPANYNAME?mode=json" | python -m json.tool | head -50
```

### Test RSS Feed:
```bash
curl -L "YOUR_RSS_URL" | head -50
```

If you see valid JSON/XML, the URL works!

