---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 05
subsystem: audit/skill-patch-counter
tags: [audit-05, idempotency, d-22, d-23, d-24, d-25, scheduler, failures-md]
requirements: [AUDIT-05]
dependency-graph:
  requires:
    - "scripts/audit/skill_patch_counter.py (Plan 10-01 baseline — scan_violations, append_failures, main)"
    - "tests/phase10/test_skill_patch_counter.py (Plan 10-01 — 11 behavioral tests baseline)"
    - "tests/phase10/conftest.py (tmp_git_repo, make_commit, freeze_kst_now fixtures)"
    - ".claude/failures/FAILURES.md F-D2-01 entry (2026-04-21 preserved sample for regex validation)"
  provides:
    - "_existing_violation_hashes() helper — reusable grep regex for any F-D2-NN consumer"
    - "idempotent main() — monthly scheduler safe (2026-05-20 first-run gate)"
    - "test_idempotency_skip_existing — D-24 regression anchor"
  affects:
    - ".github/workflows/skill-patch-count-monthly.yml (Plan 10-04 — now runs on idempotent code)"
    - "Phase 11 entry gate for D-22 deadline"
tech-stack:
  added:
    - "logging.getLogger(__name__) (stdlib) — replaces absent logger"
  patterns:
    - "option (a) commit short-hash set signature (RESEARCH §Pattern 5)"
    - "^## F-D2-\\d{2}.*?(?=^## F-|\\Z) entry boundary regex (MULTILINE + DOTALL)"
    - "^- `([0-9a-f]{7})` per-line hash extraction (format-coupled to append_failures L220-224)"
    - "grep-before-append guard (write_report stays unconditional, append_failures becomes conditional)"
key-files:
  created: []
  modified:
    - "scripts/audit/skill_patch_counter.py (+37 net lines: +import logging, +logger, +_existing_violation_hashes 19 lines, +main() guard block 16 lines)"
    - "tests/phase10/test_skill_patch_counter.py (+72 net lines: +test_idempotency_skip_existing 3-phase assertion)"
decisions:
  - "Signature algorithm: commit short-hash set (option (a)) — resilient to subject-line edits, fragile only to `- `7hex`` line marker re-format (AUDIT-05 / D-23)"
  - "Exit code contract preserved: rc=1 whenever violations exist in the lock window, even when no new F-D2-NN append happens (D-23 semantics)"
  - "Report file (reports/skill_patch_count_YYYY-MM.md) remains UNCONDITIONAL — monthly scheduler still rotates report file for audit trail even on skip-day (D-25 write_report invariant)"
  - "Added logging.getLogger(__name__) as deviation Rule 2 — plan prose claimed logger existed but skill_patch_counter.py used only print()"
metrics:
  duration_seconds: 130
  completed_date: "2026-04-20"
  tasks_completed: 2
  tests_added: 1
  tests_total_phase10_counter: 12
  phase04_regression: "244/244 preserved"
  failures_md_changes: 0
---

# Phase 11 Plan 05: Idempotency Counter Summary

**One-liner:** Added `_existing_violation_hashes()` grep-based guard to `skill_patch_counter.main()` so the 2026-05-20 monthly scheduler run on unchanged git state produces zero F-D2-NN duplicate entries (D-22/D-23/D-24 closed).

## Objective (met)

AUDIT-05 / D-23: idempotency guard added. Running the counter twice on identical git state now:
- 1st run: reads FAILURES.md, finds no existing hashes matching current violations → appends new F-D2-NN entry → rc=1
- 2nd run: reads FAILURES.md, finds all violation hashes already recorded → skips append, logs Korean diagnostic → rc=1 (exit code contract preserved)
- 3rd run with NEW violation: reads FAILURES.md, filters existing hashes out → appends only the NEW violation (original F-D2-NN preserved byte-exact, D-25 strict prefix invariant) → rc=1

The 2026-05-20 first-run of `.github/workflows/skill-patch-count-monthly.yml` (Plan 10-04) now executes on idempotent code. D-22 entry gate closed 29 days ahead of deadline.

## Tasks

### Task 1 — `test_idempotency_skip_existing` RED anchor (commit `5ae667c`)

