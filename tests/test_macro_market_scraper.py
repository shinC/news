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
    
    # 2. 도메인별 수집 검증
    yahoo_collected = False
    investopedia_collected = False
    
    for a in macro_articles:
        url = a.get("url", "").lower()
        if "finance.yahoo.com" in url:
            yahoo_collected = True
            # 본문 검증
            assert len(a.get("text", "")) > 150, f"Yahoo Finance article content is too short: {a.get('title')}"
        elif "investopedia.com" in url:
            investopedia_collected = True
            # 본문 검증
            assert len(a.get("text", "")) > 150, f"Investopedia article content is too short: {a.get('title')}"
            
    print(f"Yahoo Finance collected: {yahoo_collected}")
    print(f"Investopedia collected: {investopedia_collected}")
    
    # 적어도 하나 이상은 수집되었거나 둘 다 수집되었는지 확인 (보통 둘 다 정상적이어야 함)
    assert yahoo_collected, "Yahoo Finance article was not collected or parsed properly!"
    assert investopedia_collected, "Investopedia article was not collected or parsed properly!"

if __name__ == "__main__":
    test_fetch_macro_market_news()
