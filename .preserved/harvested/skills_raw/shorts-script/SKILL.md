---
name: shorts-script
description: Script writing domain knowledge for YouTube Shorts. Defines timing rules, script.json schema, and narration guidelines.
user-invocable: false
previous_failures:
  - id: FAIL-SCR-011
    type: logic
    pattern: "Hook 과속 (83자 10초) + 쉼표 결여 → 국어책 낭독체"
    preventive_check: "Hook ≤ 50자, 20자+ 문장에 쉼표 ≥ 2개"
    detected_regex: '"hook"\s*:\s*"[^"]{51,}"'
  - id: FAIL-SCR-016
    type: logic
    pattern: "어요/해요 체 혼입 (탐정 1인칭 무게감 훼손)"
    preventive_check: "종결어미 '습니다/입니다/였죠'만 사용 (incidents/wildlife/documentary)"
    detected_regex: '\S+[어해]요(?=[\s.,!?])'
  - id: FAIL-SCR-001
    type: logic
    pattern: "체언종결 2연속 (공포였다. 침묵이었다.)"
    preventive_check: "2문장 window 내 체언종결 연속 = 0"
    detected_regex: '[가-힣]+(이었|였|이)다\.\s*[가-힣]+(이었|였|이)다\.'
---

# Shorts Script Writing Guide

YouTube Shorts 대본 작성을 위한 도메인 지식. 타이밍 규칙, script.json 스키마, 내레이션 가이드라인을 정의한다.

## Timing Rules (CRITICAL)

`DESIGN_BIBLE.md` Section 6.5 **가 source of truth**. 한국어 내레이션 속도 + 유형별 길이 규칙.

### 길이 유형 (DESIGN_BIBLE Section 6.5)

| 유형 | 시간 | 비고 |
|------|------|------|
| **단편** | 50~60초 | 하나의 완결된 이야기 |
| **시리즈 (각 편)** | 90~120초 또는 50~60초 x 3~5편 | 다음 편이 궁금하게 클리프행어 필수 |
| **상한** | 120초 미만 | YouTube Shorts 최대 길이 |

### 내레이션 속도 (채널별 2-트랙)

| 속도 | 톤 | 채널 |
|------|-----|------|
| **~4.2 글자/초** | 차분/탐정/내레이터 (마침표 멈춤 많음) | incidents / incidents-jp / health |
| **~8.5 글자/초** | 빠른 스토리텔링/유머 | humor / politics / trend / sseoltube |

### 총 글자수 범위 (2-트랙)

| 유형 | 차분 (4.2자/s) | 빠름 (8.5자/s) |
|------|---------------|---------------|
| 단편 50~60초 | **210~252자** | **425~510자** |
| 시리즈 90~120초 | **378~504자** | **765~1020자** |
| 절대 상한 (120초) | **504자** | **1020자** |

### Hook/Body/CTA 세부 배분
- Hook/Body/CTA 의 구체적 시간/글자수 배분은 **채널별 + 유형별로 다르다**.
- 세부 배분은 `scripts/paperclip/agents/scripter/AGENTS.md` (Scripter Runbook) 와 각 `channel-*` SKILL 에서 관리한다.
- 본 스킬은 **총합 범위만 규정**한다.

### 검증 절차
`ALWAYS calculate and verify total character count against duration before finalizing`

1. 각 섹션의 narration 글자수를 센다
2. 전체 글자수를 합산한다
3. **채널 속도 확인** (incidents/health 계열=4.2자/s, humor/politics/trend/sseoltube=8.5자/s)
4. `전체 글자수 / 채널_속도 = 예상 소요 시간(초)`
5. 예상 시간이 **단편 50~60초** 또는 **시리즈 90~120초** 범위 안에 들어오는지 확인
6. 상한 120초 초과 금지
7. blueprint 의 `series_info.type` (단편/시리즈) 과 일치하는지 확인

## Tone

### 기본 톤 (채널 미지정 시)
- 중립적이고 정보 전달에 충실한 톤
- 유머, 강한 정치적 입장, 자극적 표현 사용 금지
- 자연스러운 한국어 내레이션 (차분한 뉴스 앵커가 설명하는 느낌)
- 과장 표현 지양, 팩트 기반 서술

### 채널별 톤 (D-02 단일 소스 원칙)
- 채널 톤은 각 채널 SKILL.md에서만 정의 (channel-humor, channel-politics, channel-trend)
- 디렉터가 CHANNEL CHARACTER GUIDE 블록을 주입하면 해당 채널 톤을 따름
- 채널 미지정 시 위의 기본 톤 적용

## 문체 규칙 (Writing Style) — 기계적 대본 금지

narrative_texture가 "무엇을 넣을지"라면, 이 섹션은 **"어떻게 쓸지"**다.
팩트 나열은 AI가 잘한다. 하지만 사람이 듣고 느끼려면 **리듬, 대비, 여백**이 필요하다.

> **데이터 근거**: 영어 true crime 쇼츠 30개 + 한국 범죄 쇼츠 19개 분석 (2026-04-07).
> 조회수 상위 쇼츠일수록 감정 형용사를 **덜** 쓰고, **팩트 배치**로 감정을 유도한다.
> 상세: `claudedocs/shorts_script_analysis/ANALYSIS.md`

### 1. 문장 리듬 변주 (필수)
같은 길이의 문장이 3개 이상 연속되면 안 된다. 짧은 펀치 → 긴 설명 → 단어 하나, 이런 파동을 만들어라.

```
BAD:  "범인은 냉장고를 열었습니다. 아이스크림 네 개와 멜론을 꺼내 먹었습니다. 보리차를 마셨습니다."
GOOD: "범인은 냉장고를 엽니다. 하겐다즈. 네 개. 멜론도 꺼냅니다. 보리차를 따라 마시고, 소파에 눕습니다."
```

| 리듬 패턴 | 효과 | 예시 |
|-----------|------|------|
| 1-3자 단문 | 충격, 강조 | "네 개.", "맨손으로." |
| 중문 후 단문 | 긴장→펀치 | "필사적으로 싸웠지만... 쓰러집니다." |
| 열거 후 전환 | 축적→반전 | "재킷, 모자, 장갑, 힙색. 그리고 사라졌습니다." |

