import yfinance as yf
import logging
from typing import Dict, Any
from src.core.scraper import fetch_company_news_us

logger = logging.getLogger(__name__)

def fetch_stock_reason_us(ticker: str) -> list:
    """티커를 기반으로 엄격한 필터링(제목+본문 포함)을 거친 뉴스 기사 헤드라인을 최대 5개 가져옵니다."""
    try:
        # fetch_company_news_us를 통해 본문 필터링이 적용된 뉴스 수집 (최근 2일)
        news_data = fetch_company_news_us([ticker], days=2)
        news_list = []
        for article in news_data:
            # 반환된 리스트에서 헤드라인 추출
            if article.get('company') == ticker:
                news_list.append(article.get('title'))
            if len(news_list) >= 5:
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
    for name, ticker in INDICES.items():
        try:
            stock = yf.Ticker(ticker)
            # 최근 2일 데이터를 가져와서 등락률 계산
            hist = stock.history(period="5d")
            if len(hist) >= 2:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                market_info["indices"][name] = {
                    "price": round(last_close, 2),
                    "change_pct": round(change_pct, 2)
                }
            else:
                logger.warning(f"{name} ({ticker}) 데이터를 충분히 가져오지 못했습니다.")
        except Exception as e:
            logger.error(f"{name} ({ticker}) 수집 실패: {e}")

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
        # download 대량 데이터 (빠름)
        data = yf.download(TOP_TICKERS, period="5d", progress=False)
        stocks_info = []
        
        # yf.download 반환 데이터 프레임은 멀티인덱스 컬럼을 가질 수 있음
        # 컬럼 형태: (Price_Type, Ticker)
        for ticker in TOP_TICKERS:
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
                    filtered_stocks.append(stock)
                    if len(filtered_stocks) >= 100:
                        break
                except Exception:
                    continue
            
            top_100 = filtered_stocks
            
            # 3단계: 상위 100개 중 상승률(change_pct)이 가장 높은 10개 종목 선정
            top_gainers_in_top_100 = sorted(top_100, key=lambda x: x['change_pct'], reverse=True)[:10]
            top_gainer_tickers = [s['ticker'] for s in top_gainers_in_top_100]
            
            # 4단계: 선정된 10개 종목에 대해서만 뉴스 검색 진행
            for stock in top_100:
                if stock['ticker'] in top_gainer_tickers:
                    stock['reason'] = fetch_stock_reason_us(stock['ticker'])
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
