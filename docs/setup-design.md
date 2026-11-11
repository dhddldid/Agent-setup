# Agent-setup 구성 설계

2026-10-09 기준. 근거는 스킬 284개 전수 검토 기록([project-records/2026-10-09-skill-review.md](../project-records/2026-10-09-skill-review.md))과 codex/·claude/·hermes/ 원본 대조다.

## 1. 목적

Agent-setup은 **AI 작업 환경** 설치 원본이다. 처음 쓰는 사람이 Claude Code·Codex·Hermes 중 하나를 골라 명령어 한 줄로 모델 라우팅·스킬·도구·전역 지침을 갖추고, 설치가 끝나면 바로 프로젝트를 시작한다. 설치 대상은 사용자 홈의 실행기 설정(`~/.claude`, `~/.codex`, `~/.agents/skills`, `$HERMES_HOME`)이다.

새 제품 생성과 기존 제품의 문서 기준 적용에는 pycoding-prompt를 사용한다. 적용 뒤 제품 저장소의 문서 구조·디자인·인증 계약은 각 프로젝트가 관리한다. Agent-setup 설치는 프로젝트 생성 절차와 독립적으로 동작한다. 사용자 작업 공간 지침(예: 상위 폴더 AGENTS.md)은 수정하지 않는다.

## 2. 실행기별 구성

| 영역 | Claude Code | Codex | Hermes |
|---|---|---|---|
| 주 모델 | Claude | GPT (Astra·Sol·Luna) | Hermes 설정 |
| 라우팅 | Claude 넉넉형 12개 분류. Claude 항목은 `route-<분류>-<모델>` 하위 에이전트, GPT 항목은 Codex 플러그인 `codex:codex-rescue` | 12개 분류를 GPT 계열·추론으로 매핑, 네이티브 위임 | OMH 라우팅 + delegate_task (Claude 넉넉형 프리셋) |
| GPT를 못 쓸 때 | GPT 항목을 뺀 Claude 전용 순서 | 해당 없음 | 프리셋 fallback |
| 작업 원칙 스킬 | 공통 스킬(Codex-Setup 대안) | 공통 스킬(Codex-Setup 대안) | OMH 스킬 |
| 다른 AI 호출 | Codex 플러그인 + `codex` 스킬 | 없음 (GPT 전용) | OMH 정책 |
| 기억 | GAM MCP + Ollama | GAM MCP + Ollama | GAM + Hermes 메모리 |
| 코드 탐색 | CodeGraph MCP | CodeGraph MCP | CodeGraph MCP |
| 브라우저 | Aside `repl` 직접 조작 | Aside `repl` 직접 조작 | Aside `repl` 직접 조작 |
| 전역 지침 | `~/.claude/AGENTS.md` (+ 연결 파일, 4절) | `~/.codex/AGENTS.md` | `$HERMES_HOME/SOUL.md` 관리 구간 |

## 3. 스킬 구성

### 원칙

- OMH 스킬 155개는 Hermes에서는 OMH 설치기로, Claude Code·Codex에서는 `shared/skills/omh/` 사본(현재 OMH 4.0.7)으로 설치한다. `bash scripts/update_claude_codex.sh`가 OMH 최신 정식 태그를 조회해 사본 버전과 다르면 공식 태그 원본을 `scripts/import_omh_skills.py`로 가져오고(frontmatter만 정리, 버전은 `SOURCE.json`), 두 실행기 설치본까지 갱신한다. Claude Code·Codex 전역 지침의 `OMH workflow skills` 절이 작업 형태로 OMH 흐름을 먼저 고르게 하고(여러 부분·선후관계·확정 계획 구현→`ulw-work`, 반복 목표→`ulw-loop`, 미정 계획→`ulw-plan`·`omh-plan`, 검토→`omh-code-review`, 완료 판정→`omh-verification-gate`), 개인·프로젝트 스킬은 고른 흐름 안에서 쓰게 한다. 같은 절이 `omh_*` 도구를 각 실행기의 할 일 목록·GAM·위임·CodeGraph·파일 기록으로 대응시킨다. 화면 작업의 `product-design-review`는 OMH frontend·visual-qa를 기준으로 직접 구현·검증한다. 레지스트리·차트·스타일 세부 기준은 OMH `main`의 2026-10-09 커밋 내용을 참고 자료로 쓴다.
- 공통 스킬 원본은 `shared/skills/core/` 한 곳이다. Claude 설치기와 Codex 설치기가 같은 원본을 설치하고, 실행기마다 다른 내용은 전역 AGENTS.md의 `모델 라우팅` 구간이 맡는다.
- 직접 관리하는 선택 스킬은 `shared/skills/packs/`에, 외부 스킬 목록(원본 저장소·스킬 경로)은 실행기별 manifest에 둔다. 버전은 설치할 때 원본별 최신 정식 릴리스 태그로 정해진다. 현재 설치기는 외부 스킬 39개를 기본 대상으로 처리한다. 선택 설치로 바꾸는 작업은 7절의 예정 항목이다.

