import sys
import os
import json
from datetime import datetime
import pytz

sys.path.append('/workspaces/news')
from src.core.scraper import fetch_company_news_us

if __name__ == "__main__":
    market_date = datetime.now(pytz.utc)
    res = fetch_company_news_us(["AAPL"], days=3, market_date=market_date)
    print("Fetched news for AAPL:")
    for article in res:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print("---")