### 2. 대비/병치 (Body 씬당 권장 1회)
평범한 것 옆에 비정상을 놓아라. 팩트를 말하지 말고 **느끼게** 하라.

**핵심 원칙 — "팩트로 느끼게" (채널별 적용 강도 다름)**:

| 채널 | 형용사/판단 스타일 | 예시 |
|------|-------------------|------|
| **humor, trend, sseoltube** | 팩트 나열 위주, 감정 형용사 최소화 | "개는 돌아왔습니다. 여자 두 명은 돌아오지 않았습니다." |
| **incidents, politics** | 형사 보고서 톤 허용. "참혹한", "잔혹하게", 분석적 판단 가능 | "극도로 침착했음을 보여줍니다.", "참혹한 현장" |

> incidents/politics에서 형사가 보고하듯 "극도로 침착했음을 보여줍니다"는 장르에 맞는 자연스러운 표현이다.
> 단, **AI 클리셰는 전 채널 금지**: "믿으시겠습니까", "놀라운 사실이 하나 더 있습니다", "상상할 수 없는"

```
humor/trend:
  BAD:  "끔찍하게도 여행객 두 명이 실종됐습니다."
  GOOD: "개는 돌아왔습니다. 여자 두 명은 돌아오지 않았습니다."

incidents/politics:
  OK:   "참혹한 현장이었습니다. 극도로 침착했음을 보여줍니다."
  BAD:  "믿으시겠습니까? 놀라운 사실이 하나 더 있습니다." ← AI 클리셰
```

대비 유형:
- **행동 대비**: 살인 직후 + 일상적 행동 (아이스크림, 잠)
- **시간 대비**: "밤 열시 삼십팔분, 마지막 이메일. 한 시간 뒤, 침입."
- **규모 대비**: "증거 만 이천 오백 점. 범인 영 명."
- **결과 대비**: "77번 구조 요청. 한 번도 연결되지 않았습니다." ← 수치+결과 대비 (데이터 검증)

### 2-1. BUT pivot (필수, Body에서 최소 1회)

"하지만" / "그런데"가 가장 강력한 전환 무기다. **모든 Body에 최소 1회** 사용.
BUT 뒤에는 항상 **기대의 반전** 또는 **충격적 사실**이 와야 한다.

> 데이터: 영어 30개 쇼츠에서 "but" 총 16회, 한국 19개에서 "하지만/그런데" 12회 사용.
> 조회수 상위 쇼츠의 공통점: BUT pivot 후에 핵심 정보 공개.

```
"남편은 아내를 마지막으로 봤다고 말했습니다.
 하지만 그날, 청소 용품에 수백 달러를 썼습니다."
 ← BUT pivot: 평범한 진술 → 반전 (ThatChapter, 492K views)
```

패턴:
```
[평범한 사실] + "하지만/그런데" + [충격적 반전]
```

### 2-2. 나열 축적 (List as weapon, 선택적)

증거/행동/검색 기록을 하나씩 나열하면 **누적 공포** 효과. 목록이 쌓일수록 소름.

```
"남편은 아들 아이패드로 검색합니다.
 시체 냄새 나기까지 시간.
 시체 분해 방지법.
 시체 처리 10가지 방법.
 신체 부위 버려도 되나.
 나무 바닥 핏자국 제거법."
 ← 6개 나열로 누적 공포 (ThatChapter, 492K views)
```

- Body 씬 1개를 나열 전용으로 쓸 수 있음
- 최소 3개, 최대 6개 항목
- 마지막 항목이 가장 충격적이어야 함

### 3. 시제 전환 (권장, 과거:현재 = 7:3)
과거형으로만 쓰면 다큐멘터리 교과서가 된다. 핵심 장면에서 **현재형**으로 전환하면 시청자가 현장에 있는 느낌을 준다.

> 데이터: 영어 쇼츠 과거시제 8.1회 vs 현재시제 3.1회 (약 7:3). 한국 쇼츠 과거 2.3 vs 현재 2.2 (약 5:5).
> 권장 비율: **과거 70% : 현재 30%**. Hook + 클라이맥스에 현재형 집중.

```
과거: "범인은 냉장고를 열었습니다."
현재: "범인은 냉장고를 엽니다."  ← 지금 이 순간 벌어지는 것처럼
```

- **Hook**: 현재형 ("~ 합니다", "~ 엽니다") — 시청자를 현장에 즉시 투입
- **Body 설명**: 과거형 ("~ 했습니다", "~ 었습니다") — 사실 전달
- **클라이맥스**: 현재형 전환 ("그리고... 문을 엽니다") — 긴장감 폭발
- 전체를 현재형으로 쓰지는 말 것 (과거↔현재 전환이 핵심)

### 4. 여백과 무음 (TTS 연동)
"..." 또는 짧은 문장 뒤 마침표는 TTS에서 무음 구간이 된다. 이 여백이 시청자에게 생각할 틈을 준다.

```
"그리고... 잠이 듭니다."     ← "..."에서 0.3초 무음
"네 식구의 집에서."          ← 마지막에 여운
```

- Body에서 가장 충격적인 사실 직전/직후에 "..." 1회 사용 권장
- 남발 금지 (전체 대본에서 최대 2-3회)

### 5. 서술자 시선 (채널별)
AI가 쓴 대본은 "누가 읽어도 같은 톤"이 된다. 서술자의 해석이나 시선을 넣어라.

| 채널 | 서술자 시선 | 예시 |
|------|------------|------|
| incidents | 담담한 관찰자 (해석은 최소, 사실 배치로 느끼게) | "물을 내리지 않았습니다." (판단 안 함) |
| humor | 동네 아저씨 (어이없다는 듯 전달) | "그래갖고 결국 어쩔 수 없었당께유" |
| politics | 냉소적 관찰자 (팩트로 비꼬기) | "본인은 모른다고 했습니다. 세 번째입니다." |
| trend | 친구한테 말하듯 | "야 이거 실화야. 진짜로." |

