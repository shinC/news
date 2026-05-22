import logging
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
import urllib.parse
from newspaper import Article
from config.settings import settings_kr

logger = logging.getLogger(__name__)

def decode_google_news_url(url: str) -> str:
    """구글 뉴스 URL을 원래의 기사 URL로 디코딩합니다."""
    if "news.google.com" not in url:
        return url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://news.google.com/'
    }
    
    try:
        # 1. GNews 유틸리티 시도
        try:
            from gnews.utils import decode_google_news_url as decoder
            decoded = decoder(url)
            if decoded and "news.google.com" not in decoded:
                return decoded
        except: pass
        
        # 2. 직접 요청 및 HTML 파싱
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if "news.google.com" not in res.url:
            return res.url
            
        # HTML 본문에서 실제 URL 추출 시도
        patterns = [
            r'data-url="([^"]+)"',
            r'data-n-au="([^"]+)"',
            r'window\.location\.replace\("([^"]+)"\)',
            r'url=(https?://[^&"]+)',
            r'content="0;url=(https?://[^"]+)"',
            r'\["https://[^"]+"\]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, res.text, re.I)
            if match:
                decoded_url = match.group(1 if "(" in pattern else 0).strip('[]" ')
                if "google.com" not in decoded_url:
                    return decoded_url
        
        # 모든 <a> 태그 중 외부 링크 검색
        soup = BeautifulSoup(res.text, 'lxml')
        for a in soup.find_all('a', href=True):
            link = a['href']
            if link.startswith('http') and "google.com" not in link:
                return link
        
        # 최후의 수단: base64 디코딩 시도
        if '/articles/' in url:
            import base64
            encoded = url.split('/articles/')[1].split('?')[0]
            padding = len(encoded) % 4
            if padding: encoded += '=' * (4 - padding)
            try:
                decoded_bytes = base64.urlsafe_b64decode(encoded)
                match_url = re.search(rb'https?://[^\x00-\x1f\x7f-\xff]+', decoded_bytes)
                if match_url:
                    return match_url.group(0).decode('utf-8')
            except: pass

        return res.url
    except Exception:
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

def fetch_google_news_rss(query: str = None, topic_id: str = None, hl: str = 'ko', gl: str = 'KR', ceid: str = 'KR:ko', max_results: int = 7) -> List[Dict[str, Any]]:
    """구글 뉴스 RSS 피드를 직접 파싱하여 기사 목록을 반환합니다.
    query가 있으면 검색 RSS를, topic_id가 있으면 토픽 RSS를 호출합니다.
    """
    import time
    import random
    
    # 랜덤 지연 추가 (차단 방지)
    delay = random.uniform(1.0, 2.5)
    time.sleep(delay)
    
    if topic_id:
        url = f"https://news.google.com/rss/topics/{topic_id}?hl={hl}&gl={gl}&ceid={ceid}"
    elif query:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    else:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'xml')
        
        items = soup.find_all('item')
        for item in items[:max_results]:
            # description에서 HTML 태그 제거하여 순수 텍스트 요약 추출
            raw_desc = item.description.text if item.description else ""
            desc_soup = BeautifulSoup(raw_desc, 'html.parser')
            clean_desc = desc_soup.get_text(separator=' ', strip=True)
            
            articles.append({
                "title": item.title.text,
                "url": item.link.text,
                "description": clean_desc,
                "publish_date_raw": item.pubDate.text,
                "source": "google_rss"
            })
    except Exception as e:
        logger.error(f"Google News RSS Error ({query}): {e}")
        
    return articles

