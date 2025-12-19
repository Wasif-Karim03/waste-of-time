#!/usr/bin/env python3
"""
Expand companies list to 500+ by testing comprehensive company list.
This script tests companies systematically and adds working ones.
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Massive comprehensive list - 1000+ company names to test
MASSIVE_LIST = """
# Tech Software/SaaS (300+)
stripe dropbox shopify airbnb uber pinterest slack zoom doordash instacart
robinhood coinbase square palantir asana notion figma canva atlassian gitlab github
databricks snowflake mongodb elastic redis twilio sendgrid plaid brex mercury
chime revolut n26 vivid okta auth0 1password lastpass cloudflare fastly
vercel netlify heroku digitalocean vultr linode squarespace wix webflow
bigcommerce woocommerce spotify netflix reddit twitter meta snapchat discord
linkedin microsoft google apple amazon tesla salesforce oracle sap adobe
intel nvidia amd qualcomm broadcom cisco juniper arista vmware citrix
nutanix purestorage netapp splunk newrelic datadog dynatrace pagerduty
servicenow zendesk intercom hubspot tableau looker qlik powerbi domo
workday adp paycom paylocity bamboohr gusto justworks rippling deel remote
linear cursor replit codesandbox supabase planetscale cockroach neon turso
railway render fly flyio stream ably pusher firebase convex sentry rollbar
bugsnag honeybadger airbrake raygun trackjs mixpanel amplitude segment heap
hotjar fullstory optimizely vwo unbounce leadpages instapage landingi
mailchimp postmark sendinblue mailgun sparkpost messagebird nexmo
ringcentral 8x8 dialpad mattermost rocketchat zulip element matrix
anthropic openai cohere ai21 jasper copy ai zapier ifttt automate
retool bubble airtable notion zapier typeform survey monkey
calendly acuity scheduling zoomify teams microsoft
dropbox box onedrive googledrive icloud
trello asana monday clickup wrike smartsheet
jira confluence bitbucket github gitlab sourceforge
docker kubernetes terraform ansible chef puppet jenkins
circleci travis githubactions gitlabci azuredevops
aws gcp azure digitalocean linode vultr hetzner
vercel netlify render railway fly heroku
mongodb redis elasticsearch couchbase dynamodb
postgresql mysql mariadb sqlserver oracle db2
snowflake bigquery redshift databricks spark hadoop
kafka rabbitmq activemq nginx apache caddy
envoy istio linkerd prometheus grafana kibana
jaeger zipkin sentry rollbar bugsnag honeybadger
airbrake raygun trackjs mixpanel amplitude segment
heap hotjar fullstory optimizely vwo unbounce
leadpages instapage landingi mailchimp postmark
sendinblue mailgun sparkpost messagebird nexmo
ringcentral 8x8 dialpad mattermost rocketchat zulip

# Fintech Banking (100+)
stripe coinbase robinhood chime sofi webull brex mercury affirm afterpay
klarna plaid square paypal venmo cashapp zelle visa mastercard
americanexpress discover goldman jpmorgan morganstanley bankofamerica wellsfargo
citigroup chase capitalone usbank pnc tdbank etrade schwab fidelity
vanguard charlesschwab blackrock statestreet bnymellon wells fargo
chase bank usbank citibank bankofamerica jpmorganchase
goldmansachs morganstanley merrill lynch charlesschwab
tdameritrade e trade fidelity investments vanguard blackrock
statestreet bnymellon northern trust statefarm allstate
geico progressive libertymutual travelers farmers nationwide

# Healthcare Pharma (50+)
pfizer moderna jnj merck gilead biogen cvs walgreens humana unitedhealth
anthem cigna bluecross aetna kaiser mayo illumina thermo agilent waters
regeneron vertex amgen bms lilly abbvie bayer novartis roche sanofi
glaxosmithkline gsk astrazeneca teva perrigo

# Retail Consumer (100+)
walmart target costco homedepot lowes bestbuy nike adidas underarmour
lululemon patagonia gap oldnavy bananarepublic athleta mcdonalds starbucks
chipotle panera subway taco bell kfc dominos pizza hut
macys nordstrom sephora ulta saks neiman marcus
petco petsmart chewy wayfair overstock bedbath beyond
gamestop barnes noble booksamillion staples officedepot
homedepot lowes menards acehardware

# Consulting Services (50+)
mckinsey bain bcg deloitte pwc ey kpmg accenture capgemini cognizant
tcs infosys wipro ibm hp dell lenovo robert half randstad manpower adecco
kelly services aerotek teksystems insight global

# Media Entertainment (50+)
disney netflix hbo paramount comcast verizon att tmobile sprint warner
universal sony nintendo activision ea epic roblox unity riot valve
playstation xbox cbs abc nbc fox cnn msnbc

# Transportation Auto (30+)
tesla ford gm chrysler toyota honda lyft uber waymo cruise zoox rivian
lucid fiat nissan bmw mercedes volvo audi porsche

# Ecommerce Marketplace (50+)
shopify etsy ebay amazon doordash ubereats grubhub postmates instacart
gopuff freshdirect hellofresh blueapron homechef

# Real Estate (20+)
zillow redfin compass opendoor trulia realtor remax century21

# Travel (30+)
booking expedia airbnb vrbo tripadvisor priceline kayak skyscanner hopper
marriott hilton hyatt ihg wyndham choice

