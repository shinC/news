import feedparser
import requests

urls = [
    "https://finance.yahoo.com/news/rssindex",
    "https://finance.yahoo.com/rss/stock-market-news",
    "https://finance.yahoo.com/rss/economy"
]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
for url in urls:
    res = requests.get(url, headers=headers)
    print(f"URL: {url}, Status: {res.status_code}")
    if res.status_code == 200:
        d = feedparser.parse(res.content)
        print(f"  Entries: {len(d.entries)}")
        if d.entries:
            print(f"  Sample: {d.entries[0].title}")
