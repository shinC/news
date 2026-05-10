from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

def get_top_trading_value_stocks(date_str=None):
    if date_str is None:
        # 최근 영업일 찾기 (최대 10일 전까지)
        curr = datetime.now()
        for i in range(10):
            target_date = (curr - timedelta(days=i)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_ticker(target_date, market="ALL")
            if not df.empty:
                print(f"데이터 수집 날짜: {target_date}")
                break
    else:
        df = stock.get_market_ohlcv_by_ticker(date_str, market="ALL")
    
    if df.empty:
        print("데이터를 찾을 수 없습니다.")
        return
    
    # 거래대금 순 정렬
    df = df.sort_values(by='거래대금', ascending=False)
    
    # 티커(종목코드)를 종목명으로 변환
    results = []
    for ticker, row in df.head(50).iterrows():
        name = stock.get_market_ticker_name(ticker)
        results.append({
            "ticker": name,
            "price": row['종가'],
            "change_pct": row['등락률'],
            "trading_value": row['거래대금']
        })
    
    for i, res in enumerate(results, 1):
        print(f"{i}. {res['ticker']} - 가격: {res['price']}, 등락: {res['change_pct']}%, 거래대금: {res['trading_value']/1e8:.2f}억")

if __name__ == "__main__":
    get_top_trading_value_stocks()
