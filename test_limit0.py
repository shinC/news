from src.core.kiwoom_api import KiwoomAPI
import requests
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
    "data_limit": "0"
}
res = requests.post(url, headers=headers, json=body, timeout=10)
print("Limit 0:", len(res.json().get("trde_prica_upper", [])))
