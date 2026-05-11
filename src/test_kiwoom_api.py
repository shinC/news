import logging
from src.core.kiwoom_api import KiwoomAPI

logging.basicConfig(level=logging.INFO)
kiwoom = KiwoomAPI()
stocks = kiwoom.get_top_trading_value("000")
print(f"Total stocks: {len(stocks)}")
if stocks:
    print(f"Top 1: {stocks[0]}")
