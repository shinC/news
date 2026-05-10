import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pytz
import urllib.parse
from gnews import GNews
from newspaper import Article
from config.settings import settings_kr

logger = logging.getLogger(__name__)

def decode_google_news_url(url: str) -> str:
    """구글 뉴스 RSS URL을 원래의 기사 URL로 디코딩합니다."""
    try:
        from gnews.utils import decode_google_news_url as decoder
        return decoder(url)
    except:
        return url

def fetch_google_news_web(query: str, hl: str = 'ko', gl: str = 'KR', ceid: str = 'KR:ko') -> List[Dict[str, Any]]:
    """구글 뉴스 검색 페이지를 직접 스크래핑하여 기사 목록을 반환합니다."""
    import urllib.parse
    import re
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': f'{hl}-{gl},{hl};q=0.9,en;q=0.8'
    }
    
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        # 구글 뉴스 웹페이지 구조 분석 (article 태그 위주)
        # 2024-2025 기준 article 태그 내부에 제목과 링크가 포함됨
        for item in soup.select('article'):
            link_tag = item.find('a', href=True)
            if not link_tag: continue
            
            title = link_tag.get_text().strip()
            href = link_tag['href']
            
            if href.startswith('.'):
                href = "https://news.google.com" + href[1:]
                
            # 시간 정보 추출
            time_tag = item.find('time')
            published_date = ""
            if time_tag:
                published_date = time_tag.get('datetime') or time_tag.get_text()
                
            articles.append({
                "title": title,
                "url": decode_google_news_url(href),
                "published date": published_date,
                "source": "google_web"
            })
            
    except Exception as e:
        logger.error(f"Google News Web Scraping Error ({hl}-{gl}): {e}")
        
    return articles

