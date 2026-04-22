---
memory_id: feedback_veo_supplementary_only
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

# feedback: I2V 보조용만, 실제 이미지 crawling 최우선

## 규칙

incidents 채널의 시각 자료는 실제 사진/영상 크롤링 최우선, AI 생성물은 보조용. 실물 자료가 많을수록 사건 신뢰도와 몰입감이 증가한다. I2V 씬은 한 편당 <= 2 권장. CLAUDE.md 금기 #11 과 결합: 기존 시그니처 v4 만 재사용, 신규 생성 절대 금지.

## 예시 - 준수

60초 영상 = 실제 현장 사진 8장 + 뉴스 풋티지 2컷 + I2V 재현 1컷 (보조) + 인트로 시그니처 v4 (기존 자산)

## 예시 - 위반

60초 영상 = 전체 I2V 생성물 9컷 (실제 자료 0, 신규 호출)

## 근거

> 보조용만, 실제 이미지 크롤링 최우선 (feedback_veo_supplementary_only). (incidents.md section 9)

해당 섹션은 project_channel_bible_incidents_v1 박제본 section 9 에도 동일 cross-reference 되어 있다. Producer (scripter / script-polisher / voice-producer / asset-sourcer) 와 Inspector (ins-korean-naturalness / ins-narrative-quality / ins-subtitle-alignment / ins-render-integrity) 가 에피소드 생성 및 GATE 심사에서 본 규칙을 참조한다.

## Cross-reference

- 채널바이블: project_channel_bible_incidents_v1 (section 9)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
