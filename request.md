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
- [ ] 4. 
- [ ] 5. 
- [ ] 6. 

## 3. 향후 요구사항 (Backlog)
- [ ] 뉴스 스크래핑 시스템 핵심 기능 구현
  - 대상 사이트: 네이버, 다음, 구글 뉴스 등
- [ ] 데이터 파싱 및 저장 로직 개발
- [ ] 자동화 및 스케줄링 설정
