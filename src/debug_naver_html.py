import sys
import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

def debug_naver_html():
    title = "LG전자"
    query = urllib.parse.quote(title)
    url = f"https://search.naver.com/search.naver?where=news&query={query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    
    res = requests.get(url, headers=headers, timeout=5)
    print(res.text[:2000])

if __name__ == "__main__":
    debug_naver_html()
