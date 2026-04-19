---
category: script
status: ready
tags: [nlm, prompt-template, script-production, 2-step, longform]
sources: [shorts_naberal/longform/PIPELINE.md, SCRIPT_SKILL.md, SCRIPT_QUALITY_GATE_CONTRACT.md]
session_origin: [70, 77 — 대표님 박제 확정]
updated: 2026-04-20
---

# NLM 2-Step Script Production Template

**Scope:** shorts_studio SCRIPT gate 의 NLM 쿼리 빌더가 참조하는 **단일 진실 원천**. Step 1 사건 발굴 + Step 2 시나리오 제조의 2-노트북 분리 규약.

> ⚠️ **"발굴/제조 분리" 고정 규약** — 1-노트북 통합 방식은 세션 70 에서 폐기됨. 이전 쿼리 가설이 다음 쿼리에 오염되어 디아틀로프 사건에서 자의적 내용 변경 사고. 혼합 시도 금지.

---

## Notebook Assignment

| Step | 역할 | library.json ID | URL |
|------|------|----------------|-----|
| Step 1 | 사건 발굴 + 팩트 추출 | `crime-stories-+-typecast-emotion` | https://notebooklm.google.com/notebook/d9aa8c99-6b27-4797-b09a-8c3e509b1e11 |
| Step 2 | 시나리오 제조 (컷 배열 JSON) | `script-production-deep-research` | https://notebooklm.google.com/notebook/64bcab8f-b487-4089-a528-c243cc4b5382 |

---

## Step 1 Prompt Skeleton — 사건 발굴

`nlm-fetcher` 에이전트 또는 수동 쿼리 시 다음 skeleton 을 채워 1회 submit. 실시간 타이핑 금지.

```
[채널 상황·시리즈 맥락]
{channel_context}
{series_context}

[지시]
1. 이 노트북 소스에서 "대박날 것 같은" 사건 후보 3~5개 제시 (훅 강도·반전 임팩트·
   사회적 공명·영상자료 확보 가능성 기준).
2. 선정 후보 각각 제공: 타임라인 / 인물관계도 / 결정적 증거 / 반전 포인트 2~3개 /
   주의사항 / 영상·이미지 자료 존재 여부.
3. 이전 대화 무시. 이 프롬프트만 기준.

[제외 조건]
{이미 제작한 사건 N건 나열 — 운영 중 누적 / 국적·언어 제약 있을 시 명시}
```

**기대 출력**: `source.md` (5,000-10,000자, 22+ 출처). 나베랄은 결과를 직접 대본으로 변환하지 않음 — Step 2 로 전달.

---

## Step 2 Prompt Skeleton — 시나리오 제조 (🔴 컷 단위 JSON 출력)

```
[전체 내용 먼저]
{source.md 전문 ← Step 1 결과}
{채널 규칙 블록}
{듀오 포맷 블록 — 탐정/조수 대화 패턴 5종 참조}

[묘사 깊이 — 필수 4요소, 각 컷에 포함]
1. 인상 (시각적 톤)
2. 사물·사람의 움직임 (동작·시선·자세·카메라 워크)
3. 감정 (인물 심리)
4. 분위기 (공간·조명·소리·날씨)

[리텐션 구조]
0:15 훅 / 3:00 버스트 / 7~8분 최대 반전 / 10분 결정적 증거 예고 /
12~15분 해결+교훈+CTA+다음편

[🔴 컷 분할 — 가장 중요]
- 한 컷씩 따로 제작할 것이므로 컷 단위로 분할 출력
- 컷 길이 가변: 긴 컷(15~30초) + 짧은 컷(2~5초) 혼재 OK
- JSON 배열로 출력:
  {
    "cut_id": "c001",
    "act": 1,
    "duration_s": 8.5,
    "narration": "...",
    "speaker": "detective" | "assistant",
    "impression": "...",       // 시각적 톤
    "motion": "...",            // 동작·시선·자세·카메라 워크
    "emotion": "...",           // 인물 심리
    "atmosphere": "...",        // 공간·조명·소리·날씨
    "visual_type": "footage" | "image" | "runway_i2v" | "illustration",
    "visual_query": "...",      // footage/image 검색어
    "runway_prompt": "..."      // runway_i2v 일 때만 — Gen-4.5 용 motion + camera direction
  }

[자체 점검]
- 컷 수: {예상 컷 수}개 내외
- 총 글자수: 6,200~7,100자 (longform 15분 기준, 7.9자/초)
- 4막 비율: 20 / 33 / 27 / 20
- 리텐션 4지점 모두 포함
- 묘사 4요소 각 컷 포함 여부 확인

이전 대화 무시.
```

**기대 출력**: JSON 배열 (단일 block). 통짜 대본/서사문은 **즉시 follow-up 으로 재출력 요청**.

---

## Follow-up Prompt Patterns (NLM 거부 시)

| 상황 | Follow-up 문구 |
|------|--------------|
| 컷 단위가 아닌 통짜 출력 | "앞의 답변을 컷 단위 JSON 배열로 다시 출력해 주세요. 각 컷에 impression/motion/emotion/atmosphere 4요소 누락 없이." |
| 묘사 4요소 누락 컷 발견 | "컷 c{N}에 motion 또는 atmosphere 필드가 누락되었습니다. 해당 컷만 4요소 모두 채워서 재출력해 주세요." |
| 글자수 미달/초과 | "총 글자수가 {실제}자로 목표({6200-7100})자 범위를 벗어났습니다. Act {가장 차이 큰 막}을 {증감}하여 재조정해 주세요." |
| visual_type 잘못 | "visual_type 에 허용되지 않은 값 '{잘못된 값}' 사용. footage/image/runway_i2v/illustration 중 하나만 허용." |
| runway_prompt 누락 | "visual_type='runway_i2v' 컷에 runway_prompt 필드가 비어 있습니다. Gen-4.5 용 motion + camera direction 채워서 재출력해 주세요." |

---

## 운영 규칙 (세션 70·77 박제)

- **대본 본문은 NLM 단독 작성** — 나베랄은 텍스트 수정 금지. 수정은 follow-up 프롬프트로만.
- **NLM 일일 50 쿼리 한도** — 선제 체크리스트 강제 (수량/글자수/전체출력/자체점검).
- **외주 원칙** — NLM = 시나리오 / Typecast = TTS / Runway Gen-4.5 = I2V / 나베랄 = 기획+프롬프트+검수+마무리.
- **실시간 타이핑 금지** — 완성된 1개 문자열로 작성 후 붙여넣기. Enter 키 누를 때마다 쿼리 발동 → 한도 급속 소진.
- **이전 대화 무시** 문구 **필수** — 컨텍스트 오염 방지.

---

## Related Wiki Nodes

- [[QUALITY_PATTERNS]] — Patterns A-D (씬 플로우 공식 / 문장 길이 리듬 / 이음쇠 분포 / 감정 전달)
- [[4ACT_STRUCTURE]] — 4막 시간/글자수 할당 + 대화 배치 규칙
- [[../continuity_bible/MOC]] — 채널 바이블 prefix (assembler 자동 주입)
- [[../render/runway_gen4_5]] — Runway Gen-4.5 어댑터 스펙 (작성 예정)

---

*Extracted 2026-04-20 from shorts_naberal/longform PIPELINE.md + SCRIPT_SKILL.md + SCRIPT_QUALITY_GATE_CONTRACT.md. 원본은 `.preserved/harvested/` 에 읽기 전용 보존. 이 노드는 shorts_studio 운영용 재서술 — 코드 흡수 아님, 패턴 추출.*
