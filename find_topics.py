import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

queries = ["비즈니스", "경제", "세계", "정치", "금융", "과학기술", "인터넷보안"]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for q in queries:
    url = f"https://news.google.com/search?q={urllib.parse.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    
    # Try to find a topic link in the results (usually there's a "Topic" badge or link)
    found = False
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if '/topics/' in href:
            topic_id = href.split('/topics/')[1].split('?')[0]
            print(f"{q}: {topic_id}")
            found = True
            break
    if not found:
        print(f"{q}: Not found")

