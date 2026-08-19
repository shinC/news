# 에이전트 파일 작성 규칙 (Agent File Writing Rules)

## 한국어 및 한글 파일 작성 규칙 (CRITICAL: Korean File Encoding Rule)
- 한글이 포함된 텍스트 파일을 새로 작성하거나 수정할 때는 **절대로 쉘 명령어(`run_command`를 통한 `cat`, `echo`, `printf` 등)를 사용하여 파일로 쓰거나 덮어쓰지 마십시오.**
- 쉘의 인코딩 불일치 및 입력 버퍼의 한계로 인하여 다량의 한글 텍스트 저장 시 마지막 부분의 바이트가 깨지는 현상(``)이 발생합니다.
- 반드시 시스템 제공 API인 `write_to_file` 또는 `replace_file_content` 도구를 사용하여 파일을 작성하십시오.
- 이는 영구적인 규칙이며, 모든 한국어 파일 쓰기 작업에 필수적으로 적용됩니다.

## Do NOT Use Shell Redirection for File Creation
- NEVER run command line operations like `cat > filepath << 'EOF'` to create or update files containing non-ASCII / Korean characters.
- ALWAYS use the `write_to_file` tool to save or update workspace files securely.

## 불필요한 run_command 실행 금지 (CRITICAL)
- `blog_post.md` 등 결과물 파일을 작성하기 전에 파일 존재 여부를 확인하는 `run_command`(예: `cat`, `ls`, `head` 등)를 절대 실행하지 마십시오.
- `write_to_file` 도구는 파일이 없으면 자동 생성하고, 있으면 `Overwrite: true` 옵션으로 덮어씁니다. 사전 확인이 필요 없습니다.
- /summary, /summary-kr 등 뉴스 요약 워크플로우 실행 시 흐름: us_economy_news.md 읽기 → (필요 시) read_url_content로 원문 확인 → write_to_file로 blog_post.md 바로 저장. run_command는 이 흐름에 포함되지 않습니다.
- 이 규칙을 어기면 불필요한 토큰 낭비가 발생합니다.
