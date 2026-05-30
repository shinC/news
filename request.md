# Project Requirements & Requests

이 파일은 프로젝트의 요구사항과 진행된 요청사항을 정리하는 문서입니다.

## 1. 완료된 요청사항 (Completed)
- [x] **프로젝트명 변경**: 템플릿 기본 설정을 `news`로 변경
  - `devcontainer.json`, `docker-compose.yml`, `Dockerfile`, `README.md`, `ARCH.md`, `SETUP.md` 업데이트 완료
- [x] **Git 사용자 설정**: `user.name` 및 `user.email` 구성 완료
  - Name: taeheon shin
  - Email: thshin81@naver.com
- [x] 1. 깃허브에 뉴스스크랩으로 유명한 프로젝트 이용해서 뉴스가져오는 프로젝트 개발
  - 참고 깃허브 - https://github.com/AndyTheFactory/newspaper4k.git
  - 미국 경제, 증시사항을 한눈에 파악하고 요약하기 위한 프로젝트
  - 주요 뉴스사이트에서 경제, 사회, 증권 분야의 최신뉴스를 2틀치를 최신순으로 수집.
  - 헤드라인 별로 리스트로 나열. 
  - 시간이 가장 최우선이고, 그다음이 중복되는 기사들 순으로 나열

- [x] 2. 주가지수 및 장마감 후 섹터/테마 시황 정보 추가
  - 야후 파이낸스(yfinance)를 활용해 미국 3대 지수(S&P 500, 나스닥, 다우존스) 수집.
  - 11개 주요 섹터 ETF의 전일 종가 등락률을 비교해 가장 상승한 섹터와 하락한 섹터 도출.
  - 결과물 상단에 요약 배치 및 데이터 출처(야후 파이낸스) 명시.

## 2. 진행 중인 요청사항 (In Progress)
- [x] 3. 미국 주식 중 거래대금별 상승률 순으로 종목 50개 수집. us_economy_news.md 에 기재  
- [x] 4. 뉴스 스크랩할 시 기업명이나, 특정 산업에 대한 키워드가 있을 경우 우선순위 둔다.  
  - 기사를 파일에 옮겨적을 때 기사 앞에 번호를 매겨서 보기 쉽게 한다.
- [x] 5. 한국 경제 증시사항 파악 및 요약 프로젝트 개발 완료 (독립 실행 구조)
- [x] 6. 미국/한국 상승률 종목 50개 수집 수정 - > 미국/한국 거래대금상위 종목 100개 수집 수정
   - 거래대금상위 100개 중에서 상승률 높은 종목 10개에 대해 이유를 찾아서 100 종목 나열된 아래 뉴스 기재 (종목별 뉴스는 5개 정도로 제한)
 - [x] 7. 한국 뉴스 데이터 수집은 네이버 증권 뉴스에 수집하도록 수정.(아래 url기재) [완료]
  - 네이버증권 주요뉴스 - https://finance.naver.com/news/mainnews.naver
  - 네이버증권 시황 - https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401
  - 네이버증권 기업 - https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=402
  - 네이버증권 많이본 뉴스 - https://finance.naver.com/news/news_list.naver?mode=RANK
  - (각 섹션별 그룹화 출력 기능 포함 구현 완료)
- [x] 8. 특정 기업명(복수 가능) 입력 시 해당 기업 관련 뉴스 스크래핑 기능 추가
  - 한국/미국 기업 구분하여 수집 로직 별도 구현
  - 최신 3일치 뉴스 수집 기준 적용
- [x] 9. 특정 기업명(복수 가능) 입력 시 해당 기업 관련 뉴스 스크래핑 기능 수정
  - 기업명이 제목과 본문에 반드시 기재되어 있어야돼. 실제 관련기업 뉴스를 수집하기 위한 요소. 기업명이 제목에도 없고, 본문에도 없는 관련없는기사에 기업명이 있어도 수집하는 케이스가 많아. 관련있는 기사를 최신순으로 수집해.
