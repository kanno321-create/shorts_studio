---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 08
subsystem: wave-4-failures-reservoir-hook-discipline
tags: [hook-extension, d-11, d-12, d-14, fail-01, fail-03, pre-tool-use, append-only, skill-backup, phase05-regression]

# Dependency graph
requires:
  - phase: 06
    plan: 01
    provides: tests/phase06/__init__.py + conftest.py fixtures (repo_root, fixtures_dir, failures_sample_text)
  - phase: 05
    provides: .claude/hooks/pre_tool_use.py (152-line Phase 5 Plan 01 baseline — load_patterns/find_studio_root/check_content/check_structure_allowed/main); .claude/deprecated_patterns.json (6 regex entries — skip_gates, TODO(next-session), T2V family, segments[], selenium, try/pass silent fallback); scripts/validate/verify_hook_blocks.py 5-case subprocess validator
  - phase: 03
    provides: .claude/failures/_imported_from_shorts_naberal.md (500-line Phase 3 import, sha256-locked — D-14 baseline that Plan 08 must NOT modify)
  - plan: 06-CONTEXT.md D-11/D-12/D-14 + 06-RESEARCH.md §Area 6 lines 799-861 (regex limitations + false-positive matrix) + §Area 7 lines 863-921 (backup pattern + restoration UX)
provides:
  - .claude/hooks/pre_tool_use.py (152 → 272 lines, +120. Added 2 imports [datetime, shutil], 2 helper functions [check_failures_append_only 41 lines, backup_skill_before_write 30 lines], 2 integration blocks in main() BEFORE studio_root/regex scan so checks are studio-agnostic.)
  - .claude/deprecated_patterns.json (6 → 8 entries. Added FAIL-01 [REMOVED]/[DELETED] marker + FAIL-03 SKILL.md annotation. Content-scan regex serves as audit trail; real enforcement lives in the Python helpers.)
  - .claude/failures/FAILURES.md (NEW, 24 lines, append-only destination seeded with entry schema — Tier, 발생 세션, 재발 횟수, Trigger, 무엇, 왜, 정답, 검증, 상태, 관련 — 10 fields).
  - .claude/failures/FAILURES_INDEX.md (NEW, 36 lines, category-tagging index — Planning/Structure, Content Quality, Audio/Publishing, Research/Fact-check, Phase 6+. References _imported entries by fail-ID without modifying that file.)
  - SKILL_HISTORY/README.md (NEW, 42 lines, backup convention + restore flow + first-time skip + never-modify directive).
  - scripts/failures/.gitkeep (NEW, empty placeholder — Plan 09 will populate with aggregate_patterns.py).
  - tests/phase06/test_failures_append_only.py (NEW, 194 lines, 14 in-process unit tests — Edit/Write/MultiEdit decision matrix + Windows path + imported-file exemption + basename false-positive guard).
  - tests/phase06/test_hook_failures_block.py (NEW, 131 lines, 7 subprocess integration tests — stdin JSON payload, deny reason shape, Phase 5 skip_gates regression, D-14 imported file pass-through).
  - tests/phase06/test_skill_history_backup.py (NEW, 162 lines, 9 unit tests — v<YYYYMMDD_HHMMSS>.md.bak format, byte-identical Korean preservation, multi-backup timestamp uniqueness).
