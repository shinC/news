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

def fetch_google_news_rss(query: str, hl: str = 'en-US', gl: str = 'US', ceid: str = 'US:en', max_results: int = 7) -> List[Dict[str, Any]]:
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'xml')
        for item in soup.find_all('item'):
            raw_desc = item.description.text if item.description else ""
            clean_desc = BeautifulSoup(raw_desc, 'html.parser').get_text(separator=' ', strip=True)
            articles.append({"title": item.title.text, "url": item.link.text, "description": clean_desc, "publish_date_raw": item.pubDate.text})
            if len(articles) >= max_results: break
    except: pass
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
        from src.core.utils import get_yahoo_summary, get_google_summary
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
    config = newspaper.Config()
    config.request_timeout = 10
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'

    for cat, query in settings.categories.items():
        logger.info(f"Fetching {cat}...")
        for item in fetch_google_news_rss(query, max_results=settings.max_results_per_section):
            try:
                url = decode_google_news_url(item['url'])
                article = newspaper.Article(url, language='en', config=config)
                article.download()
                article.parse()
                article.nlp()
                title = item.get('title', article.title)
                summary = get_best_summary(title, article.text, item.get('description'), is_finance=(cat in ['Finance', 'Economy']))
                pub = article.publish_date or ref_date
                if pub.tzinfo is None: pub = pub.replace(tzinfo=pytz.utc)
                if pub < cutoff: continue
                all_data.append({"category": cat, "title": title, "url": url, "publish_date": pub, "summary": summary, "text": article.text, "keywords": article.keywords, "priority_score": 0})
            except: pass
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
    
    try: yf_news = yf.Ticker(ticker_str).news
    except: yf_news = []
    
    config = newspaper.Config()
    config.request_timeout = 10
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    
    seen = set()
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
            news_data.append({"company": ticker_str, "title": title, "url": url, "summary": summary, "text": article.text, "publish_date": ref_date, "priority_score": 0, "original_rank": len(news_data)})
        except: pass
    return news_data
