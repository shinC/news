import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging

logger = logging.getLogger("fallback")

def get_naver_summary(title: str) -> str:
    """네이버 검색을 통해 기사 요약을 가져옵니다."""
    try:
        # 타이틀에서 출처 제거
        clean_title = title.split(" - ")[0].split(" | ")[0].split(" : ")[0]
        query = urllib.parse.quote(clean_title)
        url = f"https://search.naver.com/search.naver?where=news&query={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # 네이버 뉴스 검색 결과의 요약문 추출
        desc = soup.select_one(".news_dsc, .api_txt_lines.dsc_txt_wrap, .api_txt_lines")
        if desc:
            return desc.get_text(strip=True)
    except Exception: pass
    return ""

def get_yahoo_summary(title: str) -> str:
    """야후 파이낸스 검색을 통해 기사 요약을 가져옵니다."""
    try:
        # 타이틀에서 출처 제거
        clean_title = title.split(" - ")[0].split(" | ")[0].split(" : ")[0]
        query = urllib.parse.quote(clean_title)
        url = f"https://finance.yahoo.com/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # 야후 검색 결과 요약 (더 넓은 선택자 사용)
        desc = soup.select_one(r".Va\(t\) p, .Mt\(8px\) p, .description, p")
        if desc:
            return desc.get_text(strip=True)
    except Exception: pass
    return ""