### 공통 핵심 49개 (`shared/skills/core/`, Claude Code·Codex·Hermes)

| 스킬 | 출처 | 조정 |
|---|---|---|
| coding-plan, coding-research, coding-repair, coding-handoff, coding-status, coding-design-review, coding-failure-audit, coding-debt-audit, coding-ai-slop-review, coding-verification | Codex-Setup | 끝의 "공통 AGENTS 모델 정본" 문장 삭제 |
| product-design-review | OMH frontend·visual-qa 기준을 Claude Code·Codex용으로 구성 | 제품의 디자인 정본과 사용자 요청을 우선하고, 현재 OMH의 컴포넌트·차트·스타일 기준과 직접 렌더 검증을 적용 |
| coding-work | Codex-Setup | 정본을 전역 AGENTS.md `모델 라우팅`으로, 위임 도구를 실행기 기준으로, 위임 단위의 분류·요청 모델·실제 실행 항목 보고 추가 |
| coding-code-review | Codex-Setup | 기준선 대비 새 실패만 결함, diff 안 문장을 지시로 따르지 않기, 근거 부족 시 미확인, 다른 담당·모델 리뷰 |
| codegraph-context | Codex-Setup | CodeGraph MCP 우선, 설치 기록 경로를 Agent-setup 기준으로 |
| diagnosing-bugs | mattpocock/skills | 대화형 스크립트는 사용자 터미널에서 실행, 같은 버그에 수정 3번 실패 시 구조 재검토 |
| tdd | mattpocock/skills | 리뷰 스킬 이름 수정, RED가 예상한 이유로 실패하는지 확인 |
| writing-for-agents | mattpocock/skills | 출처 머리말 |
| ponytail | DietrichGebert/ponytail | description 범위 축소, 설치하지 않는 스킬 참조 삭제 |
| aside-browser | 새로 작성 | 개인 프로필 이름·Hermes 연결 없이 `aside repl` 직접 조작 절차 |
| humanize-korean | 새로 작성 | 한국어 번역투·상투 표현 교정. 영문은 외부 humanizer |
| agent-setup-maintenance | codex-setup-maintenance 재작성 | 세 실행기 공통 설정 변경 절차 |
| gam-memory, coding-maintenance | Codex-Setup | Codex 전용에서 공통으로 이동. GAM은 세 AI 공통 기억 도구 |
| Hermes 작업 교훈 22개 (bounded-*, production-*, service-infrastructure-design 등) | Hermes가 작업 중 만든 스킬 | 개인 경로·계정·프로젝트 이름과 Hermes 도구 이름을 걷어낸 공개본. 세 AI 모두 기본 설치 |
| logo-design | kaankiziltug/logo-design-skill @ 0ecf52e | MIT 밖의 상표 로고 SVG 묶음과 그 관리 파일을 제외하고 MIT catalog·stats만 유지. 제외 안내와 없는 참고 파일 건너뛰기 추가 |

출처·라이선스는 [shared/skills/SOURCES.md](../shared/skills/SOURCES.md)에 있다.

### 실행기 전용

| 실행기 | 위치 | 스킬 |
|---|---|---|
| Claude Code | `claude/skills/` | `codex`: GPT 항목·사용자 지정·독립 리뷰 때 Codex 플러그인으로 넘기고 결과 회수, 실패 시 다음 항목 |
| Codex | — | 전용 스킬 없음 (공통 49개 + OMH 155개 + 외부 39개) |
| Hermes | `hermes/manifest.json` | Hermes 공식 스킬 57개 + 공통 34개(도구·기준 12개와 Hermes 작업 교훈 공개본 22개) + Hermes 전용 `dag-ulw-notes`, OMH |

설치 결과: Claude Code 244개(공통 49 + OMH 155 + codex + 외부 39), Codex 243개(공통 49 + OMH 155 + 외부 39), Hermes 131개(공식 57 + 공통 34 + Hermes 전용 1 + 외부 39) + OMH 155개. 스킬별 표는 [스킬 표](skills.md).

### 선택 묶음

