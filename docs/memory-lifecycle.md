# GAM 기억 수명주기

GAM에는 세 실행기가 함께 사용할 프로젝트 결정·검증된 해결 경험을 저장한다. 프로젝트 문서가 현재 계약과 근거의 정본이며, 스킬에는 재사용 절차를 둔다. Hermes OMH 기억은 Hermes 작업 방식의 교훈을 맡는다. 두 저장소와 Hermes의 기존 메모리 설정을 유지한다.

정책 원본은 [`shared/retention/policy.json`](../shared/retention/policy.json), 실행 절차는 [gam-memory](../shared/skills/core/gam-memory/SKILL.md)다. 공통 규칙은 `shared/rules/common.md`에서 각 실행기로 생성한다. 실행기 규칙과 스킬을 설치한 에이전트가 저장·회수 절차를 수행하며, 주간 도구는 수명주기 보고와 승인 범위의 만료 보관을 담당한다.

## 기본 보존값

의미 유형과 보존 클래스는 별도로 기록한다. 모델이 저장하는 지속적 사실은 기본 `fact`·`durable`, CLI·수입 경로는 명시적 `standard`를 사용한다.

| 의미 유형 | GAM 유형 | standard TTL | standard 검토 | durable TTL·검토 | volatile TTL |
|---|---|---|---|---|---|
| fact | fact, preference, reference, entity, project | 없음 | 90일 | 기본값 없음 | 기본 7일, 정수 1~7일 |
| decision | decision | 없음 | 90일 | 기본값 없음 | 같음 |
| lesson | solution | 없음 | 90일 | 기본값 없음 | 같음 |
| procedure | convention | 없음 | 90일 | 기본값 없음 | 같음 |
| episode | session_summary | 30일 | 없음 | 기본값 없음 | 같음 |

- durable에도 명시한 검토 주기는 유지한다. durable은 TTL 입력을 거절한다.
- 검토 임박 창은 14일이다. 만료 임박 창은 `min(14일, max(floor(수명 일수/2), 1일))`이다. 만료 경고를 먼저 표시한다.
- UTC 현재 시각이 만료 시각과 같아지는 순간부터 일반 회수에서 제외한다. 태그의 날짜는 검색용 투영이며 본문의 정확한 시각을 우선한다.
- 미해결 프로젝트 결정은 별도 질문 목록으로 다룬다. 기본 90일 검토·14일 재질문·비durable 365일 상한을 적용한다. durable 미해결 결정은 상한 없이 유지한다. 상한 도달은 검토 사유로 남기고 해결 상태는 근거를 확인해 변경한다.
- 승인·태그 수정·표현 정리는 원래 기한을 유지한다. 클래스 변경은 출처와 변경 사유를 남기고 기한을 다시 계산한다. 기존 미분류 항목은 원래 시각을 유지한 채 분류 검토로 보고한다.

## OMH 규칙 → GAM 동작

출처 표기 `P/`는 OMH 소스의 `plugin_bundle/omh/`, `W/`는 `workflows/`다. 줄 번호는 이 작업에서 조사한 설치 소스를 기준으로 한다. 아래 구현 위치의 `scripts/`는 `shared/skills/core/gam-memory/scripts/`를 가리킨다.

