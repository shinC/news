import os
import requests
import xml.etree.ElementTree as ET
import urllib.parse
from googlenewsdecoder import new_decoderv1
from playwright.sync_api import sync_playwright

def test_google_news():
    query = "Stock market today"
    # 구글 뉴스 RSS 피드 주소
    rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    
    output_dir = os.path.join(os.path.dirname(__file__), "data", "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "test_google_news_result.md")
    
    print("🚀 구글 뉴스 RSS 검색을 시작합니다...", flush=True)
    
    try:
        # 1. 구글 뉴스 RSS 가져오기 (로봇 탐지에 잘 걸리지 않음)
        res = requests.get(rss_url, timeout=10)
        res.raise_for_status()
        root = ET.fromstring(res.content)
        
        items = root.findall('.//item')[:5]
        if not items:
            print("❌ 기사를 찾지 못했습니다.", flush=True)
            return
            
        print(f"✅ {len(items)}개의 기사 제목을 가져왔습니다. 가짜 주소(CBM) 암호 해독을 시작합니다...", flush=True)
        
        articles_info = []
        for item in items:
            title = item.find('title').text
            google_url = item.find('link').text
            
            # 2. googlenewsdecoder를 이용해 구글 서버 접속 없이 진짜 주소 알아내기 (CAPTCHA 원천 차단)
            try:
                dec = new_decoderv1(google_url)
                if dec.get('status'):
                    real_url = dec.get('decoded_url')
                else:
                    real_url = google_url # 실패 시 원본
            except:
                real_url = google_url
                
            articles_info.append({"title": title, "raw_link": google_url, "real_url": real_url})
            
        print(f"✅ 암호 해독 완료! 백그라운드에서 진짜 언론사 주소로 다이렉트 접속해 본문을 추출합니다.", flush=True)
        
        # 3. 본문 추출 (구글 리다이렉트를 거치지 않으므로 headless=True 모드로 조용히 실행 가능)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Google News Test Results (Decoder Version)\n")
                f.write(f"**Query**: {query}\n\n")
                
                for i, item in enumerate(articles_info):
                    print(f"[{i+1}/5] Processing: {item['title'][:40]}...", flush=True)
                    page = context.new_page()
                    
                    try:
                        # 구글을 거치지 않고 진짜 언론사 주소로 곧바로 이동!
                        page.goto(item['real_url'], wait_until='domcontentloaded', timeout=15000)
                        page.wait_for_timeout(3000)
                        
                        # 지연 로딩을 위한 스크롤 유도
                        page.mouse.wheel(0, 2000)
                        page.wait_for_timeout(2000)
                        
                        # 본문 추출
                        paragraphs = page.evaluate('''() => {
                            return Array.from(document.querySelectorAll("p"))
                                 .map(p => p.innerText.trim())
                                 .filter(t => t.length > 50)
                                 .join("\\n\\n");
                        }''')
                        
                        if not paragraphs or len(paragraphs) < 300:
                            paragraphs = page.evaluate('document.body.innerText')
                            
                        article_text = paragraphs if paragraphs else "본문을 가져오지 못했습니다."
                        final_url = page.url
                        
                    except Exception as e:
                        print(f"  -> Error navigating: {e}", flush=True)
                        article_text = f"페이지 로드 오류 또는 시간 초과: {str(e)}"
                        final_url = "Timeout or Error"
                    finally:
                        page.close()
                        
                    f.write(f"### [{i+1}] {item['title']}\n")
                    f.write(f"- **Google Encrypted Link**: {item['raw_link']}\n")
                    f.write(f"- **Decoded Real Link**: {item['real_url']}\n")
                    f.write(f"- **Final URL**: {final_url}\n")
                    f.write(f"- **Body Length**: {len(article_text)} characters\n\n")
                    f.write(f"**[본문 전체 내용]**\n```text\n{article_text}\n```\n\n")
                    f.write("---\n\n")
                    
            browser.close()
            print(f"\n🎉 테스트 완료! 결과 파일: {output_file}", flush=True)
            
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    test_google_news()
