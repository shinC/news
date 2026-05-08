# news

이 프로젝트는 최신 Python 3.14 환경을 기반으로 한 뉴스 스크래핑 시스템입니다. VS Code Dev Container를 사용하여 즉시 표준화된 개발 환경을 구축할 수 있습니다.

## 주요 특징
- **Python 3.14**: 최신 안정화 버전 Python 제공.
- **Dev Container**: VS Code에서 즉시 사용 가능한 사전 설정된 개발 환경.
- **Standardized Tools**: Ruff(Formatter/Linter), Git 브랜치 표시 PS1 등 포함.
- **SOP 기반**: 프로젝트 관리를 위한 표준 운영 절차(SOP) 문서 포함.

## 시작하기 (Getting Started)

### 1. VS Code Dev Container (추천)
1. 프로젝트를 VS Code로 엽니다.
2. 우측 하단의 **"Reopen in Container"** 팝업을 클릭하거나, 명령 팔레트(`F1`)에서 `Dev Containers: Reopen in Container`를 선택합니다.
3. 모든 설정이 자동으로 완료될 때까지 기다립니다.

### 2. 일반 도커 환경
```bash
docker compose up -d --build
docker compose exec news bash
```

## 프로젝트 구조
```text
.
├── .agents/          # AI 규칙, 스킬 및 워크플로우
├── .devcontainer/    # VS Code Dev Container 설정
├── docs/             # 설계 및 설정 문서 (ARCH, SETUP)
├── src/              # 소스 코드
├── config/           # 설정 파일
├── tests/            # 테스트 코드
├── Dockerfile        # 도커 빌드 설정
└── docker-compose.yml # 컨테이너 오케스트레이션
```

## 가이드 문서
- [환경 설정 가이드](docs/SETUP.md)
- [아키텍처 설계 가이드](docs/ARCH.md)

---
Created for news scraping project.
