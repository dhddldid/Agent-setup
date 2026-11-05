# 세 구성의 차이

2026-10-09 로컬 원본 기준.

| 영역 | Codex | Claude Code | Hermes |
|---|---|---|---|
| 형태 | 사용자 홈 전역 설치기 | `~/.claude` 전역 설치기 | 선택한 Hermes 프로필 설치기 |
| OMH | 12개 분류·작업 원칙을 Codex용으로 재작성 (분류 출처 OMH v4.0.0 README), OMH 최신 정식판 스킬 사본과 작업 형태별 흐름 규칙 | Claude Code 전용 12개 분류 순서·추론, OMH 최신 정식판 스킬 사본과 작업 형태별 흐름 규칙 | 실행 시점의 OMH 최신 정식 릴리스 설치·연결 |
| 라우팅 원본 | codex/11-working-method.md, codex/config/models.json | claude/routes/claude-code.json (실행기별 정책을 시험으로 대조) | hermes/routing-presets/*.json |
| 위임 | Codex 네이티브 위임의 model·reasoning_effort (GPT 모델) | Claude 모델은 route-<분류>-<계열> 에이전트, GPT 모델은 Codex 플러그인 codex:codex-rescue | OMH 라우팅 + delegate_task |
| fallback | 지정 조합을 쓸 수 없으면 제약 보고 | 전역 규칙에 따라 주 에이전트가 다음 항목으로 넘김 | 분류별 후보·전역·자식 공통 fallback + 소스 호환 패치 |
| 스킬 | 241개 (공통 49 + OMH 153 + 외부 39), ~/.agents/skills/ | 242개 (공통 49 + OMH 153 + codex + 외부 39), ~/.claude/skills/ | 130개 (공식 57 + 공통 34 + 외부 39) + OMH, $HERMES_HOME/skills/ |
| 기억·코드 탐색 | GAM·CodeGraph MCP, Ollama 임베딩 | GAM·CodeGraph MCP | GAM·CodeGraph MCP + Hermes 메모리 |
| 전역 지침 | $CODEX_HOME/AGENTS.md·working-method.md·models.json | ~/.claude/AGENTS.md 관리 구간(+ CLAUDE.md의 `@AGENTS.md`), ~/.claude/agent-setup/routing.json | $HERMES_HOME/SOUL.md 관리 구간 |
| 브라우저 | Aside repl 직접 조작 규칙 | Aside repl 직접 조작 규칙 | Aside repl 직접 조작 규칙 |
| Hermes 전용 | — | — | Desktop UI 크기, GPT·Claude 사용량 표시, 문서 폴더 카드, fallback 소스 패치 |
| 설치·복구 | 영수증·백업·재개·복구 | 미리보기·반복 적용·충돌 중단·백업 | 미리보기·반복 적용·충돌 중단 |
| 업데이트 | `bash scripts/update_claude_codex.sh` (Claude Code와 함께) | `bash scripts/update_claude_codex.sh` (Codex와 함께) | `bash hermes/scripts/update.sh` |
| 로컬 시험 | 설치기 단위시험 | 라우팅 에이전트 정합성 + 설치기 단위시험 | 설치 문서 검사 + 설치기 단위시험 |

## 모델

- Codex: Astra·Sol·Luna 계열 (gpt-6-astra, gpt-6.1-sol, gpt-6-luna)
- Claude Code: `claude/routes/claude-code.json`의 GPT·Claude 혼합 순서. Claude 항목은 claude-fable-5-1·claude-opus-5-5·claude-sonnet-5-5·claude-haiku-4-5, GPT 항목은 gpt-6-astra·gpt-6.1-sol·gpt-6-luna. Hermes 프리셋에서 가져온 정책을 Claude Code 원본에서 독립적으로 관리한다.
- Hermes: GPT·Claude 혼합 후보, Claude 넉넉형·GPT 넉넉형 프리셋

## Hermes에서 옮긴 기능

| Hermes 기능 | Codex | Claude Code |
|---|---|---|
| 모델 라우팅 프리셋 (GPT·Claude 혼합) | 기존 GPT 전용 표 유지 | 두 프리셋 이식; GPT 항목은 Codex 플러그인으로 실행 |
| 분류별 fallback 순서 | 해당 없음 (단일 제공자) | 전역 규칙의 다음 항목 위임 절차 |
| Aside repl 직접 조작 | `~/.codex/AGENTS.md` 규칙 | `~/.claude/AGENTS.md` 규칙 |
| desktop-app-provisioning | 선택 묶음 `shared/skills/packs/mac/` | 선택 묶음 `shared/skills/packs/mac/` |
| Desktop UI 크기, 사용량 플러그인, 문서 폴더 카드, fallback 소스 패치 | Hermes 전용 | Hermes 전용 |

## 이관 처리

- 세 원본의 추적 파일을 SHA256 대조 후 복사했다. Git 이력은 원본 저장소에 있다.
- Hermes의 reports/·project-records/·GitHub workflow는 원본 저장소에 두고, hermes/docs/verification.md는 통합 검사 기준으로 바꿨다.
- codex/.gitignore는 허용 목록 방식이다. codex/에 새 파일을 추가하면 허용 목록에도 추가한다.
- 사용 중인 Codex 설치를 이 저장소로 전환할 때는 설치 영수증의 setup_root가 `Agent-setup/codex`를 가리키는지 확인한다.

## 근거

- Codex: [설치 경로](../codex/13-environment-components.md), [모델·위임](../codex/11-working-method.md), [변경·복구](../codex/05-change-management.md), [OMH 출처](../codex/upstream/README.md)
- Claude: [설치·라우팅](../claude/README.md), [라우팅 표](../claude/routes/claude-code.json), [전역 규칙](../claude/templates/global-rules.md), [설치기](../claude/scripts/install.py)
- Hermes: [설치 목록](../hermes/INSTALL-LIST.md), [라우팅](../hermes/docs/model-routing.md), [전역 규칙](../hermes/docs/global-rules.md), [브라우저](../hermes/docs/browsers.md)