### 6. 법의학적 구체성 (Forensic Specificity, incidents/politics 필수)

추상적 서술 대신 **고유명사, 수치, 위치**를 넣어라. 구체적일수록 신뢰감이 올라가고, 시청자가 "진짜 사건"임을 느낀다.

```
BAD:  "가방에서 증거가 나왔습니다."
GOOD: "가방에서 네바다 모하비 사막에서만 발견되는 석영 모래가 나왔습니다."

BAD:  "그 시각, 차가 지나갔습니다."
GOOD: "오후 열한시 사십이분, 은색 혼다 시빅이 주유소 CCTV에 잡혔습니다."

BAD:  "많은 돈을 인출했습니다."
GOOD: "이틀간 ATM에서 삼백오십만 원을 인출했습니다."
```

- 장소: 도시명 + 구체 장소 (에드워즈 공군기지 인근, XX구 XX동)
- 시간: 시:분 단위 (오후 열한시 사십이분)
- 금액/수치: 정확한 숫자 (삼백오십만 원, 이십오 년)
- 물건: 브랜드/모델 (은색 혼다 시빅, 하겐다즈)

### 7. 능동태 지향 (Active Voice, 전 채널 권장)

수동태("~되었습니다")는 주체를 흐리게 만든다. **누가 했는지** 명확하게 써라.

```
BAD:  "시신이 발견되었습니다."
GOOD: "경찰은 시신을 발견했습니다."

BAD:  "DNA가 검출되었습니다."
GOOD: "감식반이 DNA를 검출했습니다."

BAD:  "용의자가 체포되었습니다."
GOOD: "SWAT 팀이 용의자를 체포했습니다."
```

- **예외**: 주체가 불분명하거나 의도적으로 미스터리를 유지할 때는 수동태 허용 ("누군가에 의해 옮겨졌습니다")
- Body 전체에서 능동태 70% 이상 유지 목표

### 8. 씬 내부 흐름 공식 (Scene Flow Formula) — 필수

모든 Body 씬은 아래 흐름을 따른다. 이 공식을 벗어나면 로봇적 나열이 된다.

```
[세팅] 짧은 시간/장소/상황 (10-15자)
  → [디테일] 긴 문장으로 구체적 묘사 (25-40자)
  → [축적 또는 추론] 쉼표 나열 또는 해석 (20-30자)
  → [여백 또는 전환] "..." 또는 "하지만" (10-20자)
```

#### Good Example (합격 대본에서 추출)
```
"2000년 겨울, 도쿄 세타가야."                              ← 세팅 (12자)
"미야자와 미키오는 아이들에게 종이 인형을 만들어주는         ← 디테일 (35자)
 다정한 아버지였습니다."
"아내 야스코, 발레를 사랑하는 딸 니이나,                    ← 축적: 쉼표 나열 (28자)
 기차를 좋아하는 아들 레이."
"평범하고 화목한 가족..."                                   ← 여백 (10자)
"하지만 누군가가 이 가족을 지켜보고 있었습니다."             ← 반전 (20자)
```

#### Bad Example (로봇)
```
"도쿄 세타가야구."       ← 전부 같은 길이
"미키오. 아버지."        ← 문장 5-10자 연속
"야스코. 어머니."        ← 리듬 없음
"니이나. 여덟 살."       ← 보고서 느낌
```

### 9. 문장 길이 리듬 규칙 (Rhythm Rule) — 필수

한 씬 안에서 문장 길이는 **파동**을 만들어야 한다.

```
짧(10-15) → 긴(25-40) → 중(20-30) → 짧(10-15) → 긴(25-40)

절대 금지: 같은 길이대(±5자) 문장 3개 연속
```

실측 데이터 (합격 대본 3편 평균):
- 평균 문장 길이: 21.3자
- 최단: 6자 ("맨손으로."), 최장: 38자
- 10자 미만 비율: 12% (짧은 펀치는 극소량)
- 25자 이상 비율: 35% (**긴 문장이 전체의 1/3**)

### 10. 문장 연결 비율 (Connection Ratio) — 권장

합격 대본에서 추출한 문장 간 연결 방식 비율:

| 연결 방식 | 비율 | 설명 |
|----------|------|------|
| 쉼표 나열 (A, B, C.) | 40% | "아내 야스코, 딸 니이나, 아들 레이." |
| "하지만/그런데" 전환 | 20% | 반전, 충격 사실 도입 |
| "그리고/그 뒤" 순접 | 15% | 시간 순서 진행 |
| "..." 여백 | 10% | 감정 여운, 충격 직전 |
| 현재형 전환 | 10% | "엽니다", "확인합니다" |
| 짧은 단문 펀치 | 5% | "맨손으로.", "여섯 살." |

**핵심: 짧은 펀치는 5%만. 나머지 95%는 흐르는 문장.**

### 11. 스토리텔링 체크리스트 (Script QA) — 검증용

대본 작성 후 반드시 확인:

- [ ] 같은 길이 문장이 3개 연속인 곳이 없는가?
- [ ] 각 Body 씬에 "하지만/그런데" 전환이 최소 1회 있는가?
- [ ] 25자 이상 긴 문장이 전체의 30% 이상인가?
- [ ] 쉼표 나열(A, B, C 구조)이 최소 2회 있는가?
- [ ] "..." 여백이 전체에서 2-3회 사용되었는가?
- [ ] 각 씬이 [세팅→디테일→축적/추론→여백/전환] 흐름을 따르는가?
- [ ] 읽어봤을 때 "사람이 이야기하는 느낌"이 나는가? (가장 중요)

---

## Script Structure

모든 쇼츠 대본은 Hook -> Body -> CTA 3단계 구조를 따른다.

### Hook (type: "hook")
- **시간**: 3~5초 (콜드오픈, 시청 유지율의 90% 는 이 구간에서 결정)
- **글자수**: 채널 속도 기반 산정 — 차분(4.2자/s)=13~21자 / 빠름(8.5자/s)=26~42자
- **목적**: 시청자의 주의를 즉시 집중시키는 레이어드 훅 (시각+청각+텍스트 동시 자극)
- **형식**: 질문형, 충격 통계, 대담한 주장, 이야기, 직접 약속, 대비 중 하나 (hook_style로 지정)
- **예시**: "AI가 반도체 전쟁을 완전히 바꾸고 있다?"

