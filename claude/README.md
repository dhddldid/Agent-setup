# Claude Code 구성

Claude Code의 전역 지침·라우팅·스킬 설치 원본을 이 폴더에서 관리한다. 공통 지침과 공통 스킬은 `../shared/`를 사용하며, 모델 후보의 기준은 Hermes 프리셋에서 가져온 `routes/claude-code.json`에 기록한다. 설치 대상은 선택한 Claude Code 사용자 설정 폴더다.

| 항목 | 설치 위치 | 원본 |
|---|---|---|
| 라우팅 에이전트 25개 | `~/.claude/agents/route-<분류>-<계열>.md` | [routes/claude-code.json](routes/claude-code.json) → `scripts/build_agents.py` |
| 라우팅 표 | `~/.claude/agent-setup/routing.json` | 선택한 프리셋 |
| 전역 규칙: 작업 원칙, 스킬 흐름, 작업 형태별 OMH 흐름(`OMH workflow skills`), Aside, 모델 라우팅 | `~/.claude/AGENTS.md` 관리 구간 + `~/.claude/CLAUDE.md`의 `@AGENTS.md` 한 줄 | [templates/global-rules.md](templates/global-rules.md) (`../shared/rules/`에서 생성) |
| 스킬 244개 | `~/.claude/skills/` | 공통 `../shared/skills/core/` 49개 + OMH 최신 정식판 사본 `../shared/skills/omh/` 155개(버전은 `SOURCE.json`) + Claude 전용 `skills/codex` + Codex와 같은 외부 스킬 39개(`../codex/inventories/external-skills.json`) |
| Codex 플러그인 | Claude Code 플러그인 `codex@openai-codex` | [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) |

## 모델 라우팅

Hermes에서 가져온 두 프리셋을 `routes/claude-code.json`에서 Claude Code 정책으로 독립적으로 관리한다. 기본은 Claude 넉넉형이다. `claude-*` 항목은 같은 이름의 Claude 하위 에이전트(`route-<분류>-<계열>`)로, `gpt-*` 항목은 Codex 플러그인의 `codex:codex-rescue`에 `--model`·`--effort`를 붙여 실행한다. GPT 실행은 이 컴퓨터의 Codex CLI 로그인과 Codex 사용 한도를 쓴다.

| 분류 | 용도 | Claude 넉넉형 | GPT 넉넉형 | 추론 |
|---|---|---|---|---|
| `ultrabrain` | 가장 깊은 추론이 필요한 모호한 문제 | gpt-6-astra | gpt-6-astra → claude-fable-5-1 → claude-opus-5-5 | xhigh |
| `deep` | 깊은 구현·디버깅 | claude-opus-5-5 → gpt-6.1-sol | gpt-6.1-sol → claude-fable-5-1 → claude-opus-5-5 | high |
| `architect` | 아키텍처·시스템 경계 설계 | claude-opus-5-5 → gpt-6-astra → claude-fable-5-1 | claude-fable-5-1 → gpt-6-astra → claude-opus-5-5 | xhigh |
| `unspecified-high` | 분류 밖의 복합 작업 | gpt-6.1-sol → claude-opus-5-5 | claude-opus-5-5 | medium |
| `unspecified-low` | 분류 밖의 단순 작업 | gpt-6.1-sol → claude-sonnet-5-5 | claude-opus-5-5 | low |
| `quick` | 좁은 탐색·빠른 확인 | gpt-6-luna → claude-haiku-5-5 | gpt-6-luna → claude-fable-5-1 → claude-opus-5-5 → gpt-6-astra | low |
| `writing` | 문서 작성·편집 | gpt-6.1-sol → claude-opus-5-5 | gpt-6.1-sol → claude-opus-5-5 | medium |
| `visual-engineering` | 화면·프론트엔드 구현 | claude-opus-5-5 → claude-fable-5-1 | claude-fable-5-1 → gpt-6-astra → claude-opus-5-5 | high |
| `artistry` | 창의적 설계·시각 방향 | gpt-6.1-sol → claude-opus-5-5 → claude-fable-5-1 | claude-fable-5-1 → gpt-6-astra → claude-opus-5-5 | high |
| `capable` | 일반 실행 | claude-opus-5-5 → gpt-6.1-sol → claude-fable-5-1 | claude-fable-5-1 → gpt-6-astra → claude-opus-5-5 → claude-sonnet-5-5 | medium |
| `simple-work` | 단순 실행 | gpt-6-luna → claude-haiku-5-5 | gpt-6-luna → claude-fable-5-1 → claude-opus-5-5 → claude-haiku-5-5 | low |
| `deep-work` | 길고 까다로운 복합 실행 | claude-opus-5-5 → gpt-6.1-sol | 같음 | high |

