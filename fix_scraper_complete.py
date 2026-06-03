import re

with open("src/core/scraper.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace Macro logic (around line 156-180 in the current file)
old_macro_start = 'search_query = getattr(settings, "macro_search_query", "Stock market today")'
old_macro_end = 'logger.error(f"Google Macro News Error: {e}")'

new_macro_code = """search_query = getattr(settings, "macro_search_query", "Stock market today")
        approved_domains = getattr(settings, "macro_approved_domains", ["finance.yahoo.com", "cnbc.com", "investopedia.com"])
        
        # newspaper 설정 (User-Agent 필수)
        import newspaper
        config = newspaper.Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        config.request_timeout = 10
        
        # 사 지정한 3개 도메인에서 무조건 1개씩 수집하도록 도메인별 개별 검색 수행
        for domain in approved_domains:
            domain_query = f"{search_query} site:{domain}"
            logger.info(f"Fetching Google News Macro & Market News for domain: {domain}")
            
            macro_articles = fetch_google_news_rss(query=domain_query, max_results=10)
            
            for item in macro_articles:
                url = item.get('url', '')
                if not url or url in seen_urls: continue
                
                # 구글 뉴스 검색이 site 연산자를 무시할 수 있으므 도메인 재확인
                if domain.lower() not in url.lower():
                    continue
                    
                seen_urls.add(url)
                
                title = item.get('title', '')
                summary = item.get('description', '')
                if not summary:
                    summary = title
                    
                pub = None
                if item.get('publish_date_raw'):
                    try:
                        from dateutil import parser as date_parser
                        pub = date_parser.parse(item['publish_date_raw'])
                    except: pass
                
                if not pub: pub = ref_date
                if pub.tzinfo is None: pub = pub.replace(tzinfo=pytz.utc)
                if pub < cutoff: continue
                
                # 본문 스크래핑
                full_text = summary
                if "investopedia.com" in url.lower():
                    # 인베스토피디아는 newspaper 모듈 사용 시 엉뚱한(기사를 ) 하단 문제가 있어 즉시 Playwright 사용
                    try:
                        from src.core.utils import get_article_text_playwright
                        logger.info(f"Using Playwright directly for Investopedia: {url}")
                        pw_text = get_article_text_playwright(url)
                        if pw_text and len(pw_text) > 100:
                            full_text = pw_text
                        else:
                            logger.warning(f"Playwright extracted too little text for {url}")
                    except Exception as e:
                        logger.error(f"Playwright error for Investopedia ({url}): {e}")
                else:
                    try:
                        article = newspaper.Article(url, language='en', config=config)
                        article.download()
                        article.parse()
                        if article.text and len(article.text) > 150:
                            full_text = article.text
                        else:
                            raise Exception("Text too short or blocked (possible paywall/bot protection)")
                    except Exception as parse_err:
                        logger.warning(f"Macro News standard parsing failed ({url}): {parse_err}. Trying Playwright...")
                        try:
                            from src.core.utils import get_article_text_playwright
                            pw_text = get_article_text_playwright(url)
                            if pw_text:
                                full_text = pw_text
                                logger.info(f"Playwright successfully extracted text for {url}")
                            else:
                                logger.error(f"Playwright also failed for {url}")
                        except Exception as pw_err:
                            logger.error(f"Playwright fallback error ({url}): {pw_err}")

                all_data.append({
                    "category": "Macro & Market", 
                    "title": title, 
                    "url": url, 
                    "publish_date": pub, 
                    "summary": summary, 
                    "text": full_text, 
                    "keywords": [], 
                    "sentiment": 0.0,
                    "reasoning": "Macro info"
                })
                
    "Authorization": f"Bearer {api.token}", 다음 도메인으로 넘어감
                break
    except Exception as e:
        logger.error(f"Google Macro News Error: {e}")"""

start_idx = content.find(old_macro_start)
end_idx = content.find(old_macro_end) + len(old_macro_end)

if start_idx != -1 and end_idx > start_idx:
    content = content[:start_idx] + new_macro_code + content[end_idx:]
    with open("src/core/scraper.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Macro fix applied.")
else:
    print("Macro fix failed: markers not found.")