### Body (type: "body")
- **시간**: 단편 40~50초 / 시리즈 80~110초 (여러 씬으로 분할, 전체의 ~85%)
- **목적**: 핵심 내용 전달
- **구성**: 2~6개 씬, 각 씬별 narration + visual direction
- **글자수**: `(전체 글자수 상한) - (Hook+CTA 글자수)` 로 역산. Scripter AGENTS.md 참조
- **씬 분할**: 주제의 복잡도에 따라 2~6개 씬으로 분할
- **각 씬**: scene 번호(1, 2, 3...), 개별 duration, narration, visual 포함

### CTA (type: "cta")
- **시간**: 단편 3~5초 (구독 유도) / 시리즈 5~10초 (클리프행어 + 다음 편 예고)
- **목적**: 단편=구독/좋아요 / 시리즈=다음 편이 궁금하게 만드는 클리프행어
- **글자수**: 채널 속도 기반 산정 — 차분(4.2자/s)=13~42자 / 빠름(8.5자/s)=26~85자
- **예시 (단편)**: "구독과 좋아요 눌러주세요!"
- **예시 (시리즈)**: "다음 편, 진짜 범인이 드러납니다." (DESIGN_BIBLE Section 6.5 — 시리즈는 다음 편 예고/클리프행어 필수)

### 순서 규칙
- 엄격한 순서: hook -> body 씬들 (1, 2, 3...) -> cta
- 순서 변경 금지
- Body 씬의 scene 번호는 1부터 순차 증가

## script.json Output Schema

script.json 파일의 정확한 출력 스키마. 모든 필드를 포함해야 한다.

```json
{
  "topic": "string - original topic",
  "channel": "neutral",
  "target_duration": 55,
  "total_characters": "number - sum of all narration character counts",
  "estimated_duration": "number - total_characters / channel_speed (4.2 or 8.5), rounded to 1 decimal",
  "pipeline_type": "shorts",
  "render_mode": "stock",
  "storytelling_framework": "curiosity_gap",
  "hook_style": "question",
  "key_text": [
    {"text": "시청률 97%", "source_section": 0, "display_at": "hook"},
    {"text": "3일 만에 달성", "source_section": 1, "display_at": "body"},
    {"text": "10배 성장", "source_section": 2, "display_at": "body"}
  ],
  "sections": [
    {
      "type": "hook",
      "duration": 5,
      "narration": "string (21 Korean chars max)",
      "visual": "string (scene direction for video editor)",
      "visual_type": "establishing",
      "character_count": "number",
      "emotion": "string (optional, TTS emotion preset: normal/happy/sad/angry/whisper/toneup/tonedown)",
      "emotion_intensity": "number (optional, 0.5-1.2, default 1.0)",
      "style_tag": "string (optional, SSFM 3.0 natural language style e.g. '(담담하게)', '(속삭이듯)')"
    },
    {
      "type": "body",
      "scene": 1,
      "duration": "number (seconds for this scene)",
      "narration": "string (scene narration text)",
      "visual": "string (scene direction: what to show on screen)",
      "visual_type": "detail",
      "character_count": "number",
      "emotion": "string (optional)",
      "emotion_intensity": "number (optional)",
      "style_tag": "string (optional)"
    },
    {
      "type": "body",
      "scene": 2,
      "duration": "number (seconds for this scene)",
      "narration": "string (scene narration text)",
      "visual": "string (scene direction: what to show on screen)",
      "visual_type": "action",
      "character_count": "number",
      "emotion": "string (optional)",
      "emotion_intensity": "number (optional)",
      "style_tag": "string (optional)"
    },
    {
      "type": "cta",
      "duration": 5,
      "narration": "string (21 Korean chars max)",
      "visual": "string (scene direction)",
      "visual_type": "reaction",
      "character_count": "number",
      "emotion": "string (optional)",
      "emotion_intensity": "number (optional)",
      "style_tag": "string (optional)"
    }
  ],
  "sources_used": ["url1", "url2"],
  "graphic_cards": [
    {
      "composition_id": "IntroCard",
      "graphic_props": {
        "channelName": "채널명",
        "topicText": "AI 반도체 전쟁의 시작",
        "primaryColor": "#FFFFFF",
        "accentColor": "#00F5D4",
        "secondaryColor": "#9B5DE5",
        "backgroundColor": "#2D1B69",
        "fontFamily": "Pretendard"
      },
      "position": "intro",
      "duration": 3
    }
  ]
}
```

### 스키마 규칙
- `topic`: 원본 주제 문자열 그대로
- `channel`: 디렉터가 전달한 채널명 (미지정 시 `"neutral"`)
- `target_duration`: **단편 50~60 / 시리즈 90~120** (DESIGN_BIBLE Section 6.5 기준, blueprint.series_info 에서 결정). 과거 25~35초 기본값은 outdated.
- `total_characters`: 모든 섹션의 character_count 합계. 허용 범위는 `(target_duration) x (채널_속도)` 로 계산:
  - 단편 55초 x 4.2 ≈ **231자** (incidents 등 차분 채널)
  - 단편 55초 x 8.5 ≈ **468자** (humor 등 빠른 채널)
  - 시리즈 105초 x 4.2 ≈ **441자** / 시리즈 105초 x 8.5 ≈ **893자**
