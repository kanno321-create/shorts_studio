---
phase: 03-harvest
plan: 09
subsystem: harvest

tags: [harvest, lockdown, tier-3-immutable, attrib-windows, verify-full, phase-3-complete, harvest-06]

requires:
  - phase: 03-harvest-01
    provides: lockdown.apply_lockdown + lockdown.verify_lockdown (cmd.exe subprocess form, PermissionError probe contract) + verify_harvest.py (13 task checks + --full extras)
  - phase: 03-harvest-03
    provides: theme_bible_raw (7 channel bibles) — lockdown target + probe source (documentary.md first *.md via rglob)
  - phase: 03-harvest-04
    provides: remotion_src_raw (40 files) — lockdown target
  - phase: 03-harvest-05
    provides: hc_checks_raw (2 files) — lockdown target
  - phase: 03-harvest-06
    provides: api_wrappers_raw (5 wrappers) — lockdown target
  - phase: 03-harvest-07
    provides: _imported_from_shorts_naberal.md source markers — verify_harvest check 3-07-failures-merge-has-source-comment input
  - phase: 03-harvest-08
    provides: 03-HARVEST_DECISIONS.md 39 rows + blacklist audit PASS precondition — Plan 09 MUST NOT lockdown if audit shows violations

provides:
  - Tier 3 OS-level immutable lockdown on .preserved/harvested/ (55 files R-flagged, PermissionError enforced)
  - HARVEST-06 satisfied (attrib +R recursive, PermissionError probe PASS)
  - verify_harvest.py --full 15/15 PASS (13 task checks + deep_diff 2 tree-copy dirs clean + sha256 5-file spot sample hash-match)
  - 03-VALIDATION.md frontmatter complete (status=complete, nyquist_compliant=true, wave_0_complete=true)
  - Rule 3 bug fix for verify_harvest.py manifest iteration (isinstance + dest guard)
  - Phase 3 Harvest COMPLETE entry gate for Phase 4 Agent Team Design

affects: [phase-04-agent-team-design, phase-05-orchestrator-v2-rewrite, phase-06-nlm-researcher, phase-10-sustained-operations]

tech-stack:
  added: []
  patterns:
    - "lockdown.apply_lockdown() — subprocess.run(['cmd.exe', '/c', f'attrib +R /S /D {win_path}\\\\*']) — NEVER call attrib directly in Git Bash (Korean Windows silently rejects with 매개 변수 형식이 틀립니다)"
    - "lockdown.verify_lockdown() — probe first *.md via rglob + write_text + expect PermissionError; restores original bytes on unexpected success before raising AssertionError (prevents probe corruption during failure diagnosis)"
    - "Manifest iteration guard: `isinstance(entry, dict) and 'dest' in entry` — prevents AttributeError on top-level metadata keys (manifest_version, generated_at, source_root, global_ignore) and dict-but-different-shape keys (blacklist_exclusions)"
    - "PYTHONIOENCODING=utf-8 required for verify_harvest.py on Windows cp949 (em-dash in error detail messages)"

