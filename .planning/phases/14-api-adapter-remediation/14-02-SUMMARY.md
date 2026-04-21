---
phase: 14-api-adapter-remediation
plan: 02
subsystem: testing
tags: [pytest, adapter, wave1, regression, drift-remediation, veo-i2v, runway, elevenlabs, shotstack, notebooklm, moc]

# Dependency graph
requires:
  - phase: 14-api-adapter-remediation
    plan: 01
    provides: "pytest.ini + adapter_contract marker + tests/adapters/ scaffold + --strict-markers active + --ignore addopts for D08-DEF-01"
provides:
  - 15 pre-existing pytest failures (phase05/06/07) transitioned to green via 5 atomic edits
  - veo_i2v.py self-documentation freed of T2V blacklist-tripping tokens (source-level 금기 #4 compliance)
  - Runway adapter test aligned to Phase 9.1 D-12 gen4.5 rename
  - Elevenlabs/Shotstack soft caps raised (360/420) to accommodate Phase 9.1 D-11/D-13 intentional growth
  - MOC status invariant relaxed to scaffold|partial with ready|complete drift still blocked (canonical regex shared with Plan 04)
  - NotebookLM default skill path updated to secondjob_naberal install (Phase 9 D09-DEF-02 migration)
  - Wave 1 regression sweep evidence log anchoring 742 passed / 0 failed (ADAPT-04 SC#1 proof)
affects: [14-03, 14-04, 14-05, 15]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Canonical MOC status regex ^status:\\s*(scaffold|partial)\\b — shared verbatim with Plan 04 Task 14-04-03"
    - "Adapter self-documentation discipline: blacklist-tripping tokens relocated to contract tests (tests/adapters/) not source modules (scripts/orchestrator/api/)"
    - "Per-atom commit discipline with single-file exception rule (file-level disjointness except for multi-knob single-invariant edits)"
    - "Wave-boundary sweep log artefact convention: .planning/phases/XX-name/XX-YY-wave{N}-sweep.log"

key-files:
  created:
    - .planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log
    - .planning/phases/14-api-adapter-remediation/14-02-SUMMARY.md
  modified:
    - scripts/orchestrator/api/veo_i2v.py
    - tests/phase05/test_kling_adapter.py
    - tests/phase05/test_line_count.py
    - tests/phase06/test_moc_linkage.py
    - tests/phase06/test_notebooklm_wrapper.py

key-decisions:
  - "D-17 invariant reinterpreted: 'MOC never promotes to ready/complete', NOT 'MOC stays scaffold forever' — Phase 9.1 scaffold→partial is legitimate"
  - "veo_i2v.py module-footer assert deleted — physical-absence guarantee reassigned to 3 external layers (blacklist grep + pre_tool_use + Wave 2 contract test)"
  - "Soft caps raised tight (elevenlabs 350 actual vs 360 cap, shotstack 414 actual vs 420 cap) — silent further growth still caught"
  - "Wave 1 sweep command uses PYTHONIOENCODING=utf-8 (RESEARCH R5 mitigation) — Korean test names round-trip clean"
  - "POSIX-safe verify syntax adopted: [ \"$(grep -cE '[0-9]+ failed' log)\" = \"0\" ] instead of bash-only ! grep"

patterns-established:
  - "Source-level 금기 #4 compliance: adapter self-documentation must not use the tokens the blacklist forbids; move assertions into tests/adapters/"
  - "Canonical regex reuse across plans: identical regex string shared verbatim between Plan 02 and Plan 04 to enforce drift-control consistency"
  - "Inline authority comments: every remediation cites its RESEARCH bucket + source Phase decision (D-11/D-12/D-13/D-17/D09-DEF-02) in code for future audit trail"

requirements-completed: [ADAPT-04]

# Metrics
duration: 14m12s
completed: 2026-04-21
---

# Phase 14 Plan 02: Wave 1 Regression Remediation Summary

**15 pre-existing pytest failures in phase05/06/07 flipped to green via 5 atomic edits (1 adapter self-doc rewrite + 4 test-to-code synchronizations) + Wave 1 sweep log anchored at 742 passed / 0 failed in 633s — ADAPT-04 SC#1 proven.**

## Performance

- **Duration:** 14m12s (852 seconds)
- **Started:** 2026-04-21T10:10:49Z
- **Completed:** 2026-04-21T10:25:01Z
- **Tasks:** 6/6 completed
- **Files modified:** 5 (1 production module + 4 test files)
- **Files created:** 1 (sweep log artefact)
- **Atomic commits:** 6 (one per task, per-atom discipline honoured)

## Accomplishments

- **15 failures → 0 failures** in phase05/06/07 regression sweep. Pre-remediation baseline (14-RESEARCH measured 2026-04-21): 15 failed, 727 passed in 660.60s. Post-Wave-1: **742 passed, 0 failed in 633.34s**.
- **Bucket-by-bucket flip**:
  - Bucket A (Phase 9.1 direct cascade, 3): A-1 gen4.5 / A-2 caps / A-3 aggregator cascade → green
  - Bucket A2 (veo_i2v self-doc collateral, 1): A-4 blacklist grep → green
  - Bucket A3 (Phase 5 acceptance aggregators, 2): A-5 + A-6 → green by cascade
  - Bucket B (Phase 6 D09-DEF-02 drift, 2): B-1 MOC regex / B-2 notebooklm path → green
  - Bucket B2 (Phase 6 aggregators, 2): B-3 + B-4 → green by cascade
  - Bucket C (Phase 7 regression aggregators, 5): C-1..C-5 → green by cascade
- **veo_i2v.py source cleaned** of T2V blacklist-tripping tokens (금기 #4 compliance). The module-footer assert was deleted; its physical-absence guarantee is now enforced by 3 independent layers (repo blacklist grep + pre_tool_use.py deprecated_patterns.json + Phase 14 Wave 2 contract test scheduled for Plan 14-03).
- **Canonical regex established** for MOC status invariant (`^status:\s*(scaffold|partial)\b`) — shared verbatim between Plan 02 Task 14-02-04 and Plan 04 Task 14-04-03 acceptance for drift-control consistency across plans.

## Task Commits

Each task committed atomically per plan `commit_discipline: per-atom`:

1. **Task 14-02-01: veo_i2v self-documentation rewrite (T2V blacklist unblock)** — `acd3906` (fix)
2. **Task 14-02-02: Runway model assertion — gen3_alpha_turbo → gen4.5 (D-12)** — `623d774` (fix)
3. **Task 14-02-03: Line caps raise — elevenlabs 340→360, shotstack 400→420** — `1973735` (fix)
4. **Task 14-02-04: MOC status invariant — scaffold|partial allowed, ready|complete blocked** — `0afef9c` (fix)
5. **Task 14-02-05: NotebookLM default skill path — shorts_naberal → secondjob_naberal (D09-DEF-02)** — `552f652` (fix)
6. **Task 14-02-06: Wave 1 regression sweep log — 15 failed → 0 failed, 742 passed** — `5cd6ef0` (chore)

_Per-atom note_: Task 14-02-03 edits two knobs (`elevenlabs.py: 360` + `shotstack.py: 420`) inside the same `caps` dict invariant in a single file — the documented single-file exception to per-atom file-level disjointness rule (frontmatter clarification in 14-02-PLAN.md lines 18-25). All other tasks are strictly 1 file = 1 commit.

## Files Created/Modified

### Modified (5)
- `scripts/orchestrator/api/veo_i2v.py` — module-footer T2V guard block (lines 179-185) replaced with comment-only self-documentation. Line count 185 → 185 (delta 0; assert deletion offset by comment expansion).
- `tests/phase05/test_kling_adapter.py` — line 205 `"gen3_alpha_turbo"` → `"gen4.5"` + authority comment (Phase 9.1 D-12).
- `tests/phase05/test_line_count.py` — lines 63-70 `caps` dict raised `elevenlabs.py: 340→360` + `shotstack.py: 400→420` with inline authority comments (Phase 9.1 D-11/D-13 + Phase 14 RESEARCH §Bucket A A-2).
- `tests/phase06/test_moc_linkage.py` — `test_moc_frontmatter_unchanged_scaffold` rewritten from substring check to bidirectional regex pair (allow scaffold|partial, block ready|complete) with D-17 invariant re-articulated in docstring.
- `tests/phase06/test_notebooklm_wrapper.py` — `test_default_skill_path_is_the_2026_install` expected string `shorts_naberal` → `secondjob_naberal` with D09-DEF-02 authority comment.

### Created (1)
- `.planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log` — 24 lines, authoritative evidence artefact for ADAPT-04 SC#1. Captures full phase05/06/07 pytest sweep with pass count, deprecation warning summary, and total runtime.

## Decisions Made

- **D-17 invariant reinterpretation (Task 14-02-04)**: The D-17 invariant is "MOC-as-TOC never promotes to a leaf-ready status (ready|complete)", not "MOC stays scaffold forever". This allows Phase 9.1 `scaffold → partial` legitimate progression while preserving drift control against ready/complete. Canonical regex `^status:\s*(scaffold|partial)\b` adopted with line-anchored + word-boundary matching (strictly stricter than prior `in text` substring).
- **veo_i2v.py module-level assert deletion (Task 14-02-01)**: The `assert not hasattr(VeoI2VAdapter, "text_to_video")` block uses banned tokens in its own message, creating a self-reference paradox with the repo blacklist grep. Chose RESEARCH-recommended Option (b) — delete the assert from source and reassign its guarantee to Wave 2 contract test (`tests/adapters/test_veo_i2v_contract.py::test_no_text_only_method`, scheduled for Plan 14-03). Physical-absence now enforced by 3 external layers: (1) blacklist grep, (2) pre_tool_use deprecated_patterns, (3) incoming contract test.
- **Tight soft caps (Task 14-02-03)**: Chose RESEARCH-recommended cap adjustment over file splitting. Caps set tight (actual 350 < cap 360, actual 414 < cap 420) so any further silent growth still gets caught — drift control preserved at the ~10-line margin.
- **Canonical regex cross-plan sharing**: The MOC status regex adopted in Task 14-02-04 is the same string Plan 04 Task 14-04-03 uses for its acceptance check. Written verbatim in both plans' rationale for consistency audit. Future plans adding MOC files must use this exact regex.
- **POSIX-safe verify syntax**: Task 14-02-06 acceptance uses `[ "$(grep -cE '[0-9]+ failed' log)" = "0" ]` instead of bash-only `! grep`. Runs cleanly under POSIX sh + bash + zsh.

## Deviations from Plan

**None — plan executed exactly as written.**

Every task landed in the specified file at the specified lines with the specified edit content. All 6 acceptance gates passed on first pytest run with zero re-iteration. Zero Rule 1/2/3/4 deviations. Zero auto-fixes required.

The plan's pre-step boundary verification (`cat -n scripts/orchestrator/api/veo_i2v.py | sed -n '175,190p'`) confirmed the RESEARCH-pinned line numbers (179-185) exactly, so Task 14-02-01 Edit applied surgically without adjustment.

## Evidence Blocks (CLAUDE.md 필수사항 #8)

### Baseline vs Post-Wave-1 sweep comparison

| Metric       | Pre-Wave-1 (14-RESEARCH 2026-04-21) | Post-Wave-1 (14-02-wave1-sweep.log) | Delta |
| ------------ | ----------------------------------- | ----------------------------------- | ----- |
| **Passed**   | 727                                 | **742**                             | **+15** |
| **Failed**   | 15                                  | **0**                               | **-15** |
| **Wall**     | 660.60s                             | **633.34s**                         | -27.26s (-4.1%) |
| **Warnings** | —                                   | 2 (intentional D-11 DeprecationWarning) | — |

### Task 14-02-01 evidence (T2V token count)

```bash
$ grep -cE "(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video" scripts/orchestrator/api/veo_i2v.py
0

$ py -3.11 -c "from scripts.orchestrator.api.veo_i2v import VeoI2VAdapter; assert not hasattr(VeoI2VAdapter, 'image_to_video_text_only')"
(exit 0 — no AssertionError)

$ pytest tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator -x --no-cov -q
.                                                                        [100%]
1 passed in 0.10s
```

### Task 14-02-02 evidence (gen4.5 grep)

```bash
$ grep -c "gen4.5" tests/phase05/test_kling_adapter.py
1
$ grep -c "gen3_alpha_turbo" tests/phase05/test_kling_adapter.py
0
$ grep -c "720:1280" tests/phase05/test_kling_adapter.py
1
```

### Task 14-02-03 evidence (caps grep)

```bash
$ grep -c "elevenlabs.py.*360" tests/phase05/test_line_count.py
1
$ grep -c "shotstack.py.*420" tests/phase05/test_line_count.py
1
$ grep -c "Phase 9.1 D-13" tests/phase05/test_line_count.py
1
$ grep -c "Phase 14 RESEARCH" tests/phase05/test_line_count.py
2
```

### Task 14-02-04 evidence (regex + authority)

```bash
$ grep -c "scaffold|partial" tests/phase06/test_moc_linkage.py
2   # regex literal + docstring reference
$ grep -c "ready|complete" tests/phase06/test_moc_linkage.py
2   # blocked-drift regex + docstring
$ grep -c "Phase 14 RESEARCH" tests/phase06/test_moc_linkage.py
1
$ grep -c "import re" tests/phase06/test_moc_linkage.py
2   # module header + function-local
```

### Task 14-02-05 evidence (path migration)

```bash
$ grep -c "secondjob_naberal/.claude/skills/notebooklm" tests/phase06/test_notebooklm_wrapper.py
1
$ grep -c "shorts_naberal/.claude/skills/notebooklm" tests/phase06/test_notebooklm_wrapper.py
0   # pre-migration path eliminated
$ grep -c "D09-DEF-02" tests/phase06/test_notebooklm_wrapper.py
1
```

### Task 14-02-06 sweep log summary line (final 1-line quotation)

```
742 passed, 2 warnings in 633.34s (0:10:33)
```

### Task 14-02-06 POSIX-safe verify output

```bash
$ test -f .planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log ; echo $?
0   # exists
$ grep -cE "^[0-9]+ passed" .planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log
1   # summary-line pattern present
$ [ "$(grep -cE '[0-9]+ failed' .planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log)" = "0" ] ; echo $?
0   # zero failed-lines → exit 0 (POSIX-safe, bash-agnostic)
```

## veo_i2v.py line-count delta

| Before       | After        | Delta |
| ------------ | ------------ | ----- |
| 185 lines    | 185 lines    | 0     |

The 7-line `assert` block (179-185) was replaced by a 7-line comment block. Net line count unchanged, but banned-token count changed from 3 hits → 0 hits.

## Issues Encountered

**None.** Plan specification was precise enough that every edit landed on the first attempt. The sweep took ~10m33s (as 14-RESEARCH predicted ~11m) and surfaced exactly the expected 742 passed / 0 failed — no new failure modes, no flaky tests, no environment issues.

The only environment-level observation is the pre-existing `RequestsDependencyWarning` about urllib3/chardet version mismatch, which is unrelated to Phase 14 scope and was present in the baseline sweep too.

## CLAUDE.md Compliance Check

| Rule | Applied in Task | Evidence |
| ---- | ---------------- | -------- |
| 금기 #2 (TODO 금지) | All tasks | `grep -c "TODO" <modified files>` — 0 hits |
| 금기 #3 (try-except 침묵 폴백) | Task 14-02-01 (assert deletion), Task 14-02-04 (regex failure propagation) | Assert removal documented as 3-layer compensation; regex failures raise AssertionError with diagnostic text head |
| 금기 #4 (T2V 금지) | Task 14-02-01 | `grep -cE "...t2v...|text_to_video|text2video" veo_i2v.py` → 0 |
| 금기 #6 (shorts_naberal 원본 수정) | Task 14-02-05 | Only test file inside `studios/shorts/tests/phase06/` modified; `shorts_naberal/` directory untouched |
| 필수 #4 (FAILURES.md append-only) | All tasks | No FAILURES.md edit in this plan. No new failure patterns surfaced. |
| 필수 #5 (STRUCTURE Whitelist) | Task 14-02-06 | sweep log anchored under `.planning/phases/` which is whitelisted |
| 필수 #8 (증거 기반 보고) | This SUMMARY + all task commits | Every task has pytest output quoted in commit body + grep counts in this Evidence Blocks section |

## Next Phase Readiness

**Wave 2 (Plan 14-03) unblocked** — phase05/06/07 regression green, contract tests in `tests/adapters/` can land against a clean baseline without the 15 pre-existing noise. The veo_i2v physical-absence guarantee is now a scheduled responsibility for `tests/adapters/test_veo_i2v_contract.py::test_no_text_only_method` (Plan 14-03 Task 14-03-01 scope).

**Wave 4 phase-gate scope preserved** — 14-VALIDATION.md row 14-05-01 sweep command is unchanged; the passing baseline of 742 now becomes the floor for Wave 4's final regression check (target: 742 + adapter_contract_count ≥ 25).

**ADAPT-04 Success Criteria #1 proven** — `pytest tests/phase05 tests/phase06 tests/phase07` 0 failures. Remaining Phase 14 criteria (ADAPT-01/02/03/05/06) are all Wave 2/3/4 scope.

**No blockers** for Plan 14-03 (Wave 2 contract tests) execution.

## Self-Check: PASSED

- [x] `scripts/orchestrator/api/veo_i2v.py` exists and was modified — FOUND
- [x] `tests/phase05/test_kling_adapter.py` exists and was modified — FOUND
- [x] `tests/phase05/test_line_count.py` exists and was modified — FOUND
- [x] `tests/phase06/test_moc_linkage.py` exists and was modified — FOUND
- [x] `tests/phase06/test_notebooklm_wrapper.py` exists and was modified — FOUND
- [x] `.planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log` exists — FOUND (24 lines, `742 passed, 2 warnings in 633.34s` summary line present)
- [x] Commit `acd3906` exists (Task 14-02-01) — FOUND
- [x] Commit `623d774` exists (Task 14-02-02) — FOUND
- [x] Commit `1973735` exists (Task 14-02-03) — FOUND
- [x] Commit `0afef9c` exists (Task 14-02-04) — FOUND
- [x] Commit `552f652` exists (Task 14-02-05) — FOUND
- [x] Commit `5cd6ef0` exists (Task 14-02-06) — FOUND
- [x] `grep -cE "(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video" scripts/orchestrator/api/veo_i2v.py` → 0
- [x] `grep -cE '[0-9]+ failed' .planning/phases/14-api-adapter-remediation/14-02-wave1-sweep.log` → 0
- [x] All 5 pinned single-nodeid pytest commands exit 0 (Task 14-02-01..05 acceptance)
- [x] Wave 1 sweep `pytest tests/phase05 tests/phase06 tests/phase07` → 742 passed, 0 failed
- [x] Zero TODO in any modified file
- [x] Zero `skip_gates` in any modified file

---
*Phase: 14-api-adapter-remediation*
*Plan: 02 (Wave 1 Regression Remediation)*
*Completed: 2026-04-21*
