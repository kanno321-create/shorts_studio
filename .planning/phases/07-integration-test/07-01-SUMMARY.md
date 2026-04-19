---
phase: 7
plan: 07-01
subsystem: integration-test / Wave 0 foundation
tags: [phase-7, wave-0, foundation, tests, fixtures, harness-audit, D-11, D-13]
requirements: [TEST-01, AUDIT-02]
success_criteria: [SC1, SC5]
dependency_graph:
  requires: [Phase 4 agents, Phase 5 orchestrator, Phase 6 wiki+fallback]
  provides:
    - "tests/phase07/ package + conftest for downstream Waves 1-5"
    - "tests/phase07/fixtures/ 6 zero-byte placeholder media files"
    - "scripts/validate/harness_audit.py --json-out D-11 6-key JSON emission"
  affects:
    - "Unblocks Plans 07-02..07-08 (Wave 1-5 entire Phase 7 chain)"
    - "AUDIT-02 test surface (JSON schema) now programmatically assertable"
tech_stack:
  added: []
  patterns:
    - "D-13 independent conftest (no copy from phase05/06)"
    - "Don't Hand-Roll zero-byte placeholder (MagicMock bypass of read_bytes)"
    - "Pitfall 8 backward-compatible CLI extension (additive flag only)"
    - "stdlib-only helpers (re, json, pathlib, datetime) — no new deps"
key_files:
  created:
    - tests/phase07/__init__.py
    - tests/phase07/fixtures/__init__.py
    - tests/phase07/conftest.py
    - tests/phase07/fixtures/mock_kling.mp4
    - tests/phase07/fixtures/mock_runway.mp4
    - tests/phase07/fixtures/mock_typecast.wav
    - tests/phase07/fixtures/mock_elevenlabs.wav
    - tests/phase07/fixtures/mock_shotstack.mp4
    - tests/phase07/fixtures/still_image.jpg
    - tests/phase07/test_infra_smoke.py
    - tests/phase07/test_mock_fixtures_bytes.py
    - tests/phase07/test_harness_audit_json_flag.py
  modified:
    - scripts/validate/harness_audit.py  # 122 → 284 lines (additive)
    - .planning/phases/07-integration-test/07-VALIDATION.md  # 3 rows flipped + Wave 0 checkboxes
decisions:
  - "D-11 JSON schema emitted with 6 mandatory keys + phase + ISO-8601 Z-suffix timestamp metadata"
  - "Scanner excludes harness_audit.py itself + deprecated_patterns.json from self-scans to prevent self-referential matches"
  - "UTF-8 sys.stdout.reconfigure guard added to main() for Windows cp949 default (D-22)"
  - "Fixtures stay 0-byte (Don't Hand-Roll) — real MP4/WAV headers introduce unnecessary complexity + fragility with no testing value"
metrics:
  duration: ~25 minutes
  completed_date: 2026-04-19
  tasks_completed: 3/3
  commits: 4  # 2 × RED + 2 × GREEN
  files_created: 12
  files_modified: 2
  lines_added: ~647
  tests_added: 27  # 9 infra_smoke + 6 fixture_bytes + 7 json_flag + 5 parametrize duplicates
  regression_baseline: "809/809 preserved (Phase 4 244 + Phase 5 329 + Phase 6 236)"
  full_suite: "836/836 passing (809 baseline + 27 new Phase 7)"
  harness_audit_score: 90  # threshold 80, exit 0
---

# Phase 7 Plan 01: Wave 0 Foundation Summary

One-liner: tests/phase07/ scaffold + 6 zero-byte media fixtures + harness_audit.py --json-out D-11 JSON emission (all backward-compatible, 809 regression preserved).

---

## Objective (from PLAN)

Wave 0 FOUNDATION — Create `tests/phase07/` package skeleton with shared fixtures independent from phase05/06 conftests (D-13), seed 6 zero-byte placeholder media fixtures under `tests/phase07/fixtures/`, and extend the existing 122-line `scripts/validate/harness_audit.py` with a `--json-out PATH` flag emitting the D-11 6-key JSON schema while preserving the legacy `HARNESS_AUDIT_SCORE: N` stdout text (Pitfall 8 — additive, zero-breaking-change).

Purpose: Wave 0 infrastructure unblocks every downstream Wave 1-5 plan. TEST-01..04 cannot run without `_fake_env` fixture + placeholder files; AUDIT-02 tests cannot parse JSON unless `--json-out` flag exists.

---

## Tasks Completed

