# Agent-setup

**AI 작업 환경 설치 원본.** Claude Code·Codex·Hermes 중 쓰고 싶은 AI를 골라 아래 요청 한 문장을 AI에게 보내면, AI가 이 저장소를 읽고 그 컴퓨터(macOS·Windows)에 맞는 방법으로 모델 라우팅·스킬·도구·전역 지침을 설치하고 실제 동작까지 확인한다. 설치가 끝나면 바로 프로젝트를 시작하면 된다.

| AI | 이런 사람에게 | 지원 OS | 설치 안내 (AI가 읽는 문서) |
|---|---|---|---|
| Claude Code | Claude를 주로 쓰고, 필요할 때 GPT(Codex)도 섞어 쓰고 싶다 | macOS, Windows | [claude/INSTALL_FOR_AGENTS.md](claude/INSTALL_FOR_AGENTS.md) |
| Codex | ChatGPT·Codex(GPT)만 쓴다 | macOS (Windows는 WSL2) | [codex/INSTALL_FOR_AGENTS.md](codex/INSTALL_FOR_AGENTS.md) |
| Hermes | Hermes Desktop에서 GPT·Claude를 함께 쓴다 | Apple Silicon Mac | [hermes/INSTALL_FOR_AGENTS.md](hermes/INSTALL_FOR_AGENTS.md) |

