import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("KIWOOM_APP_KEY")
APP_SECRET = os.getenv("KIWOOM_SECRET_KEY")

def get_token():
    url = "https://api.kiwoom.com/oauth2/token"
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    res = requests.post(url, json=body)
    return res.json().get("token")

def test_tr_opt10032():
    token = get_token()
    if not token:
        print("토큰 발급 실패")
        return
        
    url = "https://api.kiwoom.com/v1/openapi/tr"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api_id": "opt10032"
    }
    
    # KOSPI(001) 거래대금 상위
    body = {
        "input": {
            "시장구분": "001",
            "정렬구분": "1",
            "관리종목제외": "1"
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        print(f"상태 코드: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"응답 데이터 요약: {str(data)[:500]}...")
            
            # NEXT API 응답은 보통 "output" 키 안에 리스트가 있음
            if "output" in data:
                for stock in data["output"][:5]:
                    print(f"종목: {stock.get('종목명')} ({stock.get('종목코드')}), 거래대금: {stock.get('거래대금')}")
        else:
            print(f"에러 응답: {res.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

if __name__ == "__main__":
    test_tr_opt10032()
