import logging
import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
import newspaper
from config.settings import settings

logger = logging.getLogger(__name__)

def decode_google_news_url(url: str) -> str:
    if "news.google.com" not in url: return url
    try:
        from googlenewsdecoder import new_decoderv1
        from concurrent.futures import ThreadPoolExecutor
        
        # 수동으로 스레드를 생성하여 wait=False로 셧다운함으로써 join 락 차단
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(new_decoderv1, url)
        try:
            dec = future.result(timeout=3.0)
            if dec.get('status'):
                return dec.get('decoded_url')
        finally:
            executor.shutdown(wait=False)
    except Exception as e:
        logger.error(f"Error decoding Google News URL (timeout): {e}")
    return url

def fetch_google_news_rss(query: str = None, topic_id: str = None, hl: str = 'en-US', gl: str = 'US', ceid: str = 'US:en', max_results: int = 7) -> List[Dict[str, Any]]:
    import time
    import random
    import urllib.request
    
    # 랜덤 지연 추가 (지연 시간 소폭 상향하여 안정성 도모)
    delay = random.uniform(1.0, 2.0)
    logger.info(f"Google RSS 차단 방지를 위해 {delay:.2f}초 대기합니다...")
    time.sleep(delay)
    
    if topic_id:
        url = f"https://news.google.com/rss/topics/{topic_id}?hl={hl}&gl={gl}&ceid={ceid}"
    elif query:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    else:
        return []

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    articles = []
    try:
        req = urllib.request.Request(url, headers=headers)
        # urllib 타임아웃을 3.0초로 타이트하게 지정하여 구글의 Hold 지연을 즉시 탈출
        with urllib.request.urlopen(req, timeout=3.0) as response:
            html_content = response.read()
            soup = BeautifulSoup(html_content, 'xml')
            for item in soup.find_all('item'):
                raw_desc = item.description.text if item.description else ""
                clean_desc = BeautifulSoup(raw_desc, 'html.parser').get_text(separator=' ', strip=True)
                
                raw_url = item.link.text if item.link else ""
                
                articles.append({
                    "title": item.title.text if item.title else "", 
                    "url": raw_url, 
                    "description": clean_desc, 
                    "publish_date_raw": item.pubDate.text if item.pubDate else ""
                })
                if len(articles) >= max_results: break
    except Exception as e: 
        logger.error(f"Google RSS Error: {e}")
    return articles

def check_similarity(t, s):
    if not s: return True
    tw = set(re.sub(r'[^a-z0-9]', ' ', t.lower()).split())
    sw = set(re.sub(r'[^a-z0-9]', ' ', s.lower()).split())
    if not tw: return False
    common = len(tw.intersection(sw))
    return common > len(tw) * 0.7 and len(s) < 350

def get_best_summary(title, article_text, rss_desc, is_finance=False):
    summary = ""
    if rss_desc and len(rss_desc) > 200 and not check_similarity(title, rss_desc):
        summary = rss_desc
    if not summary and article_text and len(article_text) > 300:
        summary = article_text[:1200]
    if not summary or len(summary) < 200 or check_similarity(title, summary):
        from src.core.utils import get_yahoo_summary, get_google_summary
        
        # 야후/구글 검색 스니펫 (네이버 API 요약 제거)
        fallback = get_yahoo_summary(title) if is_finance else get_google_summary(title)
            
        if fallback and len(fallback) > 150:
            summary = fallback
    if not summary or len(summary) < 150 or check_similarity(title, summary):
        summary = article_text[:1000] if article_text else rss_desc or title
    summary = re.sub(r'\s+', ' ', summary).strip()
    return summary[:1500] if len(summary) > 1500 else summary

