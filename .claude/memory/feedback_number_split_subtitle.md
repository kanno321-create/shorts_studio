---
memory_id: feedback_number_split_subtitle
category: feedback
status: active
imprinted_session: 33
imprinted_date: 2026-04-22
phase: 16-01
channel: incidents
source_refs:
  - .preserved/harvested/theme_bible_raw/incidents.md section 9
  - .preserved/harvested/skills_raw/channel-incidents/SKILL.md
failure_mapping: []
---

# feedback: 숫자 + 단위는 한 단어 유지

## 규칙

자막에서 숫자 + 단위 조합 (1,701통, 7명, 3시간 뒤) 은 반드시 한 단어 (공백 없는 토큰 또는 한 줄 내) 로 유지. 2줄 이상 분할은 시청자의 수치 인지 단절을 유발.

## 예시 - 준수

편지 1,701통 (한 단어)

## 예시 - 위반

1,701 / 통 (2토큰 분할, 수치 인지 단절)

## 근거

> 숫자 쪼개짐 금지 (1,701통 한 단어 유지, feedback_number_split_subtitle). (incidents.md section 9)

해당 섹션은 project_channel_bible_incidents_v1 박제본 section 9 에도 동일 cross-reference 되어 있다. Producer (scripter / script-polisher / voice-producer / asset-sourcer) 와 Inspector (ins-korean-naturalness / ins-narrative-quality / ins-subtitle-alignment / ins-render-integrity) 가 에피소드 생성 및 GATE 심사에서 본 규칙을 참조한다.

## Cross-reference

- 채널바이블: project_channel_bible_incidents_v1 (section 9)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
