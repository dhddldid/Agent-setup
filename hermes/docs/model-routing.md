# 모델 라우팅

Hermes 내부 위임에 적용하는 사용자 지정 정책이다. 외부 Claude Code·Codex 설정과 현재 대화 모델은 변경하지 않는다. 정확한 모델 ID·순서·추론·fallback은 선택한 프리셋 JSON을 정본으로 삼는다.

## 버전 선택

- [Claude 넉넉형](../routing-presets/claude-generous.json)
- [GPT(코덱스) 넉넉형](../routing-presets/gpt-generous.json)

설치 기본은 Claude 넉넉형이며 GPT(코덱스) 넉넉형은 선택사항이다. [routing-snapshot.json](../routing-snapshot.json)은 Claude형 호환 사본이며 적용 요청에는 프리셋을 명시한다. 설치·전환 요청 없이 기존 환경의 라우팅을 자동 변경하지 않는다.

| 분류 | Claude 넉넉형 | 추론 | GPT 넉넉형 | 추론 |
|---|---|---|---|---|
| ultrabrain | Astra → Opus | xhigh | Astra → Opus | xhigh |
| deep | Opus → Sol | high | Sol → Opus | high |
| architect | Opus → Astra | xhigh | Astra → Opus | xhigh |
| unspecified-high | Sol → Opus | medium | Opus | medium |
| unspecified-low | Sol → Sonnet | low | Opus | low |
| quick | Luna → Opus | low | Luna → Opus → Astra | low |
| writing | Opus → Sonnet → Sol | medium | Sol → Opus | medium |
| visual-engineering | Opus | high | Astra → Opus | high |
| artistry | Opus | high | Astra → Opus | high |
| capable | Opus → Sol | medium | Astra → Opus → Sonnet | medium |
| simple-work | Luna → Haiku 5.5 | low | Luna → Opus → Haiku 4.5 | low |
| deep-work | Opus → Sol | max | Opus → Sol | max |

Claude 넉넉형은 GPT·Claude 후보로 작업별 순서를 구성하고, 최종 fallback을 Opus로 유지한다. Sol은 GPT-6.1 Sol, Luna·Astra는 GPT-6, Opus·Sonnet은 Claude 5.5다. 두 프리셋의 deep-work는 OMH 4.0.0 기본값(Opus → Sol, `max`)을 따른다. 각 실행기의 정책은 해당 폴더에서 독립적으로 관리한다.

## 적용 기준

- GPT·Claude 후보만 사용한다. Kimi·Qwen·Gemini·GLM·DeepSeek를 추가하지 않으며 계정·인증·제공자 연결은 보존한다.
- OMH 분류별 후보와 Hermes 실행 fallback은 별개다. 전역 fallback은 Opus, 자식 공통 fallback은 Opus → Astra → Sonnet이며(2026-10-15 결정: Anthropic 계정 사용량이 모두 소진되면 GPT로 넘어감) 분류 변경으로 공통 순서를 바꾸지 않는다.
- 주 모델이 사용 가능하면 유지한다. 이미 시도한 모델·사용 불가능한 후보는 건너뛴다. 모델별 제한·계정 전체 제한·인증·통신 오류를 구분하고 사용 제한 기록은 초기화하지 않는다.
- 추론은 작업 분류별로 유지하며 전역 모델별 고정으로 대체하지 않는다. 이 프리셋을 최신 모델 목록으로 취급하지 않는다.

선택한 프로필의 로그인·모델 가용성을 확인하고 프리셋의 모든 분류를 적용한다. `~/.omh/routing/model-providers.json`의 `models`에는 GPT 후보를 `openai-codex`, Claude 후보를 `anthropic`으로 연결한다. Claude 넉넉형의 `claude-haiku-5-5`도 같은 이름의 모델과 `anthropic` 제공자를 명시하고 기존 모델 연결을 보존한다. OMH는 연결된 후보를 앞으로 모을 수 있으므로 저장 후 순서·추론·제공자와 실제 자식 fallback을 다시 읽는다.

```sh
omh model-chains show --json
```

공통 fallback 적용 명령:

```sh
hermes config set fallback_providers '[{"provider":"anthropic","model":"claude-opus-5-5"}]'
hermes config set delegation.fallback_providers '[{"provider":"anthropic","model":"claude-opus-5-5"},{"provider":"openai-codex","model":"gpt-6-astra"},{"provider":"anthropic","model":"claude-sonnet-5-5"}]'
```

## fallback 순서·추론 보존

설치된 소스에서 fallback 순서·추론 보존이 필요한지 확인한다. 아래는 소스 호환 패치다. `scripts/` 명령은 Agent-setup의 `hermes/`에서 실행한다.

- `configure_delegation_reasoning.py`: fallback 시 자식에게 배정한 추론을 유지한다.
- `configure_gpt_fallback.py`: GPT 시작 자식에서 Opus를 마지막에 두고 나머지 공통 순서(Astra → Sonnet)를 유지한다. 이전 버전 패치가 설치돼 있으면 같은 명령이 새 순서로 갱신한다. Claude 시작 자식과 공통 설정은 보존한다.

```sh
python3 scripts/configure_delegation_reasoning.py --source-root <확인한-Hermes-소스-루트>
python3 scripts/configure_delegation_reasoning.py --source-root <확인한-Hermes-소스-루트> --apply
python3 scripts/configure_gpt_fallback.py --source-root <확인한-Hermes-소스-루트>
python3 scripts/configure_gpt_fallback.py --source-root <확인한-Hermes-소스-루트> --apply
```

실제 import 경로의 소스 루트를 지정하고 미리보기 후 호환될 때만 적용한다. 변경된 관리 구간·다른 함수 구조·심볼릭 링크는 거부하며 같은 패치는 건너뛴다. 새 프로세스에서 반영을 확인한다. 전환 모델이 추론을 지원하지 않으면 오류를 알리고 수준을 조용히 낮추지 않는다.

## 완료 확인

작업 분류에 맞는 `omh_delegate_route` 적용 직후 `delegate_task`로 최소 실제 위임을 실행한다. 응답과 `session_model_usage`의 모델·`billing_provider`·API 호출 수를 대조하며, 추론이 관측되지 않으면 배정값과 구분한다. 오류가 포함된 `completed`나 대체 모델의 성공을 원래 모델의 성공으로 보고하지 않는다.

fallback 순서와 추론 유지는 실제 한도를 소진하거나 제한을 초기화하지 않고 통제된 시험으로 확인한다. 설정 대조·mock 전환·실제 제공자 호출은 따로 기록한다. 현재 확인 범위와 과거 근거는 [검증 상태](verification.md)에 있다.

## AI에게 적용 요청

아래는 쉘 명령이 아니라 AI 채팅에 붙여 넣는 요청이다. 둘 중 하나만 사용한다.

### Claude 넉넉형 요청

```text
https://github.com/PyeongsaengCoding/Agent-setup 의 main에서 hermes/docs/model-routing.md와 hermes/routing-presets/claude-generous.json을 읽고, 내 현재 Hermes 프로필을 Claude 넉넉형으로 맞춰줘. OMH 분류별 모델 순서·추론과 Hermes 전역·자식 공통 fallback을 구분하고 공통 fallback의 마지막 Opus를 유지해줘. GPT·Claude 계열 외 후보는 모든 분류에서 제거하고, 로그인·구독·다른 프로필은 변경하지 말고, 필요한 호환 패치까지 확인·적용한 뒤 라우팅 설정과 실제 위임 결과를 알려줘.
```

### GPT(코덱스) 넉넉형 요청

```text
https://github.com/PyeongsaengCoding/Agent-setup 의 main에서 hermes/docs/model-routing.md와 hermes/routing-presets/gpt-generous.json을 읽고, 내 현재 Hermes 프로필을 GPT(코덱스) 넉넉형으로 맞춰줘. OMH 분류별 모델 순서·추론과 Hermes 전역·자식 공통 fallback을 구분하고 공통 fallback의 마지막 Opus를 유지해줘. GPT·Claude 계열 외 후보는 모든 분류에서 제거하고, 로그인·구독·다른 프로필은 변경하지 말고, 필요한 호환 패치까지 확인·적용한 뒤 라우팅 설정과 실제 위임 결과를 알려줘.
```

## 선택적 CLI 전환

