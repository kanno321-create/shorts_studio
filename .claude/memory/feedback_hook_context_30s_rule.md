---
name: feedback_hook_context_30s_rule
description: hook section 에는 날짜·장소·인원·숫자 등 구체 fact 1+ 필수. 추상적 의문문만으로는 시청자 30초 안에 사건 파악 불가.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/script.json (v2 hook 실패 — "저 용의자 약에 취한 거 아닙니까?")
  - output/ryan-waller/script_v3.json hook (v3 — "2006년 12월 24일 크리스마스 이브. 애리조나 피닉스. 열여덟 살...")
  - C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/script.json hook (reference — "63개 기호, 51년, 조롱 메시지")
failure_mapping:
  - FAIL-v2-인트로_맥락부재: "뭘 말하려나 모르겠다" (대표님 직접 판정)
---

# feedback: hook 30초 컨텍스트 룰

## 규칙

**hook section 의 narration 문단은 사건을 특정하는 **구체 fact 최소 3개** 포함.** 추상적 의문/훅 문장만으로는 시청자가 30초 안에 "무슨 사건인지" 파악 불가 → 이탈률 상승.

### 구체 fact 카테고리 (최소 3개 이상)

1. **날짜/시점** — "2006년 12월 24일", "1986년 3월"
2. **장소** — "애리조나 피닉스", "캘리포니아 호숫가"
3. **인원/피해 규모** — "열여덟 살 남자친구", "5명 피살", "37명 주장"
4. **사건 특성 숫자** — "여섯 시간 취조", "51년 미제", "63개 기호"
5. **핵심 고유명사** — "Zodiac Killer", "헤더 콴", "카버 부자"

### 올바른 hook (v3)

> "2006년 12월 24일 크리스마스 이브. 애리조나 피닉스입니다. 열여덟 살 남자친구가 피를 흘리며 멍하니 앉아 있었습니다. 옆에는 스물한 살 여자친구의 시신. 형사는 여섯 시간을 몰아붙였고 의료진은 단 한 번도 부르지 않았습니다. 그러나 진실은 전혀 달랐습니다. 오늘의 기록."

→ 포함: 2006 / 12월 24일 / 피닉스 / 18세 / 21세 / 여섯 시간 / 시그니처 "오늘의 기록"

### 위반 hook (v2)

> (왓슨) "저 용의자, 완전 약에 취한 거 아닙니까?"
> (narrator) "오늘의 기록. 2006년, 피닉스."

→ 왓슨 질문만 + 연도·장소 단편만. 사건 개요 (용의자 정체, 피해 규모, 상황) 전달 0.

### Reference (zodiac-killer)

> "이 암호에는 63개의 기호가 쓰여 있습니다. 51년 동안 아무도 풀지 못했습니다. 풀렸을 때, 메시지는 조롱이었습니다... 오늘의 기록."

→ 63 기호 / 51년 / 조롱 / 시그니처 — 관객이 "암호가 안 풀린 미제 사건" 즉각 파악.

## Why

세션 #34 v2 대표님 판정: "인트로가 뭘 말하려나 모르겠다". hook 이 왓슨 의문 1 문장 + 날짜·장소 단편만 배치하면 "누가 / 무엇을 / 어떻게" 이해 불가.

Shorts 30초 rule — 30초 이내 사건 개요 파악 못하면 이탈. Reference 영상들이 hook 에 구체 fact 3-5개 배치하는 이유.

## How to apply

- **scripter 에이전트가 hook 작성 시 체크리스트**:
  - [ ] 날짜/시점 1개 이상
  - [ ] 장소 1개 이상
  - [ ] 인원·규모·핵심 고유명사 1개 이상
  - [ ] "오늘의 기록" 시그니처 포함 (channel-incidents)
  - [ ] 총 hook duration 9-15s 권장 (채널 preset)
- **ins-narrative-quality 검증**:
  - hook narration 정규식 체크: `r"(19|20)\d{2}년"` (날짜) AND `r"[가-힣]+시|[가-힣]+주"` (장소) 최소 1건씩 매치
  - 매치 0건이면 FAIL

## 검증

```bash
python -c "
import json, re
d = json.load(open('output/<episode>/script_v3.json'))
hook = [s for s in d['sections'] if s['section_id'] == 'hook'][0]
narr = hook['narration']
has_year = bool(re.search(r'(19|20)\d{2}\s*년', narr))
has_place = bool(re.search(r'[가-힣]{2,}(시|도|주|구|동)|(Phoenix|뉴욕|캘리포니아)', narr))
has_number = bool(re.search(r'\d+(\s*(명|살|번|시간|건|개))', narr))
count = sum([has_year, has_place, has_number])
assert count >= 2, f'hook context insufficient (has_year={has_year} place={has_place} num={has_number})'
print(f'✅ hook context OK ({count}/3 categories)')
"
```

## Cross-reference

- `feedback_script_section_paragraph_not_sentences`
- reference: `shorts_naberal/output/zodiac-killer/script.json` hook
- Ryan Waller v2 FAIL — 세션 #34 대표님 판정
