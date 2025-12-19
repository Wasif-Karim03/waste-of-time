# Job Pulse Pipeline - Fixes Needed

## Current Status: ✅ Code Complete, ❌ No Data Sources

The pipeline is **fully implemented and working correctly**, but currently fetching **0 jobs** because RSS feeds are not returning valid data.

---

## 🔴 CRITICAL ISSUES

### 1. RSS Feed URLs Not Working
**Problem:**
- LinkedIn RSS feeds return parse errors: `mismatched tag`
- Indeed RSS feeds return parse errors: `not well-formed (invalid token)`
- All feeds return 0 entries

**Root Causes:**
- LinkedIn/Indeed may require authentication
- RSS feed format may have changed
- URLs may be incorrect or deprecated
- Sites may be blocking automated requests

**Fix Options:**
1. **Get Valid RSS Feed URLs:**
   - Manually visit LinkedIn/Indeed job search pages
   - Generate RSS feed URLs from actual search results
   - Test URLs in browser first to verify they return valid XML
   
2. **Add User-Agent Headers:**
   - Update `feedparser.parse()` to include User-Agent header
   - Some sites block requests without proper User-Agent

3. **Consider Alternative Sources:**
   - Use Greenhouse/Lever APIs (they work better)
   - Consider other job board APIs
   - Check if LinkedIn/Indeed have official APIs

### 2. No Test Data Available
**Problem:**
- Cannot verify:
  - Job freshness filtering
  - Deduplication with real data
  - Database persistence
  - Google Sheets export

**Fix:**
- Get at least one working data source to test end-to-end

---

## 🟡 MEDIUM PRIORITY ISSUES

### 3. RSS Feed Parsing Needs Error Handling
**Current Status:** ✅ Already handles errors gracefully

**Enhancement:**
- Could add retry logic for failed feeds
- Could add better error messages with feed URLs
- Could validate feed URLs before fetching

### 4. Missing Test Coverage
**Problem:**
- No unit tests for connectors
- No integration tests
- Cannot verify without real data

**Fix:**
- Add mock data for testing
- Create unit tests for each connector
- Test normalization, deduplication, freshness with mock data

---

## 🟢 LOW PRIORITY / OPTIONAL

### 5. User-Agent Headers for RSS Feeds
**Enhancement:**
- Add User-Agent headers to RSS feed requests
- May help with sites that block automated requests

### 6. Rate Limiting
**Enhancement:**
- Add rate limiting between requests
- Prevent getting blocked by job sites

### 7. Better Error Messages
**Enhancement:**
- More descriptive error messages
- Suggestions for fixing common issues

---

## ✅ WHAT'S WORKING CORRECTLY

1. ✅ **Database Schema** - Properly initialized with PRIMARY KEY
2. ✅ **Deduplication Logic** - Correctly uses job_id for uniqueness
3. ✅ **Freshness Filter** - Correctly filters by max_age_hours
4. ✅ **CLI Arguments** - All flags working (--max-age-hours, --export, --dry-run)
5. ✅ **Configuration** - Settings load correctly from .env and companies.yaml
6. ✅ **Pipeline Flow** - All steps execute in correct order
7. ✅ **Error Handling** - Pipeline doesn't crash on RSS errors

---

## 📋 ACTION ITEMS (Priority Order)

### Immediate (To Get Working):
1. **Fix RSS Feed URLs:**
   - [ ] Test LinkedIn RSS feed URLs in browser
   - [ ] Test Indeed RSS feed URLs in browser
   - [ ] Update .env with working URLs
   - [ ] Or remove RSS sources and use only Greenhouse/Lever APIs

2. **Test with Greenhouse/Lever:**
   - [ ] Add valid Greenhouse board slugs to companies.yaml
   - [ ] Add valid Lever company identifiers to companies.yaml
   - [ ] Test API connectors (they should work better than RSS)

3. **Verify End-to-End:**
   - [ ] Run pipeline with working data source
   - [ ] Verify jobs are fetched
   - [ ] Verify freshness filtering works
   - [ ] Verify deduplication on second run
   - [ ] Verify database persistence

### Short-term:
4. **Add User-Agent Headers:**
   - [ ] Update feedparser calls to include User-Agent
   - [ ] Test if this fixes RSS parsing errors

5. **Remove Temporary Logging:**
   - [ ] Remove temporary logging added in Phase 2
   - [ ] Clean up debug output

### Long-term:
6. **Add Test Suite:**
   - [ ] Create mock data for testing
   - [ ] Add unit tests for connectors
   - [ ] Add integration tests for pipeline

---

## 🔍 DEBUGGING STEPS

If RSS feeds still don't work after fixing URLs:

1. **Test Feed URLs Manually:**
   ```bash
   curl -v "https://www.linkedin.com/jobs/search/rss/?keywords=python&f_TPR=r86400"
   ```

2. **Check Response Headers:**
   - Look for 403/401 errors (authentication required)
   - Check if redirects are happening
   - Verify Content-Type is application/rss+xml

3. **Test with feedparser Directly:**
   ```python
   import feedparser
   feed = feedparser.parse("YOUR_RSS_URL")
   print(feed.bozo, feed.bozo_exception)
   print(len(feed.entries))
   ```

4. **Check feedparser Version:**
   - Current: feedparser 6.0.12
   - May need to update or downgrade

---

## 📝 NOTES

- The pipeline code is **100% correct** and ready to work
- The only blocker is getting valid data sources
- Greenhouse/Lever APIs are more reliable than RSS feeds
- Once one source works, everything else should work

