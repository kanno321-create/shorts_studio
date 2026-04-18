# Channel Bibles

> Phase 50 Plan 50-01 산출물 디렉토리.
> 채널별 **10줄 규격서**만 담는다. 현재는 Plan 50-00이 템플릿만 준비한 상태 (2026-04-17).

---

## 목적

1. **NLM 쿼리 입력** — Plan 50-02 NLM Fetcher가 각 채널 바이블 10줄을 NotebookLM에 투입
2. **검사관 군단 기준치** — Plan 50-03 `ins-bible-fit` / `ins-forbidden-words` / `ins-channel-voice` 가 정량 체크에 사용
3. **단일 진실 원천** — 기존 `channel-*` SKILL.md 100줄+ 대신 **10줄 축약**이 프롬프트에 직접 삽입

기존 `.claude/skills/channel-*/SKILL.md` 는 **참조 스킬**로 유지. 바이블은 **프롬프트 인라인 주입** 전용.

---

## 10줄 필수 필드 (D-50-02)

각 파일은 `.claude/channel_bibles/{channel}.md` 로 저장한다.
아래 10개 필드를 정확히 그 순서로 작성.

| # | 필드 | 설명 | 예시 |
|---|------|------|------|
| 1 | **타겟** | 주 시청자 연령·성별·관심사 | "30~50대 남성, 범죄·미스터리 관심" |
| 2 | **길이** | 단편/시리즈 초수 범위 | "단편 50-60s / 시리즈편 90-120s" |
| 3 | **목표** | 감정 1개 또는 정보 1개 | "불안 + 추리 쾌감" |
| 4 | **톤** | 말투 + 금지 표현 | "탐정 독백 1인칭, 습니다체, 감정 과잉 금지" |
| 5 | **금지어** | 블랙리스트 5~10개 | "충격, 경악, 믿을 수 없는, 역대급, 반드시" |
| 6 | **문장규칙** | 어미·길이·쉼표 규정 | "종결 ~습니다. 한 컷 한 호흡. 2절 이상 금지" |
| 7 | **구조** | 4단계 or 5단계 흐름 | "사건전 → 사건 → 사건후 → 평가 → 공포" |
| 8 | **근거규칙** | 숫자·비교·사례 밀도 | "섹션당 구체적 숫자 1+ 또는 사례 1+" |
| 9 | **화면규칙** | 컷당 비주얼 힌트 | "실제 사진 ≥ 70%, Veo 보조 30%, 영상 우선" |
| 10 | **CTA규칙** | 시그니처 + 구독 유도 | "Part1: 시그니처 '놓지 않았습니다' / Part2: 독백 / Part3: 경각심" |

---

## 템플릿

신규 채널 바이블은 `.claude/channel_bibles/_template.md` 참조 (Plan 50-01에서 작성).

```markdown
---
channel: <slug>
version: v1.0
approved_by: 대표님
approved_date: 2026-04-XX
lineage: .claude/skills/channel-<slug>/SKILL.md
---
# <채널명> 바이블 v1.0

1. **타겟**: ...
2. **길이**: ...
3. **목표**: ...
4. **톤**: ...
5. **금지어**: ...
6. **문장규칙**: ...
7. **구조**: ...
8. **근거규칙**: ...
9. **화면규칙**: ...
10. **CTA규칙**: ...
```

---

## 대상 채널 (6개)

- `incidents.md` — 사건기록부 (파일럿)
- `wildlife.md` — WildCamera
- `documentary.md` — Global English Documentary
- `humor.md` — 충청도 사투리 유머
- `politics.md` — 정치 풍자
- `trend.md` — MZ 트렌드

파일럿: **incidents 먼저** (사건기록부 1개로 방법론 검증 → 5채널 확장).

---

## 참조

- Plan 50-00: `../../../.planning/phases/50-script-quality-research/50-00-foundation-research-PLAN.md`
- Plan 50-01: `../../../.planning/phases/50-script-quality-research/50-01-channel-bibles-PLAN.md`
- 사건기록부 초안: `../../../output/_research/phase-50-preparation/07-channel-bible-incidents-draft.md`
- D-50-02 결정: `../../../.planning/phases/50-script-quality-research/50-CONTEXT.md`
