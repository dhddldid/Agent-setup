# 스킬·도구 전체 목록

MacBook 설정에서 아래 스킬 66개를 **모두 설치**한다. 표의 구분은 설치 여부가 아니라 사용 시점을 나타낸다. 관련 작업에서만 스킬 본문을 읽고, 설치·앱 발견·실제 행동은 따로 확인한다. `~`는 설정할 컴퓨터의 사용자 홈이다. 도구와 외부 스킬은 설치할 때 원본의 최신 정식 릴리스를 조회해 설치한다.

| 구분 | 항목 | 사용하는 때·역할 | 실제 설치 위치 | 설치 방식·연결 |
|---|---|---|---|---|
| 핵심 | `coding-plan` | 여러 계약을 바꾸는 기능의 범위·완료 조건 결정 | `~/.agents/skills/coding-plan/SKILL.md` | Agent-setup `shared/skills/core/coding-plan` 복사 |
| 핵심 | `coding-research` | 외부 사양·라이브러리 선택 근거 조사 | `~/.agents/skills/coding-research/SKILL.md` | Agent-setup `shared/skills/core/coding-research` 복사 |
| 핵심 | `coding-design-review` | 권한·데이터·시스템 경계의 반례 검토 | `~/.agents/skills/coding-design-review/SKILL.md` | Agent-setup `shared/skills/core/coding-design-review` 복사 |
| 핵심 | `codegraph-context` | 코드 위치·호출 관계·변경 영향이 불명확할 때 | `~/.agents/skills/codegraph-context/SKILL.md` | Agent-setup `shared/skills/core/codegraph-context` 복사; CodeGraph MCP 사용 |
| 핵심 | `coding-work` | 복합 코딩 작업의 담당·모델·파일 소유권 배정과 통합 | `~/.agents/skills/coding-work/SKILL.md` | Agent-setup `shared/skills/core/coding-work` 복사; 앱 위임 사용 |
| 핵심 | `coding-handoff` | 담당 간 인계·중단 작업 재개 | `~/.agents/skills/coding-handoff/SKILL.md` | Agent-setup `shared/skills/core/coding-handoff` 복사 |
| 핵심 | `coding-code-review` | 변경 코드와 요구사항의 재현 가능한 결함 검토 | `~/.agents/skills/coding-code-review/SKILL.md` | Agent-setup `shared/skills/core/coding-code-review` 복사 |
| 핵심 | `coding-failure-audit` | 예외·미확정 상태를 정상처럼 처리하는지 검사 | `~/.agents/skills/coding-failure-audit/SKILL.md` | Agent-setup `shared/skills/core/coding-failure-audit` 복사 |
| 핵심 | `coding-ai-slop-review` | 제품 화면의 중복·빈 안내·내부 상태 노출 검토 | `~/.agents/skills/coding-ai-slop-review/SKILL.md` | Agent-setup `shared/skills/core/coding-ai-slop-review` 복사 |
| 핵심 | `coding-debt-audit` | 유지보수 문제를 근거·영향·노력으로 정리 | `~/.agents/skills/coding-debt-audit/SKILL.md` | Agent-setup `shared/skills/core/coding-debt-audit` 복사 |
| 핵심 | `coding-verification` | 요구사항별 검증 증거와 완료 범위 판단 | `~/.agents/skills/coding-verification/SKILL.md` | Agent-setup `shared/skills/core/coding-verification` 복사 |
| 핵심 | `coding-repair` | 실패한 검증 수정·중단 구현 재개 | `~/.agents/skills/coding-repair/SKILL.md` | Agent-setup `shared/skills/core/coding-repair` 복사 |
| 핵심 | `coding-status` | 여러 작업의 상태·검증 결과 요약 | `~/.agents/skills/coding-status/SKILL.md` | Agent-setup `shared/skills/core/coding-status` 복사 |
| 핵심 | `gam-memory` | 관련 과거 결정 검색·승인된 지식 저장 | `~/.agents/skills/gam-memory/SKILL.md` | Agent-setup `shared/skills/core/gam-memory` 복사; GAM MCP 사용 |
| 핵심 | `coding-maintenance` | 설정·기억·기록의 보존 정책과 승인된 정리 | `~/.agents/skills/coding-maintenance/SKILL.md` | Agent-setup `shared/skills/core/coding-maintenance` 복사 |
| 핵심 | `tdd` | 중요한 로직에서 실패 테스트부터 구현 | `~/.agents/skills/tdd/SKILL.md` | Agent-setup `shared/skills/core/tdd` 복사 |
| 핵심 | `diagnosing-bugs` | 원인 불명 버그·성능 저하 재현과 가설 검증 | `~/.agents/skills/diagnosing-bugs/SKILL.md` | Agent-setup `shared/skills/core/diagnosing-bugs` 복사 |
| 핵심 | `ponytail` | 기존 코드·플랫폼 기능으로 구현 단순화 | `~/.agents/skills/ponytail/SKILL.md` | Agent-setup `shared/skills/core/ponytail` 복사 |
| 핵심 | `writing-for-agents` | AGENTS.md·스킬 지침 간결화 | `~/.agents/skills/writing-for-agents/SKILL.md` | Agent-setup `shared/skills/core/writing-for-agents` 복사 |
| 핵심 | `product-design-review` | 사용자 화면·흐름 구현과 시각 검증 | `~/.agents/skills/product-design-review/SKILL.md` | Agent-setup `shared/skills/core/product-design-review` 복사 |
| 핵심 | `agent-setup-maintenance` | AI 작업 환경(전역 지침·라우팅·공통 스킬·도구) 변경 관리 | `~/.agents/skills/agent-setup-maintenance/SKILL.md` | Agent-setup `shared/skills/core/agent-setup-maintenance` 복사 |
| 핵심 | `aside-browser` | 브라우저 작업을 Aside `repl`로 직접 조작 | `~/.agents/skills/aside-browser/SKILL.md` | Agent-setup `shared/skills/core/aside-browser` 복사 |
| 핵심 | `humanize-korean` | 한국어 문서·응답의 번역투·상투 표현 교정 | `~/.agents/skills/humanize-korean/SKILL.md` | Agent-setup `shared/skills/core/humanize-korean` 복사 |
| 업무 | `microsoft-foundry` | Foundry 모델·에이전트의 구축·운영 | `~/.agents/skills/microsoft-foundry/SKILL.md` | [Microsoft Azure Skills](https://github.com/microsoft/azure-skills)에서 복사 |
| 업무 | `airunway-aks-setup` | AI Runway의 AKS 모델 서빙 준비 | `~/.agents/skills/airunway-aks-setup/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `appinsights-instrumentation` | Application Insights 계측 구성 | `~/.agents/skills/appinsights-instrumentation/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-ai` | Azure AI Search·Speech·OpenAI·문서 처리 | `~/.agents/skills/azure-ai/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-aigateway` | AI 서비스용 API Management 게이트웨이 | `~/.agents/skills/azure-aigateway/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-cloud-migrate` | 다른 클라우드에서 Azure로 이전 | `~/.agents/skills/azure-cloud-migrate/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-compliance` | Azure 보안·준수 상태 점검 | `~/.agents/skills/azure-compliance/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-compute` | Azure VM·VMSS 용량과 운영 | `~/.agents/skills/azure-compute/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-deploy` | 준비된 Azure 배포 실행 | `~/.agents/skills/azure-deploy/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-diagnostics` | Azure 장애·로그 진단 | `~/.agents/skills/azure-diagnostics/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-enterprise-infra-planner` | 기업 Azure 인프라 설계·구성 | `~/.agents/skills/azure-enterprise-infra-planner/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-kubernetes` | AKS 클러스터 구축·운영 | `~/.agents/skills/azure-kubernetes/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-kusto` | Azure 로그·시계열 KQL 분석 | `~/.agents/skills/azure-kusto/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-messaging` | Event Hubs·Service Bus 문제 해결 | `~/.agents/skills/azure-messaging/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-prepare` | 요청된 azd 배포 파일 준비 | `~/.agents/skills/azure-prepare/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-quotas` | Azure 할당량·지역별 용량 확인 | `~/.agents/skills/azure-quotas/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-rbac` | Azure 역할·조건·권한 설계 근거 확인 | `~/.agents/skills/azure-rbac/SKILL.md` | [MicrosoftDocs Agent Skills](https://github.com/MicrosoftDocs/Agent-Skills) 최신 원본 복사; 공식 문서 조회 필요 |
| 업무 | `azure-reliability` | Azure App Service·Functions 복원력 점검 | `~/.agents/skills/azure-reliability/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-resource-lookup` | 구독 전체 Azure 리소스 조회 | `~/.agents/skills/azure-resource-lookup/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-resource-visualizer` | Azure 리소스 관계 도식화 | `~/.agents/skills/azure-resource-visualizer/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-storage` | Blob·Files·Queues·Tables·Data Lake 작업 | `~/.agents/skills/azure-storage/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-upgrade` | Azure 요금제·서비스·SDK 업그레이드 | `~/.agents/skills/azure-upgrade/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `azure-validate` | Azure 배포 전 설정·권한 점검 | `~/.agents/skills/azure-validate/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `entra-agent-id` | Entra 에이전트 ID·토큰 교환 구성 | `~/.agents/skills/entra-agent-id/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `entra-app-registration` | Entra 앱 등록·OAuth·MSAL 구성 | `~/.agents/skills/entra-app-registration/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `python-appservice-deploy` | Python 앱을 Azure App Service에 배포 | `~/.agents/skills/python-appservice-deploy/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `copywriting` | 마케팅 페이지·캠페인 문구 작성 | `~/.agents/skills/copywriting/SKILL.md` | [Marketing Skills](https://github.com/coreyhaines31/marketingskills) 원본 복사 |
| 업무 | `seo-audit` | 웹 검색 노출·기술 SEO 점검 | `~/.agents/skills/seo-audit/SKILL.md` | Marketing Skills 원본 복사 |
| 업무 | `aso` | 앱 스토어 검색·전환 점검 | `~/.agents/skills/aso/SKILL.md` | Marketing Skills 원본 복사 |
| 업무 | `analytics` | 제품·마케팅 이벤트 계측 | `~/.agents/skills/analytics/SKILL.md` | Marketing Skills 원본 복사 |
| 업무 | `cro` | 랜딩·폼 전환 개선 검토 | `~/.agents/skills/cro/SKILL.md` | Marketing Skills 원본 복사 |
| 업무 | `archify` | 공유할 HTML 구조·흐름 다이어그램 | `~/.agents/skills/archify/SKILL.md` | [Archify](https://github.com/tt-a1i/archify) 원본 복사 |
| 핵심 | `humanizer` | 완성 문서의 반복·부풀린 표현 교정 | `~/.agents/skills/humanizer/SKILL.md` | Agent-setup `shared/skills/core/humanizer` 복사 ([Humanizer](https://github.com/blader/humanizer) v3.1.0 원본 그대로) |
| 핵심 | `shadcn` | shadcn/ui 컴포넌트 추가·검색·구성·스타일 | `~/.agents/skills/shadcn/SKILL.md` | Agent-setup `shared/skills/core/shadcn` 복사 ([shadcn-ui/ui](https://github.com/shadcn-ui/ui) 공식 스킬 원본) |
| 핵심 | `shadcn-lint` | @shadcn/lint 설치·등록·규칙 안내 | `~/.agents/skills/shadcn-lint/SKILL.md` | Agent-setup `shared/skills/core/shadcn-lint` 복사 ([shadcn-ui/lint](https://github.com/shadcn-ui/lint) SETUP.md 기반) |
| 핵심 | `logo-design` | 로고·브랜드 마크 브리프·컨셉·SVG 제작·16px 시험·전달 파일 | `~/.agents/skills/logo-design/SKILL.md` | Agent-setup `shared/skills/core/logo-design` 복사 ([kaankiziltug/logo-design-skill](https://github.com/kaankiziltug/logo-design-skill) @ 0ecf52e, 상표 로고 SVG 묶음 제외) |
| 핵심 | Hermes 작업 교훈 22개·OMH 153개 | 운영 진단·인프라 설계·미디어·검증 교훈과 OMH 계획·검토·운영 워크플로 | `~/.agents/skills/<이름>/SKILL.md` | Agent-setup `shared/skills/core`·`shared/skills/omh`(OMH 최신 정식판 사본, 버전은 `SOURCE.json`) 복사; 목록은 [스킬 표](../docs/skills.md) |
| 업무 | `iterative-retrieval` | 이미 배정한 하위 작업의 부족한 맥락 보완 | `~/.agents/skills/iterative-retrieval/SKILL.md` | [ECC](https://github.com/affaan-m/ECC) 원본 복사 |
| 업무 | `cost-analysis` | 실제 Azure 비용·청구 변화 분석 | `~/.agents/skills/cost-analysis/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `cost-estimation` | 계획 중인 Azure 사용료 추정 | `~/.agents/skills/cost-estimation/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `cost-governance` | Azure 예산·알림·정책 관리 | `~/.agents/skills/cost-governance/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `cost-optimization` | 실행 중인 Azure 리소스 비용 최적화 | `~/.agents/skills/cost-optimization/SKILL.md` | Microsoft 원본 복사 |
| 업무 | `motion-design` | 모션 그래픽·홍보 영상·쇼츠·키네틱 타이포의 연출 설계와 개선 | `~/.agents/skills/motion-design/SKILL.md` | [Open Design](https://github.com/nexu-io/open-design) 원본 복사 |
| 업무 | `hyperframes-animation` | HyperFrames 애니메이션 규칙·장면 청사진·전환·런타임 어댑터 | `~/.agents/skills/hyperframes-animation/SKILL.md` | [HyperFrames](https://github.com/heygen-com/hyperframes) 원본 복사 |
| 도구 | GAM 최신 정식 릴리스 | 결정 검색·검토·승인 저장; 키워드·의미 검색 | `$(uv tool dir)/global-memory-mcp/`; 실행 파일은 `$(uv tool dir --bin)/global-memory-mcp` | [공식 GAM](https://github.com/ozankasikci/global-agent-memory/releases)의 최신 정식 태그 커밋을 `uv tool install`로 설치; Codex MCP 연결 |
| 도구 | CodeGraph 최신 정식 릴리스 | Git 저장소별 구조·호출·변경 영향 탐색 | `~/Library/Application Support/codex-setup/tools/codegraph/node_modules/.bin/codegraph` | [공식 CodeGraph](https://github.com/colbymchenry/codegraph/releases) 최신 정식 태그의 npm 패키지 설치(결정한 태그·커밋은 `tool-releases.json`에 기록); Codex MCP 연결 |
| 도구 | Ollama 최신 안정판 + `nomic-embed-text` | GAM 기억·질문의 벡터 생성 | `$(brew --prefix)/bin/ollama`, `~/.ollama/models/` | [공식 Ollama](https://github.com/ollama/ollama/releases) 안정판을 Homebrew로 설치·서비스 시작·모델 다운로드 |
| 설치 기반 | uv 최신 안정판 | GAM의 공식 도구 설치·업데이트 | `$(brew --prefix)/bin/uv`; GAM 위치는 `uv tool dir`로 조회 | [공식 uv](https://github.com/astral-sh/uv/releases) 확인 후 Homebrew 설치·갱신 |
| 설치 기반 | Node.js 최신 호환 LTS + npm | CodeGraph 설치·실행 | `$(brew --prefix node@24)/bin/node`, `$(brew --prefix node@24)/bin/npm` (현재 호환판 예시) | [Node.js LTS](https://nodejs.org/en/about/previous-releases) 확인 후 Homebrew 설치·갱신 |
| 설치 기반 | Python 최신 호환 안정판·Homebrew | 설정 절차 실행·uv/Node/Ollama 준비 | `$(command -v python3)`, `$(command -v brew)` | [Homebrew 공식 설치 안내](https://brew.sh/)를 확인하고 AI가 누락 항목을 준비 |
| 앱 기능 | Codex 파일·명령·브라우저·컴퓨터·위임 | 작업 종류에 따라 앱에서 선택 | ChatGPT/Codex 앱 내부 | 앱 제공 기능; 별도 CLI 설치 대상 아님 |

핵심 스킬 27개는 Agent-setup `shared/skills/core/`(Claude Code·Codex 공통)에서 사용자 `~/.agents/skills/`에 독립 복사한다. 앱 설치·브라우저 프로필 가져오기 스킬(desktop-app-provisioning)은 `shared/skills/packs/mac/`의 선택 묶음이다. 기존에 설치된 저장소 링크도 백업 후 복사본으로 전환한다. 외부 스킬은 [설치 목록](inventories/external-skills.json)의 각 항목이 적은 원본 저장소·스킬 경로를 따른다. 설치기는 새 설치와 `--refresh` 때 원본별 최신 정식 릴리스 태그와 그 커밋을 조회해 받는다. 원본은 Git LFS 필터를 끈 상태로 받으므로 LFS로 관리하는 미디어는 포인터 파일로 남고, git-lfs가 없는 컴퓨터에서도 설치된다. 정식 릴리스를 내지 않는 원본(현재 MicrosoftDocs/Agent-Skills)은 기본 브랜치의 최신 커밋을 받는다. 미리보기(`--apply` 생략)는 스킬마다 조회한 태그·커밋을 보여준다. 실제 출처·태그·커밋·해시는 `~/Library/Application Support/codex-setup/`의 설치 기록에 대상 스킬 폴더별로 남는다. 이미 설치된 외부 스킬은 `scripts/install_external_skills.py --all --apply --refresh`로 대조한다. 기본 갱신은 설치 당시 원본과 전체 폴더가 일치할 때만 교체한다. 사용자가 기존 스킬까지 최신화를 요청한 경우 AI가 변경 대상과 원본을 검토한 뒤 `--replace-existing`을 추가해 각 폴더를 백업·교체·검증한다. 관련 작업에서만 필요한 스킬을 선택한다.

**GAM·Ollama:** GAM 설치·업데이트 자체는 Ollama를 설치하지 않는다. 이 저장소의 설정 절차가 Ollama와 `nomic-embed-text`를 준비하고 벡터 응답을 확인한다. 기억은 `~/Documents/Global Agent Memory/`에, 설정·검색 DB는 `~/Library/Application Support/global-memory/`에 둔다. 기억은 자동으로 무조건 저장하지 않고 후보 검토와 승인 범위를 따른다.

**CodeGraph:** 설치 시 모든 제품 저장소를 색인하지 않는다. 작업할 Git 저장소에서 필요할 때 색인·동기화하고 `.codegraph/`에 저장한다. 앱에 MCP가 보이고 실제 응답하는지 별도로 확인한다.

앱 배포판의 `openai-docs`, `skill-creator`, `skill-installer`와 문서·PDF·시트·슬라이드·이미지 기능은 앱/플러그인 제공 여부를 확인한다. 이 저장소의 66개 스킬 개수나 복사 설치 대상에 포함하지 않는다. Hermes·OMH CLI·Graft는 설치하지 않는다. OMH 차용 원칙과 출처는 [upstream/README.md](upstream/README.md)에 있다.
