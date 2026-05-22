import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
res = requests.get("https://news.google.com/home?hl=ko&gl=KR&ceid=KR:ko", headers=headers)
soup = BeautifulSoup(res.text, 'lxml')

for a in soup.find_all('a'):
    href = a.get('href', '')
    if '/topics/' in href:
        topic_id = href.split('/topics/')[1].split('?')[0]
        text = a.get_text(strip=True)
        if text:
            print(f"{text}: {topic_id}")
