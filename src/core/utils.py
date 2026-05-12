import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import re

logger = logging.getLogger("fallback")

def get_naver_summary(title: str) -> str:
    """네이버 검색을 통해 기사 본문을 직접 파싱하거나 요약을 가져옵니다."""
    try:
        import newspaper
        # 1. 쿼리 클리닝: 특수문자 제거 및 핵심 키워드 위주로
        clean_title = re.sub(r'[^\w\s]', ' ', title.split(" - ")[0].split(" | ")[0])
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        # newspaper 설정 (User-Agent 필수)
        config = newspaper.Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        config.request_timeout = 10

        def try_search(q):
            print(f"[DEBUG] try_search with query: {q}")
            query = urllib.parse.quote(q)
            url = f"https://search.naver.com/search.naver?where=news&query={query}"
            headers = {'User-Agent': config.browser_user_agent}
            res = requests.get(url, headers=headers, timeout=5)
            print(f"[DEBUG] response status: {res.status_code}, length: {len(res.text)}")
            return BeautifulSoup(res.text, 'lxml')

        soup = try_search(clean_title)
        
        # 만약 검색 결과가 없으면 제목의 앞부분 4단어로 더 짧게 재시도
        if not soup.select_one(".news_tit"):
            short_q = " ".join(clean_title.split()[:4])
            if len(short_q) > 2:
                soup = try_search(short_q)

        # 2. 뉴스 검색 결과에서 링크 추출 (네이버 뉴스 링크 우선)
        link_tag = soup.select_one("a[href*='n.news.naver.com']")
        if not link_tag:
            # 외부 링크라도 찾기
            for a in soup.select("div.news_area a, div.news_contents a, a.news_tit, a.el_title"):
                if a.get('href') and a['href'].startswith('http'):
                    link_tag = a
                    break
                    
        if link_tag:
            real_url = link_tag['href']
            # 3. 해당 링크를 직접 파싱 시도
            article = newspaper.Article(real_url, config=config)
            article.download()
            article.parse()
            article.nlp()
            
            summary = article.summary if (article.summary and len(article.summary) > 300) else article.text[:1000]
            if summary and len(summary) > 150:
                return summary

        # 4. 파싱 실패 시 검색 결과의 스니펫이라도 반환 (단, 최소 길이는 확보)
        desc = soup.select_one(".news_dsc, .api_txt_lines.dsc_txt_wrap, .api_txt_lines, div.dsc_wrap, div.news_dsc_wrap")
        if desc:
            print(f"[DEBUG] Returning snippet description, length: {len(desc.get_text(strip=True))}")
            return desc.get_text(strip=True)
        else:
            # 본문 스니펫 클래스가 바뀌었을 경우를 대비해 p 태그나 특정 텍스트 래퍼 탐색
            for el in soup.select("div.news_contents div, div.news_wrap div"):
                text = el.get_text(strip=True)
                if len(text) > 50 and not text.startswith("동영상") and not text.startswith("포토"):
                    return text
            print(f"[DEBUG] No description found in soup")
    except Exception as e:
        print(f"[DEBUG] Exception in get_naver_summary: {e}")
    return ""

def get_yahoo_summary(title: str) -> str:
    """야후 파이낸스 검색을 통해 기사 본문을 직접 파싱하거나 요약을 가져옵니다."""
    try:
        import newspaper
        # 1. 쿼리 클리닝
        clean_title = re.sub(r'[^\w\s]', ' ', title.split(" - ")[0].split(" | ")[0])
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        # newspaper 설정
        config = newspaper.Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        config.request_timeout = 10

        def try_search(q):
            query = urllib.parse.quote(q)
            url = f"https://finance.yahoo.com/search?q={query}"
            headers = {'User-Agent': config.browser_user_agent}
            res = requests.get(url, headers=headers, timeout=5)
            return BeautifulSoup(res.text, 'lxml')

        soup = try_search(clean_title)
        
        # 2. 검색 결과에서 링크 추출 시도
        # Yahoo Finance의 새로운 뉴스 링크 패턴 반영
        link_tag = soup.select_one("a[href*='/news/'], a.subtle-link, div.stream-item a")
        if not link_tag and len(clean_title.split()) > 5:
            short_q = " ".join(clean_title.split()[:5])
            soup = try_search(short_q)
            link_tag = soup.select_one("a[href*='/news/'], a.subtle-link")

        if link_tag:
            href = link_tag['href']
            real_url = "https://finance.yahoo.com" + href if href.startswith('/') else href
            # 3. 직접 파싱 시도
            article = newspaper.Article(real_url, config=config)
            article.download()
            article.parse()
            article.nlp()
            
            summary = article.summary if (article.summary and len(article.summary) > 300) else article.text[:1000]
            if summary and len(summary) > 150:
                return summary

        # 4. 파싱 실패 시 검색 결과의 스니펫이라도 반환
        desc = soup.select_one(r"div.compText, .Va\(t\) p, .Mt\(8px\) p, .description, p")
        if desc:
            snippet = desc.get_text(separator=' ', strip=True)
            if len(snippet) > 50:
                return snippet
    except Exception as e:
        logger.debug(f"Exception in get_yahoo_summary: {e}")
    return ""

def get_google_summary(title: str) -> str:
    """구글 뉴스 검색을 통해 기사 스니펫(Snippet)을 가져옵니다."""
    try:
        # 1. 쿼리 클리닝
        clean_title = re.sub(r'[^\w\s]', ' ', title.split(" - ")[0].split(" | ")[0])
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        encoded_query = urllib.parse.quote(clean_title)
        url = f"https://news.google.com/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'lxml')
        
        # 구글 뉴스 검색 결과에서 스니펫(기사 요약 문구) 추출
        # 1. 특정 스니펫 클래스 시도
        desc = soup.select_one("div[jsname='sE79S'], .GI77S, .mCbY7l, .B6fVDf")
        if desc:
            return desc.get_text(strip=True)

        # 2. article 태그 순회하며 제목 제외 텍스트 추출
        for article in soup.select('article'):
            # 제목 태그 찾기 (h3, h4 또는 a)
            title_tag = article.find(['h3', 'h4', 'a'], href=True)
            if not title_tag: continue
            article_title = title_tag.get_text().strip()
            
            # 전체 텍스트
            full_text = article.get_text(separator=' ', strip=True)
            
            # 제목과 기타 메타정보(출처, 시간) 제외 시도
            # 단순 replace는 위험할 수 있으므로, 텍스트가 제목보다 충분히 길 때만 반환
            if len(full_text) > len(article_title) + 50:
                snippet = full_text.replace(article_title, "").strip()
                # 시간 정보 제거 (예: "2 hours ago")
                snippet = re.sub(r'\d+\s+(hours?|days?|minutes?|secs?)\s+ago', '', snippet, flags=re.I).strip()
                # 출처 이름 제거 시도 (보통 마지막이나 처음에 위치)
                if len(snippet) > 50:
                    return snippet
                
    except Exception as e:
        logger.debug(f"Exception in get_google_summary: {e}")
    return ""
