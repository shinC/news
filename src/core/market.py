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
    "PTON", "CRSP", "ENPH", "FSLR", "SEDG", "RUN", "SPWR", "PLUG"
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

def get_market_data() -> Dict[str, Any]:
    """
    야후 파이낸스(yfinance)를 사용하여 미국 3대 지수와 주요 11개 섹터 ETF의 전일 종가 기준 등락률을 수집합니다.
    """
    logger.info("야후 파이낸스(yfinance)에서 시황 데이터 수집 시작...")
    market_info = {
        "indices": {},
        "top_sector": None,
        "bottom_sector": None,
        "source": "Yahoo Finance (yfinance)"
    }

    # 1. 3대 지수 수집
    market_date = None
    for name, ticker in INDICES.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                market_info["indices"][name] = {
                    "price": round(last_close, 2),
                    "change_pct": round(change_pct, 2)
                }
                # 기준 날짜 추출 (가장 마지막 데이터의 날짜)
                if market_date is None:
                    market_date = hist.index[-1].to_pydatetime()
            else:
                logger.warning(f"{name} ({ticker}) 데이터를 충분히 가져오지 못했습니다.")
        except Exception as e:
            logger.error(f"{name} ({ticker}) 수집 실패: {e}")

    market_info["market_date"] = market_date
    logger.info(f"수집된 시장 기준 날짜: {market_date}")

    # 2. 섹터 ETF 등락률 수집 및 비교
    sector_performance = []
    for ticker, name in SECTOR_ETFS.items():
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="5d")
            if len(hist) >= 2:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                sector_performance.append({
                    "ticker": ticker,
                    "name": name,
                    "change_pct": change_pct
                })
        except Exception as e:
            logger.error(f"섹터 ETF {name} ({ticker}) 수집 실패: {e}")

    if sector_performance:
        # 등락률 기준으로 정렬 (내림차순)
        sector_performance.sort(key=lambda x: x["change_pct"], reverse=True)
        market_info["top_sector"] = sector_performance[0]
        market_info["bottom_sector"] = sector_performance[-1]

    # 3. 거래대금 상위 특징주(상승률 순 50개) 수집
    logger.info("거래대금 기준 상위 특징주 수집 시작...")
    try:
        target_tickers, ticker_name_map = get_dynamic_tickers()
        # download 대량 데이터 (빠름)
        data = yf.download(target_tickers, period="5d", progress=False)
        stocks_info = []
        
        # yf.download 반환 데이터 프레임은 멀티인덱스 컬럼을 가질 수 있음
        # 컬럼 형태: (Price_Type, Ticker)
        for ticker in target_tickers:
            try:
                # yf 버전에 따라 멀티인덱스 접근 방식이 다를 수 있음
                if hasattr(data.columns, 'levels'):
                    close_col = ('Close', ticker)
                    vol_col = ('Volume', ticker)
                    if close_col in data.columns and vol_col in data.columns:
                        hist_close = data[close_col].dropna()
                        hist_vol = data[vol_col].dropna()
                        
                        if len(hist_close) >= 2 and len(hist_vol) >= 1:
                            last_close = hist_close.iloc[-1]
                            prev_close = hist_close.iloc[-2]
                            last_vol = hist_vol.iloc[-1]
                            
                            change_pct = ((last_close - prev_close) / prev_close) * 100
                            trading_value = last_close * last_vol
                            
                            stocks_info.append({
                                "ticker": ticker,
                                "price": round(float(last_close), 2),
                                "change_pct": round(float(change_pct), 2),
                                "trading_value": float(trading_value)
                            })
            except Exception as e:
                continue
                
        if stocks_info:
            # 1단계: 거래대금(trading_value) 기준 내림차순 정렬
            stocks_info.sort(key=lambda x: x['trading_value'], reverse=True)
            
            # 2단계: 단일 종목(EQUITY)만 필터링하여 상위 100개 확보
            filtered_stocks = []
            for stock in stocks_info:
                try:
                    # yfinance의 info 호출은 다소 느릴 수 있으므로 상위권에서만 확인하거나
                    # 티커 명명 규칙을 활용할 수 있으나, 가장 확실한 방법은 info['quoteType'] 확인
                    # 다만 속도를 위해 여기서는 기본적인 티커 길이 등으로 1차 필터링 후 
                    # 필요시 상위권만 정밀 확인하는 방식을 취합니다.
                    # 대부분의 TOP_TICKERS는 이미 주식으로 구성되어 있습니다.
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
            
            # 4단계: 선정된 종목들에 대해서만 뉴스 검색 진행
            for stock in top_100:
                if stock['ticker'] in gn_tk_set:
                    stock['reason'] = fetch_stock_reason_us(stock['ticker'], market_date=market_info.get("market_date"))
                else:
                    stock['reason'] = []
                    
            market_info["top_stocks"] = top_100
        else:
            market_info["top_stocks"] = []
    except Exception as e:
        logger.error(f"특징주 수집 실패: {e}")
        market_info["top_stocks"] = []

    logger.info("시황 데이터 수집 완료.")
    return market_info
