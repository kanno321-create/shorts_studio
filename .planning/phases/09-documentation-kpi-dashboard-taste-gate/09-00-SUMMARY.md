---
phase: 09-documentation-kpi-dashboard-taste-gate
plan: 00
subsystem: testing
tags: [pytest, scaffold, phase-9, wave-0, taste-gate, kpi, documentation, red-baseline, d-10, d-12, d-13]

requires:
  - phase: 08-remote-publishing-production-metadata
    provides: "D-13 Phase-independent conftest precedent + UTF-8 cp949 reconfigure idiom + scripts/failures/__init__.py 7-line namespace marker pattern + scripts/validate/phase08_acceptance.py SC aggregator shape"
  - phase: 06-wiki-notebooklm-integration-failures-reservoir
    provides: "Hook check_failures_append_only D-11 append-only contract enforced by pre_tool_use.py; D-14 sha256 immutable lock on harvested FAILURES.md prefix"
provides:
  - "tests/phase09/ test package scaffold (1 __init__.py + 1 conftest with 3 fixtures + 7 RED test stubs + 1 SC 1-4 aggregator)"
  - "synthetic_taste_gate_april fixture — D-10 sample 6 (탐정/조수 페르소나 titles, fake 6-char video_ids abc123/def456/ghi789/jkl012/mno345/pqr678, scores [5,4,4,3,2,1])"
  - "tmp_failures_md fixture — tmp FAILURES.md seeded with Phase 6 schema prefix + best-effort FAILURES_PATH monkeypatch (no-op while scripts.taste_gate.record_feedback not yet importable)"
  - "freeze_kst_2026_04_01 fixture — datetime.now(KST) frozen to 2026-04-01T09:00:00+09:00 for deterministic build_failures_block timestamps"
  - "scripts/taste_gate/ namespace marker (7-line mirror of scripts/failures/__init__.py)"
  - "docs/ directory (via .gitkeep) prepared for Plan 09-01 ARCHITECTURE.md target"
  - "phase09_acceptance.py RED baseline (4 stub aggregators returning False → exit 1)"
affects: [09-01 architecture-md, 09-02 kpi-log, 09-03 taste-gate-docs, 09-04 record-feedback, 09-05 e2e-phase-gate]

tech-stack:
  added:
    - "tests/phase09/ pytest test package (inherits pytest 8.x from project baseline, no new deps)"
    - "scripts/taste_gate/ Python stdlib-only namespace (will host record_feedback.py in Plan 09-04)"
  patterns:
    - "D-13 Phase-independent conftest — zero imports from tests/phase05..08 conftests (mirrors Phase 7/Phase 8 precedent)"
    - "pytest.importorskip(scripts.taste_gate.record_feedback) module-level guards on 4 test files to keep collection green while implementation awaits Plan 09-04"
    - "File-existence pytest.skip gates on 3 document-target test files (test_architecture_doc_structure / test_kpi_log_schema / test_taste_gate_form_schema) so Plans 09-01/02/03 RED→GREEN transitions are per-test"
    - "UTF-8 sys.stdout.reconfigure at conftest + acceptance aggregator import (Windows cp949 safety per Pitfall 7)"
    - "SC 1-4 aggregator mirror of scripts/validate/phase08_acceptance.py shape (Wave 0 stubs all return False; Plan 09-05 flips to subprocess.run(pytest ...) checks)"

key-files:
  created:
    - tests/phase09/__init__.py
    - tests/phase09/conftest.py
    - tests/phase09/test_architecture_doc_structure.py
    - tests/phase09/test_kpi_log_schema.py
    - tests/phase09/test_taste_gate_form_schema.py
    - tests/phase09/test_record_feedback.py
    - tests/phase09/test_score_threshold_filter.py
    - tests/phase09/test_failures_append_only.py
    - tests/phase09/test_e2e_synthetic_dry_run.py
    - tests/phase09/phase09_acceptance.py
    - scripts/taste_gate/__init__.py
    - docs/.gitkeep
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/deferred-items.md
  modified: []

