---
memory_id: project_channel_preset_incidents
source_triangulation:
  - .preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json
  - .preserved/harvested/baseline_specs_raw/nazca-lines/visual_spec.json
  - .preserved/harvested/baseline_specs_raw/roanoke-colony/visual_spec.json
status: production_active
imprinted_session: 33
imprinted_date: 2026-04-22
phase: 16-04
channel: incidents
---

# incidents 채널 preset — v1.0 박제

> shorts_naberal 3 production 에피소드 triangulation 결과. visual_spec.json 생성 시 이 값들을
> scripts/orchestrator/api/visual_spec_builder.load_channel_preset() 의 hardcoded default 로 사용.

## channelName
사건기록부 — 3 episode 전수 동일 (zodiac-killer, nazca-lines, roanoke-colony).

## accentColor
#FF2200 — crimson red, incidents brand color (zodiac-killer 기준). nazca-lines/roanoke-colony 는
#FFD000 사용 — 에피소드별 topic 에 맞춰 accentColor 조정 가능. builder 는 blueprint.title_display.accent_color 우선,
없으면 #FF2200 fallback.

## fontFamily
허용: BlackHanSans / DoHyeon / NotoSansKR (Google Fonts only — shorts-designer 스킬 문서 명시)
금지: Pretendard (shorts-designer 스킬 문서 명시 금지)
기본값: BlackHanSans (zodiac-killer + roanoke-colony 공통).

## subtitlePosition
0.8 — 하단 (incidents 화면규칙 9 "자막 6-12자, 의미단위 그룹핑"). zodiac-killer + roanoke-colony 공통. nazca-lines 는 0.65 (예외).

## subtitleHighlightColor
#FFFFFF — word highlight 현재 단어 색상 (zodiac-killer + roanoke-colony 공통).
nazca-lines 는 #FFD000 (예외, accentColor 와 동일).

## subtitleFontSize
68 (1080x1920 기준, 24-128 범위 내) — zodiac-killer + roanoke-colony 공통.
nazca-lines 는 88 (예외).

## hashtags 템플릿
기본: #쇼츠 #범죄 #미제사건 #실화
topic 특화 시 3 hashtag 추가 허용 (총 <= 7 — YouTube Shorts 권장 상한).

## transitions 풀 (8종)
- fade (default)
- glitch (20 frames, 강)
- rgb-split (30 frames, 중)
- zoom-blur (25 frames, 중)
- light-leak (35 frames, 약-중)
- clock-wipe (30 frames, 약)
- pixelate (22 frames, 강)
- checkerboard (30 frames, 약-중)

할당 공식: title_hash %% 8 round-robin (visual_spec.clipDesign[] 에 개별 지정 없을 때만).

## 캐릭터 좌우 의미 고정 (Q4 매핑)
- characterLeftSrc = assistant (왓슨/조수) — <episode>/character_assistant.png
- characterRightSrc = detective (Morgan/탐정) — <episode>/character_detective.png
- zodiac-killer 및 roanoke-colony 양쪽 baseline 이 동일 convention 확인
- incidents-jp (Phase 17+) 도 동일 좌우 규칙, 파일 내용만 일본 캐릭터 교체

## durationInFrames 공식
audio_duration_seconds * 30 (int round). ffprobe 실측 narration.mp3 기준
(Narration Drives Timing — Plan 16-02 Pattern 4).

## clipDesign movement 정책
- VALID_MOVEMENTS = {"zoom_in", "zoom_out", "pan_left", "pan_right"}
- None = 의도적 freeze (Pitfall 4 — _NULL_FREEZE sentinel 경유 Zod pop)
- intro/outro signature 비디오 clip 은 movement=None (정지 시그니처)
- 제공되지 않은 image clip 은 round-robin 배정 (visual_spec_builder.ROUND_ROBIN_MOVEMENTS)

## source_strategy 기준값 (incidents baseline)
- real_image_target: 11-13 (per 60s episode)
- veo_supplement: <= 2 (feedback_veo_supplementary_only)
- signature_reuse: 2 (intro + outro) 또는 1 (outro 프로그램적 — Plan 16-03 Option A)
- real_ratio: >= 0.75 (zodiac-killer 는 약 0.81)

## 재사용
asset-sourcer 가 scripts/orchestrator/api/visual_spec_builder.build() 호출 시
channel_preset 인자로 본 메모리 파일을 load_channel_preset(Path(".claude/memory/project_channel_preset_incidents.md"))
로 로드하여 전달.
