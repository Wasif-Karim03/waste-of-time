#!/usr/bin/env python3
"""Merge existing companies with newly found startups."""

# Existing companies from companies.yaml
existing_greenhouse = {
    'spacex', 'databricks', 'stripe', 'cloudflare', 'mongodb', 'waymo', 'datadog',
    'purestorage', 'coinbase', 'hellofresh', 'okta', 'anthropic', 'roblox', 'airbnb',
    'intercom', 'elastic', 'brex', 'affirm', 'lyft', 'figma', 'dropbox', 'instacart',
    'reddit', 'asana', 'sofi', 'jetbrains', 'gitlab', 'pinterest', 'robinhood', 'twilio',
    'redis', 'justworks', 'newrelic', 'gusto', 'vercel', 'smartsheet', 'udemy', 'discord',
    'tcs', 'amplitude', 'duolingo', 'pagerduty', 'squarespace', 'webflow', 'dialpad',
    'linkedin', 'n26', 'airtable', 'tripadvisor', 'chime', 'coursera', 'mercury',
    'homechef', 'fastly', 'opendoor', 'vultr', 'wrike', 'udacity', 'abc', 'skyscanner',
    'mixpanel', 'lastpass', 'calendly', 'circleci', 'typeform', 'mattermost', '2u',
    'beyond', 'planetscale', 'rocketchat', 'jasper', 'retool', 'universal', 'netlify',
    'disney', 'domo', 'noble', 'remote', 'wayfair', 'fox', 'kayak', 'unbounce'
}

existing_lever = {'palantir', 'zoox', 'spotify', 'plaid', 'neon'}

# New startups found (from found_startups.txt)
new_greenhouse = {
    'adyen', 'via', 'scopely', 'klaviyo', 'zoominfo', 'contentful', 'housecall',
    'slice', 'make', 'getyourguide', 'iterable', 'greenhouse', 'alloy', 'customerio',
    'spin', 'bird', 'doximity', 'labelbox', 'rocketlawyer', 'dashlane', 'fieldwire',
    'juno', 'veracode', 'masterclass', 'stockx', 'apollo', 'bitwarden', 'knock', 'root',
    'niantic', 'commercetools', 'mercari', 'treasuryprime'
}

new_lever = {
    'labelbox', 'filevine', 'ro', 'outreach', 'jobvite', 'finix', 'pipedrive',
    'omnisend', 'logrocket', 'arcadia', 'revel', 'teller', 'signal', 'skillshare', 'clubhouse'
}

# Merge (new companies are added)
all_greenhouse = sorted(list(existing_greenhouse | new_greenhouse))
all_lever = sorted(list(existing_lever | new_lever))

# Create YAML content
yaml_content = f"""# Comprehensive companies list - {len(all_greenhouse) + len(all_lever)} companies
# Includes big tech, startups, and companies across all industries
# Mix of large companies and smaller growing startups

greenhouse_boards:
"""

for company in all_greenhouse:
    yaml_content += f"  - {company}\n"

yaml_content += "\nlever_companies:\n"

for company in all_lever:
    yaml_content += f"  - {company}\n"

# Write to file
with open('companies.yaml', 'w') as f:
    f.write(yaml_content)

print(f"✅ Merged companies list created!")
print(f"   - {len(existing_greenhouse)} existing greenhouse companies")
print(f"   - {len(new_greenhouse)} new greenhouse startups added")
print(f"   - Total: {len(all_greenhouse)} greenhouse companies")
print(f"\n   - {len(existing_lever)} existing lever companies")
print(f"   - {len(new_lever)} new lever startups added")
print(f"   - Total: {len(all_lever)} lever companies")
print(f"\n   Grand Total: {len(all_greenhouse) + len(all_lever)} companies")

