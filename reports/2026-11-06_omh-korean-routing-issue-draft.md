# OMH 이슈 초안: 한국어 여러 부분 요청에 dag-ulw 추천이 붙지 않음

- 올릴 곳: https://github.com/rlaope/oh-my-hermes/issues (계정 dhddldid)
- 비슷한 기존 이슈: #1582(한국어 요청이 스킬에 닿지 않음, P1로 처리됨), #1689, #1607
- 측정 근거: 이 저장소의 `hermes/omh/trigger-packs/evaluate.py`, `scripts/check_parallel_gaps.py`

## 한국어 요약

| 항목 | 내용 |
|---|---|
| 현상 | 기능 여러 개를 나열하거나 "~부터 ~까지 개발해줘"처럼 평소 말투로 요청하면 Route Hint가 아예 붙지 않거나 웹 조사 같은 엉뚱한 흐름이 붙는다. 그래서 AI가 에이전트를 하나씩 띄운다. 같은 요청을 영어로 쓰면 dag-ulw가 붙는다. |
| 원인 | dag-ulw·ulw-work에는 기본 한국어 신호 단어가 없다. 사용자 단어 목록은 OMH 기본 규칙이 아무것도 고르지 않은 문장에만 쓰인다. |
| 측정 | 단어 목록을 맞춘 문장은 46/51을 맞혔다. 처음 보는 문장은 0/10과 1/10을 맞혔다. 작은 요청에 잘못 붙은 경우는 0건이다. |
| 영향 | 30일 동안 위임 75번 중 58번이 에이전트 1개짜리였다. dag-ulw를 쓴 세션은 위임한 21개 중 4개였다. |
| 지금 하는 일 | 공통 지침에 "나눠서 한 번에 띄우기" 규칙을 넣었다. 한국어 단어 목록은 보조로 쓴다. 3일마다 기록을 점검한다. |
| 요청 | ① 특정 언어의 단어 대신 일의 모양(나열된 여러 기능, 단계, 범위)으로 판단하기, 또는 한국어 신호 단어 기본 제공 ② 여러 부분 요청에서 사용자 단어 목록이 기본 규칙과 겨룰 수 있게 하기 ③ 문장 묶음으로 Route Hint를 시험하는 공식 방법 |

## 올릴 본문 (영어)

**Title:** `[Bug]: Casual Korean multi-part build requests get no dag-ulw Route Hint; user trigger packs cannot close the gap`

```
## What happens
In Hermes, everyday Korean requests that describe a multi-part build
(several features, staged development, "from X to Y") get no Route Hint,
or a hint for an unrelated workflow. The agent then runs the job one
subagent at a time. Equivalent English requests reach dag-ulw.

Examples (OMH 4.0.6, Hermes, real Route Hint via awareness_route_hint):
- "회원가입 로그인부터 일반채팅, 지식그래프까지 설계에 맞게 개발해줘" -> no hint
- "메일 가져오기, 파일 업로드, 검색 기능 개발해줘" -> web-research (shipped rule)
- "그럼 그거 다 이어붙여서 진행해" -> no hint
- "추천대로 진행" -> no hint

## Why a user pack does not fix it
- dag-ulw / ulw-work have no Hangul entries in the shipped shortlist, and
  dag-ulw's strong routing signals are English and Russian only.
- A user trigger pack (~/.omh/routing/trigger-packs/ko.json) is consulted
  only as the last resort in awareness_route_hint, after every shipped rule,
  and only when the router's own selection equals the pack skill.
- Measured with an isolated OMH/Hermes home:
  | set | multi-part hit | small-ask false positive |
  |---|---|---|
  | pack tuning set | 46/51 | 0/54 |
  | fresh held-out sentences (2 sets) | 0/10, 1/10 | 0/10, 0/10 |
  Phrase lists fit the sentences they were written for and miss fresh
  casual phrasing. 2 of the 10 held-out misses were claimed by a shipped
  rule (web-research, img-summary) that a pack cannot override.

## Impact
Over 30 days of my Hermes history: 75 delegate_task spawns, 58 with a
single task; dag-ulw loaded in 4 of 21 delegating sessions.

## What I do locally for now
- A global rule in SOUL.md: list parts and what each waits on before the
  first delegation, and start every ready part in one delegate_task call.
- A local Korean trigger pack (supplement only).
- A no-agent cron every 72h that counts single-task spawns and sessions
  without dag-ulw from state.db, and replays a Korean request corpus
  through awareness_route_hint after each OMH update.

## Ask
1. Recognize multi-part shape language-independently (several listed
   features/stages, "from X to Y" ranges) instead of per-language cue
   phrases, or ship Korean cues for dag-ulw / ulw-work / ulw-loop.
2. Let a matching user-pack entry compete with shipped rules for
   compound requests, or flag compound requests so a shipped single-domain
   rule (web-research, workspace-file-operator) does not win.
3. Optional: a supported way to run the Route Hint offline against a
   corpus (we call awareness_route_hint in an isolated home).

Happy to share the corpus and the evaluation script.
```
