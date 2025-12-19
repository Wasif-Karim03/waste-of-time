# Guide: Adding More Job Platforms

This guide explains how to configure the job aggregation pipeline to fetch jobs from multiple platforms.

## Currently Supported Platforms

### ✅ Working (Free APIs - Recommended)

1. **Greenhouse** - Free API, no authentication required
   - Configure in `companies.yaml`: `greenhouse_boards: [stripe, dropbox, ...]`
   - Test: `curl https://boards-api.greenhouse.io/v1/boards/stripe/jobs`

2. **Lever** - Free API, no authentication required
   - Configure in `companies.yaml`: `lever_companies: [netflix, reddit, ...]`
   - Test: `curl "https://api.lever.co/v0/postings/netflix?mode=json"`

### ⚠️ RSS Feeds (Require Valid URLs)

3. **Indeed RSS** - Public RSS feeds available
4. **LinkedIn RSS** - Limited/No public RSS feeds (LinkedIn removed most RSS support)
5. **Glassdoor RSS** - Limited/No public RSS feeds
6. **Handshake RSS** - Requires institutional access

---

## How to Add Platforms

### Option 1: Greenhouse/Lever (Easiest & Most Reliable)

These are free APIs that work immediately. Just add company names to `companies.yaml`:

```yaml
greenhouse_boards:
  - stripe
  - dropbox
  - shopify
  - airbnb
  - uber

lever_companies:
  - netflix
  - reddit
  - twitch
```

**To find companies:**
1. Visit company careers page
2. Check URL for `boards.greenhouse.io/COMPANYNAME` or `jobs.lever.co/COMPANYNAME`
3. Test the API before adding

### Option 2: RSS Feeds (Indeed, LinkedIn, Glassdoor, Handshake)

RSS feeds require valid URLs. Update your `.env` file:

```env
# Indeed RSS (most reliable RSS source)
INDEED_RSS_URLS=https://www.indeed.com/rss?q=software+engineer&l=&sort=date&fromage=1,https://www.indeed.com/rss?q=python+developer&l=&sort=date&fromage=1

# LinkedIn RSS (limited availability)
LINKEDIN_RSS_URLS=

# Glassdoor RSS (may not exist)
GLASSDOOR_RSS_URLS=

# Handshake RSS (requires institutional access)
HANDSHAKE_RSS_URLS=
```

**Finding Valid RSS URLs:**

#### Indeed RSS:
1. Go to https://www.indeed.com
2. Search for jobs (e.g., "software engineer")
3. Copy the search URL
4. Convert to RSS: Replace `/jobs` with `/rss` or add `/rss` before `?q=`
   - Example: `https://www.indeed.com/rss?q=software+engineer&sort=date&fromage=1`
5. Test in browser - should show XML/RSS feed

#### LinkedIn RSS:
⚠️ **LinkedIn removed most RSS feed support.** You may need to:
- Use LinkedIn's official API (requires approval)
- Use third-party APIs (may require payment)
- Focus on Greenhouse/Lever instead (most companies post there too)

#### Glassdoor RSS:
Glassdoor typically doesn't provide public RSS feeds. You may need to:
- Use Glassdoor's API (may require business account)
- Use third-party aggregation services
- Focus on other platforms

#### Handshake RSS:
Handshake is primarily for students/universities and requires:
- Institutional/university credentials
- API access through your school
- Contact Handshake support for RSS feed URLs

---

## Recommended Approach

**For maximum job coverage with minimal setup:**

1. **Use Greenhouse/Lever APIs** (Free, reliable, immediate)
   - Add 20-50 companies to `companies.yaml`
   - Most tech companies use these platforms
   - Gets you hundreds of jobs immediately

2. **Add Indeed RSS** (Free, works with valid URLs)
   - Get valid RSS URLs from Indeed search
   - Add to `.env` as `INDEED_RSS_URLS`

3. **Skip LinkedIn/Glassdoor/Handshake RSS** (Limited/no public access)
   - These platforms don't offer reliable RSS feeds
   - Would require paid APIs or scraping (against terms of service)

---

## Testing Your Configuration

After adding platforms, test the pipeline:

```bash
# Dry run to see what's being fetched
python -m app.main --dry-run

# Check logs for each platform:
# - "Fetching Greenhouse: X boards"
# - "Fetching Lever: X companies"  
# - "Fetching Indeed RSS: X feeds"
# - "Fetched X entries"
```

---

## Example: Finding More Greenhouse Companies

1. **Search Google:** "site:boards.greenhouse.io careers"
2. **Visit companies:** Click through to find board slugs
3. **Test API:** `curl https://boards-api.greenhouse.io/v1/boards/COMPANYNAME/jobs`
4. **Add to companies.yaml:** If API returns JSON, add the company

**Popular Greenhouse companies:**
- stripe, dropbox, shopify, airbnb, uber, pinterest, github (some), slack, zoom

**Popular Lever companies:**
- netflix, reddit, twitch, spotify, instacart, robinhood

---

## Limitations

- **LinkedIn:** No public RSS feeds, API requires approval
- **Glassdoor:** No public RSS feeds, API may require business account
- **Handshake:** Requires institutional access
- **Indeed:** RSS feeds work but URLs must be correctly formatted

**Solution:** Focus on Greenhouse/Lever APIs - they're free, reliable, and cover most tech companies!

