---
phase: 04-agent-team-design
plan: 06
subsystem: agents
tags: [inspector, technical, audio, render, subtitle, whisperx, kresnik, remotion, logicqa, rubric, pytest]

# Dependency graph
requires:
  - phase: 04-agent-team-design
    provides: Plan 04-01 Wave 0 FOUNDATION — agent-template.md, rubric-schema.json, validate_all_agents, conftest.py fixtures
provides:
  - 3 Technical Inspector AGENT.md files (ins-audio-quality, ins-render-integrity, ins-subtitle-alignment)
  - Technical category JSON-meta-only evaluation spec (no ffmpeg/WhisperX in Phase 4)
  - tests/phase04/test_inspector_technical.py — 31 structural + content + invariant assertions
  - Phase 5 handoff contract for real ffmpeg/ffprobe/WhisperX subprocess invocation
affects: [04-07, 04-08, 05-orchestrator, 07-integration-test]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Inspector JSON-meta-only evaluation (Phase 4 spec, Phase 5 tool invocation)"
    - "LogicQA main_q + 5 sub_qs enforced via pytest token scan"
    - "Content keyword regression via direct read_text assertions"
    - "Phase 5 deferral invariant in MUST REMEMBER section"

key-files:
  created:
    - .claude/agents/inspectors/technical/ins-audio-quality/AGENT.md
    - .claude/agents/inspectors/technical/ins-render-integrity/AGENT.md
    - .claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md
    - tests/phase04/test_inspector_technical.py
  modified: []

key-decisions:
  - "ins-subtitle-alignment vs ins-readability split — technical 담당 alignment + word/line count + font_size_pt range, style(ins-readability) 담당 typography/contrast. MUST REMEMBER 에 침범 금지 명시."
  - "ins-audio-quality 에서 AUDIO-04 (AF-4/5/13 차단) 는 ins-license 주 책임으로 위임하고 본 Inspector 는 peak/silence/sync 에 초점."
  - "Phase 4 스펙 한정 원칙 MUST REMEMBER 7번 항목으로 명시 — 실 ffmpeg/ffprobe/WhisperX subprocess 는 Phase 5 오케스트레이터가 호출. Phase 4 프롬프트에는 JSON 메타 소비 로직만 작성."

patterns-established:
  - "Technical Inspector 프롬프트 패턴: producer_output JSON (기측정 peak_dbfs/resolution/start_sec) 소비 + LogicQA 다수결 + rubric-schema.json 출력"
  - "pytest 모듈: 구조 (role/category/maxTurns/name) + LogicQA 토큰 (q1..q5) + 도메인 키워드 + MUST REMEMBER 위치 + 금지 invariants (RUB-02/06) + Phase 5 deferral + subprocess validate_all_agents"
  - "모든 Inspector AGENT.md 는 validate_all_agents 의 AGENT-07(≤500 lines) + AGENT-08(desc≤1024chars, ≥3 triggers) + AGENT-09(MUST REMEMBER at end) 통과"

requirements-completed:
  - AGENT-04
  - AGENT-07
  - AGENT-08
  - AGENT-09
  - RUB-01
  - RUB-02
  - RUB-04
  - RUB-05
  - RUB-06
  - SUBT-01
  - SUBT-03
  - CONTENT-06

# Metrics
duration: 6min
completed: 2026-04-18
---

# Phase 04 Plan 06: Inspector Technical 3 Summary

**3 Technical Inspectors (ins-audio-quality / ins-render-integrity / ins-subtitle-alignment) with JSON-meta-only evaluation, WhisperX+kresnik±50ms alignment gate, and 31-assertion pytest regression.**

## Performance

- **Duration:** 6 min (334s)
- **Started:** 2026-04-18T20:25:57Z
- **Completed:** 2026-04-18T20:31:31Z
- **Tasks:** 2
- **Files created:** 4 (3 AGENT.md + 1 test file)
- **Files modified:** 0

## Accomplishments

- 3 Technical Inspector AGENT.md specs (~118/114/120 lines each, all under 500-line AGENT-07 cap) landed under `.claude/agents/inspectors/technical/`.
- ins-subtitle-alignment carries **SUBT-01 (WhisperX + kresnik/wav2vec2-large-xlsr-korean word-level)** + **SUBT-03 (±50ms accuracy)** + **CONTENT-06 (1-4 단어/라인, 24-32pt)** in a single inspector with explicit ins-readability overlap avoidance.
- ins-render-integrity gates **9:16 / 1080×1920 / ≤59.5s / codec∈{h264,hevc} / Remotion composition meta completeness** — CONTENT-05 + CONTENT-07 Shorts format mandate.
- ins-audio-quality gates **peak < -3 dBFS / silence span < 1s / audio↔video duration sync ≤100ms** — AUDIO-02 ducking/crossfade support (AUDIO-04 license delegated to ins-license).
- Each AGENT.md carries LogicQA main_q + 5 sub_qs (RUB-01), rubric-schema output contract (RUB-04), 창작 금지 (RUB-02), producer_prompt 읽기 금지 (RUB-06), maxTurns=3 (RUB-05), Supervisor 재호출 금지 (AGENT-05), and Phase 5 deferral invariant in MUST REMEMBER positioned at file end (AGENT-09 RoPE).
- 31/31 pytest assertions PASS covering frontmatter shape, LogicQA structure, content keywords, MUST REMEMBER placement, prohibition invariants, Phase 5 deferral text, and subprocess-based validate_all_agents integration.

