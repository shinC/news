import logging
import sys
import os

# 프로젝트 루트 디렉토리를 경로에 추가
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.scraper_kr import fetch_news
from config.settings import settings_kr

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_fetch_news():
    setup_logging()
    logger = logging.getLogger("test_scraper")
    
    logger.info("Testing fetch_news...")
    settings_kr.max_results = 5
    news = fetch_news()
    
    logger.info(f"Total news fetched: {len(news)}")
    for i, item in enumerate(news[:5]):
        logger.info(f"News {i+1}: {item['title']} ({item['url']})")

if __name__ == "__main__":
    test_fetch_news()
