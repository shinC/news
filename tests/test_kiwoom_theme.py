import asyncio
from src.core.kiwoom_api import KiwoomAPI
import json
import requests

def test_theme():
    api = KiwoomAPI()
    if not api.get_token():
        print("Token failed")
        return
        
    url = f"{api.base_url}/v1/openapi/tr"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api.token}",
        "api-id": "OPT90001"
    }
    body = {
        "input": {
            "검색구분": "0",  # 0: 전체, 1: 상
            "종목코드": "",
            "날짜구분": "1", # 1: 당일?
            "테마명": "",
            "등락수익": "1" # 1: 상승률순 정렬?
        }
    }
    res = requests.post(url, headers=headers, json=body, timeout=10)
    print(res.status_code)
    print(res.text[:500])

if __name__ == "__main__":
    test_theme()
