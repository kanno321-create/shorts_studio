---
name: feedback_subtitle_short_chunks_2_4_words
description: 자막 cue 1개는 2-4 단어 / ≤12자. sentence-level (20-30자) 는 1080×1920 / 68pt 폰트에서 자동 2-line wrap → 가독성 실패.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/subtitles_remotion.json (184 cue, avg 2-4 단어)
  - output/ryan-waller/subtitles_remotion.json (v2 — 20 sentence-level cue, 2-line wrap)
  - output/ryan-waller/subtitles_remotion_v3.json (v3 — 71 cue, avg 2.6 단어)
failure_mapping:
  - FAIL-v2-자막_2줄_wrap: "자막이 두 줄로 내려와서 못 읽겠다" (대표님 직접 판정)
---

# feedback: 자막 cue = 2-4 단어 / ≤12자

## 규칙

**subtitles_remotion.json cues[] 각 cue 는 2-4 단어 / ≤12자 / ~10자 avg**. Reference zodiac-killer 184-cue 스타일. Sentence-level (문장 전체) cue 는 Remotion 68pt 폰트 + 1080px 폭에서 자동 2-line wrap → 가독성 실패.

### 올바른 chunking (v3)

```json
{
  "cues": [
    {"start_s": 0.0, "end_s": 1.2, "text": "2006년 12월 24일", "words": ["2006년", "12월", "24일"]},
    {"start_s": 1.2, "end_s": 2.4, "text": "크리스마스 이브", "words": ["크리스마스", "이브"]},
    {"start_s": 2.4, "end_s": 3.6, "text": "애리조나 피닉스입니다", "words": ["애리조나", "피닉스입니다"]}
  ]
}
```

avg words/cue: 2.6 / avg chars: 10.2 / Remotion 1-line 가독.

### 위반 chunking (v2)

```json
{
  "cues": [
    {"start_s": 0.0, "end_s": 2.4,
     "text": "저 용의자, 완전 약에 취한 거 아닙니까?"}
  ]
}
```

20자 → Remotion auto-wrap 2-line → 대표님 "못 읽겠다".

## chunking 알고리즘 (권장)

```python
MAX_CHARS_PER_CUE = 12
MAX_WORDS_PER_CUE = 4
MIN_WORDS_PER_CUE = 2

def chunk_words(words):
    chunks, current = [], []
    for w in words:
        trial = current + [w]
        if len(trial) > MAX_WORDS_PER_CUE or char_len(trial) > MAX_CHARS_PER_CUE:
            chunks.append(current); current = [w]
        else:
            current = trial
    if current: chunks.append(current)
    # tail-merge under-min
    if len(chunks) >= 2 and len(chunks[-1]) < MIN_WORDS_PER_CUE:
        chunks[-2] += chunks.pop()
    return chunks
```

Section duration 은 각 그룹의 character length 비례 분배 (sum(len) 가중치).

## Why

세션 #34 v2 대표님 판정: "자막이 두 줄로 내려와서 못 읽겠다". 68pt 한국어 폰트 x 1080 px 폭 기준 한 줄에 ~16자 수용. 20+자 = wrap 강제.

Reference 영상 (zodiac 184 cue) 는 처음부터 2-4 단어 chunk 로 생성되어 1-line 유지.

## How to apply

- **subtitle-producer / generate_*_subtitles 스크립트 에서**:
  - 공백 split → 2-4 단어 group → ≤12자 guard → 비례 시간 분배
  - faster-whisper word-level timing 가능하면 그것 기반, 아니면 fallback chunking
- **ins-subtitle-alignment 검증**:
  - cues 배열의 avg chars/cue ≤ 12
  - max chars/cue ≤ 16 (tail 허용)
  - avg words/cue ∈ [2, 4]

## 검증

```bash
python -c "
import json
d = json.load(open('output/<episode>/subtitles_remotion_v3.json'))
cues = d['cues']
avg_chars = sum(len(c['text']) for c in cues)/len(cues)
max_chars = max(len(c['text']) for c in cues)
avg_words = sum(len(c.get('words', c['text'].split())) for c in cues)/len(cues)
assert avg_chars <= 12, f'avg chars too high: {avg_chars}'
assert max_chars <= 16, f'max chars too high: {max_chars}'
assert 2 <= avg_words <= 4, f'avg words out of range: {avg_words}'
print(f'✅ subtitle chunks OK ({len(cues)} cues, avg {avg_words:.1f}w/{avg_chars:.1f}c)')
"
```

## Cross-reference

- `feedback_subtitle_semantic_grouping` (의미 단위 보존)
- `feedback_number_split_subtitle` (숫자+단위 한 단어)
- reference: `shorts_naberal/output/zodiac-killer/subtitles_remotion.json`
- Ryan Waller v2 FAIL — 세션 #34 대표님 판정
