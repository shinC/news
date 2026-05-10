import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("KIWOOM_APP_KEY")
APP_SECRET = os.getenv("KIWOOM_SECRET_KEY")

def get_token():
    url = "https://mockapi.kiwoom.com/oauth2/token"
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    res = requests.post(url, json=body)
    return res.json().get("token")

def test_tr_opt10001():
    token = get_token()
    if not token:
        print("토큰 발급 실패")
        return
        
    url = "https://mockapi.kiwoom.com/v1/openapi/tr"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api_id": "opt10001"
    }
    
    # 삼성전자 정보
    body = {
        "input": {
            "종목코드": "005930"
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        print(f"상태 코드: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"응답 데이터: {data}")
        else:
            print(f"에러 응답: {res.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

if __name__ == "__main__":
    test_tr_opt10001()
