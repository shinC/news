import yfinance as yf
import logging
import pandas as pd
import requests
from io import StringIO
from typing import Dict, Any
from src.core.scraper import fetch_company_news_us

logger = logging.getLogger(__name__)

def fetch_stock_reason_us(ticker: str, market_date=None) -> list:
    """티커를 기반으로 엄격한 필터링(제목+본문 포함)을 거친 뉴스 기사 헤드라인을 최대 5개 가져옵니다."""
    try:
        # fetch_company_news_us를 통해 본문 필터링이 적용된 뉴스 수집 (최근 3일)
        news_data = fetch_company_news_us([ticker], days=3, market_date=market_date)
        news_list = []
        for article in news_data:
            # 반환된 리스트에서 헤드라인 추출
            if article.get('company') == ticker:
                news_list.append({
                    "title": article.get('title'),
                    "url": article.get('url'),
                    "publish_date": article.get('publish_date')
                })
            if len(news_list) >= 10:
                break
        return news_list
    except Exception as e:
        logger.error(f"상승 이유 검색 실패 ({ticker}): {e}")
    return []

# 주요 3대 지수 티커
INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI"
}

# 미국 주요 11개 산업 섹터 ETF 티커
SECTOR_ETFS = {
    "XLK": "Technology (기술)",
    "XLF": "Financials (금융)",
    "XLV": "Health Care (헬스케어)",
    "XLE": "Energy (에너지)",
    "XLY": "Consumer Discretionary (임의소비재)",
    "XLI": "Industrials (산업재)",
    "XLC": "Communication Services (통신)",
    "XLP": "Consumer Staples (필수소비재)",
    "XLU": "Utilities (유틸리티)",
    "XLB": "Materials (소재)",
    "XLRE": "Real Estate (부동산)"
}

# 고거래대금 대용으로 사용할 주요 기술주 및 대형주 티커 (Nasdaq 100 및 주요 S&P 500)
TOP_TICKERS = [
    "AAPL", "MSFT", "AMZN", "NVDA", "META", "TSLA", "GOOGL", "GOOG", "AVGO", "PEP",
    "COST", "CSCO", "TMUS", "ADBE", "TXN", "CMCSA", "AMD", "NFLX", "INTC", "INTU",
    "QCOM", "AMGN", "HON", "AMAT", "SBUX", "BKNG", "ISRG", "MDLZ", "GILD", "LRCX",
    "ADI", "VRTX", "REGN", "PANW", "ADP", "SNPS", "KLAC", "CSX", "CDNS", "MELI",
    "MU", "PYPL", "MAR", "MNST", "ORLY", "ASML", "CTAS", "CHTR", "NXPI", "PDD",
    "LULU", "DXCM", "KDP", "CRWD", "ABNB", "MRVL", "FTNT", "PCAR", "MCHP", "KHC",
    "PAYX", "IDXX", "ROST", "AEP", "CTSH", "EXC", "EA", "BIIB", "AZN", "FAST",
    "CEG", "VRSK", "CPRT", "ODFL", "WBD", "CSGP", "BKR", "DDOG", "TEAM", "WDAY",
    "ZS", "ALGN", "EBAY", "SIRI", "ILMN", "MTCH", "ZM", "OKTA", "DOCU", "MDB",
    "PTON", "CRSP", "ENPH", "FSLR", "SEDG", "RUN", "SPWR", "PLUG", "SPCX", "SKHYV"
]

