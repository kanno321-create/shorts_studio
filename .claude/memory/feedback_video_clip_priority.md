---
memory_id: feedback_video_clip_priority
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

# feedback: 영상:이미지 비율 >= 30%

## 규칙

쇼츠 한 편의 총 clip 구성 중 동영상 (I2V 생성물 + 실제 영상 풋티지) 비율이 >= 30% 여야 한다. 순수 스틸 이미지 배열은 Ken Burns 줌팬 적용하더라도 AI 슬라이드쇼 감각이 남는다. 60초 영상 기준 영상 clip 총 >= 18초.

## 예시 - 준수

60초 영상 = I2V 22초 + 실제 영상 8초 + 이미지 30초 (영상 50%)

## 예시 - 위반

60초 영상 = Ken Burns 이미지만 60초 (영상 0%, 슬라이드쇼 감각)

## 근거

> 영상:이미지 >= 30% (feedback_video_clip_priority). (incidents.md section 9)

해당 섹션은 project_channel_bible_incidents_v1 박제본 section 9 에도 동일 cross-reference 되어 있다. Producer (scripter / script-polisher / voice-producer / asset-sourcer) 와 Inspector (ins-korean-naturalness / ins-narrative-quality / ins-subtitle-alignment / ins-render-integrity) 가 에피소드 생성 및 GATE 심사에서 본 규칙을 참조한다.

## Cross-reference

- 채널바이블: project_channel_bible_incidents_v1 (section 9)
- 원본 SSOT: .preserved/harvested/theme_bible_raw/incidents.md
- SKILL 파생: .preserved/harvested/skills_raw/channel-incidents/SKILL.md
