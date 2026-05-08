# Architecture & Design (ARCH) - US Economy News Scraper

## 1. 기술 스택 (Tech Stack)
- **Language**: Python 3.14
- **Core Library**: `newspaper4k[gnews,nlp]` (Google News 통합 및 기사 본문/요약 추출)
- **Market Data**: `yfinance` (야후 파이낸스 기반 주가지수 및 섹터 데이터 수집)
- **Data Processing**: 
  - `pandas` (데이터 정렬 및 전처리)
  - `scikit-learn` (TF-IDF 및 코사인 유사도 기반 기사 클러스터링)
- **Environment**: Docker / Dev Container

## 2. 디렉토리 구조 (Directory Structure)
```text
.
├── docs/
│   ├── PRD.md             # 요구사항 정의서
│   └── ARCH.md            # 아키텍처 및 설계 문서
├── src/
│   ├── core/
│   │   ├── market.py      # yfinance 연동 및 지수/섹터 시황 수집
│   │   ├── scraper.py     # 구글 뉴스(newspaper4k) 연동 및 2일 이내 기사 수집
│   │   ├── analyzer.py    # 유사 기사 그룹화 및 중복도 산출
│   │   └── formatter.py   # 시황 및 뉴스를 마크다운 포맷으로 변환 및 저장
│   └── main.py            # 실행 진입점 및 파이프라인 조율
├── config/
│   └── settings.py        # 대상 카테고리("미국 경제/비즈니스"), 기간 등 환경설정
└── data/
    └── output/            # 생성된 마크다운 결과물 저장 폴더
```

## 3. 데이터 파이프라인 (Data Pipeline)
1. `main.py` 실행 시 `market.py`를 호출하여 미국 3대 지수 및 섹터 시황을 먼저 수집.
2. 이어서 설정값(`settings.py`)을 로드하여 `scraper.py`를 통해 기사 수집.
3. 획득한 데이터는 `analyzer.py`로 전달되며, 기사 내용 간의 유사도를 검사하여 클러스터(동일 이슈 그룹)를 형성하고 빈도수(중복도) 계산.
4. 데이터는 1순위 발행 시간(최신순), 2순위 클러스터 빈도(내림차순)로 정렬됨.
5. 정렬된 데이터는 `formatter.py`를 거쳐 `data/output/` 내의 `.md` 파일로 가시화 및 저장됨.

---
*Project: news*
