"""Fetch the daily CNBC/Investopedia closing articles.

This is intentionally a standalone first step.  It does not modify ``main.py``
or any existing scraper.  Run without ``--append`` to inspect the result; use
``--append`` only after the extracted text has been verified.
"""

from __future__ import annotations

import argparse
import logging
import os
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

try:
    from curl_cffi import requests as http_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests as http_requests
    CURL_CFFI_AVAILABLE = False
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


LOG = logging.getLogger("fetch_macro_closing")
KST = timedelta(hours=9)
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
DATE_HEADER = re.compile(
    r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s+(?:AM|PM)\s+(?:EDT|EST|ET)$",
    re.I,
)
INVESTOPEDIA_URL = re.compile(
    r"/stock-market-today-dow-jones-s-and-p-500-(\d{8})-\d+/?$", re.I
)


def previous_us_weekday(kst_now: datetime | None = None) -> date:
    """Return the previous US calendar weekday for a KST morning run."""
    now = kst_now or (datetime.now(timezone.utc) + KST)
    us_date = now.date() - timedelta(days=1)
    while us_date.weekday() >= 5:
        us_date -= timedelta(days=1)
    return us_date


def cnbc_url_for(day: date) -> str:
    return f"https://www.cnbc.com/{day:%Y/%m/%d}/stock-market-today-live-updates.html"


def cnbc_candidate_urls(target_day: date) -> list[str]:
    """CNBC는 목표 미국 거래일의 전날 URL에서 최신 본문을 제공한다."""
    return [cnbc_url_for(target_day - timedelta(days=1))]


def _article_links(page, days: list[date]) -> list[str]:
    """Find Investopedia candidates from its public topic page."""
    listing_url = "https://www.investopedia.com/markets-news-4427704"
    links = []
    try:
        request_kwargs = {"headers": HTTP_HEADERS, "proxies": {"http": "", "https": ""}, "timeout": 30}
        if CURL_CFFI_AVAILABLE:
            request_kwargs["impersonate"] = "chrome124"
        listing = http_requests.get(listing_url, **request_kwargs)
        listing.raise_for_status()
        listing_soup = BeautifulSoup(listing.text, "html.parser")
        links = [{"href": a.get("href", ""), "text": a.get_text(" ", strip=True)} for a in listing_soup.select("a[href]")]
    except Exception as exc:
        LOG.warning("Investopedia 목록 HTTP 확인 실패: %s", exc)
        page.goto(listing_url, wait_until="commit", timeout=30000)
        page.wait_for_timeout(2500)
        links = page.eval_on_selector_all("a[href]", "els => els.map(a => ({href:a.href, text:(a.innerText||'').trim()}))")
    wanted = {f"{day:%m%d%Y}" for day in days}
    result = []
    for item in links:
        href = item.get("href", "")
        title = item.get("text", "")
        match = INVESTOPEDIA_URL.search(href)
        if match and match.group(1) in wanted and len(title) > 20:
            if href not in result:
                result.append(href)
    return result


