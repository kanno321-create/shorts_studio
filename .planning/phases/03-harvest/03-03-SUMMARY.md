---
phase: 03-harvest
plan: 03
subsystem: infra
tags: [harvest, shutil-copytree, filecmp, channel-bibles, theme-bible, niche]

# Dependency graph
requires:
  - phase: 03-harvest
    provides: "path_manifest.json (Plan 03-02) — theme_bible_raw entry with .claude/channel_bibles source, 7 md files, HARVEST-01 req_id"
  - phase: 03-harvest
    provides: "harvest_importer.py + diff_verifier.py (Plan 03-01 parallel track) — stage 3/4 executors and recursive filecmp.dircmp wrapper"
provides:
  - ".preserved/harvested/theme_bible_raw/ populated with 7 byte-identical .md files (README + 6 niche bibles: documentary, humor, incidents, politics, trend, wildlife)"
  - "scripts/harvest/audit_log.md with STAGE_COPY_theme_bible_raw_OK entry"
  - "HARVEST-01 requirement satisfied (physical copy + verified diff-empty)"
affects: [04-agent-team-design, 05-orchestrator, wiki-continuity-bible]

# Tech tracking
tech-stack:
  added: []
  patterns: ["manifest-driven shutil.copytree with ignore_patterns merged from per-entry ignore + global_ignore secret patterns", "filecmp.dircmp deep_diff gate (mismatches == [] acceptance)"]

key-files:
  created:
    - ".preserved/harvested/theme_bible_raw/README.md"
    - ".preserved/harvested/theme_bible_raw/documentary.md"
    - ".preserved/harvested/theme_bible_raw/humor.md"
    - ".preserved/harvested/theme_bible_raw/incidents.md"
    - ".preserved/harvested/theme_bible_raw/politics.md"
    - ".preserved/harvested/theme_bible_raw/trend.md"
    - ".preserved/harvested/theme_bible_raw/wildlife.md"
    - "scripts/harvest/audit_log.md"
  modified: []

key-decisions:
  - "Used manifest-driven shutil.copytree fallback because harvest_importer.py --stage 3 --name <single> hits a stage-gate bug (stage_enabled check skips stage 2 manifest load, making stage 3 see empty manifest). Fallback implements byte-for-byte identical logic and is explicitly authorized by the plan <action> block. Bug logged to deferred-items for Plan 03-01 track to address."

patterns-established:
  - "Raw-dir harvest unit: {source path}/{cherry_pick} -> .preserved/harvested/{name}/ via shutil.copytree + merged ignore patterns; verify with scripts/harvest/diff_verifier.py {name}"
  - "Pre-clean guard: rmtree existing dest before copy (E2 edge case), safe because lockdown is Wave 4 (not yet applied)"

requirements-completed: [HARVEST-01]

# Metrics
duration: 1min
completed: 2026-04-19
---

# Phase 03-harvest Plan 03: THEME-BIBLE-COPY Summary

**shorts_naberal .claude/channel_bibles/ (7 .md files, 22,951 bytes) copied byte-identical to .preserved/harvested/theme_bible_raw/ with diff_verifier mismatches=[]**

## Performance

- **Duration:** ~1 min (copy + verify + commit)
- **Started:** 2026-04-18T19:04:13Z
- **Completed:** 2026-04-18T19:05:14Z
- **Tasks:** 1 (Task 1: Execute theme_bible_raw copy via harvest_importer)
- **Files modified:** 8 committed (7 .md + audit_log.md)

## Accomplishments

- 7 channel bibles physically ingested into `.preserved/harvested/theme_bible_raw/`: README.md, documentary.md, humor.md, incidents.md, politics.md, trend.md, wildlife.md
- `filecmp.dircmp` deep diff returned `0 mismatches` — byte-identical to source
- `shorts_naberal/.claude/channel_bibles/` source bytes unchanged (read-only contract preserved)
- No secret-file leakage (global_ignore blocked client_secret*.json, token_*.json, .env*, *.key, *.pem, __pycache__, *.pyc)
- HARVEST-01 satisfied — Phase 4 agents can reference channel bibles from the preserved copy
- Wave 1 parallel execution unblocked for Plans 03-04 / 03-05 / 03-06 (no file overlap)

## Task Commits

Each task was committed atomically with `--no-verify`:

1. **Task 1: Execute theme_bible_raw copy via harvest_importer** — `fba21e4` (feat)

## Files Created/Modified

- `.preserved/harvested/theme_bible_raw/README.md` — channel_bibles index/readme
- `.preserved/harvested/theme_bible_raw/documentary.md` — documentary niche bible
- `.preserved/harvested/theme_bible_raw/humor.md` — humor niche bible
- `.preserved/harvested/theme_bible_raw/incidents.md` — incidents niche bible
- `.preserved/harvested/theme_bible_raw/politics.md` — politics niche bible
- `.preserved/harvested/theme_bible_raw/trend.md` — trend niche bible
- `.preserved/harvested/theme_bible_raw/wildlife.md` — wildlife niche bible
- `scripts/harvest/audit_log.md` — created; first entry = `STAGE_COPY_theme_bible_raw_OK 7 files copied`

**Copy metrics:**
- File count: 7 (expected 7) — matches source exactly
- Total bytes: 22,951
- Ignored files: 0 (channel_bibles/ contains only .md files; global_ignore patterns had nothing to exclude)
- diff_verifier exit code: 0 (mismatches=[])

## Decisions Made

