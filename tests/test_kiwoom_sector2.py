import asyncio
from src.core.kiwoom_api import KiwoomAPI
import json
import requests

def test_tr(tr_id, body_input):
    api = KiwoomAPI()
    if not api.get_token(): return
    url = f"{api.base_url}/v1/openapi/tr"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api.token}", "api-id": tr_id}
    res = requests.post(url, headers=headers, json={"input": body_input}, timeout=10)
    print(f"{tr_id} status:", res.status_code)
    print(res.text[:200])

if __name__ == "__main__":
    test_tr("opt20004", {"시장구분": "0", "업종코드": "001"})
    test_tr("opt20002", {"시장구분": "0", "업종코드": "001"})
