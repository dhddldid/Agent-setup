# macOS MacBook 설치 기준

이 문서는 검증된 macOS 설치의 완료 기준이다. WSL2는 [README](README.md)의 안내처럼 AI가 스킬·작업 기준을 재사용할 수 있으나 Linux에 맞는 설치·검증이 필요하다. macOS에서는 사용자가 README의 요청문만 보낸다. 이 문서는 설정을 맡은 AI의 **완료 조건**이다. 명령 순서는 AI가 정한다. AI는 대상 MacBook·계정·앱에서 가능한 방법을 선택하고, 필요한 준비·검사·오류 수정을 수행한다.

## 버전 선택

- Codex 앱에서 실제 사용할 수 있는 Sol·Astra·Luna 최신 모델을 확인한다. [모델 분류와 추론 수준](11-working-method.md#모델-역할)은 유지하고, 사용할 수 없는 조합을 임의 대체하지 않는다.
- Python·uv·CodeGraph와 호환되는 Node·Ollama가 대상 Mac에서 동작한다. 이미 있는 도구는 호환성과 상태를 확인하고, 준비 방법은 AI가 환경과 공식 문서를 보고 선택한다.
- GAM·CodeGraph와 외부 스킬은 설치기가 실행할 때마다 원본의 최신 정식 릴리스를 조회해 설치한다. `scripts/setup_runtime.py`는 CodeGraph를 최신 정식 태그의 npm 패키지로, GAM을 최신 정식 태그 커밋에서 `uv tool install`로 설치하고, 결정한 태그·커밋을 `~/Library/Application Support/codex-setup/tool-releases.json`에 기록한다. 정식 릴리스를 내지 않는 원본은 기본 브랜치의 최신 커밋을 받는다.
- `inventories/tools.lock.json`과 `inventories/external-skills.json`에는 원본 저장소·패키지·설치 방법·스킬 경로만 둔다. `config/models.json`은 검증한 모델 식별자 기준이다. 설치 결과는 버전 번호와 함께 실제 도구 동작으로 확인한다.
- 새 정식 릴리스가 설치에 실패하면 실패한 단계와 오류를 보고하고 원인을 고친다. Ollama 서비스·모델·임베딩 응답은 GAM과 별도로 확인한다.
- 이미 설치된 외부 스킬은 `scripts/install_external_skills.py --all --apply --refresh`로 최신 정식판과 대조한다. 설치 당시와 같은 폴더만 교체하고, 설명 줄 외에 사용자가 고친 폴더는 `--replace-existing`에서도 그대로 남는다.
- 설치 뒤 업데이트는 Agent-setup 루트의 `bash scripts/update_claude_codex.sh` 한 줄로 한다. OMH 스킬 사본을 최신 정식 태그로 맞추고 관리 지침·공통 스킬·외부 스킬을 다시 설치한다.

## 완료 조건

| 영역 | 확인할 결과 |
|---|---|
| 로컬 접근 | ChatGPT 앱의 현재 작업이 대상 컴퓨터의 파일·명령에 접근한다. 불가능하면 설정을 진행할 수 있는 로컬 작업 경로를 찾고 필요한 사용자 조치만 알린다. |
| 사용자 홈 적용 | Agent-setup 저장소를 지속 경로에 두고 로그인한 사용자의 실제 홈과 `$CODEX_HOME`에 적용한다. 사용자 설정·인증·기억·무관한 파일을 보존하고 변경 전 백업·복구 경로를 확인한다. |
| Codex 설정 자유도 | 사용자 `config.toml`의 모델·추론·개인 설정을 보존하고 GAM·CodeGraph 연결 블록만 갱신한다. 사용자가 수정한 전역 `AGENTS.md`는 보존한다. 핵심 스킬은 사용자 홈의 독립 복사본으로 설치하고 모델 분담 문서는 `$CODEX_HOME/working-method.md`, 실제 모델 식별자는 `$CODEX_HOME/models.json`에 둔다. |
| 도구 | GAM·CodeGraph가 Codex MCP에 연결되고 실제 응답한다. GAM은 대상 사용자 홈의 Vault·Ollama·임베딩 모델과 의미 검색이 동작한다. CodeGraph는 작업할 Git 저장소에서 색인·변경 반영·직접 호출이 동작한다. 기존 기억의 내용을 보존한다. |
| 스킬 | [전체 목록](03-skills.md)의 64개 스킬을 모두 설치하고 관련 작업에서만 선택한다. [스킬별 과제](inventories/coding-skills.json)로 핵심 스킬의 발견·본문 읽기·선택·행동을 확인하고 업무 스킬의 앱 발견과 대표 사용 조건도 확인한다. 설치 파일의 존재나 CLI 표본만으로 앱의 성공을 판정하지 않는다. |
| 모델·팀장 | [12개 분류](11-working-method.md#모델-역할)에 따라 주 에이전트가 담당·파일 소유권·모델·추론을 실제 배정한다. 가능한 모델·추론 조합의 결과를 회수하고, 격리 코딩 과제에서 구현·독립 리뷰·통합 검사를 확인한다. 요청한 값과 백엔드 관측값을 구분한다. |
| 복구·정리 | 실제 사용자 홈에서 반복 적용에 중복·설정 훼손이 없고 설치 백업의 복구 경로가 유효하다. 만료 임시 기억의 정리와 중요 기억의 보존을 확인한다. 정기 실행은 앱에서 실제 제공되는 기능으로 연결하고 예약 실행의 관측 범위를 보고한다. |
| 앱 재확인 | 새 로컬 코딩 작업에서 스킬과 GAM·CodeGraph 직접 도구가 보이고 실제 응답하는지 확인한다. GAM `memory_status`의 `transport=streamable-http`, `embedding_state=configured`, `keyword_only=false`를 확인한다. 앱 재시작·로그인·macOS 권한이 필요하면 그 단계에서 이어간다. |

## 설치 결과 보고

AI는 사용한 설정 저장소 체크아웃, `$CODEX_HOME`, 스킬 63개, GAM·CodeGraph·Ollama·색인의 실제 경로와 동작 결과를 보고한다. 각 항목은 설치, 앱 발견, 실제 동작을 구분한다. 경로 기준은 [13-environment-components.md](13-environment-components.md)다.

## 제공 도구

`scripts/setup_runtime.py`는 검증한 버전의 계획·적용·상태·복구를, `scripts/probe_tools.py`는 임시 자료로 MCP 동작을, `scripts/probe_gam_semantic.py`는 독립 임시 Vault에서 의미 검색을, `scripts/evaluate_skills.py`는 선택형 보조 평가를 제공한다. GAM 의미 검색에는 Ollama의 로컬 서비스·`nomic-embed-text` 모델과 GAM의 백그라운드 임베딩 서비스가 필요하다. Codex MCP는 준비된 GAM 서비스에 연결하고 서비스가 없을 때 직접 실행으로 전환한다. 이 검사 도구가 시험 자료를 만들더라도 대상 컴퓨터의 실제 적용·앱 검증을 대체하지 않는다. AI는 필요한 도구를 선택해 사용할 수 있다. 설치·검증의 실제 결과는 [15-local-task-readiness.md](15-local-task-readiness.md) 기준으로 완료와 미확인을 구분해 보고한다. 새 컴퓨터의 앱 검증을 앞선 컴퓨터의 기록으로 대체하지 않는다.
