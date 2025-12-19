# CSV Analysis Summary: Software Engineering Jobs

## Executive Summary
- **Total Jobs Found**: 606
- **Date Range**: Last 48 hours
- **Companies**: 4 companies active
- **Keyword Match Rate**: 0.5% (3 jobs)

## Detailed Breakdown

### By Company
1. **Stripe**: 547 jobs (90.3%) - Dominates results
2. **Airbnb**: 26 jobs (4.3%)
3. **Dropbox**: 23 jobs (3.8%)
4. **Pinterest**: 10 jobs (1.7%)

### Job Freshness
- **0-6 hours**: 23 jobs (3.8%)
- **6-12 hours**: 3 jobs (0.5%)
- **12-24 hours**: 12 jobs (2.0%)
- **24-48 hours**: 568 jobs (93.7%) ← Most jobs are 24-48 hours old
- **Average age**: 42.1 hours

### Keyword Matching
- **Jobs with tags**: 3 (0.5%)
- **Jobs without tags**: 603 (99.5%)

This indicates that while jobs are being fetched, most don't contain "software engineering" in their title/company/location fields. They're still included because the system shows ALL jobs from the last 48 hours, using keywords only for scoring/sorting.

### Remote Work
- **Remote jobs**: 1 (0.2%)
- **On-site jobs**: 605 (99.8%)

Very few remote opportunities in this batch.

## Insights & Recommendations

### ✅ What's Working
1. **Fresh job data**: All jobs are within 48 hours (as configured)
2. **Large volume from major companies**: 606 jobs is substantial
3. **Good variety of companies**: Even with only 4 active, they represent different sectors

### ⚠️ Areas for Improvement

1. **Limited Company Diversity**
   - Only 4 out of 87 companies had jobs in last 48 hours
   - 90% of jobs from one company (Stripe)
   - **Recommendation**: This is normal - not all companies post jobs daily. Consider:
     - Expanding search window to 72 hours for more diversity
     - Adding more active hiring companies
     - Checking if other companies use different job board formats

2. **Low Keyword Match Rate**
   - Only 0.5% of jobs matched "software engineering"
   - **Recommendation**: 
     - This is expected - keywords are used for scoring, not filtering
     - Jobs are still shown even without keyword matches
     - Try broader searches or use multiple keyword variations

3. **Remote Opportunities**
   - Only 1 remote job found
   - **Recommendation**: 
     - Add remote-specific keywords to search
     - Filter for remote roles in post-processing
     - Some companies may not mark roles as remote in job titles

## Next Steps

1. **Try Different Searches**:
   - "software engineer" (singular)
   - "backend engineer", "frontend engineer", "full stack"
   - "developer", "programmer", "engineering"
   - Multiple keywords: "software engineer, developer, backend"

2. **Expand Time Window** (optional):
   - Change `MAX_AGE_HOURS` to 72 hours for more jobs
   - Balance between freshness and volume

3. **Review Top Jobs**:
   - Focus on the 3 jobs with keyword matches (highest scores)
   - Check Stripe's 547 jobs for relevant positions

4. **Check Other Companies**:
   - Many companies in your list may post jobs less frequently
   - Consider adding companies known for frequent hiring

## Data Quality Notes

- All jobs have valid posted dates
- All jobs are within 48-hour window (as configured)
- Source data is clean (100% from Greenhouse API)
- Locations are mostly empty (companies may not populate this field)

