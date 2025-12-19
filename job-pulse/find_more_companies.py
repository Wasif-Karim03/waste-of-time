#!/usr/bin/env python3
"""Comprehensive script to find 500+ working Greenhouse/Lever companies."""

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Expanded comprehensive list across all industries
ALL_COMPANIES = [
    # Tech - Enterprise/SaaS
    "stripe", "dropbox", "shopify", "airbnb", "uber", "pinterest", "slack", "zoom",
    "doordash", "instacart", "robinhood", "coinbase", "square", "palantir",
    "asana", "notion", "figma", "canva", "atlassian", "gitlab",
    "databricks", "snowflake", "mongodb", "elastic", "redis", "twilio", "sendgrid",
    "plaid", "brex", "mercury", "chime", "revolut", "n26",
    "okta", "auth0", "1password", "lastpass", "cloudflare", "fastly",
    "vercel", "netlify", "heroku", "digitalocean", "vultr",
    "squarespace", "wix", "webflow", "bigcommerce",
    "spotify", "netflix", "reddit", "twitter", "meta", "snapchat", "discord",
    "linkedin", "microsoft", "google", "apple", "amazon",
    "salesforce", "oracle", "sap", "adobe", "intel", "nvidia", "amd",
    "qualcomm", "broadcom", "cisco", "juniper", "arista",
    "vmware", "citrix", "nutanix", "purestorage", "netapp",
    "splunk", "newrelic", "datadog", "dynatrace", "pagerduty",
    "servicenow", "zendesk", "intercom", "hubspot",
    "tableau", "looker", "qlik", "powerbi", "domo",
    "workday", "adp", "paycom", "paylocity", "bamboohr",
    "gusto", "justworks", "rippling", "deel", "remote",
    
    # Fintech/Banking
    "goldman", "jpmorgan", "morganstanley", "bankofamerica", "wellsfargo",
    "citigroup", "americanexpress", "visa", "mastercard", "discover",
    "chase", "capitalone", "usbank", "pnc", "tdbank",
    "sofi", "affirm", "afterpay", "klarna", "square", "stripe",
    "robinhood", "webull", "etrade", "schwab", "fidelity",
    "paypal", "venmo", "cashapp", "zelle",
    
    # Healthcare/Pharma
    "pfizer", "moderna", "jnj", "merck", "gilead", "biogen",
    "cvs", "walgreens", "humana", "unitedhealth", "anthem", "cigna",
    "bluecross", "aetna", "kaiser", "mayo",
    
    # Retail/Consumer
    "walmart", "target", "costco", "homedepot", "lowes", "bestbuy",
    "nike", "adidas", "underarmour", "lululemon", "patagonia",
    "gap", "oldnavy", "bananarepublic", "athleta",
    "mcdonalds", "starbucks", "chipotle", "panera",
    
    # Consulting
    "mckinsey", "bain", "bcg", "deloitte", "pwc", "ey", "kpmg",
    "accenture", "capgemini", "cognizant", "tcs", "infosys",
    "ibm", "hp", "dell", "lenovo",
    
    # Media/Entertainment
    "disney", "hbo", "paramount", "comcast", "verizon", "att", "t-mobile",
    "warner", "universal", "sony", "nintendo",
    
    # Transportation/Auto
    "tesla", "ford", "gm", "chrysler", "toyota", "honda",
    "lyft", "uber", "waymo", "cruise", "zoox", "rivian", "lucid",
    
    # Energy
    "exxon", "chevron", "bp", "shell", "conocophillips",
    
    # Aerospace
    "boeing", "lockheed", "northrop", "raytheon",
    
    # More Tech Startups
    "notion", "linear", "cursor", "replit", "codesandbox",
    "supabase", "planetscale", "cockroach", "neon",
    "turso", "railway", "render", "fly", "flyio",
    "stream", "ably", "pusher", "firebase", "supabase",
    "convex", "planetscale", "neon", "turso",
    
    # E-commerce/Marketplace
    "etsy", "ebay", "amazon", "shopify", "bigcommerce",
    "square", "woocommerce", "magento",
    
    # Food Delivery
    "doordash", "ubereats", "grubhub", "postmates", "instacart",
    "gopuff", "freshdirect", "helloFresh",
    
    # Real Estate
    "zillow", "redfin", "compass", "opendoor", "trulia",
    
    # Travel
    "booking", "expedia", "airbnb", "vrbo", "tripadvisor",
    
    # Education
    "coursera", "udemy", "udacity", "khan", "duolingo",
    "chegg", "quizlet", "brainly",
    
    # Gaming
    "activision", "ea", "epic", "roblox", "unity",
    "riot", "valve", "nintendo", "playstation", "xbox",
    
    # Biotech/Life Sciences
    "illumina", "thermo", "agilent", "waters",
    "regeneron", "vertex", "amgen", "bms",
    
    # Industrial/Manufacturing
    "ge", "honeywell", "emerson", "3m", "dow",
    "dupont", "basf", "caterpillar", "deere",
    
    # Professional Services
    "robert", "randstad", "manpower", "adecco",
    
    # Construction
    "fluor", "bechtel", "jacobs", "aecom",
    
    # Telecom
    "verizon", "att", "t-mobile", "sprint", "comcast",
    
    # Insurance
    "statefarm", "allstate", "geico", "progressive", "liberty",
    
    # Hospitality
    "marriott", "hilton", "hyatt", "ihg", "wynn",
    
    # Logistics/Shipping
    "fedex", "ups", "dhl", "usps", "amazon",
    
    # More comprehensive list
    "wayfair", "overstock", "homedepot", "lowes",
    "bestbuy", "gamestop", "barnes", "booksamillion",
    "macys", "nordstrom", "sephora", "ulta",
    "petco", "petsmart", "chewy",
    "grubhub", "postmates", "doordash", "ubereats",
    "zipcar", "turo", "getaround",
    "kickstarter", "indiegogo", "gofundme",
    "medium", "substack", "ghost",
    "patreon", "onlyfans", "twitch",
    "vimeo", "dailymotion", "youtube",
    "soundcloud", "bandcamp", "pandora",
    "iheartradio", "siriusxm",
    "tinder", "bumble", "hinge", "match",
    "linkedin", "facebook", "instagram", "snapchat",
    "tiktok", "twitter", "reddit", "pinterest",
    "quora", "stackoverflow", "github",
    "gitlab", "bitbucket", "sourceforge",
    "docker", "kubernetes", "terraform",
    "ansible", "chef", "puppet",
    "jenkins", "circleci", "travis", "github",
    "gitlab", "bitbucket", "azure", "aws", "gcp",
    "mongodb", "redis", "elasticsearch",
    "cassandra", "couchbase", "dynamodb",
    "postgresql", "mysql", "mariadb",
    "sqlserver", "oracle", "db2",
    "snowflake", "bigquery", "redshift",
    "databricks", "spark", "hadoop",
    "kafka", "rabbitmq", "activemq",
    "nginx", "apache", "caddy",
    "envoy", "istio", "linkerd",
    "prometheus", "grafana", "kibana",
    "jaeger", "zipkin", "sentry",
    "rollbar", "bugsnag", "honeybadger",
    "airbrake", "raygun", "trackjs",
    "mixpanel", "amplitude", "segment",
    "heap", "hotjar", "fullstory",
    "optimizely", "vwo", "unbounce",
    "leadpages", "instapage", "landingi",
    "mailchimp", "sendgrid", "postmark",
    "sendinblue", "mailgun", "sparkpost",
    "twilio", "messagebird", "nexmo",
    "ringcentral", "8x8", "dialpad",
    "zoom", "microsoft", "teams",
    "slack", "discord", "mattermost",
    "rocketchat", "zulip", "element",
    "matrix", "riot", "signal",
    "telegram", "whatsapp", "wechat",
    "line", "kakao", "viber",
    "snapchat", "instagram", "facebook",
    "twitter", "linkedin", "reddit",
    "pinterest", "tumblr", "medium",
    "wordpress", "ghost", "substack",
    "wix", "squarespace", "webflow",
    "shopify", "woocommerce", "bigcommerce",
    "magento", "prestashop", "opencart",
    "etsy", "ebay", "amazon",
    "walmart", "target", "costco",
    "homedepot", "lowes", "bestbuy",
    "gamestop", "barnes", "booksamillion",
    "macys", "nordstrom", "sephora",
    "ulta", "petco", "petsmart",
    "chewy", "wayfair", "overstock",
    "zillow", "redfin", "compass",
    "opendoor", "trulia", "realtor",
    "airbnb", "vrbo", "booking",
    "expedia", "tripadvisor", "priceline",
    "kayak", "skyscanner", "hopper",
    "doordash", "ubereats", "grubhub",
    "postmates", "instacart", "gopuff",
    "freshdirect", "hellofresh", "blueapron",
    "tinder", "bumble", "hinge",
    "match", "okcupid", "plentyoffish",
    "eharmony", "coffee", "meetsbagel",
    "zoosk", "elitesingles", "silversingles",
    "ourtime", "seniorpeoplemeet", "christianmingle",
    "jdate", "jsingles", "blackpeoplemeet",
    "latinopeoplemeet", "asianpeoplemeet",
    "indianpeoplemeet", "filipinopeoplemeet",
]