affects:
  - Plan 06-09 (aggregate_patterns.py will read both FAILURES.md and _imported_*.md + write to SKILL.md.candidate — this plan seeds both append-only source + index tooling expects).
  - Plan 06-11 (D-14 sha256 invariant test for _imported_*.md; this plan's check_failures_append_only explicitly excludes that file by basename check, keeping responsibility separated).
  - Phase 5 Plan 01 hook tests (5 test files, 31 tests) — regression green; 8-pattern deprecated_patterns.json + new studio-agnostic FAILURES/SKILL checks do not disturb existing deny/allow decisions.
  - All future SKILL.md edits anywhere under the studio will auto-trigger backup_skill_before_write pre-side-effect (Phase 10 FAIL-04 freeze → this is the recoverability hinge).

# Tech tracking
tech-stack:
  added: []  # stdlib-only: datetime, shutil, pathlib; no new runtime deps
  patterns:
    - "Studio-agnostic Hook checks ordering: FAILURES append-only and SKILL backup are wired BEFORE `find_studio_root` in main() — these checks fire regardless of whether the tool-use target is inside a studio. Reason: FAILURES.md lives at `.claude/failures/FAILURES.md` (one level above studio scripts/), and SKILL_HISTORY backup must succeed even if the Hook is invoked from a non-studio cwd. The existing deprecated_patterns scan remains inside the studio-scoped branch (pattern file is per-studio)."
    - "Basename-exact match over substring: check_failures_append_only uses `name != 'FAILURES.md'` instead of `endswith('FAILURES.md')` to guard against FAILURES.md.bak, FAILURES_INDEX.md, and mySKILL.md-style false positives. Path-separator normalization (`fp.replace('\\', '/')`) before rsplit keeps it Windows-safe. Covered by test_non_basename_match_with_substring_allowed."
    - "Whitespace-stripped old_string semantics: `old.strip()` treats whitespace-only old_string as empty (= pure insertion). This avoids blocking legitimate empty-line repositioning edits while still denying any semantic modification. Covered by test_edit_whitespace_only_old_string_allowed + test_edit_empty_old_string_allowed."
    - "Strict-prefix Write contract for append-only: `not new.startswith(existing)` — byte-exact match required. Any modification of existing content (whitespace normalization, line reordering, entry deletion) fails this check. Weaker semantic-append semantics were considered and rejected: if a future workflow needs semantic-aware append, the test-assertion chain would silently drift. Exact-prefix is checkable, auditable, and matches D-11's intent."
    - "backup_skill_before_write as side-effect-only (return None): no payload/decision mutation. The pre-tool-use hook's decision remains independent of backup. Success = silent copy; OSError is the only failure mode and that's converted to deny at main() boundary. This keeps the helper trivially composable with any future decoration (e.g. Plan 09 dry-run could wrap it to log without copying)."
    - "datetime timestamp collision avoidance: v<YYYYMMDD_HHMMSS>.md.bak format means max-resolution-1-sec per skill. test_multiple_backups_same_skill_accumulate sleeps 1.1s between backups to prove accumulation. Phase 10 mass-patch scenarios requiring sub-second uniqueness would need to escalate to microseconds (%f), but current D-12 spec locks seconds — intentional lossy compression for human-readable filenames."
    - "Studio-agnostic relative path for SKILL_HISTORY: `Path('SKILL_HISTORY')` resolves against cwd, mirroring Claude Code's behavior of setting cwd to the studio root at tool-invocation time. Tests use monkeypatch.chdir(tmp_path) to isolate; production use gets `{studio_root}/SKILL_HISTORY/` naturally."
    - "Content-scan regex as audit annotation, not enforcement: the two new deprecated_patterns entries (`[REMOVED]|[DELETED]` + `SKILL\\.md`) are deliberately broad. They will produce some false positives (any doc mentioning SKILL.md triggers the pattern). This is accepted because (a) the Python checks are the real safety net, (b) the regex trail makes 'why was this denied' searchable in git-grep, (c) the broad SKILL.md match prompts authors to think about backup policy every time they touch SKILL references. The deprecated_patterns scan is only triggered inside a studio root (find_studio_root branch), so docs/tests outside studios are unaffected."

key-files:
  created:
    - .claude/failures/FAILURES.md (24 lines — append-only entry schema + D-11/D-14/D-2 invariants)
    - .claude/failures/FAILURES_INDEX.md (36 lines — category index referencing _imported entries by fail-ID)
    - SKILL_HISTORY/README.md (42 lines — backup convention + restore instructions + machine-managed directive)
    - scripts/failures/.gitkeep (Plan 09 placeholder)
    - tests/phase06/test_failures_append_only.py (194 lines, 14 tests — FAIL-01 D-11 unit)
    - tests/phase06/test_hook_failures_block.py (131 lines, 7 tests — FAIL-01 D-11 subprocess integration)
    - tests/phase06/test_skill_history_backup.py (162 lines, 9 tests — FAIL-03 D-12 unit)
  modified:
    - .claude/hooks/pre_tool_use.py (152 → 272 lines, +120. Zero existing-line deletions. Imports: +datetime, +shutil. New functions: check_failures_append_only, backup_skill_before_write. main() integration: 2 new blocks before studio_root branch.)
    - .claude/deprecated_patterns.json (6 → 8 entries, +2. FAILURES [REMOVED] marker + SKILL.md edit annotation. Regex validation: all 8 compile via re.compile().)
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (rows 6-08-01 + 6-08-02 + 6-08-03 flipped from "❌ W0 / ⬜ pending" to "✅ on disk / ✅ green").

key-decisions:
  - "Studio-agnostic placement of FAILURES + SKILL checks: wired BEFORE find_studio_root() in main(). Alternative was placing them inside the studio-scoped branch (after studio_root = find_studio_root(...)), but that would mean FAILURES.md edits from a non-studio cwd would bypass the check. Chose upfront placement because (a) FAILURES.md is path-identified by basename not studio membership, (b) SKILL_HISTORY backup must succeed regardless of cwd context, (c) existing deprecated_patterns scan stays studio-scoped (pattern file is per-studio). The 2-block separation in main() mirrors the Layer 1 / Layer 2 split in the original hook design."
  - "SKILL.md regex pattern kept broad despite false-positive risk: the plan specified `SKILL\\.md` — a pure content scan that triggers on any Write/Edit mentioning SKILL.md as a string. Considered narrowing to `(?<=['\"])SKILL\\.md(?=['\"])` (string-literal only) or matching only at file-path-like positions. Kept broad per plan because: (1) Python check backup_skill_before_write is the real enforcement — regex only adds audit-trail value, (2) false positives block edits to docs mentioning SKILL.md, which is acceptable since author should consider D-12 backup policy anyway, (3) narrow regex would create a feature-regex-to-implementation coupling (if enforcement moves, narrow regex breaks silently). Documenting in the reason string that 'the real check is in backup_skill_before_write Python helper' makes the two-layer contract explicit."
  - "Basename-exact match over endswith for FAILURES.md: chose `name != 'FAILURES.md'` because `endswith('FAILURES.md')` false-positives on FAILURES.md.bak and FAILURES_INDEX.md. The test_non_basename_match_with_substring_allowed regression guard pins this. Windows path separator handled by `fp.replace('\\\\', '/').rsplit('/', 1)[-1]` — a single normalization step that doesn't depend on Path().name which behaves differently on Windows vs POSIX."
  - "OSError → deny contract for backup failures: backup_skill_before_write propagates OSError (disk full, permission denied); main() catches and converts to `{decision: deny, reason: 'SKILL_HISTORY backup failed (D-12): ...'}`. Alternative was silent fallback (allow the write, log warning). Chose deny because D-12 states 'SKILL 수정 직전 기존 버전을 SKILL_HISTORY/...로 복사' — if backup fails, the D-12 contract is broken and proceeding with the edit would lose recoverability. Fail-loud > fail-silent for recovery invariants."
  - "Separation of FAILURES.md append-only check from _imported_from_shorts_naberal.md immutability check: Plan 11 owns D-14 sha256 verification for the imported file. Plan 08 explicitly excludes _imported_*.md from check_failures_append_only by basename. Rationale: (a) the imported file is immutable, not append-only — different contract, different test, (b) D-14 deserves its own sha256 verifier (Plan 11) rather than being conflated with the append-only logic, (c) test_imported_file_exempt_from_append_only locks this separation so a future refactor doesn't accidentally collapse the two checks. Two invariants, two tests, two plans."
  - "14 + 7 + 9 = 30 tests instead of minimum 10 + 5 + 7 = 22: went above plan's ≥ thresholds because the decision matrix has more edge cases than Phase 5 regex-only patterns. Key additions beyond the plan's explicit test list: (a) test_edit_whitespace_only_old_string_allowed [semantic-empty old_string], (b) test_multiedit_mixed_denied [short-circuit on first non-empty], (c) test_windows_path_separator_recognized [separator agnostic], (d) test_non_basename_match_with_substring_allowed [FAILURES_INDEX.md + .bak guard], (e) test_backup_skipped_for_skill_md_sibling_basenames [SKILLS.md etc. not matched], (f) test_multiple_backups_same_skill_accumulate [timestamp collision prevention], (g) test_hook_write_append_to_failures_allowed [positive-control for subprocess path]. Each locks a specific edge case from RESEARCH §Area 6 false-positive matrix."

patterns-established:
  - "Pattern: Pre-tool-use Hook with two-phase check (decision + side-effect). check_failures_append_only returns deny reason or None (pure decision). backup_skill_before_write performs side effect and raises on failure (converted to deny by caller). This split keeps testability high — the decision function can be unit-tested without filesystem, and the side-effect function can be tested with tmp_path + monkeypatch.chdir. Future hook helpers should follow the same contract: pure deciders return str|None; side-effect helpers return None and raise OSError-subclass on failure."
  - "Pattern: Append-only enforcement via strict-prefix Write check + Edit old_string ban. For any file where 'never modify existing content' is a hard contract: (a) deny Edit with non-empty old_string, (b) deny Write whose content does NOT start with existing file bytes, (c) allow Write when file doesn't exist (first create). This trio is the minimum set for append-only semantics. Future reservoirs (KPI log, decision journal, etc.) can copy check_failures_append_only's logic verbatim by changing only the basename match."
  - "Pattern: Pre-write backup with timestamped filename for recoverability. SKILL_HISTORY/<name>/v<YYYYMMDD_HHMMSS>.md.bak. Applied to SKILL.md but generalizable: any file that gets patched and whose history matters (STRUCTURE.md, ROADMAP.md, deprecated_patterns.json, etc.). Future hooks needing recoverability can clone backup_skill_before_write by changing basename filter + history root path. test_multiple_backups_same_skill_accumulate + test_backup_content_is_byte_identical_korean show the contract for free."
  - "Pattern: Hook checks ordered from studio-agnostic to studio-specific. main() now runs: parse payload → tool_name gate → FAILURES check (studio-agnostic) → SKILL backup (studio-agnostic) → studio_root lookup → STRUCTURE.md whitelist (studio-specific) → deprecated_patterns regex (studio-specific). This ordering means global invariants (D-11, D-12) always fire, while per-studio conventions fire only within studio scope. Future global invariants should be wired upfront; future per-studio rules should sit inside the find_studio_root branch."

requirements-completed: [FAIL-01, FAIL-03]

# Metrics
duration: ~10m
completed: 2026-04-19
---

# Phase 6 Plan 08: FAILURES Reservoir Hook Discipline Summary

**Wave 4 HOOK EXTENSION locking D-11 append-only + D-12 SKILL backup + D-14 imported-file separation into pre_tool_use.py. Two new helpers (check_failures_append_only: 41 lines, backup_skill_before_write: 30 lines) wired BEFORE the studio-root branch make the checks studio-agnostic — FAILURES.md protection and SKILL_HISTORY backup fire regardless of whether the tool-use target is inside a studio. Two deprecated_patterns entries added as audit trail (6 → 8 total). FAILURES.md seeded with 10-field entry schema; FAILURES_INDEX.md provides category-tagging index referencing `_imported_from_shorts_naberal.md` entries by fail-ID without ever modifying that 500-line Phase 3 sha256-locked file. 30 new tests (14 unit + 7 subprocess + 9 backup) lock the full decision matrix including Windows path separators, whitespace-only old_string, sibling-basename false positives, and Korean Unicode backup preservation. Phase 5 regression: 5 verify_hook_blocks.py checks + 31 hook tests all green; full Phase 6 suite 170 passed.**

## Performance

| Metric | Value |
|---|---|
| pre_tool_use.py line delta | +120 (152 → 272) |
| deprecated_patterns.json entries | 6 → 8 |
| Tests created | 30 (14 unit + 7 subprocess + 9 SKILL) |
| Test runtime (3 new files) | ~1.6s |
| Phase 6 full suite runtime | ~2.1s (170 tests) |
| Phase 5 hook regression | 31 tests + 5 subprocess checks, all green |

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written. The broad `SKILL\\.md` content-scan regex was flagged as potentially over-matching docs but kept per plan (audit trail only; real enforcement is the Python helper).

### Path Correction

The plan frontmatter listed hook path as `.claude/hooks/pre_tool_use.py` while an ambiguous reference in the execution prompt pointed to `scripts/hook/pre_tool_use.py`. Verified via Glob: the hook lives at `.claude/hooks/pre_tool_use.py` (matching Phase 5 Plan 01 baseline and `.claude/settings.json` registration). No file created at the erroneous path.

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| `python -c "import json; d = json.loads(open('.claude/deprecated_patterns.json', encoding='utf-8').read()); assert len(d['patterns']) == 8"` | ✅ exits 0 |
| `python -c "import ast; ast.parse(open('.claude/hooks/pre_tool_use.py', encoding='utf-8').read())"` | ✅ exits 0 |
| `def check_failures_append_only` present | ✅ 1 occurrence |
| `def backup_skill_before_write` present | ✅ 1 occurrence |
| `SKILL_HISTORY` referenced in hook | ✅ multiple |
| `append-only` referenced in hook | ✅ multiple |
| All 8 regex patterns compile | ✅ verified via re.compile loop |
| `python scripts/validate/verify_hook_blocks.py` | ✅ 5/5 PASS |
| `pytest tests/phase06/test_failures_append_only.py` | ✅ 14/14 pass |
| `pytest tests/phase06/test_hook_failures_block.py` | ✅ 7/7 pass |
| `pytest tests/phase06/test_skill_history_backup.py` | ✅ 9/9 pass |
| `test -f .claude/failures/FAILURES.md` | ✅ 24 lines |
| `test -f .claude/failures/FAILURES_INDEX.md` | ✅ 36 lines |
| `grep -c "append-only" .claude/failures/FAILURES.md` | ✅ ≥ 1 |
| `grep -c "_imported_from_shorts_naberal.md" .claude/failures/FAILURES_INDEX.md` | ✅ ≥ 1 |
| Phase 5 hook test regression (31 tests) | ✅ all pass |
| Full Phase 6 suite (170 tests) | ✅ all pass |

## Commits

- `5450f51` — feat(06-08): extend pre_tool_use hook with FAILURES append-only + SKILL backup (D-11, D-12)
- `88a3ae5` — test(06-08): seed FAILURES reservoir + 30 Hook enforcement tests (FAIL-01, FAIL-03)

## Self-Check: PASSED

All artifacts created, all commits verified, all acceptance criteria met.