def discover_urls(day: date, page) -> dict[str, str]:
    """Discover exactly one candidate per source; never silently choose a mismatch."""
    # Investopedia URL의 날짜는 CNBC와 하루 차이로 표시되는 경우가 있어
    # 해당 거래일과 다음 날짜를 후보로 보되, 페이지 검증을 통과한 것만 사용한다.
    candidates: dict[str, list[str]] = {
        "CNBC": cnbc_candidate_urls(day),
        "Investopedia": _article_links(page, [day, day + timedelta(days=1)]),
    }
    urls: dict[str, str] = {}
    for source, values in candidates.items():
        valid = []
        for url in values:
            try:
                # URL 검증은 Chromium이 충돌해도 동작하도록 HTTP를 우선 사용한다.
                request_kwargs = {"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 30}
                if CURL_CFFI_AVAILABLE:
                    request_kwargs["impersonate"] = "chrome124"
                response = http_requests.get(url, **request_kwargs)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                title_node = soup.find("title") or soup.find("h1")
                title = title_node.get_text(" ", strip=True) if title_node else ""
                body = soup.get_text(" ", strip=True)
                body_head = body[:5000].lower()
                # 장중 페이지는 최종 마감 기사로 사용하지 않는다.
                intraday_markers = ("in early trading", "in recent trading", "before the bell", "stock futures")
                is_intraday = source == "Investopedia" and any(marker in body_head for marker in intraday_markers)
                target_marker = f"{day:%B} {day.day}, {day.year}".lower()
                target_marker_short = f"{day:%b} {day.day}, {day.year}".lower()
                target_marker_nocomma = f"{day:%b} {day.day} {day.year}".lower()
                has_target_update_date = target_marker in body_head or target_marker_short in body_head or target_marker_nocomma in body_head
                if response.url.startswith("https://") and not is_intraday and ("stock market" in title.lower() or "stock market" in body_head) and (source != "CNBC" or has_target_update_date):
                    valid.append(url)
            except Exception as exc:
                LOG.warning("%s 후보 HTTP 확인 실패: %s", source, exc)
                # HTTP가 차단된 경우에만 브라우저 검증을 시도한다.
                try:
                    page.goto(url, wait_until="commit", timeout=30000)
                    title = page.title() or ""
                    body = page.locator("body").inner_text(timeout=10000)
                    body_head = body[:5000].lower()
                    intraday_markers = ("in early trading", "in recent trading", "before the bell", "stock futures")
                    is_intraday = source == "Investopedia" and any(marker in body_head for marker in intraday_markers)
                    target_marker = f"{day:%B} {day.day}, {day.year}".lower()
                    target_marker_short = f"{day:%b} {day.day}, {day.year}".lower()
                    target_marker_nocomma = f"{day:%b} {day.day} {day.year}".lower()
                    has_target_update_date = target_marker in body_head or target_marker_short in body_head or target_marker_nocomma in body_head
                    if not is_intraday and ("stock market" in title.lower() or "stock market" in body_head) and (source != "CNBC" or has_target_update_date):
                        valid.append(url)
                except Exception as browser_exc:
                    LOG.warning("%s 후보 브라우저 확인 실패: %s", source, browser_exc)
        if len(valid) == 1:
            urls[source] = valid[0]
        elif len(valid) > 1:
            raise RuntimeError(f"{source}: 기준일과 일치하는 후보가 여러 개입니다: {valid}")
        else:
            LOG.warning("%s: 기준일 %s 기사 URL을 확인하지 못했습니다.", source, day)
    return urls


def extract_intro(page, url: str) -> tuple[str, str]:
    """Extract title plus the article intro, stopping at the first live update timestamp."""
    headers = HTTP_HEADERS
    html = ""
    document_title = ""
    raw_html = ""
    try:
        request_kwargs = {"headers": headers, "proxies": {"http": "", "https": ""}, "timeout": 30}
        if CURL_CFFI_AVAILABLE:
            request_kwargs["impersonate"] = "chrome124"
        response = http_requests.get(url, **request_kwargs)
        LOG.info("HTTP 응답 %s: status=%s bytes=%s", url, response.status_code, len(response.content))
        response.raise_for_status()
        raw_html = response.text
        soup_probe = BeautifulSoup(response.text, "html.parser")
        meta_title = soup_probe.find("meta", attrs={"property": "og:title"}) or soup_probe.find("meta", attrs={"name": "title"})
        document_title = (meta_title.get("content", "") if meta_title else (soup_probe.title.get_text(" ", strip=True) if soup_probe.title else ""))
        container = (
            soup_probe.select_one('[id^="liveBlog"]')
            or soup_probe.select_one('[id^="LiveStory-SpecialReport-featuredContent"]')
            or soup_probe.select_one('[class*="LiveStory-SpecialReport-featuredContent"]')
            or soup_probe.find("article")
            or soup_probe.find("main")
        )
        if container:
            html = str(container)
        elif "cnbc.com" in url:
            # CNBC가 featuredContent를 서버 HTML에 직접 넣지 않는 경우 JSON-LD 사용
            for script in soup_probe.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or script.get_text())
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and item.get("articleBody"):
                            html = "<article><h1>{}</h1>{}</article>".format(
                                item.get("headline", document_title),
                                "".join(f"<p>{p}</p>" for p in str(item["articleBody"]).split("\n\n") if p.strip()),
                            )
                            break
                except (json.JSONDecodeError, TypeError):
                    continue
                if html:
                    break
    except Exception as exc:
        LOG.warning("HTTP 본문 요청 실패(%s): %s", url, exc)

    # 서버 HTML에 본문이 없을 때만 브라우저 렌더링을 시도한다.
    if len(html) < 500 and "cnbc.com" in url:
        raise RuntimeError("CNBC 본문 HTML을 HTTP로 받지 못했습니다. 브라우저 fallback을 사용하지 않습니다.")
    if len(html) < 500:
        try:
            # 일부 CNBC 페이지는 광고/리다이렉트 단계에서 ERR_ABORTED를 반환하지만
            # DOM은 이미 일부 로드되어 있을 수 있으므로 계속 검사한다.
            page.goto(url, wait_until="commit", timeout=30000)
        except Exception as exc:
            LOG.warning("페이지 탐색 중 중단(%s): %s", url, exc)
        page.wait_for_timeout(2500)
        article_locator = page.locator('[id^="liveBlog"], [class*="LiveStory-SpecialReport-featuredContent"]')
        if article_locator.count() == 0:
            article_locator = page.locator("article")
        if article_locator.count() == 0:
            article_locator = page.locator("main")
        if article_locator.count() == 0:
            raise RuntimeError(f"기사 본문 컨테이너를 찾지 못했습니다: {url}")
        html = article_locator.first.inner_html(timeout=10000)

    soup = BeautifulSoup(html, "html.parser")
    # 이미지 캡션/크레딧은 기사 본문이 아니다.
    for node in soup.select("figure, figcaption, .image-caption, .mntl-figure-caption, .img-caption, [class*='InlineImage'], [class*='inlineImage'], [id^='ArticleBody-InlineImage']"):
        node.decompose()
    # Investopedia의 Value Add 구독 홍보 블록은 기사 본문이 아니다.
    for node in soup.find_all(["p", "div"]):
        text = node.get_text(" ", strip=True).lower()
        if text.startswith("go beyond the day’s market moves") or text.startswith("go beyond the day's market moves"):
            node.decompose()
    title_node = soup.find("h1") or soup.find("h2")
    if title_node:
        title = title_node.get_text(" ", strip=True)
    else:
        meta_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find("meta", attrs={"name": "title"})
        title = (meta_title.get("content", "") if meta_title else (document_title or (page.title() or ""))).strip()
    chunks: list[str] = []
    started = False
    for node in soup.find_all(["p", "h1", "h2", "h3", "h4"]):
        text = node.get_text(" ", strip=True)
        if not text:
            continue
        if DATE_HEADER.match(text):
            break
        # 첫 제목(h1) 뒤에 나오는 h2/h3/h4는 라이브 업데이트나 추천 기사다.
        if started and node.name in {"h2", "h3", "h4"}:
            break
        if text.lower() in {"tradingview", "getty images"} or " via getty images" in text.lower():
            continue
        if node.name == "h1":
            started = True
        if started and node.name == "p":
            chunks.append(text)
    if not chunks:
        # CNBC의 featuredContent는 문단이 div로만 구성되는 경우가 있다.
        fallback = soup.get_text(" ", strip=True)
        fallback = re.sub(r"\b(?:TradingView|Getty Images)\b", "", fallback, flags=re.I)
        fallback = re.sub(r"\s+", " ", fallback).strip()
        if len(fallback) > 200:
            chunks = [fallback]
        else:
            raise RuntimeError(f"본문 추출 실패 또는 라이브 업데이트 경계를 찾지 못했습니다: {url}")
    return title, "\n\n".join(chunks)


