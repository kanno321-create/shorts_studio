---
phase: 03-harvest
plan: 04
subsystem: infra

tags: [harvest, remotion, shutil, copytree, ignore-patterns, node_modules-exclusion]

requires:
  - phase: 03-harvest-01
    provides: harvest_importer.py stdlib modules (shutil-based copy with ignore_patterns)
  - phase: 03-harvest-02
    provides: path_manifest.json remotion_src_raw entry (source=remotion/src, ignore=[node_modules,__pycache__,*.pyc,.venv,.git], req_id=HARVEST-02)
provides:
  - .preserved/harvested/remotion_src_raw/ tree (40 files, 0.161 MB) — Remotion composition source reference
  - node_modules (758 MB) verifiably excluded; no secret/pycache contamination
  - Wave 1 raw copy track for HARVEST-02 satisfied (complements parallel plans 03-03/05/06)
affects: [phase-04-agent-team-design, phase-05-orchestrator-v2-rewrite]

tech-stack:
  added: []
  patterns:
    - "shutil.copytree + shutil.ignore_patterns defensive ignore layering (manifest.ignore + global_ignore + hardcoded _DEFAULT_IGNORE)"
    - "diff_verifier.deep_diff post-copy validation as acceptance gate (mismatches==[])"

key-files:
  created:
    - .preserved/harvested/remotion_src_raw/Root.tsx
    - .preserved/harvested/remotion_src_raw/index.ts
    - .preserved/harvested/remotion_src_raw/components/ (15 files)
    - .preserved/harvested/remotion_src_raw/compositions/ (11 files)
    - .preserved/harvested/remotion_src_raw/lib/ (12 files incl. transitions/)
  modified:
    - scripts/harvest/audit_log.md (STAGE_3_OK entry appended)

key-decisions:
  - "Used direct shutil.copytree fallback (per plan <action> block) instead of harvest_importer.py --stage 3 because stage 3 requires stages 1-2 to populate manifest dict in same invocation; harvest_importer CLI lacks a 'load manifest only + copy one' mode. Layered ignore_patterns (manifest.ignore + global_ignore + defensive 'node_modules') achieves identical behavior."
  - "Size sanity threshold at 100 MB — actual 0.161 MB confirms no node_modules (758 MB parent) leakage."

patterns-established:
  - "Raw harvest copy pattern: pre-clean dst if exists, layered ignore, post-verify with diff_verifier, size sanity check < 100 MB."
  - "Append [STAGE_3_OK] line to scripts/harvest/audit_log.md for parity with other wave-1 copies even when harvest_importer CLI bypass is used."

requirements-completed:
  - HARVEST-02

duration: 1min
completed: 2026-04-19
---

# Phase 03 Plan 04: REMOTION-COPY Summary

**Copied shorts_naberal/remotion/src/ (40 files, 0.161 MB) to .preserved/harvested/remotion_src_raw/ with node_modules (758 MB) verifiably excluded — HARVEST-02 satisfied.**

## Performance

- **Duration:** ~1 min (~86 s wall time)
- **Started:** 2026-04-18T19:04:42Z
- **Completed:** 2026-04-18T19:06:08Z
- **Tasks:** 1 / 1
- **Files copied:** 40
- **Total size:** 0.161 MB (threshold 100 MB — PASS)

## Accomplishments

- `.preserved/harvested/remotion_src_raw/` populated with full Remotion composition source tree
- Root.tsx + index.ts + components/ (15) + compositions/ (11) + lib/ (12 incl. transitions/presentations) all present
- `node_modules` absent (0 hits via `Path.rglob('node_modules')`) — 758 MB exclusion verified
- `__pycache__` absent (0 hits)
- Secret file patterns absent (client_secret*.json / token_*.json / .env* / *.key / *.pem — 0 hits total)
- `diff_verifier.py remotion_src_raw`: 0 mismatches, exit 0
- Audit log entry `[STAGE_3_OK] remotion_src_raw mode=tree files=40 size_mb=0.161` appended

## Task Commits

1. **Task 1: Execute remotion_src_raw copy with node_modules/pycache ignore** — `4bc7ece` (feat)

_(Plan metadata commit deferred to orchestrator-level wave close; this executor committed the artifact only, per parallel_execution directive using --no-verify.)_

## Files Created/Modified