선택한 버전의 열두 분류를 적용하는 명령이다. 기존 환경에서도 제거한 후보가 남지 않도록 전체 분류를 명시한다. 새 설치는 위 AI 요청으로 전체 프리셋과 호환 패치까지 맞춘다. 현재 프로필을 확인한 뒤 둘 중 한 블록만 실행한다. 미연결 후보를 연결하거나 로그인하지 않는다.

### claude-generous CLI

```sh
omh model-chains set ultrabrain 'gpt-6-astra:xhigh, claude-opus-5-5:xhigh'
omh model-chains set deep 'claude-opus-5-5:high, gpt-6.1-sol:high'
omh model-chains set architect 'claude-opus-5-5:xhigh, gpt-6-astra:xhigh'
omh model-chains set unspecified-high 'gpt-6.1-sol:medium, claude-opus-5-5:medium'
omh model-chains set unspecified-low 'gpt-6.1-sol:low, claude-sonnet-5-5:low'
omh model-chains set quick 'gpt-6-luna:low, claude-opus-5-5:low'
omh model-chains set writing 'claude-opus-5-5:medium, claude-sonnet-5-5:medium, gpt-6.1-sol:medium'
omh model-chains set visual-engineering 'claude-opus-5-5:high'
omh model-chains set artistry 'claude-opus-5-5:high'
omh model-chains set capable 'claude-opus-5-5:medium, gpt-6.1-sol:medium'
omh model-chains set simple-work 'gpt-6-luna:low, claude-haiku-5-5:low'
omh model-chains set deep-work 'claude-opus-5-5:max, gpt-6.1-sol:max'
omh model-chains show --json
```

### gpt-generous CLI

```sh
omh model-chains set ultrabrain 'gpt-6-astra:xhigh, claude-opus-5-5:xhigh'
omh model-chains set deep 'gpt-6.1-sol:high, claude-opus-5-5:high'
omh model-chains set architect 'gpt-6-astra:xhigh, claude-opus-5-5:xhigh'
omh model-chains set unspecified-high 'claude-opus-5-5:medium'
omh model-chains set unspecified-low 'claude-opus-5-5:low'
omh model-chains set quick 'gpt-6-luna:low, claude-opus-5-5:low, gpt-6-astra:low'
omh model-chains set writing 'gpt-6.1-sol:medium, claude-opus-5-5:medium'
omh model-chains set visual-engineering 'gpt-6-astra:high, claude-opus-5-5:high'
omh model-chains set artistry 'gpt-6-astra:high, claude-opus-5-5:high'
omh model-chains set capable 'gpt-6-astra:medium, claude-opus-5-5:medium, claude-sonnet-5-5:medium'
omh model-chains set simple-work 'gpt-6-luna:low, claude-opus-5-5:low, claude-haiku-4-5:low'
omh model-chains set deep-work 'claude-opus-5-5:max, gpt-6.1-sol:max'
omh model-chains show --json
```

## 업데이트

Hermes와 OMH를 최신 정식 릴리스로 올리고 이 사용자의 수정 사항을 다시 맞추는 명령은 하나다. 실행 중인 Hermes 작업이 끝나면 Hermes Desktop을 ⌘Q로 종료하고 터미널 앱에서 실행한다.

```bash
bash "$AGENT_SETUP/hermes/scripts/update.sh"   # AGENT_SETUP = 이 컴퓨터의 Agent-setup 체크아웃
```

Agent-setup 루트에서는 `bash hermes/scripts/update.sh`로 실행한다. `--dry-run`은 단계별 명령과 확인한 값(설치·최신 버전, 실제 omh 경로)만 출력하고, `--check`는 버전과 사용자 지정 상태만 보고한다. 업데이트가 게이트웨이를 재시작하므로 Hermes 안의 터미널에서는 실제 실행을 거부한다.

