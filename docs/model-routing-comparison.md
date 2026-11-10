# 실행기별 모델 라우팅 비교

확인일: 2026-11-10(KST). OMH 4.0.7 추천표(4.0.6과 동일), Hermes 0.22.7 기준.

## 적용 대상과 출처

| 구분 | 표의 기준 | 출처 |
|---|---|---|
| Codex | 저장소의 GPT 전용 정책 | [작업 방식](../codex/11-working-method.md), [모델 ID](../codex/config/models.json) |
| Claude Code | 저장소 기본 프리셋 `claude-generous` | [라우팅 원본](../claude/routes/claude-code.json) |
| Hermes 커스텀 OMH | 확인 시점에 실제 적용된 18개 사용자 지정 체인 | 선택한 Hermes 환경의 `omh model-chains show --json` |
| OMH 기본값 | OMH 4.0.7 패키지의 기본 체인 | `omh/plugin_bundle/omh/hermes_delegation.py`의 `HERMES_MIXTURE_CATEGORY_CHAINS` |

Codex·Claude Code 열은 설치 원본의 정책을 보여준다. Hermes 커스텀 열은 확인 시점의 적용값을 보여준다. 실제 모델 호출·계정 지원 검증은 실행 기록으로 별도 확인한다. 후보는 왼쪽부터 시도하며 괄호는 행의 모든 후보에 적용되는 추론 강도다.

## 네 가지 구성 비교

| 분류 | Codex | Claude Code · 기본 프리셋 | Hermes 커스텀 OMH · 현재 적용 | OMH 4.0.7 기본값 |
|---|---|---|---|---|
| `ultrabrain` | Astra (`xhigh`) | Astra (`xhigh`) | Astra (`xhigh`) | Astra (`xhigh`) |
| `deep` | Sol (`high`) | Opus → Sol (`high`) | Opus → Sol (`high`) | Opus → Sol → Kimi (`high`) |
| `architect` | Astra (`xhigh`) | Opus → Astra → Fable (`xhigh`) | Opus → Astra → Fable (`xhigh`) | Opus → Astra → Fable → Kimi (`xhigh`) |
| `unspecified-high` | Sol (`medium`) | Sol → Opus (`medium`) | Sol → Opus (`medium`) | Sol → Opus → Kimi (`medium`) |
| `unspecified-low` | Luna (`low`) | Sol → Sonnet (`low`) | Sol → Sonnet (`low`) | GLM-5.3 → DeepSeek Flash → Sol → Sonnet (`low`) |
| `quick` | Luna (`low`) | Luna → Haiku 5.5 (`low`) | Luna → Haiku 5.5 (`low`) | GLM-5.3 Flash → Luna → Haiku 5.5 → Kimi (`low`) |
| `writing` | Sol (`medium`) | Opus → Sonnet (`medium`) | Opus → Sonnet (`medium`) | Opus → Sonnet → Kimi → Gemini (`medium`) |
| `visual-engineering` | Sol (`high`) | Opus → Fable (`high`) | Opus → Fable (`high`) | Opus → Fable → Gemini → Kimi (`high`) |
| `artistry` | Astra (`high`) | Opus → Fable (`high`) | Opus → Fable (`high`) | Gemini → Opus → Fable → Kimi (`high`) |
| `capable` | Sol (`medium`) | Opus → Sol → Fable (`medium`) | Opus → Sol → Fable (`medium`) | Opus → Sol → Fable → Kimi (`medium`) |
| `simple-work` | Luna (`low`) | Luna → Haiku 5.5 (`low`) | Luna → Haiku 5.5 (`low`) | Luna → Haiku 5.5 → DeepSeek Flash (`low`) |
| `deep-work` | Sol (`max`) | Opus → Sol (`max`) | Opus → Sol (`max`) | Opus → Sol (`max`) |

## 두 설치 프리셋 비교