def test_greenhouse(company):
    """Test if a company uses Greenhouse."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            data = response.json()
            jobs = data if isinstance(data, list) else data.get('jobs', [])
            if jobs:
                return (True, company, len(jobs))
    except:
        pass
    return (False, company, 0)

def test_lever(company):
    """Test if a company uses Lever."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                return (True, company, len(data))
    except:
        pass
    return (False, company, 0)

print(f"Testing {len(ALL_COMPANIES)} companies across all industries...")
print("This will take a few minutes...\n")

greenhouse_working = []
lever_working = []
seen = set()

with ThreadPoolExecutor(max_workers=30) as executor:
    futures = []
    for company in ALL_COMPANIES:
        if company not in seen:
            seen.add(company)
            futures.append(executor.submit(test_greenhouse, company))
            futures.append(executor.submit(test_lever, company))
    
    for future in as_completed(futures):
        try:
            works, company, count = future.result()
            if works:
                source = "greenhouse" if "greenhouse" in str(future) else "lever"
                if source == "greenhouse" and (company, count) not in greenhouse_working:
                    greenhouse_working.append((company, count))
                    print(f"✅ Greenhouse: {company} ({count} jobs)")
                elif source == "lever" and (company, count) not in lever_working:
                    lever_working.append((company, count))
                    print(f"✅ Lever: {company} ({count} jobs)")
        except:
            pass

# Remove duplicates and sort
greenhouse_working = sorted(list(set(greenhouse_working)), key=lambda x: x[1], reverse=True)
lever_working = sorted(list(set(lever_working)), key=lambda x: x[1], reverse=True)

print(f"\n{'='*60}")
print(f"Found {len(greenhouse_working)} unique Greenhouse companies")
print(f"Found {len(lever_working)} unique Lever companies")
print(f"Total: {len(greenhouse_working) + len(lever_working)} companies")
print(f"{'='*60}")

# Save to file
with open('found_companies.json', 'w') as f:
    json.dump({
        'greenhouse': [c[0] for c in greenhouse_working],
        'lever': [c[0] for c in lever_working],
        'greenhouse_with_counts': greenhouse_working,
        'lever_with_counts': lever_working
    }, f, indent=2)

print(f"\nResults saved to found_companies.json")
print(f"\nTop 20 Greenhouse companies:")
for company, count in greenhouse_working[:20]:
    print(f"  {company}: {count} jobs")

