import os
import requests
import json
import datetime
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

def debug_today():
    token = get_token()
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    print(f"Today Date: {today_str}")

    url = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10062"
    }

    test_date_params = [
        {"strt_dt": today_str, "end_dt": today_str},
        {"strt_dt": "", "end_dt": ""},
        {"strt_dt": "0", "end_dt": "0"},
        {"unit_tp": "1000", "strt_dt": "", "end_dt": ""},
        {"unit_tp": "1", "strt_dt": "", "end_dt": ""},
    ]

    for idx, d_param in enumerate(test_date_params):
        print(f"\n================ Test Date Param Set {idx+1}: {d_param} ================")
        for m_code in ["000", "001"]:
            body = {
                "mrkt_tp": m_code,
                "stex_tp": "3",
                "amt_qty_tp": "0",  # 금액
                "trde_tp": "1",     # 순매수
                "sort_cnd": "1",    # 순매수액순
                "unit_tp": "1",     # 단위
            }
            body.update(d_param)
            res = requests.post(url, headers=headers, json=body)
            resp_json = res.json()
            data = resp_json.get("eql_nettrde_rank", [])
            print(f"market_code: {m_code} -> Code: {resp_json.get('return_code')}, Total returned: {len(data)}, Msg: {resp_json.get('return_msg')}")
            if data:
                print("First item sample:", data[0])

if __name__ == "__main__":
    debug_today()
