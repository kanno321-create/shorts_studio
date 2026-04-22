---
name: feedback_script_markers_absolute_compliance
description: 🔴 영구 INVARIANT Rule 2 — 대본에 적힌 감정·상황·움직임 표현 그대로 제작, 대본 밖 요소 추가 절대 금지. 향후 모든 영상 작업에 필수 적용.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
priority: critical
---

# 🔴 INVARIANT Rule 2 — 대본 표현 (감정·상황·움직임) 절대 준수, 벗어남 금지

## 대표님 원문 (verbatim)

2026-04-23 세션 #34:
> "절대원칙이 대본에적힌 감정표현, 상황표현, 움직임에관한표현등을 보고 제작하고, 절대 벗어나는 작업은 하지 않는다."

## 규칙

모든 에이전트는 script.json 에 기술된 **emotion / situation / motion** 표현을 신호로 해석하고 **그대로만** 영상·음성·시각에 반영한다. 대본에 없는 요소를 에이전트가 자체 해석·추가 **금지**.

### 3 표현 카테고리

| 카테고리 | 의미 | 소비자 | 예시 |
|---------|------|-------|------|
| **emotion_markers** | 감정 톤 표현 | TTS (emotion_preset), 자막 스타일 | "긴박하게", "속삭이듯", "슬프게", "몰아붙였고" |
| **situation_markers** | 장소/시간/대상 | 영상 scene, 이미지 검색 keyword | "2006년 12월 24일", "피닉스 자택", "취조실", "법원" |
| **motion_markers** | 움직임 동사 | Kling I2V prompt 의 motion 지시 | "천천히 걷는다", "고개를 숙인다", "피를 흘리며 멍하니 앉아" |

### Script schema 요구사항

shot (or scene) level 에 각 marker 배열 명시:

```json
{
  "shot_id": "hook_s01",
  "text": "2006년 12월 24일 크리스마스 이브.",
  "emotion_markers": [{"token":"(뉴스 톤)", "span":null, "maps_to":"tonedown"}],
  "situation_markers": [
    {"token":"2006년 12월 24일", "span":[0,10], "maps_to":"Dec 24 2006"},
    {"token":"크리스마스 이브", "span":[11,17], "maps_to":"Christmas Eve"}
  ],
  "motion_markers": [],
  "visual_requirement_ko": "2006년 12월 24일 크리스마스 이브 피닉스 야경"
}
```

- `span`: 대본 원문 내 character offset (추적용)
- `maps_to`: 에이전트가 소비할 canonical form (영문 / preset enum)

### 대본 밖 요소 추가 금지 (위반 예시)

| 대본 원문 | 금지된 에이전트 해석 (대본 밖) | 허용된 해석 (대본 markers 내) |
|----------|---------------------------|--------------------------|
| "크리스마스 이브 피닉스입니다" | "1980년대 네온사인 거리" (시대 착오) | "크리스마스 등 달린 야경" (대본 situation 그대로) |
| "형사는 여섯 시간을 몰아붙였고" | "경찰차 사이렌 울리며" (대본 없음) | "취조실에서 6시간 경과 + 압박" (대본 motion+situation) |
| "진범은 이미 피닉스를 벗어나고" | "고속도로 폭발" (대본 없음) | "실루엣 야간 도주" (대본 motion) |

### 구현 강제 수단

1. **shot-planner / scripter AGENT.md** — emotion/situation/motion markers 필드 output 강제
2. **asset-sourcer / video-producer / subtitle-producer** — markers 를 search keyword / i2v prompt / subtitle cue 로 변환 (canonical form 사용)
3. **ins-narrative-quality** 검증 — `visual_requirement_ko` 의 모든 단어가 markers 의 `token` + `maps_to` 에서 파생됐는지 assertion
4. **ins-mosaic / 영상 검수** — final 영상 요소 중 대본 marker 외 추가 요소 검출 시 FAIL

## Why

Ryan Waller v3.2 실패 7지적의 배경 root cause 중 하나:
- "대본에 담배를 피고있다고하면 담배를 피는 영상이 나와야 한다" — 대표님 2026-04-23
- "크리스마스라는 것 때문에 [집 영상을] 하루종일 틀고있노" — 대본의 "크리스마스 이브" 는 시점 표식이지 장면 전체가 아닌데 에이전트가 전체 장면으로 확대 해석

Rule 1 (대본 읽기) + Rule 2 (대본 그대로 반영) 은 세트로 작동. Rule 1 만으로는 에이전트가 "읽기만" 하고 자체 해석 추가 가능 → Rule 2 로 "읽은 내용만 반영" 강제.

## How to apply

- **scripter 단계**: narration 생성 + 각 section/shot 의 markers 자동 추출 (token + span + maps_to)
- **shot-planner**: section 을 shot 으로 분할 시 markers 를 shot 단위로 재분배
- **asset-sourcer**: search_keywords = situation_markers.maps_to + 고유명사만 (대본 외 추가 금지)
- **video-producer**: i2v_prompt = motion_markers.maps_to + situation_markers.maps_to (영문 template) 만 조합
- **voice-producer**: emotion_preset = emotion_markers.maps_to (Typecast enum) 으로 직접 매핑
- **subtitle-producer**: cue 는 shot.text substring 그대로 (marker-based chunk 분할 권장)

## 검증

```python
# assertion 예: visual_requirement_ko 가 markers 에서만 파생 여부
import json, re
shot = json.load(open('output/<ep>/script.json'))['sections'][0]['shots'][0]
vocab = set()
for m_list in (shot['emotion_markers'], shot['situation_markers'], shot['motion_markers']):
    for m in m_list:
        vocab |= set(re.findall(r'\S+', m['token'] + ' ' + m.get('maps_to','')))
for word in re.findall(r'\S+', shot['visual_requirement_ko']):
    assert any(word in v for v in vocab), f"외부 요소 '{word}' in visual_requirement_ko"
```

## Cross-reference

- `feedback_every_agent_reads_script_first.md` (Rule 1 — 선행 조건)
- `feedback_agents_require_visual_analysis.md` (Rule 3 — 시각 검증)
- `feedback_hook_visual_brief_not_extended.md` (전단계 박제)
- `feedback_shot_level_context_sync.md` (전단계 박제, 본 Rule 2 가 상위 규칙)