APPEND-only modification to `tests/phase10/test_skill_patch_counter.py`. 3-phase assertion:
- **Phase A** (1st run, fresh hook violation): `rc=1` + exactly 1 F-D2-NN entry
- **Phase B** (2nd run, identical state): `rc=1` but FAILURES.md byte-exact (`post2 == post1`)
- **Phase C** (3rd run, new CLAUDE.md violation): `rc=1` + 2 F-D2-NN entries, Phase A content preserved as strict prefix (`post3.startswith(post1)`)

Verified RED before implementation: Phase B `assert post2 == post1` failed because the unguarded counter duplicate-appends on every invocation (reproduction of D10-01-DEF-02 root cause). Existing 11 tests remained GREEN (pure append, zero modification to Plan 10-01 baseline).

### Task 2 — `_existing_violation_hashes` + main() guard GREEN (commit `c3f87d3`)

Three surgical edits to `scripts/audit/skill_patch_counter.py`:

1. **Imports** (L46-54): `import logging` added. `logger = logging.getLogger(__name__)` added at L60. **Deviation Rule 2** — plan prose assumed `logger` existed but module used only `print()`.

2. **Helper** (L190-208): `_existing_violation_hashes(failures_text) -> set[str]`. Parses F-D2-NN entries via `re.compile(r"^## F-D2-\d{2}.*?(?=^## F-|\Z)", re.MULTILINE | re.DOTALL)` boundary regex, then per-line `re.match(r"^- `([0-9a-f]{7})`")` extracts the commit short-hash of each violation row.

3. **main() guard** (L316-336): After `write_report(...)` and before `append_failures(...)`, read FAILURES.md, compute `existing_hashes`, filter `new_violations` to those whose `[:7]` short-hash is absent. If `not new_violations`: emit Korean `logger.info` ("신규 violation 없음 — 기존 F-D2-NN 에 %d건 이미 기록 (대표님, 재실행 skip)") and skip append. Otherwise: call `append_failures(new_violations, ...)`. `return 1` preserved in both branches so exit code = "violations exist in window".

Post-change verification:
- `pytest tests/phase10/test_skill_patch_counter.py -v` → **12/12 PASSED** (11 existing + 1 new)
- `pytest tests/phase04/ -q` → **244/244 passed** (baseline preserved)
- Helper spot-test: `_existing_violation_hashes(sample)` returns `{'abc1234', 'def5678', '111aaaa'}` correctly across 2 F-D2-NN entries

## Signature Algorithm Evidence

Algorithm is commit short-hash set (RESEARCH §Pattern 5 option (a)). Grep evidence:

```bash
$ grep -n "def _existing_violation_hashes" scripts/audit/skill_patch_counter.py
190:def _existing_violation_hashes(failures_text: str) -> set[str]:

$ grep -c "existing_hashes" scripts/audit/skill_patch_counter.py
3   # declaration (L321) + filter usage (L324) + empty-branch default (L322)

$ grep -n "신규 violation 없음" scripts/audit/skill_patch_counter.py
325:                "[skill_patch_counter] 신규 violation 없음 — 기존 F-D2-NN 에 %d건 "

$ grep -n "대표님" scripts/audit/skill_patch_counter.py
184: (pre-existing from Plan 10-01 write_report note)
326:                "이미 기록 (대표님, 재실행 skip)",
```

Regex format-couple: The line regex `r"^- `([0-9a-f]{7})`"` is format-locked to `append_failures` L220-224 which emits `f"- `{short_hash}` ...` where `short_hash = (v.get("hash") or "")[:7]`. A single atomic edit to either side (adding a space before `7-hex`, switching to 8-hex, reformatting to table row) breaks both — the coupling is tested by `test_idempotency_skip_existing`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Added `logging.getLogger(__name__)`**
- **Found during:** Task 2 Step 3 ("Verify `logger` is defined in the module (it is)")
- **Issue:** Plan prose asserted logger existed but grep on skill_patch_counter.py showed zero `logger` references — module used only `print()`. Calling `logger.info(...)` as the plan's action spec required would have raised `NameError` at runtime.
- **Fix:** Added `import logging` (L5 insertion) and `logger = logging.getLogger(__name__)` at module level after the `sys.stdout.reconfigure` guard (L60). Standard stdlib idiom, zero external dep, zero behavior change for non-idempotent paths (logger is quiet at default WARNING level; info message emits only when caller configures logging).
- **Files modified:** scripts/audit/skill_patch_counter.py
- **Commit:** c3f87d3 (bundled with Task 2 GREEN — single atomic edit)