def get_dynamic_tickers() -> tuple[list, dict]:
    """위키피디아에서 S&P 500과 Nasdaq 100 티커를 동적으로 수집하고, 주요 인기 티커를 추가합니다. 티커와 종목명 딕셔너리를 함께 반환합니다."""
    ticker_name_map = {}
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        # S&P 500
        res_sp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers, timeout=10)
        sp500_df = pd.read_html(StringIO(res_sp.text))[0]
        sp500 = sp500_df['Symbol'].tolist()
        for _, row in sp500_df.iterrows():
            ticker_name_map[row['Symbol'].replace('.', '-')] = row['Security']
        
        # Nasdaq 100
        res_ndx = requests.get('https://en.wikipedia.org/wiki/Nasdaq-100', headers=headers, timeout=10)
        tables = pd.read_html(StringIO(res_ndx.text))
        nasdaq100 = []
        for t in tables:
            if 'Ticker' in t.columns:
                nasdaq100 = t['Ticker'].tolist()
                if 'Company' in t.columns:
                    for _, row in t.iterrows():
                        ticker_name_map[row['Ticker'].replace('.', '-')] = row['Company']
                break
                
        # 인기 특징주 (위 지수에 없을 수 있는 종목들) - Yahoo Finance Most Actives 250개 동적 수집
        extra = []
        try:
            url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
            params = {"scrIds": "most_actives", "count": 250}
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                quotes = resp.json().get('finance', {}).get('result', [{}])[0].get('quotes', [])
                extra = [q['symbol'] for q in quotes if 'symbol' in q]
                for q in quotes:
                    if 'symbol' in q and 'shortName' in q:
                        ticker_name_map[q['symbol'].replace('.', '-')] = q['shortName']
        except Exception as api_e:
            logger.warning(f"Yahoo API most_actives 수집 실패: {api_e}")
            extra = ["PLTR", "ARM", "COIN", "RIVN", "SMCI", "SOUN", "DJT", "HOOD", "RDDT", "MSTR", "WDC", "SNDK"]
        
        combined = list(set(sp500 + nasdaq100 + extra + TOP_TICKERS))
        # yfinance 티커 형식에 맞춤 (예: BRK.B -> BRK-B)
        combined = [t.replace('.', '-') for t in combined]
        logger.info(f"동적 티커 수집 완료: 총 {len(combined)}개 종목")
        return combined, ticker_name_map
    except Exception as e:
        logger.warning(f"동적 티커 수집 실패, 기본 TOP_TICKERS로 대체합니다: {e}")
        return TOP_TICKERS, {}

def fetch_ticker_data(t: yf.Ticker):
    """fast_info를 최우선으로 시도하고, Rate Limit (429) 발생 시 history(period='2d')로 차단을 우회하여 수집합니다."""
    lp, pc, vol = None, None, None
    try:
        fi = t.fast_info
        lp = fi.last_price
        pc = getattr(fi, 'regular_market_previous_close', None) or fi.previous_close
        vol = fi.last_volume
    except Exception:
        pass

    if lp is None or pc is None:
        try:
            hist = t.history(period="2d")
            if len(hist) >= 2:
                pc = float(hist['Close'].iloc[-2])
                lp = float(hist['Close'].iloc[-1])
                vol = float(hist['Volume'].iloc[-1])
            elif len(hist) == 1:
                lp = float(hist['Close'].iloc[-1])
                pc = lp
                vol = float(hist['Volume'].iloc[-1])
        except Exception:
            pass

    if lp is not None and pc is not None and pc > 0:
        cp = ((lp - pc) / pc) * 100
        return lp, pc, cp, vol
    return None, None, None, None

