import asyncio
import os
from dotenv import load_dotenv
import requests

load_dotenv()

def fetch_data(stex_tp):
    url = "https://api.kiwoom.com/oauth2/token"
    body = {
        "grant_type": "client_credentials",
        "appkey": os.getenv("KIWOOM_APP_KEY"),
        "secretkey": os.getenv("KIWOOM_SECRET_KEY")
    }
    res = requests.post(url, json=body)
    token = res.json().get("token")
    
    url = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10032"
    }
    body = {
        "mrkt_tp": "000",
        "stex_tp": stex_tp,
        "mang_stk_incls": "0",
        "data_limit": "5"
    }
    res = requests.post(url, headers=headers, json=body)
    return res.json().get("trde_prica_upper", [])

if __name__ == "__main__":
    print("=== stex_tp=3 (통합) ===")
    data_3 = fetch_data("3")
    for d in data_3[:5]:
        print(d.get("stk_nm"), d.get("cur_prc"), d.get("trde_prica"))
        
    print("=== stex_tp=1 (KRX) ===")
    data_1 = fetch_data("1")
    for d in data_1[:5]:
        print(d.get("stk_nm"), d.get("cur_prc"), d.get("trde_prica"))