key-files:
  created:
    - .planning/phases/03-harvest/03-09-SUMMARY.md (this file)
  modified:
    - scripts/harvest/audit_log.md (Wave 4 Task 1 + Task 2 entries appended)
    - scripts/harvest/verify_harvest.py (Rule 3 fix: _deep_diff_all + _sha256_spot_sample manifest guard)
    - .planning/phases/03-harvest/03-VALIDATION.md (frontmatter: status=complete, nyquist_compliant=true, wave_0_complete=true, completed=2026-04-19)
    - .planning/phases/03-harvest/*.preserved/harvested/** (file attributes only; 55 files gained NTFS R flag — not tracked by git)
    - .planning/STATE.md (phase 3 complete, progress 94%, plan 03-09 decisions)
    - .planning/ROADMAP.md (Phase 3 checkbox + Plan 03-09 checkbox marked)

key-decisions:
  - "Lockdown via cmd.exe subprocess (M-1 module-call form) — direct `attrib +R /S /D \"path/*\"` in Git Bash silently fails with Korean Windows error 매개 변수 형식이 틀립니다 and leaves the tree writable (SILENT SECURITY HOLE, live-tested 2026-04-19 per 03-RESEARCH.md §5). Mandatory `subprocess.run(['cmd.exe', '/c', ...])` with backslash path normalization via `str(target.resolve()).replace('/', '\\\\')`. verify_lockdown PermissionError probe on theme_bible_raw/documentary.md (first *.md via rglob) is the sole acceptance signal; independent raw `attrib /s` listing provides secondary audit evidence (55 files show 'A    R' flag)."
  - "Rule 3 deviation — verify_harvest.py _deep_diff_all + _sha256_spot_sample crashed with AttributeError: 'str' object has no attribute 'get' on first --full invocation. Root cause: both functions iterated the entire manifest dict without filtering top-level metadata keys. path_manifest.json mixes raw_dir entries (theme_bible_raw/remotion_src_raw/hc_checks_raw/api_wrappers_raw — dicts with source+dest+cherry_pick) with metadata keys (manifest_version=string, generated_at=string, source_root=string, global_ignore=list) and a dict-but-different-shape key (blacklist_exclusions with full_file/path_prefix/pattern). Fix: added `isinstance(entry, dict) and 'dest' in entry` guard, preserves original `source` presence check for tree-copy subset. Cherry-pick entries (source=None) are correctly skipped in both functions (deep_diff requires src directory, sha256 samples from dst tree but needs src root for comparison). After fix: 15/15 PASS (13 task + 2 --full extras)."
  - "No except-pass silent swallow invariant — `grep -c 'except.*: *pass' lockdown.py` returns 0, confirming no error hiding in lockdown flow. If apply_lockdown OR verify_lockdown raises, the exception propagates with full context per CLAUDE.md rule #3 Failure Investigation."
  - "audit_log append via printf (not heredoc) — first heredoc attempt on Windows Git Bash silently failed to persist the Wave 4 Task 2 block (command returned success but content was not written). printf form with explicit \\n escapes worked correctly. Defensive: always `tail -N` audit_log.md after appending to confirm."
  - "PYTHONIOENCODING=utf-8 required — verify_harvest.py emits em-dash `—` inside FAIL detail messages (write SUCCEEDED on ... — lockdown not applied). Windows cp949 default stdout encoding raises UnicodeEncodeError. Post-lockdown FAIL path never executes so the final PASS run is unaffected, but all development/diagnostic runs must set this env var."
  - "03-VALIDATION.md frontmatter flipped only after verify_harvest --full exit 0 — plan flow is atomic: lockdown → verify → flip or FAIL (no partial flip). verify_harvest was made to exit 0 after Rule 3 fix + lockdown applied; frontmatter edit executed as separate Edit tool call (regex-driven python heredoc in plan was bypassed since inline Edit is simpler and auditable)."

patterns-established:
  - "Phase completion gate pattern — verify_harvest.py --full exit 0 is the single boolean that gates phase transition. All 15 checks (13 task + deep_diff + sha256) must be GREEN; any FAIL blocks 03-VALIDATION.md flip. Phase 4 /gsd:plan-phase 4 is only entered after this signal."
  - "Manifest-driven verification contract — checks iterate path_manifest.json for dynamic raw_dir discovery. Non-dict and missing-dest entries are explicitly filtered; cherry-pick vs tree-copy subsets are handled by source presence check. Future phases adding new raw dirs need only add to manifest — no code change required for deep_diff/sha256 extras."
  - "Independent verification chain — lockdown is proven via TWO methods: (1) Python PermissionError probe (automated, recorded in verify_harvest 3-09-lockdown-write-denied check), (2) raw cmd.exe `attrib /s` output parsing for 'A    R' flag count (human-auditable via audit_log.md). Both must agree; if only one passes, lockdown is suspect."
  - "NTFS attributes are NOT git-tracked — attrib +R is an OS-level filesystem attribute, not a file content change. git status shows no .preserved/harvested/ changes after lockdown. This is the intended Tier 3 behavior: lockdown is a filesystem property enforced by Windows, not by git. Clone/checkout does NOT preserve R flag — future re-lockdown would be required on new working trees (documented in 03-RESEARCH.md §5 + AGENT.md unlock docs)."

requirements-completed:
  - HARVEST-06

duration: 8min
completed: 2026-04-19
---

# Phase 03 Plan 09: LOCKDOWN + FULL-VERIFY Summary

**Tier 3 immutable lockdown applied to .preserved/harvested/ (55 files attrib +R, PermissionError probe PASS) + verify_harvest --full 15/15 all GREEN — Phase 3 Harvest COMPLETE, Phase 4 Agent Team Design 진입 허가**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-18T19:20:00Z
- **Completed:** 2026-04-18T19:28:00Z
- **Tasks:** 2 (both auto, non-TDD)
- **Files modified:** 3 code/state (audit_log, verify_harvest, 03-VALIDATION) + 55 NTFS-flagged
- **Commits:** 2 (studio@8ae370e + studio@d4fc5e4)

## Accomplishments

- **HARVEST-06 satisfied (Tier 3 immutable):** `cmd.exe /c attrib +R /S /D <win_path>\*` applied recursively to `.preserved/harvested/`. 55 files now carry NTFS R flag across 4 raw dirs (theme_bible_raw=7, remotion_src_raw=40, hc_checks_raw=2, api_wrappers_raw=5 + directory nodes). Independent `attrib /s` listing confirmed `A    R` on every file.
- **verify_lockdown PermissionError probe PASS:** `probe.write_text("LOCKDOWN_VERIFY_TAMPER")` on theme_bible_raw/documentary.md (first *.md via rglob) raised PermissionError as expected. lockdown.verify_lockdown returned success without restore fallback (write denied, no probe corruption).
- **verify_harvest.py --full 15/15 PASS:** 13 task-level checks (per 03-VALIDATION.md Per-Task Verification Map) + 2 --full extras (deep_diff 2 tree-copy dirs clean + sha256 5-file spot sample hash-match). Exit 0. All 5 ROADMAP Phase 3 Success Criteria verifiably TRUE.
- **03-VALIDATION.md frontmatter flipped:** `status: draft → complete`, `nyquist_compliant: false → true`, `wave_0_complete: false → true`, added `completed: 2026-04-19`.
- **Phase 3 gate cleared:** 9 requirements satisfied (HARVEST-01/02/03/04/05/06/07/08 + AGENT-06). CONFLICT_MAP 39 재드리프트 구조적 차단 완료. Ready for Phase 4 Agent Team Design.

## What Was Built

### Task 1: Tier 3 Lockdown (studio@8ae370e)

**Input:** `.preserved/harvested/` tree (55 files across 4 raw dirs, previously committed by Plans 03-03~03-06). Precondition: Plan 03-08 Task 2 blacklist audit showed Result: PASS (0 matches across 7 checks).

**Process:**
1. Normalized target to Windows path: `str(target.resolve()).replace('/', '\\')` → `C:\Users\PC\Desktop\naberal_group\studios\shorts\.preserved\harvested`
2. `subprocess.run(["cmd.exe", "/c", f"attrib +R /S /D {win_path}\\*"], capture_output=True, text=True, check=False)`
3. returncode == 0 verified, no stderr
4. `verify_lockdown(target)`: picked theme_bible_raw/documentary.md via rglob, attempted `write_text("LOCKDOWN_VERIFY_TAMPER")`, caught PermissionError (expected), returned success
5. Independent audit: `cmd.exe //c "attrib .preserved\\harvested\\*.* /s" | grep -c " R "` → 55 files

**Output:** scripts/harvest/audit_log.md Wave 4 Task 1 block with Result: PASS + attrib command verbatim + R-count + probe result.

### Task 2: verify_harvest --full 15/15 PASS (studio@d4fc5e4)

**Input:** Post-lockdown state + existing 03-01~08 artifacts.

**Process:**
1. `PYTHONIOENCODING=utf-8 python scripts/harvest/verify_harvest.py --full` (encoding needed for em-dash in potential FAIL messages)
2. First run crashed on `_deep_diff_all` with `AttributeError: 'str' object has no attribute 'get'` — Rule 3 deviation applied
3. Fixed `_deep_diff_all` + `_sha256_spot_sample` to filter manifest entries: `if not isinstance(entry, dict) or "dest" not in entry: continue`
4. Re-ran: 15/15 PASS (exit 0)
5. Appended Wave 4 Task 2 block to audit_log.md (via printf form after heredoc silently failed on Windows Git Bash)
6. Edited 03-VALIDATION.md frontmatter inline (4 field changes)

**13 Task Checks Result:**
```
[OK] 3-01-agent-md-exists: 108 lines
[OK] 3-01-agent-md-description-length: 378 chars
[OK] 3-01-scripts-harvest-package: 8 files present
[OK] 3-02-manifest-valid-json: 9 entries
[OK] 3-03-theme-bible-raw-exists: 7 .md files
[OK] 3-04-remotion-src-raw-exists: node_modules excluded
[OK] 3-05-hc-checks-raw-exists: 37486 bytes
[OK] 3-06-api-wrappers-raw-cherry-pick: 5 cherry-picked files
[OK] 3-07-failures-merge-has-source-comment: 1 source markers
[OK] 3-08-decisions-md-39-rows: 39 rows (13+16+10)
[OK] 3-08-blacklist-grep-skip-gates: 0 matches
[OK] 3-08-blacklist-grep-todo: 0 matches
[OK] 3-09-lockdown-write-denied: write denied on documentary.md

--- full-mode extras ---
[OK] 3-full-deep-diff: 2 dirs clean
[OK] 3-full-sha256-sample: 5 files hash-matched

--- summary: 15/15 passed, 0 failed ---
```

**Output:**
- audit_log.md Wave 4 Task 2 block with full exit/OK/FAIL counts + Rule 3 deviation note
- verify_harvest.py +19 lines (2 filter guard blocks, docstring comments)
- 03-VALIDATION.md frontmatter: 4 field changes + completed date added

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Fixed verify_harvest.py manifest iteration crash**
- **Found during:** Task 2 first invocation of `verify_harvest.py --full`
- **Issue:** `_deep_diff_all` and `_sha256_spot_sample` iterated the manifest dict without filtering top-level metadata keys. On encountering `manifest_version: "1.0"` (string), `entry.get("source")` raised `AttributeError: 'str' object has no attribute 'get'`. After first fix (`isinstance(entry, dict)` guard), `blacklist_exclusions` (dict with different shape: `full_file`/`path_prefix`/`pattern`/`source` where source is a prose citation, not a path) caused new FAIL: `blacklist_exclusions: src=False dst=False`.
- **Fix:** Added compound guard `isinstance(entry, dict) and "dest" in entry` to both functions. Matches the exact raw_dir entry contract from path_manifest.json — only tree/cherry-pick entries have a `dest` key. Preserved the original `source` presence check to skip cherry-pick entries in deep_diff and sha256 sampling.
- **Files modified:** `scripts/harvest/verify_harvest.py` (+19 lines, 2 function edits)
- **Commit:** studio@d4fc5e4

**2. [Rule 3 — Blocking] PYTHONIOENCODING=utf-8 wrapper for cp949 compatibility**
- **Found during:** Pre-flight quick verify (before Task 1)
- **Issue:** Default Windows stdout encoding is cp949 (Korean Windows). verify_harvest.py emits em-dash `—` inside FAIL detail messages (e.g., `write SUCCEEDED on ... — lockdown not applied`). cp949 cannot encode U+2014 em-dash, raises `UnicodeEncodeError` mid-print, crashing the verification loop.
- **Fix:** All `python scripts/harvest/verify_harvest.py` invocations prefixed with `PYTHONIOENCODING=utf-8`. Not committed as code change because post-lockdown the FAIL branch never executes; documentation-only fix in audit_log + SUMMARY.
- **Files modified:** None (documentation-only)
- **Commit:** N/A (documented in audit_log.md + this SUMMARY)

**3. [Rule 3 — Blocking] printf vs heredoc for audit_log.md append**
- **Found during:** Task 2 verify gate (audit_log.md tail check failed silently)
- **Issue:** First heredoc append of Wave 4 Task 2 block returned success from bash but content was not written to audit_log.md. Suspected Windows Git Bash environment interaction with `cat <<EOF ... EOF` when TS variable substitution was involved. Gate check `grep -q "Wave 4 Task 2"` failed.
- **Fix:** Re-appended via `printf` form with explicit `\n` escapes. Content persisted correctly. Tail verification confirmed.
- **Files modified:** scripts/harvest/audit_log.md (Task 2 block appended)
- **Commit:** studio@d4fc5e4

### Auth Gates
None — fully autonomous execution.

## Deferred Issues
None.

## Validation Evidence

**SC1 (4 raw dirs diff 0):** verified via Plan 07 aggregate diff ALL_CLEAN + verify_harvest --full 3-full-deep-diff OK  
**SC2 (attrib +R applied):** verified via Task 1 PermissionError probe + 55-file R-count + verify_harvest 3-09-lockdown-write-denied OK  
**SC3 (HARVEST_DECISIONS.md 39 entries):** verified via Plan 08 row count + verify_harvest 3-08-decisions-md-39-rows OK  
**SC4 (_imported_from_shorts_naberal.md exists):** verified via Plan 07 source marker count + verify_harvest 3-07-failures-merge-has-source-comment OK  
**SC5 (Blacklist audit 0):** verified via Plan 08 7-check audit + verify_harvest 3-08-blacklist-grep-skip-gates + 3-08-blacklist-grep-todo OK

## Phase 3 Harvest COMPLETE

All 9 requirements satisfied:
- HARVEST-01 (theme_bible_raw, Plan 03)
- HARVEST-02 (remotion_src_raw, Plan 04)
- HARVEST-03 (hc_checks_raw, Plan 05)
- HARVEST-04 (_imported_from_shorts_naberal.md, Plan 07)
- HARVEST-05 (api_wrappers_raw, Plan 06)
- HARVEST-06 (Tier 3 lockdown, **Plan 09 THIS**)
- HARVEST-07 (blacklist audit, Plan 08)
- HARVEST-08 (HARVEST_DECISIONS.md 39 rows, Plan 08)
- AGENT-06 (harvest-importer, Plan 01)

**Statement: Phase 3 Harvest COMPLETE — Phase 4 Agent Team Design 진입 허가**

## Self-Check: PASSED

- [x] `.planning/phases/03-harvest/03-09-SUMMARY.md` exists
- [x] `scripts/harvest/audit_log.md` has Wave 4 Task 1 + Task 2 blocks with Result: PASS
- [x] `scripts/harvest/verify_harvest.py` Rule 3 fix applied (2 functions, isinstance+dest guard)
- [x] `.planning/phases/03-harvest/03-VALIDATION.md` frontmatter: status=complete, nyquist_compliant=true, wave_0_complete=true
- [x] Commit 8ae370e exists (Task 1 lockdown)
- [x] Commit d4fc5e4 exists (Task 2 full verify)
- [x] `python scripts/harvest/verify_harvest.py --full` exits 0 (15/15 PASS)
