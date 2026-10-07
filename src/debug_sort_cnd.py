import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def get_token():
    app_key = os.getenv("KIWOOM_APP_KEY")
    secret_key = os.getenv("KIWOOM_SECRET_KEY")
    url = "https://api.kiwoom.com/oauth2/token"
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "secretkey": secret_key
    }
    res = requests.post(url, json=body)
    return res.json().get("token")

def test_sort_cnd():
    token = get_token()
    url = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10062"
    }

    date_str = "20261006"

    for sort_val in ["1", "2", "3", "4", "5"]:
        time.sleep(0.5)
        body = {
            "mrkt_tp": "001",    # 코스피
            "stex_tp": "1",      # KRX
            "amt_qty_tp": "0",   # 금액
            "trde_tp": "1",      # 순매수
            "sort_cnd": sort_val,
            "unit_tp": "1",
            "strt_dt": date_str,
            "end_dt": date_str
        }
        res = requests.post(url, headers=headers, json=body)
        print(f"\n--- sort_cnd={sort_val} (KOSPI stex_tp=1) ---")
        items = res.json().get("eql_nettrde_rank", [])
        print(f"Total: {len(items)}")
        for item in items[:5]:
            print(f"Rank {item.get('rank')}: {item.get('stk_nm')} | Organ: {item.get('orgn_nettrde_amt')} | Foreign: {item.get('for_nettrde_amt')} | Total: {item.get('nettrde_amt')}")

if __name__ == "__main__":
    test_sort_cnd()
