import sys
import os

# Add project root to path
sys.path.append(os.path.abspath('.'))

from core.scraper_kr import fetch_company_news_kr
from core.utils import get_naver_summary

def test_single():
    print("Testing get_naver_summary directly:")
    title = "[특징주] LG전자, AI 데이터센터‧로봇 확장성 부각에 급등…52주 신고가 경신 - 이투데이"
    summary = get_naver_summary(title)
    print(f"Summary length: {len(summary)}")
    print(f"Summary: {summary[:300]}...")
    
    print("\nTesting fetch_company_news_kr:")
    news = fetch_company_news_kr(["LG전자"], days=1)
    if not news:
        print("No news fetched!")
        return
        
    for item in news[:2]:
        print(f"\nTitle: {item['title']}")
        summ = item.get('summary', '')
        print(f"Summary length: {len(summ)}")
        print(f"Summary: {summ[:300]}...")

if __name__ == "__main__":
    test_single()
