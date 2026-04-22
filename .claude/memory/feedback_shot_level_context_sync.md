---
name: feedback_shot_level_context_sync
description: 대본 문장 단위로 영상 맥락 일치 필수. "담배를 피고 있다" 문장에 맞춰 담배 영상. section-level 단일 clip 은 granular 부족.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/script_v3.json (section-level 단일 visual_directing)
  - output/ryan-waller/final_v3.mp4 (9 section × 1 clip → 맥락 불일치 다수)
failure_mapping:
  - FAIL-v3-대본영상_맥락_section단위_단일clip: 대표님 "대본 및 나레이션이랑 영상은 같은 맥락이어야해" + "대본에 담배를 피고있다고하면, 담배를 피는 영상이 나와야 한다는거다"
---

# feedback: shot-level 대본-영상 맥락 일치

## 규칙

**대본의 각 문장 (또는 문장 내 핵심 명사구) 에 맞춰 영상이 바뀌어야 한다.** section-level 단일 clip 으로 10-15초 동안 한 장면만 보여주면 section 안에서 말하는 여러 사실 중 하나만 시각화되고 나머지는 맥락 불일치.

### 예시 위반 (v3)

`body_6hours` section (14.5s) narration:
> "취조는 여섯 시간 동안 계속됐습니다. 라이언은 점점 말을 잃어갔고 한쪽 동공은 풀어져 갔습니다. 그러나 달튼은 연기라고 확신했죠. 병원도 구급차도 부르지 않았습니다. 그 시각 진범은 이미 피닉스를 벗어나고 있었습니다."

**영상**: `broll_03_clock_v3.mp4` (벽시계) 만 14.5s 내내.

→ 영상이 "진범 도주"·"병원 부재"·"라이언 동공" 등 4개 핵심 사실 중 **1개 (시간)** 만 시각화. 나머지 3개는 대본만 읽음 → 대표님 "대본과 영상 따로 논다".

### 올바른 shot breakdown (v3.1 이후)

```
body_6hours 14.5s 를 3 shot 으로 분할:
  shot 3.1 (0-5s) "여섯 시간 / 말을 잃어갔고 / 동공 풀림"
    → broll_03_clock.mp4 (5s) + Ryan 얼굴 close-up 교차
  shot 3.2 (5-10s) "달튼 연기 확신 / 병원 부재"
    → broll_05_hospital.mp4 (5s, 빈 복도)
  shot 3.3 (10-14.5s) "진범 피닉스 벗어나고 있었다"
    → broll_04_fleeing.mp4 (4.5s trim, 도주 실루엣)
```

각 shot 은 **하나의 fact 를 직접 시각화**. 영상 흐름 = 대본 흐름.

### 구현 (visual_spec 확장)

현재 v3 의 `scene_sources` 는 section 당 1 항목. v3.1 은 shot 당 1 항목으로 확장:

```json
{
  "sections": [
    {
      "section_id": "body_6hours",
      "shots": [
        {"text_excerpt": "취조는 여섯 시간 ... 동공은 풀어져 갔습니다", "duration_s": 5.0,
         "visual_directing": "벽시계 → Ryan 얼굴 close-up 부은 눈",
         "src": "broll_03_clock_v3.mp4"},
        {"text_excerpt": "그러나 달튼은 ... 부르지 않았습니다", "duration_s": 5.0,
         "visual_directing": "빈 병원 복도 → 형사 모니터 무표정",
         "src": "broll_05_hospital_v3.mp4"},
        {"text_excerpt": "그 시각 진범은 ... 벗어나고 있었습니다", "duration_s": 4.5,
         "visual_directing": "도주 실루엣 피닉스 외곽 road",
         "src": "broll_04_fleeing_v3.mp4"}
      ]
    }
  ]
}
```

scene_sources 는 shots 전수 flat 화.

### 맵핑 룰

- **short section ≤ 5s**: 1 shot (현재 v3 와 동일)
- **medium section 5-10s**: 1-2 shots
- **long section > 10s**: 2-4 shots 필수 (Kling 10s 상한도 해결됨 — freeze 회피)
- **shot 경계** = 문장 경계 (period/question) 또는 의미 덩어리 경계

## Why

세션 #34 v3 대표님 판정 원문:
> "시나리오 , 대본대로 영상이 움직여야된다고, 영상의 움직임이 대본의 내용을 따라야된다. 대본에 담배를 피고있다고하면, 담배를 피는 영상이 나와야한다는거다. 대본 및 나레이션이랑 영상은 같은 맥락이어야해"

Reference zodiac-killer 의 visual_directing 에 `→` 로 여러 장면 지시 ("Z340 원본 → 인트로 시그니처 → ...") — 이는 **여러 clip 이어 붙임** 의도. 내가 단일 clip 에 `→` directing 을 주고 Ken Burns pan 으로 대체하려 한 것은 오해.

Reference 의 `visual_spec.json` 은 body 당 여러 clip. 우리 v3 는 body 당 1 clip. 바로 이 gap 이 "대본-영상 따로" 의 root cause.

또한 freeze 14건도 동일 root cause — 10s Kling clip 이 14s section 덮으면 freeze. shot breakdown 하면 4.5s 꼬리도 다른 clip 이 채움 → freeze 0.

## How to apply

- **scripter → shot-planner → asset-sourcer** 3 단계 분리:
  1. scripter 가 section-level narration + visual_directing
  2. shot-planner 가 section 을 2-5 shots 로 분할 + 각 shot visual_directing + duration
  3. asset-sourcer 가 shot-level source 수급 (multi-source search 의 query 도 shot visual_directing 기반)
- **visual_spec_builder**:
  - `scene_sources` → `shot_sources` (flat list, 각 shot 의 src)
  - 기존 script.sections 기반 equal split 로직 대신 shot.duration_s 기반 durationInFrames 계산
- **Kling I2V fallback 호출**:
  - shot 이 실 footage 부재 시 shot.visual_directing 을 prompt 로 Kling 호출
  - duration 은 shot.duration_s 에 맞춰 5 or 10 선택 (단일 shot ≤ 10s 원칙)

## 검증

```bash
python -c "
import json
d = json.load(open('output/<episode>/script_v3_1.json'))
for s in d['sections']:
    shots = s.get('shots')
    narration_len = len(s.get('narration', ''))
    if narration_len < 40:
        continue  # short section OK with 1 shot
    assert shots and len(shots) >= 2, (
        f'section {s[\"section_id\"]} long ({narration_len}c) but only {len(shots) if shots else 0} shots'
    )
print('✅ shot breakdown coverage OK')
"
```

## Cross-reference

- `feedback_script_video_sync_via_visual_directing` (상위 규칙)
- `feedback_kling_duration_10s_not_5s` (10s 상한, shot 나눠서 해결)
- reference: `shorts_naberal/output/zodiac-killer/visual_spec.json` (body 당 여러 clip)
- 세션 #34 v3 대표님 직접 판정
