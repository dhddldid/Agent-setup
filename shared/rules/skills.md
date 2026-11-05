## 작업 흐름과 스킬

- 일반 답변·작은 수정은 바로 처리한다. 복합 작업의 전체 흐름은 아래 `OMH workflow skills` 절에 따라 OMH 워크플로(ulw-work·ulw-loop·ulw-plan·omh-code-review·omh-verification-gate)로 고른다. coding-plan(요구사항과 검증 방법 연결), coding-work·coding-handoff(분담), coding-code-review(리뷰), coding-verification(완료 판단)은 그 흐름의 각 단계 안에서 기준으로 함께 적용한다.
- 위치·관계 파악은 codegraph-context, 원인 불명 실패는 diagnosing-bugs, 중요한 로직은 tdd, 구현 단순화는 ponytail, 반복 실패와 중단 작업 재개는 coding-repair를 사용한다.
- 실패 처리 감사는 coding-failure-audit, 설계 반례는 coding-design-review, 제품 문구는 coding-ai-slop-review, 기술부채는 coding-debt-audit를 사용한다.
- 화면 작업은 OMH frontend·visual-qa 기준을 Claude Code·Codex에 맞춘 product-design-review로 구현·검증한다. 사용자가 레퍼런스 선택을 요청하거나 에이전트의 제안에 동의하면 실제 사례 최소 5개를 추천하고 사용자가 고른 방향을 구현한다. 그 외에는 제품 목적·기존 브랜드·현재 디자인 기준으로 진행한다.
- shadcn/ui를 쓰는 프로젝트의 컴포넌트 추가·구성·스타일은 shadcn, @shadcn/lint 설치·규칙은 shadcn-lint를 사용한다.
- 한국어 문장 다듬기는 humanize-korean, 영문은 humanizer, AGENTS.md·스킬 작성은 writing-for-agents, 과거 결정 회수·저장은 gam-memory, 기억·기록 정리는 coding-maintenance, 이 AI 작업 환경의 설정 변경은 agent-setup-maintenance를 사용한다.
- 다른 실행기용으로 쓰인 스킬의 도구 이름은 대응 도구로 바꿔 수행한다: `terminal()`은 셸 명령, `delegate_task`는 하위 에이전트 위임, `cronjob`은 예약 작업, `vision_analyze`는 이미지 읽기, `browser_navigate`는 Aside `repl`, `skill_view`는 스킬 파일 읽기.