| OMH 규칙 | GAM에서 수행하는 동작·적용 위치 | OMH 근거 |
|---|---|---|
| off/review-first/auto-safe 모드 | 정책 memory_mode와 admission 사전 검사, 스킬 승인 분기 | P/memory_admission.py:116–199 |
| 같은 턴의 사용자 사실 저장 | 다른 도구 호출 전 한 사실씩 요약, 검증 해결책은 근거 확보 뒤 저장; 공통 규칙·스킬 | P/tools/memory_tool.py:200–209 |
| 다섯 의미 유형·세 클래스·요약 제한 | 9개 GAM 유형 매핑, 500자 요약·태그 최대8·출처160자; lifecycle/admission | P/tools/memory_tool.py:183–188,532–547,647–659 |
| 명령형 요약 차단 | 서술형 관찰로 재작성 후 사전 검사·스킬 검토 | P/memory_admission.py:318–349 |
| 범위·구조 메타데이터 검사 | 프로젝트 detect/list 후 등록 이름 사용, 개인·회사 계정 경계 확인; 스킬 | P/memory_admission.py:281–317,374–388 |
| 원문 전체 안전 판정 | 요약·제목·본문·태그·출처·메타데이터를 저장 전에 검사, 비밀·로그·진행 상태 제외; admission·스킬 | P/memory_admission.py:1112–1121,1519–1545; P/_governance_safety.py:760–791 |
| 원문 해시·길이와 제한된 메타데이터 | GAM에는 안전 요약·출처·기한만 전달, 영수증은 ID·버전·해시·사유만 기록; 스킬·보관 도구 | P/memory_admission.py:1163–1194; P/memory_recall_support.py:1594–1643 |
| NFC·소문자·공백 정규화 중복 | 같은 프로젝트의 살아 있는 항목과 정확 비교, force=false; lifecycle.duplicate_key·admission | P/memory_admission.py:435–460,890–919 |
| 중복 skip와 대기 후보 | 정확한 기존 ID를 확인해 생성을 생략, 중복 후보의 승인은 검토로 보류; 스킬 | P/memory_admission.py:447–477,922–972 |
| subject·유사도는 힌트 | 같은 주제의 값 변경과 독립 사실을 근거로 구분, 의미 유사도만으로 폐기하지 않음; 스킬 | P/memory_admission.py:478–491,975–1011 |
| 안전·비중복·비파생·절대 날짜 승인 | 상시 승인을 조건식으로 제한, 불명확하면 대기; 공통 규칙·admission·스킬 | P/memory_admission.py:492–533,573–593 |
| 정확한 리뷰·페이로드 검증 | get 버전 그대로 approve/update/reject에 전달, 승인 뒤 get+범위 검색; 스킬 | P/_governance_evaluation.py:148–214 |
| 유형·클래스별 TTL | durable 없음, standard episode30일, volatile7일/1~7일; 정책·derive | P/memory_governance.py:69–90,125–190 |
| 유형·클래스별 stale | standard 일반90일, episode와 durable 기본 없음, 명시 주기 유지; derive·classify | P/memory_admission.py:1737–1775 |
| 절대 날짜·일수 충돌과 승인 시 기한 유지 | 입력 충돌 거절, 캡처 때 계산한 기한 보존; derive·스킬 | P/memory_admission.py:350–373,1216–1287 |
| 만료·임박·출처 변경 | UTC 등호 만료, 반수명 경고 창, 출처 changed→stale/unreadable→unknown; classify | P/memory_recall_support.py:1432–1495 |
| 미해결 질문의 별도 수명 | 90일 검토·14일 질문·365일 상한, durable 상한 없음, 해결은 근거로 처리; derive·classify·스킬 | P/memory_admission.py:1150–1161,1428–1452; P/memory_recall_support.py:1395–1429 |
| 5턴·종료·복구·압축 검토 | 동일 5턴 기준, 압축 독립 계기; 공통 규칙·consolidation_reasons·스킬 | P/memory_dreaming.py:288–299,339–396; P/memory_provider.py:1254–1270 |
| 여유 공간·중복·만료 계기 | 기본 기억 파일에 비례 여유값, GAM 중복·만료 조건 별도; consolidation_reasons | P/memory_dreaming.py:51–65,397–405 |
| 같은 상시 사유 억제·실제 정리 구분 | last standing reasons와 pending 검토를 별도 기록, 신규 저장은 캡처로 보고; 스킬·사유 계산기 | P/memory_dreaming.py:309–336,406–433; P/memory_provider.py:1621–1636 |
| 압축 시 사용자 제약만 회수 | 정본 결정과 대조하고 새 지속 사실만 저장, 무출처 원래 항목 보존; 스킬 | P/memory_dreaming.py:487–503,547–588 |
| 기본 기억에서 프로젝트 지식 이관 | 240자 이하의 고유한 온전한 항목을 GAM durable 승인·회수 뒤 원본 제거, 사용자 정체성·말투 보존; 스킬 | P/tools/memory_tool.py:877–1009; P/memory_admission.py:1876–1921 |
| retire·보관 | 계획을 먼저 보고하고 만료 대상 재조회 뒤 hard_delete=false, 정확한 보관 상태·활성 검색 제외 검증; gam_retention | W/memory_lifecycle.py:71–107; P/tools/memory_tool.py:1777–1857 |
| 결정 변경의 supersede | 승인된 새 ID와 기존 관측 ID 연결, 양쪽 이력 재조회; 스킬 | P/memory_admission.py:412–424,837–887 |
| 경로 제한·버전·복원 | vault 일치 확인, symlink/경로 탈출 제외, 대상 버전 재검사; 복원은 새 검토 후보로 연결 | W/_memory_lifecycle_scan.py:45–79; W/_memory_lifecycle_plans.py:301–323 |
| 거절 결정의 별도 회수 | 명시 요청 시 project/rejected/decision/태그 부분집합, 기본6/최대20, 일반 문맥과 분리; recall·스킬 | W/rejected_decision_recall.py:25–40,49–82,120–166 |
| 거절 기억도 안전·수명 검사 | 리뷰 근거·안전·TTL·stale·대체 확인, include_stale는 정보값으로 취급; recall·스킬 | W/rejected_decision_recall.py:54–117 |
| 적격성 검사 뒤 랭킹·최신 subject | 일반 회수에서 비활성·오래된 출처·만료 제외, 최신 값이 만료돼도 이전 값을 부활시키지 않음; recall | P/_governance_evaluation.py:148–319; P/memory_recall_selector.py:580–633 |
| 쿼리 커버리지·BM25F | GAM 검색 후보를 적격성 검사 후 사용, 현재 순위는 native_approximate로 명시; 스킬·정책 | P/memory_recall_support.py:55–82,930–1035 |
| RRF·사용량·핀·예산 | token_budget 명시, 검증 후보의 제한된 접두 문맥 구성, 실제 전달 이력만 사용; 스킬 | P/memory_recall_support.py:29–53,181–289,412–426; P/memory_recall_selector.py:752–805 |
| attention·이미 전달한 revision | reference는 쿼리 확인, archive는 명시 조회, ID+버전 중복 전달 억제; attention 메타데이터와 실행 세션 기록 | P/memory_recall_selector.py:690–751 |

