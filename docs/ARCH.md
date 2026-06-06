# Architecture & Design (ARCH) - Global Financial News Pipeline

## 1. 기술 스택 (Tech Stack)
- **Language**: Python 3.10+
- **Market Data**:
    - `yfinance`: 미국 지수, 섹터 및 특징주 데이터 수집
    - `Kiwoom API (NEXT)`: 한국 실시간 거래대금 상위 종목 수집
    - `requests` & `BeautifulSoup`: 네이버 금융 시황 및 테마 데이터 크롤링
- **News Scraping**:
    - `newspaper4k`: 구글 뉴스 연동, 본문 추출, 자연어 처리(NLP) 기반 요약 및 키워드 생성
- **Data Processing**:
    - `pandas`: 데이터 전처리, 정렬 및 정규화
    - `scikit-learn`: TF-IDF 및 코사인 유사도 기반 기사 클러스터링
- **Automation & AI**:
    - `Github Actions` / `Docker`: 자동 실행 환경
    - `LLM (Gemini/OpenAI)`: 최종 요약 리포트 및 블로그 포스트 생성

## 2. 디렉토리 구조 (Directory Structure)
```text
.
├── docs/
│   ├── PRD.md              # 요구사항 정의서
│   └── ARCH.md             # 아키텍처 및 설계 문서
├── tests/                  # 단위 테스트 및 기능 검증 스크립트
├── src/
│   ├── main.py             # 미국 뉴스 파이프라인 엔트리포인트
│   ├── main_kr.py          # 한국 뉴스 파이프라인 엔트리포인트
│   ├── search_company.py   # 특정 기업 뉴스 검색 유틸리티
│   ├── core/
│   │   ├── market.py       # 미국 시황 데이터 수집 (yfinance)
│   │   ├── market_kr.py    # 한국 시황 데이터 수집 (Naver/Kiwoom)
│   │   ├── scraper.py      # 미국 뉴스 스크래핑 (Google News)
│   │   ├── scraper_kr.py   # 한국 뉴스 스크래핑 (Naver Finance)
│   │   ├── analyzer.py     # 기사 유사도 분석 및 클러스터링
│   │   ├── formatter.py    # 마크다운 리포트 생성 및 저장
│   │   └── kiwoom_api.py   # 키움 API NEXT 연동 모듈
│   └── utils/              # 공통 유틸리티 (로깅, 날짜 처리 등)
├── config/
│   └── settings.py         # 마켓별 설정 (키워드, 기간, 카테고리 등)
└── data/
    └── output/             # 생성된 리포트 저장 폴더
```

## 3. 데이터 파이프라인 (Data Pipeline)

### 3.1. 기본 시황/뉴스 파이프라인 (main.py / main_kr.py)
1. **시황 수집**: `market.py` 또는 `market_kr.py`를 통해 지수 및 거래대금 상위 종목 수집 (키움 API NEXT / 네이버 금융).
2. **뉴스 수집**:
    - **미국**: `scraper.py`를 통해 야후 파이낸스 및 인베스토페디아 직접 스크래핑(Playwright)으로 최신 마감시황 뉴스를 수집하고, 상승률/거래대금 상위 특징주 기사는 `[ticker] stock why up today` 패턴의 쿼리를 통해 구글 뉴스 RSS로 수집.
    - **한국**: `scraper_kr.py`를 통해 구글 카테고리 RSS, 연합인포맥스 매크로 RSS(키워드 필터링 적용), 네이버 특징주 `특징주 '종목명'` 검색(원본 URL 및 제목만 추출) 수집.
3. **데이터 정규화**: 구글 뉴스 암호화 URL들의 리다이렉트를 `googlenewsdecoder`를 통해 일괄(Batch) 디코딩하여 원본 링크를 복원하고, 야후/인베스토페디아에서 직접 수집된 기사의 경우에는 Playwright로 본문을 즉시 추출.
4. **정렬 알고리즘**: 검색 엔진 원본 랭킹과 발행 시간을 결합한 다차원 정렬 적용.
5. **저장**: `formatter.py`를 통해 마크다운 리포트 생성 및 저장 (특징주도 클릭 가능한 링크 연동).

1. 사용자가 입력한 `--market` 및 `--companies` 인자 수신.
2. 대상 마켓에 맞는 `fetch_company_news_us/kr` 함수 호출 (최근 3일 데이터 수집).
3. 제목 또는 본문에 기업명이 포함된 기사를 정밀 필터링하여 노이즈 제거.
4. 원본 검색 순위를 유지하여 브라우저 결과와 일치하는 기업 뉴스 리포트 생성.

## 4. 실행 명령어 (Execution Commands)

### 4.1. 데일리 시황 및 뉴스 수집
- **미국 마켓 수집**:
  ```bash
  python src/main.py
  ```
- **한국 마켓 수집**:
  ```bash
  python src/main_kr.py
  ```

### 4.2. 특정 기업 뉴스 집중 검색
- **미국 기업 검색** (예: Apple, Microsoft):
  ```bash
  python src/search_company.py --market us --companies AAPL MSFT --days 3
  ```
- **한국 기업 검색** (예: 삼성전자, SK하이닉스):
  ```bash
  python src/search_company.py --market kr --companies 삼성전자 SK하이닉스 --days 3
  ```

### 4.3. 결과물 확인
- 모든 결과물은 `data/output/` 디렉토리에 마크다운(`.md`) 파일로 생성됩니다.
- 주요 파일명: `us_economy_news.md`, `kr_economy_news.md`, `company_news_us.md`, `company_news_kr.md`

---
*Project: news*
