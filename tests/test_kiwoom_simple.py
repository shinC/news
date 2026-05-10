import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_kiwoom_simple():
    app_key = os.getenv("KIWOOM_APP_KEY")
    secret_key = os.getenv("KIWOOM_SECRET_KEY")
    base_url = "https://api.kiwoom.com"

    # 1. Get Token
    auth_url = f"{base_url}/oauth2/token"
    auth_body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "secretkey": secret_key
    }
    res = requests.post(auth_url, json=auth_body)
    if res.status_code != 200:
        print(f"Auth Error: {res.text}")
        return
    
    token = res.json().get("access_token") or res.json().get("token")

    # 2. Test opt10001 (Samsung Electronics)
    print("\n--- Testing opt10001 (Samsung Electronics) ---")
    tr_url = f"{base_url}/v1/openapi/tr"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api-id": "opt10001"
    }
    body = {
        "input": {
            "종목코드": "005930"
        }
    }
    res = requests.post(tr_url, headers=headers, json=body)
    print(f"opt10001 Status: {res.status_code}")
    print(f"opt10001 Response: {res.text}")

if __name__ == "__main__":
    test_kiwoom_simple()
