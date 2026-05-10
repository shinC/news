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
        "api-id": "opt90001"
    }
    body = {
        "input": {
            "검색구분": "0",
            "종목코드": "",
            "날짜구분": "1",
            "테마명": "",
            "등락수익구분": "3" # 1: 상위기간수익률, 3: 상위등락률
        }
    }
    res = requests.post(url, headers=headers, json=body, timeout=10)
    print("opt90001 status:", res.status_code)
    print(res.text[:500])

if __name__ == "__main__":
    test_theme()
