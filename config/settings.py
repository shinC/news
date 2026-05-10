from pydantic import BaseModel, Field

class Settings(BaseModel):
    # Google News 검색 설정
    country: str = "US"
    topic: str = "BUSINESS" # "BUSINESS" 카테고리를 활용하여 경제/비즈니스 뉴스 수집
    period: str = "2d"      # 최근 2일
    max_results: int = 50   # 가져올 최대 뉴스 개수

    # 출력 설정
    output_dir: str = "data/output"
    output_filename: str = "us_economy_news.md"

    # 우선순위 키워드 (연준, 금리, PCE, CPI 등 주요 매크로 지표)
    priority_keywords: list = [
        "Federal Reserve", "Interest Rate", "PCE", "CPI", "Fed",
        "연준", "금리", "물가", "인플레이션", "금리인상", "금리인하"
    ]

settings = Settings()

class SettingsKR(BaseModel):
    # Google News 검색 설정 (한국)
    country: str = "KR"
    topic: str = "BUSINESS" 
    period: str = "2d"
    max_results: int = 50

    # 출력 설정
    output_dir: str = "data/output"
    output_filename: str = "kr_economy_news.md"

    # 우선순위 키워드 (연준, 금리, PCE, CPI 등 주요 매크로 지표)
    priority_keywords: list = [
        "연준", "금리", "PCE", "CPI", "한국은행", "금통위",
        "Federal Reserve", "Interest Rate", "Inflation", "인플레이션"
    ]

    # 네이버 증권 뉴스 수집 경로 (카테고리별)
    naver_finance_sections: dict = {
        "주요뉴스": "https://finance.naver.com/news/mainnews.naver",
        "시황": "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401",
        "기업": "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=402",
        "많이본 뉴스": "https://finance.naver.com/news/news_list.naver?mode=RANK"
    }

settings_kr = SettingsKR()