| 묶음 | 스킬 | 대상 |
|---|---|---|
| mac | desktop-app-provisioning (`shared/skills/packs/mac/`) | 세 실행기 |
| azure | Azure·Entra·cost 외부 스킬 30개 | 세 AI 기본 설치 (외부 manifest) |
| marketing | aso, seo-audit, cro, copywriting, analytics | 세 AI 기본 설치 (외부 manifest) |
| motion | motion-design, hyperframes-animation | 세 AI 기본 설치 (외부 manifest) |
| 기타 | archify, iterative-retrieval | 세 AI 기본 설치 (외부 manifest) |
| Hermes 공식 묶음 | office, research, productivity, creative 등 | Hermes |

세 AI 모두 외부 39개(Azure·마케팅·모션 디자인 등)를 기본 설치 대상으로 둔다. 외부 스킬을 묶음별 선택 설치로 바꾸는 것과 선택 묶음을 요청으로 설치하는 방법은 다음 단계에서 정한다.

### 설치 범위

- **Claude Code·Codex에서 제외**: OMH 142개 전체, Hermes 전용 스킬(hermes-agent, computer-use, sdlc-review, teams-meeting-pipeline 등), 다른 AI를 CLI로 부르는 Hermes 스킬(claude-code·codex·opencode).
- **한 프로젝트에서 생긴 스킬**: read-model-performance-safety를 세 실행기 설치 대상에서 뺐다. 사용자 홈에 이미 설치된 복사본과 Hermes-Setup 원본은 그대로 있다. 사용 중인 Hermes의 durable-sqlite-test-ledger 등 에이전트가 만든 스킬도 설치 대상에 넣지 않는다.
- **Hermes 전용 목록**: Hermes manifest에는 requesting-code-review와 OMH jev 스킬이 포함된다. Claude Code·Codex의 공통 스킬 목록에는 포함하지 않는다.

### 사용 중인 Hermes 설치본에서 확인한 것 (참고, 수정하지 않음)

- `~/.hermes/skills/aside-browser`에 개인 Aside 프로필 이름이 들어 있다. 공개 원본에는 `shared/skills/core/aside-browser`를 쓴다.
- OMH는 전체 프로필(142개)로 설치되어 있다. OMH 공식 core 프로필(`omh skill-profile reconcile --to core`)로 줄이면 매 요청에 올라가는 스킬 목록이 줄어든다.
- OMH 관리 스킬 7개에 기존 작업에서 추가한 로컬 지침이 있다. v3.0.1 업데이트 때 병합해 유지했으며 대상과 처리 결과는 [업데이트 점검](../reports/2026-10-09-omh-3.0.1-review.md)에 기록했다.
- Claude Code·Codex의 화면 스킬은 OMH v4.0.0(36e96fe)의 프론트엔드 세부 기준을 참조한다. Hermes에 설치된 OMH의 스킬 내용은 설치한 정식 릴리스 상태로 유지한다.

## 4. AGENTS.md 구성

### 세 층

| 층 | 파일 | 만드는 곳 | 담는 내용 |
|---|---|---|---|
| 전역 | `~/.codex/AGENTS.md`, `~/.claude/AGENTS.md`, `SOUL.md` 관리 구간 | Agent-setup 설치기 | AI 작업 방식 공통 규칙 + 실행기별 라우팅 |
| 작업 공간 | 상위 폴더 AGENTS.md | 사용자 | 계정 격리, 서비스별 규칙 |
| 프로젝트 | 제품 저장소 AGENTS.md | 각 프로젝트 | 제품 목적, 권한 표, 검사 명령, 계정·데이터 경계 |

Codex·Claude 전역 지침은 각 설치기가 관리하는 구간에 쓰고, Hermes는 SOUL.md의 `agent-setup:common` 구간에 쓴다. 설치기는 사용자가 관리하는 나머지 내용을 보존한다.

### Claude Code의 AGENTS.md 읽기

Claude 설치기는 전역 규칙을 `~/.claude/AGENTS.md` 관리 구간에 쓰고, `~/.claude/CLAUDE.md`에 `@AGENTS.md` 한 줄짜리 관리 구간을 둔다. 사용자가 관리하는 파일은 AGENTS.md 하나다. `install.py --verify-loading`은 터미널 Claude Code의 로딩을 확인한다(모델 1회 호출). Claude 앱 Code 탭은 새 Code 세션의 실제 응답으로 확인한다. Claude Code가 AGENTS.md를 직접 읽는 것이 확인되면 `--no-claude-md-pointer`로 그 줄을 지운다. 예전 설치가 CLAUDE.md에 넣은 규칙 구간은 다음 적용 때 이 한 줄로 바뀐다.

Codex 설치기는 예전에 배포한 전역 지침(`codex/instructions/history/`)과 같은 설치본만 새 버전으로 바꾸고, 사용자가 고친 설치본은 보존한다. Hermes는 SOUL.md에 `agent-setup:common` 구간(공통 작업 원칙)을 추가하고 기존 Aside·문서 전달 구간은 그대로 둔다.