각 실행기는 자기 라우팅 원본을 유지한다. 아래 표는 Claude Code의 두 설치 프리셋을 비교한다. Hermes의 두 설치 프리셋은 [기존 라우팅 안내](../hermes/docs/model-routing.md)와 [README](../README.md#hermes--omh-분류별-위임)에서 확인한다.

| 분류 | Claude 넉넉형 · 기본 | GPT 넉넉형 |
|---|---|---|
| `ultrabrain` | Astra (`xhigh`) | Astra → Fable → Opus (`xhigh`) |
| `deep` | Opus → Sol (`high`) | Sol → Fable → Opus (`high`) |
| `architect` | Opus → Astra → Fable (`xhigh`) | Fable → Astra → Opus (`xhigh`) |
| `unspecified-high` | Sol → Opus (`medium`) | Opus (`medium`) |
| `unspecified-low` | Sol → Sonnet (`low`) | Opus (`low`) |
| `quick` | Luna → Haiku 5.5 (`low`) | Luna → Fable → Opus → Astra (`low`) |
| `writing` | Opus → Sonnet (`medium`) | Sol → Opus (`medium`) |
| `visual-engineering` | Opus → Fable (`high`) | Fable → Astra → Opus (`high`) |
| `artistry` | Opus → Fable (`high`) | Fable → Astra → Opus (`high`) |
| `capable` | Opus → Sol → Fable (`medium`) | Fable → Astra → Opus → Sonnet (`medium`) |
| `simple-work` | Luna → Haiku 5.5 (`low`) | Luna → Fable → Opus → Haiku 5.5 (`low`) |
| `deep-work` | Opus → Sol (`max`) | Opus → Sol (`max`) |

## Hermes 설치 원본과 현재 적용값

2026-11-10 기준 `hermes/routing-presets/claude-generous.json`의 18개 분류 체인은 `omh model-chains show --json`의 현재 적용값과 같다. 2026-11-10 사용자 결정에 따라 Claude 넉넉형(Hermes·Claude Code)은 OMH 4.0.7 추천 순서·추론을 따르고 GPT·Claude가 아닌 후보(Gemini·Grok·Kimi·GLM·DeepSeek)만 뺀다. Fable은 Claude 계열이라 OMH 순서대로 남는다. x-search는 Sol(`high`)이다. Claude Code는 12개 분류만 쓰므로 OMH 전용 6개 분류(google-search·x-search·review·swarm·forensics·synthesize)는 Hermes에만 있다. 자식 공통 fallback(Opus → Astra → Sonnet)과 Codex 정책은 그대로다.

## 정확한 모델 ID

| 표 이름 | 모델 ID |
|---|---|
| Astra | `gpt-6-astra` |
| Sol | `gpt-6.1-sol` |
| Luna | `gpt-6-luna` |
| Fable | `claude-fable-5-1` |
| Opus | `claude-opus-5-5` |
| Sonnet | `claude-sonnet-5-5` |
| Haiku 4.5 | `claude-haiku-4-5` |
| Haiku 5.5 | `claude-haiku-5-5` |
| Kimi K3 | `kimi-k3` |
| GLM-5.3 | `glm-5.3` |
| GLM-5.3 Flash | `glm-5.3-flash` |
| DeepSeek Flash | `deepseek-flash` |
| Gemini 3.1 Pro | `gemini-3.1-pro` |

## 업데이트 후 비교 방법

1. `omh --version`과 `hermes --version`으로 버전을 기록한다.
2. `omh model-chains show --json`으로 사용자 지정 체인과 `origin`을 확인한다.
3. 설치된 같은 버전 패키지의 `HERMES_MIXTURE_CATEGORY_CHAINS`를 읽어 기본값과 비교한다.
4. 기존 `model-chains.json`의 명시된 분류는 사용자 체인을 유지하고, 기본값을 따르는 분류는 새 패키지의 체인을 사용한다.
5. 변경은 사용자가 승인한 실행기·분류에 적용한다. 확인 시점의 스냅샷과 설치 프리셋을 각각 갱신한다.

패키지 기본값 출처 SHA256: `d97311befc37815422bdc42a0f4118d129eb0abe763ae5aa1dfd8f28e38192b6`.