key-decisions:
  - "D-10 honored: synthetic sample 6 uses 탐정/조수 페르소나 titles (탐정이 조수에게 묻다 / 100억 갑부 / 3번째 편지 / 조수가 놓친 단서 / 5번 방문한 이유 / 범인의 마지막 말) — zero 테스트용 쇼츠 placeholder hits."
  - "D-12/D-13 anchored in tests before implementation: test_failures_append_only.py AST-scans scripts/taste_gate/record_feedback.py for open(path, 'w') violation AND skip_gates/TODO(next-session)/try-except-pass Hook-3종 forbidden patterns. test_score_threshold_filter.py locks score <=3 boundary via 5 unit tests plus a mixed-six-row synthetic end-to-end."
  - "Pitfall 3 honored: video_ids use obviously-fake 6-char format (abc123..pqr678) — shortern than YouTube's canonical 11-char base64 so retrospective analysis in Phase 10 can never mistake dry-run data for real."
  - "Test contract with fixture: synthetic sample scores [5,4,4,3,2,1] → D-13 filter yields exactly 3 escalations (scores 3/2/1). Test test_filter_mixed_six_rows locks this invariant so any regression in either the sample fixture or filter_escalate() contract will surface."
  - "Task 9-00-02 scoped 7 test stubs that collect but skip/importorskip on Wave 0 — chose pytest.skip(file-existence) for doc targets and pytest.importorskip(module) for code targets per the distinct RED→GREEN transitions Plans 09-01/02/03 (doc files appear) vs 09-04 (Python module appears) drive."
  - "Task 9-00-03 SC#1-4 aggregator returns False stubs (not subprocess calls) at Wave 0 — Plan 09-05 flips each to subprocess.run(pytest ...) per scripts/validate/phase08_acceptance.py precedent. Mirror path (tests/ not scripts/validate/) matches PLAN frontmatter."

metrics:
  duration: ~15min
  completed: 2026-04-20
  tasks_complete: 3
  files_created: 13
  files_modified: 0
  commits: 3
  new_tests: 0 green / 35 RED-collected (17 file-existence-gated + 18 importorskip-gated)
  regression_baseline_preserved: true (Phase 4 244 + Phase 5 329 + Phase 6 236 + Phase 7 177 + Phase 8 205 = 1191 tests collectible per-phase)

wave: 0
depends_on: []
estimated_commits: 3
actual_commits: 3
---

# Phase 9 Plan 00: Foundation Summary

**One-liner:** Wave 0 RED scaffold — tests/phase09/ test package with 3 fixtures (D-10 synthetic 6 + D-12 FAILURES seed + 2026-04-01 KST freeze), 7 RED test stubs covering SC#1-4 + KPI-05/06 acceptance surface, phase09_acceptance.py SC 1-4 aggregator (all-FAIL by design), scripts/taste_gate/ namespace marker (7-line mirror of scripts/failures/), and docs/ directory prepared for Plan 09-01 ARCHITECTURE.md. Unblocks Waves 1-3.

## Execution

### Task 9-00-01 — Package markers + namespace + conftest (commit 7875cee)

Shipped 4 scaffolding files in one atomic commit:

- `tests/phase09/__init__.py` — empty package marker (D-13 Phase 7 precedent)
- `tests/phase09/conftest.py` (166 lines) — 3 fixtures:
  - `synthetic_taste_gate_april(tmp_path)` → writes tmp/wiki/kpi/taste_gate_2026-04.md with status=dry-run frontmatter + 탐정/조수 페르소나 6 rows + scores [5,4,4,3,2,1]
  - `tmp_failures_md(tmp_path, monkeypatch)` → writes seeded FAILURES.md with Phase 6 schema prefix + attempts best-effort FAILURES_PATH monkeypatch (no-op while module awaits Plan 09-04)
  - `freeze_kst_2026_04_01(monkeypatch)` → patches datetime.now(KST) inside scripts.taste_gate.record_feedback when importable; returns frozen datetime(2026, 4, 1, 9, 0, 0, tzinfo=KST) regardless
- `scripts/taste_gate/__init__.py` — 7-line namespace marker exact mirror of scripts/failures/__init__.py shape
- `docs/.gitkeep` — empty placeholder so docs/ directory is git-tracked for Plan 09-01 ARCHITECTURE.md