def append_articles(path: Path, articles: list[tuple[str, str, str]]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    new = []
    for source, title, body in articles:
        if title in existing or any(title in item for item in new):
            continue
        new.append(f"\n\n### {source}: {title}\n\n{body}\n")
    if new:
        path.write_text(existing.rstrip() + "\n" + "".join(new), encoding="utf-8")


def run(output: Path, append: bool = False, day: date | None = None) -> list[tuple[str, str, str]]:
    target_day = day or previous_us_weekday()
    with sync_playwright() as playwright:
        cdp_url = os.getenv("NEWS_CDP_URL", "").strip()
        owns_browser = not bool(cdp_url)
        if cdp_url:
            LOG.info("기존 Chrome CDP 세션에 연결: %s", cdp_url)
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            if not browser.contexts:
                raise RuntimeError("CDP Chrome에 사용할 브라우저 컨텍스트가 없습니다.")
            context = browser.contexts[0]
        else:
            LOG.info("NEWS_CDP_URL이 없어 임시 Chromium을 사용합니다.")
            browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
            context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36")
        page = context.new_page()
        # 라이브 페이지의 이미지·광고 리소스로 인한 Chromium 충돌을 줄인다.
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in {"image", "media", "font"} else route.continue_())
        try:
            urls = discover_urls(target_day, page)
            articles = []
            for source, url in urls.items():
                article_page = None
                try:
                    # 후보 탐색 탭과 본문 추출 탭을 분리한다.
                    article_page = context.new_page()
                    article_page.route("**/*", lambda route: route.abort() if route.request.resource_type in {"image", "media", "font"} else route.continue_())
                    title, body = extract_intro(article_page, url)
                    if source == "Investopedia":
                        body_lower = body.lower()
                        if any(marker in body_lower for marker in ("in early trading", "in recent trading", "before the bell", "stock futures")):
                            raise RuntimeError("장중 기사로 판정되어 마감 기사에서 제외했습니다.")
                    articles.append((source, title, body))
                except Exception as exc:
                    LOG.error("%s 본문 추출 실패(%s): %s", source, url, exc)
                finally:
                    if article_page:
                        try:
                            article_page.close()
                        except Exception:
                            pass
        finally:
            try:
                page.close()
            except Exception:
                pass
            if owns_browser:
                browser.close()
    if append:
        append_articles(output, articles)
    return articles


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--append", action="store_true", help="검증된 결과를 us_economy_news.md 하단에 추가")
    parser.add_argument("--output", type=Path, default=Path("data/output/us_economy_news.md"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    LOG.info("HTTP client: %s", "curl_cffi" if CURL_CFFI_AVAILABLE else "requests (curl_cffi 미설치)")
    articles = run(args.output, append=args.append)
    for source, title, body in articles:
        print(f"\n[{source}] {title}\n{body}\n")
    if not args.append:
        print("\n미리보기만 수행했습니다. 확인 후 --append로 파일에 추가하세요.")


if __name__ == "__main__":
    main()