- **Fallback over importer CLI for single-name invocation.** Plan `<action>` authorized a manifest-driven Python fallback when `--stage copy` CLI "is not yet wired". The existing `--stage 3 --name theme_bible_raw` path fails because the importer's stage-gate logic (`stage_enabled(n) = args.stage == 0 or args.stage == n`) also gates stages 1 and 2 — so stage 3 runs against an empty manifest dict and raises `KeyError: "manifest missing entry 'theme_bible_raw'"`. The fallback implements byte-for-byte identical copy logic (same `shutil.ignore_patterns(*(entry['ignore'] + m['global_ignore']))`, same `copytree` call, same pre-clean). The importer bug is out-of-scope for this plan (Plan 03-01 parallel track owns the importer) and logged as a deferred issue.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] harvest_importer --stage 3 --name single-name invocation fails (manifest unloaded)**
- **Found during:** Task 1 (first attempted execution path)
- **Issue:** `python scripts/harvest/harvest_importer.py --stage 3 --name theme_bible_raw` raises `[STAGE_3_ERROR] "manifest missing entry 'theme_bible_raw'"` and exits 1. Root cause: the stage-gate predicate `stage_enabled(n)` short-circuits stages 1 and 2 when `--stage 3` is explicit, so the manifest JSON is never loaded and stage 3 sees `manifest = {}`.
- **Fix:** Switched to the manifest-driven `shutil.copytree` fallback that the plan `<action>` block explicitly authorizes for this contingency ("If `--stage copy` CLI is not yet wired in harvest_importer.py [Plan 01 deliverable], use this fallback Python one-liner implementing the exact same logic"). Manually appended a well-formed `STAGE_COPY_theme_bible_raw_OK` line to `scripts/harvest/audit_log.md` to preserve the audit contract.
- **Files modified:** `.preserved/harvested/theme_bible_raw/` (7 files created), `scripts/harvest/audit_log.md` (1 line appended)
- **Verification:** `python scripts/harvest/diff_verifier.py theme_bible_raw` exits 0 with `[OK] theme_bible_raw: 0 mismatches`. All 7 expected file names present. No secret-pattern files in dest.
- **Committed in:** `fba21e4` (Task 1 commit)

**Scope boundary:** The importer's stage-gate bug itself is not fixed here. It belongs to Plan 03-01 (harvest-importer AGENT.md + stdlib modules) which is the parallel Wave 1 track owning `harvest_importer.py`. Fixing it inside Plan 03-03 would cross plan boundaries. Logged below for Plan 03-01 to pick up.

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fallback path is plan-authorized and byte-identical to the intended logic. All acceptance criteria still met. No scope creep.

## Deferred Issues

- **[harvest_importer.py stage-gate bug]** `--stage N --name X` single-dir invocation fails for N ≥ 3 because stages 1 and 2 (blacklist + manifest load) are also gated by `stage_enabled`. Three possible fixes for Plan 03-01 track to consider:
  1. Make stages 1 and 2 always run (unconditional prerequisite) regardless of `--stage` value.
  2. When `--stage N` is specified for N ≥ 3, auto-enable stages 1 through N.
  3. Raise a clear error early if `--stage 3` is set without `--stage 0` or pre-loaded state.
  Location: `scripts/harvest/harvest_importer.py:249-251` (stage_enabled definition) and the stage 3 block at `harvest_importer.py:277-293`. Detected 2026-04-18 during Plan 03-03 Task 1.

## Issues Encountered

- `harvest_importer.py --help` prints a `UnicodeEncodeError` on Windows cp949 console due to em-dash (`\u2014`) in the description string. Not blocking for execution (code path runs via `argparse.parse_args()` which doesn't require help output). Noted for awareness; low priority.

## User Setup Required

None — no external service configuration needed.

## Next Phase Readiness

- Wave 1 proceeds: Plans 03-04 (remotion_src_raw), 03-05 (hc_checks_raw), 03-06 (api_wrappers_raw) are independent of this plan's files and can run in parallel — **no file conflicts**.
- Wave 2 diff-verification aggregation can now include `theme_bible_raw` in its checklist.
- Phase 4 (Agent Team Design) has a stable, verified, read-only reference for channel bibles (theme_bible_raw/) to cite from agent prompts.
- Lockdown (Wave 4) is intentionally not yet applied; the dir is still writable until the full harvest is assembled.

---

## Self-Check: PASSED

**Files verified on disk:**
- FOUND: `.preserved/harvested/theme_bible_raw/README.md`
- FOUND: `.preserved/harvested/theme_bible_raw/documentary.md`
- FOUND: `.preserved/harvested/theme_bible_raw/humor.md`
- FOUND: `.preserved/harvested/theme_bible_raw/incidents.md`
- FOUND: `.preserved/harvested/theme_bible_raw/politics.md`
- FOUND: `.preserved/harvested/theme_bible_raw/trend.md`
- FOUND: `.preserved/harvested/theme_bible_raw/wildlife.md`
- FOUND: `scripts/harvest/audit_log.md`

**Commits verified in git log:**
- FOUND: `fba21e4` — feat(03-harvest-03): copy shorts_naberal channel_bibles/ to theme_bible_raw (HARVEST-01)

**Acceptance criteria:**
- [x] `.preserved/harvested/theme_bible_raw/` directory exists
- [x] 7 .md files present (README + documentary + humor + incidents + politics + trend + wildlife)
- [x] `diff_verifier.py theme_bible_raw` exits 0 (mismatches=[])
- [x] No `client_secret*.json` or `token_*.json` leakage in dest
- [x] shorts_naberal source untouched (verified via `git status` on source repo — empty)
- [x] Commit made with `--no-verify`

---

*Phase: 03-harvest*
*Plan: 03 (THEME-BIBLE-COPY)*
*Completed: 2026-04-19*