All 3 fixture function definitions matched via grep (exact count 3), no 테스트용 쇼츠 placeholder hits (count 0), 8 hits on the 6 fake video_ids (6 table cells + 2 header references, >= 6 required), Korean 탐정이 조수에게 묻다 title anchor present.

### Task 9-00-02 — 7 RED test stubs (commit 9916114)

Shipped 7 test files (417 lines total) in one atomic commit. Each file is parse-valid, pytest-collectible, and RED by design:

| File | Tests | Gate Pattern | RED→GREEN Owner |
|------|-------|--------------|-----------------|
| test_architecture_doc_structure.py | 6 | file-existence pytest.skip | Plan 09-01 |
| test_kpi_log_schema.py | 5 | file-existence pytest.skip | Plan 09-02 |
| test_taste_gate_form_schema.py | 6 | file-existence pytest.skip | Plan 09-03 |
| test_record_feedback.py | 4 | pytest.importorskip module | Plan 09-04 |
| test_score_threshold_filter.py | 6 | pytest.importorskip module | Plan 09-04 |
| test_failures_append_only.py | 6 | pytest.importorskip module | Plan 09-04 |
| test_e2e_synthetic_dry_run.py | 2 | pytest.importorskip module | Plan 09-05 |

35 total test functions. 10 pytest.importorskip occurrences across the 4 module-gated files (>= 4 required per acceptance). All 7 files AST-parse clean, `pytest tests/phase09/ --collect-only` exits 0 with 17 tests collected (the importorskip-guarded modules skip at module level, which is the intended RED behavior).

Notable test anchors:

- **test_mermaid_block_count** regex `^```mermaid\s*$` with MULTILINE — locks D-02 ≥ 3 Mermaid blocks
- **test_reading_time_annotations** regex `⏱\s*~?(\d+)\s*min` — sums ≤ 35 min tolerance (30 + 5 per D-03)
- **test_tldr_section_near_top** — TL;DR line index < 50 (D-03 top-pinned)
- **test_api_contract_present** — exact literal checks for `youtubeanalytics.googleapis.com/v2/reports` + `yt-analytics.readonly` + `audienceWatchRatio` + `averageViewDuration` (D-07)
- **test_hybrid_structure** — Part A + Part B strings + 6 exact column names (video_id/title/3sec_retention/completion_rate/avg_view_sec/taste_gate_rank) (D-06)
- **test_persona_titles_not_placeholder** — asserts `테스트용 쇼츠 not in content` AND regex `탐정|조수|범인|갑부|편지` match (CONTEXT.md §specifics)
- **test_filter_mixed_six_rows** — locks the [5,4,4,3,2,1] fixture ↔ filter_escalate() contract to exactly 3 escalations (score <= 3)
- **test_no_open_w_for_failures** — AST-walks record_feedback.py for any open(path, 'w') violation (Pitfall 2)
- **test_no_skip_gates_string** / **test_no_todo_next_session** / **test_no_try_except_silent_fallback** — Hook 3종 차단 forbidden-pattern anchors

### Task 9-00-03 — phase09_acceptance.py RED baseline (commit 53a5372)

Shipped tests/phase09/phase09_acceptance.py (2439 bytes) mirroring scripts/validate/phase08_acceptance.py shape:

- 4 SC aggregator functions (sc1_architecture_doc / sc2_kpi_log_hybrid / sc3_taste_gate_protocol_and_dryrun / sc4_e2e_synthetic_dryrun) each returning `False` at Wave 0
- `main()` dispatcher prints per-SC `SC#<N>: PASS|FAIL` lines + final `Phase 9 acceptance: ALL_PASS|FAIL` marker (mirrors Phase 8 `SC<N>: PASS` + `Phase 8 acceptance: ALL_PASS` format)
- UTF-8 sys.stdout.reconfigure guard at `__main__` entry (Pitfall 7)
- Exit 0 iff all 4 SC return True; exit 1 otherwise

