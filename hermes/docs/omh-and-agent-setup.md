# Hermes에서 Agent-setup과 OMH의 역할 나눔

확인일: 2026-11-05(KST). 이 Mac의 설치본은 Hermes v0.22.5·OMH 4.0.5(preview 빌드)이고, 같은 날 최신 정식 릴리스는 Hermes v0.22.7·OMH 4.0.6이다.

Hermes에서는 Agent-setup이 설치한 구성과 OMH가 설치한 구성이 함께 동작한다. Agent-setup은 이 사용자의 작업 원칙·스킬·모델 정책·도구 연결을 설치하고, OMH는 작업 분류·워크플로 스킬·분류별 위임 모델을 제공한다. Claude Code·Codex는 OMH를 실행하지 않고 Agent-setup이 넣은 OMH 스킬 사본(`shared/skills/omh/`)과 각 실행기 지침을 쓴다.

## 영역별 구성

| 영역 | Agent-setup에만 있는 것 | OMH에만 있는 것 | 둘 다 있을 때 동작 |
|---|---|---|---|
| 스킬 | `~/.hermes/skills/`: Hermes 공식 스킬, 공통 스킬(GAM·CodeGraph·코드 검토·한국어 다듬기 등), 외부 스킬, 작업 중 만든 스킬 | `~/.local/share/omh/current/skills/`: OMH 워크플로 144개(`omh-*`, `ulw-*`, `dag-ulw`) | 이름이 같으면 Hermes가 `프로젝트 스킬 → ~/.hermes/skills → skills.create_dir → 외부 폴더(OMH)` 순서로 앞쪽을 쓴다(`agent/skill_utils.py:381`). 같은 순위 안의 같은 이름은 거부한다. 2026-10-20 기준 이름 충돌 0개. 역할이 겹치는 스킬(예: `coding-code-review`·`omh-code-review`)은 아래 [작업 흐름 선택](#작업-흐름-선택)에 따라 OMH 흐름 안에서 함께 쓴다 |
| 전역 지침 | 프로필 `SOUL.md`의 공통 작업 원칙·OMH 워크플로 사용·Aside·문서 전달 구간(`scripts/install_global_rules.py`) | 매 턴 붙는 OMH 안내(Route Hint·스킬 후보), 프로젝트 `AGENTS.md`의 `omh:agent-instructions` 구간 | 현재 사용자 지시 → 가장 가까운 프로젝트 `AGENTS.md` → 전역 지침 순서로 따른다. OMH 안내는 구조·내용만 정하고, 답변 언어·말투는 `SOUL.md`를 따른다 |
| 모델 라우팅 | 설치 원본 프리셋(`hermes/routing-presets/`), 메인 대화 기본 모델·fallback 설정 | 분류별 기본 체인(패키지 내장), 실행값 파일 `~/.omh/routing/model-chains.json`, 위임 직전 라우팅 도구 | 프리셋을 `omh model-chains set`으로 넣은 분류는 `override`가 되어 OMH 기본값보다 우선한다. 분류 체인은 하위 에이전트(`delegate_task`)에만 적용되고, 메인 대화·cron·칸반은 Hermes 기본 모델을 쓴다 |
| 기억 | GAM(`global-memory` MCP): 프로젝트 결정·검증된 해결 경험 | OMH 기억(Hermes 기억 제공자 `omh`): Hermes 작업 방식의 교훈 | 프로젝트 지식은 GAM에 저장해 Claude·Codex와 함께 쓰고, OMH 기억에는 Hermes 실행 교훈만 둔다. Hermes 기본 기억(`MEMORY.md`·`USER.md`)은 모든 세션에 필요한 사실만 둔다 |
| 코드 탐색 | CodeGraph MCP와 `codegraph-context` 스킬(코드 작업 시작 시 상시 사용) | `omh-codegraph-refresh` 워크플로 | 공통 지침이 CodeGraph MCP 사용을 정하고, OMH 워크플로는 색인 갱신 계획이 필요할 때 쓴다 |
| 브라우저 | Aside 설치와 `repl` 직접 조작 규칙 | `omh-browser` 정책 안내(로그인·클릭·폼 작업 범위) | 조작 도구는 Aside 규칙을 따르고, 권한·확인 범위는 OMH 안내를 함께 적용한다 |
| 플러그인 | `provider-usage`, `web-codex-search`. Discord를 쓰는 사용자만 `desktop-discord-reports`, `discord-project-sidebar`를 선택 설치 | `omh` 플러그인(`omh_*` 도구·턴 훅) | 이름이 달라 각자 등록된다. 같은 이벤트를 쓰는 훅은 모두 실행된다 |
| 프로젝트 식별 | 없음 | OMH 기억이 프로젝트를 구분하는 식별자(Git 원격 주소로 자동 결정) | 프로젝트마다 할 초기화는 없다. 식별이 `unresolved`인 프로젝트만 그 폴더에서 `omh memory project-identity init`을 실행한다. OMH 4.0.0에는 `omh init` 명령이 없다 |
| 업데이트 | `hermes/scripts/update.sh` 한 줄 명령, 외부 구성요소 고정값 확인(`scripts/check_releases.py`) | `omh update`가 자기 명령 패키지·워크플로·플러그인을 갱신 | `update.sh`가 Hermes·OMH를 최신 정식 릴리스로 함께 올리고 아래 표의 사용자 지정을 다시 맞춘다. 절차는 [업데이트](model-routing.md#업데이트)에 있다 |
| Claude Code·Codex | OMH 스킬 사본, 실행기별 라우팅·지침 | 실행 런타임 없음 | Claude·Codex 전역 지침의 `OMH 워크플로 스킬` 절이 `omh_*` 도구를 각 실행기 도구로 대응시킨다 |

## 사용자 지정 항목과 업데이트

업데이트는 Agent-setup 루트에서 `bash hermes/scripts/update.sh` 한 줄로 한다. Hermes Desktop의 업데이트 버튼은 `hermes update --keep-stash`를 실행해 Hermes 본체의 로컬 수정을 stash에 보관한 채 다시 적용하지 않는다. 이 Mac에는 그렇게 보관된 stash가 3개 남아 있고, 2026-10-10 Desktop 업데이트 이후 호환 패치 두 개가 빠진 상태다. 그래서 업데이트 버튼은 쓰지 않는다.

아래 표의 "업데이트 때 동작"은 `hermes update`와 `omh update`·`omh setup`의 실제 코드와 이 Mac의 업데이트 기록으로 확인했다(2026-11-05). 모델 체인·설정·SOUL·스킬·트리거 팩·provider-usage는 업데이트 뒤에도 그대로 남았고, 초기화된 것은 Desktop 업데이트로 빠진 Hermes 본체 수정이었다.

| 커스텀 항목 | 저장 위치 | 업데이트 때 동작(Hermes/OMH) | 다시 적용하는 곳 | OMH와 함께 동작하는 방식 |
|---|---|---|---|---|
| 라우팅 프리셋·모델 체인 | 원본 `hermes/routing-presets/*.json`, 적용값 `~/.omh/routing/model-chains.json`(`override`) | Hermes: 건드리지 않는다. OMH: 파일이 없을 때만 새로 만들고 `override` 값은 유지한다. 터미널의 대화형 `omh setup`에서 체인 질문에 답하면 사용자가 값을 바꿀 수 있다 | 다시 적용할 필요 없음. `update.sh`가 업데이트 전후 값을 비교한다. 바꿀 때는 [`omh model-chains set`](model-routing.md) | OMH가 위임 직전 `omh_delegate_route`로 분류를 고르면 그 분류의 `override` 체인이 하위 에이전트 모델·추론을 정한다 |
| 위임·fallback 설정 | `~/.hermes/config.yaml`의 `delegation.*`, `fallback_providers`, `model.*` | Hermes: 설정 이전은 빠진 키만 추가한다. `--backup`으로 업데이트하면 업데이트 전 스냅샷에서 `model.*`·`moa`를 되살린다. OMH: 이 키를 쓰지 않는다. `auxiliary.compression.fallback_chain`이 없을 때만 `fallback_providers`를 읽어 값을 만든다 | 다시 적용할 필요 없음. `update.sh`가 `hermes update --backup --yes`로 올리고 전후 값을 비교한다 | Hermes 전역 fallback과 자식 공통 fallback은 Hermes 설정이 정하고, 분류별 모델 순서는 OMH 체인이 정한다 |
| OMH 연결 설정 | `~/.hermes/config.yaml`의 `skills.external_dirs`, `plugins.enabled`, `plugins.entries.omh`, `memory.provider` | OMH: 업데이트·setup 때마다 OMH 경로(`~/.local/share/omh/current/skills`)와 `omh` 플러그인 항목을 다시 맞춘다. `memory.provider`는 비어 있을 때만 `omh`로 정한다. 목록의 다른 항목은 유지한다 | OMH가 직접 맞춘다 | OMH 워크플로 144개와 `omh_*` 도구를 Hermes에 연결하는 값이다 |
| SOUL 관리 구간 4개 | `~/.hermes/SOUL.md`의 `agent-setup:common`, `agent-setup:omh-workflow`, `hermes-setup:aside-browser`, `hermes-setup:document-delivery` | Hermes: 사용자가 고친 `SOUL.md`는 덮어쓰지 않는다. OMH: `SOUL.md`를 쓰지 않는다 | `update.sh`가 `install_global_rules.py --apply`를 실행한다. 설치기는 Git 이력과 적용 기록(`$HERMES_HOME/.agent-setup/managed-blocks.json`)으로 이전 배포본을 알아보고 구간 안만 새 템플릿으로 바꾼다. 구간을 직접 고쳤으면 `.agent-setup/diffs/`에 차이를 남기고 멈춘다 | 공통 원칙은 작업 방식, OMH 워크플로 규칙은 [작업 흐름 선택](#작업-흐름-선택), Aside 규칙은 `omh-browser` 범위 안내와 함께 브라우저 조작, 문서 전달 규칙은 결과물 전달을 맡는다. 답변 언어·말투도 `SOUL.md`가 정한다 |
| 사용자 스킬 | `~/.hermes/skills/` | Hermes: 기본 스킬 동기화는 같은 이름의 사용자 스킬과 사용자가 고친 기본 스킬을 건너뛴다. OMH: 쓰지 않는다 | 다시 적용할 필요 없음. `update.sh`가 스킬 폴더 해시를 비교한다 | 고른 OMH 워크플로의 각 노드·작업 라인이 프로젝트 규칙·계정·도구·점검에 맞는 사용자 스킬을 불러 쓴다. 이름이 같으면 사용자 스킬이 우선한다 |
| OMH 워크플로 스킬·플러그인 | `~/.local/share/omh/generations/<id>/`(`current`가 가리킴), `~/.hermes/plugins/omh/` | OMH: 업데이트마다 새 generation을 만들고 이전 것을 정리한다. 플러그인에 로컬 변경이 있으면 갱신을 거부하고, `omh setup --force`는 변경을 덮어쓴다 | 수정하지 않는다. 바꿀 내용은 사용자 스킬·트리거 팩·SOUL 템플릿에 둔다 | OMH 본체다 |
| Hermes 본체 수정 묶음 | `~/.hermes/hermes-agent` 작업 트리. 원본 `hermes/patches/hermes-agent/<태그>.patch`(현재 v0.22.2·v0.22.5·v0.22.7) | Hermes: 업데이트 전에 로컬 수정을 stash에 넣고, `--yes`면 자동으로 다시 적용한다. 다시 적용이 충돌하면 깨끗한 새 버전으로 두고 stash를 보관한다. Desktop 업데이트(`--keep-stash`)는 다시 적용하지 않는다. OMH: 건드리지 않는다 | `update.sh`가 `apply_local_patches.py --apply`를 실행한다. 새 태그용 패치가 없으면 아무것도 바꾸기 전에 멈추고, AI에게 패치 이전을 요청하라고 안내한다 | 계정 선택·사용량 표시·모델별 계정 쿨다운·턴 복구는 OMH 위임을 포함한 모든 Hermes 모델 호출에 적용된다 |
| 호환 패치 2개 | `~/.hermes/hermes-agent`의 `agent/chat_completion_helpers.py`, `tools/delegate_tool_config.py` | 본체 수정 묶음과 같은 stash 동작. 2026-10-10 Desktop 업데이트로 빠졌다 | `update.sh`가 `configure_delegation_reasoning.py`·`configure_gpt_fallback.py --apply`를 실행한다 | OMH 분류가 정한 추론 강도를 위임 자식에 유지하고, GPT로 시작한 자식의 fallback 순서를 맞춘다 |
| provider-usage | `~/.hermes/plugins/provider-usage`(v0.2.1), `~/.hermes/desktop-plugins/provider-usage/plugin.js` | Hermes: 사용자 플러그인은 업데이트하지 않는다. OMH: 건드리지 않는다 | `apply_local_patches.py`(플러그인 태그 기준 `patches/provider-usage/<태그>.patch`), `configure_provider_usage.py --apply` | OMH 체인이 쓰는 GPT·Claude 계정의 사용량·잔여 한도를 보여준다 |
| 한국어 트리거 팩 | 원본 `hermes/omh/trigger-packs/ko.json`, 설치본 `~/.omh/routing/trigger-packs/ko.json` | Hermes: 건드리지 않는다. OMH: 사용자 팩을 읽기만 한다 | `update.sh`가 `install_omh_trigger_pack.py --apply`로 빠진 구문만 더한다. 사용자가 넣은 구문은 유지한다 | 한국어 문장으로 `dag-ulw`·`ultrawork` 등 9개 워크플로의 추천 점수를 올리고, 다른 힌트가 없을 때 `user_trigger_pack` Route Hint를 만든다 |
| GAM과 OMH 기억 | GAM: `global-memory` MCP와 GAM Vault. OMH 기억: `~/.omh/memory/`(`memory.provider: omh`) | Hermes: 건드리지 않는다. OMH: 업데이트가 기억 저장소를 쓰지 않는다 | 다시 적용할 필요 없음 | 프로젝트 결정·해결 경험은 GAM에 저장해 세 AI가 함께 쓰고, Hermes 실행 교훈은 `omh_memory`로 OMH 기억에 둔다 |

## 작업 흐름 선택

Hermes는 OMH 설치기가 플러그인과 워크플로 144개를 직접 설치하므로, Claude·Codex용 `shared/rules/omh.md`(OMH 도구를 각 실행기 도구로 대응시키는 절)는 받지 않는다. 대신 Agent-setup이 [OMH 워크플로 규칙](../templates/omh-workflow.md)을 `SOUL.md`의 `agent-setup:omh-workflow` 구간으로 넣는다. 한국어 설명은 [한국어 안내](../../docs/ko/hermes/templates/omh-workflow.md)에 있다.

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

### 바꾼 이유

이전 규칙은 "사용자 스킬이 다루는 단계는 그 스킬, 나머지 단계는 OMH"였다. 사용자 스킬이 있는 작업에서는 OMH 흐름이 거의 쓰이지 않았다. 2026-11-05에 `~/.hermes/state.db`에 남은 기록을 보면 `omh_dag` 호출과 `ulw-work`·`ulw-loop`·`omh-verification-gate` 로드가 모두 0건이었고, OMH Route Hint를 따르지 않은 대화도 2건 이상 있었다. 한국어 문장은 OMH 기본 한국어 트리거 데이터에 `dag-ulw`·`ultrawork` 구문이 없어 이 흐름을 추천받지 못했다.

2026-11-05에 세 가지를 바꿨다.

- 규칙: 작업 형태로 OMH 흐름을 먼저 고르고, 사용자 스킬은 그 흐름 안에서 쓴다. `install_global_rules.py`가 이전 배포본을 알아보고 구간을 바꿀 수 있게 고쳐 이 Mac의 `SOUL.md`에 적용했다. 같은 명령을 다시 실행하면 `unchanged`가 나온다.
- 한국어 트리거 팩: 9개 워크플로에 한국어 구문 42개를 넣었다. OMH 라우터로 확인하니 "백엔드와 프론트엔드를 병렬로 구현해줘"는 `dag-ulw`, "승인된 계획대로 구현해줘"는 `ultrawork`로 바뀌었다. 일상 대화 3개는 전후 모두 흐름이 붙지 않았다.
- 업데이트: `update.sh`가 업데이트 뒤 규칙과 트리거 팩을 다시 맞춘다.

새 세션에서 Hermes가 실제로 흐름을 고르는지는 아직 관찰하지 않았다.

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
