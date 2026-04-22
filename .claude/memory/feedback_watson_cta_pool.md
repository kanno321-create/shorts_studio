---
memory_id: feedback_watson_cta_pool
category: feedback
status: active
imprinted_session: 33
imprinted_date: 2026-04-22
phase: 16-01
channel: incidents
source_refs:
  - .preserved/harvested/theme_bible_raw/incidents.md section 10
  - .preserved/harvested/skills_raw/channel-incidents/SKILL.md
failure_mapping: []
---

# feedback: 왓슨 CTA 10 pool

## 규칙

왓슨 (즌다) 화자가 마지막 CTA 를 담당하는 경우, 사전 승인 10 pool 에서 랜덤 선택. 탐정 퇴장 pool 과 달리 시청자에게 한 단계 더 친근하게 접근 가능하지만, 급전환 없이 탐정 독백의 무게감에서 자연 전환해야 한다 (일본어 레퍼런스 mary-celeste-jp 패턴).

## 예시 - 승인 pool (>= 5건 나열, 전체 10 pool 에서 발췌)

- 이런 미스터리, 더 궁금하지 않으신가요.
- 현장은 아직 남아 있습니다. 다음 기록에서 다시 만나요.
- 탐정의 기록을 따라가 보시겠어요.
- 이 사건, 여러분은 어떻게 보셨습니까.
- 다음 기록도 함께 펼쳐 보시죠.

## 예시 - 위반

구독 좋아요 알림설정 부탁드립니다! (급전환 + 과도한 요구)

## 근거

> 왓슨 CTA 풀 10개 (feedback_watson_cta_pool). (incidents.md section 10)

해당 섹션은 project_channel_bible_incidents_v1 박제본 section 10 에도 동일 cross-reference 되어 있다. Producer (scripter / script-polisher / voice-producer / asset-sourcer) 와 Inspector (ins-korean-naturalness / ins-narrative-quality / ins-subtitle-alignment / ins-render-integrity) 가 에피소드 생성 및 GATE 심사에서 본 규칙을 참조한다.

## Cross-reference

- 채널바이블: project_channel_bible_incidents_v1 (section 10)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