- `estimated_duration`: `total_characters / 채널_속도` (incidents/health=4.2, humor/politics/trend/sseoltube=8.5), 소수점 1자리까지 반올림
- `sections`: hook 1개 + body 2~6개 + cta 1개 (단편=4~6 섹션, 시리즈=6~10 섹션)
- `storytelling_framework`: 5종 중 1개 (필수, Storytelling Framework 섹션 참조)
- `hook_style`: 6종 중 1개 (필수, Hook Formula 섹션 참조)
- `key_text`: 핵심 팩트 배열 3-6개 (필수, key_text Rules 섹션 참조)
- `sources_used`: source.md의 Sources 섹션에서 가져온 URL 목록
- `graphic_cards`: Remotion 그래픽 카드 배열. 빈 배열도 허용 (`[]`). D-03 규칙 참조
- `emotion`: (선택) 섹션별 TTS 감정 프리셋. 미지정 시 voice-presets.json의 `emotion_map`에서 자동 매핑
- `emotion_intensity`: (선택) 감정 강도 0.5-1.2. 자연스러운 범위는 0.8-1.1. 기본값 1.0
- `style_tag`: (선택) SSFM 3.0 자연어 스타일 태그 (예: `"(속삭이듯)"`, `"(담담하게)"`, `"(공포에 질려)"`)

### 채널별 기본 감정 매핑 (scripter가 emotion 미지정 시 자동 적용)

| 섹션 | incidents | humor | politics | trend |
|------|-----------|-------|----------|-------|
| Hook | normal | normal | tonedown | happy |
| Body | tonedown | happy | normal | normal |
| 클라이맥스 | whisper | toneup | toneup | toneup |
| CTA | sad | normal | tonedown | happy |

scripter가 `emotion`을 명시하면 매핑을 오버라이드한다. `style_tag`는 SSFM 3.0 모델에서만 작동하며, ssfm-v21에서는 무시된다.

## Storytelling Framework (per D-03)

scripter가 주제/채널에 맞게 5종 중 하나를 선택하여 `storytelling_framework` 필드에 기록한다.

| Framework | 설명 | 효과 | 채널 적합성 |
|-----------|------|------|-------------|
| `curiosity_gap` | 훅에서 질문, 답은 끝에 | >65% 리텐션 시 4-7배 노출 | humor, trend, neutral |
| `pattern_interrupt` | 예상 깨는 오프닝 | +23% 리텐션 | trend |
| `open_loop` | 중간부터 시작, 미해결 긴장감 | 70%+ 완시청 | humor |
| `problem_agitation_solution` | 문제->고통 자극->해결 | 가장 보편적 | politics, neutral |
| `proof_first` | 결과/통계 먼저, 설명 나중 | 교육 콘텐츠 최적 | politics, neutral |

### 채널별 선호 프레임워크

| 채널 | Primary | Secondary | 근거 |
|------|---------|-----------|------|
| humor | open_loop | curiosity_gap | 이야기(썰) 형식에 최적 |
| politics | proof_first | problem_agitation_solution | 팩트 기반 앵커 톤 |
| trend | pattern_interrupt | curiosity_gap | MZ 빠른 템포 |
| neutral | curiosity_gap | proof_first | 기본 정보 전달에 보편적 |

## Hook Formula (per D-04, 49개 쇼츠 분석 데이터 보강)

scripter가 6종 중 하나를 선택하여 `hook_style` 필드에 기록한다.

| Hook Style | 예시 | 리텐션 효과 | 49개 분석 |
|------------|------|-------------|----------|
| `question` | "이게 진짜 가능할까요?" | 65%+ | |
| `shock_stat` | "97%가 모르는 사실" | 60%+ | 한국 63% 사용 |
| `bold_claim` | "이건 완전히 틀렸습니다" | 60%+ | |
| `story` | "어제 무슨 일이 있었냐면" | 70%+ | 영어 27% (최고 조회수) |
| `direct_promise` | "3분이면 완벽히 이해됩니다" | 65%+ | |
| `contrast` | "전에는 A, 지금은 B" | 60%+ | |

> **49개 분석 데이터 (2026-04-07)**:
> - 영어 조회수 상위: `story`(scenario) 27% + `bold_claim`(statement) 16% = **조회수 최상위 조합**
> - 한국: `shock_stat`(날짜+수치) 63%로 압도적 — 뉴스 클립 영향. **나레이션 채널은 story형이 더 적합.**
> - **⚠️ superlative("가장 충격적인", "역대 최악의") 남용 경고**: 영어 분석에서 superlative Hook의 평균 조회수가 scenario/statement보다 낮음. 시청자가 과장에 면역됨.
> - **인용 Hook 추천**: 범인/피해자 실제 발언 인용이 가장 강력 (영어 1-2위 모두 인용형)

## key_text Rules (per D-05, D-06)

scripter가 대본에서 숫자/통계/대비/핵심 팩트를 3-6개 추출하여 `key_text` 배열에 기록한다.

- **개수**: 3-6개 (필수)
- **내용**: 숫자, 통계, 대비, 핵심 팩트
- **길이**: 최대 6단어/18자 per item
- **Hook 필수**: 최소 1개는 display_at: "hook"
- **source_section**: sections 배열의 인덱스 (추출 원본 위치)
- **display_at**: "hook" 또는 "body" (일반적 위치. 정확한 타이밍은 Phase 25에서 결정)

### key_text JSON 스키마

```json
{
  "key_text": [
    {"text": "시청률 97%", "source_section": 0, "display_at": "hook"},
    {"text": "3일 만에 달성", "source_section": 1, "display_at": "body"},
    {"text": "10배 성장", "source_section": 2, "display_at": "body"}
  ]
}
```

- `text` (string, 필수): 오버레이 텍스트. 최대 6단어/18자.
- `source_section` (integer, 필수): sections 배열 인덱스 (추출 원본 위치).
- `display_at` (string, 필수): "hook" 또는 "body".

### visual_type Classification (v5.0 확장)

Shorts 파이프라인 (avatar_enabled=False)에서 사용하는 6종 visual_type:

| visual_type | 설명 | 기본 할당 |
|-------------|------|-----------|
| `establishing` | 배경 설정 와이드 샷 (도시 전경, 건물 외관) | hook, body scene 1 |
| `detail` | 클로즈업, 디테일 (숫자, 제품, 문서) | body scene 2+ |
| `action` | 동적 장면 (사람 걷기, 기계 작동) | body scene 2+ |
| `reaction` | 반응 샷 (군중, 리액션) | cta |
| `metaphor` | 은유적 이미지 (체스, 빙산, 저울) | body |
| `text` | 텍스트 카드/그래픽 카드 | key_text 강조 시 |

