import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List
import urllib.parse
from src.core.kiwoom_api import KiwoomAPI

logger = logging.getLogger(__name__)

ETF_KEYWORDS = [
    "KODEX", "TIGER", "HANARO", "ACE", "SOL", "RISE", "KOSEF", "ARIRANG", 
    "KBSTAR", "PLUS", "WON", "KIWOOM", "HIT", "KINDEX", "ETN", 
    "선물", "인버스", "레버리지"
]

def is_etf(name: str) -> bool:
    """종목명에 ETF/ETN 관련 키워드가 포함되어 있는지 확인합니다."""
    name_upper = name.upper().replace(" ", "")
    for kw in ETF_KEYWORDS:
        if kw in name_upper:
            return True
    return False

from src.core.scraper_kr import fetch_company_news_kr

def fetch_stock_reason_kr(stock_name: str) -> List[str]:
    """종목명 기반으로 엄격한 필터링(제목+본문 포함)을 거친 뉴스 기사 헤드라인을 최대 5개 가져옵니다."""
    try:
        # fetch_company_news_kr를 통해 본문 필터링이 적용된 뉴스 수집 (최근 2일)
        news_data = fetch_company_news_kr([stock_name], days=2)
        news_list = []
        for article in news_data:
            # 반환된 리스트에서 헤드라인 추출
            if article.get('company') == stock_name:
                news_list.append(article.get('title'))
            if len(news_list) >= 5:
                break
        return news_list
    except Exception as e:
        logger.error(f"상승 이유 검색 실패 ({stock_name}): {e}")
    return []

def _fetch_sise_market_sum(sosok_id: int, pages: int = 10) -> List[Dict[str, Any]]:
    """KOSPI(0) 또는 KOSDAQ(1)의 시가총액 상위 종목들을 수집합니다. (거래대금 순위 정확도 향상을 위함)"""
    stocks = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    for page in range(1, pages + 1):
        url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok_id}&page={page}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'lxml')
            table = soup.find('table', {'class': 'type_2'})
            if not table:
                continue
            
            rows = table.find_all('tr')
            for r in rows:
                tds = r.find_all('td')
                if len(tds) >= 12: # 시가총액 페이지는 컬럼이 많음
                    try:
                        name = tds[1].text.strip()
                        if not name or is_etf(name):
                            continue
                        
                        price_str = tds[2].text.strip().replace(",", "")
                        # 등락률은 5번째 컬럼 (N, 종목명, 현재가, 전일비, 등락률...)
                        change_pct_str = tds[4].text.strip().replace("%", "").replace("+", "")
                        # 거래대금은 10번째 컬럼 근처 (보통 거래량, 거래대금, 전일거래량 순)
                        # 시총 페이지: 0:N, 1:종목명, 2:현재가, 3:전일비, 4:등락률, 5:액면가, 6:시가총액, 7:상장주식수, 8:외인비율, 9:거래량, 10:PER, 11:ROE
                        # 아, 시총 페이지엔 '거래대금'이 기본으로 안 나올 수 있습니다. 
                        # 필드를 선택해야 함: &field=amount (거래대금)
                        # 필드 추가 URL: ...&field=amount&field=market_sum
                        pass
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"네이버 시총 수집 실패: {e}")
    return stocks

def _fetch_accurate_stocks() -> List[Dict[str, Any]]:
    """시가총액 상위 1,000개(KOSPI 500, KOSDAQ 500)를 수집하여 정확한 거래대금 순위를 뽑습니다."""
    stocks = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    # field=amount (거래대금) 필드를 명시적으로 요청
    for sosok in [0, 1]:
        for page in range(1, 11): # 10페이지 = 500개
            url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}&field=amount"
            try:
                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'lxml')
                table = soup.find('table', {'class': 'type_2'})
                if not table: continue
                
                rows = table.find_all('tr')
                for r in rows:
                    tds = r.find_all('td')
                    if len(tds) >= 10:
                        try:
                            name = tds[1].text.strip()
                            if not name or is_etf(name): continue
                            
                            price_val = float(tds[2].text.strip().replace(",", ""))
                            change_pct = float(tds[4].text.strip().replace("%", "").replace("+", ""))
                            # 시총 페이지 기본 컬럼: 거래량(9)
                            volume_val = float(tds[9].text.strip().replace(",", ""))
                            
                            stocks.append({
                                "ticker": name,
                                "price": str(int(price_val)),
                                "change_pct": change_pct,
                                "trading_value": price_val * volume_val
                            })
                        except (ValueError, IndexError):
                            continue
            except Exception as e:
                logger.error(f"네이버 정밀 수집 실패: {e}")
    return stocks

