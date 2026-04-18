---
phase: 03-harvest
plan: 07
subsystem: harvest

# Dependency graph
requires:
  - phase: 03-harvest
    provides: path_manifest.json (Plan 03-02) — 4 raw_dir entries with per-entry + global ignore patterns
  - phase: 03-harvest
    provides: ".preserved/harvested/theme_bible_raw/ (Plan 03-03) — 7 channel bibles byte-identical"
  - phase: 03-harvest
    provides: ".preserved/harvested/remotion_src_raw/ (Plan 03-04) — 40 Remotion src files, node_modules excluded"
  - phase: 03-harvest
    provides: ".preserved/harvested/hc_checks_raw/ (Plan 03-05) — hc_checks.py + test_hc_checks.py byte-identical"
  - phase: 03-harvest
    provides: ".preserved/harvested/api_wrappers_raw/ (Plan 03-06) — 5 wrappers byte-identical"
provides:
  - ".claude/failures/_imported_from_shorts_naberal.md (500 lines) — HARVEST-04 read-only FAILURES archive for D-2 저수지 regime"
  - "scripts/harvest/audit_log.md aggregated Wave 2 record (diff-clean proof + FAILURES merge receipt)"
  - "Aggregate diff verification proof: 4/4 raw dirs mismatch-count = 0 (ALL_CLEAN)"
affects: [phase-06-feedback-loop, phase-10-operations, phase-04-content-audio, phase-05-video, phase-05-orchestrator]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fnmatch.fnmatchcase for ignore-pattern matching (NOT substring `in`) — glob-style semantics matches copy-time shutil.ignore_patterns exactly"
    - "SOURCES locked list constant for FAILURES merge (explicit path list, NOT glob) — prevents silent drift when future FAILURES files added to shorts_naberal"
    - "Idempotency via marker check: grep for `<!-- source: ... -->` before append; second run SKIPs cleanly (P5 avoidance per RESEARCH.md § Common Pitfalls)"
    - "sha256 digest stored in source comment block for downstream integrity auditing"

key-files:
  created:
    - ".claude/failures/_imported_from_shorts_naberal.md (500 lines, 42468 bytes source + 5 line header + wrapper) — HARVEST-04 archive"
  modified:
    - "scripts/harvest/audit_log.md (Wave 2 Task 1 + Task 2 entries appended)"

key-decisions:
  - "Used inline Python fallback for aggregate diff verification — diff_verifier.py --all flag NOT yet wired (Plan 01 deliverable scope limited to per-dir CLI). Inline implementation uses identical deep_diff + filecmp.cmp(shallow=False) semantics so the result is equivalent; follow-up plan may wire --all flag directly but not required for correctness."
  - "SOURCES locked list pattern enforced (B-2 FIX) — explicit `[Path('.../orchestrator.md')]` list instead of `glob('**/FAILURES.md')`. RESEARCH.md §6 verified only 1 source file exists at 2026-04-19 (orchestrator.md). Future additions MUST extend the list explicitly — comment in code documents this invariant."
  - "fnmatch.fnmatchcase (not `in` containment) chosen for ignore pattern matching — matches shutil.ignore_patterns glob semantics used during Wave 1 copies; substring match would produce false positives on patterns like `*.pyc` vs `file.pyc.bak`."

patterns-established:
  - "Aggregate verification protocol: iterate path_manifest.json raw_dir entries → branch on source vs cherry_pick mode → accumulate mismatches → exit 1 if non-empty. Reusable for future Wave 1 style copies."
  - "Archive-merge template: header (title + read-only notice + D-2 regime link) → per-source block (source marker + imported date + sha256 + content verbatim + END marker). Marker pair enables deterministic idempotency check."
  - "Audit log accumulation: append-only markdown with timestamped section headers per plan/wave. Becomes the evidence chain for Phase 3 lockdown (Plan 03-09)."

requirements-completed: [HARVEST-04]

# Metrics
duration: 5min
completed: 2026-04-19
---

# Phase 03 Plan 07: DIFF-VERIFY + FAILURES-MERGE Summary

**Wave 1 aggregate integrity proven (0 mismatches across 4 raw dirs) and HARVEST-04 satisfied — shorts_naberal orchestrator.md (487 lines, sha256 978bb938...) merged into D-2 저수지 read-only archive with idempotent marker-guarded append.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-19T04:10:00Z (approx)
- **Completed:** 2026-04-19T04:15:00Z
- **Tasks:** 2 of 2
- **Files modified:** 2 (1 created archive + 1 audit log update)

## Accomplishments

