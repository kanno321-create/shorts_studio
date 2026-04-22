---
name: feedback_hook_visual_brief_not_extended
description: hook section 의 한 visual (예: 크리스마스 집 외관) 은 2-3초만 노출. 전체 hook 10초 내내 동일 장면 금지 — 시청자 이탈 + "왜 하루종일 틀고있노" 판정.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/final_v3.mp4 (v3 — hook 10.72s 내내 broll_02_christmas_night)
  - output/ryan-waller/visual_spec_v3.json hook clip durationInFrames=322
failure_mapping:
  - FAIL-v3-크리스마스_집_과노출: 대표님 "초반에나오는 크리스마스의 집영상이 너무 오래뜨고 나레이션이랑 전혀 관계없는데 왜자꾸 사용하노,,, 크리스마스라는것때문에? 그럼 아주잠깐만 사용하지 하루종일틀고있노"
---

# feedback: hook 시각 = brief & multi-shot (10초 단일 장면 금지)

## 규칙

**hook section (channel-incidents preset = 9~12s) 은 여러 shot 으로 분할** + 각 shot ≤ 3s. 한 시각 요소 (예: 크리스마스 집 외관) 가 hook 10초 내내 나오면 시청자가 사건 파악 못 하고 이탈.

### 위반 예시 (v3)

hook narration (10.72s):
> "2006년 12월 24일 크리스마스 이브. 애리조나 피닉스입니다. 열여덟 살 남자친구가 피를 흘리며 멍하니 앉아 있었습니다. 옆에는 스물한 살 여자친구의 시신이 있었죠. 형사는 여섯 시간을 몰아붙였고 의료진은 단 한 번도 부르지 않았습니다. 그러나 진실은 전혀 달랐습니다. 오늘의 기록."

v3 영상: `broll_02_christmas_night_v3.mp4` (크리스마스 장식 집 외관) **10.72s 내내**.

→ "피를 흘리며 앉아 있었습니다" / "시신" / "여섯 시간" / "오늘의 기록" 4개 사실 전부 **크리스마스 장식 집 외관** 으로 덮임. 시청자 눈에 "크리스마스 관련 영상" 으로 각인 → 사건 정체성 희미.

### 올바른 hook shot breakdown (v3.1 이후)

hook 10.72s 를 **4 shot 으로 분할**:

| shot | 시간 | 대본 발언 | 영상 |
|------|------|----------|------|
| shot 0.1 | 0-2s | "2006년 12월 24일 크리스마스 이브. 애리조나 피닉스입니다." | `broll_02_christmas_night.mp4` (집 외관 + 크리스마스 등, 2s) |
| shot 0.2 | 2-5s | "열여덟 살 남자친구가 피를 흘리며 멍하니 앉아 있었습니다." | Ryan 얼굴 close-up 부은 눈 (취조실 아닌 발견 당시, 3s) |
| shot 0.3 | 5-8s | "옆에는 스물한 살 여자친구의 시신이 있었죠." | 현장 — 희생자 실루엣 blur (3s, ins-mosaic 준수) |
| shot 0.4 | 8-10.7s | "형사는 여섯 시간을 몰아붙였고 ... 오늘의 기록." | 취조실 + 시그니처 탐정 실루엣 (2.7s, intro_signature 일부 또는 broll_01) |

각 shot 이 2-3s 로 짧아서 시청자가 "여러 장면 = 복잡한 사건" 인상. 크리스마스 집은 첫 2s 만 — "시점 정보" 역할.

### 일반 원칙 (any section)

- 1 visual element 의 최대 노출 = **3s** (채널-incidents default)
- 10s 이상 section 은 최소 3 shot 필요
- 반복 cut 허용 (같은 clip 을 두 번 쓸 수 있음, 단 중간에 다른 clip 끼워)

## Why

세션 #34 v3 대표님 판정 원문:
> "초반에나오는 크리스마스의 집영상이 너무 오래뜨고 나레이션이랑 전혀 관계없는데 왜자꾸 사용하노,,, 크리스마스라는것때문에? 그럼 아주잠깐만 사용하지 하루종일틀고있노"

핵심 두 가지:
1. "크리스마스라는것때문에" — 대표님이 내 매핑 로직을 즉시 간파. "연도·시점 표식" 용도로만 사용해야 하는데 전체 hook 덮어씀.
2. "아주잠깐만 사용하지 하루종일" — 한 영상의 적정 노출은 2-3s ("잠깐"). 10s 이상은 "하루종일" 체감.

reference zodiac-killer hook 확인 시 실제로 3-4 개 shot 으로 구성됨 (Z340 원본 close-up → 인트로 시그니처 → 탐정 실루엣 순차).

## How to apply

- **shot-planner 에이전트 측**:
  - section 마다 narration 문장 수 기준으로 shot count 결정 (≥ 문장 수)
  - 각 shot duration 2-3s (단, short section 1 shot 5s 도 허용)
  - hook 은 반드시 ≥ 3 shots (채널 특성)
- **visual_spec_builder 측**:
  - scene_sources 확장 → shot_sources (flat list, shot 당 1 src)
  - hook section 의 shots 순서 = narration 순서 엄수
- **ins-narrative-quality 검증**:
  - hook section 의 shots 수 ≥ 3
  - 각 shot duration ≤ 3.5s

## 검증

```bash
python -c "
import json
d = json.load(open('output/<episode>/visual_spec_v3_1.json'))
# hook clips group 추출 (intro 제외)
# (구체 구현: clip 을 section 단위로 grouping)
print('visual_spec contains intro + hook shots + body shots + outro — check manually per section')
"
```

## Cross-reference

- `feedback_hook_context_30s_rule` (hook 대본 content 규칙)
- `feedback_shot_level_context_sync` (상위 원칙)
- `feedback_kling_duration_10s_not_5s` (shot duration 10s 초과 금지)
- reference: `shorts_naberal/output/zodiac-killer/visual_spec.json` hook clips
- 세션 #34 v3 대표님 직접 판정
