# `shared/rules/omh.md` 한국어 안내 — 에이전트는 영문 원본을 로드한다

영문 원본: [shared/rules/omh.md](../../../../shared/rules/omh.md). Claude Code·Codex 전역 지침에 들어가는 규칙을 한국어로 설명한다.

## OMH 워크플로 스킬

OMH(oh-my-hermes) 워크플로 스킬(`omh-*`, `ulw-*`)이 설치되어 있다. 어떤 언어로 받은 작업이든 행동하기 전에 작업 형태에 맞춰 전체 흐름을 직접 고른다.
- 여러 부분을 순서대로 진행하거나 병렬로 처리할 작업은 `ulw-work`를 작업 라인으로 나눠 쓴다. (`dag-ulw`는 Hermes의 `omh_dag` 런타임이 필요하므로 이 실행기에서는 같은 형태를 `ulw-work` 작업 라인으로 처리한다.)
- 승인된 계획을 여러 작업 라인으로 나누어 구현할 때는 `ulw-work`를 쓴다.
- 조사·구현·검증을 반복해야 하는 장기 목표에는 `ulw-loop`를 쓴다.
- 아직 결정되지 않았거나 위험이 큰 계획에는 `ulw-plan` 또는 `omh-plan`을 쓴다.
- 리뷰에는 `omh-code-review`를 쓴다.
- 범위가 작고 명확한 수정 하나, 일반 답변, 한 번에 끝나는 조회는 바로 처리한다.
선택한 워크플로 스킬을 불러 절차를 따른다. 완료를 선언하기 전에는 `omh-verification-gate`를 불러 검증 기준을 따른다.

- 개인·프로젝트 스킬(GAM, CodeGraph, Aside, coding-*, 프로젝트 스킬)은 선택한 워크플로 안에서 프로젝트 규칙, 계정, 도구, 점검 기준에 적용한다. 각 작업 라인에서도 관련 스킬을 불러온다. 이 스킬들은 워크플로 안에서 실행되고 선택한 워크플로는 그대로 유지한다. 같은 일에 coding-* 스킬과 OMH 스킬이 함께 맞으면 OMH 절차를 따르고 coding-* 스킬의 보고·검증 기준을 함께 적용한다.
- OMH 스킬은 Hermes 도구 이름을 쓴다. 이 실행기에서는 대응 수단으로 같은 결과를 만든다: `omh_todo`는 실행기의 할 일 목록, `omh_memory`는 GAM(gam-memory), `omh_delegate_route`·`delegate_task`는 아래 모델 라우팅에 따른 위임, `omh_jev_ask`는 다른 모델 계열에 맡긴 독립 검토, `omh_codegraph_summary`는 CodeGraph, `omh_agent_board`·`omh_run_summary`는 작업 폴더의 Markdown 기록, `omh_reviewed`·`omh_operation_artifact`는 결과 파일과 검증 기록이다. 그 밖의 `omh_*` 도구는 같은 산출물을 파일과 명령으로 만든다.
- OMH 기록은 작업 대상 저장소의 `.omh/`에 둔다. 준비한 계획·인계 내용과 실제 실행·검증 결과를 구분해 보고한다.
