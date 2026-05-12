import sys
import os
from gnews import GNews

def test_gnews():
    google_news = GNews(language='ko', country='KR', period='1d', max_results=3)
    news = google_news.get_news("LG전자")
    print(f"Found {len(news)} articles.")
    for item in news:
        print(f"\nTitle: {item['title']}")
        print(f"URL: {item['url']}")
        article = google_news.get_full_article(item['url'])
        if article:
            print(f"Parsed Text Length: {len(article.text)}")
            print(f"Parsed Text: {article.text[:200]}...")
        else:
            print("Failed to get full article.")

if __name__ == "__main__":
    test_gnews()