def fetch_news(dynamic_keywords: List[str] = None, market_date: datetime = None) -> List[Dict[str, Any]]:
    logger.info("Category News Pipeline Started")
    all_data = []
    ref_date = market_date if market_date else datetime.now(pytz.utc)
    if ref_date.tzinfo is None: ref_date = ref_date.replace(tzinfo=pytz.utc)
    cutoff = ref_date - timedelta(days=3)

    # 주요뉴스 헤드라인 수집 (Category News) 주석 처리 (사용자 요청)
    # for cat, query_or_topic in settings.categories.items():
    #     if query_or_topic.startswith("CAAq"):
    #         logger.info(f"Fetching {cat} (Topic ID)...")
    #         rss_articles = fetch_google_news_rss(topic_id=query_or_topic, max_results=settings.max_results_per_section)
    #     else:
    #         logger.info(f"Fetching {cat} (Query)...")
    #         rss_articles = fetch_google_news_rss(query=query_or_topic, max_results=settings.max_results_per_section)
    #     for item in rss_articles:
    #         try:
    #             url = item['url']
    #             title = item.get('title', '')
    #             
    #             # 네이버 API 요약 삭제, RSS 설명 사용
    #             summary = item.get('description', '')
    #             if not summary:
    #                 summary = title
    #             
    #             # 날짜 파싱
    #             pub = None
    #             if item.get('publish_date_raw'):
    #                 try:
    #                     from dateutil import parser as date_parser
    #                     pub = date_parser.parse(item['publish_date_raw'])
    #                 except: pass
    #             
    #             if not pub: pub = ref_date
    #             if pub.tzinfo is None: pub = pub.replace(tzinfo=pytz.utc)
    #             if pub < cutoff:
    #                 continue
    #             
    #             all_data.append({
    #                 "category": cat, 
    #                 "title": title, 
    #                 "url": url, 
    #                 "publish_date": pub, 
    #                 "summary": summary, 
    #                 "text": summary, # 본문 대신 요약 사용
    #                 "keywords": [], 
    #                 "priority_score": 0
    #             })
    #         except Exception as e: 
    #             logger.error(f"Category Parsing Error: {e}")

    # 2. 야후 파이낸스 및 인베스토페디아 직접 스크래핑으로 매크로 뉴스 추가
    logger.info("Fetching Yahoo Finance & Investopedia Macro & Market News via Direct Scraping...")
    try:
        from playwright.sync_api import sync_playwright
        from src.core.utils import get_article_text_playwright
        
        macro_articles = []
        
        # 날짜 필터 완화 (장외 시간/주말에도 최근 마감시황 뉴스를 안정적으로 가져오도록 5일로 설정)
        cutoff_macro = ref_date - timedelta(days=5)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage', '--no-sandbox'])
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # 2.1 Yahoo Finance Direct Scraping (topic: stock-market-news)
            try:
                yahoo_count = 0
                seen_yahoo_urls = set()
                
                # 최대 3페이지까지 탐색하여 "stock market"으로 시작하는 기사 발굴
                for page_num in range(1, 4):
                    if page_num == 1:
                        yahoo_url = "https://finance.yahoo.com/topic/stock-market-news"
                    else:
                        yahoo_url = f"https://finance.yahoo.com/topic/stock-market-news/{page_num}/"
                        
                    logger.info(f"Opening Yahoo Topic Page (Page {page_num}): {yahoo_url}")
                    page.goto(yahoo_url, timeout=30000, wait_until='domcontentloaded')
                    page.wait_for_timeout(2000)
                    
                    # 각 페이지마다 기사 로드를 위해 3회 스크롤
                    for _ in range(3):
                        page.evaluate("window.scrollBy(0, 1500);")
                        page.wait_for_timeout(800)
                        
                    yahoo_links = page.evaluate("""() => {
                        let res = [];
                        let anchors = document.querySelectorAll('a');
                        for (let a of anchors) {
                            let href = a.getAttribute('href');
                            if (!href) continue;
                            
                            let title = a.innerText ? a.innerText.trim() : "";
                            if (!title) {
                                let heading = a.querySelector('h3, h4, span, p');
                                if (heading) title = heading.innerText.trim();
                            }
                            if (!title) {
                                title = a.getAttribute('title') || a.getAttribute('aria-label') || "";
                                title = title.trim();
                            }
                            
                            let isArticle = href.includes('/news/') || href.includes('/article/') || href.includes('/articles/') || href.includes('/live/') || href.includes('/video/') || href.includes('/markets/');
                            if (isArticle && title.length > 12) {
                                res.push({title: title, href: href});
                            }
                        }
                        return res;
                    }""")
                    
                    found_article = False
                    for item in yahoo_links:
                        title = item['title']
                        raw_url = item['href']
                        full_url = raw_url if raw_url.startswith("http") else "https://finance.yahoo.com" + raw_url
                        if full_url in seen_yahoo_urls:
                            continue
                        
                        title_lower = title.lower()
                        # 사용자의 엄격한 제목 시작 요구사항 부합 여부 검증 ("stock market news" 또는 "stock market today")
                        if title_lower.startswith("stock market"):
                            seen_yahoo_urls.add(full_url)
                            macro_articles.append({
                                "title": title,
                                "url": full_url,
                                "publish_date": ref_date,
                                "description": title
                            })
                            yahoo_count += 1
                            found_article = True
                            break
                            
                    if found_article:
                        logger.info(f"Successfully found Yahoo Finance macro article on page {page_num}.")
                        break
            except Exception as ye:
                logger.error(f"Yahoo direct scraping error: {ye}")
                
            # 2.2 Investopedia Direct Scraping (markets-news)
            # 기사 제목에 "market news" 키워드가 포함된 최신 기사 선별
            try:
                investopedia_url = "https://www.investopedia.com/markets-news-4427704"
                logger.info(f"Opening Investopedia Page and scrolling: {investopedia_url}")
                page.goto(investopedia_url, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(3000)
                
                 # 스크롤하여 더 많은 기사 로드
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1500);")
                    page.wait_for_timeout(1000)
                
                investopedia_links = page.evaluate("""() => {
                    let res = [];
                    let anchors = document.querySelectorAll('.mntl-document-card, a');
                    for (let a of anchors) {
                        let href = a.getAttribute('href');
                        if (!href) continue;
                        
                        let titleEl = a.querySelector('.card__title-text, .card__title');
                        let title = titleEl ? titleEl.innerText.trim() : a.innerText.trim();
                        
                        if (href.startsWith('http') && href.includes('investopedia.com') && title.length > 15) {
                            res.push({title: title, href: href});
                        }
                    }
                    return res;
                }""")
                
                seen_inv_urls = set()
                inv_count = 0
                
                # 인베스토페디아 마감시황 뉴스 조건: "markets news" 또는 "market news" 시작
                for item in investopedia_links:
                    title = item['title']
                    href = item['href']
                    if href in seen_inv_urls:
                        continue
                        
                    title_lower = title.lower()
                    if title_lower.startswith("markets news") or title_lower.startswith("market news"):
                        seen_inv_urls.add(href)
                        macro_articles.append({
                            "title": title,
                            "url": href,
                            "publish_date": ref_date,
                            "description": title
                        })
                        inv_count += 1
                        break
            except Exception as ie:
                logger.error(f"Investopedia direct scraping error: {ie}")
                
            browser.close()
            
        # 2.3 수집된 기사의 본문(Playwright) 및 정보 저장
        for item in macro_articles:
            url = item['url']
            title = item['title']
            pub = item['publish_date']
            desc = item['description']
            
            logger.info(f"Extracting body content for Macro News: {title} ({url})")
            full_text = get_article_text_playwright(url)
            
            # 요약 생성
            summary = full_text[:1200] if len(full_text) > 200 else desc
            
            all_data.append({
                "category": "Macro & Market",
                "title": title,
                "url": url,
                "publish_date": pub,
                "summary": summary,
                "text": full_text if full_text else summary,
                "keywords": [],
                "priority_score": 0
            })
            
    except Exception as e:
        logger.error(f"Yahoo & Investopedia Macro Scraping Error: {e}")

    return all_data
