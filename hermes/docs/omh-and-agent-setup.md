# Hermes에서 Agent-setup과 OMH의 역할 나눔

확인일: 2026-11-05(KST). Agent-setup은 Hermes·OMH·provider-usage를 실행 시점의 최신 정식 릴리스로 설치·업데이트한다. 이 Mac의 설치본과 최신 정식판 비교, 최신 태그용 수정 묶음 유무는 Agent-setup 루트의 `python3 scripts/check_releases.py`로 확인한다.

Hermes에서는 Agent-setup이 설치한 구성과 OMH가 설치한 구성이 함께 동작한다. Agent-setup은 이 사용자의 작업 원칙·스킬·모델 정책·도구 연결을 설치하고, OMH는 작업 분류·워크플로 스킬·분류별 위임 모델을 제공한다. Claude Code·Codex는 OMH를 실행하지 않고 Agent-setup이 넣은 OMH 스킬 사본(`shared/skills/omh/`)과 각 실행기 지침을 쓴다.

## 영역별 구성

| 영역 | Agent-setup에만 있는 것 | OMH에만 있는 것 | 둘 다 있을 때 동작 |
|---|---|---|---|
| 스킬 | `~/.hermes/skills/`: Hermes 공식 스킬, 공통 스킬(GAM·CodeGraph·코드 검토·한국어 다듬기 등), 외부 스킬, 작업 중 만든 스킬 | `~/.local/share/omh/current/skills/`: OMH 워크플로 153개(`omh-*`, `ulw-*`, `dag-ulw`) | 이름이 같으면 Hermes가 `프로젝트 스킬 → ~/.hermes/skills → skills.create_dir → 외부 폴더(OMH)` 순서로 앞쪽을 쓴다(`agent/skill_utils.py:381`). 같은 순위 안의 같은 이름은 거부한다. 2026-10-20 기준 이름 충돌 0개. 역할이 겹치는 스킬(예: `coding-code-review`·`omh-code-review`)은 아래 [작업 흐름 선택](#작업-흐름-선택)에 따라 OMH 흐름 안에서 함께 쓴다 |
| 전역 지침 | 프로필 `SOUL.md`의 공통 작업 원칙·OMH 워크플로 사용·Aside·문서 전달 구간(`scripts/install_global_rules.py`) | 매 턴 붙는 OMH 안내(Route Hint·스킬 후보), 프로젝트 `AGENTS.md`의 `omh:agent-instructions` 구간 | 현재 사용자 지시 → 가장 가까운 프로젝트 `AGENTS.md` → 전역 지침 순서로 따른다. OMH 안내는 구조·내용만 정하고, 답변 언어·말투는 `SOUL.md`를 따른다 |
| 모델 라우팅 | 설치 원본 프리셋(`hermes/routing-presets/`), 메인 대화 기본 모델·fallback 설정 | 분류별 기본 체인(패키지 내장), 실행값 파일 `~/.omh/routing/model-chains.json`, 위임 직전 라우팅 도구 | 프리셋을 `omh model-chains set`으로 넣은 분류는 `override`가 되어 OMH 기본값보다 우선한다. 분류 체인은 하위 에이전트(`delegate_task`)에만 적용되고, 메인 대화·cron·칸반은 Hermes 기본 모델을 쓴다 |
| 기억 | GAM(`global-memory` MCP): 프로젝트 결정·검증된 해결 경험 | OMH 기억(Hermes 기억 제공자 `omh`): Hermes 작업 방식의 교훈 | 프로젝트 지식은 GAM에 저장해 Claude·Codex와 함께 쓰고, OMH 기억에는 Hermes 실행 교훈만 둔다. Hermes 기본 기억(`MEMORY.md`·`USER.md`)은 모든 세션에 필요한 사실만 둔다 |
| 코드 탐색 | CodeGraph MCP와 `codegraph-context` 스킬(코드 작업 시작 시 상시 사용) | `omh-codegraph-refresh` 워크플로 | 공통 지침이 CodeGraph MCP 사용을 정하고, OMH 워크플로는 색인 갱신 계획이 필요할 때 쓴다 |
| 브라우저 | Aside 설치와 `repl` 직접 조작 규칙 | `omh-browser` 정책 안내(로그인·클릭·폼 작업 범위) | 조작 도구는 Aside 규칙을 따르고, 권한·확인 범위는 OMH 안내를 함께 적용한다 |
| 플러그인 | `provider-usage`, `web-codex-search`. Discord를 쓰는 사용자만 `desktop-discord-reports`, `discord-project-sidebar`를 선택 설치 | `omh` 플러그인(`omh_*` 도구·턴 훅) | 이름이 달라 각자 등록된다. 같은 이벤트를 쓰는 훅은 모두 실행된다 |
| 프로젝트 식별 | 없음 | OMH 기억이 프로젝트를 구분하는 식별자(Git 원격 주소로 자동 결정) | 프로젝트마다 할 초기화는 없다. 식별이 `unresolved`인 프로젝트만 그 폴더에서 `omh memory project-identity init`을 실행한다 |
| 업데이트 | `hermes/scripts/update.sh` 한 줄 명령, 설치본 대 최신 정식판·최신 태그용 패치 점검(`scripts/check_releases.py`) | `omh update`가 자기 명령 패키지·워크플로·플러그인을 갱신 | `update.sh`가 Hermes·OMH·provider-usage를 실행 시점의 최신 정식 릴리스로 함께 올리고, 외부 스킬을 최신 정식판으로 갱신한 뒤 아래 표의 사용자 지정을 다시 맞춘다. 최신 태그용 수정 묶음이 없으면 바꾸기 전에 멈추고 패치 이전을 요청하라고 안내한다. 절차는 [업데이트](model-routing.md#업데이트)에 있다 |
| Claude Code·Codex | OMH 최신 정식판 스킬 사본(`shared/skills/omh/`, 버전은 `SOURCE.json`), 실행기별 라우팅·지침, 한 줄 업데이트 `bash scripts/update_claude_codex.sh` | 실행 런타임 없음 | Claude·Codex 전역 지침의 `OMH workflow skills` 절이 작업 형태로 OMH 흐름을 먼저 고르게 한다(여러 부분·선후관계·확정 계획 구현→`ulw-work`, 반복 목표→`ulw-loop`, 미정 계획→`ulw-plan`·`omh-plan`, 검토→`omh-code-review`, 완료 판정→`omh-verification-gate`). `dag-ulw`는 Hermes `omh_dag`가 필요해 Claude·Codex에서는 `ulw-work` 작업 줄로 처리한다. 같은 절이 `omh_*` 도구를 각 실행기 도구로 대응시킨다 |

## 사용자 지정 항목과 업데이트

업데이트는 Agent-setup 루트에서 `bash hermes/scripts/update.sh` 한 줄로 한다. Hermes Desktop의 업데이트 버튼은 `hermes update --keep-stash`를 실행해 Hermes 본체의 로컬 수정을 stash에 보관한 채 다시 적용하지 않는다. 이 Mac에는 그렇게 보관된 stash가 3개 남아 있고, 2026-10-10 Desktop 업데이트 이후 호환 패치 두 개가 빠진 상태다. 그래서 업데이트 버튼은 쓰지 않는다.

아래 표의 "업데이트 때 동작"은 `hermes update`와 `omh update`·`omh setup`의 실제 코드와 이 Mac의 업데이트 기록으로 확인했다(2026-11-05). 모델 체인·설정·SOUL·스킬·트리거 팩·provider-usage는 업데이트 뒤에도 그대로 남았고, 초기화된 것은 Desktop 업데이트로 빠진 Hermes 본체 수정이었다.

| 커스텀 항목 | 저장 위치 | 업데이트 때 동작(Hermes/OMH) | 다시 적용하는 곳 | OMH와 함께 동작하는 방식 |
|---|---|---|---|---|
| 라우팅 프리셋·모델 체인 | 원본 `hermes/routing-presets/*.json`, 적용값 `~/.omh/routing/model-chains.json`(`override`) | Hermes: 건드리지 않는다. OMH: 파일이 없을 때만 새로 만들고 `override` 값은 유지한다. 터미널의 대화형 `omh setup`에서 체인 질문에 답하면 사용자가 값을 바꿀 수 있다 | 다시 적용할 필요 없음. `update.sh`가 업데이트 전후 값을 비교한다. 바꿀 때는 [`omh model-chains set`](model-routing.md) | OMH가 위임 직전 `omh_delegate_route`로 분류를 고르면 그 분류의 `override` 체인이 하위 에이전트 모델·추론을 정한다 |
| 위임·fallback 설정 | `~/.hermes/config.yaml`의 `delegation.*`, `fallback_providers`, `model.*` | Hermes: 설정 이전은 빠진 키만 추가한다. `--backup`으로 업데이트하면 업데이트 전 스냅샷에서 `model.*`·`moa`를 되살린다. OMH: 이 키를 쓰지 않는다. `auxiliary.compression.fallback_chain`이 없을 때만 `fallback_providers`를 읽어 값을 만든다 | 다시 적용할 필요 없음. `update.sh`가 `hermes update --backup --yes`로 올리고 전후 값을 비교한다 | Hermes 전역 fallback과 자식 공통 fallback은 Hermes 설정이 정하고, 분류별 모델 순서는 OMH 체인이 정한다 |
| OMH 연결 설정 | `~/.hermes/config.yaml`의 `skills.external_dirs`, `plugins.enabled`, `plugins.entries.omh`, `memory.provider` | OMH: 업데이트·setup 때마다 OMH 경로(`~/.local/share/omh/current/skills`)와 `omh` 플러그인 항목을 다시 맞춘다. `memory.provider`는 비어 있을 때만 `omh`로 정한다. 목록의 다른 항목은 유지한다 | OMH가 직접 맞춘다 | OMH 워크플로 153개와 `omh_*` 도구를 Hermes에 연결하는 값이다 |
| SOUL 관리 구간 4개 | `~/.hermes/SOUL.md`의 `agent-setup:common`, `agent-setup:omh-workflow`, `hermes-setup:aside-browser`, `hermes-setup:document-delivery` | Hermes: 사용자가 고친 `SOUL.md`는 덮어쓰지 않는다. OMH: `SOUL.md`를 쓰지 않는다 | `update.sh`가 `install_global_rules.py --apply`를 실행한다. 설치기는 Git 이력과 적용 기록(`$HERMES_HOME/.agent-setup/managed-blocks.json`)으로 이전 배포본을 알아보고 구간 안만 새 템플릿으로 바꾼다. 구간을 직접 고쳤으면 `.agent-setup/diffs/`에 차이를 남기고 멈춘다 | 공통 원칙은 작업 방식, OMH 워크플로 규칙은 [작업 흐름 선택](#작업-흐름-선택), Aside 규칙은 `omh-browser` 범위 안내와 함께 브라우저 조작, 문서 전달 규칙은 결과물 전달을 맡는다. 답변 언어·말투도 `SOUL.md`가 정한다 |
| 사용자 스킬 | `~/.hermes/skills/` | Hermes: 기본 스킬 동기화는 같은 이름의 사용자 스킬과 사용자가 고친 기본 스킬을 건너뛴다. OMH: 쓰지 않는다 | 다시 적용할 필요 없음. `update.sh`가 스킬 폴더 해시를 비교한다 | 고른 OMH 워크플로의 각 노드·작업 라인이 프로젝트 규칙·계정·도구·점검에 맞는 사용자 스킬을 불러 쓴다. 이름이 같으면 사용자 스킬이 우선한다 |
| OMH 워크플로 스킬·플러그인 | `~/.local/share/omh/generations/<id>/`(`current`가 가리킴), `~/.hermes/plugins/omh/` | OMH: 업데이트마다 새 generation을 만들고 이전 것을 정리한다. 플러그인에 로컬 변경이 있으면 갱신을 거부하고, `omh setup --force`는 변경을 덮어쓴다 | 수정하지 않는다. 바꿀 내용은 사용자 스킬·트리거 팩·SOUL 템플릿에 둔다 | OMH 본체다 |
| Hermes 본체 수정 묶음 | `~/.hermes/hermes-agent` 작업 트리. 원본 `hermes/patches/hermes-agent/<태그>.patch`(현재 v0.22.2·v0.22.5·v0.22.7·v0.23.1) | Hermes: 업데이트 전에 로컬 수정을 stash에 넣고, `--yes`면 자동으로 다시 적용한다. 다시 적용이 충돌하면 깨끗한 새 버전으로 두고 stash를 보관한다. Desktop 업데이트(`--keep-stash`)는 다시 적용하지 않는다. OMH: 건드리지 않는다 | `update.sh`가 `apply_local_patches.py --apply`를 실행한다. 새 태그용 패치가 없으면 아무것도 바꾸기 전에 멈추고, AI에게 패치 이전을 요청하라고 안내한다 | 계정 선택·사용량 표시·모델별 계정 쿨다운·턴 복구는 OMH 위임을 포함한 모든 Hermes 모델 호출에 적용된다 |
| 호환 패치 2개 | `~/.hermes/hermes-agent`의 `agent/chat_completion_helpers.py`, `tools/delegate_tool_config.py` | 본체 수정 묶음과 같은 stash 동작. 2026-10-10 Desktop 업데이트로 빠졌다 | `update.sh`가 `configure_delegation_reasoning.py`·`configure_gpt_fallback.py --apply`를 실행한다 | OMH 분류가 정한 추론 강도를 위임 자식에 유지하고, GPT로 시작한 자식의 fallback 순서를 맞춘다 |
| provider-usage | `~/.hermes/plugins/provider-usage`, `~/.hermes/desktop-plugins/provider-usage/plugin.js` | Hermes: 사용자 플러그인은 업데이트하지 않는다. OMH: 건드리지 않는다 | `update.sh`가 최신 정식 태그를 조회해 플러그인을 그 태그로 올린다. 로컬 수정은 이름 붙인 stash에 백업하고, `apply_local_patches.py`가 새 태그용 `patches/provider-usage/<태그>.patch`를 적용한 뒤 `configure_provider_usage.py --apply`와 Desktop 미러 복사를 한다. 새 태그용 패치가 없으면 바꾸기 전에 멈춘다 | OMH 체인이 쓰는 GPT·Claude 계정의 사용량·잔여 한도를 보여준다 |
| 한국어 트리거 팩 | 원본 `hermes/omh/trigger-packs/ko.json`, 설치본 `~/.omh/routing/trigger-packs/ko.json` | Hermes: 건드리지 않는다. OMH: 사용자 팩을 읽기만 한다 | `update.sh`가 `install_omh_trigger_pack.py --apply`로 빠진 구문만 더한다. 사용자가 넣은 구문은 유지한다. 이어서 `scripts/check_parallel_gaps.py routing`으로 실제 요청 회귀 문장을 다시 점검하고, 누락은 경고로 보여준 뒤 업데이트를 계속한다 | 한국어 문장으로 `dag-ulw`·`ultrawork` 등 워크플로의 추천 점수를 올리고, 다른 힌트가 없을 때 `user_trigger_pack` Route Hint를 만든다 |
| GAM과 OMH 기억 | GAM: `global-memory` MCP와 GAM Vault. OMH 기억: `~/.omh/memory/`(`memory.provider: omh`) | Hermes: 건드리지 않는다. OMH: 업데이트가 기억 저장소를 쓰지 않는다 | 다시 적용할 필요 없음 | 프로젝트 결정·해결 경험은 GAM에 저장해 세 AI가 함께 쓰고, Hermes 실행 교훈은 `omh_memory`로 OMH 기억에 둔다 |

## 작업 흐름 선택

Hermes는 OMH 설치기가 플러그인과 워크플로 153개를 직접 설치하므로, Claude·Codex용 `shared/rules/omh.md`(OMH 도구를 각 실행기 도구로 대응시키는 절)는 받지 않는다. 대신 Agent-setup이 [OMH 워크플로 규칙](../templates/omh-workflow.md)을 `SOUL.md`의 `agent-setup:omh-workflow` 구간으로 넣는다. 한국어 설명은 [한국어 안내](../../docs/ko/hermes/templates/omh-workflow.md)에 있다.

작업 요청을 받으면 요청 언어와 관계없이 Hermes가 먼저 작업 형태에 맞는 전체 흐름을 직접 고른다.

| 작업 형태 | 흐름 |
|---|---|
| 순서가 있거나 병렬로 나눌 수 있는 여러 부분의 작업 | `dag-ulw` |
| 승인된 계획을 여러 작업 라인으로 구현 | `ulw-work` |
| 조사·구현·검증을 반복하는 장기 목표 | `ulw-loop` |
| 정하지 않았거나 위험이 큰 계획 | `ulw-plan` 또는 `omh-plan` |
| 리뷰 | `omh-code-review` |
| 범위가 작고 명확한 수정 하나 | 바로 처리 |

- 고른 흐름은 `skill_view`로 불러 따르고, 완료를 말하기 전에 `omh-verification-gate`를 불러 검증한다.
- 개인·프로젝트 스킬은 고른 흐름 안에서 프로젝트 규칙·계정·도구·점검에 쓴다. 각 노드와 작업 라인도 관련 스킬을 불러온다.
- OMH Route Hint나 스킬 후보가 나오면 첫 행동 전에 그 스킬을 불러와 따르거나, 다른 흐름이 맞는 이유를 한 줄로 밝힌다.
- `delegate_task` 직전에는 매번 `omh_delegate_route`를 호출한다. 세 단계 이상 작업은 `omh_todo`에 기록하고, 여러 에이전트를 쓰면 `omh_agent_board`로 관리한 뒤 `omh_run_summary`로 시간·토큰을 보고한다.
- 준비한 계획·인계와 실제 실행·검증 결과를 나눠 보고하고, 사용자에게는 한국어로 보고한다.

### 한국어 여러 부분 요청이 `dag-ulw`에 닿는 경로

"회원가입 로그인부터 일반채팅, 지식그래프까지 설계에 맞게 개발해줘" 같은 요청은 두 장치로 `dag-ulw`에 닿는다. 주 장치는 3번 전역 규칙이고, 1·2번 트리거 팩은 팩에 든 표현과 비슷한 문장에서 Route Hint를 더하는 보조 장치다.

1. 사용자 트리거 팩: OMH 플러그인의 Route Hint(`awareness_route_hint`)는 OMH 기본 규칙을 먼저 적용하고, 기본 규칙이 아무 흐름도 고르지 않은 문장에만 `~/.omh/routing/trigger-packs/ko.json`을 쓴다. 이때 라우터가 고른 흐름이 팩에 적힌 흐름과 같아야 힌트가 붙는다. 넓은 단어(`개발`·`진행` 등)는 전체 구문으로만 점수를 받아 작은 요청에는 힌트가 붙지 않는다.
2. Route Hint: 위 조건을 통과하면 OMH가 그 턴에 `dag-ulw`·`ulw-work`·`ulw-loop` Route Hint를 붙이고, Hermes는 첫 행동 전에 그 흐름을 불러온다.
3. 전역 규칙: Route Hint가 없거나 다른 흐름을 가리켜도 `SOUL.md`의 OMH 워크플로 구간이 여러 부분 작업에서 `dag-ulw`와 `dag-ulw-notes`를 직접 불러오게 한다. 공통 작업 원칙의 "여러 부분으로 된 작업" 절은 첫 위임 전에 부분 목록과 기다리는 대상을 적고, 준비된 부분을 한 번의 위임 호출로 시작하게 한다. 이 절은 Claude Code·Codex 전역 지침에도 같은 내용으로 들어간다.

회귀 문장은 `hermes/omh/trigger-packs/ko-corpus.json`에 있다. 실제 대화에서 고른 문장과 같은 말투로 쓴 연습 문장을 합쳐 여러 부분 요청 51개, 작은 요청 54개다. `python3 hermes/omh/trigger-packs/evaluate.py`가 임시 OMH·Hermes 홈에서 각 문장의 실제 Route Hint를 판정한다(`ulw-work`·`ulw-loop`도 적중). 2026-11-06 측정값은 다음과 같다.

| 문장 묶음 | 여러 부분 요청 적중 | 작은 요청 오탐 |
|---|---|---|
| 회귀 문장(팩 조정에 사용) | 46/51 | 0/54 |
| 조정에 쓰지 않은 새 문장 두 묶음 | 0/10, 1/10 | 0/10, 0/10 |

새 문장 적중률이 낮아서 평소 말투의 여러 부분 요청은 대부분 3번 전역 규칙이 받친다. 놓친 경우는 아래 3일 점검이 찾는다.

### 병렬 실행 누락 점검

`scripts/check_parallel_gaps.py`가 라우팅과 실제 실행을 각각 점검한다. Python 표준 라이브러리로 동작하고 LLM 호출 비용은 0이다.

| 점검 | 시점 | 확인 내용 |
|---|---|---|
| `routing` | `update.sh`의 트리거 팩 설치 직후, 3일 주기 작업 | 회귀 문장 중 여러 부분 요청이 큰 흐름을 받지 못한 경우, 작은 요청이 큰 흐름을 받은 경우 |
| `history --days 3` | 3일 주기 작업 | Hermes `state.db`(읽기 전용)의 위임 호출 수·작업 수, 한 작업만 맡긴 호출, 그 뒤 같은 턴에 이어진 위임, `dag-ulw`를 불러오지 않은 위임 세션. Claude Code·Codex 기록도 확인 가능한 범위에서 함께 센다 |

3일 주기 작업은 `hermes/scripts/install_parallel_gap_check.py --apply`가 Hermes no-agent cron(`every 72h`)으로 등록한다. 알림 대상은 `--deliver`로 정하고 기본값은 `local`(cron 실행 기록)이다. 이 Mac에서는 대화 정리 작업과 같은 Discord 채널을 지정해 발견한 내용이 있을 때만 알리고, 보고서는 `$HERMES_HOME/reports/parallel-gaps/`에 남긴다. 한 작업만 맡긴 호출은 검토 대상이고, 분할 사유는 해당 대화 원문에서 판단한다.

### 바꾼 이유

이전 규칙은 "사용자 스킬이 다루는 단계는 그 스킬, 나머지 단계는 OMH"였다. 사용자 스킬이 있는 작업에서는 OMH 흐름이 거의 쓰이지 않았다. 2026-11-05에 `~/.hermes/state.db`에 남은 기록을 보면 `omh_dag` 호출과 `ulw-work`·`ulw-loop`·`omh-verification-gate` 로드가 모두 0건이었고, OMH Route Hint를 따르지 않은 대화도 2건 이상 있었다. 한국어 문장은 OMH 기본 한국어 트리거 데이터에 `dag-ulw`·`ultrawork` 구문이 없어 이 흐름을 추천받지 못했다.

2026-11-05에 세 가지를 바꿨다.

- 규칙: 작업 형태로 OMH 흐름을 먼저 고르고, 사용자 스킬은 그 흐름 안에서 쓴다. `install_global_rules.py`가 이전 배포본을 알아보고 구간을 바꿀 수 있게 고쳐 이 Mac의 `SOUL.md`에 적용했다. 같은 명령을 다시 실행하면 `unchanged`가 나온다.
- 한국어 트리거 팩: 9개 워크플로에 한국어 구문 42개를 넣었다. OMH 라우터로 확인하니 "백엔드와 프론트엔드를 병렬로 구현해줘"는 `dag-ulw`, "승인된 계획대로 구현해줘"는 `ultrawork`로 바뀌었다. 일상 대화 3개는 전후 모두 흐름이 붙지 않았다.
- 업데이트: `update.sh`가 업데이트 뒤 규칙과 트리거 팩을 다시 맞춘다.

새 세션에서 Hermes가 실제로 흐름을 고르는지는 아직 관찰하지 않았다.

2026-11-06에 다시 세 가지를 바꿨다. 최근 30일 기록에서 Hermes 위임 호출 75건 중 58건이 작업 하나만 맡겼고, 위임한 21개 세션 중 4개만 `dag-ulw`를 불러왔다. 실제 한국어 요청은 기존 트리거 팩의 긴 구문과 표현이 달라 `dag-ulw` 추천을 받지 못했다.

- 한국어 트리거 팩: 실제 대화 문장으로 회귀 문장을 만들고 일상 표현을 더했다. 실제 Route Hint 기준 회귀 문장 적중은 31/51에서 46/51로 올랐고, 조정에 쓰지 않은 새 문장은 0/10·1/10이다. 사용자 결정(2026-11-06)으로 팩은 보조로 두고 전역 규칙과 3일 점검을 주 장치로 쓴다.
- 규칙: 공통 작업 원칙에 "여러 부분으로 된 작업" 절을, OMH 워크플로 구간에 `dag-ulw`·`dag-ulw-notes` 직접 로드를 더했다. `dag-ulw-notes` 스킬을 저장소에 두고 설치 목록에 올렸다.
- 점검: 업데이트 때 라우팅 점검, 3일마다 대화 기록 점검을 실행한다([병렬 실행 누락 점검](#병렬-실행-누락-점검)).

## 문서 언어

AI가 읽는 글(SOUL 구간 템플릿, 규칙, 스킬 설명, 코드 주석, 데이터)은 AI가 더 잘 따르는 영문으로 쓴다. 사용자가 읽을 한국어 안내는 `docs/ko/<같은 상대경로>`에 함께 둔다. 예를 들어 `hermes/templates/omh-workflow.md`의 한국어 안내는 `docs/ko/hermes/templates/omh-workflow.md`다. 영문 원본을 고치면 한국어 안내도 같은 변경에서 맞춘다. 이 문서·README·설치 목록처럼 사용자가 읽는 문서와 사용자에게 보내는 보고는 한국어로 쓴다.

## 알려진 제한

- OMH Route Hint는 사용자 메시지만 읽는다. 플러그인의 "Skills that may fit" 후보는 OMH가 만든 한글 색인을 쓰며 사용자 트리거 팩을 합치지 않으므로, 한국어 문장에는 `dag-ulw`·`ultrawork`가 후보 목록에 나오지 않는다. Hermes는 `SOUL.md` 규칙에 따라 흐름을 직접 고른다.
- "여러 파일 걸친 기능 추가하고 문서랑 테스트까지 끝까지 해줘"처럼 파일을 언급한 작업 요청은 OMH 라우터의 파일 조회 처리에 먼저 걸려 흐름이 붙지 않는다. OMH 쪽 수정이 필요하다.
- OMH 메뉴 막대 앱(`~/.omh/menubar`)은 특정 generation의 `omh` 경로로 실행된다. OMH 업데이트가 두 번 더 지나 그 generation이 정리되면 실행되지 않으므로, 업데이트 뒤 메뉴 막대 앱을 다시 시작한다.

## OMH 설치본

- PATH의 `omh`는 `~/.local/bin/omh → ~/.local/share/omh/current/venv/bin/omh`로 현재 generation을 실행한다. 2026-11-05 이 Mac의 설치본은 main 브랜치로 만든 preview 4.0.5였다. 옵션 없는 `omh update`는 설치 기록과 관계없이 preview를 받기 때문이다. `update.sh`는 `--channel stable --version <최신>`으로 정식 릴리스로 옮긴다.
- `~/.local/share/omh/venv`는 curl 설치기의 기본 위치이고, PATH의 `omh`는 이 venv를 실행하지 않는다. `update.sh`는 업데이트와 점검이 성공하고 이 venv를 쓰는 명령·프로세스가 없을 때 이 venv를 휴지통으로 옮긴다. curl 설치기를 다시 실행하면 이 venv가 다시 생기므로 업데이트는 `update.sh`로 한다.

## 프로젝트 식별 확인

```bash
cd <프로젝트>
omh memory project-identity show
```

`"state":"resolved"`면 그대로 쓴다. `unresolved`면 `diagnostics` 값을 확인한다. `remote_absent`는 Git 원격을 연결하거나 `init`으로 식별자를 만든다. `git_metadata_unreadable`은 저장소 상태를 먼저 고친다. 2026-10-20 점검에서 `~/Downloads/Coding` 아래 Git 프로젝트 38개 중 36개가 자동으로 식별됐다.
