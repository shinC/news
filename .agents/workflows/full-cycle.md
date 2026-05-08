---
description: 기획부터 배포까지 SOP에 따라 순차적 진행
---

tasks:
  - id: planning
    name: "1단계: 기획 및 설계"
    instruction: "@standard_sop 규칙의 Phase 1에 따라 기획안과 아키텍처 문서를 작성해줘."
    wait_for_approval: true # 사용자가 문서를 확인하고 승인해야 다음으로 넘어감

  - id: development
    name: "2단계: 기능 구현"
    instruction: "작성된 docs/들을 참고하여 @standard_sop Phase 2 지침대로 코드를 작성해줘."
    depends_on: [planning]
    wait_for_approval: false

  - id: testing
    name: "3단계: QA 및 검증"
    instruction: "@standard_sop Phase 3에 따라 테스트를 수행하고 결과 리포트를 제출해줘."
    depends_on: [development]
    
  - id: release
    name: "4단계: 릴리즈 준비"
    instruction: "@standard_sop Phase 4에 따라 최종 배포 준비를 완료해줘."
    depends_on: [testing]