- [x] 10. 뉴스데이터 수집 고도화 작업 [완료]
  - 날짜 없는 기사 제외 로직 강화 (확인 불가 시 배제)
  - `market_date` 기준 시점 동기화: 주말이나 공휴일 수집 시에도 해당 장마감 시점의 뉴스를 정확히 매칭하도록 개선
  - GNews + yfinance 하이브리드 수집 체계 구축으로 수집 범위 및 정확도 대폭 향상 (Intel-Apple 등 주요 이슈 누락 해결)

- [x] 11. 현재 문제점 수정요청
 - 주요뉴스 헤드라인 데이터 수집 못함.
 - " name 're' is not defined
05/12/2026 01:35:47 PM - 기사 파싱 실패 (https://news.google.com/rss/articles/CBMiTkFVX3lxTFBtYml6MUUyZkdCRTZSTUM4eFZwb09zRlhnVEN0QkNRSkd6LVY2Wm1iTTVEVF9BYzFrbzZlVnk1cWM2cnlhQ19GTFZIMDZHZw?oc=5): name 're' is not defined" 오류발생
 -  개발 수정하는데 너무 오래 걸림. 테스트는 전체 기사로 하지 말고 몇개 기사 테스트하고 확인.
- [x] 12. 구글뉴스 접속 금지에 따른 코드 수정 [완료]
 - 문제점
  - 빈번한 접속으로 구글 뉴스 RSS 접속 차단
  - 뉴스 URL 디코딩을 위한 리다이텍팅
  - 호출시간에 약간의 지연을 랜덤하게 삽입
 - 해결책.
  - 우선은 본문을 가져오기 위해 url 디코딩한 후 호출하는 부분은 삭제.(구글 url 그대로 수집)
  - 구글 rss는 종목별로 10번 정도 호출, 그리고 정해놓은 산업별로 1번씩정도만 호출.
  - 본문은 우선 가져오지 말고 제목과 링크만 수집. 
  - 우선은 미국뉴스 수집에만 적용. 
- [x] 13. 구글 뉴스 수집 변경

  - 13-1. 카테고리 및 매크로 뉴스
  
  - 매크로 뉴스 수집은 아래 예제처럼 "Stock market today" 으로 구글검색해서 장마감 뉴스 5개 수집
    query = "Stock market today"
    rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
  - 카테고리 뉴스 수집은 그대로 유지.
  - googlenewsdecoder 를 통해 진짜 url 수집
  - naver api를 통해 요약 생성하는 부분은 삭제.
  - 13-2. 특정 종목/기업뉴스
  - 구글 뉴스 rss 검색해서 상위 5개 기사만 수집. 네이버 API요약을 삭제
  - googlenewsdecoder 를 통해 진짜 url 수집 


  - [x] 14. 한글 뉴스 수집 변경

  - 14-1. 카테고리 및 매크로 뉴스
  
  - 매크로 뉴스 수집은 아래 예제처럼 [검색어] 으로 검색해서 장마감 뉴스 수집. 뉴스 url과 검색어는 계속 추가할 수 있게 설계.
  - https://news.einfomax.co.kr/rss/S1N2.xml ["증시-마감"]
  - 본문 URL 링크 수집. 본문 수집.

  - 카테고리 뉴스 수집은 그대로 유지.
  - googlenewsdecoder 를 통해 진짜 url 수집
  - naver api를 통해 요약 생성하는 부분은 삭제.

  - 14-2. 특정 종목/기업뉴스
  - 네이버 검색에서 "특징주 '종목명'" 으로 검색해서 뉴스 5개 수집
  - 원본 URL, 제목 수집. 
- [x] 15. 미국 종목 뉴스 수집 변경

- 미국 주식 종목 상위 100개 중 상승률 상위 20개 및 거래대금 상위 20개 가져와서 뉴스 검색해올 때 단순히 ticker 로만 검색이 아닌 "[ticker] stock why up today" 검색해서 가져오게 해. 
## 3. 향후 요구사항 (Backlog)

- [ ] 뉴스 스크래핑 시스템 핵심 기능 구현
  - 대상 사이트: 네이버, 다음, 구글 뉴스 등
- [ ] 데이터 파싱 및 저장 로직 개발
- [ ] 자동화 및 스케줄링 설정