Claude Code에는 하위 에이전트 단위 모델 자동 대체가 없다. 전역 규칙에 따라 주 에이전트가 항목 실패(모델 사용 불가·한도·인증 오류, 빈 Codex 결과)를 보고 같은 작업을 다음 항목에 넘긴다. Fable은 요금제에 따라 별도 사용 크레딧을 쓴다.

## 설치

아래 명령은 `Agent-setup/claude/`에서 실행한다. Python은 3.12 이상을 사용한다. 사용자 설정 폴더를 별도로 쓰면 설치와 로딩 확인에 같은 `--home <경로>`를 지정한다.

```sh
claude plugin marketplace add openai/codex-plugin-cc
claude plugin install codex@openai-codex
python3 scripts/install.py                          # 미리보기
python3 scripts/install.py --apply                  # Claude 넉넉형 적용
python3 scripts/install.py --preset gpt-generous --apply
python3 ../codex/scripts/install_external_skills.py --all --skills-dir ~/.claude/skills  # 외부 39개 미리보기
python3 ../codex/scripts/install_external_skills.py --all --skills-dir ~/.claude/skills --apply
python3 ../codex/scripts/apply_skill_descriptions.py --skill-root ~/.claude/skills
python3 ../codex/scripts/apply_skill_descriptions.py --skill-root ~/.claude/skills --backup-root ~/.claude/agent-setup/backups --apply
python3 scripts/install.py --verify-loading         # 터미널 Claude Code의 전역 규칙 로딩 확인 (모델 1회 호출)
```

전역 규칙은 `~/.claude/AGENTS.md`의 관리 구간에 들어간다. Claude Code가 이 파일을 읽도록 `~/.claude/CLAUDE.md`에 `@AGENTS.md` 한 줄짜리 관리 구간을 둔다. 사용 중인 Claude Code가 AGENTS.md를 직접 읽는다면 `--no-claude-md-pointer`로 그 줄을 빼거나 지운다. 예전 설치가 CLAUDE.md에 넣은 규칙 구간은 다음 적용 때 이 한 줄로 바뀐다. 규칙 원본은 `../shared/rules/`이고 `python3 ../scripts/build_rules.py`가 `templates/global-rules.md`를 만든다.

외부 스킬은 설치할 때 원본별 최신 정식 릴리스 태그로 받는다.

Claude Code에서 `/codex:setup`으로 Codex 설치·로그인을 확인한다. Aside 앱·CLI 설치는 [Hermes 브라우저 안내](../hermes/docs/browsers.md)의 Aside 절을 따른다.

설치기는 처음 쓰는 파일을 추가하고, 자신이 설치한 그대로인 파일만 갱신한다. 사용자가 수정했거나 다른 출처의 같은 경로 파일이 있으면 아무것도 쓰지 않고 충돌 목록을 출력한다. 갱신·삭제 전 파일은 `~/.claude/agent-setup/backups/`에 남는다. 미리보기 결과에 Codex 플러그인과 Aside CLI 설치 여부도 표시한다.

## 업데이트

Agent-setup 루트에서 한 줄로 실행한다. OMH 최신 정식 태그를 조회해 OMH 스킬 사본이 다르면 공식 태그 원본에서 다시 가져오고, 기록된 프리셋으로 이 설치기를 다시 실행한 뒤 외부 스킬을 최신 정식판으로 갱신하고 설명 조정을 다시 적용한다. Codex가 설치된 컴퓨터에서는 Codex 쪽도 함께 갱신한다.

```sh
bash scripts/update_claude_codex.sh            # 적용
bash scripts/update_claude_codex.sh --dry-run  # 실행할 명령과 현재 값
bash scripts/update_claude_codex.sh --check    # 현재 상태만
```

## 완료 확인

1. Claude Code `/agents`에서 `route-*` 23개와 Codex 플러그인을 설치했다면 `codex:codex-rescue`를 확인한다.
2. 작은 읽기 전용 작업을 Claude 항목 하나(예: `route-quick-fable`)와 GPT를 사용한다면 GPT 항목 하나(`--model gpt-6-luna --effort low`)로 위임해 실제 실행 모델을 확인한다.
3. 사용하는 Claude Code 화면에서 전역 규칙 로딩을 확인한다. 터미널 CLI는 `python3 scripts/install.py --verify-loading`의 `loaded` 결과를, Claude 앱 Code 탭은 새 Code 세션의 실제 응답을 확인한다.
4. Aside를 설치한 OS에서 `aside repl`로 선택한 프로필의 페이지를 열고 결과를 읽는다.

## 검사

```sh
python3 scripts/build_agents.py --check
python3 -m unittest discover -s tests -v
```