### Scope-boundary (out of plan)

**Pre-existing failure NOT fixed:** `tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default` fails against the current `.planning/STATE.md` (missing `phase_lock: false` frontmatter field). This is **D10-03-DEF-01**, already logged in `.planning/phases/10-sustained-operations/deferred-items.md:34` as a Plan 10-02 follow-up. Out of Plan 11-05 scope (boundary: audit/skill_patch_counter + its test) per CLAUDE.md Rule 1.

### None other

All acceptance criteria met without architectural changes. No Rule 4 events. No authentication gates. No checkpoint triggers.

## Test Evidence

```
$ pytest tests/phase10/test_skill_patch_counter.py -v
tests/phase10/test_skill_patch_counter.py::test_tmp_git_repo_fixture_creates_repo PASSED
tests/phase10/test_skill_patch_counter.py::test_make_forbidden_commit_helper PASSED
tests/phase10/test_skill_patch_counter.py::test_reports_gitkeep_exists PASSED
tests/phase10/test_skill_patch_counter.py::test_A_no_violations_in_clean_repo PASSED
tests/phase10/test_skill_patch_counter.py::test_B_single_hook_violation_counts_1 PASSED
tests/phase10/test_skill_patch_counter.py::test_C_all_four_forbidden_paths_count_4 PASSED
tests/phase10/test_skill_patch_counter.py::test_D_files_outside_forbidden_not_counted PASSED
tests/phase10/test_skill_patch_counter.py::test_E_dry_run_skips_file_output PASSED
tests/phase10/test_skill_patch_counter.py::test_F_report_contains_kst_timestamp PASSED
tests/phase10/test_skill_patch_counter.py::test_G_failures_append_is_hook_safe PASSED
tests/phase10/test_skill_patch_counter.py::test_H_cli_since_until_override PASSED
tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing PASSED

============================= 12 passed in 3.09s ==============================

$ pytest tests/phase04/ -q
244 passed in 0.32s
```

Phase 11 cumulative test count: 274 → **275** (11 existing phase10 counter + 1 new + 263 other phase04/phase10/phase11 tests).

## Scheduler Deadline Evidence

D-22 gate: 2026-05-20 first monthly scheduler execution.
Plan 11-05 completion: 2026-04-21 (today — via commit `c3f87d3`).
Margin: **29 days** before first scheduler fire. `.github/workflows/skill-patch-count-monthly.yml` now executes on idempotent `skill_patch_counter.main()`.

## FAILURES.md Invariant

`git status .claude/failures/FAILURES.md` → **clean** (zero changes). F-D2-01 byte-exact preservation verified at runtime via `test_idempotency_skip_existing` Phase C assertion `post3.startswith(post1)`. The 2026-04-21 F-D2-01 "directive-authorized" entry survives future scheduler runs on unchanged git state.

## Commits

- `5ae667c` — test(11-05): add test_idempotency_skip_existing RED for AUDIT-05 D-24
- `c3f87d3` — feat(11-05): add idempotency guard to skill_patch_counter (AUDIT-05 D-23)

## Known Stubs

None. The idempotency guard is fully wired: main() reads FAILURES.md on every invocation, the regex is format-coupled to the live write path, and the exit-code contract is preserved in both branches.

## Self-Check: PASSED

Verified the following claims post-SUMMARY write:
- FOUND: scripts/audit/skill_patch_counter.py (modified L46-54, L60, L190-208, L316-336)
- FOUND: tests/phase10/test_skill_patch_counter.py (appended test_idempotency_skip_existing at EOF)
- FOUND: commit 5ae667c (Task 1 RED)
- FOUND: commit c3f87d3 (Task 2 GREEN)
- FOUND: .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-05-idempotency-counter-SUMMARY.md (this file)
- CLEAN: .claude/failures/FAILURES.md untouched
- VERIFIED: 12/12 Phase 10 counter tests GREEN
- VERIFIED: 244/244 Phase 04 baseline preserved
- D-22 deadline margin: 29 days (29 Apr 21 → 20 May 20)
