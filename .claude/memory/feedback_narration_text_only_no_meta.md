---
name: feedback_narration_text_only_no_meta
description: script.json 의 `text` 필드는 TTS 에 그대로 전달되는 **발화 텍스트만** — emotion/visual_cue/citation_ref 는 metadata, 절대 text 에 포함 금지.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/narration.mp3 (v1 — 감정선/괄호/슬래시 낭독됨)
  - output/ryan-waller/script.json (v1 — text 필드는 OK 했으나 SSML 오염이 추가됨)
failure_mapping:
  - FAIL-1-v1: 대본의 감정선/슬래시/괄호 그대로 낭독 (근본 원인 = SSML 오염, 보조 원인 = script text 필드 sanitize 부재)
---

# feedback: narration text = 발화 텍스트만 (meta 혼입 금지)

## 규칙

**`script.json` sentence 의 `text` 필드는 TTS 에 그대로 입력되는 발화 텍스트만.** 감정 지시, 비주얼 큐, citation 번호, SSML 태그, 괄호 주석 등 metadata 는 **다른 필드** (emotion, visual_cue, citation_ref, silence_after_ms) 에 분리. `text` 에 혼입 시 literal 낭독 발생.

### 올바른 구조

```json
{
  "speaker_id": "narrator",
  "text": "크리스마스 밤, 집 안에서, 여자친구가 총에 맞아 숨졌습니다.",  // ✅ 순수 발화
  "emotion": "tonedown",                                                   // ✅ 별도 필드
  "visual_cue": "crime_scene_exterior_night",                              // ✅ 별도 필드
  "citation_ref": "nlm_facts:1",                                           // ✅ 별도 필드
  "silence_after_ms": 400                                                  // ✅ 별도 필드
}
```

### 위반 예시 (금지)

```json
// ❌ text 에 감정 지시 혼입
{"text": "(슬프게) 크리스마스 밤, 여자친구가 총에 맞아 숨졌습니다."}

// ❌ text 에 비주얼 큐 혼입
{"text": "크리스마스 밤 / [CCTV 블러] / 여자친구가 총에 맞아 숨졌습니다."}

// ❌ text 에 citation 숫자 혼입
{"text": "크리스마스 밤, 여자친구가 총에 맞아 숨졌습니다. [1]"}

// ❌ text 에 SSML 혼입 (이것이 세션 #33 root cause)
{"text": "크리스마스 밤,<break time=\"0.2s\"/> 여자친구가 총에 맞아 숨졌습니다."}

// ❌ text 에 감독 주석 혼입
{"text": "크리스마스 밤, 여자친구가 총에 맞아 숨졌습니다. // (긴 포즈)"}
```

### TTS 엔진별 SSML 지원 매트릭스

| Provider | Model | SSML 지원 | 비고 |
|----------|-------|-----------|------|
| Typecast | ssfm-v30 | ❌ 미지원 | literal 낭독 |
| ElevenLabs | turbo v2.5 | ⚠️ 일부 (break, phoneme) | `enable_ssml` 플래그 필요 |
| Edge TTS | Azure | ✅ 지원 | `<speak>` wrapper 권장 |
| OpenAI TTS | tts-1-hd | ❌ 미지원 | plain text only |

**기본 원칙**: SSML 은 provider-specific opt-in. script.json level 에서는 **절대 포함 금지** (범용 schema).

## Why (왜)

세션 #33 Ryan Waller v1 의 FAIL-1 은 두 단계 혼입:
1. script.json text 필드는 깔끔했음 (이 부분은 OK)
2. 하지만 `typecast.py:_inject_punctuation_breaks()` 가 TTS 직전 `<break/>` SSML 주입 → literal 낭독

즉, script.json 자체는 clean 해도 하류 adapter 에서 SSML 오염 가능. 이를 방지하려면:
- (A) script.json 단계 schema 검증 (SSML regex 차단)
- (B) TTS adapter 단계 provider-specific SSML gating (Typecast 는 무조건 strip)

이 메모리는 (A) + (B) 양쪽 원칙 박제.

## How to apply (언제 적용)

- **scripter / script-polisher 에이전트가 text 필드 작성 시**:
  - 감정/비주얼/citation/silence 정보는 **별도 필드**에 배치
  - `text` 에는 실제로 소리내 읽을 한국어 문장만
  - 괄호 `( )` 사용은 OK (한국어 자연 표기) 이지만, 감독 주석이 아니라 부연 설명용만 허용
- **voice-producer / TTS adapter 호출 시**:
  - script.json 의 `text` 를 TTS 입력으로 **그대로 전달** — 추가 transform 금지
  - SSML pause 가 필요하면 script.json `silence_after_ms` 필드를 audio concatenation 단계에서 실제 AudioSegment 무음으로 변환
  - provider-specific SSML 은 `enable_ssml=True` 명시적 플래그로만 opt-in (기본 OFF)
- **ins-schema-integrity 검증**:
  - `text` 필드 regex `r"<\w+\s*[^>]*>"` 매칭 0건
  - `text` 필드 괄호 내용에 "슬프게|차갑게|빠르게|작게" 같은 감독 지시 키워드 0건

## 검증

```bash
# 1. script.json text 필드 SSML 오염 검사
python -c "
import json, re
data = json.load(open('output/ryan-waller/script.json'))
for sec in data['sections']:
    for s in sec['sentences']:
        assert not re.search(r'<\w+[^>]*>', s['text']), f'SSML in: {s[\"text\"]}'
        assert not re.search(r'\[\d+\]', s['text']), f'citation num in: {s[\"text\"]}'
print('✅ text 필드 clean')
"

# 2. generated narration.mp3 ear-verify (3초 샘플)
ffmpeg -i output/ryan-waller/narration.mp3 -t 5 -ss 5 /tmp/sample.mp3
# → 대표님 직접 청취
```

## Cross-reference

- `feedback_typecast_ssml_literal_read` — 관련 root cause (SSML injection 하류에서)
- `project_tts_stack_typecast` — TTS 스택 + SSML 지원 여부
- `project_channel_bible_incidents_v1` §6 (대본 규칙)
- 세션 #33 Ryan Waller v1 FAIL-1 / FAIL-2