- `.preserved/harvested/remotion_src_raw/Root.tsx` — Remotion root composition (9082 bytes)
- `.preserved/harvested/remotion_src_raw/index.ts` — Remotion entry (113 bytes)
- `.preserved/harvested/remotion_src_raw/components/` — 15 composition components (BracketCaption, CTAOverlay, crime/, longform/, __tests__/)
- `.preserved/harvested/remotion_src_raw/compositions/` — 11 composition cards (Bar/Comparison/Highlight/Intro/List/Outro + supporting)
- `.preserved/harvested/remotion_src_raw/lib/` — 12 files (props-schema.ts, transitions/, test-gfcar-subs.json fixtures, transitions/presentations/{checkerboard,clock-wipe,glitch,light-leak,pixelate,rgb-split,zoom-blur}.tsx)
- `scripts/harvest/audit_log.md` — appended `[STAGE_3_OK]` line for parity with parallel plans

## Decisions Made

- **Fallback to direct shutil.copytree per plan action block**: `harvest_importer.py --stage 3 --name remotion_src_raw` fails with `[STAGE_3_ERROR] manifest missing entry` because stage 3 depends on stage 2 loading the manifest dict within the same invocation (`stage_enabled(n)` returns True only for `args.stage==0 or args.stage==n`). The plan's `<action>` block anticipated this by providing a Python fallback heredoc — used that path. Ignore semantics are identical: manifest.ignore (`[node_modules, __pycache__, *.pyc, .venv, .git]`) + global_ignore (5 secret patterns) + defensive explicit `node_modules`. End result: behaviorally identical to the intended harvest_importer path; diff_verifier confirms mismatches==[].
- **No additional decisions beyond plan as written.**

## Deviations from Plan

None — plan executed exactly as written. The `<action>` block explicitly provided the `shutil.copytree` Python fallback (lines 126-142 of 03-04-PLAN.md) as an alternative if `--stage copy` is not yet wired; that fallback was used. All acceptance criteria met verbatim.

## Issues Encountered

- **harvest_importer.py --help UnicodeEncodeError (cp949)** on Windows: argparse description contains em-dash (`—`) which Windows cp949 console codec cannot emit. Non-blocking for this task (used fallback Python heredoc). Deferred for future plan if script help output is needed on Windows consoles.
- **harvest_importer.py --stage 3 execution path**: As documented in Decisions above. Not a bug per se — the plan anticipated this with the fallback block. Logged here for Phase 03-07 gate awareness and any future consolidation of stage-isolated invocations.

Both items logged to `.planning/phases/03-harvest/deferred-items.md` would be appropriate if that file is being maintained; neither blocked this plan.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Wave 1 raw copy track for HARVEST-02 complete. Sibling plans 03-03 (theme_bible_raw), 03-05 (hc_checks_raw cherry_pick), 03-06 (api_wrappers_raw cherry_pick) executing in parallel; their commits already visible in `git log` (fba21e4, 51205ba, aeac16b).
- Unblocks: Phase 4 agent team design (can reference Remotion components/compositions naming), Phase 5 Orchestrator v2 rewrite (can reference composition invocation patterns in Root.tsx).
- No blockers introduced.

## Self-Check

**Files:**
- FOUND: .preserved/harvested/remotion_src_raw/Root.tsx
- FOUND: .preserved/harvested/remotion_src_raw/index.ts
- FOUND: .preserved/harvested/remotion_src_raw/components/ (15 files)
- FOUND: .preserved/harvested/remotion_src_raw/compositions/ (11 files)
- FOUND: .preserved/harvested/remotion_src_raw/lib/ (12 files)
- FOUND: scripts/harvest/audit_log.md (STAGE_3_OK line appended)

**Commit:**
- FOUND: 4bc7ece (feat(03-04): copy remotion/src/ to remotion_src_raw (HARVEST-02))

**Acceptance criteria verified:**
- `test -d .preserved/harvested/remotion_src_raw`: PASS
- Subdirs components/, compositions/, lib/: ALL PRESENT
- `! test -d .preserved/harvested/remotion_src_raw/node_modules`: PASS (0 hits via rglob)
- `__pycache__`: 0 hits
- Size < 100 MB: 0.161 MB (PASS)
- `python scripts/harvest/diff_verifier.py remotion_src_raw`: exit 0, 0 mismatches (PASS)
- Secret files: 0 hits across all 5 patterns (PASS)

## Self-Check: PASSED

---
*Phase: 03-harvest*
*Plan: 04 (REMOTION-COPY)*
*Completed: 2026-04-19*
