import sys
import os
import logging
from datetime import datetime
import re

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
    
    # 1. 기업 뉴스 수집 (1개만)
    logger.info("기업 뉴스 수집 테스트 (LG전자)")
    company_news = fetch_company_news_kr(["LG전자"], days=1)
    
    # 2. 일반 카테고리
    logger.info("카테고리 뉴스 수집 테스트")
    general_news = fetch_news(dynamic_keywords=["금융"])
    
    all_news = company_news + general_news
    logger.info(f"수집된 총 기사 수: {len(all_news)}")
    
    if len(all_news) == 0:
        logger.error("기사가 하나도 수집되지 않았습니다!")
        return

    # 요약 품질 확인 (저장 전에 수행)
    print("\n=== 요약 품질 확인 (샘플 5개) ===")
    count = 0
    for news in all_news:
        summary = news.get('summary', '')
        if summary and len(summary) > 200:
            print(f"\n[성공] 제목: {news['title']}")
            print(f"[요약 길이: {len(summary)}]")
            print(f"[요약 내용]: {summary[:300]}...")
            count += 1
        if count >= 5: break
    
    if count == 0:
        print("\n[경고] 200자 이상의 요약이 하나도 없습니다. 모두 제목만 나왔을 가능성이 큽니다.")
        for news in all_news[:3]:
            print(f"\n[실패?] 제목: {news['title']}")
            print(f"[요약 길이: {len(news.get('summary', ''))}]")
            print(f"[요약 내용]: {news.get('summary', '')}")

    # 3. 분석 및 정렬
    sorted_news = analyze_and_sort(all_news)
    
    # 4. 포맷팅 (파일명만 전달)
    output_filename = "test_minimal_kr_v2.md"
    save_to_markdown(
        news_data=sorted_news,
        market_data=None,
        report_title="Minimal Test Report",
        output_filename=output_filename
    )
    
    logger.info(f"결과물이 data/output/{output_filename} 에 저장되었습니다.")

if __name__ == "__main__":
    test_minimal()
