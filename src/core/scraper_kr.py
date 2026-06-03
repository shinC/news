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
    try:
        from googlenewsdecoder import new_decoderv1
        dec = new_decoderv1(url)
        if dec.get('status'):
            return dec.get('decoded_url')
    except Exception as e:
        logger.error(f"Error decoding Google News URL: {e}")
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
    설정된 여러 카테고리에 대해 구글 뉴스 RSS 및 연합인포맥스 RSS 매크로 뉴스에서 최신 기사를 수집합니다.
    """
    logger.info(f"뉴스 다중 수집 시작 (한국, 기간: {settings_kr.period})")
    
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
 
    # [사용자 요청] 네이버 주요뉴스 헤드라인 수집 비활성화
    """
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
    """
 
    # 0-2. 연합인포맥스 RSS 매크로 뉴스 수집
    logger.info("연합인포맥스 RSS 매크로 뉴스 수집 시작")
    try:
        for feed in getattr(settings_kr, "macro_rss_feeds", []):
            feed_url = feed.get("url")
            keywords = feed.get("keywords", [])
            if not feed_url: continue
            
            res = requests.get(feed_url, timeout=10)
            res.raise_for_status()
            rss_soup = BeautifulSoup(res.text, 'xml')
            
            macro_count = 0
            for item in rss_soup.find_all('item'):
                if macro_count >= 3:
                    break
                title = item.title.text if item.title else ""
                description = item.description.text if item.description else ""
                link = item.link.text if item.link else ""
                
                # 키워드 매칭 검증
                matched = False
                for kw in keywords:
                    if kw in title or kw in description:
                        matched = True
                        break
                
                if matched and link:
                    try:
                        article = newspaper.Article(link, language='ko', config=config)
                        article.download()
                        article.parse()
                        article.nlp()
                        
                        summary_text = article.summary if (article.summary and len(article.summary) > 200) else article.text[:1000] if article.text else description
                        
                        # 발행일 파싱
                        pub_date = None
                        if item.pubDate:
                            try:
                                # 예: 2026-05-27 14:25:15
                                pub_date = datetime.strptime(item.pubDate.text.strip(), '%Y-%m-%d %H:%M:%S')
                                pub_date = kst.localize(pub_date)
                            except:
                                try:
                                    from dateutil import parser as date_parser
                                    pub_date = date_parser.parse(item.pubDate.text.strip())
                                    if pub_date.tzinfo is None:
                                        pub_date = kst.localize(pub_date)
                                    else:
                                        pub_date = pub_date.astimezone(kst)
                                except: pass
                            
                        if not pub_date:
                            pub_date = article.publish_date or datetime.now(kst)
                            if pub_date.tzinfo is None:
                                pub_date = kst.localize(pub_date)
                            else:
                                pub_date = pub_date.astimezone(kst)
                        
                        # 기간 필터링
                        if pub_date < cutoff_date or pub_date > upper_cutoff:
                            continue
                            
                        # 우선순위 스코어
                        priority_score = 0
                        text_to_check = (title + " " + summary_text + " " + " ".join(article.keywords if isinstance(article.keywords, list) else [])).lower()
                        for keyword in priority_keywords:
                            if keyword.lower() in text_to_check:
                                priority_score += 1
                                
                        all_news_data.append({
                            "category": "Macro & Market",
                            "title": title,
                            "url": link,
                            "publish_date": pub_date,
                            "authors": article.authors,
                            "summary": summary_text,
                            "text": article.text or description,
                            "keywords": article.keywords if isinstance(article.keywords, list) else [],
                            "priority_score": priority_score
                        })
                        macro_count += 1
                    except Exception as parse_err:
                        logger.error(f"연합인포맥스 매크로 기사 파싱 실패 ({link}): {parse_err}")
    except Exception as e:
        logger.error(f"연합인포맥스 RSS 매크로 뉴스 수집 전체 실패: {e}")

    # [사용자 요청] 구글 카테고리 뉴스 수집 비활성화
    """
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
                
                # 구글 카테고리 뉴스: 본문 스크래핑 생략 (다이어트 로직)
                title = item.get('title', '')
                summary_text = item.get('description', '')
                if not summary_text:
                    summary_text = title
                    
                pub_date = None
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
                        logger.debug(f"기간 외 기사 제외 ({pub_date}): {title}")
                        continue
                else:
                    # 발행일을 알 수 없는 경우 RSS 날짜가 있다면 건너뛰지 않음
                    if not item.get('publish_date_raw'):
                        logger.warning(f"발행일을 알 수 없는 기사 제외: {title}")
                        continue
                    # RSS 날짜라도 없으면 어쩔 수 없이 대략적인 현재 시간 사용 (필요시)
                    pub_date = datetime.now(kst)
 
                # 우선순위 키워드 포함 여부 검사
                priority_score = 0
                text_to_check = (title + " " + summary_text).lower()
                for keyword in priority_keywords:
                    if keyword.lower() in text_to_check:
                        priority_score += 1
 
                all_news_data.append({
                    "category": cat_name,
                    "title": title,
                    "url": url,
                    "publish_date": pub_date,
                    "authors": [],
                    "summary": summary_text,
                    "text": summary_text, # 본문 없이 요약만
                    "keywords": [],
                    "priority_score": priority_score
                })
            except Exception as e:
                logger.error(f"기사 파싱 실패 ({item['url']}): {e}")
    """
                
    logger.info(f"총 {len(all_news_data)}개의 기사가 수집되었습니다.")
    return all_news_data

# [기존 네이버 뉴스 수집 로직 보관]
# def fetch_news_naver_legacy(dynamic_keywords: List[str] = None, market_date: datetime = None) -> List[Dict[str, Any]]:
#     sections = settings_kr.naver_finance_sections
#     ...

def fetch_company_news_kr(companies: List[str], days: int = 3) -> List[Dict[str, Any]]:
    """
    네이버 모바일 뉴스 검색에서 "특징주 '종목명'" 패턴으로 검색하여 상위 5개 기사의 원본 URL과 제목을 수집합니다.
    """
    logger.info(f"한국 특징주 뉴스 수집 시작: 대상 기업={companies}")
    news_data = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://m.naver.com/'
    }
    
    for company in companies:
        logger.info(f"[{company}] 특징주 검색 중 (Naver Mobile)...")
        try:
            query = f"특징주 {company}"
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://m.search.naver.com/search.naver?where=m_news&query={encoded_query}&sort=1"
            res = requests.get(search_url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'lxml')
            
            seen_urls = set()
            seen_titles = set()
            company_articles = []
            
            kst = pytz.timezone('Asia/Seoul')
            now = datetime.now(kst)
            cutoff_date = now - timedelta(days=days)
            
            # 모든 a 태그를 순회하면서 특징주와 회사명이 들어간 제목 수집
            for a in soup.find_all('a', href=True):
                url = a['href']
                title = a.get_text().strip()
                
                if not url.startswith('http'):
                    continue
                    
                # 특징주 키워드와 회사명이 모두 제목에 들어있는 경우 (본문 요약(Snippet) 방지를 위해 길이 90자 제한 추가)
                if '특징주' in title and company in title and 10 < len(title) < 90:
                    pub_date = None
                    
                    # 제목 태그(a)에서부터 상위로 올라가며 날짜 텍스트가 포함된 가장 가까운 컨테이너를 찾음
                    container = a
                    raw_title = title
                    import re
                    while container and container.name != 'body':
                        text = container.get_text()
                        if re.search(r'\d+[분시간일]\s*전|\d{4}\.\d{2}\.\d{2}', text):
                            raw_title = text
                            break
                        container = container.parent
                    
                    # 날짜 파싱
                    match_min = re.search(r'(\d+)분\s*전', raw_title)
                    match_hour = re.search(r'(\d+)시간\s*전', raw_title)
                    match_day = re.search(r'(\d+)일\s*전', raw_title)
                    match_date = re.search(r'(\d{4}\.\d{2}\.\d{2})\.?', raw_title)
                    match_short_date = re.search(r'(\d{2}\.\d{2})\.?', raw_title)
                    
                    if match_min:
                        pub_date = now - timedelta(minutes=int(match_min.group(1)))
                    elif match_hour:
                        pub_date = now - timedelta(hours=int(match_hour.group(1)))
                    elif match_day:
                        pub_date = now - timedelta(days=int(match_day.group(1)))
                    elif match_date:
                        try:
                            parsed = datetime.strptime(match_date.group(1), '%Y.%m.%d')
                            pub_date = kst.localize(parsed)
                        except: pass
                    elif match_short_date:
                        try:
                            parsed = datetime.strptime(f"{now.year}.{match_short_date.group(1)}", '%Y.%m.%d')
                            pub_date = kst.localize(parsed)
                        except: pass
                        
                    # 미래 날짜로 파싱된 경우 (숫자 오인식 등) 초기화하여 newspaper로 Fallback
                    if pub_date and pub_date > now + timedelta(hours=24):
                        pub_date = None
                        
                    if not pub_date:
                        try:
                            import newspaper
                            config = newspaper.Config()
                            config.request_timeout = 5
                            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
                            article = newspaper.Article(url, language='ko', config=config)
                            article.download()
                            article.parse()
                            if article.publish_date:
                                pub_date = article.publish_date
                                if pub_date.tzinfo is None:
                                    pub_date = kst.localize(pub_date)
                                else:
                                    pub_date = pub_date.astimezone(kst)
                        except: pass
                    
                    if pub_date and pub_date < cutoff_date:
                        continue

                    # 조선비즈5시간 전네이버뉴스 같은 메타텍스트가 뒤에 붙는 경우가 많으므로 정제 시도
                    # "네이버뉴스" 제거
                    if title.endswith("네이버뉴스"):
                        title = title[:-5].strip()
                    # "...전" (시간 전, 일 전, 분 전) 패턴이 붙어 있다면 그 부분과 앞의 언론사명 제거
                    # 보통 제목 뒤에 '언론사명N시간 전' 형태로 붙음
                    meta_patterns = [r'[가-힣\w\s]+?\d+?시간\s*전$', r'[가-힣\w\s]+?\d+?일\s*전$', r'[가-힣\w\s]+?\d+?분\s*전$', r'[가-힣\w\s]+?\d{4}\.\d{2}\.\d{2}\.?$', r'[가-힣\w\s]+?\d{2}\.\d{2}\.?$']
                    for pattern in meta_patterns:
                        match = re.search(pattern, title)
                        if match:
                            title = title[:match.start()].strip()
                            break
                    
                    norm_title = title.replace(" ", "")
                    if url not in seen_urls and norm_title not in seen_titles:
                        
                        # 네이버 뉴스 링크인 경우 기사원문(원본 URL) 추출 시도
                        if "news.naver.com" in url:
                            try:
                                res_n = requests.get(url, headers=headers, timeout=5)
                                soup_n = BeautifulSoup(res_n.text, 'lxml')
                                origin_link = soup_n.select_one('a.media_end_head_origin_link')
                                if origin_link and origin_link.get('href'):
                                    url = origin_link.get('href')
                            except Exception as e:
                                pass

                        seen_urls.add(url)
                        seen_titles.add(norm_title)
                        company_articles.append({
                            "company": company,
                            "title": title,
                            "url": url,
                            "summary": title,
                            "text": title,
                            "publish_date": pub_date,
                            "priority_score": 0,
                            "original_rank": len(company_articles)
                        })
                        if len(company_articles) >= 5:
                            break
                            
            logger.info(f"[{company}] 특징주 뉴스 수집 완료: {len(company_articles)}개")
            news_data.extend(company_articles)
            
        except Exception as e:
            logger.error(f"[{company}] 특징주 뉴스 수집 중 오류: {e}")
            
    # 정렬: original_rank 순
    news_data.sort(key=lambda x: (
        x.get('original_rank', 99),
        -(x['publish_date'].timestamp() if x.get('publish_date') else 0)
    ))
            
    logger.info(f"수집 완료된 총 기업 특징주 기사 수: {len(news_data)}")
    return news_data
