---
name: product-design-review
description: Create or change user-facing screens and flows using the product's design system, then verify the rendered result. Use for UI implementation, redesign, component registry adoption, chart styling, footers, motion, and visual review.
---

# 제품 화면 제작과 검수

화면 작업의 기준은 OMH `omh-frontend`와 `omh-visual-qa`다. Claude Code·Codex에서는 이 기준을 해당 실행기의 코드·브라우저 도구로 직접 수행한다. 제품의 `DESIGN.md`, 화면 계약과 사용자 요청을 먼저 적용한다. 새 제품의 컴포넌트 라이브러리는 제품 요구와 기존 스택에 맞춰 선택한다.

## 화면 구현

1. 대상 화면, 사용자, 주요 과업, 기존 디자인 기준과 실제 화면을 확인한다. 새 제품이나 큰 시각 변경에서는 색·타이포그래피·간격·레이아웃·컴포넌트·모션·반응형 규칙을 제품의 디자인 정본에 연결한다. 기존 제품의 작은 수정은 현재 기준을 이어간다.
2. 사용자가 레퍼런스 선택을 요청하거나 에이전트의 제안에 동의하면 실제 사례 최소 5개를 표 한 장(사이트 | 링크 | 테마 | 채택할 요소 | 추천 이유)으로 제시하고 추천 하나를 표 아래 한 줄로 밝힌다. 사용자가 링크를 직접 열어 보므로 화면 캡처는 사용자가 요청할 때만 만든다. 선택 절차가 없는 작업은 제품 목적과 기존 브랜드에 맞춰 진행한다. 제공된 레퍼런스에서는 적용할 디자인 토큰과 화면 패턴을 구체적으로 읽는다.
3. 화면·컴포넌트별 필요한 상태를 정한다. 기본·hover·focus·active·disabled와 해당 화면의 loading·empty·error를 포함하고, 키보드·터치·접근성·한국어 및 CJK 줄바꿈을 확인한다. 장식보다 정보 위계와 주요 행동을 우선한다.
4. 현재 컴포넌트와 토큰을 사용해 요청 범위를 구현한다. 외부 레지스트리 컴포넌트, 마키·텍스트 효과, 차트, 푸터 또는 스타일 프리셋을 다룰 때는 [OMH 프론트엔드 적용 기준](references/omh-frontend-practices.md)의 해당 부분을 읽는다. shadcn/ui를 선택한 프로젝트의 컴포넌트 작업은 `shadcn`, 해당 lint 구성은 `shadcn-lint`를 함께 사용한다.

## 렌더 결과 검증

- 변경한 화면을 실제로 렌더링하고 지원하는 화면 크기와 상태를 확인한다. 웹의 새 화면·큰 개편은 데스크톱·태블릿·모바일을 포함하며 1440·768·375px을 시작 크기로 삼고 제품의 지원 크기를 추가한다.
- 레퍼런스 또는 제품 디자인 정본과 화면을 비교해 간격·색·타이포그래피·정렬·잘림·상태 차이를 기록한다. 발견한 문제를 고친 뒤 같은 조건에서 다시 확인한다.
- 조작이 있는 화면은 주요 클릭 경로, 키보드 포커스, 오류·빈 상태와 필요한 모션 상태를 확인한다. 성능 수치는 측정한 환경과 경로를 함께 기록한다.
- 구현, 코드 검사, 브라우저 동작, 접근성, 렌더 확인, 배포 상태를 실제 관찰한 근거에 맞춰 각각 보고한다. 화면 검수만 요청받은 경우 발견 사항과 근거를 전달한다.

OMH 출처: [omh-frontend](https://github.com/rlaope/oh-my-hermes/blob/36e96feb432068cd27eecf5b434acdf1328341b4/skills/omh-frontend/SKILL.md), [omh-visual-qa](https://github.com/rlaope/oh-my-hermes/blob/36e96feb432068cd27eecf5b434acdf1328341b4/skills/omh-visual-qa/SKILL.md). 프론트엔드 세부 기준은 2026-10-09의 OMH `main` 커밋을 따른다. Hermes 전용 실행 기록과 전달 형식은 Claude Code·Codex의 직접 작업 흐름에 맞게 바꾼다.
