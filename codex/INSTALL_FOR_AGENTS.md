# Codex 작업 환경 설치 (AI용)

[설치 공통 기준](../docs/install-common.md)을 따른다. 아래는 Codex에 갖출 것과 완료 기준이다. 설치 방법은 AI가 정한다. 모델은 계정에서 쓸 수 있는 GPT 계열(Astra·Sol·Luna)만 쓴다.

Agent-setup 전체 체크아웃을 사용한다. 이 문서의 `scripts/`, `config/`, `inventories/` 경로는 `codex/` 기준이며, 공통 스킬은 형제 폴더 `shared/skills/`에서 읽는다. Python 3.12 이상을 준비한다.

## 갖출 것

| 항목 | 기준 |
|---|---|
| Codex | 앱 또는 CLI 설치·로그인 상태 |
| 모델 라우팅 | 12개 분류별 GPT 모델·추론 (`working-method.md`, `models.json`) |
| 스킬 | [스킬 표](../docs/skills.md)의 Codex 열 (공통 49개 + OMH 153개 + 외부 39개), `~/.agents/skills/`. 외부 스킬은 설치 시점의 원본별 최신 정식 릴리스 |
| 전역 지침 | `$CODEX_HOME/AGENTS.md` (기본 `~/.codex/AGENTS.md`), 작업 형태별 OMH 흐름 절(`OMH workflow skills`) 포함 |
| 업데이트 | 설치 뒤 Agent-setup 루트에서 `bash scripts/update_claude_codex.sh` |
| MCP | CodeGraph, GAM (`~/.codex/config.toml`, 다른 설정 키 보존) |
| Aside | 공통 기준대로 |

설치 방법은 대상 OS와 기존 환경을 보고 AI가 정한다. 이 저장소의 설치기와 [구성 안내](README.md)는 참고 자료다. Windows는 WSL2의 Linux 홈에서 구성하고 해당 환경의 도구·서비스 연결을 검증한다. [기존 설치 이관](05-change-management.md#기존-codex-setup-설치-이관)에서는 새 원본 경로와 사용자 수정 여부를 확인한다.

## 완료 기준

[공통 검증 기준](../docs/verification.md), [macOS 완료 기준](10-new-machine.md), [앱 작업 준비](15-local-task-readiness.md)를 따른다. 사용자가 작업할 Codex 앱 또는 CLI의 새 작업에서 스킬·GAM·CodeGraph가 보이고 실제로 응답하는지, 실제 코드 저장소 하나에서 CodeGraph 색인 생성 후 심볼 조회와 GAM 시험 기억의 저장·활성화·프로젝트 범위 회수가 되는지(시험 기억은 확인 후 보관 처리), 분류별 모델 위임이 실제로 실행되는지 확인한다. 사용자 홈의 보존된 지침·스킬 차이를 대조한 결과와 함께 항목별 통과·실패·미확인을 보고한다.
