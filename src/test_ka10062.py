import os
import requests
import json
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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

def test_ka10062():
    token = get_token()
    if not token:
        print("토큰 발급 실패")
        return

    url = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10062"
    }

    import datetime
    today_str = datetime.datetime.now().strftime("%Y%m%d")

    test_bodies = [
        {"mrkt_tp": "000", "stex_tp": "3", "amt_qty_tp": "0", "trde_tp": "1", "sort_cnd": "1", "unit_tp": "1", "strt_dt": "20261006", "end_dt": "20261006"},
        {"mrkt_tp": "001", "stex_tp": "3", "amt_qty_tp": "0", "trde_tp": "1", "sort_cnd": "1", "unit_tp": "1", "strt_dt": "20261006", "end_dt": "20261006"},
        {"mrkt_tp": "101", "stex_tp": "3", "amt_qty_tp": "0", "trde_tp": "1", "sort_cnd": "1", "unit_tp": "1", "strt_dt": "20261006", "end_dt": "20261006"},
    ]

    for idx, body in enumerate(test_bodies):
        print(f"\n--- Test Body {idx+1}: {body} ---")
        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            print(f"Status Code: {res.status_code}")
            resp_json = res.json()
            print("Response JSON:", json.dumps(resp_json, indent=2, ensure_ascii=False)[:2000])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_ka10062()