def get_market_data() -> Dict[str, Any]:
    """
    네이버 증권 웹 크롤링을 통해 한국 시황 데이터(지수, 특징주, 테마)를 수집합니다.
    """
    logger.info("네이버 증권(Naver Finance)에서 시황 데이터 수집 시작...")
    market_info = {
        "indices": {},
        "top_sector": None,
        "bottom_sector": None,
        "top_stocks": [],
        "source": "Naver Finance (네이버 금융)"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    # 1. 3대 지수 수집
    try:
        url_sise = "https://finance.naver.com/sise/"
        res = requests.get(url_sise, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        indices_map = {
            "KOSPI": ("KOSPI_now", "KOSPI_change"),
            "KOSDAQ": ("KOSDAQ_now", "KOSDAQ_change"),
            "KOSPI200": ("KPI200_now", "KPI200_change")
        }
        
        for name, (id_now, id_change) in indices_map.items():
            now_elem = soup.select_one(f"#{id_now}")
            change_elem = soup.select_one(f"#{id_change}")
            if now_elem and change_elem:
                price = now_elem.text.strip()
                change_texts = change_elem.text.split()
                change_pct = "0.00"
                for t in change_texts:
                    if "%" in t:
                        change_pct = t.replace("%", "").replace("상승", "").replace("하락", "").replace("보합", "")
                        break
                
                sign = -1 if "하락" in change_elem.text or "-" in change_elem.text else 1
                try:
                    change_pct_float = float(change_pct.replace("+", "").replace("-", "")) * sign
                except ValueError:
                    change_pct_float = 0.0

                market_info["indices"][name] = {
                    "price": price,
                    "change_pct": change_pct_float
                }
    except Exception as e:
        logger.error(f"지수 수집 실패: {e}")

    # 2. 테마 (섹터) 등락률 수집
    try:
        url_theme = "https://finance.naver.com/sise/theme.naver"
        res = requests.get(url_theme, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        table = soup.find('table', {'class': 'type_1 theme'})
        if table:
            rows = table.find_all('tr')
            themes = []
            for r in rows:
                tds = r.find_all('td')
                if len(tds) >= 3:
                    theme_name = tds[0].text.strip()
                    change_pct_str = tds[1].text.strip().replace("%", "").replace("+", "").replace("-", "")
                    if not change_pct_str: continue
                    sign = -1 if "-" in tds[1].text else 1
                    try:
                        change_pct = float(change_pct_str) * sign
                        themes.append({"name": theme_name, "change_pct": change_pct})
                    except ValueError: continue
            
            if themes:
                themes.sort(key=lambda x: x["change_pct"], reverse=True)
                market_info["top_sector"] = themes[0]
                market_info["bottom_sector"] = themes[-1]
    except Exception as e:
        logger.error(f"테마 데이터 수집 실패: {e}")

    # 3. KOSPI/KOSDAQ 통합 거래대금 상위 100개 수집
    try:
        # 1순위: 키움 API 사용
        kiwoom = KiwoomAPI()
        all_stocks = kiwoom.get_top_trading_value("000")
        
        # 2순위: 키움 API 실패 시 고급 크롤링 (시총 상위 1,000개 기반)
        if not all_stocks:
            logger.info("키움 API 실패 또는 미설정으로 네이버 고급 크롤링을 수행합니다.")
            all_stocks = _fetch_accurate_stocks()
        
        if all_stocks:
            # 중복 제거 (티커 기준)
            seen = set()
            unique_stocks = []
            for s in all_stocks:
                if s["ticker"] not in seen:
                    unique_stocks.append(s)
                    seen.add(s["ticker"])
            
            # 1단계: 거래대금 순 정렬 후 상위 100개 추출
            unique_stocks.sort(key=lambda x: x["trading_value"], reverse=True)
            top_100 = unique_stocks[:100]
            
            # 2단계: 상위 100개 중 상승률이 가장 높은 10개 종목 선정
            top_gainers_in_top_100 = sorted(top_100, key=lambda x: x["change_pct"], reverse=True)[:10]
            top_gainer_names = [s["ticker"] for s in top_gainers_in_top_100]
            
            # 3단계: 선정된 10개 종목에 대해서만 이유 검색
            for stock in top_100:
                if stock["ticker"] in top_gainer_names:
                    stock["reason"] = fetch_stock_reason_kr(stock["ticker"])
                else:
                    stock["reason"] = []
            
            # 최종 정렬 상태는 '거래대금 순' 유지
            market_info["top_stocks"] = top_100
    except Exception as e:
        logger.error(f"특징주 수집 실패: {e}")

    logger.info("네이버 증권 시황 데이터 수집 완료.")
    return market_info
