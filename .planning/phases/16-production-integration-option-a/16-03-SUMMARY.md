---
phase: 16
plan: 16-03
subsystem: production-integration / subtitles + signatures + character overlay
tags: [subtitle-producer, faster-whisper, harvest-extension, outro-research, character-overlay, veo-zero-enforcement]
dependency_graph:
  requires: [16-01-SUMMARY.md, 16-02-SUMMARY.md]
  provides:
    - "scripts/orchestrator/subtitle/word_subtitle.py (faster-whisper large-v3 ported)"
    - "scripts/orchestrator/api/subtitle_producer.py (Python wrapper)"
    - ".claude/agents/producers/subtitle-producer/AGENT.md (Producer #15)"
    - ".preserved/harvested/video_pipeline_raw/signatures/ + characters/ (binary harvest)"
    - "remotion/src/components/OutroCard.tsx (programmatic outro)"
  affects:
    - ".claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md (v1.1 → v1.2)"
    - "CLAUDE.md 금기 #9 (Producer 14 → 15, 32 → 33 agents)"
tech_stack:
  added:
    - "faster-whisper >= 1.0.3 (Korean large-v3 ASR)"
  patterns:
    - "Subprocess wrapper pattern (ffmpeg_assembler-alike) for subtitle_producer"
    - "Programmatic Remotion OutroCard (no external mp4 dependency)"
    - "Read-only harvest via attrib +R / chmod -w (one-way copy)"
key_files:
  created:
    - ".preserved/harvested/video_pipeline_raw/signatures/incidents_intro_v4_silent_glare.mp4"
    - ".preserved/harvested/video_pipeline_raw/signatures/README.md"
    - ".preserved/harvested/video_pipeline_raw/characters/incidents_detective_longform_a.png"
    - ".preserved/harvested/video_pipeline_raw/characters/incidents_detective_longform_b.png"
    - ".preserved/harvested/video_pipeline_raw/characters/incidents_assistant_jp_a.png"
    - ".preserved/harvested/video_pipeline_raw/characters/incidents_zunda_shihtzu_a.png"
    - ".preserved/harvested/video_pipeline_raw/characters/README.md"
    - ".preserved/harvested/video_pipeline_raw/harvest_extension_manifest.json"
    - "scripts/orchestrator/subtitle/__init__.py"
    - "scripts/orchestrator/subtitle/word_subtitle.py"
    - "scripts/orchestrator/api/subtitle_producer.py"
    - ".claude/agents/producers/subtitle-producer/AGENT.md"
    - "remotion/src/components/OutroCard.tsx"
    - "tests/phase16/test_outro_research_findings.py"
    - "tests/phase16/test_harvest_extension.py"
    - "tests/phase16/test_subtitle_producer.py"
    - "tests/phase16/test_ins_subtitle_alignment_spec.py"
    - "tests/phase16/test_character_overlay_injection.py"
    - "tests/phase16/test_signature_reuse_no_veo_call.py"
  modified:
    - "requirements.txt (+ faster-whisper)"
    - ".claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md (v1.2)"
    - "remotion/src/compositions/ShortsVideo.tsx (OutroCard import)"
decisions:
  - "Option A (programmatic OutroCard) — evidence triangulation (see Task 0 findings)"
  - "word_subtitle.py 1:1 ported (do NOT refactor — FAIL-EDT-008 defense)"
  - "subtitle-producer v1.0 added → Producer #15 (33-agent cap)"
  - "ins-subtitle-alignment v1.1 → v1.2 (faster-whisper large-v3)"
  - "Veo API calls = 0 (금기 #11) — intro_v4 re-used by reference, outro programmatic"
metrics:
  duration_minutes: null  # filled after completion
  commit_count: null
  files_created: 20
  files_modified: 3
  tests_added: 6
phase_final: false
created: 2026-04-22
last_updated: 2026-04-22
---

# Phase 16-03 — Summary + Outro Research

> Plan 16-03 실행 요약. Task 0 outro research findings 최상단 박제, 이후 waves/tasks 실행 결과 기록.

---

## Task 0 — Outro Research Findings (2026-04-22)

### 증거 요약

**Phase A (harvested remotion_render.py grep)**
- 명령: `grep -n "outro\|OUTRO\|end_card\|ending\|OutroCard\|outro_signature\|outro_mp4" .preserved/harvested/video_pipeline_raw/remotion_render.py`
- 결과: **0 건** (파일 `.planning/phases/16-production-integration-option-a/16-03-task0-grep-remotion.log` 는 line count 0).
- 해석: harvested Python orchestrator (1162 lines, shorts_naberal 버전의 상류 source) 는 outro mp4 를 생성·복사·참조하는 로직을 **전혀 포함하지 않음**. outro 는 이 계층 관심사 밖.