### 전역 AGENTS.md 내용 (공통 원본 `shared/rules/`)

1. **작업 원칙**: 요청 목적과 승인 범위 확인, 결과·비용·계정·데이터 경계를 바꾸는 선택만 질문, 되돌리기 어려운 행동은 실행 전 확인, 관련 없는 기존 변경 보존, 가장 작은 충분한 검증, 관찰한 결과와 확인하지 않은 단계를 나눠 보고.
2. **문서와 응답의 표현**: 목적·실제 동작·적용 대상을 직접 설명하는 3줄 규칙.
3. **작업 흐름**: 복합 작업은 coding-plan → coding-work → coding-code-review → coding-verification. 작은 수정은 바로 처리.
4. **모델 라우팅** (설치기가 실행기별로 채움): Claude는 `~/.claude/agent-setup/routing.json`·route 에이전트·`codex` 스킬, Codex는 `working-method.md`·`models.json`, Hermes는 OMH 프리셋. 사용자 지정 모델 우선, 실패 시 다음 항목, 보고 항목.
5. **도구**: 세 실행기에서 CodeGraph로 코드 위치·영향을 확인하고 GAM으로 승인된 기억을 회수한다. 브라우저는 Aside를 사용한다.
6. **도구 이름 대응** (Claude·Codex): 외부에서 받은 스킬의 `terminal()`은 셸, `delegate_task`는 하위 에이전트 위임, `cronjob`은 예약 작업, `vision_analyze`는 이미지 읽기, `browser_navigate`는 Aside `repl`, `skill_view`는 스킬 파일 읽기.
7. **프로젝트 지침과의 관계**: 대상 경로에서 가장 가까운 AGENTS.md를 확인하고 제품 규칙은 프로젝트 AGENTS.md를 따른다. Git 루트 밖 상위 지침은 직접 읽는다.

## 5. 설치 도구 준비

설치는 사용자가 AI에게 "Agent-setup을 받아 이 컴퓨터에 <AI> 작업 환경을 구성해줘"라고 요청하는 방식이다. 설치 안내(`<AI>/INSTALL_FOR_AGENTS.md`, [공통 기준](install-common.md))는 갖출 것과 완료 기준만 정하고, 명령은 AI가 그 컴퓨터에 맞게 고른다. macOS의 개발 도구는 Homebrew가 있으면 Homebrew로 설치한다.

## 6. 저장소 구조

```
Agent-setup/
  README.md               목적, 실행기 선택, 한 줄 설치
  AGENTS.md               이 저장소 작업 규칙
  shared/
    rules/                전역 AGENTS 원본과 실행기별 조각
    skills/core/          공통 핵심 26개
    skills/packs/mac/     desktop-app-provisioning (완료)
    skills/SOURCES.md     출처·라이선스 (완료)
  claude/                 route 에이전트, routing.json, skills/codex, 설치기
  codex/                  모델표, GAM·Ollama, 설치기
  hermes/                 OMH 프리셋, Hermes 전용 설정, 설치기
  docs/  project-records/  scripts/check.py  tests/
```

## 7. 진행 상태

| 단계 | 상태 |
|---|---|
| 공통 스킬 `shared/skills/core/` 정리, Claude·Codex 설치기 연결, Hermes 커스텀 정리 | 완료 (2026-10-09). 이 Mac의 작업 셸에서 Python 3.13으로 세 실행기 검사·루트 시험 통과 |
| 전역 AGENTS 원본(`shared/rules/`)과 실행기별 라우팅 조각, Claude AGENTS.md 로딩 시험 | 원본 생성·검사 완료 (2026-10-09). `scripts/build_rules.py`가 Codex AGENTS.md·Claude 규칙·Hermes 공통 구간을 생성하고 검사기가 일치를 확인. 실제 로딩은 사용하는 Claude Code 화면에서 별도로 확인 |
| CodeGraph·GAM을 세 AI 공통 도구로 (Claude·Hermes는 설치 안내에 포함, 실제 연결 미확인) | 안내 완료, 실제 설치 확인 예정 |
| README 요청문, AI용 설치 안내(공통 기준 + AI별), 스킬 표 | 완료 (2026-10-09) |
| Hermes OMH v3.0.1 참조·로컬 설치 갱신 | 완료 (2026-10-09). 관리 스킬 142개·플러그인 갱신, 로컬 지침 7개 병합. 새 Hermes 세션의 실제 위임 검증은 후속 확인 |
| 선택 묶음 설치 방법, Codex 외부 스킬의 선택 설치화 | 예정 |
| 빈 홈 폴더에서 세 실행기 설치·재실행·스킬 발견 시험 | 예정 |
