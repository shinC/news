from src.core.kiwoom_api import KiwoomAPI
api = KiwoomAPI()
api.get_token()

res_0 = api.get_top_trading_value("0")
res_10 = api.get_top_trading_value("10")
res_001 = api.get_top_trading_value("001")
res_101 = api.get_top_trading_value("101")

print(f"0: {len(res_0)}, 10: {len(res_10)}, 001: {len(res_001)}, 101: {len(res_101)}")
# Let's check first item of 0 vs 001, and 10 vs 101
if res_0 and res_001:
    print("0 first:", res_0[0]['ticker'])
    print("001 first:", res_001[0]['ticker'])
if res_10 and res_101:
    print("10 first:", res_10[0]['ticker'])
    print("101 first:", res_101[0]['ticker'])
