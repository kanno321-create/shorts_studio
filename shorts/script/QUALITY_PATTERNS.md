---
category: script
status: ready
tags: [script-quality, patterns, narrative, style, reviewer-rubric]
sources: [shorts_naberal/longform/claudedocs/SCRIPT_QUALITY_GATE_CONTRACT.md]
session_origin: [세션 77 이전 합격 대본 3편 분석 박제 — setagaya-part1/2/3]
updated: 2026-04-20
---

# Script Quality Patterns A-D

**Scope:** shorts_studio SCRIPT gate 및 Reviewer rubric 의 단일 진실 원천. 대표님이 "올려도 될 정도"로 승인한 실제 대본 3편 (setagaya-part1/2/3, 100-126초) 패턴 분석 박제.

**사용처:**
- NLM Step 2 결과물 검증 (자체 점검 rubric)
- `ins-narrative-quality` Reviewer rubric 의 rule 집합
- `ins-readability` 문장 길이 리듬 체크
- `script-polisher` 자동 교정 규칙

---

## Pattern A — 씬 내부 흐름 공식

**공식:** `[세팅 문장] → [디테일 축적] → [여백 또는 전환] → [반전 또는 다음 씬 연결]`

합격 대본의 모든 Body 씬은 이 흐름 준수.

### 예시 1 (Part 1 Body 1)
```
[세팅]   "2000년 겨울, 도쿄 세타가야."
[디테일] "미야자와 미키오는 아이들에게 종이 인형을 만들어주는 다정한 아버지였습니다."
[축적]   "아내 야스코, 발레를 사랑하는 딸 니이나, 기차를 좋아하는 아들 레이."
[여백]   "평범하고 화목한 가족..."
[반전]   "하지만 누군가가 이 가족을 지켜보고 있었습니다."
```

### 예시 2 (Part 2 Body 5)
```
[세팅]   "범인은 전화선도 끊었습니다."
[반전]   "하지만 선을 자르거나 부순 게 아닙니다."
[디테일] "벽에서 조용히 뽑아두었습니다."
[추론]   "이 사소한 행동 하나가, 범인이 극도로 침착했음을 보여줍니다."
```

---

## Pattern B — 문장 길이 리듬 (실측 기반)

**공식:** 한 씬 안에서 문장 길이가 `짧(~15자) → 긴(25~40자) → 짧(~15자)` **파동**.

합격 대본 실측:
```
Part 1 Body 1: 12자 → 35자 → 28자 → 10자(여백) → 20자
Part 2 Body 1: 10자 → 28자 → 12자 → 18자
```

### 절대 금지
- 같은 길이(10-15자) 문장 **3개 이상 연속** — 이게 "로봇 느낌"의 원인
- 전체가 짧은 펀치 (과적용)

### Reviewer 체크
- `ins-readability` 가 segment 단위로 실측: 3개 연속 같은 길이 발견 시 FAIL + VQQA remediation_hint = "문장 길이 파동 복원 필요"

---

## Pattern C — 이음쇠 분포 (빈도 강제)

합격 대본에서 문장과 문장이 어떻게 연결되는지 실측 분포:

| 연결 방식 | 빈도 | 예시 |
|----------|------|------|
| **쉼표 나열** | 40% | "아내 야스코, 발레를 사랑하는 딸 니이나, 기차를 좋아하는 아들 레이." |
| **"하지만" 전환** | 20% | "하지만 누군가가 이 가족을 지켜보고 있었습니다." |
| **"그리고" 연결** | 15% | "그리고 새벽 한 시 십팔분." |
| **"..." 여백** | 10% | "평범하고 화목한 가족..." |
| **시제 전환 (현재형)** | 10% | "미키오가 업무 이메일을 확인합니다." |
| **짧은 단문 펀치** | 5% | "맨손으로." |

