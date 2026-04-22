---
memory_id: feedback_script_tone_seupnida
category: feedback
status: active
imprinted_session: 33
imprinted_date: 2026-04-22
phase: 16-01
channel: incidents
source_refs:
  - .preserved/harvested/theme_bible_raw/incidents.md section 4
  - .preserved/harvested/skills_raw/channel-incidents/SKILL.md
failure_mapping:
  - FAIL-SCR-011
  - FAIL-SCR-016
---

# feedback: 종결어미 습니다/입니다/였죠 만

## 규칙

incidents 채널 탐정 독백 종결어미는 습니다 / 입니다 / 였죠 3종만 허용. 어요/해요/요 체 혼입 절대 금지. 일상 대화체가 섞이면 탐정 1인칭 독백의 무게감이 무너지고 국어책 낭독체로 변질된다 (FAIL-SCR-011 원인).

## 예시 - 준수

그는 그날 밤 돌아오지 않았습니다.

## 예시 - 위반

그는 그날 밤 돌아오지 않았어요.

## 근거

> 종결어미 습니다/입니다/였죠 만 (FAIL-SCR-011 방지, feedback_script_tone_seupnida). (incidents.md section 4)

해당 섹션은 project_channel_bible_incidents_v1 박제본 section 4 에도 동일 cross-reference 되어 있다. Producer (scripter / script-polisher / voice-producer / asset-sourcer) 와 Inspector (ins-korean-naturalness / ins-narrative-quality / ins-subtitle-alignment / ins-render-integrity) 가 에피소드 생성 및 GATE 심사에서 본 규칙을 참조한다.

## Cross-reference

- 채널바이블: project_channel_bible_incidents_v1 (section 4)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
