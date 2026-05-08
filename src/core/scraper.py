import logging
from typing import List, Dict, Any
import newspaper
from newspaper.google_news import GoogleNewsSource
from config.settings import settings

logger = logging.getLogger(__name__)

def fetch_news() -> List[Dict[str, Any]]:
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
    for article in downloaded_articles:
        try:
            article.parse()
            article.nlp() # 키워드와 요약 생성
            
            data = {
                "title": article.title,
                "url": article.url,
                "publish_date": article.publish_date,
                "authors": article.authors,
                "summary": article.summary,
                "text": article.text,
                "keywords": article.keywords
            }
            news_data.append(data)
        except Exception as e:
            logger.error(f"기사 파싱 실패 ({article.url}): {e}")
            
    logger.info(f"파싱 완료된 기사 수: {len(news_data)}")
    return news_data