- Aggregate diff verification across all 4 raw dirs returned ALL_CLEAN (theme_bible_raw / remotion_src_raw / hc_checks_raw / api_wrappers_raw — each 0 mismatches)
- Created `.claude/failures/_imported_from_shorts_naberal.md` (500 lines) with read-only archive header + D-2 저수지 notice + full verbatim orchestrator.md content wrapped by source markers + sha256 digest
- Idempotency verified via dry-run: second invocation correctly SKIPs (marker check passes, no duplicate append, line count stays 500)
- SOURCES locked list pattern enforced — explicit single-path constant in both primary importer branch and fallback block
- fnmatch.fnmatchcase applied for ignore-pattern matching (matches copy-time shutil.ignore_patterns glob semantics)
- audit_log.md updated with cumulative Wave 2 Task 1 + Task 2 entries

## Task Commits

1. **Task 1: diff_verifier aggregate ALL_CLEAN** — `ad98b32` (feat)
2. **Task 2: FAILURES merge HARVEST-04** — `1ff5768` (feat)

**Plan metadata commit:** pending (will be created together with SUMMARY.md + STATE.md + ROADMAP.md updates)

## Files Created/Modified

- `.claude/failures/_imported_from_shorts_naberal.md` (CREATED — 500 lines, 487 lines from orchestrator.md + 8 lines header + 5 lines per-source wrapper block)
- `scripts/harvest/audit_log.md` (MODIFIED — appended Wave 2 Task 1 "diff_verifier aggregate" + Task 2 "FAILURES merge" sections)

## Verification Results

### Task 1: Aggregate diff verification

```
[theme_bible_raw] mismatches: 0
[remotion_src_raw] mismatches: 0
[hc_checks_raw] mismatches: 0
[api_wrappers_raw] mismatches: 0
ALL_CLEAN
```

### Task 2: FAILURES merge acceptance

| Criterion | Expected | Actual | Status |
|-----------|----------|--------|--------|
| File exists | yes | yes | OK |
| Line count | ≥ 487 | 500 | OK |
| Source marker count | exactly 1 | 1 | OK |
| END source marker count | exactly 1 | 1 | OK |
| D-2 저수지 text | present | present | OK |
| sha256 line | present | `978bb9381fee4e879c99915277a45778091b06f997b6c7355a155a5169ae1559` | OK |
| Idempotency | re-run SKIPs | SKIP confirmed, lines unchanged | OK |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] diff_verifier.py --all flag not yet wired**
- **Found during:** Task 1
- **Issue:** Plan's preferred command `python scripts/harvest/diff_verifier.py --all` fails — the `_cli()` in `diff_verifier.py` only accepts a single `raw_dir_name` positional argument. `--all` flag was not implemented as part of Plan 01's deliverable.
- **Fix:** Used the plan's explicitly-documented fallback inline Python block (per plan's `<action>` section which provides both primary and fallback commands side-by-side). Identical deep_diff + filecmp.cmp(shallow=False) semantics produce equivalent result.
- **Files modified:** scripts/harvest/audit_log.md
- **Commit:** ad98b32
- **Note:** Wiring `--all` into diff_verifier.py is a candidate improvement for a future plan but is not required for Phase 3 completion — fallback is authoritative per plan text.

### Auth Gates

None — all operations local-only (no remote API calls).

## Source Integrity

- **shorts_naberal/.claude/failures/orchestrator.md**
  - Lines: 487
  - Bytes: 42,468
  - SHA-256: `978bb9381fee4e879c99915277a45778091b06f997b6c7355a155a5169ae1559`
  - Verified 2026-04-19

## HARVEST-04 Compliance

HARVEST-04 requires: "shorts_naberal FAILURES 이관 (read-only archive for D-2 저수지)". Satisfied via:
1. Target file created at canonical path `studios/shorts/.claude/failures/_imported_from_shorts_naberal.md`
2. Full 487-line orchestrator.md content embedded verbatim (byte-identical, sha256 digest recorded)
3. Read-only archive notice in header
4. D-2 저수지 regime link in header (Phase 10 첫 1~2개월 SKILL patch 금지 참조 전용)
5. Traceable per-source comment block (source + imported + sha256 + END markers)
6. Idempotent re-merge (P5 avoidance per RESEARCH.md § Common Pitfalls)

## Phase 3 Wave Progress

- Wave 0: 03-01 (harvest_importer) + 03-02 (path_manifest) — COMPLETE
- Wave 1: 03-03 / 03-04 / 03-05 / 03-06 (4 raw dir copies) — COMPLETE (all 4 diff-clean)
- Wave 2: **03-07 (this plan) — COMPLETE**
- Wave 3: 03-08 decisions.md — PENDING
- Wave 4: 03-09 lockdown — PENDING

## Self-Check: PASSED

- [x] `.claude/failures/_imported_from_shorts_naberal.md` — FOUND (500 lines)
- [x] `scripts/harvest/audit_log.md` — FOUND (updated with Wave 2 entries)
- [x] Commit `ad98b32` (Task 1) — FOUND in git log
- [x] Commit `1ff5768` (Task 2) — FOUND in git log
- [x] All success criteria met (diff ALL_CLEAN, ≥487 lines, exactly 1 marker pair, SOURCES locked, fnmatch.fnmatchcase used, idempotency verified)
