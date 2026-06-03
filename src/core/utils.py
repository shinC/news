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
            SEARCH_URL_CACHE[title] = real_url
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
            SEARCH_URL_CACHE[title] = real_url
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

def get_naver_api_summary(query: str) -> str:
    """네이버 뉴스 검색 API를 사용하여 기사 요약(스니펫)을 가져옵니다."""
    from config.settings import settings
    import requests
    import re
    import html
    
    client_id = settings.naver_client_id
    client_secret = settings.naver_client_secret
    
    if not client_id or not client_secret:
        return ""
        
    url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(query)}&display=5&sort=sim"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items:
                # 첫 번째 결과의 description 사용 (HTML 태그 제거)
                desc = items[0].get('description', '')
                clean_desc = re.sub(r'<[^>]+>', '', desc) # HTML 태그 제거
                clean_desc = html.unescape(clean_desc) # HTML 엔티티 제거
                return clean_desc
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"Naver API Error: {e}")
        
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
        # 구글이 차단된 경우 (JS 활성화 메시지 등) 야후 검색으로 자동 전환
        if "enable javascript" in res.text.lower() or "unusual traffic" in res.text.lower():
            logger.warning("Google Search blocked. Falling back to Yahoo Search.")
            return get_yahoo_summary(title)

        snippets = []
        for d in soup.select("div[jsname='sE79S'], .GI77S, .mCbY7l, .B6fVDf, .VwiC3b, .yXK7ab"):
            text = d.get_text(strip=True)
            if len(text) > 50:
                snippets.append(text)
        
        if not snippets:
            return get_yahoo_summary(title)
        
        if snippets:
            # 제목과 너무 비슷한 것 제외하고 가장 긴 것 선택
            snippets.sort(key=len, reverse=True)
            for s in snippets:
                title_words = set(clean_title.lower().split())
                s_words = set(s.lower().split())
                if len(title_words.intersection(s_words)) < len(title_words) * 0.9:
                    return s
            return snippets[0]

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

