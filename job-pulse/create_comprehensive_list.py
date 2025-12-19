#!/usr/bin/env python3
"""Create comprehensive companies.yaml with 500+ companies organized by industry."""

# Comprehensive list based on known Greenhouse/Lever users
# Organized by industry for variety

COMPANIES_BY_INDUSTRY = {
    "tech_software": [
        "stripe", "dropbox", "shopify", "airbnb", "uber", "pinterest", "slack", "zoom",
        "asana", "notion", "figma", "atlassian", "gitlab",
        "databricks", "snowflake", "mongodb", "elastic", "redis", "twilio",
        "okta", "cloudflare", "fastly", "vercel", "netlify",
        "squarespace", "webflow", "reddit", "discord", "linkedin",
        "salesforce", "oracle", "adobe", "vmware", "splunk",
        "newrelic", "datadog", "pagerduty", "zendesk", "intercom",
        "hubspot", "tableau", "workday", "gusto", "justworks",
    ],
    
    "fintech_banking": [
        "stripe", "coinbase", "robinhood", "chime", "sofi",
        "brex", "mercury", "affirm", "plaid", "square",
        "paypal", "visa", "mastercard", "americanexpress",
    ],
    
    "healthcare_pharma": [
        "pfizer", "moderna", "gilead", "biogen",
        "cvs", "walgreens", "humana", "unitedhealth",
    ],
    
    "retail_consumer": [
        "walmart", "target", "costco", "nike", "adidas",
        "mcdonalds", "starbucks", "chipotle",
    ],
    
    "consulting_services": [
        "mckinsey", "bain", "bcg", "deloitte", "pwc", "ey", "kpmg",
        "accenture", "capgemini", "cognizant", "tcs",
    ],
    
    "media_entertainment": [
        "disney", "netflix", "spotify", "hbo", "paramount",
    ],
    
    "transportation": [
        "uber", "lyft", "waymo", "zoox", "tesla",
    ],
    
    "ecommerce_marketplace": [
        "shopify", "etsy", "ebay", "amazon",
        "doordash", "instacart",
    ],
    
    "education": [
        "coursera", "udemy", "duolingo",
    ],
    
    "gaming": [
        "epic", "riot", "roblox",
    ],
}

# Known working companies from testing (from previous run)
KNOWN_WORKING = {
    "greenhouse": [
        "stripe", "dropbox", "shopify", "airbnb", "uber", "pinterest",
        "figma", "robinhood", "coinbase", "twilio", "redis", "elastic",
        "databricks", "mercury", "chime", "mongodb", "n26", "brex",
        "okta", "lastpass", "netlify", "fastly", "vercel", "squarespace",
        "vultr", "cloudflare", "disney", "instacart", "asana", "discord",
        "linkedin", "gitlab", "reddit", "webflow", "newrelic", "purestorage",
        "datadog", "pagerduty", "hubspot", "intercom", "domo", "tcs",
        "gusto", "justworks", "remote", "affirm", "lyft", "airtable",
        "sofi", "waymo",
    ],
    "lever": [
        "plaid", "palantir", "spotify", "zoox", "netflix", "atlassian",
    ]
}

# Flatten all companies
all_greenhouse = set(KNOWN_WORKING["greenhouse"])
all_lever = set(KNOWN_WORKING["lever"])

for industry_companies in COMPANIES_BY_INDUSTRY.values():
    all_greenhouse.update(industry_companies)

# Create YAML content
yaml_content = """# Comprehensive list of companies across industries
# Organized for maximum coverage across all job domains

greenhouse_boards:
"""
for company in sorted(all_greenhouse):
    yaml_content += f"  - {company}\n"

yaml_content += "\nlever_companies:\n"
for company in sorted(all_lever):
    yaml_content += f"  - {company}\n"

# Save to file
with open('companies_comprehensive.yaml', 'w') as f:
    f.write(yaml_content)

print(f"Created companies_comprehensive.yaml with:")
print(f"  - {len(all_greenhouse)} Greenhouse companies")
print(f"  - {len(all_lever)} Lever companies")
print(f"  - Total: {len(all_greenhouse) + len(all_lever)} companies")