## 도구 사용

```sh
# 보존 계획만 조회
python3 scripts/retention.py
# 현재 승인 범위의 캐시 정리와 GAM 만료 보관
python3 scripts/retention.py apply
# 인자 확인
python3 scripts/retention.py --help
```

GAM 실행 Python은 로컬 `retention.json`의 `gam_python`을 먼저 사용하고, `uv tool dir`의 공식 설치 환경, 기존 Codex 설치 기록 순서로 찾는다. 세 실행기 모두 같은 adapter를 사용한다. macOS의 설정 위치는 `~/Library/Application Support/agent-setup/retention.json`, 다른 플랫폼은 `~/.local/state/agent-setup/retention.json`이다. `gam_command`, `gam_config`, `gam_vault`, `gam_state`로 대상을 명시할 수 있다. 도구는 GAM 설치 환경의 MCP·PyYAML을 사용한다. 실제 기억은 GAM API로 보관한다.

GAM만 확인하려면 설치된 GAM Python으로 다음을 실행한다.

```sh
<GAM Python> shared/skills/core/gam-memory/scripts/gam_retention.py \
  --policy shared/retention/policy.json --config <GAM 설정> --vault <Vault>
```

출력 rows에는 정확한 ID·버전·수명주기 상태·사유·archive_eligible가 나온다. apply 영수증은 대상별 archived/skipped/failed를 남긴다. 중요 태그·높은 중요도·decision/preference/convention 보호는 로컬 보관 안전장치로 유지한다. 보호된 만료 항목도 일반 회수에서 제외하고 보고한다. 미분류 기존 항목은 분류 검토로 표시하고, 기존 temporary+expires 태그는 호환 보관 경로로 처리한다. Codex의 예전 `expired_memory`·`stale_memory` 함수는 기존 호출자용 호환 판정이며 실제 유지관리 실행은 공통 정책·adapter를 사용한다.

## 확인된 적용 범위와 남은 통합

- **구현·단위 검증:** 타입/클래스 기한 계산, 만료·검토·임박·미해결 분류, 프로젝트·상태·출처·최신 subject 회수 게이트, 안전 사전 검사, 검토 사유 계산, 보고 우선 스캔, 허용된 만료 보관과 재조회 절차. 출처의 실제 읽기·변경 확인과 의미적 안전 판정은 에이전트가 담당한다.
- **에이전트 절차:** 같은 턴 저장, 후보 승인, 프로젝트 등록/이름 변경, 수정 이력, 거절 결정, 기본 기억 이관, 검토 상태 기록. 각 실행기의 스킬을 읽은 에이전트가 적용한다.
- **호스트 이벤트 통합 공백:** Hermes·Claude Code·Codex의 턴/종료/압축 이벤트 훅과 영속 카운터의 자동 연결은 미검증이다. 현재는 에이전트 체크포인트로 수행한다.
- **랭킹·안전 분류기 동등성 공백:** GAM native 검색 순위와 portable 안전 검사는 각각 근사·보조 검사다. OMH 전체 코퍼스 scorer, 토크나이저, 사용량/RRF/attention, classifier/v3의 완전한 이식과 fixture 검증은 남아 있다.
- **백엔드 트랜잭션 공백:** approve/update/reject는 반환 버전으로 낙관적 충돌을 검사한다. archive/supersede에는 exact-old-version CAS 인자가 없어 재조회 후 변경 사이의 경쟁이 남는다. 원자적 check+capture+approve, 불변 review/digest 검증, tombstone·복원 트랜잭션은 GAM 백엔드 지원이 필요하다.
- **운영 적용:** 이 저장소 검사와 사본 일치는 로컬 구현 증거다. 사용자 홈 설치, 실제 GAM 쓰기, 주간 스케줄 실행, 세 실행기의 실제 세션 관측은 별도로 확인한다.

## 출처

- [OMH 저장소](https://github.com/rlaope/oh-my-hermes): 위 표의 admission/governance/dreaming/provider/recall/lifecycle 모듈. 설치·갱신은 최신 정식 릴리스를 따라가며, 변경 시 이 표와 테스트를 함께 대조한다.
- [GAM 저장소](https://github.com/ozankasikci/global-agent-memory): 프로젝트·candidate/approve/reject/supersede/archive·검색 API. 이 작업에서는 실제 노출된 MCP 스키마와 설치 패키지의 응답 구조를 확인했다.
- [공통 규칙](../shared/rules/common.md), [정책](../shared/retention/policy.json), [공통 스킬](../shared/skills/core/gam-memory/SKILL.md), [테스트](../tests/test_retention.py).