# Education (30+)
coursera udemy udacity khan duolingo chegg quizlet brainly 2u
edx coursera udacity pluralsight linkedinlearning

# Energy (20+)
exxon chevron bp shell conocophillips marathon valero

# Aerospace (10+)
boeing lockheed northrop raytheon spacex blueorigin

# Insurance (20+)
statefarm allstate geico progressive liberty travelers farmers nationwide
aetna cigna humana unitedhealthcare

# Logistics (10+)
fedex ups dhl usps amazonlogistics
""".split()

# Remove duplicates and sort
UNIQUE_COMPANIES = sorted(list(set([c.strip() for c in MASSIVE_LIST if c.strip() and not c.startswith('#')])))

# Already found companies (don't retest)
ALREADY_FOUND = {
    "databricks", "stripe", "cloudflare", "mongodb", "datadog", "purestorage",
    "coinbase", "okta", "airbnb", "intercom", "elastic", "brex", "affirm",
    "lyft", "figma", "dropbox", "instacart", "reddit", "asana", "sofi",
    "jetbrains", "gitlab", "pinterest", "robinhood", "twilio", "redis",
    "justworks", "newrelic", "gusto", "vercel", "discord", "pagerduty",
    "squarespace", "webflow", "dialpad", "chime", "mercury", "mixpanel",
    "mattermost", "planetscale", "rocketchat", "netlify", "disney",
    "palantir", "zoox", "spotify", "plaid", "neon"
}

# Companies to test (excluding already found)
TO_TEST = [c for c in UNIQUE_COMPANIES if c not in ALREADY_FOUND]

print(f"Testing {len(TO_TEST)} additional companies...")
print(f"(Already have {len(ALREADY_FOUND)} working companies)\n")

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

greenhouse_new = {}
lever_new = {}

# Test in batches
BATCH_SIZE = 50
total_batches = (len(TO_TEST) + BATCH_SIZE - 1) // BATCH_SIZE

for batch_num in range(total_batches):
    start = batch_num * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(TO_TEST))
    batch = TO_TEST[start:end]
    
    print(f"Batch {batch_num + 1}/{total_batches} ({len(batch)} companies)...")
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = []
        for company in batch:
            futures.append(executor.submit(test_greenhouse, company))
            futures.append(executor.submit(test_lever, company))
        
        batch_found = 0
        for future in as_completed(futures):
            result = future.result()
            if result:
                source, company, count = result
                if source == "greenhouse" and company not in greenhouse_new:
                    greenhouse_new[company] = count
                    print(f"  ✅ {company}: {count} jobs")
                    batch_found += 1
                elif source == "lever" and company not in lever_new:
                    lever_new[company] = count
                    print(f"  ✅ {company}: {count} jobs")
                    batch_found += 1
    
    print(f"  Found {batch_found} new companies this batch\n")
    time.sleep(0.5)

# Merge with existing
all_greenhouse = {
    "databricks": 701, "stripe": 548, "cloudflare": 547, "mongodb": 399,
    "datadog": 371, "purestorage": 365, "coinbase": 362, "okta": 315,
    "airbnb": 208, "intercom": 202, "elastic": 192, "brex": 172,
    "affirm": 162, "lyft": 162, "figma": 156, "dropbox": 150,
    "instacart": 149, "reddit": 137, "asana": 129, "sofi": 128,
    "jetbrains": 122, "gitlab": 120, "pinterest": 106, "robinhood": 102,
    "twilio": 92, "redis": 92, "justworks": 84, "newrelic": 82,
    "gusto": 78, "vercel": 76, "discord": 62, "pagerduty": 55,
    "squarespace": 55, "webflow": 55, "dialpad": 53, "chime": 46,
    "mercury": 43, "mixpanel": 25, "mattermost": 12, "planetscale": 6,
    "rocketchat": 5, "netlify": 2, "disney": 2
}
all_greenhouse.update(greenhouse_new)

all_lever = {"palantir": 227, "zoox": 211, "spotify": 119, "plaid": 77, "neon": 18}
all_lever.update(lever_new)

# Sort
greenhouse_sorted = sorted(all_greenhouse.items(), key=lambda x: x[1], reverse=True)
lever_sorted = sorted(all_lever.items(), key=lambda x: x[1], reverse=True)

# Create YAML
yaml_content = f"# Comprehensive companies list - {len(all_greenhouse) + len(all_lever)} companies\n"
yaml_content += "# Tested and confirmed working across all industries\n\n"
yaml_content += "greenhouse_boards:\n"
for company, count in greenhouse_sorted:
    yaml_content += f"  - {company}  # {count} jobs\n"

yaml_content += "\nlever_companies:\n"
for company, count in lever_sorted:
    yaml_content += f"  - {company}  # {count} jobs\n"

with open('companies_expanded.yaml', 'w') as f:
    f.write(yaml_content)

print(f"\n{'='*60}")
print(f"✅ EXPANDED LIST CREATED")
print(f"{'='*60}")
print(f"Original: {len(ALREADY_FOUND)} companies")
print(f"New found: {len(greenhouse_new) + len(lever_new)} companies")
print(f"Total: {len(all_greenhouse) + len(all_lever)} companies")
print(f"{'='*60}")

