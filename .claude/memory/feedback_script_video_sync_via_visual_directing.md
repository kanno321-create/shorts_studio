---
name: feedback_script_video_sync_via_visual_directing
description: script.json section 마다 `visual_directing` 필드 필수. 영상/이미지 매핑의 SSOT. 대본과 영상이 따로 놀면 시청자가 영상에서 사건 파악 불가.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/script.json (reference — section 마다 visual_directing 필드 존재)
  - output/ryan-waller/script.json (v2 — visual_directing 필드 없음)
  - output/ryan-waller/script_v3.json (v3 — 9 section 전수 visual_directing 포함)
failure_mapping:
  - FAIL-v2-대본영상_따로놈: "대본이랑 영상이랑 따로놀잖아" (대표님 직접 판정)
---

# feedback: script.json 의 visual_directing 필드 = 영상 매핑 SSOT

## 규칙

**script.json 의 각 section 에 `visual_directing` 필드 필수.** 해당 section 의 narration 이 말하는 내용을 영상이 직접 표현하도록 directing 문장을 배치. 이 필드가 footage sourcing / visual_spec_builder / asset selection 의 **단일 진실 소스 (SSOT)**.

### 올바른 구조 (v3, reference 모방)

```json
{
  "section_id": "body_scene",
  "narration": "희생자는 스물한 살 헤더 콴이었습니다. 피닉스 자택에서 총에 맞아 숨진 채 발견됐죠...",
  "visual_directing": "피닉스 교외 주택 내부 어두운 거실 → 바닥 피해자 실루엣 → 의자에 앉은 Ryan 피 묻은 얼굴 → CCTV 정면 샷"
}
```

### 위반 구조 (v2 — 필드 없음)

```json
{
  "id": "conflict",
  "sentences": [
    {"text": "크리스마스 밤, 집 안에서, 여자친구가 총에 맞아 숨졌습니다.",
     "visual_cue": "crime_scene_exterior_night"}  // scene-level 단독 키워드만
  ]
}
```

→ scene-level `visual_cue` (1-2 단어) 만으로는 footage sourcing 이 올바른 영상을 찾지 못함. 결과: gpt-image-2 가 일반 누와르 이미지 생성 → 대본 내용 (크리스마스 밤 살인) 과 무관한 영상.

### directing 문구 작성 규칙

- **한국어 + 구체 고유명사** 혼합 가능 (Phoenix, Ryan, CCTV 등)
- **장면 전환 `→` 로 순서 표시** (예: "주택 외관 → 내부 거실 → Ryan 클로즈업")
- **카메라 앵글/조명 단서** 포함 ("CCTV 와이드샷", "형광등", "탐정 실루엣")
- **시대 / 장소 / 인물** 명시 (reference zodiac 의 "1960년대 캘리포니아 밤 호숫가")

## Why

세션 #34 대표님 판정: "대본이랑 영상이랑 따로놀잖아… 영상은 그냥 아무거나 같다 붙혀서 이어 놓기만하고, 나레이션은 대본만 읽고있으니 서로 따로놀고있어".

원인 = v2 script 에 section-level directing 부재. 결과: footage sourcing 키워드가 일반적 누와르만 반환, Kling I2V prompt 도 section-agnostic.

Reference zodiac-killer/mary-celeste 등은 모든 section 에 directing 필드 존재 → asset 이 narration 내용과 직접 동기화.

## How to apply

- **scripter 에이전트 작성 시**:
  - 모든 section 에 `visual_directing` 필드 생성 (빈 값 금지)
  - narration 의 핵심 fact (인물·사건·장소) 를 시각화할 구체 directing 배치
- **source_*_footage.py CLI 의 search query**:
  - section.visual_directing 에서 tokenize 하여 query 구성
  - Ryan Waller 같이 영어권 사건은 한국어+영어 하이브리드 쿼리
- **build_*_visual_spec.py 측**:
  - section_id → clip 매핑 테이블에 visual_directing 내용 반영
  - real footage 가 없으면 directing 문구를 Kling I2V prompt seed 로 활용
- **ins-narrative-quality / ins-mosaic 측**:
  - section 마다 visual_directing 존재 + ≥20자 체크

## 검증

```bash
python -c "
import json
d = json.load(open('output/<episode>/script_v3.json'))
missing = [s['section_id'] for s in d['sections'] if not s.get('visual_directing','').strip()]
assert not missing, f'sections missing visual_directing: {missing}'
avg_len = sum(len(s['visual_directing']) for s in d['sections'])/len(d['sections'])
assert avg_len >= 20, f'directing too short on average: {avg_len}'
print(f'✅ visual_directing OK for all {len(d[\"sections\"])} sections (avg {avg_len:.0f} chars)')
"
```

## Cross-reference

- `feedback_script_section_paragraph_not_sentences` (schema 전환)
- `feedback_multi_source_video_search_required` (directing → search query)
- reference: `shorts_naberal/output/zodiac-killer/script.json` (visual_directing 필드 존재)
- Ryan Waller v2 FAIL — 세션 #34 대표님 판정