def fetch_news(dynamic_keywords: List[str] = None, market_date: datetime = None) -> List[Dict[str, Any]]:
    """
    설정된 여러 카테고리에 대해 구글 뉴스 RSS에서 최신 기사를 수집합니다.
    (기존 네이버 증권 뉴스 수집은 주석 처리되었습니다.)
    """
    logger.info(f"구글 뉴스 다중 카테고리 수집 시작 (한국, 기간: {settings_kr.period})")
    
    all_news_data = []
    categories = settings_kr.categories
    
    # 우선순위 키워드 구성
    base_keywords = getattr(settings_kr, 'priority_keywords', [])
    priority_keywords = base_keywords + (dynamic_keywords if dynamic_keywords else [])
    
    # 기준 날짜 설정 (한국 시간 KST 기준)
    kst = pytz.timezone('Asia/Seoul')
    reference_date = market_date if market_date else datetime.now(kst)
    if reference_date.tzinfo is None:
        reference_date = kst.localize(reference_date)
    else:
        reference_date = reference_date.astimezone(kst)

    # 날짜 필터링 (3일)
    days = 3
    if settings_kr.period.endswith('d'):
        try:
            days = int(settings_kr.period[:-1])
        except: pass
    cutoff_date = reference_date - timedelta(days=days)
    upper_cutoff = reference_date + timedelta(days=1) 

    import newspaper
    config = newspaper.Config()
    config.request_timeout = 10
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

    # 0. 네이버 주요뉴스 헤드라인 수집
    try:
        logger.info("네이버 주요뉴스 헤드라인 수집 시작")
        res = requests.get('https://finance.naver.com/news/mainnews.naver', timeout=10)
        soup = BeautifulSoup(res.text, 'lxml')
        main_news_links = soup.select('li.block1 dd.articleSubject a')[:settings_kr.max_results_per_section]
        for a in main_news_links:
            try:
                title = a.text.strip()
                url = 'https://finance.naver.com' + a['href']
                
                article = newspaper.Article(url, language='ko', config=config)
                article.download()
                article.parse()
                article.nlp()
                
                summary_text = article.summary if (article.summary and len(article.summary) > 500) else article.text[:1000] if article.text else ""
                
                pub_date = article.publish_date or datetime.now(kst)
                if pub_date.tzinfo is None:
                    pub_date = kst.localize(pub_date)
                else:
                    pub_date = pub_date.astimezone(kst)
                
                # 우선순위 부여 로직
                priority_score = 1
                text_to_check = (title + " " + summary_text + " " + " ".join(article.keywords if isinstance(article.keywords, list) else [])).lower()
                for keyword in priority_keywords:
                    if keyword.lower() in text_to_check:
                        priority_score += 1
                        
                keywords = article.keywords
                if not isinstance(keywords, list):
                    keywords = []
                filtered_keywords = [k for k in keywords if isinstance(k, str) and k.lower() not in ['google', 'news', 'home']]
                
                all_news_data.append({
                    "category": "주요뉴스",
                    "title": title,
                    "url": url,
                    "publish_date": pub_date,
                    "authors": article.authors,
                    "summary": summary_text,
                    "text": article.text,
                    "keywords": filtered_keywords,
                    "priority_score": priority_score
                })
            except Exception as e:
                logger.error(f"주요뉴스 파싱 실패 ({url}): {e}")
    except Exception as e:
        logger.error(f"네이버 주요뉴스 수집 전체 실패: {e}")


    for cat_name, query_or_topic in categories.items():
        if query_or_topic.startswith("CAAq"):
            logger.info(f"카테고리 수집 중: {cat_name} (토픽 ID: {query_or_topic})")
            rss_articles = fetch_google_news_rss(topic_id=query_or_topic, max_results=settings_kr.max_results_per_section)
        else:
            logger.info(f"카테고리 수집 중: {cat_name} (쿼리: {query_or_topic})")
            rss_articles = fetch_google_news_rss(query=query_or_topic, max_results=settings_kr.max_results_per_section)
        
        for item in rss_articles:
            try:
                raw_url = item['url']
                url = decode_google_news_url(raw_url)
                
                article = newspaper.Article(url, language='ko', config=config)
                article.download()
                article.parse()
                
                # 본문이 비어있거나 구글 뉴스 기본 문구인 경우 RSS 요약/메타 설명을 대안으로 사용
                BOILERPLATE = "Comprehensive up-to-date news coverage"
                is_boilerplate = article.text and BOILERPLATE in article.text
                
                if not article.text or len(article.text) < 30 or is_boilerplate:
                    from src.core.utils import get_naver_api_summary
                    api_summary = get_naver_api_summary(item['title'])
                    
                    if api_summary:
                        article.text = api_summary
                    elif item.get('description') and BOILERPLATE not in item.get('description'):
                        article.text = item['description']
                    elif "news.google.com" not in url:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(article.html, 'lxml')
                        meta_desc = soup.find('meta', attrs={'name': 'description'}) or \
                                    soup.find('meta', attrs={'property': 'og:description'}) or \
                                    soup.find('meta', attrs={'name': 'twitter:description'})
                        if meta_desc:
                            article.text = meta_desc.get('content', '')
                
                article.nlp()
                
                # RSS 제목을 우선 사용
                title = item.get('title', article.title)
                junk_titles = ["MSN", "Google News", "Home", "AOL.com", "Yahoo Finance", "Business", "News"]
                if any(jt.lower() == (title or "").strip().lower() for jt in junk_titles) or len(title or "") < 10:
                    title = item.get('title')
                
                # 요약문 생성 로직 개선: 500자 제한을 없애고 품질 기반으로 선택
                summary_text = ""
                
                # 1단계: newspaper4k NLP 요약문 검증
                if article.summary and len(article.summary.strip()) > 100:
                    # 제목과 너무 비슷한지 체크
                    title_words = set(re.sub(r'[^\w\s]', ' ', title).split())
                    summary_words = set(re.sub(r'[^\w\s]', ' ', article.summary).split())
                    common_words = title_words.intersection(summary_words)
                    is_too_similar = len(common_words) > len(title_words) * 0.7 and len(article.summary) < 200
                    
                    if not is_too_similar:
                        summary_text = article.summary
                
                # 2단계: NLP 요약이 부실하면 본문 앞부분 또는 RSS 설명 사용
                if not summary_text or len(summary_text) < 200:
                    rss_desc = item.get('description', '')
                    if len(rss_desc) > len(summary_text) and BOILERPLATE not in rss_desc:
                        summary_text = rss_desc
                        
                    if (not summary_text or len(summary_text) < 150) and article.text and len(article.text) > 200:
                        summary_text = article.text[:1000]

                # 3단계: 최종 Fallback (요약이 부실한 경우 네이버 검색 요약 활용)
                title_words_final = set(re.sub(r'[^\w\s]', ' ', title).split())
                summary_words_final = set(re.sub(r'[^\w\s]', ' ', summary_text or "").split())
                is_too_similar = len(title_words_final.intersection(summary_words_final)) > len(title_words_final) * 0.7 and len(summary_text or "") < 200
                
                if not summary_text or len(summary_text) < 200 or BOILERPLATE in summary_text or is_too_similar:
                    from src.core.utils import get_naver_summary
                    fallback_summary = get_naver_summary(title)
                    if fallback_summary and len(fallback_summary) > len(summary_text or ""):
                        summary_text = fallback_summary
                
                pub_date = article.publish_date
                if not pub_date and item.get('publish_date_raw'):
                    try:
                        from dateutil import parser as date_parser
                        pub_date = date_parser.parse(item['publish_date_raw']).astimezone(kst)
                    except: pass
                
                if pub_date:
                    if pub_date.tzinfo is None:
                        pub_date = kst.localize(pub_date)
                    else:
                        pub_date = pub_date.astimezone(kst)
                    
                    if pub_date < cutoff_date or pub_date > upper_cutoff:
                        logger.debug(f"기간 외 기사 제외 ({pub_date}): {article.title}")
                        continue
                else:
                    # 발행일을 알 수 없는 경우 RSS 날짜가 있다면 건너뛰지 않음
                    if not item.get('publish_date_raw'):
                        logger.warning(f"발행일을 알 수 없는 기사 제외: {article.title}")
                        continue
                    # RSS 날짜라도 없으면 어쩔 수 없이 대략적인 현재 시간 사용 (필요시)
                    pub_date = datetime.now(kst)

                # 우선순위 키워드 포함 여부 검사
                priority_score = 0
                text_to_check = (title + " " + summary_text + " " + " ".join(article.keywords)).lower()
                for keyword in priority_keywords:
                    if keyword.lower() in text_to_check:
                        priority_score += 1

                # 키워드 정리
                keywords = article.keywords
                if not isinstance(keywords, list):
                    keywords = []
                filtered_keywords = [k for k in keywords if isinstance(k, str) and k.lower() not in ['google', 'news', 'home']]

                all_news_data.append({
                    "category": cat_name,
                    "title": title,
                    "url": url,
                    "publish_date": pub_date,
                    "authors": article.authors,
                    "summary": summary_text,
                    "text": article.text,
                    "keywords": keywords,
                    "priority_score": priority_score
                })
            except Exception as e:
                logger.error(f"기사 파싱 실패 ({item['url']}): {e}")
                
    logger.info(f"총 {len(all_news_data)}개의 기사가 수집되었습니다.")
    return all_news_data