### Task 7-01-01 — Phase 7 scaffold + 6 fixtures + conftest
- **RED commit:** `eca0bfe` — `test(07-01): RED — phase07 infra smoke tests failing (no conftest/fixtures yet)` (2 test files, 14 failed + 6 errors)
- **GREEN commit:** `c6044d3` — `feat(07-01): GREEN — phase07 scaffold + conftest + 6 zero-byte fixtures` (9 files, 20/20 smoke tests PASS)
- Files created:
  - `tests/phase07/__init__.py` (package marker)
  - `tests/phase07/fixtures/__init__.py` (sub-package marker)
  - `tests/phase07/conftest.py` (93 lines) — 6 fixtures: `repo_root`, `phase07_fixtures`, `_fake_env`, `tmp_session_id`, `mock_pass_verdict`, `mock_fail_verdict`
  - `tests/phase07/fixtures/mock_kling.mp4` (0 bytes)
  - `tests/phase07/fixtures/mock_runway.mp4` (0 bytes)
  - `tests/phase07/fixtures/mock_typecast.wav` (0 bytes)
  - `tests/phase07/fixtures/mock_elevenlabs.wav` (0 bytes)
  - `tests/phase07/fixtures/mock_shotstack.mp4` (0 bytes)
  - `tests/phase07/fixtures/still_image.jpg` (0 bytes)
  - `tests/phase07/test_infra_smoke.py` (71 lines, 9 tests; 14 assertions after parametrize)
  - `tests/phase07/test_mock_fixtures_bytes.py` (39 lines, 1 parametrized test, 6 assertions)

### Task 7-01-02 — harness_audit.py --json-out D-11 extension
- **RED commit:** `8a88cbc` — `test(07-01): RED — harness_audit --json-out D-11 schema tests failing` (7 tests, 5 failed + 2 passed)
- **GREEN commit:** `3f1fd4f` — `feat(07-01): GREEN — harness_audit --json-out emits D-11 6-key schema` (7/7 PASS)
- `scripts/validate/harness_audit.py`: **122 → 284 lines** (additive, backward-compatible)
- New helpers (stdlib-only):
  - `_scan_deprecated_patterns(patterns_json)` — scans `scripts/`, `.claude/agents/`, `tests/`, `wiki/` for each of 8 deprecated_patterns.json regex, excluding self + patterns JSON from self-referential matches
  - `_count_agents(agents_root)` — counts AGENT.md files under agents_root (currently 33)
  - `_skills_over_500_lines(skills_root)` — returns POSIX paths of SKILL.md > 500 lines (currently 0 — all 5 shared skills: 106-145 lines)
  - `_descriptions_over_1024(agents_root)` — returns POSIX paths of AGENT.md with frontmatter description > 1024 chars (currently 0)
  - `_a_rank_drift_count(violations)` — counts violations mentioning A급/A-rank/drift
  - `_build_d11_report(score, violations, agents_root)` — assembles full D-11 report with `phase=7` + UTC ISO-8601 Z timestamp
- `main()` changes:
  - Added `--json-out PATH` argparse flag
  - Added UTF-8 `sys.stdout.reconfigure` guard for Windows cp949 (D-22)
  - Legacy `HARNESS_AUDIT_SCORE: N` + violation/warning prints preserved exactly
  - JSON emission gated by `if args.json_out is not None:` — zero impact when flag absent
- Test file `tests/phase07/test_harness_audit_json_flag.py` (160 lines, 7 tests):
  - `test_audit_script_exists`
  - `test_text_output_backward_compatible` (Pitfall 8)
  - `test_json_out_flag_emits_d11_schema` (6 mandatory keys)
  - `test_json_types_match_d11_contract` (int/list/dict types, 0≤score≤100)
  - `test_json_out_includes_phase_and_timestamp` (metadata)
  - `test_deprecated_pattern_matches_scans_8_patterns`
  - `test_json_out_preserves_exit_code_on_score_ge_threshold`

### Task 7-01-03 — Regression sweep
- No file changes (verification-only task)
- Commands executed (all exit 0):
  - `python -m pytest tests/phase04 tests/phase05 tests/phase06 -q --no-cov` → **809 passed in 68.50s**
  - `python -m pytest tests/phase07/ -q --no-cov` → **27 passed in 3.01s**
  - `python scripts/validate/harness_audit.py` → score=90, threshold=80, exit=0
  - Full sweep `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q --no-cov` → **836 passed in 76.16s**

---

## D-11 6-key JSON Sample (current baseline)

```json
{
  "score": 90,
  "a_rank_drift_count": 206,
  "skill_over_500_lines": [],
  "agent_count": 33,
  "description_over_1024": [],
  "deprecated_pattern_matches": {
    "ORCH-08 / CONFLICT_MAP A-6": 18,
    "ORCH-09 / CONFLICT_MAP A-5": 22,
    "VIDEO-01 / D-13": 114,
    "Phase 3 canonical": 8,
    "AF-8": 12,
    "Project Rule 3": 0,
    "FAIL-01 / D-11": 2,
    "FAIL-03 / D-12": 30
  },
  "phase": 7,
  "timestamp": "2026-04-19T10:25:39.369149Z"
}
```

**Note on `a_rank_drift_count: 206`** — This number reflects raw regex matches across the scanned roots. It includes legitimate documentation/enforcement references (e.g. the deprecated_patterns.json regex itself matches across FAILURES.md documentation, validator scripts enforcing the rule, and research documents mentioning the forbidden pattern). Phase 7 Wave 4 (Plan 07-07) will interpret these counts and calibrate the "A-rank drift 0건" invariant by either excluding enforcement/documentation paths or filtering match contexts (e.g. skip matches inside code comments or markdown code blocks documenting the rule). For Plan 07-01 (Wave 0), the contract is type correctness + key presence, both of which are fully satisfied.

