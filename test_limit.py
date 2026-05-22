from src.core.kiwoom_api import KiwoomAPI
import logging

logging.basicConfig(level=logging.DEBUG)
api = KiwoomAPI()
api.get_token()

url = f"{api.base_url}/api/dostk/rkinfo"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api.token}",
    "api-id": "ka10032"
}

body = {
    "mrkt_tp": "000",
    "stex_tp": "3",
    "mang_stk_incls": "0",
    "data_limit": "200"
}
import requests
res = requests.post(url, headers=headers, json=body, timeout=10)
data = res.json().get("trde_prica_upper", [])
print(f"Fetched {len(data)} items with limit 200")
