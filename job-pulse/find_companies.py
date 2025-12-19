#!/usr/bin/env python3
"""Script to test and find working Greenhouse/Lever companies."""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Comprehensive list of potential companies across industries
COMPANIES_TO_TEST = [
    # Tech/Software
    "stripe", "dropbox", "shopify", "airbnb", "uber", "pinterest", "slack", "zoom",
    "doordash", "instacart", "robinhood", "coinbase", "square", "palantir",
    "asana", "notion", "figma", "canva", "atlassian", "github", "gitlab",
    "databricks", "snowflake", "mongodb", "elastic", "redis", "twilio", "sendgrid",
    "stripe", "plaid", "brex", "mercury", "chime", "revolut", "n26",
    "okta", "auth0", "1password", "lastpass", "cloudflare", "fastly",
    "vercel", "netlify", "heroku", "digitalocean", "linode", "vultr",
    "squarespace", "wix", "webflow", "shopify", "bigcommerce", "woocommerce",
    "spotify", "netflix", "hulu", "disney", "paramount", "warner",
    "reddit", "twitter", "facebook", "meta", "snapchat", "tiktok", "discord",
    "linkedin", "microsoft", "google", "apple", "amazon", "tesla",
    
    # Banking/Finance
    "goldman", "jpmorgan", "morganstanley", "bankofamerica", "wellsfargo",
    "citigroup", "americanexpress", "visa", "mastercard", "discover",
    "chase", "capitalone", "usbank", "pnc", "tdbank",
    
    # Healthcare
    "pfizer", "moderna", "jnj", "merck", "gilead", "biogen",
    "cvs", "walgreens", "humana", "unitedhealth", "anthem", "cigna",
    
    # Retail/Consumer
    "walmart", "target", "costco", "homedepot", "lowes", "bestbuy",
    "nike", "adidas", "underarmour", "lululemon", "patagonia",
    
    # Consulting
    "mckinsey", "bain", "bcg", "deloitte", "pwc", "ey", "kpmg",
    "accenture", "capgemini", "cognizant", "tcs", "infosys",
    
    # Media/Entertainment
    "disney", "netflix", "hbo", "paramount", "comcast", "verizon",
    "att", "t-mobile", "sprint",
    
    # More Tech
    "salesforce", "oracle", "sap", "adobe", "intel", "nvidia", "amd",
    "qualcomm", "broadcom", "cisco", "juniper", "arista",
    "vmware", "citrix", "nutanix", "purestorage", "netapp",
    "splunk", "newrelic", "datadog", "dynatrace", "pagerduty",
    "servicenow", "zendesk", "intercom", "hubspot", "salesforce",
    "tableau", "looker", "qlik", "powerbi", "domo",
    "workday", "adp", "paycom", "paylocity", "bamboohr",
    "gusto", "justworks", "rippling", "deel", "remote",
    
    # Startups/Unicorns
    "instacart", "doordash", "uber", "lyft", "airbnb", "robinhood",
    "coinbase", "stripe", "klarna", "affirm", "afterpay",
    "canva", "figma", "notion", "airtable", "coda",
    "robinhood", "webull", "sofi", "chime", "vivid",
    "rivian", "lucid", "waymo", "cruise", "zoox",
]

def test_greenhouse(company):
    """Test if a company uses Greenhouse."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) or (isinstance(data, dict) and 'jobs' in data):
                count = len(data) if isinstance(data, list) else len(data.get('jobs', []))
                return (True, company, count)
    except:
        pass
    return (False, company, 0)

def test_lever(company):
    """Test if a company uses Lever."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return (True, company, len(data))
    except:
        pass
    return (False, company, 0)

print("Testing companies... This may take a few minutes...")
print(f"Testing {len(COMPANIES_TO_TEST)} companies\n")

greenhouse_working = []
lever_working = []

with ThreadPoolExecutor(max_workers=20) as executor:
    # Test Greenhouse
    future_to_company = {executor.submit(test_greenhouse, c): c for c in COMPANIES_TO_TEST}
    for future in as_completed(future_to_company):
        works, company, count = future.result()
        if works:
            greenhouse_working.append((company, count))
            print(f"✅ Greenhouse: {company} ({count} jobs)")
    
    time.sleep(1)
    
    # Test Lever
    future_to_company = {executor.submit(test_lever, c): c for c in COMPANIES_TO_TEST}
    for future in as_completed(future_to_company):
        works, company, count = future.result()
        if works:
            lever_working.append((company, count))
            print(f"✅ Lever: {company} ({count} jobs)")

print(f"\n{'='*60}")
print(f"Found {len(greenhouse_working)} Greenhouse companies")
print(f"Found {len(lever_working)} Lever companies")
print(f"{'='*60}")

# Sort by job count
greenhouse_working.sort(key=lambda x: x[1], reverse=True)
lever_working.sort(key=lambda x: x[1], reverse=True)

print("\nGreenhouse companies (sorted by job count):")
for company, count in greenhouse_working[:50]:
    print(f"  - {company} ({count} jobs)")

print("\nLever companies (sorted by job count):")
for company, count in lever_working[:50]:
    print(f"  - {company} ({count} jobs)")