Avatar 파이프라인 (avatar_enabled=True)에서 사용하는 레거시 3종 (후방 호환):

| visual_type | 설명 | 기본 할당 |
|-------------|------|-----------|
| `avatar` | AI avatar presenter (HeyGen) | hook, cta |
| `stock` | Stock footage / B-Roll | body |
| `broll` | AI-generated B-Roll (fal.ai) | body (AI visual) |

Validator는 9종 모두 허용한다. Shorts scripter는 avatar_enabled=False일 때 6종 신규 타입을 사용한다.

**기본 할당 로직 (avatar_enabled=False):**
- `hook` sections -> visual_type: `establishing` (또는 pattern_interrupt 훅이면 `action`)
- `body scene 1` -> visual_type: `establishing`
- `body scene 2+` -> visual_type: `detail` / `action` 교대 (시각적 다양성)
- `cta` sections -> visual_type: `reaction`
- key_text 오버레이가 주 비주얼이면 `text`로 오버라이드
- 추상적/상징적 씬이면 `metaphor`로 오버라이드

### 안전 관련 참고
Safety 결과(정치 콘텐츠 판별, 실명 감지, 명예훼손 위험)는 script.json에 포함하지 않는다. Safety 결과는 metadata.json의 safety_check 섹션에만 저장된다. 대본 에이전트는 콘텐츠만 생산하고, 디렉터가 별도로 safety 평가를 수행한다.

## Visual Direction Guidelines

각 섹션의 `visual` 필드에는 영상 편집자가 화면을 구성할 수 있는 충분한 정보를 포함한다.

### 포함 요소
- **배경 유형**: stock video, text card, graphic 등
- **텍스트 오버레이**: 화면에 표시할 텍스트 내용
- **모션/전환**: 화면 전환 효과 설명

### 작성 기준
- 구체적으로: 영상 편집자가 적절한 스톡 영상을 찾거나 그래픽을 디자인할 수 있을 정도로 상세하게
- 형식: "Stock video: [설명], text overlay: [텍스트]" 패턴 권장

### 예시
- "Stock video: 반도체 칩 클로즈업, text overlay: 수치 데이터 표시"
- "Text card: 핵심 인용문 강조, 배경 진한 파란색, 텍스트 흰색"
- "Stock video: 공장 자동화 라인, text overlay: 생산량 비교 그래프"
- "Graphic: 타임라인 인포그래픽, 주요 사건 날짜 표시"

### Graphic Card Visuals

Scenes can use `Graphic:` prefix in the visual field to trigger graphic card rendering instead of stock footage.

**Prefix format:** `Graphic:card_type:content_text`

| Card Type | Format | Example |
|-----------|--------|---------|
| title_card | `Graphic:title_card:제목` | `Graphic:title_card:AI 반도체 전쟁의 시작` |
| quote_card | `Graphic:quote_card:인용문\|출처` | `Graphic:quote_card:인공지능은 새로운 전기이다\|앤드류 응` |
| stats_card | `Graphic:stats_card:숫자\|설명` | `Graphic:stats_card:3.2조 원\|AI 반도체 시장 규모` |

**Usage guidelines:**
- Shorts: max 1 graphic card total (optional)
- Video: title_card at each chapter start (mandatory for intro), 1-2 quote/stats per chapter (optional)
- Graphic card scenes have duration 3-5 seconds
- Text is Korean (Pretendard Bold font renders in the graphic)

## Graphic Cards (D-03)

script.json에 `graphic_cards` 배열을 포함한다. 각 항목은 Remotion 그래픽 카드를 정의하며, scene_designer가 이를 scene-manifest.json의 remotion 클립으로 변환한다.

### graphic_cards 스키마

```json
"graphic_cards": [
  {
    "composition_id": "string — Remotion composition ID",
    "graphic_props": { "object — composition-specific props + channel theme" },
    "position": "string — intro | outro | before_scene_N | after_scene_N",
    "duration": "number — seconds (1-5)"
  }
]
```

### Composition ID 목록

| composition_id | 용도 | 필수 graphic_props |
|---------------|------|-------------------|
| IntroCard | 채널 인트로 | channelName, topicText, logoUrl(optional) |
| OutroCard | 구독 CTA (video only) | channelName, ctaText(default: "구독과 좋아요 부탁드립니다"), logoUrl(optional) |
| ListCard | 번호/불릿 리스트 | items(string[], max 5), ordered(boolean) |
| HighlightCard | 핵심 문장 강조 | text, highlightWord(optional) |
| BarChartCard | 수평 바 차트 | bars({label, value}[], max 5), maxValue(optional), unit(optional) |
| ComparisonCard | VS 비교 | leftLabel, leftValue, rightLabel, rightValue, vsText(default: "VS") |
| TitleCard | 제목 카드 (기존) | title, subtitle(optional) |
| QuoteCard | 인용문 (기존) | citation, source(optional) |
| StatsCard | 통계 숫자 (기존) | number, label |

### 채널 테마 자동 삽입

모든 graphic_props에는 채널 테마 필드를 포함한다:

| 채널 | primaryColor | accentColor | secondaryColor | backgroundColor |
|------|-------------|-------------|----------------|-----------------|
| humor | #FFFFFF | #FFC947 | #FF6B35 | #1A1A2E |
| politics | #FFFFFF | #E63946 | #457B9D | #0D1B2A |
| trend | #FFFFFF | #00F5D4 | #9B5DE5 | #2D1B69 |

fontFamily는 항상 `"Pretendard"`.

### position 규칙

- `"intro"` — 영상 맨 처음. IntroCard 전용
- `"outro"` — 영상 맨 마지막. OutroCard 전용, **video 파이프라인만** (shorts 사용 금지, D-04)
- `"before_scene_N"` — body scene N 앞에 삽입 (예: `"before_scene_2"`)
- `"after_scene_N"` — body scene N 뒤에 삽입 (예: `"after_scene_1"`)

