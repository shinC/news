import os
import logging
from typing import List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

def save_to_markdown(news_data: List[Dict[str, Any]], market_data: Dict[str, Any] = None,
                     report_title: str = "US Economy & Business News Report",
                     index_title: str = "주요 3대 지수 (전일 대비)",
                     output_filename: str = None) -> None:
    """
    수집된 시황 정보와 정렬된 뉴스 데이터를 마크다운 포맷으로 변환하여 파일로 저장합니다.
    """
    if not os.path.exists(settings.output_dir):
        os.makedirs(settings.output_dir)
        
    filename = output_filename if output_filename else settings.output_filename
    file_path = os.path.join(settings.output_dir, filename)
    
    # === 배치 및 폴백 디코딩 일괄 수행 ===
    from src.core.utils import batch_decode_google_urls, SEARCH_URL_CACHE, search_real_url_fallback
    import time
    
    is_kr = "Korea" in report_title or "한국" in report_title
    
    # 1단계: 검색 캐시(SEARCH_URL_CACHE)에서 제목을 기반으로 1차 치환
    for item in news_data:
        title = item.get('title', '')
        if title in SEARCH_URL_CACHE and item.get('url') and "news.google.com" in item['url']:
            item['url'] = SEARCH_URL_CACHE[title]
            
    if market_data and "top_stocks" in market_data:
        for stock in market_data.get("top_stocks", []):
            for item in stock.get('reason', []):
                if isinstance(item, dict) and item.get('url') and "news.google.com" in item['url']:
                    title = item.get('title', '')
                    if title in SEARCH_URL_CACHE:
                        item['url'] = SEARCH_URL_CACHE[title]
                        
    # 2단계: 여전히 구글 URL인 것들에 대해 배치 디코더(batch_decode_google_urls) 시도
    urls_to_decode = []
    for item in news_data:
        if item.get('url') and "news.google.com" in item['url']:
            urls_to_decode.append(item['url'])
    if market_data and "top_stocks" in market_data:
        for stock in market_data.get("top_stocks", []):
            for item in stock.get('reason', []):
                if isinstance(item, dict) and item.get('url') and "news.google.com" in item['url']:
                    urls_to_decode.append(item['url'])
                    
    if urls_to_decode:
        url_mapping = batch_decode_google_urls(urls_to_decode)
        for item in news_data:
            if item.get('url') in url_mapping:
                item['url'] = url_mapping[item['url']]
        if market_data and "top_stocks" in market_data:
            for stock in market_data.get("top_stocks", []):
                for item in stock.get('reason', []):
                    if isinstance(item, dict) and item.get('url') in url_mapping:
                        item['url'] = url_mapping[item['url']]
                        
    # 3단계: 최후의 수단으로 여전히 구글 URL인 것들에 대해 개별 검색 폴백 시도
    for item in news_data:
        url = item.get('url', '')
        if url and "news.google.com" in url:
            title = item.get('title', '')
            real_url = search_real_url_fallback(title, is_kr=is_kr)
            if real_url:
                item['url'] = real_url
                SEARCH_URL_CACHE[title] = real_url
                time.sleep(0.5)
                
    if market_data and "top_stocks" in market_data:
        for stock in market_data.get("top_stocks", []):
            for item in stock.get('reason', []):
                if isinstance(item, dict):
                    url = item.get('url', '')
                    if url and "news.google.com" in url:
                        title = item.get('title', '')
                        real_url = search_real_url_fallback(title, is_kr=is_kr)
                        if real_url:
                            item['url'] = real_url
                            SEARCH_URL_CACHE[title] = real_url
                            time.sleep(0.5)
    # ===================================
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{report_title}\n\n")
        
        # 시황 정보 기록 (market_data가 있을 경우)
        if market_data:
            f.write("📈 간편 시황 요약\n")
            f.write(f"> 데이터 출처: {market_data.get('source', 'Yahoo Finance (yfinance)')}\n\n")
            
            indices = market_data.get("indices", {})
            if indices:
                f.write(f"{index_title}\n")
                for name, info in indices.items():
                    sign = "+" if info['change_pct'] > 0 else ""
                    f.write(f"- {name}: {info['price']} ({sign}{info['change_pct']}%)\n")
                f.write("\n")
                
            top_themes_detailed = market_data.get("top_themes_detailed", [])
            bottom_sector = market_data.get("bottom_sector")
            
            if top_themes_detailed:
                f.write("주요 섹터 및 테마 동향\n")
                f.write("> 조건: 해당 테마 내 10% 이상 상승 또는 거래대금 1,000억 이상인 핵심 종목 요약\n\n")
                for i, theme in enumerate(top_themes_detailed):
                    icon = "🚀" if i == 0 else "📈"
                    formatted_stocks = []
                    for s in theme['stocks']:
                        if s.get("is_fallback"):
                            formatted_stocks.append(f"{s['name']}")
                        else:
                            formatted_stocks.append(f"{s['name']}({'+' if s['change_pct'] > 0 else ''}{s['change_pct']}%)")
                    
                    stock_list_str = ", ".join(formatted_stocks) if formatted_stocks else "해당 조건의 종목 없음"
                    f.write(f"{icon} {theme['name']} (+{round(theme['change_pct'], 2)}%)\n")
                    f.write(f"  - {stock_list_str}\n\n")
                
                if bottom_sector:
                    f.write(f"가장 부진한 섹터: {bottom_sector['name']} ({round(bottom_sector['change_pct'], 2)}%)\n")
                f.write("\n")
                
            top_stocks = market_data.get("top_stocks", [])
            if top_stocks:
                f.write("거래대금 기준 특징주 상위 100 (거래대금 순)\n")
                f.write("> 참고: 거래대금 상위 100개 종목 중 상승률 상위 20개 및 거래대금 상위 20개 종목에 대해 관련 뉴스를 검색하여 표 아래에 제공합니다.\n\n")
                f.write("| 순위 | 종목명 | 심볼 | 현재가 | 등락률(%) | 거래대금(대략) |\n")
                f.write("|---|---|---|---|---|---|\n")
                
                # 뉴스 수집 대상이 된 상위 10개 상승 종목만 따로 필터링
                stocks_with_news = []
                
                # 한국 시장 여부 확인
                is_kr = "Korea" in report_title or "한국" in report_title
                
                for i, stock in enumerate(top_stocks, 1):
                    ticker = stock['ticker']
                    name = stock.get('name', ticker)
                    price = stock['price']
                    change_pct = stock['change_pct']
                    trading_value = stock['trading_value']
                    reason = stock.get('reason', [])
                    
                    if reason: # 이유(뉴스 리스트)가 존재하면 따로 저장
                        stocks_with_news.append(stock)
                    
                    # 화폐 및 단위 설정
                    if is_kr:
                        # 가격 포맷 (천단위 콤마 + 원)
                        try:
                            formatted_price = f"{int(float(price)):,}원"
                        except:
                            formatted_price = f"{price}원"
                            
                        # 거래대금 포맷 (조/억 단위)
                        if trading_value >= 1e12:
                            cho = int(trading_value // 1e12)
                            eok = int((trading_value % 1e12) // 1e8)
                            tv_str = f"{cho}조 {eok:,}억원" if eok > 0 else f"{cho}조원"
                        else:
                            eok = int(trading_value // 1e8)
                            tv_str = f"{eok:,}억원"
                            
                        price_display = formatted_price
                    else:
                        # 미국 시장 (기존 방식)
                        if trading_value >= 1e9:
                            tv_str = f"${trading_value/1e9:.2f}B"
                        else:
                            tv_str = f"${trading_value/1e6:.2f}M"
                        price_display = f"${price}"
                        
                    sign = "+" if change_pct > 0 else ""
                    f.write(f"| {i} | {name} | {ticker} | {price_display} | {sign}{change_pct}% | {tv_str} |\n")
                f.write("\n")
                
                if stocks_with_news:
                    f.write("특징주 상승 이유 (관련 주요 뉴스)\n\n")
                    for stock in stocks_with_news:
                        ticker = stock['ticker']
                        name = stock.get('name', ticker)
                        sign = "+" if stock['change_pct'] > 0 else ""
                        change_pct_str = f"{sign}{stock['change_pct']}%"
                        trading_value = stock.get('trading_value', 0)
                        if is_kr:
                            if trading_value >= 1e12:
                                cho = int(trading_value // 1e12)
                                eok = int((trading_value % 1e12) // 1e8)
                                tv_str = f"{cho}조 {eok:,}억원" if eok > 0 else f"{cho}조원"
                            else:
                                eok = int(trading_value // 1e8)
                                tv_str = f"{eok:,}억원"
                        else:
                            if trading_value >= 1e9:
                                tv_str = f"${trading_value/1e9:.2f}B"
                            else:
                                tv_str = f"${trading_value/1e6:.2f}M"
                                
                        f.write(f"{name} ({ticker}) ({change_pct_str}) | 거래대금: {tv_str}\n")
                        reasons = stock.get('reason', [])
                        for item in reasons:
                            if isinstance(item, dict):
                                title = item.get('title', 'No Title')
                                url = item.get('url', '#')
                                pub_date = item.get('publish_date')
                                date_str = ""
                                if pub_date:
                                    try:
                                        # dateutil parser might produce naive or aware datetimes, but strftime works either way
                                        date_str = pub_date.strftime('%Y-%m-%d')
                                    except:
                                        date_str = str(pub_date)
                                
                                if date_str:
                                    f.write(f"- [{title}]({url}) [{date_str}]\n")
                                else:
                                    f.write(f"- [{title}]({url})\n")
                            else:
                                f.write(f"- {item}\n")
                        f.write("\n")
        
        f.write("---\n\n")
        
        # 마감시황 뉴스 분리
        macro_news_list = [item for item in news_data if item.get('category') == "Macro & Market"]
        other_news_list = [item for item in news_data if item.get('category') != "Macro & Market"]
        
        if macro_news_list:
            f.write("마감시황\n\n")
            for idx, item in enumerate(macro_news_list, 1):
                pub_date = item.get('publish_date')
                date_str = pub_date.strftime('%Y-%m-%d') if pd.notnull(pub_date) else "Unknown Date"
                title = item.get('title', 'No Title')
                url = item.get('url', '#')
                
                f.write(f"{idx}. [{title}]({url})\n")
                f.write(f"- 발행일시: {date_str}\n")
                summary = item.get('summary', '')
                if summary:
                    f.write(f"- 요약: {summary[:1500]}...\n")
                keywords = item.get('keywords', [])
                if not isinstance(keywords, list):
                    keywords = []
                filtered_keywords = [k for k in keywords if isinstance(k, str) and k.lower() not in ['google', 'news', 'home']]
                if filtered_keywords:
                    f.write(f"- 키워드: {', '.join(filtered_keywords)}\n")
                f.write("\n")
            f.write("---\n\n")
            
        f.write("주요 뉴스 헤드라인 (섹션별 & 중요도순)\n\n")
        
        if not other_news_list:
            f.write("수집된 뉴스가 없습니다.\n")
            return
            
        # 카테고리별로 그룹화
        grouped_news = {}
        for item in other_news_list:
            cat = item.get('category', '기타')
            if cat not in grouped_news:
                grouped_news[cat] = []
            grouped_news[cat].append(item)
            
        global_idx = 1
        for cat, items in grouped_news.items():
            f.write(f"{cat}\n\n")
            
            for item in items:
                cluster_id = item.get('cluster_id')
                cluster_size = item.get('cluster_size', 1)
                priority_score = item.get('priority_score', 0)
                
                pub_date = item.get('publish_date')
                date_str = pub_date.strftime('%Y-%m-%d') if pd.notnull(pub_date) else "Unknown Date"
                
                title = item.get('title', 'No Title')
                url = item.get('url', '#')
                
                # 기사 제목에 순번(번호) 추가
                f.write(f"{global_idx}. [{title}]({url})\n")
                f.write(f"- 발행일시: {date_str}\n")
                
                summary = item.get('summary', '')
                if summary:
                    f.write(f"- 요약: {summary[:1500]}...\n")
                    
                keywords = item.get('keywords', [])
                if not isinstance(keywords, list):
                    keywords = []
                if keywords:
                    # 'google' 단독 키워드 등 불필요한 키워드 필터링
                    filtered_keywords = [k for k in keywords if isinstance(k, str) and k.lower() not in ['google', 'news', 'home']]
                    if filtered_keywords:
                        f.write(f"- 키워드: {', '.join(filtered_keywords)}\n")
                
                f.write("\n")
                global_idx += 1
            
            f.write("---\n")
            
    logger.info(f"결과물이 {file_path} 에 저장되었습니다.")
    
# pandas is used in date_str check
import pandas as pd

def save_company_news_to_markdown(news_data: List[Dict[str, Any]], market_type: str = "us") -> None:
    """
    기업별 뉴스 검색 결과를 마크다운 포맷으로 변환하여 파일로 저장합니다.
    """
    if not os.path.exists(settings.output_dir):
        os.makedirs(settings.output_dir)
        
    filename = f"company_news_{market_type}.md"
    file_path = os.path.join(settings.output_dir, filename)
    
    # === 배치 및 폴백 디코딩 일괄 수행 ===
    from src.core.utils import batch_decode_google_urls, SEARCH_URL_CACHE, search_real_url_fallback
    import time
    
    is_kr = market_type == "kr"
    
    for item in news_data:
        title = item.get('title', '')
        if title in SEARCH_URL_CACHE and item.get('url') and "news.google.com" in item['url']:
            item['url'] = SEARCH_URL_CACHE[title]
            
    urls_to_decode = [item['url'] for item in news_data if item.get('url') and "news.google.com" in item['url']]
    if urls_to_decode:
        url_mapping = batch_decode_google_urls(urls_to_decode)
        for item in news_data:
            if item.get('url') in url_mapping:
                item['url'] = url_mapping[item['url']]
                
    for item in news_data:
        url = item.get('url', '')
        if url and "news.google.com" in url:
            title = item.get('title', '')
            real_url = search_real_url_fallback(title, is_kr=is_kr)
            if real_url:
                item['url'] = real_url
                SEARCH_URL_CACHE[title] = real_url
                time.sleep(0.5)
    # ===================================
    
    market_name = "미국" if market_type == "us" else "한국"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{market_name} 관심 기업 최신 뉴스 스크래핑 리포트\n\n")
        
        if not news_data:
            f.write("수집된 뉴스가 없습니다.\n")
            return
            
        # 기업별로 그룹화
        grouped_news = {}
        for item in news_data:
            comp = item.get('company', 'Unknown')
            if comp not in grouped_news:
                grouped_news[comp] = []
            grouped_news[comp].append(item)
            
        for comp, items in grouped_news.items():
            f.write(f"{comp}\n\n")
            
            for idx, item in enumerate(items, 1):
                pub_date = item.get('publish_date')
                date_str = pub_date.strftime('%Y-%m-%d') if pd.notnull(pub_date) else "Unknown Date"
                
                title = item.get('title', 'No Title')
                url = item.get('url', '#')
                
                f.write(f"{idx}. [{title}]({url})\n")
                f.write(f"- 발행일시: {date_str}\n")
                
                summary = item.get('summary', '')
                if summary:
                    f.write(f"- 요약: {summary[:1500]}...\n")
                    
                keywords = item.get('keywords', [])
                if keywords:
                    f.write(f"- 키워드: {', '.join(keywords)}\n")
                
                f.write("\n")
            
            f.write("---\n\n")
            
    logger.info(f"기업별 뉴스 스크래핑 결과가 {file_path} 에 저장되었습니다.")
