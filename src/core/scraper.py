import logging
from typing import List, Dict, Any
import newspaper
from newspaper.google_news import GoogleNewsSource
from config.settings import settings

logger = logging.getLogger(__name__)

def fetch_news(dynamic_keywords: List[str] = None) -> List[Dict[str, Any]]:
    """
    구글 뉴스에서 '미국 경제/비즈니스' 카테고리의 최근 기사를 수집합니다.
    """
    logger.info(f"구글 뉴스 수집 시작: 카테고리={settings.topic}, 기간={settings.period}")
    
    # GNews 기반의 GoogleNewsSource 생성
    # topic 매개변수가 GoogleNewsSource에 없을 수도 있으므로,
    # newspaper4k 문서나 gnews 동작 방식에 따라 다를 수 있습니다.
    # 일단 topic과 period를 전달해 봅니다.
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
    # 이 과정은 스레드풀을 사용하여 병렬로 진행됨
    logger.info("기사 다운로드 시작...")
    downloaded_articles = source.download_articles()
    
    news_data = []
    
    # 합쳐진 우선순위 키워드 구성
    base_keywords = getattr(settings, 'priority_keywords', [])
    priority_keywords = base_keywords + (dynamic_keywords if dynamic_keywords else [])
    logger.info(f"총 {len(priority_keywords)}개의 키워드로 우선순위 분석을 진행합니다.")
    
    for article in downloaded_articles:
        try:
            article.parse()
            article.nlp() # 키워드와 요약 생성
            
            # 우선순위 키워드 포함 여부 검사 (가중치 부여)
            priority_score = 0
            text_to_check = (article.title + " " + article.summary + " " + " ".join(article.keywords)).lower()
            
            for keyword in priority_keywords:
                if keyword.lower() in text_to_check:
                    priority_score += 1
            
            from datetime import datetime, timedelta
            import pytz
            
            # 날짜 필터링 (설정된 period 기준)
            # settings.period가 '2d' 형태라고 가정
            days = 2
            if settings.period.endswith('d'):
                try:
                    days = int(settings.period[:-1])
                except: pass
            
            cutoff_date = datetime.now(pytz.utc) - timedelta(days=days)
            
            # 기사 날짜 확인 및 필터링
            pub_date = article.publish_date
            if pub_date:
                # timezone이 없는 경우 UTC로 가정
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=pytz.utc)
                else:
                    pub_date = pub_date.astimezone(pytz.utc)
                
                if pub_date < cutoff_date:
                    logger.info(f"오래된 기사 제외 ({pub_date}): {article.title}")
                    continue
            else:
                # 날짜를 알 수 없는 경우 일단 포함하되, 로그 기록
                # (또는 엄격하게 제외하려면 여기서 continue)
                logger.warning(f"발행일을 알 수 없는 기사: {article.title}")
                # 최신성 보장을 위해 날짜 없는 기사도 제외하고 싶다면 아래 주석 해제
                # continue

            data = {
                "title": article.title,
                "url": article.url,
                "publish_date": article.publish_date,
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

def fetch_company_news_us(companies: List[str], days: int = 3) -> List[Dict[str, Any]]:
    """
    구글 뉴스에서 특정 기업들에 대한 최신 기사를 수집합니다.
    """
    logger.info(f"미국 기업 뉴스 수집 시작: 대상 기업={companies}, 기간={days}일")
    news_data = []
    
    from datetime import datetime, timedelta
    import pytz
    cutoff_date = datetime.now(pytz.utc) - timedelta(days=days)
    for company in companies:
        logger.info(f"[{company}] 뉴스 검색 중...")
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(company)
            news_items = ticker_obj.news
            
            # 티커에서 회사 풀네임 가져오기 (예: "Apple Inc." -> "Apple")
            company_full_name = company
            try:
                info = ticker_obj.info
                if 'shortName' in info:
                    company_full_name = info['shortName'].split(',')[0].split(' Inc')[0].split(' Corp')[0].split(' Ltd')[0].strip()
            except Exception:
                pass
                
            for item in news_items:
                try:
                    content = item.get('content', {})
                    if not content: continue
                    
                    url = content.get('canonicalUrl', {}).get('url', '')
                    if not url:
                        url = content.get('clickThroughUrl', {}).get('url', '')
                    if not url: continue
                    
                    # pub_date 필터링
                    pub_date_str = content.get('pubDate', '')
                    pub_date = None
                    if pub_date_str:
                        try:
                            # 2026-05-08T21:30:17Z
                            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ")
                            pub_date = pub_date.replace(tzinfo=pytz.utc)
                            if pub_date < cutoff_date:
                                continue
                        except Exception:
                            pub_date = datetime.now(pytz.utc)
                            
                    # 본문 검증을 위해 기사 다운로드
                    config = newspaper.Config()
                    config.request_timeout = 10
                    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
                    article = newspaper.Article(url, language='en', config=config)
                    
                    title = ""
                    text = ""
                    try:
                        article.download()
                        article.parse()
                        article.nlp()
                        title = article.title
                        text = article.text
                    except Exception as e:
                        # WSJ, Barrons 등 403 에러가 발생하는 사이트 대응: yfinance 요약 정보 활용
                        logger.warning(f"기사 본문 다운로드 실패 ({url}), 요약 정보로 대체 검증: {e}")
                        title = content.get('title', '')
                        text = content.get('summary', '')
                    
                    if not title or not text: continue
                    
                    # 티커 또는 회사명이 제목/본문에 있는지 검증
                    import re
                    def has_match(target_text, ticker_str, name_str):
                        target_text = target_text.lower()
                        # 1. 티커 매칭 (독립된 단어로)
                        if re.search(r'\b' + re.escape(ticker_str.lower()) + r'\b', target_text):
                            return True
                        # 2. 풀네임 매칭
                        if name_str.lower() in target_text:
                            return True
                        # 3. 핵심어 매칭 (예: "Micron Technology" -> "Micron")
                        # 첫 단어가 3글자 이상인 경우에만 핵심어로 인정하여 매칭 시도
                        name_words = name_str.split(' ')
                        if name_words:
                            first_word = name_words[0].lower()
                            if len(first_word) >= 3 and first_word in target_text:
                                return True
                        return False
                        
                    if not has_match(title, company, company_full_name) or not has_match(text, company, company_full_name):
                        logger.debug(f"[{company}] 제목과 본문 모두에 기재되어 있지 않아 제외: {title}")
                        continue
                    
                    data = {
                        "company": company,
                        "title": title,
                        "url": url,
                        "publish_date": pub_date,
                        "authors": article.authors,
                        "summary": article.summary,
                        "text": text,
                        "keywords": article.keywords,
                    }
                    news_data.append(data)
                except Exception as e:
                    logger.error(f"기사 파싱 실패 ({url}): {e}")
        except Exception as e:
            logger.error(f"[{company}] 뉴스 수집 실패: {e}")
            
    # 최신순으로 정렬
    news_data.sort(key=lambda x: x['publish_date'] if x['publish_date'] else datetime.min.replace(tzinfo=pytz.utc), reverse=True)
            
    logger.info(f"파싱 완료된 총 기업 기사 수: {len(news_data)}")
    return news_data