### Shorts 규칙 (pipeline_type: "shorts")

- IntroCard: 선택적, position `"intro"`, duration 1-3초 (30-90 frames)
- OutroCard: **사용 금지** (D-04: 60초 제한)
- 본문 그래픽 카드: 최대 1개 (60초 제한 때문에 남은 시간 고려)
- graphic_cards가 비어있어도 유효 (그래픽 없는 쇼츠)

### Video 규칙 (pipeline_type: "video")

- IntroCard: 권장, position `"intro"`, duration 3-5초 (90-150 frames)
- OutroCard: 권장, position `"outro"`, duration 3-5초 (90-150 frames)
- 본문 그래픽 카드: 챕터당 0-2개 권장
- 그래픽 카드의 총 duration이 영상 전체의 20%를 초과하지 않도록 한다

## Feedback Handling

사용자 피드백에 따른 대본 재생성 절차.

### 재생성 규칙
1. 피드백을 주의 깊게 읽는다
2. 피드백에서 언급된 부분만 수정한다
3. 수정 후 타이밍 제약을 재확인한다
4. character_count와 estimated_duration을 재계산한다
5. metadata.json의 version을 증가시킨다

### 버전 관리
- 초기 생성: version = 1
- 각 피드백-재생성 사이클마다 version + 1

### 주의사항
- 피드백에 없는 부분은 변경하지 않는다
- 타이밍 제약은 수정 후에도 반드시 유지한다
- source.md에 없는 정보를 추가하지 않는다

## metadata.json Update

script.json 작성 완료 후 metadata.json의 script 단계를 업데이트한다.

```json
{
  "steps": {
    "script": {
      "status": "completed",
      "completed_at": "[ISO timestamp]",
      "output": "script.json",
      "version": 1
    }
  }
}
```

### 업데이트 규칙
- script.json을 먼저 작성한 후에 metadata.json을 업데이트한다 (원자적 완료)
- version은 피드백-재생성 사이클마다 증가한다
- completed_at은 ISO 8601 형식의 타임스탬프


## Video Script Rules

When pipeline_type is 'video', the script follows multi-chapter structure per D-04, D-05, D-06.

### Chapter Structure

- **Intro** (type: "intro", chapter: 0): Hook the viewer in 20-30 seconds. Present the core question or tension that the video will explore. This is the "why should I watch" moment.
- **Chapters** (type: "chapter", chapter: 1..N): Each chapter is a self-contained argument or story beat. Target 60-180 seconds each. Each chapter should advance the narrative while being comprehensible on its own.
- **Conclusion** (type: "conclusion", chapter: -1): Summarize key points, deliver the final insight, call to action (subscribe/like), 20-30 seconds.

### Chapter Count Guidelines

The scripter dynamically decides chapter count (3-7) based on topic complexity and target_duration:

| Target Duration | Chapters | Rationale |
|----------------|----------|-----------|
| 5 min (300s) | 3 chapters | Quick overview, each chapter ~80s |
| 8-10 min (480-600s) | 4-5 chapters | Standard depth, each chapter ~100-120s |
| 12-15 min (720-900s) | 5-7 chapters | Deep dive, each chapter ~100-150s |

### Scene Visual Direction Rules

Each chapter (and intro/conclusion) breaks into scenes of 3-5 seconds each:
- Visual descriptions MUST be in English (for Google image crawling + Veo AI prompt compatibility)
- Visual descriptions should be concrete and specific ("US Capitol building exterior" not "government")
- Visual descriptions should describe what the viewer sees, not abstract concepts
- Each scene within a chapter should have a different visual concept for variety (per D-09 context diversity)
- Avoid repeating the same visual concept across adjacent chapters

### Scene Structure

Each section contains a `scenes` array:
```json
"scenes": [
  {"visual": "semiconductor chip close-up macro lens", "duration_target": 4},
  {"visual": "global trade routes map animation", "duration_target": 4},
  {"visual": "factory automation assembly line", "duration_target": 5}
]
```

Rules:
- `visual` (string): English stock search description, concrete and searchable
- `duration_target` (number): 3-5 seconds per scene
- Total scene durations within a section should approximately match the section duration
- Minimum 2 scenes per section, no maximum but keep practical (3-8 scenes typical for a 120s chapter)

### Character Count Estimate

- Korean narration speed: ~4.2 chars/second (calm news anchor style — video mode 는 long-form 이므로 차분한 톤 기본값 고정. shorts 는 채널별 2-트랙(4.2/8.5)이므로 이 섹션 수치를 shorts 에 사용하지 말 것.)
- 5 min video (300s): ~1,260 total characters
- 10 min video (600s): ~2,520 total characters
- 15 min video (900s): ~3,780 total characters

### Video Timing Verification

Before writing the final script.json for video mode:
1. Sum all section character_count values
2. Calculate estimated_duration = total_characters / 4.2
3. Verify estimated_duration is within +-10% of target_duration
4. Verify each chapter title is <= 40 characters
5. Verify each scene duration_target is 3-5 seconds
6. Verify chapter count is 3-7

### pipeline_type Field

The `pipeline_type` field is REQUIRED in the root of script.json:
- `"shorts"`: Uses hook/body/cta section types (existing behavior)
- `"video"`: Uses intro/chapter/conclusion section types (new behavior)

Both modes use the same `sections` array structure. The pipeline_type determines which section types are valid.

## Genre Techniques (장르별 대본 기법)

GAN 로테이션 5회(R3-R7) 블라인드 평가로 검증된 기법만 수록.
scripter는 채널+주제에 맞는 기법을 선택하여 대본 구조에 적용한다.

### 전 장르 공통: narrative_texture (서사 질감)

**규칙**: 모든 Body 씬에 아래 질감 도구를 **최소 1개** 넣어라. 팩트만 나열하면 국어책이 된다.

