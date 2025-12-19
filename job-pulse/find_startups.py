#!/usr/bin/env python3
"""Find and test startup and smaller companies for Greenhouse/Lever."""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Comprehensive list of startups and smaller companies across industries
# Mix of known startups, growing companies, and industry-specific firms
STARTUP_COMPANIES = [
    # Dev Tools & Infrastructure Startups
    "railway", "render", "fly", "flyio", "supabase", "planetscale", "cockroach",
    "neon", "turso", "convex", "replit", "codesandbox", "cursor", "linear",
    "retool", "airplane", "n8n", "zapier", "make", "bubble", "webflow",
    "framer", "modular", "dbt", "databricks", "snowflake",
    
    # AI/ML Startups
    "anthropic", "cohere", "ai21", "together", "replicate", "huggingface",
    "wandb", "weights", "cerebras", "sambanova", "scale", "labelbox",
    "snorkel", "baseten", "modal", "runway", "elevenlabs", "perplexity",
    
    # Fintech Startups
    "mercury", "ramp", "divvy", "divvyhq", "card", "stripe", "brex",
    "radicle", "unit", "synapse", "treasuryprime", "finix", "modern",
    "teller", "alloy", "unit21", "sardine", "checkout", "adyen",
    
    # SaaS & Productivity Startups
    "notion", "coda", "clickup", "monday", "asana", "linear", "shortcut",
    "height", "plane", "jira", "basecamp", "wrike", "smartsheet",
    "airtable", "smartsheet", "airtable",
    
    # Communication & Collaboration
    "discord", "slack", "mattermost", "rocketchat", "element", "signal",
    "telegram", "whatsapp", "clubhouse", "twitter", "meta",
    
    # E-commerce & Marketplace Startups
    "shopify", "woocommerce", "bigcommerce", "commercetools", "medusa",
    "vendure", "saleor", "strapi", "dato", "contentful", "sanity",
    
    # Developer Tools
    "vercel", "netlify", "cloudflare", "fastly", "bunny", "stackpath",
    "github", "gitlab", "bitbucket", "sourcegraph", "gitpod", "codespace",
    
    # Security Startups
    "1password", "lastpass", "dashlane", "bitwarden", "auth0", "okta",
    "snyk", "veracode", "checkmarx", "contrast", "snyk",
    
    # Analytics & Data Startups
    "mixpanel", "amplitude", "segment", "heap", "posthog", "fullstory",
    "hotjar", "logrocket", "sentry", "rollbar", "bugsnag", "honeybadger",
    
    # Marketing & Sales Startups
    "hubspot", "salesforce", "pipedrive", "close", "outreach", "apollo",
    "zoominfo", "clearbit", "hunter", "mailchimp", "sendgrid", "postmark",
    "customerio", "iterable", "klaviyo", "omnisend",
    
    # Healthcare Tech Startups
    "ro", "hims", "hers", "teladoc", "amwell", "doximity", "tempus",
    "flatiron", "komodo", "insitro", "recursion", "zymergen",
    
    # EdTech Startups
    "coursera", "udemy", "udacity", "masterclass", "skillshare", "pluralsight",
    "codeschool", "treehouse", "lambda", "galvanize", "hackreactor",
    
    # Real Estate Tech
    "zillow", "redfin", "compass", "opendoor", "knock", "offerpad",
    "rentals", "apartments", "streeteasy", "trulia", "realtor",
    
    # Food & Delivery Startups
    "doordash", "ubereats", "grubhub", "postmates", "instacart", "gopuff",
    "goat", "stockx", "thredup", "poshmark", "mercari", "depop",
    
    # Travel Startups
    "airbnb", "vrbo", "expedia", "booking", "kayak", "hopper", "skyscanner",
    "tripadvisor", "getyourguide", "klook", "viator", "tours",
    
    # Gaming Startups
    "roblox", "epic", "unity", "riot", "supercell", "king", "zynga",
    "scopely", "playtika", "moonactive", "niantic", "pokemon",
    
    # Media & Entertainment Startups
    "netflix", "hulu", "disney", "paramount", "warner", "peacock",
    "spotify", "pandora", "siriusxm", "iheartradio", "clubhouse",
    
    # Transportation & Mobility
    "uber", "lyft", "via", "juno", "gett", "bolt", "lime", "bird",
    "spin", "jump", "revel", "citibike", "bikeshare",
    
    # Climate & Energy Startups
    "tesla", "rivian", "lucid", "nio", "xpeng", "li", "fisker",
    "arcadia", "rooftop", "sunrun", "vivint", "sunpower",
    
    # Biotech & Pharma Startups
    "moderna", "biontech", "curevac", "novavax", "pfizer", "jnj",
    "regeneron", "gilead", "biogen", "vertex", "amgen", "bms",
    
    # HR & Recruiting Startups
    "greenhouse", "lever", "workable", "smartrecruiters", "icims",
    "jobvite", "cornerstone", "successfactors", "workday", "bamboohr",
    "zenefits", "gusto", "justworks", "rippling", "deel", "remote",
    "oyster", "pilot", "boundless", "papaya",
    
    # Legal Tech Startups
    "legalzoom", "rocketlawyer", "lawdepot", "documently", "clio",
    "mycase", "filevine", "casepeer", "lawpay", "timekeeper",
    
    # Insurance Tech Startups
    "lemonade", "metromile", "root", "clearcover", "hippo", "kin",
    "next", "trov", "slice", "cuvva", "bought", "many",
    
    # Construction & PropTech
    "procore", "autodesk", "buildertrend", "jobber", "housecall",
    "jobber", "servicetitan", "fieldpulse", "workiz", "fieldwire",
    
    # More Growing Startups (Series A-C)
    "figma", "canva", "notion", "airtable", "coda", "notion",
    "linear", "height", "plane", "shortcut", "jira", "monday",
    "clickup", "wrike", "smartsheet", "asana", "basecamp",
]