Wave 0 execution confirmed:
```
$ python tests/phase09/phase09_acceptance.py
SC#1: FAIL
SC#2: FAIL
SC#3: FAIL
SC#4: FAIL
Phase 9 acceptance: FAIL
EXIT=1
```

Also logged D08-DEF-01 (pre-existing combined-sweep mocks/ ModuleNotFoundError) to deferred-items.md with verification: same 6 ERROR count + 1134 tests on commit 9916114 (pre-Task 9-00-03) — Phase 9 Wave 0 added zero production code and zero regression signal.

## Verification Results

### Automated (required by PLAN)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| `test -f tests/phase09/__init__.py` | exit 0 | exit 0 | ✅ |
| `test -f tests/phase09/conftest.py` | exit 0 | exit 0 | ✅ |
| `test -f scripts/taste_gate/__init__.py` | exit 0 | exit 0 | ✅ |
| `test -f docs/.gitkeep` | exit 0 | exit 0 | ✅ |
| `wc -l < scripts/taste_gate/__init__.py` | 5..10 | 7 | ✅ |
| `grep -c "def synthetic_taste_gate_april\|def tmp_failures_md\|def freeze_kst_2026_04_01" conftest.py` | 3 | 3 | ✅ |
| `grep -c "sys.stdout.reconfigure" conftest.py` | >= 1 | 1 | ✅ |
| `grep -c "탐정이 조수에게 묻다" conftest.py` | >= 1 | 1 | ✅ |
| `grep -c "테스트용 쇼츠" conftest.py` | 0 | 0 | ✅ |
| `grep -c "abc123\|def456\|ghi789\|jkl012\|mno345\|pqr678" conftest.py` | >= 6 | 8 | ✅ |
| AST parse validity (all 9 .py files) | all OK | all OK | ✅ |
| `grep -c "def test_"` per test file | arch≥5, kpi≥4, tg≥5, rf≥3, st≥5, fail≥5, e2e≥2 | 6/5/6/4/6/6/2 | ✅ |
| `grep -rn "pytest.importorskip" tests/phase09/ | wc -l` | >= 4 | 10 | ✅ |
| `grep -c "def sc1/sc2/sc3/sc4"` acceptance.py | 4 | 4 | ✅ |
| `grep -c "sys.stdout.reconfigure"` acceptance.py | >= 1 | 1 | ✅ |
| `pytest tests/phase09/ --collect-only -q` | exit 0 | exit 0 (17 tests collected) | ✅ |
| `python tests/phase09/phase09_acceptance.py` | exit 1 | exit 1 (4 FAILs) | ✅ RED baseline |

### Regression (Phase 4-8 preserved)

| Phase | Expected | Actual | Status |
|-------|----------|--------|--------|
| Phase 4 isolated | 244 tests | 244 collected | ✅ |
| Phase 5 isolated | 329 tests | 329 collected | ✅ |
| Phase 6 isolated | 236 tests | 236 collected | ✅ |
| Phase 7 isolated | 177 tests | 177 collected | ✅ |
| Phase 8 isolated | 205 tests | 205 collected | ✅ |
| Total per-phase | 1191 tests | 1191 collected | ✅ baseline preserved |

Combined sweep `tests/phase04..phase08 --co` exits with code 2 due to pre-existing D08-DEF-01 (6 collection ERRORs on `tests/phase08/mocks/test_*_mock.py` + `test_full_publish_chain_mocked.py` / `test_pinned_comment.py` / `test_smoke_cleanup.py` / `test_uploader_mocked_e2e.py` from `ModuleNotFoundError: No module named 'mocks.youtube_mock'`). Verified pre-existing by running identical command on commit `9916114` (before Task 9-00-03) — same 6 ERRORs + same 1134 tests collected. OUT OF SCOPE for Phase 9 Wave 0 per deviation Rule scope boundary; logged to `deferred-items.md`.

## Deviations from Plan

**None — plan executed exactly as written.**

