# Phase 16: Production Integration Option A — Context

**Gathered:** 2026-04-22 세션 #33
**Status:** Ready for planning
**Source:** Orchestrator-constructed (대표님 전권 위임, session #32 shock-event recovery + session #33 mapping-driven decisions)

---

<domain>
## Phase Boundary

Phase 16 delivers a production-grade shorts pipeline by **adopting** (not re-designing) shorts_naberal's Remotion-based architecture. Output criteria: each shorts video must match shorts_naberal baseline — 1080×1920 · 60–120s · stereo 48kHz · word-level burned-in subtitles · intro signature (detective silhouette, 3s+) · outro treatment (3s+) · detective+assistant character overlays · b-roll photo library (≥5 images) · Remotion compositing instead of raw ffmpeg concat.

**Scope in:**
- Adopt shorts_naberal production architecture (Remotion + faster-whisper + visual_spec + sources/ discipline) for **incidents channel (Korean)** only
- Add one new Producer: `subtitle-producer` (word-level ASS/JSON generation)
- Extend `asset-sourcer` output schema to include visual_spec.json + character PNG + intro/outro signature references
- Branch ASSEMBLY gate to use Remotion renderer as priority 1 (ffmpeg + Shotstack retained as fallback)
- Port key harvested modules verbatim (1:1) with Python wrappers; do NOT re-implement from scratch

**Scope out (deferred to future phases):**
- Non-incidents channels (wildlife / humor / politics / trend / documentary) — channel-bible imprint only, no rendering integration
- incidents-jp (Japanese variant) — Phase 17 (scope doubling: だ/である + VOICEVOX + subtitles_jp.* + metadata_jp)
- Veo signature regeneration or Kling replacement — Phase 17+ (if 대표님 directs)
- Thumbnail redesign (existing thumbnail-designer kept as-is)

</domain>

<decisions>
## Implementation Decisions (Locked)

### Agent Topology
- **Producer count: 14 → 15** (session #33 amend, CLAUDE.md 금기 #9 updated). Reason: `ins-subtitle-alignment/AGENT.md` already documents "상류 = subtitle-producer" as a reserved slot; GAN separation (RUB-02) forbids Inspector from generating. Selection forced — not preference.
- **New agent: `subtitle-producer`** (Plan 16-03 responsibility). Produces word-level ASS/JSON/SRT triple.
- **Extended agent: `asset-sourcer`** (Plan 16-04 responsibility). Additional output: `visual_spec.json`, `scene-manifest.json` v4, `sources/` directory population, character PNG + signature mp4 copy.
- **No other agents added.** Total 33 hard cap (Producer 15 + Inspector 17 + Supervisor 1).

### Video Stack
- **Renderer: Remotion 4.x** (TypeScript, Node 18+). Priority 1 in ASSEMBLY gate.
- **Fallbacks:** Shotstack API (P2), ffmpeg local (P3) — retained from current implementation.
- **Python wrapper:** `scripts/orchestrator/api/remotion_renderer.py` (new). Mirrors ffmpeg_assembler signature for ASSEMBLY gate compatibility.
- **Composition:** `ShortsVideo.tsx` single composition + TransitionSeries with 7 transition variants (copy from shorts_naberal) + 3 crime components (title card, detective+assistant TopBar, outro card). Copy verbatim from harvested.
- **Ken Burns pan/zoom:** Remotion interpolate + Easing — do NOT hand-roll (harvested pattern).

### Audio + Subtitle Stack
- **TTS:** Existing Typecast primary + ElevenLabs fallback (Phase 9.1 stack preserved).
- **Subtitle alignment:** faster-whisper `large-v3` (NOT stock whisper, NOT WhisperX). Port `word_subtitle.py` 1697 lines verbatim.
- **Formats:** `subtitles_remotion.ass` (Aegisub v4+) + `subtitles_remotion.json` (Remotion direct import) + `subtitles_remotion.srt` (compat backup). All three generated together.
- **Hook clip duration override:** 9.0s hard-fixed (channel-incidents SKILL §Hook signature rule).

### Veo Policy (Session #32 locked)
- **Veo API new calls: 0 (zero) in Phase 16.** CLAUDE.md 금기 #11 strict.
- **Existing Veo assets re-used by reference/copy only:**
  - `C:/Users/PC/Desktop/shorts_naberal/output/_shared/signatures/incidents_intro_v4_silent_glare.mp4` (1.70 MB) — confirmed exists (session #33 mapping check)
  - `.preserved/harvested/video_pipeline_raw/generate_intro_signature.py` — preserved for reference only, never executed
- **Kling regeneration of signature: NOT in Phase 16** (possibly Phase 17 if 대표님 directs)

### Intro/Outro Signature Treatment
- **Intro:** Use `incidents_intro_v4_silent_glare.mp4` verbatim (Hook section, 9.0s).
- **Outro:** UNRESOLVED — no `incidents_outro*.mp4` file exists in shorts_naberal. Resolution task belongs to Plan 16-03 Task 0:
  1. Grep `shorts_naberal/scripts/video-pipeline/remotion_render.py` for outro generation logic
  2. Inspect `visual_spec.json:132-136` (`outro_signature.mp4` path semantics — Remotion `public/` vs episode-local)
  3. Compare 3+ incidents episode `visual_spec.json` for common outro pattern
  4. Document findings in Plan 16-03 SUMMARY.md and design outro logic accordingly (likely: Remotion programmatic outro card, not external mp4)

### Character Overlay Treatment
- **Asset source:** `shorts_naberal/output/_shared/characters/` (4 PNG files confirmed):
  - `incidents_detective_longform_a.png` (primary detective)
  - `incidents_detective_longform_b.png` (variant)
  - `incidents_assistant_jp_a.png` (assistant/Watson)
  - `incidents_zunda_shihtzu_a.png` (mascot, restricted use per 대표님 "몰입 방해" guidance)
- **Copy flow:** `asset-sourcer` copies to `output/<episode>/sources/character_detective.png` + `character_assistant.png` at ASSETS gate.
- **Rendering:** `ShortsVideo.tsx` receives via props `characterLeftSrc` + `characterRightSrc`, applies circular crop + border + face zoom + TopBar positioning. Python does NOT transform images.
- **Registry integration:** Phase 9.1 `CharacterRegistry` (existing) tracks which character PNG is used per episode; `asset-sourcer` consults registry for persona continuity.

### Harvest Extension (Plan 16-03 Task 1)
Current `.preserved/harvested/` lacks binary assets due to size. Must copy (read-only, one-way):
- `output/_shared/signatures/incidents_intro_v4_silent_glare.mp4` → `.preserved/harvested/video_pipeline_raw/signatures/`
- `output/_shared/characters/incidents_*.png` (4 files) → `.preserved/harvested/video_pipeline_raw/characters/`
- `attrib +R /S /D` (Windows) + `chmod -R a-w` (POSIX) applied after copy.
- CLAUDE.md 금기 #6 preserved: source files in shorts_naberal remain untouched.

### Channel Scope
- **Phase 16 = incidents (Korean) only.**
- **incidents-jp explicitly deferred to Phase 17** despite baseline specs existing (zodiac-killer-jp / nazca-lines-jp / roanoke-colony-jp confirmed session #33). Reason: scope doubling (だ/である + VOICEVOX + WhisperX `--language ja` + metadata_jp + subtitles_jp.*).
- **Other 5 channel bibles (wildlife/humor/politics/trend/documentary):** Plan 16-01 imprints channel bibles as reference memories only; actual rendering integration is Phase 17+ per channel.

### Testing & Verification
- **Regression baseline:** 986+ existing tests (Phase 4 244 + Phase 5 329 + Phase 6 236 + Phase 7 177) must stay green.
- **New Phase 16 tests:** ≥20 (estimate: Remotion renderer unit 8 + subtitle-producer 5 + visual_spec schema 4 + asset-sourcer extension 3+).
- **Baseline comparison:** Post-execution must include ffprobe diff vs `shorts_naberal/output/zodiac-killer/final.mp4` reference — resolution, duration, subtitle track count, audio channels, bitrate each within ±10% or better.
- **"Spec pass ≠ production pass" guard:** Verifier must output quantitative comparison against ≥3 baseline episodes (zodiac-killer + mary-celeste OR db-cooper OR elisa-lam).

### Claude's Discretion
These are implementation details the orchestrator did not lock — planner may choose:
- Internal module naming (e.g., `remotion_renderer.py` vs `remotion_compose.py`)
- Wave breakdown within each Plan (Wave 1 / 2 / 3 structure)
- Test file naming conventions (within project's existing `tests/phase{N}/test_*.py` scheme)
- Exact TypeScript project structure inside `remotion/` directory (e.g., `src/compositions/ShortsVideo.tsx` vs `src/ShortsVideo.tsx`)
- Which subset of 7 transitions to port first (if Wave split is needed)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 16 Research & Context
- `.planning/phases/16-production-integration-option-a/16-RESEARCH.md` — 1259-line Phase 16 research (authoritative Q1-Q4 answers, Standard Stack, Don't Hand-Roll, Common Pitfalls, Code Examples)
- `.planning/phases/16-production-integration-option-a/16-CONTEXT.md` — this file (locked decisions)

### Session #32 Handoff (Pre-Planning SSOT)
- `NEXT_SESSION_START.md` — Session #33 entry prompt + Phase A1~A4 roadmap origin
- `WORK_HANDOFF.md` (Session #32 section, first ~110 lines) — shock-event detail
- `SESSION_LOG.md` (Session #32 entry) — 대표님 verbatim quotes preserving context

### Project Memories (Auto-loaded by session_start.py)
- `.claude/memory/reference_production_gap_map.md` — 11 missing components + production vs our 13 GATE mapping
- `.claude/memory/reference_harvested_full_index.md` — 9-folder 160-file harvest index
- `.claude/memory/reference_signature_and_character_assets.md` — **Phase 16 asset SSOT** (v4 intro + 4 character PNGs + outro unresolved + episode standard structure)
- `.claude/memory/project_image_stack_gpt_image2.md` — image stack (gpt-image-2 primary for anchors/thumbnails)
- `.claude/memory/feedback_i2v_prompt_principles.md` — I2V prompt rules (Camera Lock / Anatomy Positive / Micro Verb) + VEO_PROMPT_GUIDE usage
- `.claude/memory/feedback_no_mockup_no_empty_files.md` — absolute prohibition on mocks/empty files
- `.claude/memory/MEMORY.md` — memory index

### Channel Bible Sources (Plan 16-01 consumes)
- `.preserved/harvested/theme_bible_raw/incidents.md` — incidents channel v1.0 SSOT (primary target of 16-01)
- `.preserved/harvested/theme_bible_raw/wildlife.md` / `humor.md` / `politics.md` / `trend.md` / `documentary.md` — other 5 bibles (imprint as reference, not rendered this phase)
- `.preserved/harvested/skills_raw/channel-incidents/SKILL.md` — duo dialogue rules + CTA signature + hook signature Veo reuse pattern
- `.preserved/harvested/skills_raw/channel-incidents-jp/SKILL.md` — Phase 17 reference (NOT this phase)

### Production Stack Sources (Plans 16-02/03/04 port from)
- `.preserved/harvested/video_pipeline_raw/remotion_render.py` (47024 bytes) — Python Remotion orchestration (port to `scripts/orchestrator/api/remotion_renderer.py`)
- `.preserved/harvested/video_pipeline_raw/generate_intro_signature.py` (4814 bytes) — Veo signature generator (preserve for reference, DO NOT execute)
- `.preserved/harvested/audio_pipeline_raw/` — TTS + word-level subtitle generation source modules
- `.preserved/harvested/visual_pipeline_raw/` — visual_spec generation logic + Ken Burns
- `.preserved/harvested/design_docs_raw/DESIGN_BIBLE.md` + `DESIGN_SPEC.md` + `NLM_PROMPT_GUIDE.md` + `VEO_PROMPT_GUIDE.md` — 4 core design docs

### Baseline Specs (Reference shorts)
- `.preserved/harvested/baseline_specs_raw/zodiac-killer/` — 11-file complete Remotion input exemplar (visual_spec.json + scene-manifest.json + script.json + subtitles_remotion.ass/json/srt + source.md + blueprint.json + metadata.json + sources_metadata.json + _upload_script.json)
- `.preserved/harvested/baseline_specs_raw/{nazca-lines,roanoke-colony}/` — 2 more incidents episodes for pattern triangulation
- `shorts_naberal/output/{zodiac-killer,mary-celeste,db-cooper,elisa-lam,kitakyushu-matsunaga}/final.mp4` — 5+ production videos for post-integration quantitative baseline comparison (READ-ONLY, ffprobe only)

### Current Codebase (Integration Points)
- `scripts/orchestrator/shorts_pipeline.py` — 13 GATE state machine; ASSEMBLY gate (approx line 515–562) receives Remotion branch
- `scripts/orchestrator/api/ffmpeg_assembler.py` — existing assembler (kept as fallback, NOT removed)
- `scripts/orchestrator/gate_guard.py` — GATE enforcement (ensure Remotion path participates in gate_dispatch)
- `.claude/agents/producers/asset-sourcer/AGENT.md` — extend output schema (Plan 16-04)
- `.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md` — update description from "WhisperX" to "faster-whisper large-v3"; declare `subtitle-producer` as its upstream
- `CLAUDE.md` — 금기 #9 amended to 33 agents; Navigator updated with subtitle-producer + remotion_renderer (session #33)

### GSD State
- `.planning/ROADMAP.md` — Phase 16 detail block (Goal, SC, Constraints, Plans, Research Questions, Fixed decisions) at line ~461
- `.planning/STATE.md` — Phase 16 added entry in Roadmap Evolution section
- `.planning/REQUIREMENTS.md` — add REQ-PROD-INT-01~NN during Plan generation (planner's responsibility)
- `.preserved/harvested/` — read-only locked (attrib +R on Windows, chmod -w on POSIX); plans may READ but never WRITE

</canonical_refs>

<specifics>
## Specific Ideas

### Plan 16-01 Specifics (Channel Bibles + Memory Mapping)
- **No code changes** — pure text imprinting.
- **Primary deliverable:** `.claude/memory/project_channel_bible_incidents_v1.md` — condensed 7-channel structure with incidents marked "production-active" and others marked "reference only".
- **Secondary:** 12+ feedback memory mappings. Each feedback listed in incidents.md footnotes — check if exists in `.claude/memory/`, create if missing (full content from incidents.md cross-references), update if exists with v1.0 amendments.
  - `feedback_script_tone_seupnida` — "습니다/입니다/였죠" ending rule (FAIL-SCR-016 defense)
  - `feedback_duo_natural_dialogue` — 왓슨 질문 키워드 ≥60% 탐정 답변 첫 문장 포함 (FAIL-SCR-004 defense)
  - `feedback_subtitle_semantic_grouping` — 6–12자 동사 종결, 의미 단위 분할
  - `feedback_video_clip_priority` — 영상:이미지 ≥30% 비율
  - `feedback_outro_signature` — 탐정 정면→뒤돌아 걸어감 패턴
  - `feedback_series_ending_tiers` — Part 1/2/3 CTA differentiation
  - `feedback_detective_exit_cta` — 10-pool detective exit phrases, 과공손 "뵙겠습니다" 금지
  - `feedback_watson_cta_pool` — 10-pool Watson CTA
  - `feedback_dramatization_allowed` — factual strictness vs scene detail dramatization allowed
  - `feedback_info_source_distinction` — "~라고 합니다" vs "탐정 직접 본 것" distinction
  - `feedback_veo_supplementary_only` — Veo 보조용, 실제 이미지 크롤링 최우선
  - `feedback_number_split_subtitle` — "1,701통" one-word subtitle rule
- **MEMORY.md index updated** with all new/updated entries.

### Plan 16-02 Specifics (Remotion Renderer)
- **New directory:** `remotion/` at project root (separate from `scripts/`). TypeScript project with `package.json` + `tsconfig.json` + `remotion.config.ts` + `src/Root.tsx` + `src/compositions/ShortsVideo.tsx` + `src/components/{TitleCard,TopBar,OutroCard,BRollImage,AssetClip}.tsx` + `src/transitions/{fade,slide,wipe,...}.ts`.
- **Node ≥ 18 required** — document in README or top-level note; confirm `node --version` before bootstrap.
- **Python wrapper:** `scripts/orchestrator/api/remotion_renderer.py` (estimated ~200–300 lines). Subprocess wrapper calling `npx remotion render ShortsVideo --props=<json>`. Signature mirrors `ffmpeg_assembler.FfmpegAssembler.assemble(...)` for drop-in use.
- **ASSEMBLY gate branch (shorts_pipeline.py):** `renderer = remotion or shotstack or ffmpeg` priority cascade with circuit breaker (reuse Phase 7 CircuitBreaker pattern). Track which renderer was used in `assembly_metadata.json`.
- **ffprobe post-check:** After render, run `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name,r_frame_rate` on output; assert `width=1080 height=1920 codec_name=h264|hevc`. Fail ASSEMBLY gate if mismatch.

### Plan 16-03 Specifics (Subtitles + Signatures + Overlays)
- **New agent:** `.claude/agents/producers/subtitle-producer/AGENT.md` — declare upstream (voice-producer narration.mp3 + script.json), downstream (ins-subtitle-alignment verification), output (subtitles_remotion.{ass,json,srt} triple).
- **Port:** `scripts/orchestrator/api/subtitle_producer.py` — 1:1 from `.preserved/harvested/audio_pipeline_raw/word_subtitle.py` (1697 lines harvested, trim to essential API but preserve correctness-critical logic).
- **Model:** faster-whisper `large-v3` (confirm pip install `faster-whisper>=1.0.3`; cache model to `~/.cache/huggingface/` first-run).
- **Harvest extension (Task 1):** Binary asset copy (signatures + characters) to `.preserved/harvested/video_pipeline_raw/signatures|characters/` with attrib +R.
- **Outro research (Task 0 BEFORE other work):** Triangulate outro generation method — document in Plan 16-03 SUMMARY.md appendix before designing outro component.
- **Signature integration:** `remotion_renderer.py` copies `incidents_intro_v4_silent_glare.mp4` to `output/<episode>/sources/intro_signature.mp4` at render time (not at ASSETS gate) to keep episode directory minimal.
- **Character overlay:** Python does NO image transformation. `asset-sourcer` only copies PNGs; `ShortsVideo.tsx` handles `<Img circleCrop={true} zoomFace={true} borderColor="#..." />` rendering.
- **ins-subtitle-alignment update:** Update AGENT.md description from "WhisperX" to "faster-whisper large-v3 with kresnik wav2vec2 optional boost"; clarify upstream as subtitle-producer.

### Plan 16-04 Specifics (visual_spec + sources + asset-sourcer)
- **Schema:** `visual_spec.json` matches zodiac-killer reference exactly — channelName / titleLine1 / titleLine2 / titleKeywords[] / accentColor / hashtags / fontFamily / characterLeftSrc / characterRightSrc / subtitlePosition / subtitleHighlightColor / subtitleFontSize / audioSrc / durationInFrames / transitionType / clips[] (each with type=video|image, src, durationInFrames, transition, movement).
- **Pydantic v2 model:** `scripts/orchestrator/api/models.py` — add `VisualSpec(BaseModel)` with `extra='forbid'`. Follow Phase 6 ContinuityPrefix pattern.
- **Scene manifest v4:** `scene-manifest.json` — aligned with scripter output, includes sentence-level timing hints for subtitle-producer.
- **sources/ directory contract:** `output/<episode>/sources/{intro_signature.mp4, outro_*, character_detective.png, character_assistant.png, brollXX.jpg...}` with minimum 5 b-roll images enforced.
- **asset-sourcer extension:** Update AGENT.md output schema to include visual_spec generation. Port relevant logic from `.preserved/harvested/visual_pipeline_raw/design_engine.py` (18688 bytes) + `_build_render_props_v2.py` (7139 bytes).
- **Baseline verification script:** `scripts/validate/verify_baseline_parity.py` — compares our output against ≥3 shorts_naberal final.mp4 files via ffprobe; emits JSON report with pass/fail per criterion. Called by gate_guard ASSEMBLY gate as final check.

</specifics>

<deferred>
## Deferred Ideas (Out of Phase 16 Scope)

- **incidents-jp (Japanese variant):** Phase 17. Baseline specs exist (zodiac-killer-jp / nazca-lines-jp / roanoke-colony-jp) but integration is scope-doubling.
- **Non-incidents channel rendering integration:** wildlife / humor / politics / trend / documentary rendering integration deferred to Phase 18+. Phase 16-01 imprints bibles as reference only.
- **Veo signature regeneration or Kling alternative (v5 signature):** Phase 17+ if 대표님 directs.
- **Thumbnail redesign:** thumbnail-designer kept as-is; its Remotion-native thumbnail rendering is Phase 18+.
- **CharacterRegistry expansion beyond 4 PNGs:** Phase 9.1 registry contract preserved; adding new characters is per-episode not architectural.
- **Non-Korean TTS/subtitle languages:** Phase 19+ (after incidents-jp validates cross-language stack).
- **Remotion cloud rendering (Lambda):** Phase 20+ (local CLI sufficient for weekly 3–4 uploads).
- **A/B testing of alternate subtitle models (Whisper vs WhisperX vs Deepgram):** Phase 20+.

</deferred>

---

*Phase: 16-production-integration-option-a*
*Context gathered: 2026-04-22 via orchestrator-constructed CONTEXT.md (대표님 전권 위임, session #32 shock-event + session #33 mapping-driven decisions)*