| 도구 | 설명 | 예시 |
|------|------|------|
| 감각 형용사 | 시/청/촉/후/미각 자극 | "깜깜한 새벽", "스산한 골목" |
| 동작 묘사 | 인물의 구체적 신체 동작 | "눈 비비면서", "마이크를 쥐고" |
| 의태어/의성어 | 소리나 모양 흉내 | "쾅", "슥슥", "곤두박질" |
| 비유/직유 | 다른 것에 빗대기 | "밑 빠진 독에 물 붓기" |
| 감정 반응 | 짧은 감정 표현 | "기가 찼당께", "멘붕" |

**채널별 질감 우선순위**:
- humor: 의태어 + 동작묘사 (사투리와 자연스럽게 어울림)
- politics: 비유 + 감각 형용사 (풍자에 효과적)
- incidents: 감각 형용사 + 감정 반응 (적소에 "참혹한/끔찍한" 사용 가능. 남발만 금지)
- trend: 의태어 + 동작묘사 (MZ 대화체에 자연스러움)

**글자수 트레이드오프**: 질감 도구는 2-6자를 추가 소비. 105자 하한을 지키면서 팩트를 압축하여 질감 공간 확보.

### 전 장르 공통: 금지 규칙

1. **감탄 반복 금지**: 동일/유사 감탄 표현 연속 2회 이상 금지 ("미쳤다. 진짜 미쳤다." 금지)
2. **CTA 채널별 분리**:
   - **incidents**: 여운형("이 집은 지금도 남아있습니다.") 또는 연결형("다음 편에서 이어집니다."). "구독/좋아요" 직접 언급 금지 — 무거운 톤을 깨뜨림.
   - **humor/trend/politics**: 판단 위임형("이런 경험 있는 사람?"), 콘텐츠 연결형("이것보다 더한 썰이 있는디유"), 또는 자연스러운 구독 유도 허용
3. **톤 혼재 금지**: humor에 "레전드"/MZ 용어, politics에 사투리, trend에 격식체 혼입 금지
4. **Body 합계 글자수 최소 75자**: Hook+CTA를 제외한 Body만 75자 이상 (105자 하한 준수 보장)

---

### humor 채널 기법 (3종, 블라인드 평가 38/38/36)

#### `misunderstanding_chain` (오해 연쇄법)
- **호환**: open_loop + story/question
- **규칙**: Hook에서 오해 예고 → Body 씬1 최초 오해(사소) → 씬2 연쇄 오해("그래갖고") → 씬3 해소가 더 웃긴 반전 → CTA 경험 공유
- **핵심**: 오해는 일상적이고 사소해야 한다. 감탄사 "워메" 1회만.

#### `role_reversal_story` (역전 관계법)
- **호환**: curiosity_gap + contrast/story
- **규칙**: Hook에서 강자/약자 관계 설정+역전 암시 → 씬1 강자의 부당 행동 → 씬2 "근디 이 사람이유..." 약자 배경 폭로 → 씬3 역전 결과 → CTA 판단 위임
- **핵심**: 강자를 직접 비난 금지. 상황 묘사만.

#### `deadpan_absurd` (무표정 황당법)
- **호환**: pattern_interrupt + bold_claim/shock_stat
- **규칙**: Hook에서 황당한 결과를 담담하게 → Body 전체 간접 화법(~했다고 해유) → 황당 디테일 3개+ → 마지막에 당사자 반응 인용("본인은 괜찮다 했당께") → CTA 콘텐츠 연결형
- **핵심**: 화자 감정 표현 전체 1회만. 담담함이 웃음의 원천.

---

### politics 채널 기법 (2종, 블라인드 평가 36/50 PASS + 33/50 조건부)

#### `self_contradiction_mirror` (자기모순 거울법)
- **호환**: proof_first + contrast/bold_claim
- **규칙**: Hook에서 과거 발언 인용(출처 병기) → Body 씬1 발언 맥락 압축 → 씬2-3 현재 행동 팩트(수치) 대비 → CTA 판단 위임
- **핵심**: 직접 비난 단어 금지. 발언-행동 병치만으로 시청자가 판단.

#### `timeline_collapse` (타임라인 붕괴법) — 조건부
- **호환**: proof_first + shock_stat/bold_claim
- **규칙**: Hook에서 최근 공식 발표(수치) → Body에서 시간순 3-4개 발표 나열(날짜+수치) → 변화폭 명시 → "문제는 이겁니다" → CTA 판단 위임
- **⚠️ 주의**: 감정적 선동 표현 금지 ("불판 위", "눈물 난다" 등). Don't Rule 3 위반 위험. 풍자는 팩트 나열+반어로만.

---

### incidents 채널 기법 (1종, 블라인드 평가 35/50 조건부)

#### `silent_number` (침묵의 숫자법) — 조건부
- **호환**: proof_first + shock_stat/bold_claim
- **규칙**: Hook에서 숫자 하나만 제시(맥락 없이) → 씬1 표면적 의미 → 씬2-3 이면의 실제 맥락 → CTA 판단 위임
- **⚠️ 주의**: 감정 형용사("끔찍한") 대신 수치 대비로 무게감. Body 합계 최소 85자. 선정적 질감 금지.
- **source.md 필수**: 실제 사건 데이터만 사용. 가공 시나리오 금지.

---

### trend 채널 기법 (2종, 블라인드 평가 36/35 조건부)

#### `data_flex` (데이터 플렉스법) — 조건부
- **호환**: proof_first/pattern_interrupt + shock_stat/contrast
- **규칙**: Hook에서 숫자 하나 → 씬1 체감 비교(일상 비유로 환산) → 씬2 "근데 더 웃긴 건" + 2차 수치 → CTA 시청자 자기 데이터 요청
- **⚠️ 주의**: Body 합계 최소 85자. 감탄 연속 2회 금지. 가르치는 톤 금지.

#### `before_after_snap` (비포애프터 스냅법) — 조건부
- **호환**: pattern_interrupt/curiosity_gap + contrast/bold_claim
- **규칙**: Hook에서 "옛날 방식" 한 줄 → 씬1 "지금은" 전환 → 씬2 수치로 증명 → CTA 양자택일 질문
- **⚠️ 주의**: Body 합계 최소 85자. Hook이 MZ 톤과 괴리되지 않도록 ("비즈니스" 같은 딱딱한 단어 지양).
