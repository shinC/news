import os
import requests
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class KiwoomAPI:
    def __init__(self):
        self.app_key = os.getenv("KIWOOM_APP_KEY")
        self.secret_key = os.getenv("KIWOOM_SECRET_KEY")
        self.base_url = "https://api.kiwoom.com"
        self.token: Optional[str] = None

    def get_token(self) -> bool:
        """OAuth2 토큰을 발급받습니다."""
        if not self.app_key or not self.secret_key:
            logger.warning("키움 API 키가 설정되지 않았습니다.")
            return False
            
        url = f"{self.base_url}/oauth2/token"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key
        }
        try:
            res = requests.post(url, json=body, timeout=10)
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("token")
                return True
            else:
                logger.error(f"키움 토큰 발급 실패: {res.text}")
        except Exception as e:
            logger.error(f"키움 토큰 발급 예외: {e}")
        return False

    def get_top_trading_value(self, market_code: str = "000") -> List[Dict[str, Any]]:
        """거래대금 상위 종목을 조회합니다 (ka10032).
        KRX와 NXT 데이터를 각각 가져와 합산합니다.
        """
        if not self.token and not self.get_token():
            return []
            
        url = f"{self.base_url}/api/dostk/rkinfo"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "api-id": "ka10032"
        }
        
        def fetch_data(stex_tp):
            body = {
                "mrkt_tp": market_code,
                "stex_tp": stex_tp,
                "mang_stk_incls": "0",
                "data_limit": "100"
            }
            try:
                res = requests.post(url, headers=headers, json=body, timeout=10)
                if res.status_code == 200:
                    return res.json().get("trde_prica_upper", [])
            except Exception as e:
                logger.error(f"Kiwoom API fetch error (stex_tp={stex_tp}): {e}")
            return []

        # KRX (1)와 NXT (2) 데이터 각각 수집
        krx_data = fetch_data("1")
        nxt_data = fetch_data("2")
        
        stock_map = {}
        
        # KRX 데이터 처리
        for item in krx_data:
            name = item.get("stk_nm", "").strip()
            ticker = item.get("stk_cd", "").strip()
            try:
                price = item.get("cur_prc", "0").replace("+", "").replace("-", "").replace(",", "")
                change_pct = float(item.get("flu_rt", "0").replace("+", "").replace("%", ""))
                tv = float(item.get("trde_prica", "0")) * 1000000 
                stock_map[ticker] = {
                    "name": name,
                    "ticker": ticker,
                    "price": price,
                    "change_pct": change_pct,
                    "trading_value": tv
                }
            except: continue

        # NXT 데이터 합산
        for item in nxt_data:
            ticker = item.get("stk_cd", "").strip().replace("_NX", "") # 접미사 제거하여 매칭
            try:
                tv = float(item.get("trde_prica", "0")) * 1000000
                if ticker in stock_map:
                    stock_map[ticker]["trading_value"] += tv
                else:
                    # KRX에 없는 종목이 NXT에 있을 경우 (드묾)
                    name = item.get("stk_nm", "").strip()
                    price = item.get("cur_prc", "0").replace("+", "").replace("-", "").replace(",", "")
                    change_pct = float(item.get("flu_rt", "0").replace("+", "").replace("%", ""))
                    stock_map[ticker] = {
                        "name": name,
                        "ticker": ticker,
                        "price": price,
                        "change_pct": change_pct,
                        "trading_value": tv
                    }
            except: continue

        stocks = list(stock_map.values())
        formatted_stocks = []
        for s in stocks:
            formatted_stocks.append({
                "ticker": s["name"], # 종목명 (메인 스크립트 호환용)
                "ticker_cd": s["ticker"], # 종목코드
                "price": s["price"],
                "change_pct": s["change_pct"],
                "trading_value": s["trading_value"]
            })
            
        return formatted_stocks
    def get_theme_ranking(self) -> List[Dict[str, Any]]:
        """테마그룹별 등락률 순위를 조회합니다 (ka90001)."""
        if not self.token and not self.get_token():
            return []
            
        url = f"{self.base_url}/api/dostk/thme"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "api-id": "ka90001"
        }
        body = {
            "qry_tp": "0", # 전일대비 등락률 순
            "date_tp": "0", # 당일
            "flu_pl_amt_tp": "0", # 상승순
            "stex_tp": "1" # 코스피/코스닥 합산 (코스피 기준 정렬 시 HTS와 유사)
        }
        
        themes = []
        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # ka90001의 경우 출력 키가 thema_grp 임
                output = data.get("thema_grp", data.get("output", []))
                for item in output:
                    try:
                        name = item.get("thema_nm", "").strip()
                        theme_id = item.get("thema_grp_cd", "").strip()
                        change_pct = float(item.get("flu_rt", "0"))
                        main_stk = item.get("main_stk", "").strip()
                        themes.append({
                            "name": name,
                            "id": theme_id,
                            "change_pct": change_pct,
                            "main_stk": main_stk
                        })
                    except Exception:
                        continue
            else:
                logger.warning(f"키움 테마 API 요청 실패 ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"키움 테마 API 요청 예외: {e}")
            
        return themes

    def get_theme_components(self, theme_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """특정 테마의 구성 종목을 조회합니다 (ka90002)."""
        if not self.token and not self.get_token():
            return []
            
        url = f"{self.base_url}/api/dostk/thme"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "api-id": "ka90002"
        }
        body = {
            "thema_grp_cd": theme_id,
            "stex_tp": "0"
        }
        
        stocks = []
        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                data = res.json()
                output = data.get("thema_comp_stk", data.get("output", []))
                for item in output:
                    try:
                        name = item.get("stk_nm", "").strip()
                        if not name: continue
                        
                        price = abs(int(item.get("cur_prc", "0").replace(",", "")))
                        change_pct = float(item.get("flu_rt", "0"))
                        volume = int(item.get("acc_trde_qty", "0"))
                        
                        # 거래대금 계산 (원 단위)
                        trading_value = price * volume
                        
                        stocks.append({
                            "name": name,
                            "change_pct": change_pct,
                            "trading_value": trading_value
                        })
                    except Exception:
                        continue
            
            # 한도만큼만 반환
            return stocks[:limit]
        except Exception as e:
            logger.error(f"키움 테마 종목 API 요청 예외: {e}")
            
        return stocks
