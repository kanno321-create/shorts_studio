---
memory_id: feedback_duo_natural_dialogue
category: feedback
status: active
imprinted_session: 33
imprinted_date: 2026-04-22
phase: 16-01
channel: incidents
source_refs:
  - .preserved/harvested/theme_bible_raw/incidents.md section 7
  - .preserved/harvested/skills_raw/channel-incidents/SKILL.md
failure_mapping:
  - FAIL-SCR-004
---

# feedback: 왓슨 질문 키워드 >= 60% 탐정 답변 첫 문장 포함

## 규칙

듀오 포맷 (탐정 + 왓슨/즌다) 에서 왓슨이 질문하면, 탐정은 첫 문장에서 그 질문의 핵심 키워드를 >= 60% 포함해 정면 호응해야 한다. 키워드 미스매치는 대화 흐름 붕괴 + 교과서 낭독체로 빠지는 FAIL-SCR-004 의 주원인.

## 예시 - 준수

(왓슨) 범인은 누구였죠? -> (탐정) 범인은 끝내 밝혀지지 않았습니다.

## 예시 - 위반

(왓슨) 범인은 누구였죠? -> (탐정) 사건 당일 비가 왔습니다. (키워드 0% 대응, 화제 전환)

## 근거

> 왓슨 첫 질문 -> 탐정 답변 (feedback_duo_natural_dialogue). (incidents.md section 7 갈등오해)

해당 섹션은 project_channel_bible_incidents_v1 박제본 section 7 에도 동일 cross-reference 되어 있다. Producer (scripter / script-polisher / voice-producer / asset-sourcer) 와 Inspector (ins-korean-naturalness / ins-narrative-quality / ins-subtitle-alignment / ins-render-integrity) 가 에피소드 생성 및 GATE 심사에서 본 규칙을 참조한다.

## Cross-reference

- 채널바이블: project_channel_bible_incidents_v1 (section 7)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
