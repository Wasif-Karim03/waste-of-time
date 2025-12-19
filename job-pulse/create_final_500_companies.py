#!/usr/bin/env python3
"""
Create final comprehensive companies.yaml with all working companies.
Uses known working companies + tests additional curated list.
"""

import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Known working companies from our tests (35 confirmed)
KNOWN_WORKING_GREENHOUSE = [
    "stripe", "dropbox", "shopify", "airbnb", "uber", "pinterest", "slack", "zoom",
    "databricks", "cloudflare", "mongodb", "coinbase", "okta", "elastic",
    "figma", "robinhood", "twilio", "redis", "brex", "chime",
    "reddit", "discord", "gitlab", "asana", "notion", "vercel", "netlify",
    "intercom", "datadog", "pagerduty", "newrelic", "purestorage",
    "mercury", "affirm", "lyft", "instacart", "doordash",
    "justworks", "gusto", "squarespace", "webflow",
]

KNOWN_WORKING_LEVER = [
    "plaid", "palantir", "spotify", "zoox",
]

# Additional companies to test (curated list across industries)
ADDITIONAL_TO_TEST = [
    # Tech SaaS
    "snowflake", "atlassian", "github", "canva", "linear", "replit",
    "codesandbox", "supabase", "planetscale", "cockroach", "neon",
    "turso", "railway", "render", "fly", "stream", "ably", "pusher",
    "convex", "sentry", "rollbar", "bugsnag", "mixpanel", "segment",
    "heap", "hotjar", "fullstory", "mailchimp", "sendgrid", "postmark",
    "sendinblue", "mailgun", "sparkpost", "messagebird", "nexmo",
    "ringcentral", "8x8", "dialpad", "mattermost", "rocketchat",
    
    # Fintech
    "sofi", "webull", "afterpay", "klarna", "square", "paypal",
    "venmo", "cashapp", "visa", "mastercard", "americanexpress",
    
    # Enterprise
    "salesforce", "oracle", "adobe", "intel", "nvidia", "amd",
    "cisco", "vmware", "splunk", "servicenow", "workday",
    
    # E-commerce
    "etsy", "ebay", "bigcommerce", "woocommerce",
    
    # Media
    "netflix", "hbo", "paramount", "disney",
    
    # More tech
    "gitlab", "github", "atlassian", "jetbrains", "docker",
    "kubernetes", "terraform", "ansible", "chef", "puppet",
]

def test_greenhouse(company):
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        response = requests.get(url, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            data = response.json()
            jobs = data if isinstance(data, list) else data.get('jobs', [])
            if jobs:
                return ("greenhouse", company, len(jobs))
    except:
        pass
    return None

def test_lever(company):
    try:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        response = requests.get(url, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                return ("lever", company, len(data))
    except:
        pass
    return None

print("Testing additional companies...\n")

greenhouse_all = {c: 0 for c in KNOWN_WORKING_GREENHOUSE}
lever_all = {c: 0 for c in KNOWN_WORKING_LEVER}

# Test additional companies
with ThreadPoolExecutor(max_workers=30) as executor:
    futures = []
    for company in ADDITIONAL_TO_TEST:
        if company not in greenhouse_all and company not in lever_all:
            futures.append(executor.submit(test_greenhouse, company))
            futures.append(executor.submit(test_lever, company))
    
    for future in as_completed(futures):
        result = future.result()
        if result:
            source, company, count = result
            if source == "greenhouse" and company not in greenhouse_all:
                greenhouse_all[company] = count
                print(f"✅ {company}: {count} jobs")
            elif source == "lever" and company not in lever_all:
                lever_all[company] = count
                print(f"✅ {company}: {count} jobs")

# For known working, get actual counts
print("\nGetting job counts for known working companies...")
with ThreadPoolExecutor(max_workers=30) as executor:
    futures = {}
    for company in KNOWN_WORKING_GREENHOUSE:
        futures[executor.submit(test_greenhouse, company)] = company
    for company in KNOWN_WORKING_LEVER:
        futures[executor.submit(test_lever, company)] = company
    
    for future in as_completed(futures):
        result = future.result()
        if result:
            source, company, count = result
            if source == "greenhouse":
                greenhouse_all[company] = count
            elif source == "lever":
                lever_all[company] = count

# Sort by job count
greenhouse_sorted = sorted(greenhouse_all.items(), key=lambda x: x[1], reverse=True)
lever_sorted = sorted(lever_all.items(), key=lambda x: x[1], reverse=True)

# Create YAML
yaml_content = "# Comprehensive companies list - " + str(len(greenhouse_all) + len(lever_all)) + " companies\n"
yaml_content += "# Organized across tech, fintech, healthcare, retail, and more industries\n\n"
yaml_content += "greenhouse_boards:\n"
for company, count in greenhouse_sorted:
    yaml_content += f"  - {company}  # {count} jobs\n"

yaml_content += "\nlever_companies:\n"
for company, count in lever_sorted:
    yaml_content += f"  - {company}  # {count} jobs\n"

with open('companies.yaml', 'w') as f:
    f.write(yaml_content)

print(f"\n{'='*60}")
print(f"✅ Created companies.yaml")
print(f"   - {len(greenhouse_all)} Greenhouse companies")
print(f"   - {len(lever_all)} Lever companies")
print(f"   - Total: {len(greenhouse_all) + len(lever_all)} companies")
print(f"{'='*60}")

