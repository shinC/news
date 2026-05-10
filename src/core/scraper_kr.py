import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse
from newspaper import Article
from config.settings import settings_kr

logger = logging.getLogger(__name__)

def fetch_news(dynamic_keywords: List[str] = None) -> List[Dict[str, Any]]:
    """
    네이버 증권 뉴스의 주요 섹션들을 스크래핑한 뒤,
    newspaper4k를 이용해 본문을 파싱하고 키워드 가중치를 적용합니다.
    """
    sections = settings_kr.naver_finance_sections
    logger.info(f"네이버 증권 뉴스 수집 시작: 대상 섹션 {len(sections)}개")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    # 각 섹션별로 기사를 수집하여 category 태그를 붙입니다.
    raw_articles = []
    
    # 섹션별 최대 수집 개수 (전체 개수를 섹션 수로 나눔)
    num_sections = len(sections)
    target_per_section = settings_kr.max_results // num_sections
    
    for category, base_url in sections.items():
        logger.info(f"섹션 수집 중: {category} ({base_url})")
        section_urls = []
        try:
            res = requests.get(base_url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'lxml')
            
            # 네이버 증권 뉴스 링크 패턴 추출 개선
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
            
            logger.info(f"  - {category} 섹션에서 {len(section_urls)}개 URL 발견")
            for url in section_urls:
                raw_articles.append({"url": url, "category": category})
                
        except Exception as e:
            logger.error(f"네이버 증권 뉴스 URL 수집 실패 ({category}: {base_url}): {e}")
 
    logger.info(f"네이버 증권 뉴스 URL 총 {len(raw_articles)}건 수집 완료")
 
    logger.info("기사 다운로드 및 파싱 시작...")
    news_data = []
    
    # 합쳐진 우선순위 키워드 구성
    base_keywords = getattr(settings_kr, 'priority_keywords', [])
    priority_keywords = base_keywords + (dynamic_keywords if dynamic_keywords else [])
    logger.info(f"총 {len(priority_keywords)}개의 키워드로 우선순위 분석을 진행합니다.")
    
    import newspaper
    config = newspaper.Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    config.request_timeout = 10
    
    for item in raw_articles:
        url = item['url']
        category = item['category']
        try:
            logger.info(f"기사 다운로드 중: {url}")
            article = Article(url, language='ko', config=config)
            article.download()
            article.parse()
            article.nlp() 
            
            # 발행일시 추출 보완 (네이버 뉴스의 경우 newspaper4k가 놓치는 경우가 많음)
            publish_date = article.publish_date
            if not publish_date and 'naver.com' in url:
                try:
                    import pandas as pd
                    soup_article = BeautifulSoup(article.html, 'lxml')
                    
                    # 1. Naver mnews 전용 속성 (data-date-time)
                    date_span = soup_article.find('span', {'data-date-time': True})
                    if date_span:
                        publish_date = pd.to_datetime(date_span.get('data-date-time'))
                    else:
                        # 2. 기타 변형 속성 (data-published-time)
                        pub_span = soup_article.find('span', {'data-published-time': True})
                        if pub_span:
                            publish_date = pd.to_datetime(pub_span.get('data-published-time'))
                        else:
                            # 3. Meta tag (article:published_time)
                            meta_date = soup_article.find('meta', property='article:published_time')
                            if meta_date and meta_date.get('content'):
                                publish_date = pd.to_datetime(meta_date.get('content'))
                except Exception as de:
                    logger.warning(f"네이버 날짜 추출 실패 ({url}): {de}")
            
            priority_score = 0
            text_to_check = (article.title + " " + article.summary + " " + " ".join(article.keywords)).lower()
            
            for keyword in priority_keywords:
                if keyword.lower() in text_to_check:
                    priority_score += 1
            
            from datetime import datetime, timedelta
            import pytz
            
            # 날짜 필터링 (설정된 period 기준)
            days = 2
            if settings_kr.period.endswith('d'):
                try:
                    days = int(settings_kr.period[:-1])
                except: pass
            
            # 한국 시간(KST) 기준으로 계산
            kst = pytz.timezone('Asia/Seoul')
            cutoff_date = datetime.now(kst) - timedelta(days=days)
            
            if publish_date:
                # timezone이 없는 경우 KST로 가정
                if publish_date.tzinfo is None:
                    publish_date = kst.localize(publish_date)
                else:
                    publish_date = publish_date.astimezone(kst)
                
                if publish_date < cutoff_date:
                    logger.info(f"오래된 한국 기사 제외 ({publish_date}): {article.title}")
                    continue
            else:
                # 날짜 정보가 없는 경우 최신성 보장을 위해 제외 (필요시 포함으로 변경 가능)
                logger.warning(f"발행일을 알 수 없는 한국 기사 제외: {article.title}")
                continue

            data = {
                "title": article.title,
                "url": url,
                "category": category,  # 카테고리 정보 보존
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
    네이버 뉴스 검색을 통해 특정 기업들에 대한 최신 기사를 수집합니다.
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
    
    from datetime import datetime, timedelta
    import pytz
    kst = pytz.timezone('Asia/Seoul')
    cutoff_date = datetime.now(kst) - timedelta(days=days)
    
    for company in companies:
        logger.info(f"[{company}] 네이버 뉴스 검색 중...")
        try:
            encoded_query = urllib.parse.quote(company)
            urls = []
            
            # 5페이지(약 50개 기사)까지 수집 (관련순의 경우 과거 기사가 많을 수 있으므로 풀을 더 늘림)
            for page in range(1, 6):
                start = (page - 1) * 10 + 1
                # sort=0: 관련도순, sort=1: 최신순
                search_url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sort=0&start={start}"
                res = requests.get(search_url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'lxml')
                
                links = soup.select('a')
                for a in links:
                    href = a.get('href', '')
                    if 'n.news.naver.com' in href:
                        urls.append(href)
            
            urls = list(set(urls)) # 중복 제거
            logger.info(f"[{company}] 네이버 뉴스 링크 {len(urls)}개 수집됨")
            
            for url in urls:
                try:
                    article = Article(url, language='ko', config=config)
                    article.download()
                    article.parse()
                    article.nlp()
                    
                    publish_date = article.publish_date
                    if not publish_date:
                        try:
                            import pandas as pd
                            soup_article = BeautifulSoup(article.html, 'lxml')
                            date_span = soup_article.find('span', {'data-date-time': True})
                            if date_span:
                                publish_date = pd.to_datetime(date_span.get('data-date-time'))
                            else:
                                meta_date = soup_article.find('meta', property='article:published_time')
                                if meta_date and meta_date.get('content'):
                                    publish_date = pd.to_datetime(meta_date.get('content'))
                        except: pass
                    
                    if publish_date:
                        if publish_date.tzinfo is None:
                            publish_date = kst.localize(publish_date)
                        else:
                            publish_date = publish_date.astimezone(kst)
                            
                    if publish_date < cutoff_date:
                            continue
                            
                    # 기사 제목과 본문에 기업명이 모두 포함되어 있는지 확인 (둘 중 하나라도 없으면 제외)
                    if company not in article.title or company not in article.text:
                        logger.debug(f"[{company}] 제목과 본문 모두에 기재되어 있지 않아 제외: {article.title}")
                        continue
                            
                    data = {
                        "company": company,
                        "title": article.title,
                        "url": url,
                        "publish_date": publish_date,
                        "authors": article.authors,
                        "summary": article.summary,
                        "text": article.text,
                        "keywords": article.keywords,
                    }
                    news_data.append(data)
                except Exception as e:
                    logger.debug(f"기사 파싱 실패 ({url}): {e}")
        except Exception as e:
            logger.error(f"[{company}] 뉴스 수집 중 오류: {e}")
            
    # 최신순으로 정렬
    news_data.sort(key=lambda x: x['publish_date'] if x['publish_date'] else datetime.min.replace(tzinfo=kst), reverse=True)
            
    logger.info(f"파싱 완료된 총 기업 기사 수: {len(news_data)}")
    return news_data
