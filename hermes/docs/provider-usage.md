# 사용량 플러그인 표시 제한

`provider-usage`의 상태바·툴팁·상세 패널·한도 알림에는 연결된 GPT·Claude만 표시한다. 내부 제공자 ID는 GPT가 `openai-codex`, Claude가 `anthropic`이다. 표시명은 GPT·Claude로 맞춘다. 조회 실패는 오류로 표시하고 사용량 0으로 처리하지 않는다.

원본 플러그인의 눈 버튼은 상태바 표시만 조절한다(v0.2.1 기준 확인). 상세 패널과 알림까지 제한하는 기본 설정은 확인되지 않아, 이 저장소의 표시 어댑터를 적용한다. 공식 플러그인의 기본 기능과 구분한다.

## 적용

플러그인 설치·활성화 후 Agent-setup의 `hermes/`에서 미리보기와 적용을 수행한다.

```sh
python3 scripts/configure_provider_usage.py
python3 scripts/configure_provider_usage.py --apply
```

기본 홈은 `${HERMES_HOME:-$HOME/.hermes}`이며 `--home`으로 프로필을 지정한다. 설치 원본 `plugins/provider-usage/desktop/plugin.js`와 Desktop 복사본 `desktop-plugins/provider-usage/plugin.js`를 확인한다. 복사본이 없으면 화면 적용은 미완료다.

Desktop 복사본의 홈이 다르면 실제 위치를 확인해 `--desktop-home`을 지정한다. 앱 수준 공유에 따른 영향 범위는 확인하되 다른 프로필을 자동 수정하지 않는다.

원본은 선택한 홈의 `backups/provider-usage/`에 권한 600으로 보존한다. 같은 어댑터는 건너뛰고, 호환되지 않거나 사용자가 변경한 코드는 보존하고 중단한다. 복구 시 대상 백업과 이후 사용자 변경을 확인한다. Agent-setup의 `bash hermes/scripts/update.sh`가 플러그인을 실행 시점의 최신 정식 태그로 올리고 `patches/provider-usage/<태그>.patch`와 이 어댑터를 다시 적용한다. 새 태그용 패치가 없으면 바꾸기 전에 멈춘다. 업데이트 후에는 미리보기와 표시 검증을 반복한다.

API 키·인증 파일·모델·OMH fallback은 수정하지 않는다. 이 어댑터는 표시와 알림만 제한한다. 원본 백엔드의 다른 제공자 조회 기능까지 비활성화하는 것은 아니다.

## 보존과 확인

새로고침 주기·Used/Remaining·상태바 선택을 보존한다. `barProviders`가 없거나 `null`이면 연결된 GPT·Claude 둘 다 표시하고, 명시한 빈 목록·단일 선택은 그대로 유지한다. 숨긴 제공자 ID는 눈 버튼을 조작한 뒤에도 저장 목록에서 삭제하지 않는다.

`python3 -m unittest discover -s tests -v`로 어댑터와 DOM 검사를 실행한다. DOM 검사는 설치 원본·Desktop 복사본과 기존 의존성을 사용하며, 없으면 해당 검사를 건너뛴다. 별도 의존성 위치는 `HERMES_DESKTOP_NODE_MODULES`로 지정한다.

실제 Desktop에서 조회·새로고침과 모든 표시 영역의 제한, 숨긴 제공자의 알림 차단, 기존 선택 보존을 확인한다. 재로딩이 필요하면 지원 기능을 사용하며 세션을 종료하거나 앱을 강제 재시작하지 않는다.

[원본 플러그인](https://github.com/PhoeniXAbhisheK/hermes-plugin-provider-usage), [검증 상태](verification.md).
