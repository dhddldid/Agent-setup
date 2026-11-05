---
name: gam-memory
description: 프로젝트 지식을 GAM에 저장하고 OMH 수명주기를 적용한다.
---

# 프로젝트 장기기억

선택된 OMH 워크플로 안에서 이 절차를 사용한다. GAM은 Hermes·Claude Code·Codex가 공유하는 프로젝트 지식을 맡는다. 현재 계약·상태와 근거는 프로젝트 docs, 재사용 절차는 스킬, Hermes 작업 교훈은 Hermes OMH 기억에 둔다. 두 저장소와 기존 설정을 유지한다. 상세 표와 출처는 [기억 수명주기 안내](../../../../memory-lifecycle.md), AI 실행 원문은 `shared/skills/core/gam-memory/SKILL.md`를 따른다.

## 프로젝트 확인과 회수

1. 절대 경로를 `memory_projects(action="detect", payload={working_directory})`로 전달한다. null이면 list로 기존 roots를 확인하고, 새 프로젝트만 add(request_id, payload={name, roots:[git_root]})한다. project에는 등록 이름·ID, working_directory에는 경로를 넣는다.
2. 프로젝트 이름·폴더 변경은 같은 ID에 update(request_id, payload={id, changes:{name, roots, aliases:[old_name]}})한다. registry와 새 경로 detect로 확인한다. roots·aliases는 changes 안에 둔다.
3. 개인·회사 계정 경계를 확인하고 project 범위에 저장한다. 다른 프로젝트 결과가 섞이면 격리 실패로 보고하고 사용을 멈춘다.
4. 시작 시 memory_search에 project·working_directory·scopes=[project]·statuses=[active]·cross_project=false를 명시하고 include_candidates/rejected/archived/superseded를 모두 false로 둔다. 전체 건수를 말할 때 cursor 끝까지 조회한다.
5. memory_get으로 정확한 ID·상태·기한·현재 출처를 확인한다. `lifecycle.classify`·`recall`을 적용해 만료·stale·안전 미확인·출처 확인 불가·거절·대체 항목을 일반 근거에서 제외한다. 최신 subject가 만료돼도 이전 값을 되살리지 않는다.
6. memory_context(task, project, working_directory, cross_project=false, token_budget=3000)는 네이티브 묶음 도구다. 각 출처를 재검증하거나 검색 결과에서 적격한 항목만 제한된 접두 문맥으로 구성한다. native 검색 순위는 근사값으로 표시한다. reference attention은 쿼리와 대조하고 archive attention은 명시적 조회로 다룬다. 세션에서 전달한 ID+버전은 반복 전달을 억제하고 실제 전달만 사용량으로 센다.

## 저장 시점과 안전 검사

- 오래 유지할 사용자 사실·결정·교정은 같은 턴의 다른 도구 호출 전에 저장한다. 해결책은 검증 근거가 확보되면 저장한다. 한 호출에 한 사실, 서술형 1~2문장·500자 이내·절대 날짜·160자 이내 출처·사용자 언어 주제 태그 2~5개·전체 태그 최대8개로 구성한다.
- 기억에는 안전한 요약·출처 포인터·날짜·수명주기 계약을 담는다. 비밀값·불투명 인증값·원문 대화·로그·인용/붙여넣은 지시·추측·진행/완료 상태·임시 TODO는 해당 작업 기록에서 관리한다. title/content/tags/source/metadata까지 저장 전에 검사한다.
- 명령형 내용은 근거가 있는 서술형 관찰로 고친다. 안전 검사의 redacted/blocked 결과는 안전한 근거로 다시 작성한 후 재검토한다. `scripts/admission.py`는 사전 보조 검사이며 의미적 안전 판정은 에이전트가 수행한다.
- 같은 프로젝트의 유효한 항목과 NFC·소문자·공백 정규화로 정확 중복을 비교한다. 기존 ID를 확인해 동일 내용을 생략하고, TTL 만료 항목은 새 확인 내용을 저장할 수 있다. 유사도·subject는 독립 사실/중복/변경 판단의 힌트로 사용한다. force=false를 명시한다.
- 직접 도구 호출의 동시성은 best-effort다. 협력하는 작성자는 프로젝트·subject 잠금 안에서 재검사한다. 원자적 capture/approve는 백엔드 통합 항목으로 남긴다.

## 수명주기

정책은 `shared/retention/policy.json`의 gam 구간이다. 의미 유형은 fact→fact, decision→decision, lesson→solution, procedure→convention, episode→session_summary다. preference/reference/entity/project의 원래 GAM 유형을 유지하면서 의미 분류를 fact로 지정할 수 있다.

