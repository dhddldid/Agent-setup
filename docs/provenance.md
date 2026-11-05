# 출처

세 원본 저장소의 추적 파일을 실행기 폴더에 복사했다. 출처 커밋과 파일별 SHA256는 [이관 목록](import-manifest.json)에 있다.

| 폴더 | 원본 | 라이선스·출처 |
|---|---|---|
| codex/ | Codex-Setup | upstream/README.md, upstream-LICENSE-OMH (OMH MIT), 차용 스킬별 LICENSE, inventories/ 설치 목록 |
| claude/ | Claude-Setup (로컬) | routes/claude-code.json의 OMH 출처, upstream-LICENSE-OMH (OMH MIT 사본) |
| hermes/ | Hermes-Setup | LICENSE (MIT), docs/sources.md, manifest.json의 원본·플러그인 저장소 |

Codex·Claude의 12개 분류·추론 표는 OMH v4.0.0(36e96fe) README의 추천 모델 표를 출처로 한다. Claude·Codex의 OMH 스킬 사본 버전은 `shared/skills/omh/SOURCE.json`에, Hermes OMH는 실행 시점에 조회한 최신 정식 릴리스로 설치한다.

외부 공개 전에 확인할 항목:

- Codex-Setup 자체의 최상위 라이선스
- codex/inventories/external-skills.json 외부 스킬 39개의 라이선스 (2026-10-21 추가한 motion-design·hyperframes-animation은 원본 저장소 LICENSE가 Apache-2.0)
- Hermes provider-usage 플러그인의 라이선스

루트의 README·AGENTS·CLAUDE·docs/·scripts/check.py·tests/는 Agent-setup에서 작성했다.
