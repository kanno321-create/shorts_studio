---
name: feedback_script_section_paragraph_not_sentences
description: script.json 은 sections[] flat array + section 당 narration 단일 문단 (reference zodiac-killer 모방). sentences[] 배열 금지 — TTS 조각화로 로봇 낭독 유발.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/script.json (reference SSOT)
  - output/ryan-waller/script.json (v2 실패 — sentences[] 분해 구조)
  - output/ryan-waller/script_v3.json (v3 성공 구조)
failure_mapping:
  - FAIL-v2-나레이션_영혼없음: TTS 20회 조각 호출 + 매번 silence 400-700ms → 호흡 끊김
  - FAIL-v2-한단어씩_쉼: 문장 조각마다 gap 삽입 → 자연 흐름 파괴
---

# feedback: script.json = section-paragraph 구조 (sentences[] 금지)

## 규칙

**script.json 은 sections[] flat array + 각 section 에 `narration` 단일 문단 필드.** sentences[] 배열로 분해하면 TTS 가 문장 조각마다 호출되어 prosody 연속성이 깨지고 "한 단어씩 쉬면서 국어책 읽기" 현상 발생.

### 올바른 schema (v3, reference 모방)

```json
{
  "sections": [
    {
      "section_id": "hook",
      "section_type": "hook",
      "speaker_id": "narrator",
      "narration": "100+ 자 문단 전체 — TTS 가 한 번에 합성",
      "emotion": "tense",
      "silence_after_ms": 600,
      "visual_directing": "장면 directing 구체 문구"
    }
  ]
}
```

### 금지 schema (v2 실패)

```json
{
  "sections": [
    {
      "id": "hook",
      "sentences": [
        {"speaker_id": "assistant", "text": "...", "silence_after_ms": 300},
        {"speaker_id": "narrator", "text": "...", "silence_after_ms": 400}
      ]
    }
  ]
}
```

### TTS 호출 방식 (연동 규칙)

- section 당 1 Typecast API call (narration 필드 전체를 text 로)
- silence 는 section 말미 silence_after_ms 만 삽입 (300-700ms)
- 문장 간 silence 0 — Typecast native pause 가 구두점에서 자연 pause 생성

## Why

세션 #33~34 v2 Ryan Waller 쇼츠 실패 판정. 근본 원인 = sentences[] 로 분해한 script 가 20회 TTS 호출 + 매회 silence 삽입 → 대표님 "한 단어씩 쉬면서 국어책 읽기" 감지.

Reference zodiac-killer/elisa-lam/mary-celeste 등은 모두 sections[].narration 단일 문단 구조. v3 에서 이 구조 회복 후 TTS 호출 20회 → 9회, silence 총량 대폭 축소.

## How to apply

- **scripter / script-polisher 에이전트가 script 작성 시**:
  - `sections[]` flat array 만 사용
  - 각 section 에 `narration` (문단), `speaker_id`, `emotion`, `silence_after_ms`, `visual_directing` 필드 배치
  - sentence 단위 분해 절대 금지
- **voice-producer / TTS 호출 측**:
  - section 당 1회 호출 (narration 필드 → text 인자)
  - silence 는 section 말미만
- **ins-schema-integrity** 에서 검증:
  - `sections[i].narration` 존재 + string (≥30자)
  - `sections[i].sentences` 필드 **부재** (있으면 FAIL)

## 검증

```bash
# script.json 이 sentences[] 쓰는지 체크
python -c "
import json
d = json.load(open('output/<episode>/script.json'))
for s in d['sections']:
    assert 'narration' in s and isinstance(s['narration'], str), f'missing narration: {s}'
    assert 'sentences' not in s, f'sentences[] forbidden in: {s[\"section_id\"]}'
print('✅ section-paragraph schema OK')
"
```

## Cross-reference

- `feedback_narration_text_only_no_meta` (text 필드 clean 룰)
- `feedback_typecast_ssml_literal_read` (SSML 주입 금지)
- `feedback_hook_context_30s_rule` (hook 문단 내 구체 fact 필수)
- reference: `shorts_naberal/output/zodiac-killer/script.json`
- Ryan Waller v2 FAIL — 세션 #34 대표님 판정
