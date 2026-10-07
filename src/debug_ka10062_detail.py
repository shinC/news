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

def debug_detail():
    token = get_token()
    url = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10062"
    }

    # 20261006 코스피(001) 및 코스닥(101) 및 전체(000) 각각 수집
    for m_code, m_name in [("001", "KOSPI"), ("101", "KOSDAQ"), ("000", "ALL")]:
        time.sleep(0.5)
        body = {
            "mrkt_tp": m_code,
            "stex_tp": "3",       # 통합
            "amt_qty_tp": "0",    # 금액
            "trde_tp": "1",       # 순매수
            "sort_cnd": "1",      # 순매수액순
            "unit_tp": "1",       # 단위 1
            "strt_dt": "20261006",
            "end_dt": "20261006"
        }
        res = requests.post(url, headers=headers, json=body)
        print(f"\n================ {m_name} (mrkt_tp={m_code}) ================")
        resp_json = res.json()
        items = resp_json.get("eql_nettrde_rank", [])
        print(f"Total Count: {len(items)}")
        for item in items[:5]:
            print(json.dumps(item, ensure_ascii=False))

if __name__ == "__main__":
    debug_detail()
