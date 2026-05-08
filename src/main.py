import logging
import sys
import os

# src 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import fetch_news
from core.analyzer import analyze_and_sort
from core.formatter import save_to_markdown
from core.market import get_market_data

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logger = logging.getLogger("main")
    
    logger.info("=== US Economy News Scraper 시작 ===")
    
    # 0. 시황 데이터 수집
    logger.info("0단계: 미국 주가지수 및 섹터 시황 수집 시작")
    market_data = get_market_data()

    # 1. 기사 수집
    logger.info("1단계: 기사 수집 (Scraping) 시작")
    raw_news = fetch_news()
    
    if not raw_news:
        logger.warning("수집된 기사가 없습니다. 마크다운 저장으로 넘어갑니다.")
        sorted_news = []
    else:
        # 2. 데이터 분석 및 정렬
        logger.info("2단계: 데이터 분석 및 정렬 (Analyzing & Sorting) 시작")
        sorted_news = analyze_and_sort(raw_news)
    
    # 3. 마크다운 저장
    logger.info("3단계: 결과물 저장 (Formatting) 시작")
    save_to_markdown(sorted_news, market_data)
    
    logger.info("=== US Economy News Scraper 완료 ===")

if __name__ == "__main__":
    main()