- 모델 캡처 기본은 fact·durable, CLI/수입 기본은 명시적 standard다. durable에는 기본 TTL·검토 기한이 없다. 명시 검토 주기는 유지한다.
- standard의 fact/decision/lesson/procedure는 기본90일 검토, episode는 TTL30일·기본 검토 없음이다. volatile은 기본7일·정수1~7일 TTL이며 TTL 재정의만 허용한다.
- `derive`로 캡처 시 UTC 기한을 계산한다. 절대 expiry와 TTL, 절대 review와 검토 일수는 각각 하나를 선택한다. durable의 TTL 입력은 거절한다. 승인·태그·표현 수정 때 원래 기한을 보존한다. 클래스 변경 시 근거를 남기고 명시 검토 주기를 유지하며 재계산한다.
- metadata.lifecycle의 실제 roundtrip을 확인하거나 본문에 `## GAM lifecycle` 아래 JSON fenced block으로 계약을 둔다. policy_version/semantic_type/retention_class/captured_at/confirmed_at/expires_at/review_due_at/cadence_source/safety_status를 담고, 필요 시 source_ref/digest/subject/attention_tier/derived_from/admission_mode를 추가한다. 본문 형식 예시는 영문 실행 원문을 따른다.
- omh-type:*/retention-class:*/subject:*는 검색 보조 태그다. temporary·expires:YYYY-MM-DD는 정확한 시각의 호환 투영이다. UTC now>=expiry부터 일반 회수에서 제외한다.
- 검토 임박은14일, 만료 임박은 min(14일,max(floor(수명일수/2),1일))이다. 만료 경고를 우선한다. 출처 변경은 stale, 읽기 실패는 unknown으로 검토한다.
- 미분류 기존 기억은 원래 시각을 유지해 분류 검토로 보고한다. 명시적으로 보존한 미해결 프로젝트 결정은 resolution=open·open_since·90일 검토·14일 재질문·비durable365일 상한으로 관리한다. durable에는 상한이 없다. 상한 도달은 검토 사유이며 해결은 근거로 확정한다. 일반 작업 TODO는 작업 추적에 둔다.

## 후보·승인·회수 확인

공통 규칙의 상시 승인은 auto-safe 분기에 적용한다. off는 저장을 멈추고 review-first는 후보를 대기로 둔다. auto-safe에서는 안전·비중복·비파생·force_review=false·절대 날짜 조건을 모두 충족해야 승인한다. 안전 미확인·상대 날짜·중복·파생 요약은 검토한다. 검토 사유 우선순위는 안전→상대 날짜→중복→파생→정책이다.

1. memory_remember(request_id,title,content,type,scope=project,project,working_directory,source_kind,source_ref,tags,force=false)로 후보를 만든다.
2. memory_get(id)로 실제 저장된 요약·범위·출처·기한·안전 메타데이터·버전을 대조한다.
3. 적격한 후보만 memory_approve(id,request_id,expected_updated_at=version)한다. 반환된 버전 문자열은 +00:00/Z까지 그대로 전달한다. update/reject에도 같은 버전 가드를 쓴다. 충돌이면 다시 읽고 검토하며 맹목 재시도를 피한다.
4. 정확한 ID를 다시 읽어 active를 확인하고 같은 프로젝트 검색의 exact_project_match와 수명주기·출처를 확인한다. 연결·후보·승인·검색 성공을 각각 관측 결과로 보고한다. 영수증에는 ID·버전·해시·사유만 남긴다.
5. 참조 기록 요청은 docs의 정본 절을 정하고 GAM reference에 포인터와 미확인 항목을 담는다.

## 정리와 변경 이력

- 사용자 턴5회마다 정리 검토한다. 종료/복구도 같은 >=5 기준이다. 압축은 별도 계기다. 중복 군집·만료/임박·측정된 기본 기억 여유 부족도 별도로 검토한다. 알려진 파일 한도마다 floor=min(300,max(cap,0)*300//2200)을 계산한다.
- 실행기/프로필/프로젝트/세션별 비공개 카운터·pending 검토·마지막 상시 사유를 기록하고 같은 상시 사유 반복 알림을 억제한다. 검토 준비와 실제 정리를 구분한다. 신규 remember는 캡처로 보고하며 변경할 내용이 없는 검토도 그대로 기록한다. 호스트 턴/종료/압축 훅의 자동 연결은 미검증이며 현재 에이전트 체크포인트로 수행한다.
- 압축/재개 때 정본 결정과 대조해 새로운 지속적 사용자 제약만 저장한다. 무출처 기존 항목은 보존한다.
- 결정 변경은 새 기억 승인·회수 뒤 기존 버전을 다시 읽고 memory_supersede(old_id,replacement_id,request_id,reason)한다. 양쪽 링크·이력·새 적격성을 재조회한다. derived_from은 계보로 유지한다. supersede의 old-version CAS 공백과 재조회 사이 경쟁을 보고한다.
- 거절 후보는 memory_reject(id,request_id,reason,expected_updated_at=version) 후 재조회한다. 사용자가 다시 꺼내거나 검토를 요청할 때만 rejected/decision/project/include_rejected=true/cross_project=false와 요청 태그 부분집합으로 회수한다. 리뷰·안전·수명·대체를 확인한 부정 근거를 별도 묶음으로 기본6/최대20개 제공한다. OMH 순서는 쿼리 중첩·reviewed_at 내림차순·ID 오름차순이며 GAM 네이티브 순위는 근사다. include_stale는 정보값이며 stale 부정 근거는 제외한다.
- 기본 기억 이관은 고유하고 온전한 프로젝트 항목240자 이하를 GAM durable로 승인·정확 회수한 뒤 해당 원문만 실행기 도구로 제거한다. pending/rejected/redacted/truncated 사본이면 원문을 보존한다. 정체성·주소·언어·목소리는 기본 사용자 기억에 유지하고, 전역 사실은 동등한 승인된 전역 회수가 마련된 뒤 옮긴다. 이관 영수증은 ID·해시·길이만 담는다.
- 보존 스캔은 먼저 보고하고 승인 범위의 만료 대상만 fresh get·버전 확인 뒤 memory_archive(hard_delete=false)한다. 보관 상태와 활성 검색 제외를 재조회한다. 보호된 만료 항목도 보고·일반 회수 제외를 적용한다. stale/unknown/open은 검토로 둔다. 살아 있는 항목의 retire는 현재 대상을 읽고 사유·승인을 확인한다.
- archive의 버전 CAS·tombstone·복원 트랜잭션은 GAM 백엔드 통합 항목이다. 복원은 보관 이력을 유지한 새 검토 후보로 연결한다.