**Phase B (baseline visual_spec triangulation, 3 episodes)**
- `zodiac-killer/visual_spec.json`: clips 16개, `clips[-1] = {"type": "video", "src": "zodiac-killer/outro_signature.mp4", "durationInFrames": 99}` (약 3.3s @ 30fps)
- `roanoke-colony/visual_spec.json`: clips 16개, `clips[-1] = {"type": "video", "src": "roanoke-colony/outro_signature.mp4", "durationInFrames": 106}` (약 3.5s)
- `nazca-lines/visual_spec.json`: clips **0개** (baseline spec 비어있음 — 재생성 필요한 샘플, triangulation 제외)
- 해석: 2 episode 에서 `clips[-1]` 가 **video 타입**이며 src 는 **episode-local** (`<episode>/outro_signature.mp4`) 경로로 일관. 기간 99~106 frames (3~3.5초).

**Phase C (shorts_naberal 실 파일 스캔)**
- `_shared/signatures/` 내 `incidents_outro*.mp4`: **부재 확인** (documentary_outro.mp4, wildlife_outro.mp4 만 존재).
- Episode `sources/outro_signature.mp4` 실 파일: zodiac-killer / db-cooper / elisa-lam 3 episode 전수 존재, **sha256 100% 동일** (`9953df790e479cbc...`, 2082298 bytes).
- 동일 hash 확인으로 outro_signature.mp4 는 channel-incidents 공유 자산 임이 확정.
- intro_v4 와 동일 파일인가? sha256 검증: `intro_v4 = 00fe67843117c7ce`, `outro = 9953df790e479cbc` → **다른 파일**.
- shorts_naberal `remotion/src/compositions/OutroCard.tsx` **존재 확인** (132 줄, 프로그램적 Remotion 렌더 — fonts/colors/fade-in, 외부 mp4 의존 0). 실제 render 경로는 OutroCard 컴포넌트 우선일 가능성 매우 높음.
- `shorts_naberal/scripts/video-pipeline/remotion_render.py`: outro 관련 코드 **0 건** (grep 확인).
- `test_graphic_cards_pipeline.py` 에 `OutroCard` position 검증 테스트 존재 → Remotion 측에 OutroCard 컴포넌트 공식 통합.

### 결론

**Option A (Remotion 프로그램적 OutroCard) 채택.**

근거 요약:
1. shorts_naberal 자체 Remotion 저장소에 OutroCard.tsx 존재 (132줄) — 외부 mp4 불필요한 완전한 프로그램적 구현.
2. `_shared/signatures/` 에 incidents_outro*.mp4 부재 → shared Veo 자산 없음 → Phase 16 에서 재생성 금지 (CLAUDE.md 금기 #11).
3. 비록 episode sources/outro_signature.mp4 가 존재하지만 이는 legacy artifact 로 현재 Remotion 렌더는 OutroCard 프로그램적 경로가 priority. 본 Phase 에서 그 legacy mp4 를 포팅할 이유 없음.
4. harvested Python orchestrator 에 outro 처리 로직 0건 → Python 계층은 OutroCard props 만 전달, 실 렌더는 Remotion 컴포넌트가 담당 (이는 Plan 16-03 Option A 설계와 일치).

### 선택 이유

- **Veo API 신규 호출 회피**: CLAUDE.md 금기 #11 엄수 (Option B 는 Veo 재생성 유도 가능성).
- **단일 소스 원칙**: shorts_naberal 상위 저장소가 이미 프로그램적 컴포넌트를 채택. 동일 디자인 언어 계승.
- **렌더 속도**: 외부 mp4 디코드 불필요 → Remotion compose 빠름.
- **데이터 무결성**: episode 마다 3.3~3.5s 가변 길이를 프로그램적 타이밍으로 정확히 매칭 (하드코딩 90 frames + channelName props 가변).

### 대표님 결재 필요 여부

**No — 결재 불필요.** Option A 는 본 Plan 16-03 의 원래 기본 경로와 일치. Phase 16 스코프 내에서 완결. 증거 log 2 file (grep + triangulation) 및 이 SUMMARY 섹션이 박제 근거.

---

## Task 0 Evidence Log References

- `.planning/phases/16-production-integration-option-a/16-03-task0-grep-remotion.log` (0 lines — harvested remotion_render.py 에 outro 관련 0건)
- `.planning/phases/16-production-integration-option-a/16-03-task0-triangulation.log` (3 episode × clips[-1] 구조)

---

## Execution Summary

> 아래 섹션은 Plan 16-03 모든 task 실행 완료 후 채워집니다.

### Waves Executed

- Wave 0: (pending)
- Wave 1: (pending)
- Wave 2: (pending)

### Deviations from Plan

_filled during execution_

### Commits

_filled during execution_

---

*Phase 16-03 — Plan 실행 시작 2026-04-22 / 나베랄 감마.*
