# Changelog

## [Unreleased]
### Added
- [Docs] 미국 증시 데일리 시황 요약 리포트 (data/output/blog_post.md)를 /summary 가이드라인 규정에 맞추어 별표와 샵 기호 없이 재생성.
- [News Scraper KR] 한국 매크로 뉴스 수집 설정에 파이낸셜뉴스 마감시황 RSS 피드 추가 (https://www.fnnews.com/rss/r20/fn_realnews_stock.xml).
- [News Scraper KR] 한국 매크로 뉴스 수집 시 standard RSS 날짜 포맷 파싱 지원을 위해 dateutil.parser 연동 추가.
- [News Scraper KR] 한국 마감시황(Macro & Market) 뉴스를 일반 카테고리와 분리하여 보고서 상단에 독자적인 '## 마감시황' H2 섹션으로 별도 나열 기능 추가.
- [News Scraper KR] 한국 매크로 뉴스 수집용 연합인포맥스 RSS 피드 파서 및 본문 기사 추출 (`newspaper4k` 활용) 기능 추가 (`scraper_kr.py`).
- [News Scraper KR] 한국 경제/비즈니스 설정에 확장 가능한 `macro_rss_feeds` 리스트 구조 및 우선순위 키워드 추가 (`config/settings.py`).
- [News Scraper KR] 한국 특정 기업/종목 뉴스 수집용 네이버 모바일 검색 (`m.search.naver.com`) 웹 스크래핑 기능 추가. 봇 감지 차단 우회를 위한 모바일 헤더 탑재 및 동적 클래스 변경에 견고한(robust) 텍스트-URL 매칭 알고리즘 구현.
- [News Scraper] 구글 뉴스 직접 웹 스크래핑 헬퍼 함수 (`fetch_google_news_web`) 추가.
- [News Scraper] 구글 뉴스 암호화 URL 복원 로직 (`decode_google_news_url`) 구현.
- [News Scraper] "MSN", "Google News" 등 무의미한 정크 타이틀 필터링 로직 강화.
- [News Scraper KR] 한국 특정 기업/종목 특징주 뉴스 수집 시 제목에서 기사 발행일자(publish_date)를 파싱하여 리포트에 기재하는 기능 추가 (`scraper_kr.py`).
- [News Scraper KR] 한국 특징주 뉴스 수집 시 최신순 정렬(`sort=1`) 옵션을 추가하고 전체 뉴스 유효기간(기본 3일) 필터 로직을 엄격하게 적용하여 기간 외 기사 필터링 추가.
- [Market KR] 한국 종목 뉴스 수집 기간을 2일에서 3일로 확대하여 누락 방지.
### Changed
- [News Scraper KR] 한국 특정 기업/종목 특징주 수집 방식을 네이버 일반 웹 검색에서 모바일 뉴스 검색으로 변경하여 안정성 극대화 및 차단 문제 해결.
- [News Scraper KR] 한국 카테고리 기사 수집 시 로컬 디코딩 라이브러리(`googlenewsdecoder`)를 도입해 진짜 URL을 해독하고 차단을 방지.
- [News Scraper KR] 한국 특징주 수집 및 시장 데이터(`market_kr.py`) 반환 구조를 리스트 형식의 딕셔너리로 일관되게 리팩토링하여 보고서에 클릭 가능한 원본 링크(hyperlink)가 렌더링되도록 개선.
- [News Scraper KR] 한글 뉴스 수집 시 기존의 네이버 OpenAPI 요약 생성 의존성을 제거하고 오버헤드 축소.
- [News Scraper] 구글 뉴스 암호화 URL 해독 방식을 로컬 디코딩 라이브러리(`googlenewsdecoder`)로 변경하여 봇 차단을 우회.
- [News Scraper] 카테고리/종목/매크로 미국 뉴스 스크래핑 시 네이버 API 요약 의존성을 제거하고 RSS 기본 description을 사용하도록 변경.
- [News Scraper] 매크로 뉴스 수집 채널을 야후 RSS에서 구글 뉴스 RSS("Stock market today" 검색어 기반 5개 뉴스)로 대체.
- [News Scraper] 미국 종목 뉴스 수집 시 구글 RSS 수집 한도를 10개에서 5개로 제한하고, 구글 검색 결과가 없을 경우에만 야후 파이낸스(`yfinance`)를 백업으로 호출하도록 분기 처리.
- [News Scraper] 뉴스 수집 우선순위 재조정: 구글 뉴스 RSS 검색을 최우선으로 하고 네이버/야후를 보완재로 사용.
- [News Scraper] 정렬 알고리즘 고도화: 단순 키워드 매칭보다 원본 검색 엔진의 랭킹(`original_rank`)을 최우선으로 반영하도록 수정.
- [Docs] PRD 및 ARCH 문서를 최신 수집 및 정렬 정책에 맞게 업데이트.

### Fixed
- [News Scraper] 미국 마감시황 뉴스 수집 시 단일 대용량 검색(max_results=100)으로 인한 구글 차단(HTTP 429) 문제를 예방하기 위해, 야후 파이낸스 및 인베스토피디아 도메인 특화 타겟팅 검색 쿼리를 도입하고 기사 수집 범위를 안정적인 개수로 축소.
- [News Scraper] 구글 뉴스 암호화 URL 일괄 해독 함수(`batch_decode_google_urls`)가 빈 리스트만 반환하던 오류를 해결하기 위해 `decoderv4` 대신 `ThreadPoolExecutor`와 `new_decoderv1`을 사용한 고성능 병렬 디코더로 전면 재구현.
- [News Scraper] 인베스토피디아 및 야후 파이낸스 마감시황 기사의 과도하게 엄격했던 제목 키워드 필터 조건을 완화하여 제목 변동에 따른 기사 누락 방지.
- [News Scraper] 미국 특정 기업 특징주 수집(`fetch_company_news_us`) 시 기사별 개별 디코딩 처리를 적용하여 본문 링크 무결성 보장.
- [News Scraper KR] `scraper_kr.py` 내의 BS4 BeautifulSoup 로컬 섀도우 임포트로 발생하던 `UnboundLocalError` 스코프 버그 해결.
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
