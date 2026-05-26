import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseModel):
    # Google News 검색 설정
    country: str = "US"
    topic: str = "BUSINESS" 
    period: str = "3d"      # 최근 3일
    max_results: int = 50   
    max_results_per_section: int = 7 # 섹션당 최대 7개
    
    # 네이버 API 설정 (환경 변수에서 로드)
    naver_client_id: str = os.getenv("NAVER_CLIENT_ID", "")
    naver_client_secret: str = os.getenv("NAVER_CLIENT_SECRET", "")

    # 출력 설정
    output_dir: str = "data/output"
    output_filename: str = "us_economy_news.md"

    # 우선순위 키워드 (연준, 금리, PCE, CPI 등 주요 매크로 지표)
    priority_keywords: list = [
        "Federal Reserve", "Interest Rate", "PCE", "CPI", "Fed",
        "연준", "금리", "물가", "인플레이션", "금리인상", "금리인하"
    ]

    # 수집 카테고리 (US)
    categories: dict = {
        "Business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
        "Economy": "CAAqIggKIhxDQkFTRHdvSkwyMHZNR2RtY0hNekVnSmxiaWdBUAE",
        "Finance": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNREpmTjNRU0FtVnVLQUFQAQ",
        "Science & technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        "Robotics": "CAAqJAgKIh5DQkFTRUFvS0wyMHZNREp3TUhRMVpoSUNaVzRvQUFQAQ",
        "Internet security": "CAAqIggKIhxDQkFTRHdvSkwyMHZNRE5xWm01NEVnSmxiaWdBUAE",
        "World": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
        "Politics": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtVnVLQUFQAQ"
    }

settings = Settings()

class SettingsKR(BaseModel):
    # Google News 검색 설정 (한국)
    country: str = "KR"
    topic: str = "BUSINESS" 
    period: str = "3d"      # 최근 3일
    max_results: int = 50
    max_results_per_section: int = 7

    # 출력 설정
    output_dir: str = "data/output"
    output_filename: str = "kr_economy_news.md"

    # 우선순위 키워드 (연준, 금리, PCE, CPI 등 주요 매크로 지표)
    priority_keywords: list = [
        "연준", "금리", "PCE", "CPI", "한국은행", "금통위",
        "Federal Reserve", "Interest Rate", "Inflation", "인플레이션"
    ]

    # 수집 카테고리 (KR)
    categories: dict = {
        "비즈니스": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB",
        "경제": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB",  # 비즈니스 토픽과 동일 적용
        "세계": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtdHZHZ0pMVWlnQVAB",
        "정치": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFp4WkRNU0FtdHZLQUFQAQ", # 대한민국(정치/사회)
        "금융": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNREpmTjNRU0FtdHZLQUFQAQ",
        "과학기술": "CAAqKAgKIiJDQkFTRXdvSkwyMHZNR1ptZHpWbUVnSnJieG9DUzFJb0FBUAE",
        "로봇": "CAAqJAgKIh5DQkFTRUFvS0wyMHZNREp3TUhRMVpoSUNhMjhvQUFQAQ", # 사용자 제공 토픽
        "인터넷보안": "CAAqIggKIhxDQkFTRHdvSkwyMHZNRE5xWm01NEVnSnJieWdBUAE"
    }

    # 네이버 증권 뉴스 수집 경로 (카테고리별)
    # naver_finance_sections: dict = {
    #     "주요뉴스": "https://finance.naver.com/news/mainnews.naver",
    #     "시황": "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401",
    #     "기업": "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=402",
    #     "많이본 뉴스": "https://finance.naver.com/news/news_list.naver?mode=RANK"
    # }

settings_kr = SettingsKR()
