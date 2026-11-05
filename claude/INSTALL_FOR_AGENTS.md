# Claude Code 작업 환경 설치 (AI용)

[설치 공통 기준](../docs/install-common.md)을 따른다. 아래는 Claude Code에 갖출 것과 완료 기준이다. 설치 방법은 AI가 정한다.

## 갖출 것

| 항목 | 기준 |
|---|---|
| Claude Code | 설치·로그인 상태 |
| Codex 플러그인 | `openai/codex-plugin-cc`의 `codex@openai-codex`와 Codex CLI 로그인. GPT 라우팅 항목을 실행한다. 사용자가 GPT를 쓰지 않으면 생략하고, 그 항목은 다음 Claude 항목으로 넘어간다 |
| 모델 라우팅 | Claude 넉넉형 (사용자가 원하면 GPT 넉넉형). 분류별 하위 에이전트 23개와 `agent-setup/routing.json` |
| 스킬 | [스킬 표](../docs/skills.md)의 Claude 열 (공통 49개 + OMH 153개 + codex + 외부 39개) |
| 전역 지침 | `~/.claude/AGENTS.md` 관리 구간, Claude Code가 읽도록 `~/.claude/CLAUDE.md`에 `@AGENTS.md` 한 줄 |
| MCP | CodeGraph, GAM (사용자 범위) |
| Aside | 공통 기준대로 |

외부 스킬 39개(Azure·마케팅·모션 디자인 등)는 Codex와 같은 목록(`../codex/inventories/external-skills.json`)과 설명 조정(`../codex/config/skill-descriptions.json`)을 사용한다. 목록에는 원본 저장소와 스킬 경로만 있고, 설치기가 실행할 때마다 원본별 최신 정식 릴리스 태그와 그 커밋을 조회해 받는다.

설치 뒤 업데이트는 Agent-setup 루트의 `bash scripts/update_claude_codex.sh` 한 줄로 한다. OMH 스킬 사본을 최신 정식 태그로 맞추고 전역 지침·공통 스킬·외부 스킬을 다시 설치한다. `--dry-run`으로 실행할 명령을 먼저 보여줄 수 있다.

설치 대상은 사용자가 실제 사용하는 Claude Code 설정 폴더다. 제공된 설치기와 [구성 안내](README.md)는 참고 자료로 사용한다. 사용자 설정을 보존하고 변경 전 백업을 남기며, 충돌한 파일은 차이를 확인해 처리한다.

이 폴더의 설치 절차는 Claude Code 전역 환경을 준비한다. 제품 생성·기존 제품 기준 적용은 pycoding-prompt의 절차를 따르며, 제품 파일·프로젝트 의존성·lint·CI는 대상 제품 저장소에서 관리한다. CodeGraph 색인과 GAM의 실제 지식·인증 정보는 사용자 데이터 경로에서 관리한다.

## 완료 기준

사용자가 작업할 Claude Code 화면에서 [공통 완료 기준](../docs/verification.md)에 따라 각 항목을 통과·실패·미확인으로 기록한다. Claude 앱 Code 탭과 터미널 CLI는 각각의 실제 상태를 확인한다.

1. 새 Claude Code 세션에서 전역 지침이 실제 응답에 적용된다.
2. 분류별 하위 에이전트 23개와 설치한 Codex 플러그인 에이전트가 발견된다.
3. Claude 후보 하나와 GPT를 사용한다면 GPT 후보 하나가 실제 하위 작업에 응답하고 실행 모델이 확인된다.
4. 관련 요청에서 설치한 스킬이 발견되고 사용된다.
5. CodeGraph·GAM MCP 도구가 실제 결과를 돌려준다. 실제 코드 저장소 하나에서 색인 생성 후 존재하는 심볼이 조회되고, GAM에 시험 기억을 저장·활성화한 뒤 같은 프로젝트 범위 검색으로 회수된다(시험 기억은 확인 후 보관 처리).
6. Aside가 설치 대상이면 선택한 프로필에서 페이지 결과를 읽을 수 있다.