## Task Commits

1. **Task 1: Write 3 Technical Inspector AGENT.md files** — `f468523` (feat)
2. **Task 2: Write Technical Inspector compliance tests** — `ef64ac3` (test)

_Note: Task 2 is the "TDD GREEN" commit — failing fixture scope (module vs function) was auto-fixed inline before initial green (see Deviations)._

## Files Created/Modified

- `.claude/agents/inspectors/technical/ins-audio-quality/AGENT.md` (118 lines) — audio peak/silence/sync inspector spec (AUDIO-02)
- `.claude/agents/inspectors/technical/ins-render-integrity/AGENT.md` (114 lines) — Remotion format inspector spec (CONTENT-05/07)
- `.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md` (120 lines) — WhisperX+kresnik ±50ms alignment inspector spec (SUBT-01/03 + CONTENT-06)
- `tests/phase04/test_inspector_technical.py` (214 lines) — 31 pytest assertions across 10 test functions

## Decisions Made

- **Technical vs Style split for subtitles**: ins-subtitle-alignment(technical) = alignment + word/line count + font_size_pt **range** only. ins-readability(style, future Plan 04-05) = typography/contrast/readability rendering. Both MUST REMEMBER sections should reference this boundary to prevent double-evaluation.
- **Technical vs Compliance split for audio**: ins-audio-quality(technical) = peak/silence/sync only. ins-license(compliance, future Plan 04-04) = AF-4/5/13 license/artist blacklist. ins-audio-quality 는 AUDIO-04 간접 지원만, 직접 강제는 ins-license 책임.
- **Phase 4 spec-only discipline**: All 3 inspectors consume already-measured JSON meta (peak_dbfs, resolution.w/h, audio_onset_sec, duration_sec). Zero subprocess/binding code in Phase 4. Phase 5 orchestrator adds ffmpeg volumedetect/silencedetect, ffprobe resolution check, WhisperX forced-alignment subprocess — explicitly deferred in MUST REMEMBER item 6 of each inspector.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pytest fixture scope mismatch (agent_paths module-scoped, repo_root function-scoped)**
- **Found during:** Task 2 (first test run)
- **Issue:** `@pytest.fixture(scope="module") def agent_paths(repo_root): ...` triggered pytest `ScopeMismatch: function scoped fixture repo_root with a module scoped request object`. 30/31 tests errored at setup.
- **Fix:** Removed `scope="module"` → default function scope. `repo_root` lookup re-runs per test (trivial Path construction, no I/O cost).
- **Files modified:** `tests/phase04/test_inspector_technical.py`
- **Verification:** Re-ran `py -3.11 -m pytest tests/phase04/test_inspector_technical.py -v` → 31 passed in 0.13s.
- **Committed in:** `ef64ac3` (Task 2 commit — caught and fixed before initial green commit)

---

**Total deviations:** 1 auto-fixed (1 bug, Rule 1)
**Impact on plan:** Trivial. Caught in first test run during Task 2; fixed inline before committing. No scope creep, no additional files.

## Issues Encountered

- None beyond the fixture scope bug (handled as Rule 1 deviation above).

## User Setup Required

None — no external service configuration required. Phase 4 is pure spec + regression test.

## Next Phase Readiness

- **Wave 2b Technical category complete.** Ready to parallelize with 04-02 (Structural), 04-03 (Content), 04-04 (Compliance), 04-05 (Style), 04-07 (Media).
- **Phase 5 handoff contract captured** in each AGENT.md's "Contract with caller" + "MUST REMEMBER item 6 (Phase 5 deferral)". Phase 5 orchestrator must:
  - Invoke ffmpeg `volumedetect,silencedetect` and produce the `{segments, silence_spans, total_duration_sec}` JSON consumed by ins-audio-quality.
  - Invoke ffprobe and produce the `{aspect_ratio, resolution, duration_sec, codec, remotion_composition_id, ...}` JSON consumed by ins-render-integrity.
  - Invoke WhisperX + `kresnik/wav2vec2-large-xlsr-korean` forced-alignment and produce `{segments, words[{text, start_sec, end_sec, audio_onset_sec}], alignment_model, alignment_log}` consumed by ins-subtitle-alignment.
  - Strip all `producer_prompt`/`system_context` fields from fan-out payloads (RUB-06 enforcement).
- **No blockers.** ins-readability (Plan 04-05) must reference the technical/style split decision above; ins-license (Plan 04-04) must own AUDIO-04 enforcement.

## Self-Check: PASSED

- `.claude/agents/inspectors/technical/ins-audio-quality/AGENT.md` — FOUND
- `.claude/agents/inspectors/technical/ins-render-integrity/AGENT.md` — FOUND
- `.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md` — FOUND
- `tests/phase04/test_inspector_technical.py` — FOUND
- Commit `f468523` (Task 1 feat) — FOUND in `git log`
- Commit `ef64ac3` (Task 2 test) — FOUND in `git log`
- `py -3.11 -m scripts.validate.validate_all_agents --path .claude/agents/inspectors/technical` → `OK: 3 agent(s) validated`
- `py -3.11 -m pytest tests/phase04/test_inspector_technical.py` → 31 passed in 0.13s

---
*Phase: 04-agent-team-design*
*Completed: 2026-04-18*
