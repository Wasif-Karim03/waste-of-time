#!/usr/bin/env python3
"""
Systematic script to test companies and build comprehensive list.
Tests companies in batches and saves results progressively.
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Comprehensive list organized by industry for variety
COMPREHENSIVE_LIST = """
# Tech Software/SaaS
stripe dropbox shopify airbnb uber pinterest slack zoom doordash instacart
robinhood coinbase square palantir asana notion figma canva atlassian gitlab
databricks snowflake mongodb elastic redis twilio sendgrid plaid brex mercury
chime revolut n26 vivid okta auth0 1password lastpass cloudflare fastly
vercel netlify heroku digitalocean vultr linode squarespace wix webflow
bigcommerce woocommerce spotify netflix reddit twitter meta snapchat discord
linkedin microsoft google apple amazon tesla salesforce oracle sap adobe
intel nvidia amd qualcomm broadcom cisco juniper arista vmware citrix
nutanix purestorage netapp splunk newrelic datadog dynatrace pagerduty
servicenow zendesk intercom hubspot tableau looker qlik powerbi domo
workday adp paycom paylocity bamboohr gusto justworks rippling deel remote

# Fintech Banking
stripe coinbase robinhood chime sofi webull brex mercury affirm afterpay
klarna plaid square paypal venmo cashapp zelle visa mastercard
americanexpress discover goldman jpmorgan morganstanley bankofamerica wellsfargo
citigroup chase capitalone usbank pnc tdbank etrade schwab fidelity
vanguard charlesschwab blackrock statestreet bnymellon

# Healthcare Pharma
pfizer moderna jnj merck gilead biogen cvs walgreens humana unitedhealth
anthem cigna bluecross aetna kaiser mayo illumina thermo agilent waters
regeneron vertex amgen bms lilly abbvie bayer novartis

# Retail Consumer
walmart target costco homedepot lowes bestbuy nike adidas underarmour
lululemon patagonia gap oldnavy bananarepublic athleta mcdonalds starbucks
chipotle panera subway macys nordstrom sephora ulta saks petco petsmart
chewy wayfair overstock bedbath gamestop barnes booksamillion

# Consulting Services
mckinsey bain bcg deloitte pwc ey kpmg accenture capgemini cognizant
tcs infosys wipro ibm hp dell lenovo robert randstad manpower adecco

# Media Entertainment
disney netflix hbo paramount comcast verizon att tmobile sprint warner
universal sony nintendo activision ea epic roblox unity riot valve
playstation xbox cbs abc nbc fox

# Transportation Auto
tesla ford gm chrysler toyota honda lyft uber waymo cruise zoox rivian
lucid fiat nissan bmw mercedes

# Ecommerce Marketplace
shopify etsy ebay amazon doordash ubereats grubhub postmates instacart
gopuff freshdirect hellofresh blueapron

# Real Estate
zillow redfin compass opendoor trulia realtor

# Travel
booking expedia airbnb vrbo tripadvisor priceline kayak skyscanner hopper

# Education
coursera udemy udacity khan duolingo chegg quizlet brainly 2u

# Energy
exxon chevron bp shell conocophillips

# Aerospace
boeing lockheed northrop raytheon

# Insurance
statefarm allstate geico progressive liberty travelers farmers nationwide

# Hospitality
marriott hilton hyatt ihg wynn

# Logistics
fedex ups dhl usps

# Industrial Manufacturing
ge honeywell emerson 3m dow dupont basf caterpillar deere

# Construction
fluor bechtel jacobs aecom

