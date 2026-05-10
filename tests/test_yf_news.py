import yfinance as yf
ticker = yf.Ticker("MU")
print(ticker.news)
