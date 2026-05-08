import yfinance as yf
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

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

    logger.info("시황 데이터 수집 완료.")
    return market_info
