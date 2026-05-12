import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath('.'))

from core.scraper_kr import fetch_news, fetch_company_news_kr
from core.analyzer import analyze_and_sort
from core.formatter import save_to_markdown
from config.settings import settings_kr

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minimal():
    logger.info("=== Minimal Test 시작 (기사 1-2개 대상) ===")
    
    # 1. 아주 제한적인 기업 1개만 수집
    logger.info("기업 뉴스 수집 테스트 (LG전자)")
    company_news = fetch_company_news_kr(["LG전자"], days=1)
    
    # 2. 일반 카테고리 (금융 키워드 위주)
    logger.info("카테고리 뉴스 수집 테스트 (금융)")
    # fetch_news() uses settings_kr.categories, so I'll just call it
    # it might take a bit longer but we need to verify the loop
    general_news = fetch_news(dynamic_keywords=["금융"])
    
    all_news = company_news + general_news
    logger.info(f"수집된 총 기사 수: {len(all_news)}")
    
    if len(all_news) == 0:
        logger.error("기사가 하나도 수집되지 않았습니다!")
        return

    # 3. 분석 및 정렬
    sorted_news = analyze_and_sort(all_news)
    
    # 4. 포맷팅
    output_path = "data/output/test_minimal_kr.md"
    save_to_markdown(
        news_data=sorted_news,
        market_data=None,
        report_title="Minimal Test Report",
        output_filename=output_path
    )
    
    logger.info(f"결과물이 {output_path} 에 저장되었습니다.")
    
    # 요약 품질 확인
    print("\n=== 요약 품질 확인 (최대 3개) ===")
    for news in all_news[:3]:
        print(f"\n[기사 제목]: {news['title']}")
        summary = news.get('summary', '')
        print(f"[요약 (길이 {len(summary or '')})]: {summary[:300]}...")

if __name__ == "__main__":
    test_minimal()