- 버전: Hermes와 OMH 모두 GitHub `releases/latest` 리다이렉트에서 실행 시점의 최신 정식 태그를 읽는다. Hermes는 stable 채널에서 `hermes update --backup --yes`로 올린다. OMH는 PATH의 `omh`가 실제로 실행하는 설치본으로 `omh update --channel stable --version <최신>`을 실행한다. `omh`는 `OMH_VERSION` 환경변수를 읽지 않고, 옵션 없는 `omh update`는 preview(main.zip)를 받는다.
- 유지와 재적용: 시작 전에 모델 체인 사용자 지정, Hermes 설정(model·fallback·delegation·스킬 폴더·플러그인·메모리·Aside·updates), SOUL 관리 블록, 사용자 스킬, 한국어 트리거 팩, 패치 상태를 `$TMPDIR`에 기록한다. 업데이트 뒤 Hermes 수정 묶음(`apply_local_patches.py --apply`), 소스 호환 패치 두 개, SOUL 관리 블록, 한국어 트리거 팩, provider-usage 표시를 다시 맞추고 `omh doctor`·`hermes doctor`를 실행한다. 이어서 시작 전 기록과 비교한 유지·변경·없어짐 표를 출력하고 게이트웨이를 재시작한 뒤 최종 버전을 보여준다. 항목별 저장 위치와 업데이트 때 동작은 [사용자 지정 항목과 업데이트](omh-and-agent-setup.md#사용자-지정-항목과-업데이트)에 있다.
- 멈추는 경우: Agent-setup에 새 Hermes 태그용 패치(`hermes/patches/hermes-agent/<태그>.patch`)가 없으면 아무것도 바꾸기 전에 멈춘다. 업데이트 뒤 패치 적용 결과가 `no_patch`·`conflict`여도 그 단계에서 멈춘다. 이때 AI에게 "Agent-setup 수정 묶음을 Hermes <태그>에 옮겨줘"라고 요청한다. AI는 이전 태그 패치를 새 버전에 맞춰 적용·시험한 뒤 아래 명령으로 새 태그 패치를 저장하고, 사용자는 같은 명령을 다시 실행한다. Hermes 채널이 stable 이외이거나, 업데이트 뒤 버전이 최신과 다르거나, SOUL.md의 관리 블록을 직접 고친 경우에도 멈춘다.

  ```bash
  cd ~/.hermes/hermes-agent && cp .git/index "$TMPDIR/idx" && GIT_INDEX_FILE="$TMPDIR/idx" git add -A && GIT_INDEX_FILE="$TMPDIR/idx" git diff --cached --binary HEAD > "$AGENT_SETUP/hermes/patches/hermes-agent/$(git describe --tags --exact-match).patch"
  ```

  provider-usage는 `dashboard/`·`tests/` 경로만 같은 방식으로 저장한다(`desktop/plugin.js`는 `configure_provider_usage.py`가 따로 맞춘다).
- stash: 이전 업데이트가 남긴 `hermes-update-autostash` stash는 목록만 보여주고 그대로 둔다. Hermes Desktop의 업데이트 버튼은 `--keep-stash`로 로컬 수정을 stash에 남기고 다시 적용하지 않으므로, 업데이트는 이 명령으로 한다.
- 이전 OMH venv(`~/.local/share/omh/venv`): 업데이트와 점검이 성공하고, PATH의 `omh`가 generation 설치본을 실행하며, 이 venv를 가리키는 명령·프로세스가 없을 때 휴지통으로 옮긴다. 조건이 남아 있으면 이유를 출력하고 그대로 둔다. curl 설치기로 업데이트하면 이 venv가 다시 생긴다.
- 갱신 뒤 Agent-setup 루트에서 `python3 scripts/check_releases.py`로 저장소 고정값이 최신 정식 릴리스와 같은지 확인한다. `behind`가 나온 항목은 고정값·사본·문서를 함께 올린다.
- 점검 경고 중 선택 기능(Docker, OpenRouter, image_gen 등)의 `⚠`와 OMH doctor의 `plugin_loader_observed`·`plugin_runtime_observed`는 터미널 점검에서 Hermes 실행을 관측하지 못했다는 표시다. 재시작 뒤 Desktop 새 세션에서 OMH 도구 호출이 되면 정상이다. 점검이 실패하면 명령은 종료 코드 2로 끝나고 이전 OMH venv를 옮기지 않는다.

갱신 뒤 Hermes Desktop 새 세션에서 플러그인 로딩, 실제 위임 모델, 계정 선택·사용량 표시를 확인한다.
