# Changelog

## [Unreleased]
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
