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

# Try KOSPI
body_kospi = {
    "mrkt_tp": "0",  # 0: KOSPI?
    "stex_tp": "1",  # 1: KRX?
    "mang_stk_incls": "0",
    "data_limit": "100"
}
res_kospi = requests.post(url, headers=headers, json=body_kospi, timeout=10)
print("KOSPI:", len(res_kospi.json().get("trde_prica_upper", [])))

# Try KOSDAQ
body_kosdaq = {
    "mrkt_tp": "10", # 10: KOSDAQ?
    "stex_tp": "1",  
    "mang_stk_incls": "0",
    "data_limit": "100"
}
res_kosdaq = requests.post(url, headers=headers, json=body_kosdaq, timeout=10)
print("KOSDAQ:", len(res_kosdaq.json().get("trde_prica_upper", [])))
