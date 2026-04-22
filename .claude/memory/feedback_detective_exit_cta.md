---
memory_id: feedback_detective_exit_cta
category: feedback
status: active
imprinted_session: 33
imprinted_date: 2026-04-22
last_updated: 2026-04-22
phase: 16-01
channel: incidents
source_refs:
  - .preserved/harvested/theme_bible_raw/incidents.md section 10
  - .preserved/harvested/skills_raw/channel-incidents/SKILL.md
  - 대표님 세션 #33 직접 피드백 (2026-04-22)
failure_mapping: []
---

# feedback: 탐정 퇴장 CTA 10 pool 돌려쓰기, 식상 반복 금지

## 규칙

탐정 퇴장 CTA 는 사전 승인된 **10개 pool 에서 선택** — 매 에피소드마다 다른 것으로 **돌려쓰기** (같은 문구 연속 3편 이상 반복 금지). 과공손 뵙겠습니다 / 인사드립니다 / 감사드립니다 류는 탐정 캐릭터 톤 (딱딱하고 무게감 있는 1인칭) 과 충돌하므로 금지. 구독 강요 금지.

**2026-04-22 세션 #33 대표님 직접 피드백**:
> "마지막에 이 기록을 아직 닫지 못했다 이런 식상한 멘트 ㄴㄴ. 끝맺음은 여러개 정해놓고 돌려써라, 그렇게 되어있을건데 쇼츠나베랄에, 그럼 전 다음 사건으로 가보겠습니다 이런거 좋잖아"

**핵심 교훈**: 같은 CTA 반복 시 **식상함 유발 + 브랜드 약화**. "이 기록을 아직 닫지 못했습니다" 같은 단일 문구만 매번 쓰면 시청자 피로도 급증. 채널바이블 §10 10-pool 원칙 **엄격 적용 + rotation 강제**.

## 승인 Pool (10개) — Tone / Use-case 매핑

에피소드 Reveal 톤 / 사건 종결 여부에 맞춰 적합한 것 선택.

| # | CTA 문구 | Tone | 적합한 사건 유형 |
|---|---------|------|-----------------|
| 1 | 저는 이 사건을, 아직 놓지 않았습니다. | 끈질김, 미련 | 미제 사건 / 범인 미검 |
| 2 | 이 기록을, 다시 펼칠 날이 올지도 모르겠습니다. | 불확실, 여운 | 미제 / 열린 결말 |
| 3 | 답은 아직, 이 현장 어딘가에 있습니다. | 미스터리 유지 | 미제 / 단서 부족 |
| 4 | 저는 이곳을 떠납니다. 사건은, 남습니다. | 냉정한 퇴장, 공허 | 해결됐지만 유족 상처 남은 사건 |
| 5 | 오늘의 기록은, 여기까지입니다. | 담담한 마무리 | 사실 전달형 / 중립 |
| 6 | 그럼 저는, 다음 기록으로 가보겠습니다. | 담담, 다음 편 기대 | 범용 (대표님 선호 스타일) |
| 7 | 이 사건은, 저를 떠나지 않을 겁니다. | 개인적 무게 | 유족 비극 강조 / 억울함 |
| 8 | 저는 오늘, 이 기록을 덮습니다. | 무거운 종결 | 끔찍한 결말 / 재판 종결 |
| 9 | 진실은 때로, 너무 늦게 도착합니다. | 회한, 사법 불신 | 경찰 과실 / 억울한 죽음 / 판결 기각 |
| 10 | 다음 사건이, 저를 기다리고 있습니다. | 담담, 다음 편 | 범용 (대표님 선호 스타일 변형) |

## 예시 — 위반 (과거 실수)

- ❌ 다음에 또 뵙겠습니다. 구독 눌러주세요. (과공손 + 구독 강요)
- ❌ "저는 이 사건을 아직 놓지 않았습니다" 를 매 에피소드마다 반복 (식상 / rotation 위반)

## 선택 가이드 (scripter / script-polisher 용)

1. 에피소드의 **감정 여운 1개** 확인 (incidents bible §3 목표):
   - **불쾌한 긴장감** → #1, #7, #8
   - **인간에 대한 공허함** → #4, #9
   - **중립 사실 전달** → #5, #6, #10
   - **미스터리 유지** → #2, #3
2. **최근 3편 CTA 확인** — 같은 번호 연속 3편 금지 (브랜드 rotation)
3. 시리즈 Part N (N < M) 인 경우: CTA + "다음 기록에서, 이어집니다." 추가 (incidents bible §10 연결형)

## 근거

- 채널바이블: project_channel_bible_incidents_v1 (section 10 — 10 pool 원칙)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md §10
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
- 대표님 세션 #33 피드백 (2026-04-22) — 식상 반복 유의 + "다음 사건 가보겠습니다" 스타일 선호

## Cross-reference

- `.claude/memory/feedback_watson_cta_pool` — 왓슨 CTA 10 pool (동일 원칙, 해요체)
- `.claude/memory/feedback_series_ending_tiers` — 시리즈 Part 1/2/3 CTA 차등
- `.claude/memory/feedback_outro_signature` — 탐정 정면 → 뒤돌아 걸어감 시각적 시그니처
