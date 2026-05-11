import os
import requests
import logging
import json
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

def debug_kiwoom_apis():
    token = get_token()
    if not token:
        print("토큰 발급 실패")
        return

    # 1. ka10032 (거래대금 상위) 필드 확인
    print("\n--- ka10032 (Trading Value Ranking) with stex_tp: 0 ---")
    url_rk = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api-id": "ka10032"
    }
    body_rk = {
        "mrkt_tp": "000",
        "stex_tp": "0",
        "mang_stk_incls": "0",
        "data_limit": "5" # 상위 5개만
    }
    res_rk = requests.post(url_rk, headers=headers, json=body_rk)
    print(f"Status: {res_rk.status_code}")
    print(json.dumps(res_rk.json(), indent=2, ensure_ascii=False))

    # 2. ka90001 (테마 순위) 확인
    print("\n--- ka90001 (Theme Ranking) ---")
    url_th = "https://api.kiwoom.com/api/dostk/thme"
    headers_th = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "api-id": "ka90001"
    }
    body_th = {"qry_tp": "0", "date_tp": "0", "flu_pl_amt_tp": "0", "stex_tp": "0"}
    res_th = requests.post(url_th, headers=headers_th, json=body_th)
    data_th = res_th.json()
    print(json.dumps(data_th, indent=2, ensure_ascii=False))
    
    # 상위 테마 코드 추출
    themes = data_th.get("output", [])
    if themes:
        top_theme = themes[0]
        theme_cd = top_theme.get("thema_grp_cd")
        theme_nm = top_theme.get("thema_nm")
        print(f"\nTop Theme: {theme_nm} ({theme_cd})")
        
        # 3. ka90002 (테마구성종목요청) 확인
        print(f"\n--- ka90002 (Theme Components for {theme_nm}) ---")
        headers_comp = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "api-id": "ka90002"
        }
        body_comp = {
            "thema_grp_cd": theme_cd,
            "stex_tp": "0"
        }
        res_comp = requests.post(url_th, headers=headers_comp, json=body_comp) # URI는 thme로 동일할 확률 높음
        print(f"Status: {res_comp.status_code}")
        print(json.dumps(res_comp.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    debug_kiwoom_apis()