### 핵심 발견
**짧은 펀치(5%)는 극소량.** 초보자는 과적용하기 쉬움 — 전체가 짧아져서 리듬 붕괴. 대부분의 흐름은 쉼표 나열(40%) + 하지만 전환(20%).

### Reviewer 체크
- segment 내 각 connector 의 비율이 위 분포의 ±5%p 범위 벗어날 시 VQQA gradient feedback.
- 단문 펀치 > 15% 시 FAIL.

---

## Pattern D — 감정 전달 = 사실 배치

**원칙:** 감정을 **직접 말하지 않고 사실 배치로 느끼게** 한다.

### BAD (감정 직접 표현)
```
"참혹한 현장이었습니다. 너무나 비극적인 사건이었습니다."
```

### GOOD (사실 배치로 느끼게)
```
"현장에서 피 묻은 휴지가 발견되었습니다...
어머니 야스코가 딸의 상처를 지혈하려 했던 흔적이었습니다."
```

시청자가 사실에서 감정을 **스스로** 끌어내야 몰입 발생.

### Banned Expressions (longform 공통 + 대표님 지시)
| 금지 | 이유 |
|------|------|
| 믿으시겠습니까 | 저급 어그로 |
| 놀라운 사실이 하나 더 | 뻔한 전개 |
| 충격적인 / 경악 / 소름 | 감정 형용사 직접 표현 금지 |
| 구독·좋아요 직접 언급 | CTA 에서 금지 |
| 놓지 않았습니다 | 대표님 지시로 폐기 |

### Reviewer 체크
- `ins-narrative-quality` 가 banned regex 스캔 — 1회 hit = FAIL.
- 감정 형용사 밀도 (`충격적인|경악|소름|참혹한|비극적인` 등) 전체 스크립트에서 0회 목표.

---

## CTA 패턴 (궁금증 질문형)

- ✅ "이 사건의 진실은 대체 무엇일까요."
- ✅ "그날 밤 대체 무슨 일이 있었던 걸까요."
- ✅ "다음 수사에서 우리는 [다음 사건 힌트]를 추적합니다."
- ❌ "구독과 좋아요 부탁드립니다" (직접 CTA 금지)

---

## Reviewer Rubric Encoding

위 패턴 A-D 는 `ins-narrative-quality` + `ins-readability` Reviewer 의 rubric JSON schema 에 다음과 같이 encode:

```json
{
  "pattern_a_scene_flow": {
    "required_order": ["setting", "detail", "pause_or_transition", "twist_or_link"],
    "severity_on_violation": "FAIL"
  },
  "pattern_b_sentence_rhythm": {
    "max_consecutive_same_length_10_15": 2,
    "wave_amplitude_min": 15,
    "severity_on_violation": "FAIL"
  },
  "pattern_c_connector_distribution": {
    "target": {"comma_list": 0.40, "but_transition": 0.20, "and_link": 0.15,
               "ellipsis_pause": 0.10, "present_tense_switch": 0.10, "punch_short": 0.05},
    "tolerance_pp": 5,
    "hard_cap_punch_short": 0.15
  },
  "pattern_d_emotion_via_facts": {
    "banned_regex": "믿으시겠습니까|놀라운 사실이|충격적인|경악|소름|참혹한|비극적인|놓지 않았습니다",
    "max_emotion_adjective_density": 0.0
  }
}
```

---

## Related

- [[NLM_2STEP_TEMPLATE]] — 이 패턴이 적용될 대본의 생성 프롬프트
- [[4ACT_STRUCTURE]] — 4막 전체 구조 (작성 예정)
- [[../continuity_bible/MOC]] — 채널 고유 어휘·금지어 레이어

---

*Extracted 2026-04-20 from shorts_naberal/longform/claudedocs/SCRIPT_QUALITY_GATE_CONTRACT.md. 원본은 `.preserved/harvested/` 에 읽기 전용. 이 노드는 shorts_studio Reviewer rubric 구축을 위한 재서술 — 패턴 추출이며 코드/계약서 흡수 아님.*
