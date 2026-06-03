import asyncio
from src.core.scraper import fetch_google_news_rss
from src.core.utils import get_article_text_playwright

macro_articles = []
macro_articles.extend(fetch_google_news_rss(query="Stock market today finance.yahoo.com", max_results=30))
macro_articles.extend(fetch_google_news_rss(query="Markets News investopedia", max_results=30))

domain_found = {"finance.yahoo.com": False, "investopedia.com": False}

print("\n=== MACRO NEWS TEST ===")
for item in macro_articles:
    url = item.get("url", "")
    title = item.get("title", "")
    
    matched_domain = None
    for domain in domain_found:
        domain_name = 'yahoo' if 'finance' in domain else 'investopedia'
        if domain in url or domain_name in title.lower():
            matched_domain = domain; break
            
    if not matched_domain or domain_found[matched_domain]: continue
    
    target = "Markets News" if "investopedia" in matched_domain else "Stock market today"
    if not all(kw in title.lower() for kw in target.lower().split()): continue
    
    domain_found[matched_domain] = True
    print(f"\n[{matched_domain}] {title}")
    
    text = get_article_text_playwright(url)
    print(f"TEXT ({len(text)} chars): {text[:300]}...")

if not domain_found['investopedia.com']:
    print("FAILED TO FIND INVESTOPEDIA")

