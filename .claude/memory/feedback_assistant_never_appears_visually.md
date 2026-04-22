---
name: feedback_assistant_never_appears_visually
description: 조수(왓슨) 캐릭터는 **영상에 절대 등장 금지**. 음성과 자막으로만 존재. 상단 overlay (Remotion character badge) 는 모든 구간 고정 노출이므로 별도 scene clip 생성 불필요.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/script_v3.json watson_q1 / watson_q2 / aftermath_watson
  - scripts/experiments/build_ryan_waller_visual_spec_v3.py SECTION_FALLBACK (v3.1 에서 교정 예정)
failure_mapping:
  - FAIL-v3-watson_shot_생성: watson_q1/q2 section 에 character_assistant.png 를 Ken Burns clip 으로 배치 → 조수가 영상 scene 에 등장 (대표님 "조수는 절대 영상에 등장하지 않는다")
---

# feedback: 조수(왓슨) 영상 등장 금지

## 규칙

**assistant / watson 화자의 narration 에 대해 별도 scene clip 을 만들지 말 것.** 왓슨 음성 + 자막은 정상, 하지만 **scene-level 영상 (mp4/png/Kling)** 에 웰시 코기 혹은 조수 캐릭터가 등장해서는 안 됨.

### 왜 별도 clip 이 불필요한가

Remotion `ShortsVideo` 의 상단 bar 에 `characterLeftSrc` (character_assistant.png) 가 **모든 프레임 overlay** 되어 항상 노출. 따라서 watson 발화 구간에도 조수 배지는 이미 보임. scene clip 에 또 배치하면 화면 중앙까지 조수가 크게 보여 "조수 scene" 인상을 줌.

### watson section 영상 처리 원칙

| section 성격 | 올바른 scene 영상 |
|-------------|------------------|
| watson 의 의문 (예: "왜 여섯 시간이나?") | 직전 narrative 영상 **연장** (scene transition 유지) |
| watson 의 놀람/감탄 | 직전 narrative clip 의 close-up 또는 B-roll 삽입 |
| aftermath_watson (final CTA) | 탐정 outro_signature.mp4 연장 or 제품 관련 타이틀 카드 |

### 구조 패턴

- **watson 발화 = 청자 대리 질문** (nar narrative 의 리액션)
- → 시청자 시선 유지 = **같은 장면 유지** 또는 약간 변화 (pan, crop-in)
- → 조수가 튀어나오면 시청자가 "왜 갑자기 강아지?" 로 몰입 깨짐

### 위반 예시 (v3)

```python
# build_ryan_waller_visual_spec_v3.py
SECTION_FALLBACK: dict[str, str] = {
    "watson_q1": "character_assistant.png",  # ❌ 조수가 영상 scene 에 등장
    "watson_q2": "character_assistant.png",  # ❌
    "aftermath_watson": "character_assistant.png",  # ❌
}
```

### 올바른 매핑 (v3.1 이후)

```python
SECTION_FALLBACK: dict[str, str] = {
    # watson 은 narrative section 의 scene 을 시각적으로 이어감
    "watson_q1": None,  # → 직전 hook clip 연장
    "watson_q2": None,  # → 직전 body_6hours clip 연장
    "aftermath_watson": "outro_signature.mp4",  # 탐정 outro 연장
}
```

빌더 측에서 `None` 만나면 직전 clip 의 durationInFrames 를 늘려 흡수.

## Why

세션 #34 v3 대표님 직접 판정 (2026-04-23): "조수는 절대 영상에 등장하지 않는다".

내가 v3 에서 watson 짧은 section (2-3s) 을 "독립 shot" 으로 처리하려 character PNG 를 Ken Burns clip 으로 배치 → 화면 절반 크기 조수 등장. 이는:
1. 시청자 몰입 끊김 (갑자기 강아지)
2. 조수 = 청자 대리 역할 (감정이입용) → 시각화하면 역할 무너짐
3. Remotion 상단 overlay 에 이미 조수 배지 있음 → 중복 + 어색

Reference zodiac-killer / mary-celeste 의 assistant 발화 section 비주얼 매핑 확인 결과 모두 **narrative scene 유지**, 조수 독립 clip 없음.

## How to apply

- **visual_spec_builder / sources_manifest 구성 시**:
  - assistant speaker section 은 별도 scene_source 배정 금지
  - 직전 narrator section 의 clip 을 연장 (durationInFrames 합산)
  - 또는 aftermath_watson 같이 section 이 길면 outro_signature 사용
- **shot-planner 에이전트 규칙**:
  - shot breakdown 시 assistant turn 은 shot 생성 하지 않음
  - `speaker_id == 'assistant'` 인 sentence 는 직전 shot 의 tail 로 흡수
- **ins-mosaic / ins-narrative-quality 검증**:
  - scene_sources 에서 character_assistant.png / character_detective.png 등장 0건 확인 (캐릭터 PNG 는 상단 bar 용으로만 public/ 에 배치)

## 검증

```bash
python -c "
import json
m = json.load(open('output/<episode>/sources_manifest_v3.json'))
bad = [s for s in m.get('scene_sources', []) if 'character_' in s]
assert not bad, f'character PNG leaked into scene_sources: {bad}'
print('✅ no character leak in scene_sources')
"
```

## Cross-reference

- `feedback_duo_cta_both_required` (duo 구조: 음성 + 자막만)
- `feedback_script_video_sync_via_visual_directing` (대본-영상 동기화)
- `reference_signature_and_character_assets` section 2 (character 용도 = top bar overlay)
- 세션 #34 v3 FAIL — 대표님 직접 판정
