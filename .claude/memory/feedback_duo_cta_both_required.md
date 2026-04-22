---
name: feedback_duo_cta_both_required
description: Aftermath 섹션은 탐정 CTA + 왓슨 CTA 양쪽 필수 (Hook 의 왓슨 질문 + 탐정 답변 대칭). 탐정 단독 CTA 는 미완성.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/script.json (v1 — aftermath 에 탐정 CTA 만, 왓슨 CTA 누락)
  - .claude/memory/feedback_detective_exit_cta.md (탐정 10 pool)
  - .claude/memory/feedback_watson_cta_pool.md (왓슨 10 pool)
  - .preserved/harvested/output/zodiac-killer/final.mp4 (reference — 탐정 + 왓슨 CTA 둘 다 포함)
failure_mapping:
  - FAIL-5-v1: 아웃로에 탐정 CTA 만, 왓슨 (웰시 코기) CTA 누락
---

# feedback: duo CTA = 탐정 + 왓슨 양쪽 필수 (한쪽만 = 실패)

## 규칙

**incidents 채널 aftermath 섹션은 "탐정 CTA + 왓슨 CTA" 두 문장이 **필수 짝**.** Hook 의 duo 패턴 (왓슨 질문 → 탐정 답변) 이 Aftermath 에서도 대칭 (탐정 CTA → 왓슨 CTA) 으로 유지된다. 한쪽만 있으면 구조 미완성.

### 구조 패턴 (대칭)

| 섹션 | 첫 화자 | 두 번째 화자 | 기능 |
|------|---------|-------------|------|
| Hook (0-9s) | assistant (왓슨) — 질문 | narrator (탐정) — 답변 | 청자 introduction |
| Aftermath (마지막 ~15-17s) | narrator (탐정) — CTA | **assistant (왓슨) — CTA** | 청자 farewell + 구독 유도 |

### pool 참조

- 탐정 CTA: `feedback_detective_exit_cta.md` 10 pool 에서 rotation
- 왓슨 CTA: `feedback_watson_cta_pool.md` 10 pool 에서 rotation
- **식상한 반복 금지** — 동일 문장 ≥3회 연속 사용 시 Inspector ins-narrative-quality 가 reject
- 왓슨 CTA 는 탐정 CTA 톤 (무게감) 에서 자연 전환 — 급 friendly 금지

### 위반 예시 (v1)

```json
// script.json aftermath sentences
[
  {"speaker_id": "narrator", "text": "뇌 일부와 왼쪽 눈을 잃고..."},
  {"speaker_id": "narrator", "text": "유족의 소송은, 기각되었죠."},
  {"speaker_id": "narrator", "text": "진실은 때로, 너무 늦게 도착합니다."}  // 탐정 CTA — 여기서 끝남 (왓슨 CTA 누락 🔴)
]
```

### 올바른 구조 (v2)

```json
[
  {"speaker_id": "narrator", "text": "뇌 일부와 왼쪽 눈을 잃고..."},
  {"speaker_id": "narrator", "text": "유족의 소송은, 기각되었죠."},
  {"speaker_id": "narrator", "text": "진실은 때로, 너무 늦게 도착합니다.", "cta_pool_ref": "feedback_detective_exit_cta#9"},
  {"speaker_id": "assistant", "text": "다음 기록도 함께 펼쳐 보시죠.", "cta_pool_ref": "feedback_watson_cta_pool#5"}  // ✅ 왓슨 CTA 추가
]
```

## Why (왜)

세션 #33 Ryan Waller v1 에서 내가 aftermath 마지막 문장을 탐정 (narrator) CTA 로 끝냄. `feedback_watson_cta_pool` 메모리 존재를 인지했으나 "CTA = 탐정 1명" 으로 착각. 채널바이블 `project_channel_bible_incidents_v1` §10 명시: 탐정 pool 10 + **왓슨 pool 10 모두 박제** — 양쪽 사용 의무.

대표님 판정: "마지막 탐정의 cta, 조수 강아지의 cta를 왜 빼먹노" + zodiac-killer/final.mp4 참조 → 해당 레퍼런스에서 탐정 퇴장 후 왓슨 follow-up CTA 1문장 있음.

## How to apply (언제 적용)

- **scripter 에이전트가 aftermath 섹션 작성 시 체크리스트**:
  1. 마지막 2 sentence = (narrator CTA) + (assistant CTA)
  2. 각 CTA 는 해당 pool 에서 선택 (`cta_pool_ref` 필드 필수)
  3. 왓슨 CTA 는 탐정 CTA 의 무게감을 이어받되 톤 전환 (micro-friendly) — 급전환 금지
- **voice-producer 가 TTS 생성 시**:
  - 탐정 CTA: Typecast Morgan + emotion=sad/tense
  - 왓슨 CTA: Typecast Risan Ji (또는 Guri) + emotion=urgent/normal
- **ins-narrative-quality 검증**:
  - aftermath 의 마지막 2 sentence speaker_id sequence = `["narrator", "assistant"]`
  - 둘 다 `cta_pool_ref` 필드 있음
  - pool 의 실제 문장과 일치 (±3자 허용)

## 검증

```bash
# 1. script.json aftermath sentences 의 speaker 시퀀스 검증
python -c "
import json, sys
data = json.load(open('output/ryan-waller/script.json'))
after = [s for s in data['sections'] if s['id']=='aftermath'][0]
speakers = [s['speaker_id'] for s in after['sentences']]
assert speakers[-2:] == ['narrator', 'assistant'], f'duo CTA missing: {speakers}'
print('✅ duo CTA 구조 OK')
"

# 2. cta_pool_ref 필드 필수
python -c "
import json
data = json.load(open('output/ryan-waller/script.json'))
after = [s for s in data['sections'] if s['id']=='aftermath'][0]
last_two = after['sentences'][-2:]
for s in last_two:
    assert 'cta_pool_ref' in s, f'missing cta_pool_ref: {s}'
print('✅ cta_pool_ref 전수')
"
```

## Cross-reference

- `feedback_detective_exit_cta` — 탐정 10 pool + rotation 원칙
- `feedback_watson_cta_pool` — 왓슨 10 pool
- `project_channel_bible_incidents_v1` §10
- `.preserved/harvested/output/zodiac-killer/final.mp4` — duo CTA 구현 레퍼런스
- 세션 #33 Ryan Waller v1 FAIL-5
