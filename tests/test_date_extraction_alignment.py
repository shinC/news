import sys
import os
from datetime import datetime, timedelta
import pytz

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.scraper import fetch_news as fetch_news_us
from core.scraper_kr import fetch_news as fetch_news_kr

def test_date_alignment():
    print("=== Testing US Date Alignment ===")
    # Mock a market date (e.g., 3 days ago)
    mock_market_date = datetime.now(pytz.utc) - timedelta(days=3)
    print(f"Mock Market Date: {mock_market_date}")
    
    # This should only fetch news around that date
    news_us = fetch_news_us(market_date=mock_market_date)
    for n in news_us:
        print(f"Title: {n['title'][:50]}... | Date: {n['publish_date']}")
        assert n['publish_date'] is not None
        # Should be within +/- 3 days of market_date (based on logic: cutoff=market-2, upper=market+1)
        assert mock_market_date - timedelta(days=2.1) <= n['publish_date'] <= mock_market_date + timedelta(days=1.1)

    print("\n=== Testing KR Date Alignment ===")
    kst = pytz.timezone('Asia/Seoul')
    mock_market_date_kr = datetime.now(kst) - timedelta(days=3)
    print(f"Mock Market Date KR: {mock_market_date_kr}")
    
    news_kr = fetch_news_kr(market_date=mock_market_date_kr)
    for n in news_kr:
        print(f"Title: {n['title'][:50]}... | Date: {n['publish_date']}")
        assert n['publish_date'] is not None
        assert mock_market_date_kr - timedelta(days=2.1) <= n['publish_date'] <= mock_market_date_kr + timedelta(days=1.1)

    print("\nVerification Complete!")

if __name__ == "__main__":
    test_date_alignment()
