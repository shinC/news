# 환경 설정 가이드 (Environment Setup)

이 문서는 본 프로젝트의 개발 및 실행 환경 설정을 요약한 문서입니다.

## 1. 기술 스택 기반 (Core Stack)
- **언어**: Python 3.14-slim (Debian 기반)
- **컨테이너 환경**: Docker / OrbStack (또는 Docker Desktop)
- **패키지 관리**: `requirements.txt` (pip 기반)

## 2. Docker 및 개발 환경 설정
### 2.1 시스템 패키지
컨테이너 빌드 시 다음의 필수 도구들이 설치됩니다:
- `build-essential`, `curl`, `wget`, `git`, `procps`, `ca-certificates`, `tzdata`

### 2.2 타임존 및 로케일
- **타임존**: `Asia/Seoul` (대한민국 표준시)로 고정되어 있습니다.

### 2.3 사용자 계정
- **사용자명**: `tripod`
- **권한**: `sudo` 권한이 부여되어 있으며, 보안을 위해 비루트(Non-root) 계정으로 기본 실행됩니다.
- **기본 쉘**: `/bin/bash`

## 3. 터미널 및 쉘 환경 (Shell Customization)
### 3.1 커스텀 프롬프트 (PS1)
터미널의 가독성을 위해 다음과 같이 커스터마이징되었습니다:
- **형식**: `[유저명] ➜ [현재 디렉토리] (현재 브랜치) $`
- **색상**: 유저명은 초록색, 경로는 파란색으로 표시되어 구분이 쉽습니다.
- **Git 연동**: 현재 디렉토리가 Git 저장소일 경우 브랜치명이 실시간으로 표시됩니다.

### 3.2 적용 방법
터미널에서 설정을 즉시 반영하려면 다음 명령어를 실행하십시오:
```bash
source ~/.bashrc
```

## 4. Git 및 무시 설정 (Ignored Files)
### 4.1 .gitignore
Git 추적에서 제외되는 항목들입니다:
- Python 바이트코드 (`__pycache__`, `.pyc`)
- 가상 환경 폴더 (`.venv`, `env`)
- 환경 변수 파일 (`.env`)
- 로그 파일 및 로컬 데이터 (`data/`, `*.log`)
- IDE 설정 파일 (`.vscode`, `.idea`)
- OS 생성 파일 (`.DS_Store`)

### 4.2 .dockerignore
Docker 빌드 시 컨테이너 내부로 복사되지 않는 항목들을 정의하여 빌드 속도와 보안을 최적화했습니다.

## 5. VS Code 통합 (Dev Container)
- **확장 프로그램**: Python, Pylance, Ruff(Linter/Formatter)가 기본 포함되어 있습니다.
- **코드 스타일**: `Ruff`를 사용하여 저장 시 자동 포맷팅 및 임포트 정리가 수행됩니다.
- **자동 설치**: 컨테이너 생성 후 `pip install --upgrade pip`가 자동으로 실행됩니다.

## 6. 일반 도커 환경에서의 실행 방법 (Standard Docker Setup)
VS Code의 Dev Container 기능을 사용하지 않고, 도커만 설치된 환경(Windows, Linux, macOS)에서 동일한 개발 환경을 수동으로 구성하는 방법입니다.

### 6.1 컨테이너 빌드 및 실행
프로젝트 루트 디렉토리에서 터미널을 열고 다음 명령어를 입력합니다:
```bash
# 컨테이너 빌드 및 백그라운드 실행
docker-compose up -d --build
```

### 6.2 컨테이너 내부 접속
컨테이너가 실행된 후, 내부 쉘(`bash`)에 접속하여 개발 작업을 수행할 수 있습니다:
```bash
# 실행 중인 'news' 서비스 컨테이너에 bash로 접속
docker-compose exec news bash
```
접속 후에는 앞서 설정한 커스텀 프롬프트와 Python 3.14 환경을 동일하게 사용할 수 있습니다.

### 6.3 컨테이너 중지
작업이 끝난 후 컨테이너를 종료하려면 다음 명령어를 사용합니다:
```bash
docker-compose down
```

### 6.4 Windows 환경 주의사항
- **WSL2 권장**: Windows 유저는 Docker Desktop과 함께 WSL2(Windows Subsystem for Linux) 환경에서 실행하는 것이 성능과 호환성 면에서 가장 좋습니다.
- **경로 구분자**: PowerShell이나 CMD에서도 위 명령어는 동일하게 작동하지만, 프로젝트 경로는 항상 절대 경로 혹은 현재 디렉토리(`.`)를 기준으로 관리됩니다.

## 7. 타 환경으로의 이전 (Migration)
본 프로젝트는 보안을 위해 API 키와 개인 설정 파일(`.env`, `ki_apikey/`)을 Git 추적에서 제외하고 있습니다. 따라서 회사나 다른 PC에서 프로젝트를 다시 내려받았을 경우, 다음 절차를 따라야 합니다:

### 7.1 환경 변수 설정
1. 프로젝트 루트에 있는 `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
2. 생성한 `.env` 파일에 자신의 키움 API 정보를 입력합니다.
   ```bash
   cp .env.example .env
   # 이후 .env 파일 수정
   ```

### 7.2 키 파일 복구
- `ki_apikey/` 폴더 내의 인증 관련 파일들은 Git에 올라가지 않으므로, 별도의 저장소(USB, 클라우드 등)에 백업해 두었다가 새로운 환경의 동일한 위치에 붙여넣어야 합니다.

---
최종 수정일: 2026-05-10
담당 에이전트: Antigravity
