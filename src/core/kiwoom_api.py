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
            
        # 보안을 위해 앞뒤 4자리만 마스킹하여 키 전달 여부 로그 추가
        app_key_log = f"{self.app_key[:4]}...{self.app_key[-4:]}" if self.app_key else "None"
        secret_key_log = f"{self.secret_key[:4]}...{self.secret_key[-4:]}" if self.secret_key else "None"
        logger.info(f"전달된 키 검증 - APP_KEY: {app_key_log}, SECRET_KEY: {secret_key_log}")
            
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
                self.token = data.get("access_token", data.get("token"))
                token_log = f"{self.token[:5]}...{self.token[-5:]}" if self.token else "None"
                logger.info(f"토큰 발급 성공 - 발급된 토큰: {token_log}")
                return True
            else:
                logger.error(f"키움 토큰 발급 실패: {res.text}")
        except Exception as e:
            logger.error(f"키움 토큰 발급 예외: {e}")
        return False

    def get_top_trading_value(self, market_code: str = "000") -> List[Dict[str, Any]]:
        """거래대금 상위 종목을 조회합니다 (ka10032).
        stex_tp="3" (통합)을 사용하여 KRX 및 NXT 합산 데이터를 가져옵니다.
        """
        if not self.token and not self.get_token():
            return []
            
        url = f"{self.base_url}/api/dostk/rkinfo"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "api-id": "ka10032"
        }
        token_sent_log = f"{self.token[:5]}...{self.token[-5:]}" if self.token else "None"
        logger.info(f"거래대금 API 호출 준비 - 전송 헤더 토큰: {token_sent_log}")
        
        body = {
            "mrkt_tp": market_code,
            "stex_tp": "3",  # 통합 (KRX + NXT)
            "mang_stk_incls": "0",
            "data_limit": "100"
        }
        
        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                resp_json = res.json()
                data = resp_json.get("trde_prica_upper", [])
                logger.info(f"Kiwoom API 거래대금 조회 성공, 수신 종목 수: {len(data)}")
                if not data:
                    logger.warning(f"Kiwoom API 응답에 trde_prica_upper 데이터가 없습니다: {resp_json}")
            else:
                logger.error(f"Kiwoom API 거래대금 조회 실패 ({res.status_code}): {res.text}")
                data = []
        except Exception as e:
            logger.error(f"Kiwoom API fetch error (stex_tp=3): {e}")
            return []

        formatted_stocks = []
        for item in data:
            name = item.get("stk_nm", "").strip()
            ticker = item.get("stk_cd", "").strip()
            if not name or not ticker:
                continue
            try:
                price = item.get("cur_prc", "0").replace("+", "").replace("-", "").replace(",", "")
                change_pct = float(item.get("flu_rt", "0").replace("+", "").replace("%", ""))
                tv = float(item.get("trde_prica", "0")) * 1000000 
                
                formatted_stocks.append({
                    "ticker": name,       # 종목명 (메인 스크립트 호환용)
                    "ticker_cd": ticker,  # 종목코드
                    "price": price,
                    "change_pct": change_pct,
                    "trading_value": tv
                })
            except Exception:
                continue
                
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

    def get_investor_trends(self, market_code: str = "0") -> Optional[Dict[str, str]]:
        """
        업종별/시장별 투자자 순매수를 조회합니다 (ka10051).
        market_code: '0' (코스피), '1' (코스닥)
        URL: /api/dostk/sect
        """
        if not self.token and not self.get_token():
            return None

        url = f"{self.base_url}/api/dostk/sect"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"Bearer {self.token}",
            "api-id": "ka10051"
        }
        body = {
            "mrkt_tp": market_code,  # 코스피: 0, 코스닥: 1
            "amt_qty_tp": "0",       # 금액: 0, 수량: 1
            "base_dt": "",           # 당일
            "stex_tp": "3"           # 통합 (1:KRX, 2:NXT, 3:통합)
        }

        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                resp_json = res.json()
                if resp_json.get("return_code") == 0 or resp_json.get("return_code") == "0":
                    data_list = resp_json.get("inds_netprps", [])
                    if data_list and isinstance(data_list, list):
                        # 첫 번째 항목(inds_cd '001_AL' 또는 '101_AL')이 시장 전체 종합
                        total_item = data_list[0]
                        foreign = total_item.get("frgnr_netprps", "0")
                        inst = total_item.get("orgn_netprps", "0")
                        person = total_item.get("ind_netprps", "0")
                        logger.info(f"Kiwoom ka10051 ({market_code}) 수집 성공: 외국인={foreign}, 기관={inst}, 개인={person}")
                        return {
                            "외국인": str(foreign),
                            "기관": str(inst),
                            "개인": str(person)
                        }
                else:
                    logger.warning(f"Kiwoom ka10051 응답 오류 메시지: {resp_json.get('return_msg')}")
            else:
                logger.error(f"Kiwoom ka10051 호출 실패 ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Kiwoom ka10051 호출 예외: {e}")

        return None


