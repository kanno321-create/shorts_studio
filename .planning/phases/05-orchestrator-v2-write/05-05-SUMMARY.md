---
phase: 05-orchestrator-v2-write
plan: 05-05
subsystem: orchestrator
tags: [orchestrator, voice-first-timeline, audio-first, transition-shots, orch-10, video-02, video-03]
wave: 3

# Dependency graph
dependency-graph:
  requires:
    - 05-01 (OrchestratorError base class, tests/phase05/ scaffold, mock_audio_timestamps fixture)
  provides:
    - scripts.orchestrator.voice_first_timeline.VoiceFirstTimeline
    - scripts.orchestrator.voice_first_timeline.AudioSegment
    - scripts.orchestrator.voice_first_timeline.VideoCut
    - scripts.orchestrator.voice_first_timeline.TimelineEntry
    - scripts.orchestrator.voice_first_timeline.TransitionEntry
    - scripts.orchestrator.voice_first_timeline.TimelineItem (Union type alias)
    - scripts.orchestrator.voice_first_timeline.TimelineMismatch
    - scripts.orchestrator.voice_first_timeline.InvalidClipDuration
    - scripts.orchestrator.voice_first_timeline.ClipDurationMismatch
    - scripts.orchestrator.voice_first_timeline.IntegratedRenderForbidden
  affects:
    - 05-06 (Shotstack adapter consumes the aligned+transitioned timeline)
    - 05-07 (shorts_pipeline ASSEMBLY GATE wires VoiceFirstTimeline between VOICE/ASSETS output and Shotstack render)
    - 05-10 (SC6 acceptance: VoiceFirstTimeline importable, integrated_render forbidden)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Audio-first 1:1 mapping — len(audio_segments) == len(video_cuts) is a hard invariant; mismatch raises TimelineMismatch with both counts in the message"
    - "Speed-band gate — audio.duration / video.duration must stay in [0.8, 1.25]; outside this band the handler is expected to regenerate the clip (no silent speed-warp)"
    - "Structural D-10 guard — integrated_render(*args, **kwargs) always raises IntegratedRenderForbidden; there is no legitimate caller, its sole purpose is to block accidental fusion"
    - "Deterministic RNG injection — __init__(rng_seed) uses random.Random(rng_seed) (not the module-global random) so parallel tests cannot cross-pollute template sequences"
    - "Inclusive-bound validation — 4.0s and 8.0s are valid; 3.99 and 8.01 are not. Same for speed 0.8 and 1.25 (boundary tests cover both)"

key-files:
  created:
    - scripts/orchestrator/voice_first_timeline.py (283 lines)
    - tests/phase05/test_voice_first_timeline.py (233 lines, 18 tests)
    - tests/phase05/test_transition_shots.py (178 lines, 15 tests)
  modified: []

key-decisions:
  - "RESEARCH §6 greedy chunk-match algorithm implemented verbatim — one cut per audio segment, enforced via len() equality. No fuzzy nearest-neighbour matching because upstream (shot-planner + VOICE gate) already emit matched counts; divergence is always an upstream bug to fail-loud on."
  - "TransitionEntry.after_index uses the PRE-insertion cut index, not the flat output index. This keeps the semantic stable ('transition appears after cut N') even as the output list grows with inserted transitions. Test test_transition_after_index_matches_insertion_point proves the invariant."
  - "Zero-duration video cuts raise ClipDurationMismatch (not ZeroDivisionError) — early guard added before the division so the error surface stays entirely within OrchestratorError. Additional test test_align_zero_video_duration_raises_clip_duration_mismatch covers it."
  - "`integrated_render` kept as an instance method (not @staticmethod) so external callers that instantiate the class still hit the guard. Making it a method-on-class is intentional: a bare module-level function would be easier to bypass via monkeypatch."

