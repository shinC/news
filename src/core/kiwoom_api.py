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
        market_code: 000(전체), 001(코스피), 101(코스닥)
        """
        if not self.token and not self.get_token():
            return []
            
        url = f"{self.base_url}/v1/openapi/tr"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "api-id": "ka10032" # 또는 opt10032
        }
        body = {
            "input": {
                "시장구분": market_code,
                "관리종목포함": "0"
            }
        }
        
        stocks = []
        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            if res.status_code == 200:
                data = res.json()
                output = data.get("output", [])
                for item in output:
                    try:
                        # 키움 API 필드명에 맞춰 파싱 (예시 기반)
                        name = item.get("종목명", "").strip()
                        ticker = item.get("종목코드", "").strip()
                        price = item.get("현재가", "0").replace("+", "").replace("-", "")
                        change_pct = float(item.get("등락률", "0"))
                        # 거래대금은 보통 '천원' 또는 '백만원' 단위이므로 확인 필요
                        tv = float(item.get("거래대금", "0")) * 1000 # 천원 단위 가정
                        
                        stocks.append({
                            "ticker": name,
                            "price": price,
                            "change_pct": change_pct,
                            "trading_value": tv
                        })
                    except (ValueError, TypeError):
                        continue
            else:
                # 500 에러 등이 나면 빈 리스트 반환하여 Fallback 유도
                logger.warning(f"키움 API TR 요청 실패 ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"키움 API 요청 중 예외 발생: {e}")
            
        return stocks