def fetch_company_news_us(company, company_full_name: str = None, days: int = 3, market_date: datetime = None) -> List[Dict[str, Any]]:
    # company가 리스트로 들어오는 경우(market.py 호환성) 처리
    ticker_str = company[0] if isinstance(company, list) else company
    logger.info(f"[{ticker_str}] Company News Pipeline Started")
    
    import yfinance as yf
    if not company_full_name:
        try: company_full_name = yf.Ticker(ticker_str).info.get('longName', ticker_str)
        except: company_full_name = ticker_str

    news_data = []
    ref_date = market_date if market_date else datetime.now(pytz.utc)
    cutoff = ref_date - timedelta(days=days)
    seen = set()
    
    # 1. Google News RSS (본문 스크래핑 제외, 제목/링크만)
    # 종목별로 5개 기사 수집
    search_query = f"{ticker_str} stock why up today"
    logger.info(f"[{ticker_str}] Fetching Google News RSS with query: '{search_query}'...")
    gn_articles = fetch_google_news_rss(search_query, max_results=5)
    
    # 구글 뉴스 암호화 URL 일괄(Batch) 디코딩 적용으로 속도 향상 및 행 현상 방지
    from src.core.utils import batch_decode_google_urls
    raw_urls = [item['url'] for item in gn_articles if item.get('url')]
    decoded_map = batch_decode_google_urls(raw_urls)
    
    for item in gn_articles:
        try:
            raw_url = item['url']
            url = decoded_map.get(raw_url, raw_url)
            if url in seen: continue
            seen.add(url)
            
            title = item.get('title', '')
            
            # 네이버 API 요약 삭제, RSS 설명 사용
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
            
            news_data.append({
                "company": ticker_str, 
                "title": title, 
                "url": url, 
                "summary": summary, 
                "text": summary, # 본문 없이 요약만 사용
                "publish_date": pub, 
                "priority_score": 0, 
                "original_rank": len(news_data)
            })
        except Exception as e:
            logger.error(f"Google News RSS Parsing Error: {e}")

    # 2. Yahoo Finance (구글 뉴스가 없는 경우에만 백업 수집)
    if not news_data:
        logger.info(f"[{ticker_str}] No Google News found. Fetching Yahoo Finance as backup...")
        try: yf_news = yf.Ticker(ticker_str).news
        except: yf_news = []
        
        config = newspaper.Config()
        config.request_timeout = 10
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        
        for item in yf_news:
            try:
                c = item.get('content', {})
                url = c.get('canonicalUrl', {}).get('url', '') or c.get('clickThroughUrl', {}).get('url', '')
                if not url or url in seen: continue
                seen.add(url)
                
                article = newspaper.Article(url, language='en', config=config)
                article.download()
                article.parse()
                article.nlp()
                
                title = article.title or c.get('title', '')
                summary = get_best_summary(title, article.text, c.get('summary'), is_finance=True)
                news_data.append({
                    "company": ticker_str, 
                    "title": title, 
                    "url": url, 
                    "summary": summary, 
                    "text": article.text, 
                    "publish_date": ref_date, 
                    "priority_score": 0, 
                    "original_rank": len(news_data)
                })
            except: pass
        
    return news_data