def get_market_data() -> Dict[str, Any]:
    """
    야후 파이낸스(yfinance)의 공식 마감 종가를 안전하게 병렬 수집하여 미국 3대 지수, 주요 11개 섹터 ETF,
    그리고 거래대금 상위 특징주의 공식 정규장 종가와 등락률을 수집합니다.
    - Rate Limited (429) 차단 시 history(period='2d') 우회 폴백을 자동 실행합니다.
    """
    logger.info("야후 파이낸스(yfinance) 공식 정규장 데이터 수집 시작...")
    from concurrent.futures import ThreadPoolExecutor

    market_info = {
        "indices": {},
        "top_sector": None,
        "bottom_sector": None,
        "source": "Yahoo Finance Official (fast_info + history fallback)"
    }

    # 1. 주요 3대 지수 수집
    logger.info("1단계: 주요 3대 지수 공식 마감 데이터 수집 중...")
    market_date = None
    for name, ticker in INDICES.items():
        try:
            t = yf.Ticker(ticker)
            lp, pc, change_pct, _ = fetch_ticker_data(t)
            if lp is not None and change_pct is not None:
                market_info["indices"][name] = {
                    "price": round(float(lp), 2),
                    "change_pct": round(float(change_pct), 2)
                }
            else:
                logger.error(f"지수 {name}({ticker})의 공식 종가 데이터가 없습니다.")
        except Exception as e:
            logger.error(f"지수 {name}({ticker}) 수집 실패: {e}")

    if len(market_info["indices"]) < 3:
        raise RuntimeError(f"주요 3대 지수 공식 데이터 수집 실패! (수집 성공: {len(market_info['indices'])}/3). 중단합니다.")

    # 2. 섹터 ETF 등락률 수집
    logger.info("2단계: 11개 섹터 ETF 공식 마감 데이터 수집 중...")
    def fetch_etf(item):
        ticker, name = item
        try:
            t = yf.Ticker(ticker)
            _, _, cp, _ = fetch_ticker_data(t)
            if cp is not None:
                return {"ticker": ticker, "name": name, "change_pct": round(float(cp), 2)}
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=11) as ex:
        sector_results = list(ex.map(fetch_etf, SECTOR_ETFS.items()))
    sector_performance = [s for s in sector_results if s]

    if not sector_performance:
        raise RuntimeError("섹터 ETF 공식 데이터 수집에 실패했습니다. 중단합니다.")

    sector_performance.sort(key=lambda x: x["change_pct"], reverse=True)
    market_info["top_sector"] = sector_performance[0]
    market_info["bottom_sector"] = sector_performance[-1]

    # 3. 거래대금 상위 특징주 수집
    logger.info("3단계: 거래대금 상위 특징주 공식 마감 데이터 수집 중...")
    target_tickers, ticker_name_map = get_dynamic_tickers()

    def fetch_stock(ticker):
        try:
            t = yf.Ticker(ticker)
            lp, pc, cp, vol = fetch_ticker_data(t)
            if lp is not None and cp is not None and lp > 0:
                tv = lp * (vol if vol else 0)
                return {
                    "ticker": ticker,
                    "price": round(float(lp), 2),
                    "change_pct": round(float(cp), 2),
                    "trading_value": float(tv)
                }
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=25) as ex:
        stock_results = list(ex.map(fetch_stock, target_tickers))

    stocks_info = [s for s in stock_results if s]
    logger.info(f"특징주 수집 완료: 총 {len(stocks_info)}개 종목 유효 데이터 확보")

    if len(stocks_info) < 20:
        raise RuntimeError(f"특징주 공식 데이터 수집 실패! 유효 종목 수가 너무 적습니다 ({len(stocks_info)}개). 임의 대체 없이 중단합니다.")

    # 기준 날짜 추출 (최신 거래일)
    try:
        sample_hist = yf.Ticker("^GSPC").history(period="1d")
        if not sample_hist.empty:
            market_info["market_date"] = sample_hist.index[-1].to_pydatetime()
    except Exception:
        market_info["market_date"] = None
                
    if stocks_info:
        # 1단계: 거래대금(trading_value) 기준 내림차순 정렬
        stocks_info.sort(key=lambda x: x['trading_value'], reverse=True)
        
        # 2단계: 단일 종목(EQUITY)만 필터링하여 상위 100개 확보
        filtered_stocks = []
        for stock in stocks_info:
            try:
                stock['name'] = ticker_name_map.get(stock['ticker'], stock['ticker'])
                filtered_stocks.append(stock)
                if len(filtered_stocks) >= 100:
                    break
            except Exception:
                continue
        
        top_100 = filtered_stocks
        
        # 3단계: 상위 100개 중 상승률 상위 20개 및 거래대금 상위 20개 선정 (중복 제거)
        top_gn = sorted(top_100, key=lambda x: x['change_pct'], reverse=True)[:20]
        top_vol = top_100[:20]
        gn_tk_set = set([s['ticker'] for s in top_gn] + [s['ticker'] for s in top_vol])
        
        # 4단계: 선정된 종목들에 대해서만 뉴스 검색 병렬 진행
        def get_reason(stock):
            if stock['ticker'] in gn_tk_set:
                stock['reason'] = fetch_stock_reason_us(stock['ticker'], market_date=market_info.get("market_date"))
            else:
                stock['reason'] = []
            return stock

        with ThreadPoolExecutor(max_workers=6) as ex:
            top_100 = list(ex.map(get_reason, top_100))
                
        market_info["top_stocks"] = top_100
    else:
        market_info["top_stocks"] = []

    logger.info("시황 데이터 수집 완료.")
    return market_info
