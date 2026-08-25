import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import pytz
from newspaper import Article

# src 디렉토리를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings_kr

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_macro_closing")

def parse_rss_feed(feed_url: str, keyword: str) -> list:
    """RSS 피드를 읽어 제목에 키워드가 포함된 기사 목록을 반환합니다."""
    logger.info(f"RSS 피드 수집 시작: {feed_url} (키워드: {keyword})")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    matched_articles = []
    try:
        res = requests.get(feed_url, headers=headers, timeout=15)
        res.raise_for_status()
        
        # XML 파서 사용
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        
        for item in items:
            title = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            pub_date = item.pubDate.text.strip() if item.pubDate else ""
            
            # 제목에 키워드가 포함되어 있는지 확인 (대소문자 및 띄어쓰기 가볍게 처리)
            if keyword in title:
                logger.info(f"키워드 매칭 성공: {title}")
                matched_articles.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date
                })
    except Exception as e:
        logger.error(f"RSS 피드 수집 실패 ({feed_url}): {e}")
        
    return matched_articles

def scrape_article_content(url: str) -> str:
    """newspaper3k를 사용하여 뉴스 본문을 스크래핑합니다."""
    logger.info(f"뉴스 본문 스크래핑 시작: {url}")
    try:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        article.nlp()
        
        # 본문 내용 요약 또는 텍스트 반환
        content = article.text.strip()
        if not content:
            content = article.summary.strip()
            
        return content if content else "본문 내용을 가져올 수 없습니다."
    except Exception as e:
        logger.error(f"본문 스크래핑 실패 ({url}): {e}")
        return "본문 스크래핑 오류로 인해 내용을 수집하지 못했습니다."

def append_to_markdown(articles: list, output_filepath: str):
    """스크랩된 뉴스 목록을 마크다운 형식으로 만들어 기존 파일 하단에 추가합니다.
    단, 파일에 이미 동일한 기사 제목이 존재하면 중복해서 추가하지 않습니다.
    """
    if not articles:
        logger.warning("추가할 수집된 기사가 없습니다.")
        return
        
    # 기존 파일이 있다면 본문을 읽어와 제목 중복 여부 확인
    existing_content = ""
    if os.path.exists(output_filepath):
        try:
            with open(output_filepath, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception as e:
            logger.error(f"기존 마크다운 파일 읽기 실패 ({output_filepath}): {e}")
            
    # 중복되지 않은 기사만 필터링
    unique_articles = []
    for art in articles:
        title = art['title']
        # 이미 파일 내에 동일한 기사 제목이 존재하는지 판단
        if title in existing_content:
            logger.info(f"중복 기사 발견 (추가 안 함): {title}")
            continue
        unique_articles.append(art)
        
    if not unique_articles:
        logger.info("모든 수집된 기사가 이미 존재합니다. 추가 작업을 생략합니다.")
        return
        
    logger.info(f"마크다운 파일에 추가 시작 (추가 기사 수: {len(unique_articles)}): {output_filepath}")
    
    # KST 기준 현재 시각
    kst = pytz.timezone('Asia/Seoul')
    now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')
    
    markdown_content = []
    markdown_content.append("\n\n---\n")
    markdown_content.append(f"## 📰 증시마감 매크로 뉴스 추가 수집 ({now_str} KST)\n")
    markdown_content.append("> 이 섹션은 증시마감 매크로 뉴스 수집기를 통해 추가 수집된 뉴스입니다.\n\n")
    
    for idx, art in enumerate(unique_articles, 1):
        title = art['title']
        link = art['link']
        pub_date = art['pub_date']
        content = art['content']
        
        markdown_content.append(f"### {idx}. {title}\n")
        markdown_content.append(f"- **출처 및 링크**: [{link}]({link})\n")
        if pub_date:
            markdown_content.append(f"- **발행 시각 (RSS 기준)**: {pub_date}\n")
        markdown_content.append(f"- **본문 내용**:\n")
        
        # 본문 내용을 들여쓰기하여 가독성 높임
        indented_content = "\n".join([f"  {line}" for line in content.split("\n") if line.strip()])
        markdown_content.append(f"{indented_content}\n\n")
        
    # 기존 파일 하단에 덧붙이기 (Append)
    try:
        # 상위 디렉토리가 없을 시 생성
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        with open(output_filepath, "a", encoding="utf-8") as f:
            f.write("".join(markdown_content))
            
        logger.info(f"성공적으로 마크다운 추가 완료: {output_filepath}")
    except Exception as e:
        logger.error(f"마크다운 파일 추가 실패 ({output_filepath}): {e}")

def main():
    logger.info("=== 증시마감 매크로 뉴스 수집기 시작 ===")
    
    # 1. 설정 로드
    feeds = getattr(settings_kr, "closing_macro_rss_feeds", [])
    if not feeds:
        logger.error("설정 파일에서 closing_macro_rss_feeds를 찾을 수 없습니다.")
        return
        
    # 2. RSS 피드 파싱 및 매칭
    all_matched = []
    for feed in feeds:
        url = feed.get("url")
        keyword = feed.get("keyword")
        if url and keyword:
            matched = parse_rss_feed(url, keyword)
            all_matched.extend(matched)
            
    # 3. 본문 스크래핑
    final_articles = []
    for art in all_matched:
        # 중복 방지를 위한 가벼운 체크 (동일 링크 배제)
        if any(x['link'] == art['link'] for x in final_articles):
            continue
            
        content = scrape_article_content(art['link'])
        art['content'] = content
        final_articles.append(art)
        
    # 4. 마크다운 파일 하단에 결과 추가
    output_path = os.path.join(settings_kr.output_dir, settings_kr.output_filename)
    append_to_markdown(final_articles, output_path)
    
    logger.info("=== 증시마감 매크로 뉴스 수집기 종료 ===")

if __name__ == "__main__":
    main()
