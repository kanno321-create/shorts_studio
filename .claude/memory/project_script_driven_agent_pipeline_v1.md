---
name: project_script_driven_agent_pipeline_v1
description: Ryan Waller v4 에서 정의된 script-driven 3-agent 영상 제작 파이프라인 SSOT. Agent 0~5 + Inspector 역할 + INVARIANT 3-rule 준수 방식. 향후 모든 영상 작업 템플릿.
type: project
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
pipeline_version: v1
---

# Script-Driven Agent Pipeline v1 — SSOT

대표님 세션 #34 지시로 확립된 영상 제작 파이프라인. 향후 모든 쇼츠/영상에 템플릿 적용.

## INVARIANT 3-Rule (모든 에이전트 필수 준수)

1. `feedback_every_agent_reads_script_first.md` — 대본 먼저 읽기
2. `feedback_script_markers_absolute_compliance.md` — 대본 표현 그대로 반영, 벗어남 금지
3. `feedback_agents_require_visual_analysis.md` — Claude Opus 4.7 subagent 로 key frame 시각 판정

## Agent 역할 매트릭스

| Agent | 이름 | 입력 | 출력 | INVARIANT 적용 |
|-------|------|------|------|----------------|
| **Agent 0** | Script Shot-Breakdown | script_v*.json (narration SSOT) | script_v4.json (22 shots + markers) | Rule 1, 2 |
| **Agent 1** | Asset Sourcer | script_v4 + .env keys | sources/real_v4/ + manifest_v4.json + Claude 시각 판정 | Rule 1, 2, **3** |
| **Agent 2** | Video Producer | script_v4 + manifest_v4 + Kling API | sources/shot_final/<shot_id>_final.mp4 × 22 | Rule 1, 2, **3** |
| **Agent 3** | TTS Generator | script_v4 (narration + emotion markers) | narration_v4.mp3 + narration_timing_v4.json | Rule 1, 2 |
| **Agent Subtitle** | Subtitle Generator | script_v4 + narration_timing_v4 | subtitles_remotion_v4.{json,ass,srt} | Rule 1, 2 |
| **Agent Spec** | Visual Spec Assembler | script_v4 + shot_final/ + timing | visual_spec_v4.json (clips + outro-last assertion) | Rule 1 |
| **Agent 5** | Render | visual_spec + narration + subtitles | final_v4.mp4 | - (orchestration) |
| **Agent 4 Inspector** | Vision Inspector | final_v4.mp4 + script_v4 | inspect_report_v4.md + Claude 시각 검사 | Rule 1, **3** |

## 데이터 흐름

```
scripter (or human) → script_v1.json
                ↓
Agent 0 (shot breakdown + markers) → script_v4.json (SSOT)
    ├──→ Agent 1 (sourcer, Claude subagent vision) ──→ manifest_v4.json + sources/real_v4/
    ├──→ Agent 3 (TTS) ──→ narration_v4.mp3 + timing_v4.json
    │                              ↓
    │                       Agent Subtitle ──→ subtitles_remotion_v4
    │
    └──→ (script_v4 + manifest_v4 + timing) → Agent 2 (producer, Claude subagent verify)
                                                ↓
                                           sources/shot_final/<shot_id>_final.mp4 × 22
                                                ↓
                                       Agent Spec ──→ visual_spec_v4.json
                                                ↓
                                       Agent 5 (Render) ──→ final_v4.mp4
                                                ↓
                                       Agent 4 Inspector (Claude subagent) ──→ report
```

## Critical Files (향후 모든 영상 적용)

- `output/<episode>/script_v4.json` — Agent 0 SSOT (shots + markers)
- `scripts/experiments/*_v4.py` — 에이전트별 실행 스크립트 (neugung episode 마다 fork)
- `scripts/orchestrator/video_sourcing/` — 재사용 검색·다운로드 모듈
- `scripts/orchestrator/api/{typecast,kling_i2v}.py` — TTS + I2V (현재는 experiment 스크립트에서 직접 SDK 호출)
- `C:\Users\PC\.claude\plans\glistening-snacking-sparkle.md` — v4 pipeline 설계 기준 (향후 신규 영상도 이 plan 을 참조)

## 재사용성 (향후 영상 제작)

**새 영상 제작 시** (세션 #35~):
1. scripter 단계에서 script_v1 (narration) 생성
2. Agent 0 (shot breakdown) 실행 → script_v4.json
3. Agent 1~5 순서대로 실행 (episode id 만 교체, 로직 재사용)
4. 각 단계 subagent 판정 필요 시 `subagent_type="general-purpose"`, `model="opus"`

**에피소드 고유 부분**:
- `script_v4.json` 의 narration / markers / keywords (episode-specific)
- `shot_final/<shot_id>_final.mp4` (episode-specific)

**재사용 (episode-invariant)**:
- 모든 \*_v4.py 스크립트의 로직
- Kling 공식 API JWT 호출 패턴
- Typecast PresetPrompt 패턴
- visual_spec 빌더 로직 (outro-last assertion)
- Remotion composition

## Cross-reference

- `feedback_every_agent_reads_script_first.md` (Rule 1)
- `feedback_script_markers_absolute_compliance.md` (Rule 2)
- `feedback_agents_require_visual_analysis.md` (Rule 3)
- `feedback_shot_level_asset_1to1_mapping.md`
- `feedback_outro_signature_must_be_last_clip.md`
- `feedback_whisper_volume_normalize.md`
- `feedback_shot_filename_label_explicit.md`
- `glistening-snacking-sparkle.md` plan — v4 상세 실행 스펙
