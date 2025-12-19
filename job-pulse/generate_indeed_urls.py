#!/usr/bin/env python3
"""Generate Indeed RSS URLs for diverse job types."""

# Comprehensive list of job types across all industries
JOB_TYPES = [
    # Technical - Software Engineering
    "software engineer", "software developer", "full stack developer",
    "frontend developer", "backend developer", "fullstack developer",
    "python developer", "java developer", "javascript developer",
    "react developer", "node.js developer", "angular developer",
    
    # Technical - Specialized
    "devops engineer", "site reliability engineer", "sre",
    "data engineer", "data scientist", "machine learning engineer",
    "ml engineer", "ai engineer", "computer vision engineer",
    "robotics engineer", "embedded engineer", "firmware engineer",
    "qa engineer", "test engineer", "quality assurance",
    "security engineer", "cybersecurity engineer", "information security",
    
    # Technical - Infrastructure/Cloud
    "cloud engineer", "aws engineer", "azure engineer", "gcp engineer",
    "kubernetes engineer", "docker engineer", "terraform engineer",
    "solutions architect", "cloud architect", "system architect",
    
    # Product & Design
    "product manager", "product owner", "technical product manager",
    "ux designer", "ui designer", "product designer", "graphic designer",
    "ux researcher", "user researcher",
    
    # Data & Analytics
    "data analyst", "business analyst", "data analyst", "business intelligence",
    "analytics engineer", "bi analyst", "financial analyst",
    
    # Business & Operations
    "project manager", "program manager", "operations manager",
    "business operations", "operations analyst", "strategy analyst",
    
    # Sales & Marketing
    "sales engineer", "sales manager", "account executive", "sales representative",
    "marketing manager", "digital marketing", "content marketing",
    "marketing analyst", "growth marketing", "product marketing",
    "social media manager", "seo specialist", "paid advertising",
    
    # Customer Success & Support
    "customer success manager", "customer support", "technical support",
    "account manager", "relationship manager",
    
    # HR & Recruiting
    "recruiter", "talent acquisition", "hr manager", "people operations",
    "hr business partner", "talent manager",
    
    # Finance & Accounting
    "accountant", "financial analyst", "controller", "cfo",
    "bookkeeper", "payroll specialist", "tax accountant",
    
    # Legal
    "paralegal", "legal assistant", "contracts manager", "compliance manager",
    
    # Healthcare
    "nurse", "medical assistant", "pharmacy technician", "healthcare administrator",
    
    # Education
    "teacher", "instructor", "curriculum developer", "educational technology",
    
    # Consulting
    "consultant", "business consultant", "management consultant",
    "strategy consultant", "it consultant",
    
    # Real Estate
    "real estate agent", "property manager", "real estate broker",
    
    # Retail & Hospitality
    "store manager", "retail manager", "restaurant manager", "hotel manager",
    
    # Construction & Engineering
    "civil engineer", "mechanical engineer", "electrical engineer",
    "construction manager", "project engineer",
    
    # Creative & Media
    "writer", "content writer", "copywriter", "technical writer",
    "video editor", "photographer", "graphic designer",
    
    # Supply Chain & Logistics
    "supply chain manager", "logistics coordinator", "procurement specialist",
    "warehouse manager",
    
    # Executive & Leadership
    "ceo", "cto", "cfo", "vp engineering", "director of engineering",
    "engineering manager", "technical lead", "staff engineer", "principal engineer",
]

def generate_indeed_rss_url(job_type: str, location: str = "", fromage: int = 1) -> str:
    """
    Generate Indeed RSS URL for a job type.
    
    Args:
        job_type: Job title/keywords to search for
        location: Location filter (optional, e.g., "San Francisco, CA" or "Remote")
        fromage: Days to look back (1 = last 24 hours, 7 = last 7 days, etc.)
    
    Returns:
        Indeed RSS URL string
    """
    from urllib.parse import quote_plus
    
    # URL encode the job type
    job_encoded = quote_plus(job_type)
    
    # Build base URL
    url = f"https://www.indeed.com/rss?q={job_encoded}&sort=date&fromage={fromage}"
    
    # Add location if provided
    if location:
        location_encoded = quote_plus(location)
        url += f"&l={location_encoded}"
    
    return url

# Generate URLs for all job types (last 24 hours for fresh jobs)
urls = []
for job_type in JOB_TYPES:
    url = generate_indeed_rss_url(job_type, fromage=1)  # Last 24 hours
    urls.append(url)

# Print as comma-separated list for .env file
print("# Comprehensive Indeed RSS URLs for diverse job types")
print("# Generated URLs for last 24 hours - covers all major job categories")
print("INDEED_RSS_URLS=" + ",".join(urls))

print(f"\n# Total: {len(urls)} RSS feeds", file=__import__('sys').stderr)

