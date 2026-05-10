# Project Requirements Document (PRD) - Global Financial News Pipeline

## 1. 프로젝트 목적 (Project Purpose)
글로벌 금융 시장(미국/한국)의 시황 정보와 주요 뉴스를 자동 수집하고, 데이터 기반의 가공을 통해 투자에 필요한 핵심 인사이트를 빠르게 파악할 수 있는 통합 뉴스 파이프라인 시스템을 구축한다.

## 2. 주요 대상 소스 (Target Sources)
- **미국 마켓 (US Market)**:
    - 시황: Yahoo Finance (`yfinance`)
    - 뉴스: Google News (via `newspaper4k`)
- **한국 마켓 (KR Market)**:
    - 시황: Naver Finance (`requests`/`BeautifulSoup`), Kiwoom API (Open API NEXT)
    - 뉴스: Naver Finance (News Sections), Google News (via `newspaper4k`)
- **특정 기업 뉴스**:
    - US: `yfinance` 기반 뉴스 피드
    - KR: Naver 뉴스 검색

## 3. 핵심 기능 (Key Features)

### 3.1. 통합 시황 파악 (Market Intelligence)
- **미국 마켓**: 3대 지수(S&P 500, NASDAQ, Dow Jones) 및 11개 산업 섹터 ETF 등락률 수집. 거래대금 상위 특징주 수집.
- **한국 마켓**: 3대 지수(KOSPI, KOSDAQ, KOSPI 200) 및 테마별 등락률 수집.
- **Kiwoom API 연동**: 한국 마켓의 실시간 거래대금 상위 100개 종목 데이터를 정확하게 수집.
- **상승 이유 분석 (Reason for Gainer)**: 거래대금 상위 종목 중 급등주를 선별하여 관련 뉴스를 매칭, 상승 원인(재료)을 자동으로 추출.

### 3.2. 지능형 뉴스 수집 및 처리 (News Engine)
- **멀티 채널 크롤링**: 구글 뉴스 및 네이버 금융 뉴스 섹션별(시황, 기업, 많이본 뉴스 등) 동시 수집.
- **본문 자동 파싱**: `newspaper4k`를 활용한 기사 본문 추출, 키워드 생성 및 메타데이터(발행일 등) 정규화.
- **데이터 필터링**: 최근 48시간 이내 기사만 선별하며, 제목/본문 내 티커 또는 기업명 포함 여부를 엄격히 검증.
- **우선순위 가중치**: 매크로 지표(금리, PCE, CPI 등) 및 관심 종목 키워드 포함 시 우선 노출 점수 부여.

### 3.3. 데이터 분석 및 정렬 (Analytics & Sorting)
- **이슈 클러스터링**: TF-IDF 및 코사인 유사도 분석을 통해 동일한 이슈를 다루는 중복 기사들을 그룹화하고 이슈의 중요도(중복도) 산출.
- **다차원 정렬**: 1순위 키워드 가중치, 2순위 최신 발행 시간, 3순위 이슈 중복도 순으로 최적의 리스트 제공.

### 3.4. 결과물 생성 및 배포 (Output & Reporting)
- **데일리 시황 리포트**: `us_economy_news.md`, `kr_economy_news.md` 형태로 섹션별 요약 제공.
- **관심 기업 리포트**: `--companies` 인자를 통해 특정 기업들에 대한 집중 리서치 결과물 생성.
- **AI 요약 블로그 포스트**: 수집된 데이터를 바탕으로 LLM(Gemini 등)을 연동하여 블로그 게시용 요약문(`blog_post.md`) 자동 생성.

## 4. 성공 기준 (Success Criteria)
- 미국/한국 마켓의 주요 지수 및 특징주 데이터를 오류 없이 100% 수집해야 함.
- 수집된 기사들이 중복 제거 및 우선순위 알고리즘에 따라 정확히 정렬되어야 함.
- 특정 기업 검색 시 제목과 본문 모두에 해당 키워드가 포함된 유효한 기사만 필터링되어야 함.
- 모든 결과물은 가독성이 확보된 마크다운 포맷으로 지정된 경로에 자동 저장되어야 함.