One micro-adjustment worth noting: the plan's `<interfaces>` block and task 9-00-03 action body show the aggregator's `main()` returning the `all()` result without the final `Phase 9 acceptance: ALL_PASS|FAIL` marker line. To preserve tooling symmetry with `scripts/validate/phase08_acceptance.py` (which tests/phase08/test_phase08_acceptance.py asserts contains `Phase 8 acceptance: ALL_PASS`), I included the analogous `Phase 9 acceptance: ALL_PASS|FAIL` print line before returning. This is an additive change (does not alter exit code contract — all SC False → exit 1 as required) and matches the "mirror of scripts/validate/phase08_acceptance.py" guidance in the `<read_first>` block. Not flagged as a Rule 1/2/3 deviation because it falls within Claude's discretion on output formatting (analogous to how Phase 8 adds `Phase 8 acceptance:` marker without it being in every PLAN prose).

## Deferred Issues

See `.planning/phases/09-documentation-kpi-dashboard-taste-gate/deferred-items.md`:

- **D08-DEF-01** (pre-existing, inherited from Plan 08-03/08-04): combined sweep `tests/phase04..phase08 --co` ERRORs on `tests/phase08/mocks/` cross-phase imports. OUT OF SCOPE for Phase 9. Isolated per-phase collection works. Phase 8 owns resolution.

## Self-Check: PASSED

Verified by this executor:

1. **Commits exist on disk:**
   - 7875cee (Task 9-00-01 scaffold) — `git log | grep 7875cee` → FOUND
   - 9916114 (Task 9-00-02 RED stubs) — `git log | grep 9916114` → FOUND
   - 53a5372 (Task 9-00-03 aggregator) — `git log | grep 53a5372` → FOUND

2. **Files exist on disk:**
   - tests/phase09/__init__.py ✓ FOUND
   - tests/phase09/conftest.py ✓ FOUND (166 lines, 3 fixtures, 8 fake-id hits, 0 placeholder hits)
   - tests/phase09/test_architecture_doc_structure.py ✓ FOUND (6 test_*)
   - tests/phase09/test_kpi_log_schema.py ✓ FOUND (5 test_*)
   - tests/phase09/test_taste_gate_form_schema.py ✓ FOUND (6 test_*)
   - tests/phase09/test_record_feedback.py ✓ FOUND (4 test_*)
   - tests/phase09/test_score_threshold_filter.py ✓ FOUND (6 test_*)
   - tests/phase09/test_failures_append_only.py ✓ FOUND (6 test_*)
   - tests/phase09/test_e2e_synthetic_dry_run.py ✓ FOUND (2 test_*)
   - tests/phase09/phase09_acceptance.py ✓ FOUND (4 sc* functions + main + cp949 guard)
   - scripts/taste_gate/__init__.py ✓ FOUND (7 lines)
   - docs/.gitkeep ✓ FOUND (0 bytes)
   - .planning/phases/09-documentation-kpi-dashboard-taste-gate/deferred-items.md ✓ FOUND

3. **Runtime contract verified:**
   - `python tests/phase09/phase09_acceptance.py` → exit 1 (RED baseline)
   - `python -m pytest tests/phase09/ --collect-only -q` → exit 0 (17 tests collectible)
   - Phase 4-8 isolated collection → 1191 tests, zero regression

## Downstream Unblocks

| Wave | Plan | Test Target | Artifact Target |
|------|------|-------------|-----------------|
| 1 | 09-01 | test_architecture_doc_structure.py | docs/ARCHITECTURE.md (single-file, 3 Mermaid + reading time ≤35min + TL;DR top 50) |
| 1 | 09-02 | test_kpi_log_schema.py | wiki/kpi/kpi_log.md (Hybrid format + YouTube Analytics v2 contract) |
| 1 | 09-03 | test_taste_gate_form_schema.py | wiki/kpi/taste_gate_protocol.md + wiki/kpi/taste_gate_2026-04.md |
| 2 | 09-04 | test_record_feedback.py + test_score_threshold_filter.py + test_failures_append_only.py | scripts/taste_gate/record_feedback.py (~150-200 LOC stdlib) |
| 3 | 09-05 | test_e2e_synthetic_dry_run.py + phase09_acceptance.py flip | E2E glue + SC 1-4 aggregator flip to subprocess.run(pytest ...) |
