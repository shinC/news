import yfinance as yf
import pandas as pd

def get_top_stocks():
    # Wikipedia에서 S&P 500 티커 가져오기
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    sp500_df = tables[0]
    tickers = sp500_df['Symbol'].tolist()
    # yfinance는 BRK.B, BF.B를 다르게 처리함
    tickers = [t.replace('.', '-') for t in tickers]
    
    # yf.download로 대량 가져오기 (기간을 최근 5일로)
    data = yf.download(tickers, period="5d", progress=False)
    
    # 필요한 데이터: 마지막 거래일의 Volume, Close
    if len(data['Close']) >= 2:
        last_close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        volume = data['Volume'].iloc[-1]
        
        # 거래대금 = Volume * Close
        trading_value = volume * last_close
        
        # 등락률
        change_pct = ((last_close - prev_close) / prev_close) * 100
        
        df = pd.DataFrame({
            'TradingValue': trading_value,
            'ChangePct': change_pct,
            'Close': last_close
        })
        
        # 결측치 제거
        df = df.dropna()
        
        # 1. 거래대금 상위 종목 필터링 (예: 상위 100개)
        top_volume_df = df.sort_values(by='TradingValue', ascending=False).head(100)
        
        # 2. 그 중 상승률 순위 50개
        top_stocks_df = top_volume_df.sort_values(by='ChangePct', ascending=False).head(50)
        
        results = []
        for ticker, row in top_stocks_df.iterrows():
            results.append({
                "ticker": ticker,
                "price": round(row['Close'], 2),
                "change_pct": round(row['ChangePct'], 2),
                "trading_value": row['TradingValue']
            })
            
        print(f"Got {len(results)} stocks")
        print(results[:2])

get_top_stocks()
