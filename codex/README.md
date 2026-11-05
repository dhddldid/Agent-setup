# Codex 작업 환경

**ChatGPT/Codex 코딩 환경을 구성하는 설치 원본입니다.** 현재 자동 설치와 통합 검증은 macOS 사용자 계정에서 수행했습니다. WSL2에서는 AI가 같은 스킬·작업 기준을 가져와 Linux 환경에 맞게 설치할 수 있지만, 아래 macOS 설치기를 그대로 실행하는 방식은 지원하지 않습니다.

Hermes·OMH 실행 환경 없이 Codex, CodeGraph, GAM을 사용합니다. OMH에서 차용한 계획·작업 분담·독립 리뷰·검증 원칙을 Codex 스킬로 제공합니다. 설정 방법과 관리 도구만 Git으로 배포하며 실제 기억·인증·대화는 각 도구의 비공개 저장소에 둡니다.

## 설치 요청문

설정할 MacBook의 ChatGPT 앱에서 해당 컴퓨터의 파일·명령을 사용할 수 있는 대화에 다음 문장을 보냅니다.

> https://github.com/PyeongsaengCoding/Agent-setup 저장소를 내 MacBook의 `$HOME/Downloads/Agent-setup`에 받아 그 안의 `codex/INSTALL_FOR_AGENTS.md`에 따라 Codex 코딩 환경을 설정해줘. 이미 받은 폴더가 있으면 그 체크아웃을 확인해 사용해줘. Homebrew가 없으면 공식 안내에 따라 준비하고, Python·uv·호환되는 Node LTS·GAM·CodeGraph·Ollama와 스킬 63개는 각각 설치 시점의 최신 안정판 또는 최신 검토된 원본을 확인해 설치·갱신해줘. 내 계정에서 사용할 수 있는 최신 모델을 확인하고, GAM은 공식 `uv tool install`의 기본 위치에 설치해줘. Ollama 서비스와 임베딩 모델을 준비해 의미 검색까지 검사해줘. [완료 기준](10-new-machine.md)에 따라 **이 컴퓨터의 ChatGPT 앱에서** 실제 코딩 작업을 검증하고, 설치 경로와 완료·미완료 항목, 내가 해야 하는 일만 알려줘.