def fetch_news(dynamic_keywords: List[str] = None, market_date: datetime = None) -> List[Dict[str, Any]]:
    """
    네이버 증권 뉴스의 주요 섹션들을 스크래핑한 뒤,
    newspaper4k를 이용해 본문을 파싱하고 키워드 가중치를 적용합니다.
    """
    sections = settings_kr.naver_finance_sections
    logger.info(f"네이버 증권 뉴스 수집 시작: 대상 섹션 {len(sections)}개, 기준날짜={market_date}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    # 각 섹션별로 기사를 수집하여 category 태그를 붙입니다.
    raw_articles = []
    num_sections = len(sections)
    target_per_section = settings_kr.max_results // num_sections
    
    for category, base_url in sections.items():
        logger.info(f"섹션 수집 중: {category} ({base_url})")
        section_urls = []
        try:
            res = requests.get(base_url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'lxml')
            
            selectors = [
                '.articleSubject a', 
                '.newsList ul li dl dt a', 
                '.hotNewsList a', 
                '.rank_news a',
                'a[href*="news_read.naver"]'
            ]
            
            seen_in_section = set()
            for selector in selectors:
                links = soup.select(selector)
                for a in links:
                    href = a.get('href', '')
                    url = None
                    if 'news_read.naver' in href:
                        params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        article_id = params.get('article_id', [None])[0]
                        office_id = params.get('office_id', [None])[0]
                        if article_id and office_id:
                            url = f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"
                    elif 'n.news.naver.com' in href:
                        url = href.split('?')[0]
                    
                    if url and url not in seen_in_section:
                        section_urls.append(url)
                        seen_in_section.add(url)
                        
                    if len(section_urls) >= target_per_section:
                        break
                if len(section_urls) >= target_per_section:
                    break
            
            for url in section_urls:
                raw_articles.append({"url": url, "category": category})
        except Exception as e:
            logger.error(f"네이버 증권 뉴스 URL 수집 실패 ({category}: {base_url}): {e}")
 
    logger.info("기사 다운로드 및 파싱 시작...")
    news_data = []
    
    # 합쳐진 우선순위 키워드 구성
    base_keywords = getattr(settings_kr, 'priority_keywords', [])
    priority_keywords = base_keywords + (dynamic_keywords if dynamic_keywords else [])
    
    import newspaper
    config = newspaper.Config()
    config.browser_user_agent = headers['User-Agent']
    config.request_timeout = 10
    
    # 기준 날짜 설정 (한국 시간 KST 기준)
    kst = pytz.timezone('Asia/Seoul')
    reference_date = market_date if market_date else datetime.now(kst)
    if reference_date.tzinfo is None:
        reference_date = kst.localize(reference_date)
    else:
        reference_date = reference_date.astimezone(kst)

    # 날짜 필터링 (설정된 period 기준)
    days = 2
    if settings_kr.period.endswith('d'):
        try:
            days = int(settings_kr.period[:-1])
        except: pass
    
    cutoff_date = reference_date - timedelta(days=days)
    upper_cutoff = reference_date + timedelta(days=1)
    
    logger.info(f"한국 뉴스 수집 기간 필터: {cutoff_date} ~ {upper_cutoff}")

    for item in raw_articles:
        url = item['url']
        category = item['category']
        try:
            article = Article(url, language='ko', config=config)
            article.download()
            article.parse()
            article.nlp() 
            
            publish_date = article.publish_date
            # 네이버 날짜 파싱 보완
            if not publish_date and 'naver.com' in url:
                try:
                    import pandas as pd
                    soup_article = BeautifulSoup(article.html, 'lxml')
                    # 다양한 패턴 시도
                    date_elem = (soup_article.find('span', {'data-date-time': True}) or 
                                 soup_article.find('span', {'data-published-time': True}) or
                                 soup_article.find('meta', property='article:published_time'))
                    
                    if date_elem:
                        date_str = date_elem.get('data-date-time') or date_elem.get('data-published-time') or date_elem.get('content')
                        if date_str:
                            publish_date = pd.to_datetime(date_str)
                except Exception as de:
                    logger.debug(f"네이버 날짜 추가 추출 실패 ({url}): {de}")
            
            if publish_date:
                if publish_date.tzinfo is None:
                    publish_date = kst.localize(publish_date)
                else:
                    publish_date = publish_date.astimezone(kst)
                
                if publish_date < cutoff_date or publish_date > upper_cutoff:
                    logger.debug(f"기간 외 한국 기사 제외 ({publish_date}): {article.title}")
                    continue
            else:
                # [고도화] 실제 날짜가 없거나 확인이 안되면 수집 금지
                logger.warning(f"발행일을 알 수 없는 한국 기사 제외: {article.title}")
                continue

            priority_score = 0
            text_to_check = (article.title + " " + article.summary + " " + " ".join(article.keywords)).lower()
            for keyword in priority_keywords:
                if keyword.lower() in text_to_check:
                    priority_score += 1
            
            data = {
                "title": article.title,
                "url": url,
                "category": category,
                "publish_date": publish_date,
                "authors": article.authors,
                "summary": article.summary,
                "text": article.text,
                "keywords": article.keywords,
                "priority_score": priority_score
            }
            news_data.append(data)
        except Exception as e:
            logger.error(f"기사 파싱 실패 ({url}): {e}")
            
    logger.info(f"파싱 완료된 한국 기사 수: {len(news_data)}")
    return news_data

def fetch_company_news_kr(companies: List[str], days: int = 3) -> List[Dict[str, Any]]:
    """
    구글 뉴스(KR)와 네이버 뉴스를 통합하여 특정 기업들에 대한 주요 뉴스를 수집합니다.
    """
    logger.info(f"한국 기업 뉴스 수집 시작: 대상 기업={companies}, 기간={days}일")
    news_data = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    import newspaper
    config = newspaper.Config()
    config.browser_user_agent = headers['User-Agent']
    config.request_timeout = 10
    
    kst = pytz.timezone('Asia/Seoul')
    cutoff_date = datetime.now(kst) - timedelta(days=days)
    
    for company in companies:
        logger.info(f"[{company}] 뉴스 검색 중 (Google News & Naver)...")
        candidates = {} # {url: {title, summary, pub_date, source, original_rank}}
        seen_titles = set()
        
        def normalize_title(t):
            import re
            t = t.lower()
            t = re.sub(r' - .+$', '', t) 
            t = re.sub(r'[^a-z0-9가-힣]', '', t)
            return t

        try:
            # Source 1: Google News Search (RSS version of web search)
            # 직접적인 웹 스크래핑이 차단되므로 브라우저 결과와 가장 유사한 RSS 검색을 최우선으로 사용합니다.
            logger.info(f"Source 1: Fetching Google News Search for {company}...")
            google_news_client = GNews(language='ko', country='KR', period=f'{days}d', max_results=20)
            gn_news = google_news_client.get_news(company)
            
            for idx, item in enumerate(gn_news):
                raw_url = item.get('url', '')
                if not raw_url: continue
                url = decode_google_news_url(raw_url)
                if url in candidates: continue
                
                title = item.get('title', '')
                norm_title = normalize_title(title)
                if norm_title in seen_titles: continue
                
                candidates[url] = {
                    "title": title,
                    "summary": item.get('description', ''),
                    "pub_date": None,
                    "source": "google_news",
                    "original_rank": idx
                }
                seen_titles.add(norm_title)

            # Source 2: Naver News (보완)
            logger.info(f"Source 2: Fetching Naver News for {company}...")
            encoded_query = urllib.parse.quote(company)
            search_url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sort=0"
            res = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for a in soup.select('a[href*="n.news.naver.com"]'):
                url = a.get('href', '').split('?')[0]
                if url in candidates: continue
                title = a.get_text()
                norm_title = normalize_title(title)
                if norm_title in seen_titles: continue
                
                candidates[url] = {
                    "title": title,
                    "summary": "",
                    "pub_date": None,
                    "source": "naver",
                    "original_rank": len(candidates) + 50
                }
                seen_titles.add(norm_title)


            # 후보 기사 처리
            final_seen_titles = set()
            for url, info in candidates.items():
                try:
                    pub_date = info['pub_date']
                    if pub_date and pub_date < cutoff_date: continue
                    
                    article = Article(url, language='ko', config=config)
                    article.download()
                    article.parse()
                    article.nlp()
                    
                    # 범용적인 제목(MSN, Google News, Home 등)으로 덮어씌워지는 것 방지
                    new_title = article.title
                    junk_titles = ["MSN", "Google News", "Home", "AOL.com", "Yahoo Finance", "Business", "News"]
                    is_junk = any(jt.lower() == (new_title or "").strip().lower() for jt in junk_titles) or len(new_title or "") < 10
                    
                    title = new_title if (new_title and not is_junk) else info['title']
                    text = article.text if article.text else info['summary']
                    
                    if not title or not text: continue
                    
                    # 최종 제목에 대해서도 junk 체크 (info['title']이 junk인 경우 대비)
                    if any(jt.lower() == title.strip().lower() for jt in junk_titles): continue
                    
                    norm_title = normalize_title(title)
                    if norm_title in final_seen_titles: continue
                    
                    # 회사명 매칭 검증
                    is_matched = company.lower() in title.lower() or company.lower() in text.lower()
                    if not is_matched: continue
                    
                    relevance_score = 1 if company.lower() in title.lower() else 0
                    final_seen_titles.add(norm_title)
                    
                    news_data.append({
                        "company": company,
                        "title": title,
                        "url": url,
                        "publish_date": article.publish_date or pub_date,
                        "relevance_score": relevance_score,
                        "original_rank": info.get('original_rank', 99),
                        "summary": article.summary,
                        "text": article.text
                    })
                except: pass
        except Exception as e:
            logger.error(f"[{company}] 뉴스 수집 중 오류: {e}")
            
    # 정렬: 구글/네이버 소스 순위(original_rank)를 최우선으로 하여 브라우저 검색 결과 반영
    # original_rank가 작을수록(0, 1, 2...) 상위 노출
    news_data.sort(key=lambda x: (
        x.get('original_rank', 99),
        -(x['publish_date'].timestamp() if x['publish_date'] else 0)
    ))
            
    logger.info(f"파싱 완료된 총 기업 기사 수: {len(news_data)}")
    return news_data
