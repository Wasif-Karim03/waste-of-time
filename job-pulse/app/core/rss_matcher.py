"""Match user search keywords to relevant RSS feeds."""

from typing import List, Set
import logging

logger = logging.getLogger(__name__)


def match_rss_feeds(keywords: List[str], all_rss_urls: List[str]) -> List[str]:
    """
    Match user keywords to relevant RSS feed URLs.
    
    This function analyzes user keywords and returns only the RSS feeds
    that are most relevant to the search, improving speed and relevance.
    
    Args:
        keywords: List of user search keywords (e.g., ["software", "engineer"])
        all_rss_urls: List of all available RSS feed URLs
    
    Returns:
        List of relevant RSS feed URLs (subset of all_rss_urls)
    
    Examples:
        >>> keywords = ["software", "engineer"]
        >>> urls = [
        ...     "https://indeed.com/rss?q=software+engineer",
        ...     "https://indeed.com/rss?q=accountant",
        ...     "https://indeed.com/rss?q=marketing"
        ... ]
        >>> matched = match_rss_feeds(keywords, urls)
        >>> assert "software+engineer" in matched[0]
        >>> assert len(matched) == 1
    """
    if not keywords or not all_rss_urls:
        return all_rss_urls
    
    # Normalize keywords to lowercase
    keywords_lower = [kw.lower().strip() for kw in keywords if kw.strip()]
    
    if not keywords_lower:
        return all_rss_urls
    
    matched_urls = []
    
    for url in all_rss_urls:
        url_lower = url.lower()
        
        # Check if any keyword appears in the URL
        # Indeed RSS URLs contain the search query in the URL like: q=software+engineer
        keyword_matched = False
        
        for keyword in keywords_lower:
            # Direct match in URL query parameter
            if f"q={keyword}" in url_lower or f"q={keyword.replace(' ', '+')}" in url_lower:
                keyword_matched = True
                break
            
            # Match keyword parts (for compound keywords like "software engineer")
            keyword_parts = keyword.split()
            if len(keyword_parts) > 1:
                # Check if all parts appear in URL
                if all(part in url_lower for part in keyword_parts if len(part) > 2):
                    keyword_matched = True
                    break
            
            # Fuzzy match - check if keyword is a substring of any part of the URL query
            # This handles variations like "engineer" matching "software+engineer"
            if keyword in url_lower and "q=" in url_lower:
                keyword_matched = True
                break
        
        if keyword_matched:
            matched_urls.append(url)
    
    # If no matches found, return all URLs (fallback)
    if not matched_urls:
        logger.info(f"No specific RSS feeds matched for keywords {keywords}, using all feeds")
        return all_rss_urls
    
    logger.info(f"Matched {len(matched_urls)} RSS feeds for keywords: {keywords} (from {len(all_rss_urls)} total)")
    return matched_urls


def match_indeed_feeds(keywords: List[str], all_indeed_urls: List[str]) -> List[str]:
    """
    Specifically match Indeed RSS feeds based on keywords.
    
    This uses keyword-to-job-type mapping for better matching.
    
    Args:
        keywords: List of user search keywords
        all_indeed_urls: List of all Indeed RSS URLs
    
    Returns:
        List of relevant Indeed RSS URLs
    """
    if not keywords or not all_indeed_urls:
        return all_indeed_urls
    
    keywords_lower = [kw.lower().strip() for kw in keywords if kw.strip()]
    
    if not keywords_lower:
        return all_indeed_urls
    
    # Combine all keywords into search terms
    search_terms = " ".join(keywords_lower)
    
    matched_urls = []
    
    for url in all_indeed_urls:
        url_lower = url.lower()
        
        # Extract the query parameter value (q=...)
        if "q=" not in url_lower:
            continue
        
        # Get the query value (everything after q= until & or end)
        query_start = url_lower.find("q=") + 2
        query_end = url_lower.find("&", query_start)
        if query_end == -1:
            query_end = len(url_lower)
        query_value = url_lower[query_start:query_end]
        
        # Normalize query value (replace + with space for matching)
        query_normalized = query_value.replace("+", " ").replace("%20", " ")
        
        # Check for exact or substring matches
        matched = False
        
        # Keyword variations mapping (handles synonyms and related terms)
        keyword_variations = {
            "accounting": ["accountant", "accounting"],
            "software engineer": ["software+engineer", "software engineer", "software+developer", "software developer"],
            "software engineering": ["software+engineer", "software engineer", "software+developer"],
            "data science": ["data+scientist", "data scientist", "data+engineer", "data engineer"],
            "product management": ["product+manager", "product manager", "product+owner"],
        }
        
        # Check each keyword against the query
        for keyword in keywords_lower:
            # Get variations for this keyword
            variations = [keyword]
            if keyword in keyword_variations:
                variations.extend(keyword_variations[keyword])
            
            keyword_normalized = keyword.replace(" ", "+")
            variations.append(keyword_normalized)
            
            # Check each variation
            for variant in variations:
                variant_normalized = variant.replace("+", " ").replace(" ", "+")
                
                # Exact match in URL query
                if variant in query_normalized or variant_normalized in query_value:
                    matched = True
                    break
                
                # Check if variant is contained in query (handles partial matches)
                # e.g., "software" matches "software+engineer"
                variant_parts = variant.split()
                if len(variant_parts) == 1:
                    # Single word - check if it's in the query
                    if variant in query_normalized:
                        matched = True
                        break
                else:
                    # Multi-word variant - check if all parts appear in query
                    # e.g., "software engineer" should match "software+engineer"
                    variant_spaces = variant.replace("+", " ")
                    if all(part in query_normalized for part in variant_spaces.split()):
                        matched = True
                        break
            
            if matched:
                break
            
            # Also check if keyword parts match query parts (fuzzy matching)
            # e.g., "accounting" should match "accountant" (both start with "account")
            keyword_parts = keyword.split()
            if len(keyword_parts) == 1 and len(keyword_parts[0]) > 4:
                # Check if significant portion of keyword matches query
                # e.g., "accounting" contains "account" which matches "accountant"
                keyword_stem = keyword_parts[0][:6]  # First 6 chars
                if keyword_stem in query_normalized:
                    matched = True
                    break
        
        if matched:
            matched_urls.append(url)
    
    # If no matches found, return empty list (don't use all feeds as fallback)
    # This ensures users only get relevant feeds
    if not matched_urls:
        logger.info(f"No Indeed RSS feeds matched for keywords: {keywords}")
        return []
    
    logger.info(f"Matched {len(matched_urls)} relevant Indeed RSS feeds for keywords: {keywords} (from {len(all_indeed_urls)} total)")
    return matched_urls

