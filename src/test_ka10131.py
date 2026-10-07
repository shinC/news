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

def test_ka10131():
    token = get_token()
    if not token:
        print("토큰 발급 실패")
        return

    url = "https://api.kiwoom.com/api/dostk/frgnistt"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10131"
    }

    # 시험 파라미터 조합 테스트
    test_params = [
        {"mrkt_tp": "001", "stex_tp": "3", "amt_qty_tp": "0", "dt": "0", "netslmt_tp": "1", "stk_inds_tp": "0"},
        {"mrkt_tp": "001", "stex_tp": "3", "amt_qty_tp": "0", "dt": "0", "netslmt_tp": "1", "stk_inds_tp": "1"},
        {"mrkt_tp": "101", "stex_tp": "3", "amt_qty_tp": "0", "dt": "0", "netslmt_tp": "1", "stk_inds_tp": "0"},
    ]

    for idx, body in enumerate(test_params):
        print(f"\n--- Test {idx+1}: {body} ---")
        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            print(f"Status Code: {res.status_code}")
            resp_json = res.json()
            print("Response Key List:", list(resp_json.keys()))
            print(json.dumps(resp_json, indent=2, ensure_ascii=False)[:3000])
        except Exception as e:
            print(f"Error: {e}")



if __name__ == "__main__":
    test_ka10131()
