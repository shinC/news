import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("KIWOOM_APP_KEY")
APP_SECRET = os.getenv("KIWOOM_SECRET_KEY")

def test_token():
    url = "https://api.kiwoom.com/oauth2/token"
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    
    print(f"요청 URL: {url}")
    # 보안을 위해 키는 출력하지 않음
    
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        print(f"상태 코드: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            if "access_token" in data:
                print("토큰 발급 성공!")
                # print(f"토큰: {data['access_token'][:10]}...") 
            else:
                print(f"응답 데이터: {data}")
        else:
            print(f"에러 응답: {res.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

if __name__ == "__main__":
    test_token()