---

## Verification

### Acceptance criteria evaluation

| # | Plan acceptance criterion | Result |
|---|---------------------------|--------|
| 1 | `test -f tests/phase07/__init__.py` | ✅ PASS |
| 2 | `test -f tests/phase07/fixtures/__init__.py` | ✅ PASS |
| 3 | All 6 fixtures exist and are 0-byte | ✅ PASS (6/6) |
| 4 | `def _fake_env` in conftest.py | ✅ PASS (1 occurrence) |
| 5 | 5 named fixtures in conftest.py | ✅ PASS (mock_pass_verdict, mock_fail_verdict, tmp_session_id, repo_root, phase07_fixtures) |
| 6 | `_REPO_ROOT = Path` in conftest.py | ✅ PASS |
| 7 | `pytest tests/phase07/test_infra_smoke.py tests/phase07/test_mock_fixtures_bytes.py -q` exits 0 | ✅ PASS (20/20) |
| 8 | `HARNESS_AUDIT_SCORE` preserved in harness_audit.py | ✅ PASS (1 occurrence on stdout) |
| 9 | `--json-out` flag present | ✅ PASS (argparse add_argument + usage) |
| 10 | 5 new helpers present | ✅ PASS (_build_d11_report, _scan_deprecated_patterns, _skills_over_500_lines, _count_agents, _descriptions_over_1024, _a_rank_drift_count — 6 helpers total) |
| 11 | `python scripts/validate/harness_audit.py` legacy text still printed | ✅ PASS |
| 12 | `pytest tests/phase07/test_harness_audit_json_flag.py -q` exits 0 | ✅ PASS (7/7) |
| 13 | `python -m py_compile scripts/validate/harness_audit.py` exits 0 | ✅ PASS |
| 14 | `pytest tests/phase04 tests/phase05 tests/phase06 -q` exits 0 | ✅ PASS (809/809) |
| 15 | `pytest tests/phase07/ -q` exits 0 | ✅ PASS (27/27) |
| 16 | `python scripts/validate/harness_audit.py` exits 0 (score ≥ 80) | ✅ PASS (score=90) |

### VALIDATION.md rows flipped

- Row 1 (7-01-01 scaffold) ⬜ pending → ✅ green
- Row 2 (7-01-02 fixture bytes) ⬜ pending → ✅ green
- Row 25 (7-01-03 regression sweep) ⬜ pending → ✅ green
- Frontmatter `wave_0_complete: false` → `true`
- Wave 0 Requirements checkboxes: 4/6 [x] (remaining 2 belong to Plans 07-02 and 07-08)

---

## Deviations from Plan

None — plan executed exactly as written.

Minor note on helper count: the spec called for "≥ 5 new helpers" and we shipped 6 (`_a_rank_drift_count` was added as a named helper rather than an inline lambda). This strictly exceeds the contract and is not a deviation.

---

## Known Stubs

None. All files are fully wired. Zero-byte fixtures are intentional placeholders per D-2 / Don't Hand-Roll (MagicMock adapters in Plans 07-02..07-03 never read_bytes on these paths), not stubs. Documented in `tests/phase07/test_mock_fixtures_bytes.py` so future drift toward hand-rolled MP4 headers is blocked.

---

## Commit Hashes (shorts repo)

| Order | Hash    | Message |
|-------|---------|---------|
| 1     | eca0bfe | test(07-01): RED — phase07 infra smoke tests failing (no conftest/fixtures yet) |
| 2     | c6044d3 | feat(07-01): GREEN — phase07 scaffold + conftest + 6 zero-byte fixtures |
| 3     | 8a88cbc | test(07-01): RED — harness_audit --json-out D-11 schema tests failing |
| 4     | 3f1fd4f | feat(07-01): GREEN — harness_audit --json-out emits D-11 6-key schema |

Final metadata commit (SUMMARY + VALIDATION flip + STATE + ROADMAP) will be recorded immediately after self-check.

---

## Self-Check: PASSED

Verification commands (all ran successfully):
- `test -f tests/phase07/__init__.py` → FOUND
- `test -f tests/phase07/fixtures/__init__.py` → FOUND
- 6 × fixture files under `tests/phase07/fixtures/` → all FOUND (all 0 bytes)
- `tests/phase07/conftest.py` → FOUND (93 lines)
- `tests/phase07/test_infra_smoke.py` → FOUND (71 lines)
- `tests/phase07/test_mock_fixtures_bytes.py` → FOUND (39 lines)
- `tests/phase07/test_harness_audit_json_flag.py` → FOUND (160 lines)
- `scripts/validate/harness_audit.py` → MODIFIED (122 → 284 lines)
- `git log` shows all 4 commit hashes (eca0bfe, c6044d3, 8a88cbc, 3f1fd4f) → FOUND
- pytest sweep Phase 4+5+6+7 → 836/836 PASS
- harness_audit.py standalone → exit 0, score 90
- harness_audit.py --json-out emits D-11 schema → valid JSON with all 6 mandatory keys

No missing items. Plan 07-01 is Wave 0 complete. Downstream Plans 07-02..07-08 are unblocked.
