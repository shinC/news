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

settings = Settings()
