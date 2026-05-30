import sys
import os
sys.path.append('/workspaces/news')
from src.core.scraper_kr import fetch_company_news_kr
import json

if __name__ == "__main__":
    res = fetch_company_news_kr(["삼성전자", "SK하이닉스"], days=3)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
