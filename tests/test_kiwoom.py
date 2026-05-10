import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_kiwoom():
    app_key = os.getenv("KIWOOM_APP_KEY")
    secret_key = os.getenv("KIWOOM_SECRET_KEY")
    base_url = "https://api.kiwoom.com"

    # 1. Get Token
    print("--- Getting Token ---")
    auth_url = f"{base_url}/oauth2/token"
    auth_body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "secretkey": secret_key
    }
    res = requests.post(auth_url, json=auth_body)
    print(f"Token Status: {res.status_code}")
    if res.status_code != 200:
        print(f"Error: {res.text}")
        return
    
    token = res.json().get("access_token") # access_token일 수도 있음
    if not token:
        token = res.json().get("token")
    print(f"Token acquired: {token[:10]}...")

    # 2. Test ka10032
    print("\n--- Testing ka10032 ---")
    tr_url = f"{base_url}/v1/openapi/tr"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10032"
    }
    body = {
        "input": {
            "시장구분": "000",
            "관리종목포함": "0"
        }
    }
    res = requests.post(tr_url, headers=headers, json=body)
    print(f"ka10032 Status: {res.status_code}")
    print(f"ka10032 Response: {res.text}")

    # 3. Test opt10032
    print("\n--- Testing opt10032 ---")
    headers["api-id"] = "opt10032"
    res = requests.post(tr_url, headers=headers, json=body)
    print(f"opt10032 Status: {res.status_code}")
    print(f"opt10032 Response: {res.text}")

if __name__ == "__main__":
    test_kiwoom()
