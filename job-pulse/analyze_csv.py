#!/usr/bin/env python3
"""Analyze the CSV file and provide insights."""

import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

csv_path = Path("/Users/wasifkarim/Desktop/Job Searching/jobs_software_engineering_20251218_141007.csv")

if not csv_path.exists():
    print(f"Error: File not found: {csv_path}")
    sys.exit(1)

# Read CSV
jobs = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        jobs.append(row)

total_jobs = len(jobs)
print(f"\n{'='*70}")
print(f"📊 CSV FILE ANALYSIS")
print(f"{'='*70}\n")
print(f"Total Jobs: {total_jobs}\n")

if total_jobs == 0:
    print("No jobs found in CSV file.")
    sys.exit(0)

# 1. Source breakdown
print("=" * 70)
print("📈 SOURCE BREAKDOWN")
print("=" * 70)
source_counts = Counter(job['Source'] for job in jobs)
for source, count in source_counts.most_common():
    percentage = (count / total_jobs) * 100
    print(f"  {source:20s}: {count:4d} jobs ({percentage:5.1f}%)")
print()

# 2. Top companies
print("=" * 70)
print("🏢 TOP 20 COMPANIES BY JOB COUNT")
print("=" * 70)
company_counts = Counter(job['Company'] for job in jobs)
for company, count in company_counts.most_common(20):
    percentage = (count / total_jobs) * 100
    print(f"  {company:30s}: {count:3d} jobs ({percentage:5.1f}%)")
print()

# 3. Remote vs On-site
print("=" * 70)
print("🏠 REMOTE vs ON-SITE")
print("=" * 70)
remote_counts = Counter(job.get('Remote', 'Unknown') for job in jobs)
for remote_status, count in remote_counts.most_common():
    percentage = (count / total_jobs) * 100
    print(f"  {remote_status:10s}: {count:4d} jobs ({percentage:5.1f}%)")
print()

# 4. Score distribution
print("=" * 70)
print("⭐ SCORE DISTRIBUTION")
print("=" * 70)
try:
    scores = [int(job.get('Score', 0)) for job in jobs if job.get('Score', '').isdigit()]
    if scores:
        score_ranges = {
            "8-10 (Excellent match)": sum(1 for s in scores if 8 <= s <= 10),
            "5-7 (Good match)": sum(1 for s in scores if 5 <= s <= 7),
            "3-4 (Fair match)": sum(1 for s in scores if 3 <= s <= 4),
            "0-2 (Low match)": sum(1 for s in scores if 0 <= s <= 2),
        }
        for range_name, count in score_ranges.items():
            percentage = (count / len(scores)) * 100
            print(f"  {range_name:30s}: {count:4d} jobs ({percentage:5.1f}%)")
        print(f"  Average Score: {sum(scores)/len(scores):.2f}")
        print(f"  Max Score: {max(scores)}")
        print(f"  Min Score: {min(scores)}")
except Exception as e:
    print(f"  Could not analyze scores: {e}")
print()

# 5. Location analysis
print("=" * 70)
print("📍 TOP 15 LOCATIONS")
print("=" * 70)
locations = [job.get('Location', 'Unknown').strip() for job in jobs]
location_counts = Counter(loc for loc in locations if loc and loc != '')
for location, count in location_counts.most_common(15):
    percentage = (count / total_jobs) * 100
    print(f"  {location:40s}: {count:3d} jobs ({percentage:5.1f}%)")
print()

# 6. Jobs with tags (keyword matches)
print("=" * 70)
print("🏷️  KEYWORD MATCHING")
print("=" * 70)
jobs_with_tags = [job for job in jobs if job.get('Tags', '').strip()]
jobs_without_tags = total_jobs - len(jobs_with_tags)
print(f"  Jobs WITH keyword tags: {len(jobs_with_tags):4d} ({(len(jobs_with_tags)/total_jobs)*100:5.1f}%)")
print(f"  Jobs WITHOUT keyword tags: {jobs_without_tags:4d} ({(jobs_without_tags/total_jobs)*100:5.1f}%)")
print()

# 7. Posted date analysis (if available)
print("=" * 70)
print("📅 POSTED DATE ANALYSIS")
print("=" * 70)
try:
    posted_dates = []
    for job in jobs:
        posted_at = job.get('PostedAt', '').strip()
        if posted_at:
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                posted_dates.append(dt)
            except:
                pass
    
    if posted_dates:
        now = datetime.now(posted_dates[0].tzinfo) if posted_dates[0].tzinfo else datetime.now()
        hours_old = [(now - dt).total_seconds() / 3600 for dt in posted_dates]
        
        age_ranges = {
            "0-6 hours (Very recent)": sum(1 for h in hours_old if 0 <= h < 6),
            "6-12 hours": sum(1 for h in hours_old if 6 <= h < 12),
            "12-24 hours": sum(1 for h in hours_old if 12 <= h < 24),
            "24-48 hours": sum(1 for h in hours_old if 24 <= h < 48),
            "48+ hours": sum(1 for h in hours_old if h >= 48),
        }
        
        for range_name, count in age_ranges.items():
            percentage = (count / len(posted_dates)) * 100
            print(f"  {range_name:30s}: {count:4d} jobs ({percentage:5.1f}%)")
        
        avg_hours = sum(hours_old) / len(hours_old)
        print(f"\n  Average job age: {avg_hours:.1f} hours")
        print(f"  Oldest job: {max(hours_old):.1f} hours ago")
        print(f"  Newest job: {min(hours_old):.1f} hours ago")
    else:
        print("  No valid posted dates found")
except Exception as e:
    print(f"  Could not analyze dates: {e}")
print()

# 8. Summary statistics
print("=" * 70)
print("📊 SUMMARY STATISTICS")
print("=" * 70)
print(f"  Total Jobs: {total_jobs}")
print(f"  Unique Companies: {len(company_counts)}")
print(f"  Unique Locations: {len(location_counts)}")
print(f"  Jobs with Remote option: {remote_counts.get('Yes', 0)}")
print(f"  Jobs matching keywords: {len(jobs_with_tags)}")
print()

# 9. Top companies by source
print("=" * 70)
print("🏢 TOP COMPANIES BY SOURCE")
print("=" * 70)
by_source = defaultdict(Counter)
for job in jobs:
    source = job.get('Source', 'Unknown')
    company = job.get('Company', 'Unknown')
    by_source[source][company] += 1

for source in sorted(by_source.keys()):
    print(f"\n  {source}:")
    for company, count in by_source[source].most_common(5):
        print(f"    {company:30s}: {count:3d} jobs")

print(f"\n{'='*70}\n")