patterns-established:
  - "Pattern: OrchestratorError hierarchy for domain-specific failures — every exception in voice_first_timeline.py subclasses OrchestratorError so Plan 07 pipeline catch-all handlers don't need new except-clauses per plan."
  - "Pattern: inclusive boundary constants as float class attributes — MIN_CLIP_DURATION=4.0, MAX_SPEED=1.25 are authoritative; tests exercise both boundaries (4.0/8.0, 0.8/1.25) so a future edit that flips `<=` to `<` fails loudly."
  - "Pattern: deterministic-RNG for randomized insertion — insert_transition_shots uses self._rng (injected via __init__) so property-style tests with fixed seeds are reproducible; same template sequence guaranteed for same seed."

requirements-completed: [ORCH-10, VIDEO-02, VIDEO-03]

# Metrics
duration: 10m
completed: 2026-04-19
---

# Phase 5 Plan 05: VoiceFirstTimeline Summary

**Audio-first assembly primitive — Typecast TTS timestamps drive video cut placement via 1:1 alignment, 4-8s duration band, 0.8-1.25 speed tolerance, and 3-template transition insertion every 3rd cut. Integrated render (audio+video simultaneous generation) is structurally forbidden via IntegratedRenderForbidden. Plan 07 wires this between VOICE/ASSETS gates and the Shotstack adapter.**

## Performance

- **Duration:** ~10 minutes
- **Tasks:** 2/2 complete
- **Files created:** 3 (1 source + 2 tests)
- **Files modified:** 0
- **Tests added:** 33 (18 alignment contract + 15 transition cadence)
- **Tests passing:** 33/33 Plan 05-05 + 113/113 full tests/phase05/ suite (no regressions)

## Accomplishments

1. **ORCH-10 enforced structurally.** `VoiceFirstTimeline.align(audio_segments, video_cuts)` is the only legal alignment path; `integrated_render()` always raises `IntegratedRenderForbidden("D-10: audio+video simultaneous generation is forbidden...")`. Any future caller that tries to fuse audio+video generation trips a loud exception instead of silently corrupting the timeline.

2. **VIDEO-02 4-8s duration band enforced.** Per-segment audio duration must be in `[MIN_CLIP_DURATION=4.0, MAX_CLIP_DURATION=8.0]`. Boundaries are inclusive (4.0 and 8.0 pass; 3.99 and 8.01 raise `InvalidClipDuration` with the segment index and actual duration in the message).

3. **VIDEO-02 speed tolerance enforced.** `speed = audio.duration / video.duration` must stay in `[MIN_SPEED=0.8, MAX_SPEED=1.25]`. Outside this band the caller is expected to regenerate the clip — the contract explicitly refuses to silently speed-warp a clip outside ±25%.

4. **VIDEO-03 transition cadence implemented.** `insert_transition_shots(timeline)` inserts a `TransitionEntry` after every 3rd cut EXCEPT the last. Template is drawn from `("prop_closeup", "silhouette", "background_wipe")` via `self._rng.choice`; duration sampled from `[0.5, 1.0]` via `self._rng.uniform`. RNG is seedable for deterministic tests.

5. **Pure data transformation — no I/O side effects.** No HTTP libraries (`httpx`/`requests` absent). No audio processing (`pydub` absent). No file I/O inside the class. This keeps Plan 06 (Shotstack render) and Plan 07 (pipeline composition) free to decide how to materialise the timeline.

## Task Commits

Each task committed atomically:

1. **Task 1: VoiceFirstTimeline source file** — `5d9ab61` (feat)
   - 4 dataclasses + 4 exception classes + class with align/insert_transition_shots/integrated_render
   - 283 lines (within plan's [180, 350] band)

2. **Task 2: 2 test files** — `7375d8c` (test)
   - test_voice_first_timeline.py: 18 tests, 233 lines (alignment contract)
   - test_transition_shots.py: 15 tests, 178 lines (cadence + templates + RNG)

## Files Created / Modified

### Source (scripts/orchestrator/)
- `scripts/orchestrator/voice_first_timeline.py` — 283 lines. 4 dataclasses (AudioSegment, VideoCut, TimelineEntry, TransitionEntry), TimelineItem Union alias, 4 exception classes subclassing OrchestratorError (TimelineMismatch, InvalidClipDuration, ClipDurationMismatch, IntegratedRenderForbidden), VoiceFirstTimeline class with class-level constants (MIN_CLIP_DURATION=4.0, MAX_CLIP_DURATION=8.0, MIN_SPEED=0.8, MAX_SPEED=1.25, TRANSITION_TEMPLATES=3-tuple, MIN/MAX_TRANSITION_DURATION=0.5/1.0, TRANSITION_EVERY_N_CUTS=3), `__init__(rng_seed)`, `align()`, `insert_transition_shots()`, `integrated_render()` guard.

### Tests (tests/phase05/)
- `tests/phase05/test_voice_first_timeline.py` — 233 lines, 18 tests:
  - align matched counts + start/end/path preservation
  - count mismatch raises TimelineMismatch (2 flavors)
  - duration bounds: 3.5/8.1 raise, 4.0/8.0 pass
  - speed bounds: 1.67/0.67 raise, 0.8/1.25 pass
  - zero video duration raises ClipDurationMismatch (defensive)
  - integrated_render raises with/without args (D-10)
  - error-message invariant guard (strings reference the rule)
  - mock_audio_timestamps fixture interoperability
- `tests/phase05/test_transition_shots.py` — 178 lines, 15 tests:
  - empty/2/3/4/6/7-cut timelines (cadence math)
  - transition never precedes first cut
  - after_index matches source cut index (not flat output index)
  - templates drawn only from 3-tuple
  - durations in [0.5, 1.0]
  - rng_seed=42 gives identical template sequences across instances
  - different seeds produce different sequences (statistical guard)
  - class-constant stability guards (TRANSITION_EVERY_N_CUTS=3, TRANSITION_TEMPLATES membership, MIN/MAX_TRANSITION_DURATION values)

## Deviations from Plan

None — plan executed exactly as written. RESEARCH §6 algorithm adopted verbatim (greedy 1:1 chunk-match, every-3rd-cut transition cadence, 3-template random selection with seeded RNG). Line counts within the 180-350 band (283). Test counts above minimums (18 >= 15 for alignment, 15 >= 10 for transitions).

Two small defensive additions (tracked as **Rule 2 — auto-add missing critical functionality** but NOT listed as deviations because they are the plan-stated behaviour expressed more explicitly):

1. **Zero-duration video cut early guard.** The plan's `<action>` block mentions `if vid.duration <= 0: raise ClipDurationMismatch(...)`. This was implemented and covered by `test_align_zero_video_duration_raises_clip_duration_mismatch` so a malformed upstream payload cannot trigger `ZeroDivisionError`.

2. **`TimelineItem = Union[TimelineEntry, TransitionEntry]` type alias exported.** The plan's interfaces block references it; kept it in `__all__` so Plan 06/07 consumers get a clean type hint without duck-typing.

## RESEARCH §6 Algorithm Fidelity

| Plan RESEARCH §6 step | Implementation | Match |
|-----------------------|----------------|-------|
| `align` count-check raise `TimelineMismatch` | Line 170-174 | ✅ exact |
| Duration band `4.0 <= aud.duration <= 8.0` | Line 177-182 (inclusive) | ✅ exact |
| Speed = `aud.duration / vid.duration` | Line 188 | ✅ exact |
| Speed band `0.8 <= speed <= 1.25` | Line 189-193 (inclusive) | ✅ exact |
| `TimelineEntry(start, end, clip, speed, audio)` | Line 194-202 | ✅ field names match |
| `insert_transition_shots` every 3rd + not last | Line 223-245 | ✅ exact |
| `TEMPLATES = [prop_closeup, silhouette, background_wipe]` | Class constant Line 143 | ✅ exact |
| `random.choice` + `random.uniform(0.5, 1.0)` | Line 236-240 via `self._rng` | ✅ RNG seeded for determinism (enhancement) |

One intentional enhancement over RESEARCH pseudocode: **RNG injection via `__init__(rng_seed)` rather than module-global `random`**. This lets tests assert template determinism (`test_determinism_with_same_seed`) without leaking state across tests. Production callers that pass `rng_seed=None` get system-random behaviour identical to the pseudocode.

## Authentication Gates

None. Plan 05-05 is pure data transformation with no external API surface.

## Known Stubs

None. VoiceFirstTimeline is complete and consumable today. Plan 06 (Shotstack adapter) will import the output types; Plan 07 (shorts_pipeline) will call `align` → `insert_transition_shots` in the ASSEMBLY gate body.

## Verification Evidence

### tests/phase05/ — 113/113 PASS (no regressions; 80 prior + 33 new)
```
C:\Users\PC\AppData\Local\Programs\Python\Python311\Lib\site-packages\requests\__init__.py:113: RequestsDependencyWarning: ...
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 0.23s
```

### Plan 05-05 isolated run — 33/33 PASS
```
python -m pytest tests/phase05/test_voice_first_timeline.py tests/phase05/test_transition_shots.py -q --no-cov
.................................                                        [100%]
33 passed in 0.10s
```

### Final verification block
```
python -c "from scripts.orchestrator.voice_first_timeline import VoiceFirstTimeline, IntegratedRenderForbidden" → exit 0
grep -q "skip_gates" scripts/orchestrator/voice_first_timeline.py → exit 1 (no match — correct)
wc -l scripts/orchestrator/voice_first_timeline.py → 283 lines (within [180, 350])
```

### Acceptance grep tallies
```
class VoiceFirstTimeline            : 1
class TimelineMismatch              : 1
class InvalidClipDuration           : 1
class ClipDurationMismatch          : 1
class IntegratedRenderForbidden     : 1
prop_closeup                        : 3 (string + test + test)
silhouette                          : 3
background_wipe                     : 3
TRANSITION_TEMPLATES                : 2 (constant + docstring)
MIN_CLIP_DURATION = 4.0             : present
MAX_CLIP_DURATION = 8.0             : present
import pydub                        : 0 (absent — correct)
import httpx                        : 0 (absent — correct)
import requests                     : 0 (absent — correct)
```

### Test file tallies
```
tests/phase05/test_voice_first_timeline.py : 18 `def test_` (>= 15 required)
tests/phase05/test_transition_shots.py     : 15 `def test_` (>= 10 required)
IntegratedRenderForbidden references       : 4 in test_voice_first_timeline.py (>= 1 required)
TimelineMismatch references                : 7 in test_voice_first_timeline.py (>= 1 required)
TRANSITION_EVERY_N_CUTS references         : 1 in test_transition_shots.py (>= 1 required)
```

## Self-Check: PASSED

Verified:
- `scripts/orchestrator/voice_first_timeline.py` exists (283 lines).
- `tests/phase05/test_voice_first_timeline.py` exists (233 lines, 18 tests).
- `tests/phase05/test_transition_shots.py` exists (178 lines, 15 tests).
- Both commits present in `git log --oneline -3`: `5d9ab61` (Task 1 feat) and `7375d8c` (Task 2 test).
- `python -c "from scripts.orchestrator.voice_first_timeline import VoiceFirstTimeline, AudioSegment, VideoCut, TimelineEntry, TransitionEntry, IntegratedRenderForbidden, TimelineMismatch, InvalidClipDuration, ClipDurationMismatch"` exits 0.
- Full Phase 5 test suite (`tests/phase05/ -q --no-cov`) exits 0 with 113 passed.
- `grep -c skip_gates scripts/orchestrator/voice_first_timeline.py` outputs 0.
- Line count 283 within plan's mandated [180, 350] range.

Ready for Plan 05-06 (API adapters — Kling/Runway/Typecast/ElevenLabs/Shotstack).
