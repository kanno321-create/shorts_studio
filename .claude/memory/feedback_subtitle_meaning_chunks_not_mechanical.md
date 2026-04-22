---
name: feedback_subtitle_meaning_chunks_not_mechanical
description: 자막 cue 는 **의미 덩어리** 단위로 묶어야 함 — 수식어+명사, 서술어+목적어, 수+단위는 한 cue 안에. 공백 기반 2-4 단어 mechanic split 금지.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/subtitles_remotion_v3.json (v3 — 공백 split 결과 단어 분리)
  - scripts/experiments/generate_ryan_waller_subtitles_v3.py (mechanic chunking)
failure_mapping:
  - FAIL-v3-자막_단어분리: 대표님 "자막은 가독성이 좋아야한다. 두단어가 같이 보여야 이해가되는데 서로 떨어져있으니까 가독성이 나쁘다. 의미있는 구절끼리 한자막에 넣고해야된다"
---

# feedback: 자막 = 의미 덩어리 chunking (mechanic split 금지)

## 규칙

**자막 cue 는 읽는 사람이 그 단위 안에서 뜻을 이해할 수 있어야 한다.** 공백·단어수로만 쪼개면 수식어와 명사, 주어와 서술어가 분리돼 가독성 떨어짐.

### 위반 예시 (v3)

v3 narration:
> "2006년 12월 24일 크리스마스 이브. 애리조나 피닉스입니다. 열여덟 살 남자친구가 피를 흘리며 멍하니 앉아 있었습니다."

v3 chunking 결과 (공백 split 2-4 단어):
```
cue 1: "2006년 12월 24일"       ✓ (날짜 덩어리 OK)
cue 2: "크리스마스 이브."         ✓
cue 3: "애리조나 피닉스입니다."   ✓
cue 4: "열여덟 살"               ⚠️ (수+단위 OK 이지만 다음이 중요)
cue 5: "남자친구가 피를"          ❌ ("남자친구가" + "피를" — 주어 + 목적어 분리)
cue 6: "흘리며 멍하니"            ❌ (서술부속 + 부사 분리, 핵심 동사 없음)
cue 7: "앉아 있었습니다."         ⚠️ (동사 단독)
```

시청자가 cue 5 에서 "남자친구가 피를" 만 보면 의미 불완전. cue 6 에 "흘리며 멍하니" 는 독립적 의미 없음.

### 올바른 chunking (v3.1 이후)

```
cue A: "2006년 12월 24일"              (날짜)
cue B: "크리스마스 이브,"              (특이일)
cue C: "애리조나 피닉스."              (장소)
cue D: "열여덟 살 남자친구가"          (주어, 수식 포함)
cue E: "피를 흘리며"                   (동사구 1)
cue F: "멍하니 앉아 있었습니다."       (동사구 2, 서술 완결)
```

각 cue 가 **문법 완결성** 또는 **의미 완결성** 을 가짐.

### 의미 덩어리 규칙 (KR, 영화자막 표준 참조)

| 규칙 | 예 (OK) | 예 (NG) |
|------|---------|---------|
| 수식어 + 명사 | "열여덟 살 남자친구" | "열여덟 / 살 남자친구" |
| 수 + 단위 | "여섯 시간" | "여섯 / 시간" |
| 주어 + 조사 | "남자친구가" | "남자 / 친구가" |
| 동사구 하나 | "피를 흘리며" | "피를 / 흘리며" |
| 고유명사 | "애리조나 피닉스" | "애리조나 / 피닉스" |
| 시간 부사 | "그 시각" | "그 / 시각" |
| 문장 주요 관계 | "그러나 달튼은 연기라고 확신했죠" 한 cue (14자) 가능 | "그러나 / 달튼은 / 연기라고 / 확신했죠" 4분할 |

### chunking 알고리즘 개선안

1. 공백 split **후** 아래 우선순위로 **병합**:
   - (가) 조사 ("가/이/을/를/의/에/로/와") 가 붙은 단어는 다음 단어와 병합
   - (나) 수식어 ("이/그/저/들/많은/작은/긴/짧은") 는 다음 명사와 병합
   - (다) 수+단위 (숫자+"시간/살/개/명/건") 병합
   - (라) 고유명사 연속 ("애리조나 피닉스") 병합
2. 병합 후 ≤ 14자 / ≤ 5 단어 유지 (v3 의 ≤ 12 보다 관대, 의미 우선)
3. 과잉 long cue (>14자) 는 동사 앞에서 분할

### 제한

- `cue ≤ 5 단어 / ≤ 14 자` (reference zodiac ~3 단어 / ~10자 보다 약간 완화, 의미 유지 우선)
- cue 지속시간 ≥ 0.6s (너무 짧으면 안 읽힘)
- 1 cue 당 1 의미 단위 (혼합 금지)

## Why

세션 #34 v3 대표님 판정 원문:
> "자막은 가독성이 좋아야한다. 두단어가 같이 보여야 이해가되는데 서로 떨어져있으니까 가독성이 나쁘다. 의미있는 구절끼리 한자막에 넣고해야된다."

내가 reference zodiac 의 "2-4 단어" 를 공백·단어수로만 지키려 했음. reference 는 실제로 **의미 단위** 로 쪼개져 있음 (단순 공백 split 우연히 일치). 우리 script 는 어구가 길어서 공백 split 이 의미 분리.

## How to apply

- **subtitle-producer / generate_*_subtitles 스크립트 측**:
  - 단계 1: 공백 split (기존)
  - 단계 2: 한국어 조사·수식어 병합 필터 적용
  - 단계 3: ≤ 14 자 / ≤ 5 단어 범위에서 cue 완성
- **ins-subtitle-alignment 측 검증**:
  - cue 마지막 단어가 조사 (가/이/을/를/의/에) 로 끝나지 않음
  - cue 단독으로 명사·동사 함께 존재 (또는 명사구 완결)

## 검증

```bash
python -c "
import json, re
d = json.load(open('output/<episode>/subtitles_remotion_v3_1.json'))
# Heuristic: cue 가 조사로 끝나거나 수식어로 끝나면 warn
BAD_TAIL = re.compile(r'(가|이|을|를|의|에|으로|로|와|과|도|만|는|은)$')
SUFFIX = re.compile(r'(피를|그|저|이|그의|이런|저런)$')
violations = [c for c in d['cues'] if BAD_TAIL.search(c['text'].strip('.!?, '))]
print(f'{len(violations)}/{len(d[\"cues\"])} cues end in dangling particle (should be few)')
"
```

## Cross-reference

- `feedback_subtitle_short_chunks_2_4_words` — 상위 (단어 수 제한 여전히 유효, 의미 덩어리 우선)
- `feedback_subtitle_semantic_grouping` (기존 박제, v3.1 에서 확장)
- `feedback_number_split_subtitle` (숫자+단위 병합 규칙 포함)
- 세션 #34 v3 대표님 직접 판정
