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

def fetch_google_news_rss(query: str = None, topic_id: str = None, hl: str = 'en-US', gl: str = 'US', ceid: str = 'US:en', max_results: int = 7) -> List[Dict[str, Any]]:
    import time
    import random
    
    # 랜덤 지연 추가 (구글 차단 방지)
    delay = random.uniform(1.5, 3.5)
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
            articles.append({
                "title": item.title.text, 
                "url": item.link.text, 
                "description": clean_desc, 
                "publish_date_raw": item.pubDate.text
            })
            if len(articles) >= max_results: break
    except Exception as e: 
        logger.error(f"Google RSS Error: {e}")
    return articles

def decode_google_news_url(url: str) -> str:
    if "news.google.com" not in url: return url
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if "news.google.com" not in res.url: return res.url
        patterns = [r'data-url="([^"]+)"', r'data-n-au="([^"]+)"', r'url=(https?://[^&"]+)', r'content="0;url=(https?://[^"]+)"']
        for p in patterns:
            m = re.search(p, res.text, re.I)
            if m:
                d = m.group(1).strip('[]" ')
                if "google.com" not in d: return d
    except: pass
    return url

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
        from src.core.utils import get_yahoo_summary, get_google_summary, get_naver_api_summary
        
        # 1순위: 네이버 API (품질 및 안정성 최고)
        fallback = get_naver_api_summary(title)
        
        # 2순위: 야후/구글 검색 스니펫
        if not fallback or len(fallback) < 150:
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

    for cat, query_or_topic in settings.categories.items():
        if query_or_topic.startswith("CAAq"):
            logger.info(f"Fetching {cat} (Topic ID)...")
            rss_articles = fetch_google_news_rss(topic_id=query_or_topic, max_results=settings.max_results_per_section)
        else:
            logger.info(f"Fetching {cat} (Query)...")
            rss_articles = fetch_google_news_rss(query=query_or_topic, max_results=settings.max_results_per_section)
        for item in rss_articles:
            try:
                url = item['url'] # URL 디코딩 생략 (차단 방지)
                title = item.get('title', '')
                
                # 본문 파싱 생략, 대신 네이버 API로 고품질 스니펫 수집
                from src.core.utils import get_naver_api_summary
                summary = get_naver_api_summary(title)
                
                # 네이버 API 실패 시 RSS 요약 사용
                if not summary or len(summary) < 150:
                    summary = item.get('description', '')
                
                # 날짜 파싱
                pub = None
                if item.get('publish_date_raw'):
                    try:
                        from dateutil import parser as date_parser
                        pub = date_parser.parse(item['publish_date_raw'])
                    except: pass
                
                if not pub: pub = ref_date
                if pub.tzinfo is None: pub = pub.replace(tzinfo=pytz.utc)
                if pub < cutoff: continue
                
                all_data.append({
                    "category": cat, 
                    "title": title, 
                    "url": url, 
                    "publish_date": pub, 
                    "summary": summary, 
                    "text": summary, # 본문 대신 요약 사용
                    "keywords": [], 
                    "priority_score": 0
                })
            except Exception as e: 
                logger.error(f"Category Parsing Error: {e}")

    # 2. 야후 파이낸스 카테고리 뉴스 추가 (Top Stories)
    logger.info("Fetching Yahoo Finance Macro & Market News...")
    try:
        import feedparser
        
        seen_urls = set([item['url'] for item in all_data])
        rss_url = "https://finance.yahoo.com/news/rssindex"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(rss_url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            d = feedparser.parse(res.content)
            for item in d.entries[:10]: # 상위 10개만 수집
                url = item.get('link', '')
                if not url or url in seen_urls: continue
                seen_urls.add(url)
                
                title = item.get('title', '')
                
                # 네이버 API 요약 활용
                from src.core.utils import get_naver_api_summary
                summary = get_naver_api_summary(title)
                
                if not summary or len(summary) < 150:
                    summary = item.get('summary', '') or item.get('description', '')
                    summary = BeautifulSoup(summary, 'html.parser').get_text(separator=' ', strip=True)
                    
                pub = ref_date
                pub_str = item.get('published') or item.get('pubDate')
                if pub_str:
                    try:
                        from dateutil import parser as date_parser
                        pub = date_parser.parse(str(pub_str))
                    except: pass
                
                if pub.tzinfo is None: pub = pub.replace(tzinfo=pytz.utc)
                if pub < cutoff: continue
                
                all_data.append({
                    "category": "Macro & Market", 
                    "title": title, 
                    "url": url, 
                    "publish_date": pub, 
                    "summary": summary, 
                    "text": summary, 
                    "keywords": [], 
                    "priority_score": 0
                })
    except Exception as e:
        logger.error(f"Yahoo Macro RSS Error: {e}")

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
    # 종목별로 10개 기사 수집
    logger.info(f"[{ticker_str}] Fetching Google News RSS...")
    gn_articles = fetch_google_news_rss(company_full_name, max_results=10)
    for item in gn_articles:
        try:
            url = item['url']
            if url in seen: continue
            seen.add(url)
            
            title = item.get('title', '')
            
            # 본문 스크래핑 대신 네이버 API 요약 사용
            from src.core.utils import get_naver_api_summary
            summary = get_naver_api_summary(title)
            
            if not summary or len(summary) < 150:
                summary = item.get('description', '')
            
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

    # 2. Yahoo Finance (원래대로 유지)
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