WSL2에서는 AI에게 이 저장소를 기준으로 WSL의 Linux 홈에 Codex CLI·스킬·도구를 구성해 달라고 요청할 수 있습니다. 스킬 지침은 재사용할 수 있지만 Homebrew, `launchctl`, macOS 경로를 쓰는 설치 절차는 Linux용으로 바꿔야 합니다. WSL2 설치 결과와 앱 연결은 그 환경에서 검증합니다. [공식 WSL 안내](https://learn.chatgpt.com/docs/windows/wsl)를 따릅니다.

## 실제 설정 위치와 자유도

Agent-setup의 `codex/`는 설치·업데이트를 재현하기 위한 원본입니다. 사용 중인 모델·추론·개인 설정은 Codex의 `$CODEX_HOME/config.toml`(기본 `~/.codex/config.toml`)에서 선택합니다. 설치기는 GAM·CodeGraph 연결 블록만 관리하고 다른 설정 키를 보존합니다. 공통 `AGENTS.md`와 모델 분담 문서, 모델 식별자 파일에 개인 수정이 있으면 재설치 때 덮어쓰지 않습니다. 핵심 스킬은 `~/.agents/skills/`에 독립 복사본으로 설치하고 모델 분담 문서는 `$CODEX_HOME/working-method.md`, 실제 모델 식별자는 `$CODEX_HOME/models.json`에 둡니다. 평소 모델 배정은 이 로컬 파일을 읽습니다. 설치·업데이트 도구는 Agent-setup 체크아웃의 `codex/`를 원본으로 사용합니다. 설치 영수증의 `setup_root`도 이 하위 폴더를 가리킵니다. 폴더를 이동하거나 기존 Codex-Setup 설치를 이관할 때는 [변경·복구 절차](05-change-management.md)에 따라 원본 참조와 사용자 수정 보존 여부를 확인합니다.

Agent-setup의 `codex/`는 프로젝트별 지침·계정·포트·서비스 연결 파일을 포함하거나 설치하지 않습니다. 해당 정보는 각 프로젝트 또는 사용자 환경에서 별도로 관리합니다.

Claude가 같은 사용자 계정에서 Codex CLI를 실행하면 **Codex CLI 프로세스**가 해당 계정의 Codex 설정과 `~/.agents/skills/`를 읽습니다. Claude 자체에 Codex 스킬이 자동 설치되는 것은 아닙니다. WSL의 Codex CLI는 기본적으로 별도의 Linux 홈을 사용하므로 Windows/macOS 계정의 스킬과 설정을 자동 공유하지 않습니다.

## 설치 구성

| 영역 | 구성 | 확인 방법 |
|---|---|---|
| 작업 방식 | 현재 대화의 주 에이전트가 팀장으로 목표·담당·파일 소유권·검증을 관리 | 앱에서 실제 배정·결과 회수·통합 과제 |
| 모델 라우팅 | [OMH v4.0.0 원본 12개 분류·추론](https://github.com/rlaope/oh-my-hermes/blob/36e96feb432068cd27eecf5b434acdf1328341b4/README.md#recommended-models)을 [Codex 모델·추론 표](11-working-method.md#모델-역할)에 매핑 | 담당별 모델·추론 요청과 실행 결과 |
| 코드 이해 | CodeGraph 앱 직접 도구·로컬 색인 | 실제 저장소 탐색과 변경 반영 |
| 장기기억 | GAM MCP·독립 Vault·Ollama 임베딩 | 후보·승인·범위·키워드와 의미 검색 검사 |
| 스킬 63개 | 계획·구현·검토와 Azure·마케팅 등 [전체 목록](03-skills.md#스킬도구-전체-목록)을 모두 설치 | 관련 작업에서만 선택·행동 평가 |
| 유지관리 | 반복 설치·백업·복구·기록 정리 | 실제 Mac 사용자 홈의 재적용·복구 검사 |

GAM·CodeGraph·Ollama의 설치 위치, 사용 조건, 자동화 범위와 Ollama의 벡터 검색 역할은 [스킬·도구 전체 목록](03-skills.md)에 정리했습니다.

## 시작 문서

| 목적 | 문서 |
|---|---|
| AI 설치 완료 기준 | [10-new-machine.md](10-new-machine.md) |
| 스킬·도구 전체 목록과 설치 방식 | [03-skills.md](03-skills.md) |
| 모델·추론·실행 흐름 | [11-working-method.md](11-working-method.md) |
| 앱 로컬 작업 준비 상태 | [15-local-task-readiness.md](15-local-task-readiness.md) |
| 데이터 위치·도구 경계 | [13-environment-components.md](13-environment-components.md) |
| 업데이트·복구 | [05-change-management.md](05-change-management.md) |
| 스킬 검증 기준 | [12-skill-application.md](12-skill-application.md) |
| 차용 출처 | [upstream/README.md](upstream/README.md) |

## 완료 기준

설정 명령의 성공만으로 완료하지 않습니다. 도구 연결, 12개 분류 설정, 스킬별 실제 행동, 통합 과제, 재실행·복구를 구분해 검사합니다. 호스트가 모델 실행값이나 스킬 읽기 기록을 제공하지 않으면 그 항목은 미확인입니다. Desktop 재시작·개인 로그인·외부 계정 검증이 필요한 경우 완료한 단계에서 이어갑니다.

설치기는 GAM·CodeGraph·외부 스킬을 실행할 때마다 원본의 최신 정식 릴리스로 설치하고, AI는 그 버전에 필요한 런타임을 준비합니다. 설치 뒤 업데이트는 Agent-setup 루트에서 `bash scripts/update_claude_codex.sh` 한 줄로 합니다. OMH 스킬 사본을 최신 정식 태그로 맞추고 관리 지침·공통 스킬·외부 스킬을 다시 설치하며, `--dry-run`은 실행할 명령과 현재 값만 보여줍니다. 앱에서 코딩할 때 Codex CLI를 별도로 실행할 필요는 없습니다.

## 설치 위치

macOS 설치는 **실제 사용할 사용자 계정**에 적용합니다. 설정 저장소의 권장 위치는 `$HOME/Downloads/Agent-setup`(즉 `/Users/<사용자명>/Downloads/Agent-setup`)입니다. 이미 다른 경로에 받았다면 그 체크아웃을 사용할 수 있습니다. 설치된 핵심 스킬은 독립 복사본이며 저장소를 옮겨도 평소 사용은 계속됩니다.

| 구성 | macOS 설치 위치 |
|---|---|
| 설정 저장소 체크아웃 | `$HOME/Downloads/Agent-setup`; 다른 지속 경로에 받았다면 실제 체크아웃 경로. Codex 설치 원본은 그 안의 `codex/` |
| Codex 설정·공통 지침 | `$CODEX_HOME/config.toml`, `$CODEX_HOME/AGENTS.md`, `$CODEX_HOME/working-method.md`, `$CODEX_HOME/models.json`; 기본 `~/.codex/` |
| 스킬 63개 | `~/.agents/skills/<스킬명>/SKILL.md`; 항목별 연결·복사 방식은 [전체 표](03-skills.md) |
| GAM 실행 파일 | `$(uv tool dir --bin)/global-memory-mcp` |
| CodeGraph 실행 파일 | `~/Library/Application Support/codex-setup/tools/codegraph/node_modules/.bin/codegraph` |
| GAM 프로그램 환경 | `$(uv tool dir)/global-memory-mcp/` |
| 설치 영수증·백업 | `~/Library/Application Support/codex-setup/` |
| GAM 기억 원본 | `~/Documents/Global Agent Memory/` |
| GAM 설정·검색 DB·인증 파일 | `~/Library/Application Support/global-memory/` |
| GAM 로그 | `~/Library/Logs/global-memory/` |
| Ollama 실행 파일·모델 | `$(brew --prefix)/bin/ollama`, `~/.ollama/models/`; 실제 경로는 설정 결과에서 확인 |
| CodeGraph 색인 | 실제 사용하는 각 Git 저장소의 `.codegraph/` |

GAM은 [공식 설치 안내](https://github.com/ozankasikci/global-agent-memory#quick-start)의 `uv tool install`을 사용합니다. Agent-setup의 `codex/`는 GAM 프로그램의 설치 경로를 지정하지 않고 `uv tool dir`과 `uv tool dir --bin`의 결과를 사용합니다. `~`는 **설치할 Mac에 로그인한 사용자 홈**입니다. 설치 결과에는 이 기기의 절대 경로를 출력합니다. 세부 소유권과 보관 정책은 [설치 구성과 데이터 위치](13-environment-components.md)를 따릅니다. 기억·인증·대화·로그는 GitHub에 올리지 않습니다.
