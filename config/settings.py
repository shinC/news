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
        "Business": "Business",
        "Economy": "Economy",
        "Finance": "Finance",
        "Science & technology": "Science & technology",
        "Robotics": "Robotics",
        "Internet security": "Internet security",
        "World": "World",
        "Politics": "Politics"
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
        "비즈니스": "비즈니스",
        "경제": "경제",
        "세계": "세계",
        "정치": "정치",
        "금융": "금융",
        "과학기술": "과학기술",
        "로봇": "로봇",
        "인터넷보안": "인터넷보안"
    }

    # 네이버 증권 뉴스 수집 경로 (카테고리별)
    # naver_finance_sections: dict = {
    #     "주요뉴스": "https://finance.naver.com/news/mainnews.naver",
    #     "시황": "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401",
    #     "기업": "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=402",
    #     "많이본 뉴스": "https://finance.naver.com/news/news_list.naver?mode=RANK"
    # }

settings_kr = SettingsKR()