# More Tech Startups
linear cursor replit codesandbox supabase planetscale cockroach neon turso
railway render fly flyio stream ably pusher firebase convex sentry rollbar
bugsnag honeybadger airbrake raygun trackjs mixpanel amplitude segment heap
hotjar fullstory optimizely vwo unbounce leadpages instapage landingi
mailchimp postmark sendinblue mailgun sparkpost messagebird nexmo
ringcentral 8x8 dialpad mattermost rocketchat zulip element matrix
""".split()

# Remove duplicates
UNIQUE_COMPANIES = sorted(list(set(COMPREHENSIVE_LIST)))

print(f"Testing {len(UNIQUE_COMPANIES)} unique companies...")
print("This will take time - testing in batches...\n")

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

greenhouse_found = {}
lever_found = {}
total_tested = 0

# Test in smaller batches for better progress tracking
BATCH_SIZE = 30
total_batches = (len(UNIQUE_COMPANIES) + BATCH_SIZE - 1) // BATCH_SIZE

for batch_num in range(total_batches):
    start_idx = batch_num * BATCH_SIZE
    end_idx = min(start_idx + BATCH_SIZE, len(UNIQUE_COMPANIES))
    batch = UNIQUE_COMPANIES[start_idx:end_idx]
    
    print(f"Batch {batch_num + 1}/{total_batches} - Testing {len(batch)} companies...")
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = []
        for company in batch:
            futures.append(executor.submit(test_greenhouse, company))
            futures.append(executor.submit(test_lever, company))
        
        batch_found = 0
        for future in as_completed(futures):
            result = future.result()
            if result:
                source, company, count = result
                if source == "greenhouse" and company not in greenhouse_found:
                    greenhouse_found[company] = count
                    print(f"  ✅ Greenhouse: {company} ({count} jobs)")
                    batch_found += 1
                elif source == "lever" and company not in lever_found:
                    lever_found[company] = count
                    print(f"  ✅ Lever: {company} ({count} jobs)")
                    batch_found += 1
    
    total_tested += len(batch)
    print(f"  Found {batch_found} new companies in this batch")
    print(f"  Progress: {total_tested}/{len(UNIQUE_COMPANIES)} tested ({total_tested*100//len(UNIQUE_COMPANIES)}%)\n")
    
    # Save progress after each batch
    if batch_found > 0:
        greenhouse_sorted = sorted(greenhouse_found.items(), key=lambda x: x[1], reverse=True)
        lever_sorted = sorted(lever_found.items(), key=lambda x: x[1], reverse=True)
        
        yaml_content = f"# Progress: {total_tested}/{len(UNIQUE_COMPANIES)} companies tested\n"
        yaml_content += f"# Found: {len(greenhouse_found)} Greenhouse + {len(lever_found)} Lever = {len(greenhouse_found) + len(lever_found)} total\n\n"
        yaml_content += "greenhouse_boards:\n"
        for company, count in greenhouse_sorted:
            yaml_content += f"  - {company}  # {count} jobs\n"
        
        yaml_content += "\nlever_companies:\n"
        for company, count in lever_sorted:
            yaml_content += f"  - {company}  # {count} jobs\n"
        
        with open('companies_progress.yaml', 'w') as f:
            f.write(yaml_content)
    
    time.sleep(0.5)  # Rate limiting

# Final results
print(f"\n{'='*60}")
print(f"✅ FINAL RESULTS")
print(f"{'='*60}")
print(f"Found {len(greenhouse_found)} Greenhouse companies")
print(f"Found {len(lever_found)} Lever companies")
print(f"Total: {len(greenhouse_found) + len(lever_found)} companies")
print(f"{'='*60}")

# Save final file
greenhouse_sorted = sorted(greenhouse_found.items(), key=lambda x: x[1], reverse=True)
lever_sorted = sorted(lever_found.items(), key=lambda x: x[1], reverse=True)

yaml_final = "# Comprehensive companies list\n"
yaml_final += f"# Total: {len(greenhouse_found) + len(lever_found)} companies\n\n"
yaml_final += "greenhouse_boards:\n"
for company, count in greenhouse_sorted:
    yaml_final += f"  - {company}  # {count} jobs\n"

yaml_final += "\nlever_companies:\n"
for company, count in lever_sorted:
    yaml_final += f"  - {company}  # {count} jobs\n"

with open('companies_final.yaml', 'w') as f:
    f.write(yaml_final)

print(f"\n✅ Final results saved to companies_final.yaml")
print(f"\nTop 20 companies by job count:")
all_companies = [(c, count, "greenhouse") for c, count in greenhouse_sorted[:20]]
all_companies.extend([(c, count, "lever") for c, count in lever_sorted[:10]])
all_companies.sort(key=lambda x: x[1], reverse=True)
for company, count, source in all_companies[:20]:
    print(f"  {company} ({source}): {count} jobs")