def get_article_text_playwright(url: str) -> str:
    """실제 브라우저를 띄워 기사 본문을 강제로 추출합니다 (차단 우회 최후의 수단)."""
    import re
    import logging
    from playwright.sync_api import sync_playwright
    
    logger = logging.getLogger(__name__)
    logger.info(f"Playwright: Fetching body for {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage', '--no-sandbox'])
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            try:
                page.goto(url, timeout=20000, wait_until='domcontentloaded')
                
                # 약간의 대기 (동적 렌더링)
                page.wait_for_timeout(2000)
                
                # 야후 파이낸스 등 주요 본문 컨테이너가 뜰 때까지 명시적 대기
                try:
                    page.wait_for_selector(".caas-body, article, main", timeout=10000)
                except Exception as e:
                    logger.warning(f"wait_for_selector timeout: {e}")
                # 본문으로 추정되는 요소들 텍스트 추출 (라이브 블로그 대응: H2/H3 만나면 컷)
                content = page.evaluate("""() => {
                    const selectors = ['.caas-body', '.article-content', 'article', '.article-body', '.story-body', '.main-content', 'main', '#content'];
                    for (let sel of selectors) {
                        let el = document.querySelector(sel);
                        if (el) {
                            let result = '';
                            let blocks = el.querySelectorAll('p, h1, h2, h3');
                            let foundP = false;
                            for (let child of blocks) {
                                // P 태그가 나오기 시작한 이후, H2나 H3가 등장하면 다음 기사/섹션으로 간주하고 중단
                                if (foundP && (child.tagName === 'H2' || child.tagName === 'H3' || child.tagName === 'H4')) {
                                    break;
                                }
                                if (child.tagName === 'P') {
                                    foundP = true;
                                    result += child.innerText + ' ';
                                } else if (!foundP && child.tagName === 'H1') {
                                    // 메인 타이틀은 포함
                                    result += child.innerText + ' ';
                                }
                            }
                            if (result.length > 200) return result;
                            
                            // 위 로직으로 못 잡았으면 fallback으로 innerText
                            if (el.innerText.length > 300) return el.innerText;
                        }
                    }
                    return document.body.innerText;
                }""")
            except:
                content = ""
            
            browser.close()
            if content and len(content) > 150:
                clean_text = re.sub(r'\s+', ' ', content).strip()
                return clean_text[:3000] # 하위 기사가 짤리므로 넉넉하게 3000자까지 허용
    except Exception as e:
        logger.error(f"Playwright 실패 ({url}): {e}")
    return ""

def batch_decode_google_urls(urls: list) -> dict:
    """
    구글 뉴스 암호화 URL 리스트를 입력받아, 배치(Batch)로 해독하여 
    {google_url: real_url} 맵핑 딕셔너리를 반환합니다.
    429 차단을 회피하기 위해 최대 20개 단위로 청킹하고, 청크 사이에 지연을 둡니다.
    """
    import time
    import logging
    from googlenewsdecoder import decoderv4
    
    logger = logging.getLogger("decode")
    
    # 중복 제거 및 구글 URL 필터링
    google_urls = list(set([u for u in urls if u and ("news.google.com" in u or "articles" in u or "read" in u)]))
    if not google_urls:
        return {}
        
    logger.info(f"배치 디코딩 시작: 총 {len(google_urls)}개의 구글 뉴스 URL")
    
    mapping = {}
    chunk_size = 20
    for i in range(0, len(google_urls), chunk_size):
        chunk = google_urls[i:i+chunk_size]
        logger.info(f"디코딩 진행 중... ({i+1}~{min(i+chunk_size, len(google_urls))}/{len(google_urls)})")
        
        try:
            # decoderv4 호출 (내부적으로 batchexecute 배치 POST 1번 쏨)
            results = decoderv4(chunk)
            
            for orig_url, res in zip(chunk, results):
                if isinstance(res, dict) and res.get("status"):
                    mapping[orig_url] = res.get("url")
                else:
                    # 실패 시 기존 URL 유지
                    mapping[orig_url] = orig_url
        except Exception as e:
            logger.error(f"배치 디코딩 중 에러 발생: {e}")
            for orig_url in chunk:
                mapping[orig_url] = orig_url
                
        # 청크 사이에 지연 시간 추가 (차단 안전핀)
        if i + chunk_size < len(google_urls):
            time.sleep(1.0)
            
    return mapping

SEARCH_URL_CACHE = {}

def search_real_url_fallback(title: str, is_kr: bool = False) -> str:
    """
    구글 뉴스 디코딩 실패 시 최후의 폴백으로,
    기사 제목의 핵심부(앞 6개 단어)를 네이버/야후 뉴스 검색에 검색하여
    첫 번째 검색 결과의 원본 URL을 반환합니다.
    """
    import urllib.parse
    import requests
    import re
    from bs4 import BeautifulSoup
    
    # 꼬리표 잘라내기
    clean_title = title.split(" - ")[0].split(" | ")[0]
    clean_title = re.sub(r'[^\w\s가-힣]', ' ', clean_title) # 한국어 매칭 보강
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    if not clean_title:
        return ""
        
    # 검색 성공률을 극대화하기 위해 앞 6개 단어만 추출
    words = clean_title.split()
    if len(words) > 6:
        query_title = " ".join(words[:6])
    else:
        query_title = clean_title
        
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    headers = {'User-Agent': user_agent}
    
    try:
        if is_kr:
            query = urllib.parse.quote(query_title)
            url = f"https://search.naver.com/search.naver?where=news&query={query}"
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'lxml')
            
            # 네이버 뉴스 링크 우선 추출
            link_tag = soup.select_one("a[href*='n.news.naver.com']")
            if not link_tag:
                for a in soup.select("div.news_area a, div.news_contents a, a.news_tit, a.el_title"):
                    if a.get('href') and a['href'].startswith('http'):
                        link_tag = a
                        break
            if link_tag:
                return link_tag['href']
        else:
            # 야후 파이낸스 검색
            query = urllib.parse.quote(clean_title)
            url = f"https://finance.yahoo.com/search?q={query}"
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'lxml')
            
            link_tag = soup.select_one("a[href*='/news/'], a.subtle-link, div.stream-item a")
            if link_tag:
                href = link_tag['href']
                return "https://finance.yahoo.com" + href if href.startswith('/') else href
    except Exception as e:
        logger.debug(f"Fallback search failed for {title}: {e}")
        
    return ""
