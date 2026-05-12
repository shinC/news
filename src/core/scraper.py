import logging
import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pytz
import newspaper
from newspaper.google_news import GoogleNewsSource
from config.settings import settings

logger = logging.getLogger(__name__)

def fetch_google_news_rss(query: str, hl: str = 'en-US', gl: str = 'US', ceid: str = 'US:en', max_results: int = 7) -> List[Dict[str, Any]]:
    """구글 뉴스 RSS 피드를 파싱하여 기사 목록을 반환합니다."""
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
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
    """
    logger.info(f"구글 뉴스 다중 카테고리 수집 시작 (기간: {settings.period})")
    
    all_news_data = []
    categories = settings.categories
    
    # 우선순위 키워드 구성
    base_keywords = getattr(settings, 'priority_keywords', [])
    priority_keywords = base_keywords + (dynamic_keywords if dynamic_keywords else [])
    
    # 기준 날짜 설정
    reference_date = market_date if market_date else datetime.now(pytz.utc)
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=pytz.utc)
    else:
        reference_date = reference_date.astimezone(pytz.utc)

    # 날짜 필터링 (3일)
    days = 3
    if settings.period.endswith('d'):
        try:
            days = int(settings.period[:-1])
        except: pass
    cutoff_date = reference_date - timedelta(days=days)
    upper_cutoff = reference_date + timedelta(days=1) 

    import newspaper
    config = newspaper.Config()
    config.request_timeout = 10
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

    for cat_name, query in categories.items():
        logger.info(f"카테고리 수집 중: {cat_name} (쿼리: {query})")
        rss_articles = fetch_google_news_rss(query, max_results=settings.max_results_per_section)
        
        for item in rss_articles:
            try:
                raw_url = item['url']
                url = decode_google_news_url(raw_url)
                
                article = newspaper.Article(url, language='en', config=config)
                article.download()
                article.parse()
                
                # 본문이 비어있거나 구글 뉴스 기본 문구인 경우 RSS 요약/메타 설명을 대안으로 사용
                BOILERPLATE = "Comprehensive up-to-date news coverage"
                is_boilerplate = article.text and BOILERPLATE in article.text
                
                if not article.text or len(article.text) < 50 or is_boilerplate:
                    # 1순위: RSS에서 제공하는 요약
                    if item.get('description') and BOILERPLATE not in item.get('description'):
                        article.text = item['description']
                    # 2순위: 메타 설명 (단, 구글 뉴스 URL이 아닐 때만)
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

                # 요약본 생성: 1000자 내외로 넉넉하게 추출하여 최종 AI 요약의 품질을 보장합니다.
                # nlp() 결과가 너무 짧으면 본문 앞부분을 충분히 가져옵니다.
                if article.summary and len(article.summary) > 500:
                    summary_text = article.summary
                else:
                    summary_text = article.text[:1000] if article.text else ""

                # 최종 Fallback: 요약이 비었거나 너무 짧거나 제목과 비슷한 경우
                if not summary_text or len(summary_text) < 250 or BOILERPLATE in summary_text or is_too_similar:
                    from src.core.utils import get_yahoo_summary, get_google_summary
                    
                    # 1순위 백업: 카테고리가 비즈니스/경제 관련이면 야후 파이낸스 우선
                    if cat_name in ['Business', 'Economy', 'Finance']:
                        fallback_summary = get_yahoo_summary(title)
                    else:
                        fallback_summary = get_google_summary(title)
                    
                    # 2순위 백업: 1순위가 실패하면 다른 엔진 시도
                    if not fallback_summary or len(fallback_summary) < 150:
                        if cat_name in ['Business', 'Economy', 'Finance']:
                            fallback_summary = get_google_summary(title)
                        else:
                            fallback_summary = get_yahoo_summary(title)

                    if fallback_summary and len(fallback_summary) > len(summary_text):
                        summary_text = fallback_summary
                    elif item.get('description') and len(item['description']) > len(summary_text):
                        summary_text = item['description']
                
                # 요약문이 여전히 너무 짧거나 제목과 같으면 RSS 설명이라도 최후의 수단으로 사용
                if len(summary_text) < 150 and item.get('description'):
                    summary_text = item['description']
                
                # 요약문에서 불필요한 공백 및 '...' 등 정리
                summary_text = re.sub(r'\s+', ' ', summary_text).strip()
                # '...'으로 끝나는 경우 제목 중복일 가능성이 높으므로 한 번 더 체크
                if summary_text.endswith('...') and len(summary_text) < 200:
                    # 최후의 보루: 구글 검색 스니펫 강제 재시도
                    from src.core.utils import get_google_summary
                    fs = get_google_summary(title)
                    if fs and len(fs) > len(summary_text):
                        summary_text = fs
                
                pub_date = article.publish_date
                if not pub_date and item.get('publish_date_raw'):
                    try:
                        from dateutil import parser as date_parser
                        pub_date = date_parser.parse(item['publish_date_raw'])
                    except: pass
                
                if pub_date:
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=pytz.utc)
                    else:
                        pub_date = pub_date.astimezone(pytz.utc)
                    
                    if pub_date < cutoff_date or pub_date > upper_cutoff:
                        logger.debug(f"기간 외 기사 제외 ({pub_date}): {article.title}")
                        continue
                else:
                    if not item.get('publish_date_raw'):
                        logger.warning(f"발행일을 알 수 없는 기사 제외: {article.title}")
                        continue
                    pub_date = datetime.now(pytz.utc)

                # 우선순위 키워드 포함 여부 검사
                priority_score = 0
                text_to_check = (article.title + " " + summary_text + " " + " ".join(article.keywords)).lower()
                for keyword in priority_keywords:
                    if keyword.lower() in text_to_check:
                        priority_score += 1

                # 키워드 정리
                keywords = [k for k in article.keywords if k.lower() not in ['google', 'news', 'home']]

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

def decode_google_news_url(url: str) -> str:
    """구글 뉴스 URL을 원래의 기사 URL로 디코딩합니다."""
    if "news.google.com" not in url:
        return url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
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
        # 신규 패턴: "https://..." 형태의 문자열 검색
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
        
        # BeautifulSoup을 사용하여 <a> 태그 및 meta refresh 등 추가 검사
        soup = BeautifulSoup(res.text, 'lxml')
        
        # meta refresh check
        meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            match = re.search(r'url=(https?://[^"]+)', content, re.I)
            if match and "google.com" not in match.group(1):
                return match.group(1)
        
        # 모든 <a> 태그 중 외부 링크 검색
        for a in soup.find_all('a', href=True):
            link = a['href']
            if link.startswith('http') and "google.com" not in link:
                return link
        
        # 최후의 수단: base64 디코딩 시도 (일부 구형/특수 패턴 대응)
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
    except Exception as e:
        logger.warning(f"URL 디코딩 실패 ({url}): {e}")
        return url

def fetch_google_news_web(query: str, hl: str = 'en-US', gl: str = 'US', ceid: str = 'US:en') -> List[Dict[str, Any]]:
    """구글 뉴스 검색 페이지를 직접 스크래핑하여 기사 목록을 반환합니다."""
    import urllib.parse
    import requests
    from bs4 import BeautifulSoup
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': f'{hl},{hl.split("-")[0]};q=0.9,en;q=0.8'
    }
    
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        for item in soup.select('article'):
            link_tag = item.find('a', href=True)
            if not link_tag: continue
            
            title = link_tag.get_text().strip()
            href = link_tag['href']
            
            if href.startswith('.'):
                href = "https://news.google.com" + href[1:]
                
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

def fetch_company_news_us(companies: List[str], days: int = 3, market_date: datetime = None) -> List[Dict[str, Any]]:
    """
    구글 뉴스 및 Yahoo Finance에서 특정 기업들에 대한 최신 기사를 수집합니다.
    """
    logger.info(f"미국 기업 뉴스 수집 시작: 대상 기업={companies}, 기간={days}일, 기준날짜={market_date}")
    news_data = []
    
    import requests
    from datetime import datetime, timedelta
    import pytz
    
    # 기준 날짜 설정
    reference_date = market_date if market_date else datetime.now(pytz.utc)
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=pytz.utc)
    else:
        reference_date = reference_date.astimezone(pytz.utc)
        
    cutoff_date = reference_date - timedelta(days=days)

    for company in companies:
        logger.info(f"[{company}] 뉴스 검색 중...")
        try:
            import yfinance as yf
            from gnews import GNews
            
            ticker_obj = yf.Ticker(company)
            
            # 티커에서 회사 풀네임 가져오기 (예: "Apple Inc." -> "Apple")
            company_full_name = company
            try:
                info = ticker_obj.info
                if 'shortName' in info:
                    company_full_name = info['shortName'].split(',')[0].split(' Inc')[0].split(' Corp')[0].split(' Ltd')[0].strip()
            except Exception:
                pass

            # 후보 기사 수집 (Source 1: yfinance)
            yf_news = ticker_obj.news
            
            # 기사 통합 및 중복 제거 (URL 및 제목 기준)
            candidates = {} # {url: {title, summary, pub_date, source}}
            seen_titles = set()
            
            def normalize_title(t):
                import re
                t = t.lower()
                t = re.sub(r' - .+$', '', t) 
                t = re.sub(r'[^a-z0-9가-힣]', '', t)
                return t

            # Source 1: Google News Search (RSS version of web search)
            # 직접적인 웹 스크래핑이 차단되는 환경이므로, 브라우저 결과와 가장 유사한 RSS 검색을 최우선으로 사용합니다.
            logger.info(f"Source 1: Fetching Google News Search for {company_full_name}...")
            google_news_client = GNews(language='en', country='US', period=f'{days}d', max_results=20)
            for q in [company_full_name, f"{company_full_name} stock"]:
                gn_news = google_news_client.get_news(q)
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

            # Source 2: Yahoo Finance
            logger.info(f"Source 2: Fetching yfinance news for {company}...")
            for item in yf_news:
                content = item.get('content', {})
                if not content: continue
                url = content.get('canonicalUrl', {}).get('url', '') or content.get('clickThroughUrl', {}).get('url', '')
                if not url: continue
                if url in candidates: continue
                
                title = content.get('title', '')
                norm_title = normalize_title(title)
                if norm_title in seen_titles: continue
                
                pub_date = None
                pub_date_str = content.get('pubDate', '')
                if pub_date_str:
                    try:
                        pub_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    except: pass
                
                candidates[url] = {
                    "title": title,
                    "summary": content.get('summary', ''),
                    "pub_date": pub_date,
                    "source": "yahoo",
                    "original_rank": len(candidates) + 50
                }
                seen_titles.add(norm_title)
            

            # 수집된 후보 기사 처리
            # 중복 제목을 다시 한 번 체크 (URL 디코딩 후에도 발생 가능)
            final_seen_titles = set()
            for url, info in candidates.items():
                try:
                    pub_date = info['pub_date']
                    if pub_date and pub_date < cutoff_date:
                        continue
                        
                    # 본문 검증을 위해 기사 다운로드
                    config = newspaper.Config()
                    config.request_timeout = 10
                    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
                    article = newspaper.Article(url, language='en', config=config)
                    
                    original_title = info['title']
                    title = original_title
                    text = info['summary']
                    summary = text
                    keywords = []
                    authors = []
                    
                    try:
                        article.download()
                        article.parse()
                        article.nlp()
                        
                        # 범용적인 제목(MSN, Google News, Home 등)으로 덮어씌워지는 것 방지
                        new_title = article.title
                        junk_titles = ["MSN", "Google News", "Home", "AOL.com", "Yahoo Finance", "Business", "News"]
                        is_junk = any(jt.lower() == new_title.strip().lower() for jt in junk_titles) or len(new_title or "") < 10
                        
                        if new_title and not is_junk:
                            title = new_title
                        
                        text = article.text if article.text else text
                        
                        # 본문이 비어있거나 구글 뉴스 기본 문구인 경우 요약 정보로 대체
                        BOILERPLATE = "Comprehensive up-to-date news coverage"
                        if not text or len(text) < 50 or BOILERPLATE in text:
                            text = info['summary']
                        
                        summary = article.summary if (article.summary and len(article.summary) > 500) else article.text[:1000] if article.text else summary
                        
                        # 보완: 요약이 여전히 너무 짧거나 제목과 비슷하면 검색 엔진을 통해 보강
                        title_words = set(re.sub(r'[^\w\s]', ' ', title).lower().split())
                        summary_words = set(re.sub(r'[^\w\s]', ' ', summary or "").lower().split())
                        common_words = title_words.intersection(summary_words)
                        
                        # 제목 단어의 80% 이상이 포함되면서 요약이 250자 미만인 경우 "제목 중복"으로 간주
                        is_too_similar = len(common_words) > len(title_words) * 0.8 and len(summary or "") < 250

                        if not summary or len(summary) < 250 or BOILERPLATE in summary or is_too_similar:
                            from src.core.utils import get_yahoo_summary, get_google_summary
                            # 기업 뉴스는 야후 파이낸스 우선
                            fallback_summary = get_yahoo_summary(title)
                            if not fallback_summary or len(fallback_summary) < 150:
                                fallback_summary = get_google_summary(title)
                                
                            if fallback_summary and len(fallback_summary) > len(summary or ""):
                                summary = fallback_summary
                            else:
                                summary = info['summary']
                        
                        # 요약문 최종 정리
                        if summary:
                            summary = re.sub(r'\s+', ' ', summary).strip()
                            
                        keywords = article.keywords
                        authors = article.authors
                    except Exception as e:
                        logger.debug(f"기사 본문 다운로드 실패 ({url}), 요약 정보로 대체: {e}")
                    
                    if not title or not text: continue
                    
                    norm_title = normalize_title(title)
                    if norm_title in final_seen_titles: continue
                    
                    # 티커 또는 회사명이 제목/본문에 있는지 검증 (정확성 향상)
                    import re
                    def get_match_info(target_text, ticker_str, name_str):
                        if not target_text: return False, False
                        target_text = target_text.lower()
                        ticker_str = ticker_str.lower()
                        name_str = name_str.lower()
                        
                        # 인텔(INTC) 전용 노이즈 필터링
                        if ticker_str == "intc" or "intel" in name_str:
                            noise_patterns = [
                                r'state intel', r'military intel', r'human intel', 
                                r'signal intel', r'security intel', r'intel agency',
                                r'intel official', r'counter-intel', r'defense intel',
                                r'intelligence' # 'intel'은 intelligence의 줄임말로 자주 쓰임
                            ]
                            for pattern in noise_patterns:
                                if re.search(pattern, target_text) and not re.search(r'\bintel corp', target_text):
                                    return False, False

                        # 단어 경계(\b)를 사용하여 정확한 티커 또는 회사명 매칭
                        ticker_match = re.search(rf'\b{re.escape(ticker_str)}\b', target_text)
                        # 핵심 단어 매칭 (예: Intel)
                        core_match = name_str in target_text
                        
                        is_matched = bool(ticker_match or core_match)
                        return True, is_matched

                    # 제목 매칭 여부 (가중치 부여)
                    _, title_matched = get_match_info(title, company, company_full_name)
                    # 본문 매칭 여부
                    _, text_matched = get_match_info(text, company, company_full_name)
                    
                    if not title_matched and not text_matched:
                        logger.debug(f"[{company}] 필터링 제외 (Title Match: {title_matched}, Text Match: {text_matched}): {title}")
                        continue
                    
                    final_seen_titles.add(norm_title)
                    
                    # 제목에 키워드가 있으면 가중치 1, 본문에만 있으면 0
                    relevance_score = 1 if title_matched else 0
                    
                    data = {
                        "company": company,
                        "title": title,
                        "url": url,
                        "publish_date": pub_date,
                        "relevance_score": relevance_score,
                        "original_rank": info.get('original_rank', 999),
                        "authors": authors,
                        "summary": summary,
                        "text": text,
                        "keywords": keywords,
                    }
                    news_data.append(data)
                except Exception as e:
                    logger.error(f"기사 파싱 실패 ({url}): {e}")
        except Exception as e:
            logger.error(f"[{company}] 뉴스 수집 실패: {e}")
            
    # 정렬: 구글/야후 소위 순위(original_rank)를 최우선으로 하여 브라우저 검색 결과 반영
    # original_rank가 작을수록(0, 1, 2...) 상위 노출
    news_data.sort(key=lambda x: (
        x.get('original_rank', 999),
        -(x['publish_date'].timestamp() if x['publish_date'] else 0)
    ))
            
    logger.info(f"파싱 완료된 총 기업 기사 수: {len(news_data)}")
    return news_data