# Remove duplicates and sort
UNIQUE_STARTUPS = sorted(list(set(STARTUP_COMPANIES)))

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

print(f"Testing {len(UNIQUE_STARTUPS)} startup/smaller companies...\n")

found_greenhouse = []
found_lever = []

with ThreadPoolExecutor(max_workers=30) as executor:
    futures = []
    for company in UNIQUE_STARTUPS:
        futures.append(executor.submit(test_greenhouse, company))
        futures.append(executor.submit(test_lever, company))
    
    for future in as_completed(futures):
        result = future.result()
        if result:
            source, company, count = result
            if source == "greenhouse" and company not in [c[0] for c in found_greenhouse]:
                found_greenhouse.append((company, count))
                print(f"✅ Greenhouse: {company} ({count} jobs)")
            elif source == "lever" and company not in [c[0] for c in found_lever]:
                found_lever.append((company, count))
                print(f"✅ Lever: {company} ({count} jobs)")

# Sort by job count
found_greenhouse.sort(key=lambda x: x[1], reverse=True)
found_lever.sort(key=lambda x: x[1], reverse=True)

print(f"\n{'='*60}")
print(f"Found {len(found_greenhouse)} Greenhouse startups")
print(f"Found {len(found_lever)} Lever startups")
print(f"Total: {len(found_greenhouse) + len(found_lever)} new companies")
print(f"{'='*60}")

# Save results
with open('found_startups.txt', 'w') as f:
    f.write("# Found startup companies\n\n")
    f.write("greenhouse_boards:\n")
    for company, count in found_greenhouse:
        f.write(f"  - {company}  # {count} jobs\n")
    f.write("\nlever_companies:\n")
    for company, count in found_lever:
        f.write(f"  - {company}  # {count} jobs\n")

print(f"\nResults saved to found_startups.txt")

