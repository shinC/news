# Changelog

## [Unreleased]
### Added
- [News Scraper] 구글 뉴스 직접 웹 스크래핑 헬퍼 함수 (`fetch_google_news_web`) 추가.
- [News Scraper] 구글 뉴스 암호화 URL 복원 로직 (`decode_google_news_url`) 구현.
- [News Scraper] "MSN", "Google News" 등 무의미한 정크 타이틀 필터링 로직 강화.
- [Market KR] 한국 종목 뉴스 수집 기간을 2일에서 3일로 확대하여 누락 방지.

### Changed
- [News Scraper] 구글 뉴스 암호화 URL 해독 방식을 로컬 디코딩 라이브러리(`googlenewsdecoder`)로 변경하여 봇 차단을 우회.
- [News Scraper] 카테고리/종목/매크로 미국 뉴스 스크래핑 시 네이버 API 요약 의존성을 제거하고 RSS 기본 description을 사용하도록 변경.
- [News Scraper] 매크로 뉴스 수집 채널을 야후 RSS에서 구글 뉴스 RSS("Stock market today" 검색어 기반 5개 뉴스)로 대체.
- [News Scraper] 미국 종목 뉴스 수집 시 구글 RSS 수집 한도를 10개에서 5개로 제한하고, 구글 검색 결과가 없을 경우에만 야후 파이낸스(`yfinance`)를 백업으로 호출하도록 분기 처리.
- [News Scraper] 뉴스 수집 우선순위 재조정: 구글 뉴스 RSS 검색을 최우선으로 하고 네이버/야후를 보완재로 사용.
- [News Scraper] 정렬 알고리즘 고도화: 단순 키워드 매칭보다 원본 검색 엔진의 랭킹(`original_rank`)을 최우선으로 반영하도록 수정.
- [Docs] PRD 및 ARCH 문서를 최신 수집 및 정렬 정책에 맞게 업데이트.

### Fixed
- [News Scraper] US 뉴스 스크래퍼(`scraper.py`)의 요약 품질 개선: 본문 추출 실패 시 구글/야후 검색 스니펫을 활용하는 다중 폴백 시스템 및 제목 유사도 체크 로직 추가.
- [News Scraper] 구글 뉴스 암호화 URL (`/articles/`) 디코딩 로직 보강 및 예외 처리 강화.
### Added
- Added `yfinance` to `requirements.txt` to fetch US market indices and sector ETFs.
- Added `src/core/market.py` to collect S&P 500, NASDAQ, Dow Jones, and Top/Bottom performing sectors.
- Added logic in `src/core/market.py` to collect the top 50 high-volume US stocks sorted by percentage increase.
- Updated `src/main.py` and `src/core/formatter.py` to include market data and top 50 stocks table at the top of the Markdown report.
- Added `docs/PRD.md` and `docs/ARCH.md` for US Economy News Scraper.
- Added `config/settings.py` with Google News configuration for "US Economy Business" and `priority_keywords`.
- Added `src/core/scraper.py` using `newspaper4k` and `GoogleNewsSource`, applying priority score based on keywords.
- Added `src/core/analyzer.py` for NLP-based article clustering using TF-IDF and Cosine Similarity, sorted by priority score, date, and cluster size.
- Added `src/core/formatter.py` to output clustered articles as Markdown, with numbered article lists.
- Added `src/main.py` pipeline.
- Expanded US and KR top stocks collection from 50 to 100.
- Added automatic news search for the top 10 highest gaining stocks to include 'reason for rise' in the markdown table.
- Replaced Google News scraper in `src/core/scraper_kr.py` with direct scraping from Naver News (Economy section) for localized and accurate Korean news.
- Added `src/main_kr.py` pipeline for Korean Economy & Business News.
- Added `src/core/market_kr.py` utilizing `BeautifulSoup` to scrape Naver Finance (Indices, Top Stocks by Trading Value, and Themes).
- Added `src/core/scraper_kr.py` to fetch Korean news via Google News.
- Updated `config/settings.py` with `SettingsKR` class for Korean specific keywords and settings.
- Refactored `src/core/formatter.py` to be generic for both US and KR reports.

- Added `.dockerignore` for best practices.
- Added `.gitignore` to exclude environment files, logs, and IDE settings.
- Added `requirements.txt` with pinned stable versions for core libraries (BeautifulSoup4, Playwright, Pydantic, etc.).

### Changed
- Updated Python version to **3.14** (latest stable as of May 2026) in `Dockerfile` and `ARCH.md`.
- Updated `Dockerfile` to automatically install dependencies from `requirements.txt`.
- Standardized `Dockerfile` for Dev Container and production parity (added `ca-certificates`, `tzdata`).
- Standardized `docker-compose.yml` to use `command: sleep infinity` for stable dev environment.
- Standardized `.devcontainer/devcontainer.json` to include Ruff formatter and common settings.
- Customized terminal prompt (`PS1`) in `Dockerfile` and `~/.bashrc` to show user, directory, and git branch.
- Created `docs/SETUP.md` to document the environment setup in Korean.

### Fixed
- Synchronized `remoteUser` in `devcontainer.json` with `USERNAME` in `Dockerfile` (set to `tripod`).
- Fixed remote connection error in OrbStack/VS Code Remote by adding `wget` to `Dockerfile`.
