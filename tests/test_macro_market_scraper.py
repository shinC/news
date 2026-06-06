import sys
import os
from datetime import datetime
import pytz
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.scraper import fetch_news

def test_fetch_macro_market_news():
    print("Testing Macro & Market news scraper...")
    ref_date = datetime.now(pytz.utc)
    articles = fetch_news(market_date=ref_date)
    
    # 1. Macro & Market 카테고리 필터링
    macro_articles = [a for a in articles if a.get("category") == "Macro & Market"]
    
    print(f"Total Macro & Market articles found: {len(macro_articles)}")
    for a in macro_articles:
        print(f"[{a.get('category')}] {a.get('title')} ({a.get('url')})")
        print(f"Text Length: {len(a.get('text', ''))}")
        print("-" * 50)
        
    assert len(macro_articles) > 0, "No Macro & Market articles collected!"
    
    # 2. 도메인별 수집 및 키워드 검증
    yahoo_collected = False
    investopedia_collected = False
    
    for a in macro_articles:
        url = a.get("url", "").lower()
        title = a.get("title", "").lower()
        if "finance.yahoo.com" in url:
            yahoo_collected = True
            # 제목 시작 검증 ("stock market" 시작)
            is_valid_start = title.startswith("stock market")
            assert is_valid_start, f"Yahoo Finance article title does not start with valid phrase: {a.get('title')}"
            # 본문 검증
            assert len(a.get("text", "")) > 150, f"Yahoo Finance article content is too short: {a.get('title')}"
        elif "investopedia.com" in url:
            investopedia_collected = True
            # 제목 시작 검증 ("markets news" 또는 "market news" 시작)
            is_valid_start = title.startswith("markets news") or title.startswith("market news")
            assert is_valid_start, f"Investopedia article title does not start with valid phrase: {a.get('title')}"
            # 본문 검증
            assert len(a.get("text", "")) > 150, f"Investopedia article content is too short: {a.get('title')}"
            
    print(f"Yahoo Finance ('stock market news') collected: {yahoo_collected}")
    print(f"Investopedia ('market news') collected: {investopedia_collected}")
    
    # 장외 시간/주말 등 야후 마감 기사가 스크롤 범위 밖에 밀려있는 경우를 고려하여 Warning으로 처리하거나 유연하게 단언
    if not yahoo_collected:
        print("[WARNING] Yahoo Finance ('stock market news') was not collected. This is normal during market closed hours/weekends.")
    if not investopedia_collected:
        print("[WARNING] Investopedia ('market news') was not collected. This is normal during market closed hours/weekends.")
        
    # 적어도 하나 이상은 수집 성공했는지 검증하여 기능 자체의 생존 여부 판단
    assert yahoo_collected or investopedia_collected, "Neither Yahoo Finance nor Investopedia news was collected!"

if __name__ == "__main__":
    test_fetch_macro_market_news()
