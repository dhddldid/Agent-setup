# 출처

- [Hermes 공식 문서](https://hermes-agent.nousresearch.com/docs/): 설치·스킬·플러그인·브라우저·설정
- [Hermes 원본](https://github.com/NousResearch/hermes-agent/releases/latest): 공식 스킬 57개의 원본. 설치할 때 최신 정식 릴리스 태그를 조회해 그 태그에서 받는다
- [OMH 설치 안내](https://github.com/rlaope/oh-my-hermes/releases/latest): 최신 정식 릴리스의 `INSTALL_FOR_AGENTS.md`를 Hermes용 검토 기준으로 쓴다
- [Provider Usage](https://github.com/PhoeniXAbhisheK/hermes-plugin-provider-usage/releases/latest): 필수 사용량 플러그인. 최신 정식 릴리스 위에 `patches/provider-usage/<태그>.patch`를 적용한다
- [Aside 개발자 안내](https://docs.aside.com/help/developers): CLI·REPL·MCP
- [Agent-setup 공통 스킬 출처](../../shared/skills/SOURCES.md): 공통 스킬 34개의 원본과 가져온 버전

`manifest.json`은 설치 원본 저장소와 스킬 목록을 적는다. `scripts/install_skills.py`는 실행할 때마다 Hermes 최신 정식 태그와 그 커밋을 조회해 그 태그를 받고, 공식 스킬의 지원 파일과 라이선스를 함께 가져온다. `scripts/check.py`는 manifest에 버전 고정 필드가 생기면 실패로 보고한다.

Hermes 배포본의 공통 스킬 34개는 Agent-setup `shared/skills/`에서 관리한다. 외부 스킬 39개는 Agent-setup `codex/inventories/external-skills.json`의 원본 저장소·스킬 경로를 따르고, 설치할 때 원본별 최신 정식 릴리스 태그의 커밋을 받는다. 받은 태그·커밋·해시는 Agent-setup 상태 경로의 설치 기록에 남는다.