**바로 보기:** [네 가지 라우팅 비교](docs/model-routing-comparison.md) · [Hermes에서 Agent-setup과 OMH 역할](hermes/docs/omh-and-agent-setup.md) · [Codex 라우팅](#codex--gpt-전용) · [Claude Code 라우팅](#claude-code--claudegpt-혼합) · [Hermes 라우팅](#hermes--omh-분류별-위임) · [설치 요청](#ai에게-보낼-요청) · [설치 구성](#설치되는-것)

## 모델 라우팅

작업을 12개 분류로 나누고, 분류에 맞는 모델과 추론 강도로 실행한다. 아래 표는 **이 저장소의 설치 원본**을 보여준다. 기본 프리셋은 Claude Code·Hermes 모두 `claude-generous`이며, 실행기별 모델 순서와 추론은 각 원본에서 독립적으로 관리한다.

### 표 읽는 법

- **모델 순서**: 왼쪽 모델을 먼저 사용하고, 사용 불가·한도·인증 등의 실패가 발생하면 해당 실행기의 fallback 절차로 다음 후보를 시도한다.
- **추론 강도**: `low`는 단순 확인, `medium`은 일반 작업·문서, `high`는 깊은 구현, `xhigh`는 복잡한 추론·설계에 배정한다. `deep-work`는 OMH v4.0.0을 따라 세 AI 모두 `max`를 사용한다. 표의 추론 값은 같은 행의 모든 후보에 적용한다.
- **적용 대상**: 현재 대화의 주 에이전트가 목표·범위·결과를 관리하고, 중요한 작업 단위에 실행기별 모델·추론을 배정한다. 작은 문서 수정과 일반 답변은 주 에이전트가 직접 처리한다.
- **프리셋 선택**: Claude 넉넉형과 GPT 넉넉형의 실제 차이는 아래 후보 순서에 있다. 작업별로 GPT와 Claude를 함께 사용한다.

| 표의 이름 | 정확한 모델 ID |
|---|---|
| Astra | `gpt-6-astra` |
| Sol | `gpt-6.1-sol` |
| Luna | `gpt-6-luna` |
| Fable | `claude-fable-5-1` |
| Opus | `claude-opus-5-5` |
| Sonnet | `claude-sonnet-5-5` |
| Haiku 4.5 | `claude-haiku-4-5` |
| Haiku 5.5 | `claude-haiku-5-5` |

### Codex — GPT 전용

Codex 네이티브 위임에 모델 ID와 `reasoning_effort`를 지정한다. 사용자가 모델을 지정하면 그 지시가 우선하며, 지정 조합을 사용할 수 없으면 제약을 보고한다.

| 작업 분류 | 적용 작업 | 모델 | 추론 |
|---|---|---|---|
| `ultrabrain` | 복잡한 추론·불확실한 문제 | Astra | `xhigh` |
| `deep` | 깊은 구현·디버깅 | Sol | `high` |
| `architect` | 시스템 설계 | Astra | `xhigh` |
| `unspecified-high` | 분류 외 복합 작업 | Sol | `medium` |
| `unspecified-low` | 분류 외 단순 작업 | Luna | `low` |
| `quick` | 좁은 탐색·빠른 확인 | Luna | `low` |
| `writing` | 문서 작성 | Sol | `medium` |
| `visual-engineering` | 화면 구현 | Sol | `high` |
| `artistry` | 창의적 설계 | Astra | `high` |
| `capable` | 일반 실행 | Sol | `medium` |
| `simple-work` | 단순 실행 | Luna | `low` |
| `deep-work` | 복합 실행 | Sol | `max` |

원본: [작업 분류·추론·위임 기준](codex/11-working-method.md), [계열별 모델 ID](codex/config/models.json).

### Claude Code — Claude·GPT 혼합

Claude 후보는 `route-<분류>-<계열>` 하위 에이전트로 실행한다. GPT 후보는 Codex 플러그인 `codex:codex-rescue`에 모델·추론을 지정해 실행하며, 해당 컴퓨터의 Codex 로그인과 사용 한도를 쓴다. 후보 실행이 실패하면 주 에이전트가 같은 작업을 다음 후보에 넘긴다. GPT 사용이 어려운 환경은 GPT 항목을 뺀 Claude 전용 순서를 사용한다.

| 작업 분류 | 적용 작업 | Claude 넉넉형 · 기본 | GPT 넉넉형 | 추론 |
|---|---|---|---|---|
| `ultrabrain` | 가장 깊은 추론이 필요한 모호한 문제 | Astra → Fable → Opus | Astra → Fable → Opus | `xhigh` |
| `deep` | 깊은 구현·디버깅 | Sol → Fable → Opus | Sol → Fable → Opus | `high` |
| `architect` | 아키텍처·시스템 경계 설계 | Fable → Astra → Opus | Fable → Astra → Opus | `xhigh` |
| `unspecified-high` | 분류 밖의 복합 작업 | Opus | Opus | `medium` |
| `unspecified-low` | 분류 밖의 단순 작업 | Opus | Opus | `low` |
| `quick` | 좁은 탐색·빠른 확인 | Luna → Fable → Opus → Astra | Luna → Fable → Opus → Astra | `low` |
| `writing` | 문서 작성·편집 | Opus → Sol | Sol → Opus | `medium` |
| `visual-engineering` | 화면·프론트엔드 구현 | Fable → Opus → Astra | Fable → Astra → Opus | `high` |
| `artistry` | 창의적 설계·시각 방향 | Fable → Opus → Astra | Fable → Astra → Opus | `high` |
| `capable` | 일반 실행 | Fable → Opus → Sonnet → Astra | Fable → Astra → Opus → Sonnet | `medium` |
| `simple-work` | 단순 실행 | Luna → Fable → Opus → Haiku 4.5 | Luna → Fable → Opus → Haiku 4.5 | `low` |
| `deep-work` | 길고 까다로운 복합 실행 | Opus → Sol | Opus → Sol | `max` |

원본: [두 프리셋의 모델·순서·추론](claude/routes/claude-code.json). 설치와 실제 호출 확인은 [Claude Code 안내](claude/README.md#모델-라우팅)를 따른다.

### Hermes — OMH 분류별 위임

OMH에서 작업 분류를 선택한 직후 `delegate_task`로 위임한다. GPT 후보는 `openai-codex`, Claude 후보는 `anthropic` 제공자에 연결한다. 선택한 Hermes 프로필의 라우팅을 적용하며, 외부 Codex·Claude Code 프로세스를 실행할 때는 해당 실행기의 정책을 따른다.

| 작업 분류 | 적용 작업 | Claude 넉넉형 · 기본 | 추론 | GPT 넉넉형 | 추론 |
|---|---|---|---|---|---|
| `ultrabrain` | 가장 깊은 추론이 필요한 모호한 문제 | Astra → Opus | `xhigh` | Astra → Opus | `xhigh` |
| `deep` | 깊은 구현·디버깅 | Opus → Sol | `high` | Sol → Opus | `high` |
| `architect` | 아키텍처·시스템 경계 설계 | Opus → Astra | `xhigh` | Astra → Opus | `xhigh` |
| `unspecified-high` | 분류 밖의 복합 작업 | Sol → Opus | `medium` | Opus | `medium` |
| `unspecified-low` | 분류 밖의 단순 작업 | Sol → Sonnet | `low` | Opus | `low` |
| `quick` | 좁은 탐색·빠른 확인 | Luna → Opus | `low` | Luna → Opus → Astra | `low` |
| `writing` | 문서 작성·편집 | Opus → Sonnet → Sol | `medium` | Sol → Opus | `medium` |
| `visual-engineering` | 화면·프론트엔드 구현 | Opus | `high` | Astra → Opus | `high` |
| `artistry` | 창의적 설계·시각 방향 | Opus | `high` | Astra → Opus | `high` |
| `capable` | 일반 실행 | Opus → Sol | `medium` | Astra → Opus → Sonnet | `medium` |
| `simple-work` | 단순 실행 | Luna → Haiku 5.5 | `low` | Luna → Opus → Haiku 4.5 | `low` |
| `deep-work` | 길고 까다로운 복합 실행 | Opus → Sol | `max` | Opus → Sol | `max` |

Hermes는 **분류별 후보 순서**와 **실행 중 공통 fallback**을 각각 설정한다.

| fallback 적용 대상 | 순서 | 동작 |
|---|---|---|
| 주 에이전트 | Opus | 현재 주 모델에서 fallback이 필요할 때 사용 |
| 위임 자식 공통 | Opus → Astra → Sonnet | 이미 시도한 모델·사용 불가능한 후보를 건너뛰고, 배정한 추론 강도를 유지 |
| GPT로 시작한 자식 | 공통 순서와 같음. 선택 호환 패치를 적용하면 Astra → Sonnet → Opus | `configure_gpt_fallback.py` 적용 시에만 바뀜 (2026-10-20 이 Mac 미적용) |

원본: [Claude 넉넉형](hermes/routing-presets/claude-generous.json), [GPT 넉넉형](hermes/routing-presets/gpt-generous.json). 프리셋 적용 요청·전환 명령·fallback 검증은 [Hermes 라우팅 안내](hermes/docs/model-routing.md)에 있다.

### 실제 적용 확인

설치 후에는 저장한 설정과 실제 실행 모델을 각각 확인한다. Codex는 위임 결과의 모델·추론, Claude Code는 Claude 하위 에이전트와 GPT 플러그인 호출 결과, Hermes는 `omh model-chains show --json`과 실제 자식 실행 결과를 대조한다. 호스트가 반환한 모델·제공자·추론을 근거로 보고하며, 관측되지 않은 항목은 미확인으로 남긴다. [설치 완료 기준](docs/verification.md)에 실행기별 확인 범위가 있다.

## AI에게 보낼 요청

파일과 명령을 쓸 수 있는 AI 대화에 하나를 골라 보낸다. 무엇을 어떻게 설치할지는 AI가 이 저장소의 설치 안내와 그 컴퓨터 상태를 보고 정한다.

| AI | 요청 |
|---|---|
| Claude Code | `https://github.com/PyeongsaengCoding/Agent-setup 를 받아 이 컴퓨터에 Claude Code 작업 환경을 구성해줘.` |
| Codex | `https://github.com/PyeongsaengCoding/Agent-setup 를 받아 이 컴퓨터에 Codex 작업 환경을 구성해줘.` |
| Hermes | `https://github.com/PyeongsaengCoding/Agent-setup 를 받아 이 컴퓨터에 Hermes 작업 환경을 구성해줘.` |

설치를 맡은 AI는 고른 AI의 설치 안내(`<AI 폴더>/INSTALL_FOR_AGENTS.md`)를 따른다. 지금 설치된 것을 먼저 확인하고, 사용자가 직접 고친 설정은 덮어쓰지 않으며, 로그인·권한·충돌만 사용자에게 묻고, 실제 동작 확인 뒤 완료한 것과 남은 것을 알려준다.

## 설치되는 것

| 항목 | Claude Code | Codex | Hermes |
|---|---|---|---|
| 모델 라우팅 | 12개 분류별 Claude 하위 에이전트 + GPT는 Codex 플러그인 | 12개 분류별 GPT 모델·추론 | OMH 프리셋 |
| 스킬 | 233개 (공통 49 + OMH 144 + codex + 외부 39) | 232개 (공통 49 + OMH 144 + 외부 39) | 130개 (공식 57 + 공통 34 + 외부 39) + OMH 144 |
| 전역 지침 | `~/.claude/AGENTS.md` | `~/.codex/AGENTS.md` | `SOUL.md` 관리 구간 |
| 코드 탐색 | CodeGraph | CodeGraph | CodeGraph |
| 기억 | GAM | GAM | GAM + Hermes 메모리 |
| 브라우저 | Aside | Aside | Aside |
| 보존 정리 | 주 1회 자동 (아래 [저장 데이터 보존](#저장-데이터-보존)) | 같음 | 같음 + Hermes 내장 정리 |

## 스킬

세 AI가 같은 작업 절차를 쓰도록 맞춘다. Hermes에서 쓰는 OMH 워크플로와 Hermes가 작업 중 만든 교훈 스킬을 Claude Code·Codex에도 설치한다. 스킬별 상세는 [스킬 표](docs/skills.md)에 있다.

| 묶음 | 개수 | 내용 | Claude Code | Codex | Hermes |
|---|---|---|---|---|---|
| 작업 원칙 | 16 | coding-plan·coding-work·coding-handoff·coding-status·coding-research·coding-repair·coding-code-review·coding-verification·coding-design-review·coding-failure-audit·coding-debt-audit·coding-ai-slop-review·diagnosing-bugs·tdd·ponytail·product-design-review | ✅ | ✅ | OMH가 같은 일 |
| 도구·글쓰기·디자인 | 11 | codegraph-context·gam-memory·coding-maintenance·agent-setup-maintenance·aside-browser·humanize-korean·humanizer·writing-for-agents·shadcn·shadcn-lint·logo-design | ✅ | ✅ | ✅ (writing-for-agents 제외) |
| Hermes 작업 교훈 | 22 | 운영 실패 진단·관리 API 일괄 작업·서비스 인프라 설계·읽기 모델 성능·SQLite 시험 기록·서브프로세스 기한·미디어 제작·모바일 앱 베타·Android 기기 검증·참고 링크 도입 검토 등 | ✅ | ✅ | ✅ |
| OMH 워크플로 | 144 | 계획(planner 19)·검토(reviewer 23)·운영(operator 38)·안내(guide 21)·추적(tracker 18)·ultrawork 9·조사(researcher 8)·기억(memory-keeper 5)·인계(handoff-guide 3) | ✅ 사본 | ✅ 사본 | ✅ OMH 설치기 |
| 외부 업무 | 39 | Azure·Entra 26, Azure 비용 4, 마케팅 5 (seo-audit·aso·analytics·cro·copywriting), 모션 디자인 2 (motion-design·hyperframes-animation), archify, iterative-retrieval | ✅ | ✅ | ✅ |
| Hermes 공식 | 57 | Hermes 내장 도구용 스킬 (메일·문서·미디어·연구 등) | — | — | ✅ |
| 실행기 전용 | 1 | codex: GPT 항목을 Codex 플러그인으로 넘기고 결과 회수 | ✅ | — | — |

Claude Code·Codex의 전역 지침은 OMH 스킬이 쓰는 Hermes 도구 이름(`omh_todo`, `omh_memory`, `delegate_task` 등)을 각 실행기의 할 일 목록·GAM·위임으로 대응시킨다.

## Hermes에서 Agent-setup과 OMH가 함께 동작하는 방식

Hermes에는 Agent-setup이 설치한 구성과 OMH가 설치한 구성이 함께 있다. Agent-setup은 작업 원칙·스킬·모델 정책·도구 연결을, OMH는 작업 분류·워크플로 스킬·분류별 위임 모델을 맡는다. Claude Code·Codex는 OMH를 실행하지 않고 OMH 스킬 사본만 쓴다. 상세는 [역할 나눔](hermes/docs/omh-and-agent-setup.md)에 있다.

| 영역 | Agent-setup에만 | OMH에만 | 둘 다 있을 때 |
|---|---|---|---|
| 스킬 | 공식 57·공통·외부 스킬, 작업 중 만든 스킬 (`~/.hermes/skills`) | 워크플로 144개 (`~/.local/share/omh/current/skills`) | 같은 이름이면 `프로젝트 → ~/.hermes/skills → 외부 폴더(OMH)` 순서로 Agent-setup 쪽을 쓴다. 역할만 겹치면 요청에 맞는 쪽을 고른다 |
| 지침 | `SOUL.md`의 공통 원칙·OMH 워크플로 사용(작업 형태로 OMH 흐름을 먼저 고르고 사용자 스킬은 그 안에서 사용, 위임 전 OMH 라우팅)·Aside·문서 전달 | 매 턴 분류 힌트, 프로젝트 `AGENTS.md`의 OMH 구간 | 사용자 지시 → 프로젝트 `AGENTS.md` → 전역 지침 순서. 말투·언어는 `SOUL.md` |
| 모델 라우팅 | 설치 프리셋, 메인 대화 기본 모델 | 분류별 기본 체인, 실행값 `~/.omh/routing/model-chains.json` | 프리셋을 넣은 분류는 `override`로 OMH 기본값보다 우선하고 업데이트 뒤에도 유지된다. 하위 에이전트에만 적용되고 메인 대화·cron은 Hermes 기본 모델 |
| 기억 | GAM: 프로젝트 결정·해결 경험 | OMH 기억: Hermes 작업 교훈 | 프로젝트 지식은 GAM에 두어 세 AI가 함께 쓴다 |
| 코드 탐색·브라우저 | CodeGraph, Aside 조작 규칙 | 색인 갱신·브라우저 범위 안내 워크플로 | 실제 도구는 CodeGraph·Aside, 범위 확인은 OMH 안내를 함께 따른다 |
| 플러그인·본체 | 사용량 표시·웹 검색 중계, Discord 보고(Discord를 쓰는 사용자만 선택 설치), Hermes 본체·provider-usage 수정 묶음(`hermes/patches/`: 계정 선택·사용량 표시·모델별 계정 쿨다운 등), fallback 호환 패치 | `omh` 플러그인 | 이름이 달라 함께 등록된다. Hermes 본체와 provider-usage는 최신 정식 릴리스 위에 수정 묶음을 적용해 쓰고, `hermes/scripts/apply_local_patches.py`로 적용 상태를 확인한다 |
| 프로젝트 식별 | 없음 | Git 원격 주소로 프로젝트 자동 식별 | 프로젝트마다 할 초기화는 없다. `omh memory project-identity show`가 `unresolved`인 프로젝트만 `omh memory project-identity init`을 실행한다. OMH 4.0.0에는 `omh init` 명령이 없다 |
| 업데이트 | `hermes/scripts/update.sh` 한 줄 명령, 외부 구성요소 고정값 확인(`scripts/check_releases.py`) | `omh update`가 자기 패키지·스킬 갱신 | [한 줄 명령](#hermesomh-업데이트)으로 함께 올리고 사용자 지정을 다시 맞춘다 |

## Hermes·OMH 업데이트

Hermes와 OMH를 최신 정식 릴리스로 올리고 이 사용자의 수정 사항을 다시 맞추는 명령은 하나다. 실행 중인 Hermes 작업이 끝나면 Hermes Desktop을 ⌘Q로 종료하고, 터미널 앱에서 Agent-setup 루트로 이동해 실행한다.

```bash
bash hermes/scripts/update.sh
```

- 실행 시점의 최신 정식 버전을 GitHub에서 읽어 Hermes(`hermes update --backup --yes`)와 OMH(`omh update --channel stable --version <최신>`)를 함께 올린다. 버전을 직접 적을 필요가 없다.
- 업데이트 전후로 모델 체인·Hermes 설정·SOUL 관리 구간·사용자 스킬·한국어 트리거 팩·패치 상태를 비교해 표로 보여주고, Hermes 수정 묶음·호환 패치·SOUL 구간·트리거 팩·provider-usage 표시를 다시 맞춘 뒤 점검과 게이트웨이 재시작까지 한다.
- 새 Hermes 태그용 수정 묶음이 `hermes/patches/hermes-agent/`에 없으면 아무것도 바꾸기 전에 멈춘다. 이때 AI에게 "Agent-setup 수정 묶음을 Hermes <태그>에 옮겨줘"라고 요청한 뒤 같은 명령을 다시 실행한다.
- `--dry-run`은 실행할 단계와 확인한 값만, `--check`는 버전과 사용자 지정 상태만 보여준다.
- Hermes Desktop의 업데이트 버튼은 Hermes 본체의 로컬 수정을 다시 적용하지 않으므로 쓰지 않는다.

단계별 동작과 멈추는 조건은 [업데이트](hermes/docs/model-routing.md#업데이트), 항목별 유지 방식은 [사용자 지정 항목과 업데이트](hermes/docs/omh-and-agent-setup.md#사용자-지정-항목과-업데이트)에 있다.

## 저장 데이터 보존

대화 기록은 세 AI 모두 90일, 재생성 가능한 자료와 생성물은 더 짧게 보존한다. 모든 항목은 기간이 지나도 **최신 3개**를 남기고, 그 뒤 새로 생긴 항목이 기간을 넘기면 다음 정리 때 지운다. 정책 원본은 [`shared/retention/policy.json`](shared/retention/policy.json), 실행은 [`scripts/retention.py`](scripts/retention.py)다.

| 대상 | 저장 형식 | 보존 | 정리 방식 |
|---|---|---|---|
| Hermes 대화 (`state.db`) | SQLite | 90일 | Hermes 내장 자동 정리 (`sessions.retention_days`) |
| Hermes 왼쪽 채팅 목록 | SQLite | 프로젝트별 직접 대화 최근 4개, 30일 (보관 포함) | 매일 04:30 [Discord 연동 정리](hermes/docs/discord.md). 실행 기록·빈 대화는 2시간 뒤 삭제 |
| Claude Code 대화 | JSONL | 90일 | Claude Code 내장 (`cleanupPeriodDays`) |
| Codex 대화 (`~/.codex/sessions`, `archived_sessions`) | JSONL | 90일 | 주간 정리 |
| Codex 생성 이미지 | PNG 폴더 | 30일 | 주간 정리 |
| Hermes 백업 (`backups/`) | 폴더 | 30일 | 주간 정리 |
| Hermes 명령 출력·화면 캡처·위임 기록 (`cache/`) | 파일 | 14일 | 주간 정리 (`cache/scratch`는 Hermes가 24시간마다 정리) |
| CodeGraph 색인 (저장소별 `.codegraph/`) | SQLite | 30일 미사용 | 주간 정리. 필요할 때 다시 색인 |
| GAM 임시 기억 (`temporary` + `expires:` 태그) | Markdown 원본 + SQLite 색인 | 만료일까지 | 주간 보관 처리 (영구 삭제 없음) |

```sh
python3 scripts/retention.py              # 미리보기
python3 scripts/retention.py configure    # Hermes·Claude 내장 보존 기간 설정
python3 scripts/retention.py schedule     # macOS launchd 주간 작업 등록 (일요일 04:30)
```

CodeGraph 색인을 찾을 폴더는 컴퓨터마다 `~/Library/Application Support/agent-setup/retention.json`의 `codegraph_roots`에 적는다. 주간 작업은 이 저장소 체크아웃 경로의 스크립트를 실행하므로, 저장소를 옮기면 `schedule`을 다시 실행한다.

## 설치 뒤

새 대화를 열어 프로젝트 작업을 시작한다. 새 제품 저장소를 만들거나 기존 제품에 문서 기준을 적용할 때는 [pycoding-prompt](https://github.com/PyeongsaengCoding/pycoding-prompt)의 해당 절차를 사용한다. 생성·적용 뒤 제품별 규칙과 현재 계약은 그 프로젝트의 AGENTS.md와 docs/에서 관리한다. 설정을 바꾸고 싶으면 AI에게 "Agent-setup 기준으로 ~를 바꿔줘"라고 요청하면 agent-setup-maintenance 스킬 절차로 처리한다.

## 저장소 관리

- 공통 원본: 전역 지침 `shared/rules/`, 공통 스킬 `shared/skills/`. 지침을 고치면 `scripts/build_rules.py`로 각 AI용 파일을 다시 만든다.
- 검사: Python 3.12 이상에서 `scripts/check.py`(세 AI 원본 검사)와 `tests/` 단위시험을 실행한다. 실제 컴퓨터의 설치 완료는 [설치 완료 기준](docs/verification.md)과 각 실행기 설치 안내의 결과로 판정한다.
- 출처와 라이선스: [이관 목록](docs/import-manifest.json), [출처 안내](docs/provenance.md), [스킬 출처](shared/skills/SOURCES.md).
