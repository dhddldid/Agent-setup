# 설치 목록

`H`는 `${HERMES_HOME:-$HOME/.hermes}`다. 기본은 `~/.hermes/`, 이름 있는 프로필은 `~/.hermes/profiles/<이름>/`이다. `$(brew --prefix)`는 설치 대상인 Apple Silicon에서 보통 `/opt/homebrew`다. npm·uv·Go 실행 파일 위치는 각 관리자의 설정을 따른다.

비-OMH 스킬 92개를 기준으로 한다. 공식 원본 57개, Agent-setup 공통 스킬 34개, Hermes 전용 보조 스킬 1개(dag-ulw-notes)다. 공통 스킬은 도구·기준 12개(desktop-app-provisioning, gam-memory, codegraph-context, aside-browser, coding-code-review, coding-maintenance, agent-setup-maintenance, humanize-korean, humanizer, shadcn, shadcn-lint, logo-design)와 Hermes 작업 교훈 공개본 22개다. 공통 스킬은 `skills/`에 Agent-setup `shared/skills/`와 같은 내용으로 둔다. 스킬 문서는 설치하지만 CLI·라이브러리·서비스 권한은 해당 작업을 사용할 때 준비한다. 공식 스킬은 설치 시점에 조회한 Hermes 최신 정식 태그의 공식 원본을 설치한다. OMH 스킬은 OMH 설치기로 별도 관리한다.

