import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pytz
import newspaper
from newspaper.google_news import GoogleNewsSource
from config.settings import settings

logger = logging.getLogger(__name__)

def fetch_news(dynamic_keywords: List[str] = None, market_date: datetime = None) -> List[Dict[str, Any]]:
    """
    구글 뉴스에서 '미국 경제/비즈니스' 카테고리의 최근 기사를 수집합니다.
    """
    logger.info(f"구글 뉴스 수집 시작: 카테고리={settings.topic}, 기간={settings.period}, 기준날짜={market_date}")
    
    # GNews 기반의 GoogleNewsSource 생성
    try:
        source = GoogleNewsSource(
            country=settings.country,
            period=settings.period,
            max_results=settings.max_results,
        )
    except Exception as e:
        logger.error(f"GoogleNewsSource 초기화 실패: {e}")
        return []

    # 'US Economy Business' 키워드로 기사 검색
    source.build(keyword="US Economy Business")
    logger.info(f"검색된 기사 수: {len(source.articles)}")
    
    # 기사 다운로드
    logger.info("기사 다운로드 시작...")
    downloaded_articles = source.download_articles()
    
    news_data = []
    
    # 합쳐진 우선순위 키워드 구성
    base_keywords = getattr(settings, 'priority_keywords', [])
    priority_keywords = base_keywords + (dynamic_keywords if dynamic_keywords else [])
    
    # 기준 날짜 설정 (market_date가 있으면 그 날을 기준으로, 없으면 현재 시간 기준)
    reference_date = market_date if market_date else datetime.now(pytz.utc)
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=pytz.utc)
    else:
        reference_date = reference_date.astimezone(pytz.utc)

    # 날짜 필터링 (설정된 period 기준)
    days = 2
    if settings.period.endswith('d'):
        try:
            days = int(settings.period[:-1])
        except: pass
    
    # 기준 날짜로부터 과거로 days만큼 필터링
    cutoff_date = reference_date - timedelta(days=days)
    # market_date가 기준일 경우, 그 날 이후의 최신 뉴스가 시황과 섞이지 않도록 상한선도 설정 가능
    upper_cutoff = reference_date + timedelta(days=1) 
    
    logger.info(f"뉴스 수집 기간 필터: {cutoff_date} ~ {upper_cutoff}")

    for article in downloaded_articles:
        try:
            article.parse()
            article.nlp()
            
            # 기사 날짜 확인 및 필터링
            pub_date = article.publish_date
            
            # 1. 날짜 추출 보완 로직 (newspaper4k가 놓친 경우 대비)
            if not pub_date:
                try:
                    # soup 등을 이용해 추가 추출 시도 가능 (현재는 기본 로직 유지)
                    pass
                except: pass

            if pub_date:
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=pytz.utc)
                else:
                    pub_date = pub_date.astimezone(pytz.utc)
                
                # 기간 외 기사 제외
                if pub_date < cutoff_date or pub_date > upper_cutoff:
                    logger.debug(f"기간 외 기사 제외 ({pub_date}): {article.title}")
                    continue
            else:
                # [고도화] 실제 날짜가 없거나 확인이 안되면 수집 금지
                logger.warning(f"발행일을 알 수 없는 기사 제외: {article.title}")
                continue

            # 우선순위 키워드 포함 여부 검사
            priority_score = 0
            text_to_check = (article.title + " " + article.summary + " " + " ".join(article.keywords)).lower()
            for keyword in priority_keywords:
                if keyword.lower() in text_to_check:
                    priority_score += 1

            data = {
                "title": article.title,
                "url": article.url,
                "publish_date": pub_date,
                "authors": article.authors,
                "summary": article.summary,
                "text": article.text,
                "keywords": article.keywords,
                "priority_score": priority_score
            }
            news_data.append(data)
        except Exception as e:
            logger.error(f"기사 파싱 실패 ({article.url}): {e}")
            
    logger.info(f"파싱 완료된 기사 수: {len(news_data)}")
    return news_data

def decode_google_news_url(url: str) -> str:
    """구글 뉴스 URL을 원래의 기사 URL로 디코딩합니다."""
    if "news.google.com" in url:
        try:
            # GNews 유틸리티 시도
            from gnews.utils import decode_google_news_url as decoder
            return decoder(url)
        except:
            try:
                import requests
                res = requests.get(url, timeout=5, allow_redirects=True)
                return res.url
            except Exception:
                return url
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
                        summary = article.summary if article.summary else summary
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
