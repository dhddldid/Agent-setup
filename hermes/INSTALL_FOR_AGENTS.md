# Hermes 작업 환경 설치 (AI용)

[설치 공통 기준](../docs/install-common.md)을 따른다. 아래는 Hermes에 갖출 것과 완료 기준이다. 설치 방법은 AI가 각 공식 문서를 확인해 정한다. 설치 대상은 **Apple Silicon(M 시리즈) Mac**이다. 다른 컴퓨터면 지원 범위를 사용자에게 알리고 진행 여부를 묻는다.

## 갖출 것

| 항목 | 기준 | 참고 |
|---|---|---|
| Hermes | Desktop 또는 CLI 설치, 사용자가 GPT·Claude 계정 로그인. 인증 파일은 로컬에만 | [공식 설치 안내](https://hermes-agent.nousresearch.com/docs/getting-started/installation) |
| Desktop UI 크기 | 기존 ChatGPT·Claude 앱이 있으면 창·글자·UI 크기를 맞춤 | [UI 크기](docs/desktop-ui.md) |
| 스킬 | [스킬 표](../docs/skills.md)의 Hermes 열 (Hermes 공식 57개 + 공통 34개 + 외부 39개). 공식 스킬은 설치 시점에 조회한 Hermes 최신 정식 태그의 원본 그대로 | [설치 목록](INSTALL-LIST.md), `scripts/install_skills.py` |
| 외부 스킬 | Codex·Claude와 같은 Azure·마케팅·모션 디자인 등 39개를 `$HERMES_HOME/skills/`에. 같은 설명 조정 적용 | `../codex/inventories/external-skills.json`, `../codex/config/skill-descriptions.json` |
| OMH | 실행 시점의 최신 정식 릴리스로 설치·setup(`omh update --channel stable --version <최신 태그>`), 연결한 GPT·Claude 제공자 반영 | [OMH 공식 안내](https://github.com/rlaope/oh-my-hermes/releases/latest) |
| 모델 라우팅 | Claude 넉넉형 (사용자가 원하면 GPT 넉넉형), 필요한 호환 패치 | [모델 라우팅](docs/model-routing.md) |
| 전역 규칙 | 선택한 프로필의 `SOUL.md`에 공통 작업 원칙·Aside·문서 전달 구간 | [전역 규칙](docs/global-rules.md), `scripts/install_global_rules.py` |
| 사용량 플러그인 | `PhoeniXAbhisheK/hermes-plugin-provider-usage`의 최신 정식 릴리스 태그, GPT·Claude만 표시, 수정 묶음 `patches/provider-usage/<태그>.patch` 적용(새 태그용 패치가 없으면 먼저 이전) | [사용량 표시](docs/provider-usage.md), `scripts/configure_provider_usage.py` |
| 본체 수정 묶음 | 최신 정식 Hermes 체크아웃에 `patches/hermes-agent/<태그>.patch`(계정 선택·사용량 표시·모델별 계정 쿨다운·턴 복구) 적용 | `scripts/apply_local_patches.py` (기본 보고, `--apply`로 적용) |
| MCP | CodeGraph, GAM | 공통 기준 |
| 브라우저 | Aside 설치, 사용자가 고른 프로필 가져오기, Aside 연결 장치 설치(`scripts/install_aside_bridge.py`), Hermes에서 `repl` 직접 조작 | [브라우저](docs/browsers.md), [배포 규칙](templates/aside-browser.md) |
| Discord (선택) | 사용자가 Discord를 쓰면 프로젝트별 채널·결과 보고 플러그인·매일 정리 작업 구성 | [Discord 연동](docs/discord.md), `discord/` |

제공된 설치·호환 패치 스크립트와 안내 문서는 참고 자료다. 기존 파일과 충돌하면 차이를 확인해 처리한다. 스킬이 쓰는 Python 라이브러리는 프로젝트 `.venv/`에 둔다.

## 적용 범위

선택한 Hermes 프로필의 실제 홈에 구성한다. 이름 있는 프로필은 `~/.hermes/profiles/<이름>/`을 대상으로 한다. 공식 스킬 57개는 Hermes 최신 정식 태그의 원본과, 공통 스킬은 루트 `shared/skills/`와 일치해야 한다. 외부 스킬 39개는 Codex와 같은 목록과 설명 조정을 사용한다. [라우팅](docs/model-routing.md)·[사용량 표시](docs/provider-usage.md)·[브라우저](docs/browsers.md)·[UI 크기](docs/desktop-ui.md)는 선택한 프로필에 적용한다. 검사 기준은 [검증 안내](docs/verification.md)를 따른다.

설치 결과에는 선택한 프로필, 적용 원본과 관리 구간, 충돌, 새 세션 검증 결과를 기록한다. 제품의 AGENTS·디자인·코드·lint·CI 설정은 해당 제품 저장소의 생성·적용 절차에서 관리한다.

## 보존과 완료 기준

선택한 프로필만 바꾼다. 다른 프로필, 설치 대상 외의 설정, 기존 브라우저 데이터, 사용자의 포커스·입력 대상·커서를 보존한다. 완료된 단계부터 이어간다.

선택한 Hermes 프로필의 새 세션에서 [공통 검증 기준](../docs/verification.md)에 따라 확인하고 항목별 통과·실패·미확인을 기록한다. 기존 스킬 충돌은 각 차이의 처리 결과와 실제 스킬 발견 여부를 함께 남긴다.

- Desktop 질문 응답, 연결한 제공자의 실제 자식 모델·provider·응답, 라우팅 문서의 fallback·추론 검증
- 전역 규칙 로딩과 문서 전달 시 실제 폴더 카드 제공·앱 미실행
- 사용량 조회·리셋 시간·새로고침과 상태바·툴팁·상세 패널·알림의 GPT·Claude 표시 제한
- CodeGraph·GAM MCP 도구 실제 응답: 실제 코드 저장소 하나에서 색인 생성 후 심볼 조회, GAM 시험 기억의 저장·활성화·프로젝트 범위 회수(시험 기억은 확인 후 보관 처리)
- 프로젝트별 Aside 프로필에서 `repl` 이동·입력·결과 읽기, 자체 AI 미호출과 포커스 보존
- 기준 앱이 있으면 창·글자·UI 크기 비교와 설정 유지 (재실행 확인 전에는 미확인)