# [기존 네이버 뉴스 수집 로직 보관]
# def fetch_news_naver_legacy(dynamic_keywords: List[str] = None, market_date: datetime = None) -> List[Dict[str, Any]]:
#     sections = settings_kr.naver_finance_sections
#     ...

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
            # Source 1: Google News Search (Direct RSS)
            logger.info(f"Source 1: Fetching Google News Search for {company}...")
            gn_news = fetch_google_news_rss(query=company, max_results=20)
            
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
                    
                    # 본문이 비어있거나 구글 뉴스 기본 문구인 경우 요약 정보로 대체
                    BOILERPLATE = "Comprehensive up-to-date news coverage"
                    if not text or len(text) < 50 or BOILERPLATE in text:
                        text = info['summary']
                    
                    summary = article.summary if (article.summary and len(article.summary) > 500) else article.text[:1000] if article.text else info['summary']
                    
                    # 보완: 요약이 여전히 너무 짧거나 제목과 비슷하면 네이버 검색을 통해 보강
                    title_words = set(re.sub(r'[^\w\s]', ' ', title).split())
                    summary_words = set(re.sub(r'[^\w\s]', ' ', summary or "").split())
                    common_words = title_words.intersection(summary_words)
                    is_too_similar = len(common_words) > len(title_words) * 0.7 and len(summary or "") < 200

                    if not summary or len(summary) < 200 or BOILERPLATE in summary or is_too_similar:
                        from src.core.utils import get_naver_summary
                        fallback_summary = get_naver_summary(title)
                        if fallback_summary and len(fallback_summary) > len(summary or ""):
                            summary = fallback_summary
                        else:
                            summary = info['summary']
                    
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
