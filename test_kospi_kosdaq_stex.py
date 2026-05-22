from src.core.kiwoom_api import KiwoomAPI
api = KiwoomAPI()
api.get_token()

kospi = api.get_top_trading_value("0")
kosdaq = api.get_top_trading_value("10")
print(f"KOSPI: {len(kospi)}, KOSDAQ: {len(kosdaq)}")
