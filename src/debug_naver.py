import sys
import os
import requests
import urllib.parse
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.path.abspath('.'))

def debug_naver_dom():
    title = "특징주 LG전자 전장 로봇 쌍끌이 기대감에 52주 신고가"
    query = urllib.parse.quote(title)
    url = f"https://search.naver.com/search.naver?where=news&query={query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    
    res = requests.get(url, headers=headers, timeout=5)
    print(f"Status: {res.status_code}, Length: {len(res.text)}")
    
    soup = BeautifulSoup(res.text, 'lxml')
    
    # Try different selectors to find news links
    print("\nTrying various selectors for links:")
    selectors = ['.news_tit', 'a.news_tit', '.news_area a', 'a.info', '.dsc_txt_wrap']
    for sel in selectors:
        elements = soup.select(sel)
        print(f"Selector '{sel}' found {len(elements)} elements.")
        if elements:
            print(f"First element for '{sel}': {elements[0]}")
            
    print("\nTrying to find descriptions:")
    desc_selectors = ['.news_dsc', '.api_txt_lines', '.dsc_txt_wrap']
    for sel in desc_selectors:
        elements = soup.select(sel)
        print(f"Selector '{sel}' found {len(elements)} elements.")
        if elements:
            print(f"First element text: {elements[0].get_text(strip=True)[:100]}")

if __name__ == "__main__":
    debug_naver_dom()
