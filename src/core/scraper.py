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
        dec = new_decoderv1(url)
        if dec.get('status'):
            return dec.get('decoded_url')
    except Exception as e:
        logger.error(f"Error decoding Google News URL: {e}")
    return url

def fetch_google_news_rss(query: str = None, topic_id: str = None, hl: str = 'en-US', gl: str = 'US', ceid: str = 'US:en', max_results: int = 7) -> List[Dict[str, Any]]:
    import time
    import random
    
    # 랜덤 지연 추가 (구글 차단 방지)
    delay = random.uniform(0.5, 1.5)
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
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'xml')
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

    # 2. 구글 뉴스 RSS로 매크로 뉴스 추가 (site: 연산자를 제외한 안전한 키워드 쿼리로 수집)
    logger.info("Fetching Google News Macro & Market News (Plain Keyword Queries)...")
    try:
        seen_urls = set([item['url'] for item in all_data])
        
        # 구글 RSS 호출 밴을 방지하기 위해 단일 일반 쿼리로 1번만 호출 후 로컬에서 도메인/키워드 필터링
        query = "Stock market today"
        
        macro_articles = []
        logger.info(f"Targeted plain query: {query}")
        macro_articles.extend(fetch_google_news_rss(query=query, max_results=50))
        
        # 구글 뉴스 암호화 URL 일괄(Batch) 디코딩 적용
        from src.core.utils import batch_decode_google_urls
        raw_urls = [item['url'] for item in macro_articles if item.get('url')]
        decoded_map = batch_decode_google_urls(raw_urls)
        
        for item in macro_articles:
            if item.get('url') in decoded_map:
                item['url'] = decoded_map[item['url']]
        
        # 수집할 도메인 추적
        domain_found = {
            "finance.yahoo.com": False,
            "investopedia.com": False
        }
        
        def process_macro_article(item, matched_domain):
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
            if pub < cutoff: return False
            
            from src.core.utils import get_article_text_playwright
            full_text = get_article_text_playwright(item['url'])
            
            all_data.append({
                "category": "Macro & Market", 
                "title": title, 
                "url": item['url'], 
                "publish_date": pub, 
                "summary": summary, 
                "text": full_text, 
                "keywords": [], 
                "priority_score": 0
            })
            seen_urls.add(item['url'])
            domain_found[matched_domain] = True
            return True

        # 1차 검색: "Stock market today" 키워드가 제목에 포함된 야후 및 인베스토페디아 기사 찾기
        for item in macro_articles:
            url = item['url']
            title = item.get('title', '')
            if not url or url in seen_urls: continue
            
            title_lower = title.lower()
            if "stock market today" not in title_lower:
                continue
                
            is_yahoo = "finance.yahoo.com" in url.lower() or "yahoo" in title_lower
            is_investopedia = "investopedia.com" in url.lower() or "investopedia" in title_lower
            
            if is_yahoo and not domain_found["finance.yahoo.com"]:
                process_macro_article(item, "finance.yahoo.com")
            elif is_investopedia and not domain_found["investopedia.com"]:
                process_macro_article(item, "investopedia.com")

        # 2차 검색: 인베스토페디아가 1차에서 안 찾아진 경우, "Markets News" 키워드로 다시 찾기
        if not domain_found["investopedia.com"]:
            for item in macro_articles:
                url = item['url']
                title = item.get('title', '')
                if not url or url in seen_urls: continue
                
                title_lower = title.lower()
                if "markets news" not in title_lower:
                    continue
                    
                is_investopedia = "investopedia.com" in url.lower() or "investopedia" in title_lower
                if is_investopedia and not domain_found["investopedia.com"]:
                    process_macro_article(item, "investopedia.com")
    except Exception as e:
        logger.error(f"Google Macro News Error: {e}")

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
    for item in gn_articles:
        try:
            url = decode_google_news_url(item['url'])
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