| 종류 | 항목 | 용도 | 설치 기준·추가 준비 | 일반 설치 경로 | 추가 도구·설정 경로 |
|---|---|---|---|---|---|
| 앱·CLI | Hermes | 주 작업 에이전트 | 필수; 공식 Desktop/CLI 설치 | `H/` | Desktop 앱은 `/Applications/`; 소스 방식 checkout은 `H/hermes-agent/` |
| Desktop 설정 | UI 크기 맞춤 | 기존 ChatGPT·Claude 앱의 창·글자·UI 크기 반영 | 기존 앱이 있으면 확인·적용·화면 비교; 두 앱이 다르면 기준 확인 | Hermes Desktop 창·Appearance 설정 | [적용 기준](docs/desktop-ui.md); 기존 앱·포커스 보존 |
| 앱 | Aside | 로그인 브라우저 작업·프로필 가져오기 | 필수; 공식 앱·CLI·자신의 로그인 | `/Applications/Aside.app` | CLI는 공식 설치기 경로 확인; macOS 프로필은 `~/Library/Application Support/Aside/` |
| MCP 연결 | Aside 연결 장치 | 프로필별 `repl` 도구 하나, 안 쓰는 연결 15분 뒤 자동 종료 | 필수; `scripts/install_aside_bridge.py --apply` | `H/integrations/aside-browser/` | 원본 `integrations/aside-browser/`; `mcp_servers.aside`에 등록 |
| 앱 | Chrome·Edge·Safari | 기존 로그인 브라우저 활용 | 사용하는 브라우저만; 프로필 가져오기는 지원 여부 확인 | `/Applications/` | `~/Library/Application Support/Google/Chrome/`, `~/Library/Application Support/Microsoft Edge/`, Safari는 OS 관리 |
| 확장·스킬팩 | OMH | 작업 분류·라우팅·검증 지침 | 필수; 공식 install·setup | `~/.omh/`; `~/.local/share/omh/` | Hermes 등록 `H/plugins/omh/`; 스킬 실제 경로는 `skills.external_dirs` 확인 |
| 업데이트 스크립트 | update.sh | Hermes·OMH·provider-usage·외부 스킬을 실행 시점의 최신 정식 릴리스로 올리고 사용자 지정을 다시 맞춤 | 업데이트할 때 Agent-setup 루트에서 `bash hermes/scripts/update.sh`; Hermes Desktop 업데이트 버튼 대신 사용 | Agent-setup 체크아웃 | `scripts/update.sh`, `scripts/update_helpers.py`; [업데이트](docs/model-routing.md#업데이트) |
| OMH 사용자 설정 | 한국어 트리거 팩 | "메일 가져오기, 파일 업로드, 검색 기능 개발해줘"처럼 여러 부분을 만드는 한국어 일상 요청을 `dag-ulw` 등 OMH 흐름에 연결하고, 작은 요청은 흐름 없이 바로 처리 | 필수; `scripts/install_omh_trigger_pack.py --apply`, 확인은 `--check`; 회귀 측정은 `omh/trigger-packs/evaluate.py` | `~/.omh/routing/trigger-packs/ko.json` | 원본 `omh/trigger-packs/ko.json`; 실제 요청 회귀 문장 `omh/trigger-packs/ko-corpus.json`; `update.sh`가 설치 직후 라우팅 점검 실행 |
| Hermes 본체 수정 | 수정 묶음 | 계정 선택·사용량 표시·모델별 계정 쿨다운·턴 복구 | 필수; 최신 정식 릴리스 위에 `scripts/apply_local_patches.py --apply` | `H/hermes-agent/` 작업 트리 | 원본 `patches/hermes-agent/<태그>.patch`; 새 태그용 패치가 없으면 업데이트 전에 이전 |
| 런타임 호환 패치 | 자식 fallback 순서·추론 | GPT 시작 자식의 Opus 마지막 순서와 작업별 추론 유지 | `scripts/update.sh`가 업데이트마다 다시 적용; 따로 적용할 때는 미리보기·적용·새 프로세스 검증 | 실제 소스의 `agent/chat_completion_helpers.py`, `tools/delegate_tool_config.py` | `scripts/configure_delegation_reasoning.py`, `scripts/configure_gpt_fallback.py`; [적용 기준](docs/model-routing.md) |
| Hermes 플러그인 | provider-usage | GPT·Claude 사용량·잔여 한도·리셋 시간 | 필수; 최신 정식 릴리스 태그로 설치·활성화·[GPT·Claude만 표시](docs/provider-usage.md)·실제 조회. `scripts/update.sh`가 업데이트마다 최신 정식 태그로 올림 | `H/plugins/provider-usage/` | Desktop UI `H/desktop-plugins/provider-usage/`; 표시 어댑터 `scripts/configure_provider_usage.py`; 인증은 사용자의 로컬 저장소; 수정 묶음 `patches/provider-usage/<태그>.patch`; 새 태그용 패치가 없으면 업데이트 전에 이전 |
| Hermes 플러그인 | web-codex-search | 메인 모델이 Claude여도 웹 검색을 로그인한 GPT(openai-codex) 계정의 서버 검색으로 처리 | 필수(메인 모델이 GPT 외일 때); 복사 후 `plugins.enabled`에 추가, `hermes config set web.search_backend codex-search` | `H/plugins/web-codex-search/` | 원본 `plugins/web-codex-search/` (이 저장소 제작) |
| Hermes 플러그인 | discord-project-sidebar | Discord 세션을 Desktop 프로젝트 아래에 표시 | 선택; Discord 사용 시 [연동 안내](docs/discord.md) | `H/plugins/discord-project-sidebar/` | 원본 `discord/plugins/`; 프로젝트 지도는 `discord.channel_prompts` |
| Hermes 플러그인 | desktop-discord-reports | Desktop 작업 결과를 프로젝트 채널 스레드로 보고 | 선택; Discord 사용 시 | `H/plugins/desktop-discord-reports/` | 원본 `discord/plugins/`; 스레드 대응 `H/state/desktop-discord-threads.json` |
| 예약 스크립트 | discord-project-hygiene | 3일 경과 스레드·Desktop 채팅 삭제(그룹별 최근 3개 유지) | 선택; Discord 사용 시 no-agent cron | `H/scripts/discord-project-hygiene.py` | 원본 `discord/scripts/`; 봇 스레드 관리 권한 |
| 예약 스크립트 | parallel-gap-check | 3일마다 대화 기록에서 한 작업만 맡긴 위임과 `dag-ulw`를 불러오지 않은 위임 세션을 찾고, 한국어 요청 라우팅을 다시 점검해 발견한 내용만 알림(LLM 호출 비용 0) | 필수; `scripts/install_parallel_gap_check.py --apply --deliver <대화 정리 작업과 같은 Discord 채널>`, 옵션 없이 실행하면 미리보기; no-agent cron `every 72h`, 등록 확인은 `hermes cron list` | `H/scripts/parallel-gap-check.py` | 점검기 Agent-setup `scripts/check_parallel_gaps.py`(직접 실행은 `history --days 3`, `routing`); 보고서 `H/reports/parallel-gaps/`; 등록 뒤 저장소 위치 유지 |
| Hermes UI 확장 | OMH Desktop·TUI | 상태·작업 표시 | OMH setup에서 선택한 UI 연결 | `H/desktop-plugins/omh/`; `H/tui-widgets/omh-status.mjs` | 설치 여부·표시는 별도 확인 |
| 프로젝트 지침 | AGENTS.md | 저장소 작업 규칙 | Agent-setup 루트와 Hermes 폴더 지침 | `Agent-setup/AGENTS.md`, `Agent-setup/hermes/AGENTS.md` | 다른 프로젝트는 각 프로젝트 루트 |
| 전역 규칙 | 공통 작업 원칙, OMH 워크플로 사용, Aside 브라우저 직접 조작, 문서 전달 | 작업 원칙·표현·프로젝트 지침·CodeGraph·여러 부분 작업은 첫 위임 전에 나누고 준비된 부분을 한 번에 위임; 작업 형태로 OMH 흐름 선택·여러 부분 작업은 Route Hint 없이 `dag-ulw`·`dag-ulw-notes` 로드·그 안에서 개인 스킬 사용·위임 전 OMH 라우팅; Aside `repl` 직접 조작; 문서 전달 시 폴더 카드 제공·앱 자동 실행 금지 | `scripts/install_global_rules.py --apply`로 추가·이전 배포본 교체; 직접 고친 구간은 보존하고 차이를 `H/.agent-setup/diffs/`에 남김 | `H/SOUL.md` | 원본 `templates/common-rules.md`(Agent-setup `shared/rules/`에서 생성), `templates/omh-workflow.md`, `templates/aside-browser.md`, `templates/document-delivery.md`; 브라우저 프로필은 프로젝트 규칙 |
| 스킬 | apple-notes | Apple 메모 읽기·검색·작성 | 공식 원본; memo; macOS Automation 승인 | `H/skills/apple/apple-notes/` | `$(brew --prefix)/bin/memo` |
| 스킬 | apple-reminders | Apple 미리 알림 관리 | 공식 원본; remindctl; 미리 알림 승인 | `H/skills/apple/apple-reminders/` | `$(brew --prefix)/bin/remindctl` |
| 스킬 | findmy | 나의 찾기 기기·AirTag 확인 | 공식 원본; 나의 찾기·iCloud; 화면 권한 | `H/skills/apple/findmy/` | macOS 기본 앱 |
| 스킬 | imessage | iMessage·SMS 조회·전송 | 공식 원본; imsg; Messages 로그인·권한 | `H/skills/apple/imessage/` | `$(brew --prefix)/bin/imsg` |
| 스킬 | claude-code | 외부 Claude Code에 코딩 위임 | 공식 원본; Claude Code CLI·로그인 | `H/skills/autonomous-ai-agents/claude-code/` | npm 전역 bin; `~/.claude/` |
| 스킬 | codex | 외부 Codex CLI에 코딩 위임 | 공식 원본; Codex CLI·로그인 | `H/skills/autonomous-ai-agents/codex/` | npm 전역 bin; `~/.codex/` |
| 스킬 | computer-use | 네이티브 앱 화면·입력 제어 | 공식 원본; cua-driver; 접근성·화면 권한 | `H/skills/autonomous-ai-agents/computer-use/` | `H/tools/` (Hermes 관리) |
| 스킬 | hermes-agent | Hermes 사용·설정·문제 해결 | 공식 원본; Hermes CLI | `H/skills/autonomous-ai-agents/hermes-agent/` | Hermes 설치 방식에 따름 |
| 스킬 | opencode | 외부 OpenCode에 코딩 위임 | 공식 원본; OpenCode CLI·로그인 | `H/skills/autonomous-ai-agents/opencode/` | npm 전역 bin 또는 `$(brew --prefix)/bin/` |
| 스킬 | architecture-diagram | 아키텍처 다이어그램 작성 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/creative/architecture-diagram/` | — |
| 스킬 | ascii-video | 영상·오디오를 ASCII 영상으로 변환 | 공식 원본; Python·NumPy·Pillow·ffmpeg | `H/skills/creative/ascii-video/` | 프로젝트 `.venv/`; `$(brew --prefix)/bin/ffmpeg` |
| 스킬 | baoyu-infographic | 정보를 인포그래픽으로 구성 | 공식 원본; 이미지 생성 도구는 사용할 때 연결 | `H/skills/creative/baoyu-infographic/` | Hermes 제공자 설정 |
| 스킬 | claude-design | 일회성 HTML 화면·발표·프로토타입 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/creative/claude-design/` | — |
| 스킬 | design-md | DESIGN.md 디자인 토큰 작성·검사 | 공식 원본; Node; `@google/design.md`를 npx로 실행 | `H/skills/creative/design-md/` | `~/.npm/_npx/` |
| 스킬 | manim-video | Manim 수학·알고리즘 영상 | 공식 원본; Manim·LaTeX·ffmpeg | `H/skills/creative/manim-video/` | 프로젝트 `.venv/`; `/Library/TeX/`; Homebrew bin |
| 스킬 | p5js | p5.js 생성형 그래픽·인터랙션 | 공식 원본; 브라우저·p5.js; 영상 출력은 Node·ffmpeg | `H/skills/creative/p5js/` | 프로젝트 HTML·`node_modules/` |
| 스킬 | popular-web-designs | 실제 디자인 시스템 참고 화면 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/creative/popular-web-designs/` | — |
| 스킬 | songwriting-and-ai-music | 작사·작곡 방향·음악 생성 요청 | 공식 원본; 음악 생성 서비스는 선택 | `H/skills/creative/songwriting-and-ai-music/` | 서비스 계정; 별도 로컬 도구 없음 |
| 스킬 | dag-ulw-notes | 여러 부분 작업을 첫 위임 전에 나누고 준비된 부분을 한 번에 시작하는 `dag-ulw` 보조 규칙, `omh_dag` 정의 형식 | Hermes 전용 로컬 스킬; `scripts/install_skills.py`로 설치, 미리보기로 확인; `dag-ulw`(OMH)와 함께 로드 | `H/skills/ultrawork/dag-ulw-notes/` | 원본 `skills/dag-ulw-notes/` |
| 스킬 | desktop-app-provisioning | 앱 설치·브라우저 프로필 이전 | 일반화한 커스텀; macOS 설치·GUI 도구·OS 승인 | `H/skills/desktop-app-provisioning/` | `/Applications/`; `H/tools/` |
| 스킬 | gam-memory | 과거 결정 회수·승인된 지식 저장 | Agent-setup 공통 스킬; GAM MCP 연결 필요 | `H/skills/gam-memory/` | GAM 공식 설치 경로; 기억 원본은 GAM Vault |
| 스킬 | codegraph-context | CodeGraph로 코드 위치·호출 관계 좁히기 | Agent-setup 공통 스킬; CodeGraph MCP 연결 (Agent-setup 공통 도구) | `H/skills/codegraph-context/` | CodeGraph 공식 설치 경로; 색인은 각 Git 저장소 `.codegraph/` |
| 스킬 | aside-browser | Aside를 repl로 직접 조작하는 절차 | Agent-setup 공통 스킬; Aside 앱·CLI (공통 도구) | `H/skills/aside-browser/` | `/Applications/Aside.app`; CLI는 공식 설치 경로 |
| 스킬 | coding-code-review | 변경 코드 결함과 파일·모듈 목적별 구조 점검 | Agent-setup 공통 스킬 | `H/skills/coding-code-review/` | Agent-setup `shared/skills/core/coding-code-review` |
| 스킬 | coding-maintenance | 기억·기록의 보존 정책과 승인된 정리 | Agent-setup 공통 스킬; GAM 연결 시 사용 | `H/skills/coding-maintenance/` | Agent-setup `codex/config/retention.json` 정책 |
| 스킬 | agent-setup-maintenance | AI 작업 환경(지침·스킬·도구) 변경 절차 | Agent-setup 공통 스킬; Agent-setup 체크아웃 | `H/skills/agent-setup-maintenance/` | Agent-setup 저장소 |
| 스킬 | humanize-korean | 한국어 번역투·상투 표현 교정 | Agent-setup 공통 스킬; 별도 설치 없음 | `H/skills/humanize-korean/` | — |
| 스킬 | humanizer | 영문 AI 투 표현 교정 | Agent-setup 공통 스킬; 별도 설치 없음 (blader/humanizer v3.1.0 원본) | `H/skills/humanizer/` | — |
| 스킬 | sdlc-review | Kanban 작업 결과 검토 | 공식 원본; Hermes Kanban worker 작업 | `H/skills/devops/sdlc-review/` | Hermes 기능; 별도 CLI 없음 |
| 스킬 | email-inbox-triage | 메일 우선순위·답장 초안 | 공식 원본; 연결된 메일 도구·계정 | `H/skills/email/email-inbox-triage/` | 선택한 메일 도구 설정 |
| 스킬 | himalaya | IMAP·SMTP 메일 CLI 작업 | 공식 원본; himalaya·IMAP/SMTP 로그인 | `H/skills/email/himalaya/` | `$(brew --prefix)/bin/himalaya`; `~/.config/himalaya/` |
| 스킬 | gif-search | Tenor GIF 검색·다운로드 | 공식 원본; curl·jq·Tenor API key | `H/skills/media/gif-search/` | `$(brew --prefix)/bin/jq`; key는 `H/.env` |
| 스킬 | songsee | 오디오 스펙트럼 분석 | 공식 원본; Go·songsee; ffmpeg 선택 | `H/skills/media/songsee/` | `$(go env GOPATH)/bin/songsee` |
| 스킬 | youtube-content | YouTube 자막을 요약·콘텐츠로 변환 | 공식 원본; youtube-transcript-api; Hermes PM extra | `H/skills/media/youtube-content/` | Hermes PM 관리 환경 또는 격리 helper `.venv/` |
| 스킬 | obsidian | Obsidian vault 노트 작업 | 공식 원본; Obsidian 앱·본인 vault | `H/skills/note-taking/obsidian/` | `/Applications/Obsidian.app`; 선택한 vault |
| 스킬 | airtable | Airtable 레코드 조회·수정 | 공식 원본; curl·Airtable PAT | `H/skills/productivity/airtable/` | macOS curl; PAT는 `H/.env` |
| 스킬 | box | Box 파일·권한·메타데이터 관리 | 공식 원본; Box CLI·OAuth | `H/skills/productivity/box/` | `H/tools/box-cli/` |
| 스킬 | document-to-action-items | 문서에서 의무·기한·할 일 추출 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/productivity/document-to-action-items/` | — |
| 스킬 | docx | Word 문서 작성·편집 | 공식 원본; python-docx | `H/skills/productivity/docx/` | 프로젝트 `.venv/` |
| 스킬 | google-workspace | Gmail·Calendar·Drive·Docs·Sheets | 공식 원본; Google OAuth·Hermes Google extra; gws 선택 | `H/skills/productivity/google-workspace/` | Hermes 관리 환경; 토큰은 `H/` |
| 스킬 | maps | 위치·경로·시간대 조회 | 공식 원본; Python 표준 라이브러리·네트워크 | `H/skills/productivity/maps/` | 추가 패키지 없음 |
| 스킬 | meeting-action-items | 회의에서 결정·담당·할 일 추출 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/productivity/meeting-action-items/` | — |
| 스킬 | notion | Notion 페이지·DB 작업 | 공식 원본; Notion token; ntn 선택 | `H/skills/productivity/notion/` | npm 전역 bin; token은 `H/.env` |
| 스킬 | pdf | PDF 읽기·작성·병합·OCR | 공식 원본; pypdf·reportlab·pdfplumber; 렌더링/OCR 도구 선택 | `H/skills/productivity/pdf/` | 프로젝트 `.venv/`; Poppler·OCR은 Homebrew |
| 스킬 | powerpoint | PowerPoint 작성·편집·렌더링 | 공식 원본; python-pptx; 렌더링은 LibreOffice·Poppler | `H/skills/productivity/powerpoint/` | 프로젝트 `.venv/`; `/Applications/LibreOffice.app`; Homebrew |
| 스킬 | product-price-monitor | 상품·항공권·매물 가격 감시 | 공식 원본; 검색/브라우저·예약 기능 | `H/skills/productivity/product-price-monitor/` | Hermes cron·브라우저 설정 |
| 스킬 | teams-meeting-pipeline | Teams 회의 자막·요약 파이프라인 | 공식 원본; Hermes Teams pipeline·Graph 권한 | `H/skills/productivity/teams-meeting-pipeline/` | Hermes plugin; 설정은 `H/.env` |
| 스킬 | weekly-review-planning | 주간 회고·다음 주 계획 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/productivity/weekly-review-planning/` | — |
| 스킬 | xlsx | Excel·CSV 작성·분석 | 공식 원본; openpyxl; 재계산은 LibreOffice 선택 | `H/skills/productivity/xlsx/` | 프로젝트 `.venv/`; `/Applications/LibreOffice.app` |
| 스킬 | arxiv | arXiv 논문 검색·조회 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/research/arxiv/` | — |
| 스킬 | competitor-news-monitor | 경쟁사 뉴스 감시·근거 정리 | 공식 원본; 검색·예약 기능 | `H/skills/research/competitor-news-monitor/` | Hermes 제공자·cron 설정 |
| 스킬 | grounded-citations | 검증 가능한 인용·출처 관리 | 공식 원본; Python 표준 라이브러리·검색 도구 | `H/skills/research/grounded-citations/` | 추가 패키지 없음 |
| 스킬 | llm-wiki | Markdown 지식 위키 구축 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/research/llm-wiki/` | — |
| 스킬 | xurl | X 검색·게시·메시지 CLI | 공식 원본; xurl·X OAuth | `H/skills/social-media/xurl/` | `~/.local/bin/` 또는 패키지 관리자 bin |
| 스킬 | codebase-inspection | 언어·코드량·구성 조사 | 공식 원본; pygount | `H/skills/software-development/codebase-inspection/` | uv tool 환경·bin 또는 프로젝트 `.venv/` |
| 스킬 | dogfood | 웹 앱 탐색 QA·오류 증거 | 공식 원본; 브라우저 도구·검사 URL | `H/skills/software-development/dogfood/` | Hermes 브라우저 설정 |
| 스킬 | github | GitHub 저장소·PR·이슈 작업 | 공식 원본; gh·GitHub 로그인 | `H/skills/software-development/github/` | `$(brew --prefix)/bin/gh`; `~/.config/gh/` |
| 스킬 | hermes-agent-skill-authoring | Hermes 스킬 작성·검증 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/software-development/hermes-agent-skill-authoring/` | — |
| 스킬 | inspecting-hermes-desktop-dom | Hermes Desktop DOM·CSS 검사 | 공식 원본; Hermes Desktop 개발용 CDP | `H/skills/software-development/inspecting-hermes-desktop-dom/` | Hermes 개발 checkout; 기본 사용자 설치에 필수 아님 |
| 스킬 | node-inspect-debugger | Node.js 디버깅 | 공식 원본; Node; CDP 라이브러리 선택 | `H/skills/software-development/node-inspect-debugger/` | Node bin; 프로젝트 `node_modules/` |
| 스킬 | python-debugpy | Python pdb·debugpy 디버깅 | 공식 원본; Python; 원격 디버깅은 debugpy | `H/skills/software-development/python-debugpy/` | 대상 프로젝트 개발 `.venv/` |
| 스킬 | requesting-code-review | 변경 검토·품질 검사 | 공식 원본; Git·프로젝트 검사 도구·위임 | `H/skills/software-development/requesting-code-review/` | 프로젝트 의존 도구; Hermes delegation |
| 스킬 | simplify-code | 최근 코드 변경 정리 | 공식 원본; Git·프로젝트 검사·위임 | `H/skills/software-development/simplify-code/` | 프로젝트 의존 도구; Hermes delegation |
| 스킬 | spike | 짧은 실험으로 가정 검증 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/software-development/spike/` | — |
| 스킬 | systematic-debugging | 재현·원인 확인 후 수정 | 공식 원본; 프로젝트의 테스트·진단 도구 | `H/skills/software-development/systematic-debugging/` | 대상 프로젝트 환경 |
| 스킬 | test-driven-development | 실패 테스트부터 구현 | 공식 원본; 별도 설치 없음; 작업에 맞는 기본 도구 | `H/skills/software-development/test-driven-development/` | — |
| 스킬 | blocked-page-recovery | 차단·로그인 벽 페이지 접근 복구 | 공식 원본; 허용된 브라우저/검색 경로 | `H/skills/web/blocked-page-recovery/` | Hermes 브라우저·제공자 설정 |
| 스킬 | shadcn | shadcn/ui 컴포넌트 추가·검색·구성·스타일 (공식 스킬) | Agent-setup 공통 스킬; Node.js; 프로젝트 패키지 실행기(npx 등) | `H/skills/shadcn/` | shadcn-ui/ui 공식 스킬 원본 |
| 스킬 | shadcn-lint | @shadcn/lint 설치·등록·규칙 안내 | Agent-setup 공통 스킬; Node.js; 대상 프로젝트의 ESLint/Oxlint | `H/skills/shadcn-lint/` | shadcn-ui/lint SETUP.md 기반 |
| 스킬 | logo-design | 로고·브랜드 마크 브리프·컨셉·SVG 제작·16px 시험·전달 파일 | Agent-setup 공통 스킬; Python 3 표준 라이브러리; PNG 렌더링은 cairosvg·rsvg-convert·Inkscape·Chrome·Quick Look 중 하나 | `H/skills/logo-design/` | kaankiziltug/logo-design-skill @ 0ecf52e (상표 로고 SVG 묶음 제외) |
| 스킬 | bounded-resource-usage-ledgers | 실행 단위 자원 사용 기록에 상한 두기 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/bounded-resource-usage-ledgers/` | — |
| 스킬 | durable-sqlite-test-ledger | 중단에도 안전한 SQLite 시험 기록 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/durable-sqlite-test-ledger/` | — |
| 스킬 | isolated-read-batch-fences | 가변 상태가 있는 읽기 도구 병렬화 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/isolated-read-batch-fences/` | — |
| 스킬 | saved-source-contention-fences | 저장 원본 경합 재시도 보호 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/saved-source-contention-fences/` | — |
| 스킬 | read-model-performance-safety | 느린 읽기 모델 개선 시 접근 검사 유지 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/read-model-performance-safety/` | — |
| 스킬 | semantic-knowledge-lifecycle | LLM 기억·지식 보존 범위 설계 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/semantic-knowledge-lifecycle/` | — |
| 스킬 | production-failure-diagnosis | 저장된 운영 실패의 원인 추적 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/production-failure-diagnosis/` | — |
| 스킬 | production-admin-api-operations | 운영 관리 API 일괄 작업 작성 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/production-admin-api-operations/` | — |
| 스킬 | product-monetization-requirements | 유료 이용·광고 제거·갱신 요구 정의 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/product-monetization-requirements/` | — |
| 스킬 | service-infrastructure-design | 서비스 인프라 재설계 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/service-infrastructure-design/` | — |
| 스킬 | setup-repository-authoring | 재현 가능한 환경 설정 저장소 작성 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/setup-repository-authoring/` | — |
| 스킬 | mobile-app-portfolio-delivery | 여러 모바일 앱을 베타까지 진행 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/mobile-app-portfolio-delivery/` | — |
| 스킬 | media-production-orchestration | 생성 미디어 일괄 제작 조율 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/media-production-orchestration/` | — |
| 스킬 | blog-motion-preview-pillow-ffmpeg | 블로그용 짧은 GIF/MP4 만들기 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/blog-motion-preview-pillow-ffmpeg/` | — |
| 스킬 | android-device-validation | Android 기기 설치·동작 확인 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/android-device-validation/` | — |
| 스킬 | atomic-firewall-bootstrap-tests | 방화벽 부트스트랩 스크립트 오프라인 수정 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/atomic-firewall-bootstrap-tests/` | — |
| 스킬 | backend-independent-rereview | 수정된 Python 백엔드를 실제 요청으로 재검토 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/backend-independent-rereview/` | — |
| 스킬 | bounded-private-evidence-reads | 비공개 근거 읽기·업로드 감사 범위 제한 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/bounded-private-evidence-reads/` | — |
| 스킬 | bounded-subprocess-pipe-io | Popen 파이프 입출력에 기한 적용 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/bounded-subprocess-pipe-io/` | — |
| 스킬 | clock-fenced-offline-integration | 시각 기준 오프라인 통합 확인 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/clock-fenced-offline-integration/` | — |
| 스킬 | future-effective-memory-tdd | 미래 시점 적용 기억 갱신을 TDD로 수정 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/future-effective-memory-tdd/` | — |
| 스킬 | project-reference-adoption | 참고 링크의 프로젝트 도입 검토 | Agent-setup 공통 스킬(Hermes 작업 교훈 공개본) | `H/skills/project-reference-adoption/` | — |
| 외부 스킬 | Azure·Entra 26, Azure 비용 4, 마케팅 5, 모션 디자인 2(motion-design·hyperframes-animation), archify, iterative-retrieval (39개) | Codex·Claude Code와 같은 업무 스킬 | Agent-setup 외부 목록 `codex/inventories/external-skills.json`의 원본(설치 시점에 조회한 원본별 최신 정식 릴리스 태그의 커밋); 설명 조정 `codex/config/skill-descriptions.json` | `H/skills/<스킬명>/` | 설치 기록은 Agent-setup 상태 경로의 별도 잠금 파일 |

출처와 설치 기준은 [manifest.json](manifest.json), 실행 방법은 [설치 안내](INSTALL_FOR_AGENTS.md)에 있다. Hermes 기본 내장 플러그인을 전부 복제하지 않는다.
