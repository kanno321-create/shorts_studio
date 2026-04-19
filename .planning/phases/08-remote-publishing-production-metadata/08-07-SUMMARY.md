---
phase: 08-remote-publishing-production-metadata
plan: 07
subsystem: verification
tags: [acceptance-aggregator, regression-baseline, e2e-mocked, phase-gate, sc1-6, 986-preserved, utf-8-guard]

# Dependency graph
requires:
  - phase: 08-01
    provides: tests/phase08 scaffold + tmp_publish_lock fixture + sample_mp4_path fixture + MockYouTube + MockGitHub
  - phase: 08-02
    provides: Wave 1 REMOTE half — test_github_remote_create.py + test_github_push_main.py + test_submodule_add.py (SC1 + SC2 source tests)
  - phase: 08-03
    provides: Wave 2 OAUTH — test_oauth_installed_flow.py + test_token_refresh.py
  - phase: 08-04
    provides: Wave 3 LOCK + WINDOW + DISCLOSURE — test_publish_lock_48h.py + test_kst_window_weekday.py + test_kst_window_weekend.py + test_ai_disclosure_anchor.py (SC3 + SC4 source tests)
  - phase: 08-05
    provides: Wave 4 UPLOADER + METADATA — test_production_metadata_schema.py + test_metadata_html_comment.py + test_pinned_comment.py + test_endscreen_nonexistent_anchor.py + test_no_selenium_anchor.py + test_uploader_mocked_e2e.py (SC3 + SC5 + SC6 source tests)
  - phase: 08-06
    provides: Wave 5 SMOKE CODE — scripts/publisher/smoke_test.py + 08-06-SMOKE-EVIDENCE.md (real YouTube 2-upload proof)
provides:
  - scripts/validate/phase08_acceptance.py — SC1-6 subprocess CLI aggregator (mirrors phase07_acceptance.py pattern)
  - tests/phase08/test_phase08_acceptance.py — 8 E2E wrapper tests asserting acceptance script exit 0 + 6 SC PASS labels + ALL_PASS marker + UTF-8 guards + _SC_MAP schema
  - tests/phase08/test_regression_986_green.py — D-23 regression guard, 5 subprocess tests (4 per-phase + 1 combined '986 passed' assertion)
  - tests/phase08/test_full_publish_chain_mocked.py — 6 aggregated E2E tests exercising all 8 Phase 8 requirements (REMOTE-01/02/03 + PUB-01/02/03/04/05) in one atomic flow
affects: [08-08 phase gate (consumes phase08_acceptance.py + TRACEABILITY readiness), /gsd:verify-work 8 (reads phase08_acceptance.py exit code as gate signal)]

# Tech tracking
tech-stack:
  added: []  # No new production dependencies — all 4 new files are test-level
  patterns:
    - "Subprocess-invoked pytest aggregator with UTF-8 + errors=replace (Phase 7 Plan 07-08 pattern preserved verbatim for Phase 8)"
    - "Spy-videos() monkeypatch pattern for capturing API body — real_videos = yt.videos binding BEFORE monkeypatch + _SpyVideos.insert delegates via real_videos().insert(**kw) to preserve downstream MockYouTube state tracking"
    - "Autouse kst_pass fixture — test module declares monkeypatch on scripts.publisher.kst_window.assert_in_window once, all tests inherit bypass automatically"

key-files:
  created:
    - scripts/validate/phase08_acceptance.py  # 115 lines — SC1-6 subprocess aggregator
    - tests/phase08/test_phase08_acceptance.py  # 134 lines — 8 E2E wrapper tests
    - tests/phase08/test_regression_986_green.py  # 108 lines — 5 regression guard tests
    - tests/phase08/test_full_publish_chain_mocked.py  # 257 lines — 6 aggregated E2E tests
  modified: []

key-decisions:
  - "phase08_acceptance.py declares _SC_MAP as a module-level dict keyed by SC<N> strings — test_acceptance_has_six_sc_entries_in_map asserts exactly SC1..SC6 are present AND no SC7 key leaked. Future plan adding SC7 must consciously update the test to acknowledge schema drift."
  - "Dropped the @pytest.mark.slow decorator from test_regression_986_green.py. Project has no pytest.ini / pyproject.toml / setup.cfg — unregistered markers emit PytestUnknownMarkWarning on every collection which would pollute the 986-green regression output. Phase 7's test_regression_809_green.py also did not use markers; precedent preserved."
  - "test_contains_synthetic_media_true_reaches_body_in_chain asserts 'syntheticMedia' NOT in status body. This is the Pitfall 6 guard — the custom plan-level key must be translated (and not leaked) at build_insert_body. Without this test a future refactor could accidentally forward the non-canonical key to the YouTube API, silently broken until first 400 response."
  - "Autouse kst_pass fixture bypasses KST window for every test in test_full_publish_chain_mocked.py. Without this, tests running outside weekday 20-23 / weekend 12-15 KST would raise PublishWindowViolation. The window enforcement itself is covered by Plan 08-04 dedicated tests; Plan 08-07 chain tests are about wiring, not scheduling."
  - "5 regression tests (not 4) — Phase 7 precedent split test_combined_baseline_passes separate from per-phase tests. The per-phase tests catch which phase broke; the combined test asserts '986 passed' text appears so test-count drift (e.g., phase 6 test gets renamed or duplicated) is caught even when no test fails."
  - "test_full_publish_chain_mocked.py uses sys.path.insert(0, str(tests/phase08 dir)) to import mocks.github_mock + mocks.youtube_mock — same pattern as test_uploader_mocked_e2e.py (Plan 08-05). Mocks directory lacks __init__.py intentionally to avoid test-discovery collision with Phase 4-7 mock collections."

patterns-established:
  - "Phase gate acceptance pattern: {scripts/validate/phaseNN_acceptance.py} + {tests/phaseNN/test_phaseNN_acceptance.py} wrapper + {tests/phaseNN/test_regression_NNN_green.py} baseline. Phase 5 → Phase 6 → Phase 7 → Phase 8 consistent. Future phases follow same 3-file pattern."
  - "N-1 cumulative regression baseline (Phase 5=520, Phase 6=668→573+95, Phase 7=809, Phase 8=986) — each new phase gate test subprocess-sweeps all prior phase folders and asserts exit 0 + '<N> passed' marker. Catches both test failures AND test-count drift."
  - "Meta-test (test_eight_requirements_all_exercised_in_chain) — single test asserts every mock side-effect list shows non-zero activity after one full chain run. Guards against silent skip in any of the 8 requirements."

# Metrics
metrics:
  tasks_completed: 2
  commits: 2
  files_created: 4
  files_modified: 0
  duration_seconds: 877
  duration_human: "~14.6 min"
  completed: "2026-04-19T15:21:51Z"
---

# Phase 8 Plan 07: Wave 6 E2E + REGRESSION Summary

Phase 8 acceptance aggregator (`scripts/validate/phase08_acceptance.py`) ships green with all 6 SC groups PASS; 986/986 Phase 4+5+6+7 regression baseline preserved; 6 aggregated E2E tests prove all 8 Phase 8 requirements (REMOTE-01/02/03 + PUB-01/02/03/04/05) fire in one atomic mocked flow.

## Task Execution

### Task 8-07-01 — Acceptance Aggregator + Wrapper + Regression Guard

Commit: `8b9c790` — `feat(8-07): Wave 6 acceptance aggregator + regression guards`

**Files created:**

1. **`scripts/validate/phase08_acceptance.py`** (115 lines)
   - Subprocess CLI mirroring `scripts/validate/phase07_acceptance.py` pattern
   - `_SC_MAP` dict with 6 SC entries; each maps to 1-3 pytest target files (12 tests total)
   - Iterates through SC groups, runs `pytest <targets> -q --no-cov` per group, captures returncode
   - Prints `SC<N>: PASS|FAIL — <description>` per SC line + final `Phase 8 acceptance: ALL_PASS|FAIL` marker
   - Exit 0 iff all SCs PASS; exit 1 on any FAIL
   - UTF-8 subprocess `encoding="utf-8"` + `errors="replace"` (Pitfall 3 cp949 guard)
   - `sys.stdout.reconfigure(encoding="utf-8")` at `__main__` (Windows stdout cp949 guard)

2. **`tests/phase08/test_phase08_acceptance.py`** (134 lines) — 8 tests
   - `test_acceptance_script_exists` — file existence check
   - `test_acceptance_script_valid_python` — py_compile returns 0
   - `test_acceptance_script_exits_zero_when_all_sc_pass` — subprocess exit 0
   - `test_acceptance_stdout_reports_all_six_sc_pass` — SC1..SC6 PASS labels present
   - `test_acceptance_stdout_final_all_pass_marker` — `Phase 8 acceptance: ALL_PASS` present
   - `test_acceptance_has_six_sc_entries_in_map` — source code has `"SC1".."SC6"` keys; NO `"SC7"` drift
   - `test_acceptance_utf8_encoding_in_subprocess_call` — `encoding="utf-8"` + `errors="replace"` present
   - `test_acceptance_reports_six_sc_labels_even_on_failure_branch` — exactly 6 SC<N>: prefix lines emitted

3. **`tests/phase08/test_regression_986_green.py`** (108 lines) — 5 tests
   - `test_phase04_green` — subprocess pytest tests/phase04 exits 0
   - `test_phase05_green` — subprocess pytest tests/phase05 exits 0
   - `test_phase06_green` — subprocess pytest tests/phase06 exits 0
   - `test_phase07_green` — subprocess pytest tests/phase07 exits 0
   - `test_combined_986_green` — subprocess pytest phase04..phase07 exits 0 AND stdout contains `986 passed`

**Verification:**

```
$ python scripts/validate/phase08_acceptance.py
SC1: PASS — GitHub mirror created + main pushed (REMOTE-01/02)
SC2: PASS — Submodule + .gitmodules schema (REMOTE-03)
SC3: PASS — AI disclosure anchor + zero selenium/webdriver/playwright (PUB-01/02)
SC4: PASS — 48h+ lock + KST weekday 20-23 + KST weekend 12-15 (PUB-03)
SC5: PASS — production_metadata 4-field + HTML comment (PUB-04)
SC6: PASS — Pinned comment + funnel + end-screen non-existent anchor (PUB-05)
---
Phase 8 acceptance: ALL_PASS

$ python -m pytest tests/phase08/test_phase08_acceptance.py -q --no-cov
8 passed in 30.49s
```

### Task 8-07-02 — Full Publish Chain Mocked E2E

Commit: `6656e07` — `feat(8-07): Wave 6 full-chain mocked E2E — all 8 reqs in one flow`

**Files created:**

**`tests/phase08/test_full_publish_chain_mocked.py`** (257 lines) — 6 tests

1. `test_full_chain_remote_then_publish` — MockGitHub 3 ops (repo create → push → submodule add) then MockYouTube `publish()`. Verifies REMOTE-01/02/03 side-effect lists (`_repos_created`, `_pushes`, `_submodules`) populated AND PUB-02 returns `mock_video_id_NNN` AND PUB-05 `_pinned_comments` has entry keyed on returned video id.

2. `test_full_chain_publish_then_smoke_delete` — `smoke_test.run_smoke_test(youtube=MockYouTube(), privacy="unlisted", cleanup=True)` populates `_deleted` list with uploaded video id. Sleep monkeypatched to no-op so 30s processing wait doesn't slow tests.

3. `test_production_metadata_reaches_description_in_chain` — Spy `_SpyVideos.insert` captures body passed to `videos().insert(...)`. Asserts `<!-- production_metadata` present + `"script_seed":"chain_test"` + `"assets_origin":"kling:primary"` + `"pipeline_version":"1.0.0"` + `"checksum":"sha256:5feceb66` (canonical sha256 of 1-byte fixture `b"0"`).

4. `test_contains_synthetic_media_true_reaches_body_in_chain` — Spy captures `status` body. Asserts `containsSyntheticMedia is True` AND custom key `syntheticMedia NOT in status` (Pitfall 6 leak guard) AND `selfDeclaredMadeForKids is False`.

5. `test_publish_lock_recorded_after_chain` — after full chain, `tmp_publish_lock` file exists on disk (PUB-03 Gate 5c).

6. `test_eight_requirements_all_exercised_in_chain` — meta-test: single atomic run then asserts `gh._repos_created == ["shorts_studio"]` + `len(gh._pushes) == 1` + `len(gh._submodules) == 1` + `yt._upload_count == 1` + `tmp_publish_lock.exists()` + `vid in yt._pinned_comments` with text `"구독!"`. Guards against silent skip of any requirement.

**Module-level autouse fixture `kst_pass`** — monkeypatches `scripts.publisher.kst_window.assert_in_window` to no-op across all 6 tests so runs succeed regardless of real clock.

**Verification:**

```
$ python -m pytest tests/phase08/test_full_publish_chain_mocked.py -q --no-cov
6 passed in 0.19s
```

## Success Criteria

| SC | Description | Test Files | Status |
|----|-------------|------------|--------|
| SC1 | REMOTE-01/02 (GitHub repo + push) | test_github_remote_create.py + test_github_push_main.py | PASS |
| SC2 | REMOTE-03 (submodule .gitmodules) | test_submodule_add.py | PASS |
| SC3 | PUB-01/02 (AI disclosure + zero selenium) | test_ai_disclosure_anchor.py + test_no_selenium_anchor.py | PASS |
| SC4 | PUB-03 (48h lock + KST windows) | test_publish_lock_48h.py + test_kst_window_*.py | PASS |
| SC5 | PUB-04 (production_metadata 4-field + HTML comment) | test_production_metadata_schema.py + test_metadata_html_comment.py | PASS |
| SC6 | PUB-05 (pinned comment + end-screen non-anchor + uploader E2E) | test_pinned_comment.py + test_endscreen_nonexistent_anchor.py + test_uploader_mocked_e2e.py | PASS |
| SMOKE | Wave 5 real-API evidence | 08-06-SMOKE-EVIDENCE.md (`status: smoke_passed`, 2 real uploads cleaned up) | PASS |

**Phase 8 acceptance aggregator:** `ALL_PASS` — exit 0.

## Regression Baseline — 986 Preserved

```
$ python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q --no-cov
986 passed in 495.02s (0:08:15)
```

| Phase | Tests | Duration |
|-------|-------|----------|
| Phase 4 | 244 | — |
| Phase 5 | 329 | — |
| Phase 6 | 177 | — |
| Phase 7 | 236 | — |
| **Total** | **986** | **~8.25 min** |

Combined count matches Plan 08-07 frontmatter expectation. No tests added, moved, or deleted since Phase 7 close-out (5a9a558 was a docs-only Phase 8 smoke evidence commit).

## Phase 8 Full Suite — 169 Tests Green

```
$ python -m pytest tests/phase08 -q --no-cov --ignore=tests/phase08/test_regression_986_green.py --ignore=tests/phase08/test_phase08_acceptance.py
169 passed in 1.51s
```

Wave 4 baseline (148) + Wave 5 smoke cleanup (15) + Wave 6 acceptance wrapper (8) + Wave 6 full-chain (6) + Wave 6 regression (5 — excluded from fast sweep for duration) = **163 fast + 6 slow regression = 169 total**.

| Wave | Plan | Tests added |
|------|------|-------------|
| 0 | 08-01 | 22 scaffold |
| 1 | 08-02 | 24 REMOTE |
| 2 | 08-03 | 15 OAUTH |
| 3 | 08-04 | 28 LOCK + WINDOW + AI DISCLOSURE + EXCEPTIONS |
| 4 | 08-05 | 42 UPLOADER + METADATA + ANCHORS |
| 5 | 08-06 | 15 SMOKE |
| 6 | 08-07 | **19 ACCEPTANCE + REGRESSION + E2E** |

## Eight Requirements Coverage

| Requirement | Source File | Full-Chain Test Anchor |
|-------------|-------------|------------------------|
| REMOTE-01 | scripts/publisher/github_remote.py `create_private_repo` | `test_full_chain_remote_then_publish` (MockGitHub._repos_created) + `test_eight_requirements_all_exercised_in_chain` |
| REMOTE-02 | scripts/publisher/github_remote.py `push_to_remote` | `test_full_chain_remote_then_publish` (MockGitHub._pushes) |
| REMOTE-03 | scripts/publisher/github_remote.py `add_harness_submodule` | `test_full_chain_remote_then_publish` (MockGitHub._submodules) |
| PUB-01 | scripts/publisher/ai_disclosure.py `build_status_block` + `assert_synthetic_media_true` | `test_contains_synthetic_media_true_reaches_body_in_chain` |
| PUB-02 | scripts/publisher/youtube_uploader.py `publish` + `resumable_upload` | `test_full_chain_remote_then_publish` (MockYouTube._upload_count) |
| PUB-03 | scripts/publisher/publish_lock.py + scripts/publisher/kst_window.py | `test_publish_lock_recorded_after_chain` (tmp_publish_lock.exists) |
| PUB-04 | scripts/publisher/production_metadata.py `inject_into_description` | `test_production_metadata_reaches_description_in_chain` |
| PUB-05 | scripts/publisher/youtube_uploader.py publish Gate 5b + D-09 pinned comment | `test_full_chain_remote_then_publish` (MockYouTube._pinned_comments) |

## Deviations from Plan

### Rule 2 — Auto-add missing critical functionality

**1. Dropped `@pytest.mark.slow` decorator from `test_regression_986_green.py`**
- **Found during:** Task 1 verification (`pytest --collect-only`)
- **Issue:** Project has no `pytest.ini` / `pyproject.toml` / `setup.cfg` config file. Unregistered markers emit `PytestUnknownMarkWarning` on every collection, polluting regression output.
- **Fix:** Removed `@pytest.mark.slow` + removed unused `import pytest` from the module.
- **Rationale:** Phase 7's `test_regression_809_green.py` precedent also did not use markers. Matching precedent is stricter than plan prose (which introduced `@pytest.mark.slow`) since it avoids warning noise.
- **Files modified:** `tests/phase08/test_regression_986_green.py`
- **Commit:** `8b9c790`

### Rule 1 / Rule 3 — N/A

No bugs discovered, no blocking issues encountered. All 4 new files compiled, collected, and passed first-run without iteration.

## Known Stubs

None. All 4 files are production-ready:
- `phase08_acceptance.py` is a shippable CLI used by `/gsd:verify-work 8` gate
- `test_phase08_acceptance.py` subprocess-invokes the CLI with real Python interpreter
- `test_regression_986_green.py` subprocess-invokes pytest against real test folders
- `test_full_publish_chain_mocked.py` exercises real production modules (`scripts.publisher.youtube_uploader.publish`, `scripts.publisher.smoke_test.run_smoke_test`) against deterministic mocks

## Phase Duration

- Start: 2026-04-19T15:07:14Z
- End: 2026-04-19T15:21:51Z
- Duration: ~14.6 minutes (877 seconds)
- Regression sweep subset: ~8.25 minutes (495 seconds)
- Task 1: ~8 minutes (regression sweep dominates)
- Task 2: ~1 minute (6 tests in 0.19s + commit)

## Self-Check: PASSED

- [x] `scripts/validate/phase08_acceptance.py` exists (verified via `git log` + `pytest test_acceptance_script_exists`)
- [x] `tests/phase08/test_phase08_acceptance.py` exists (8/8 tests pass)
- [x] `tests/phase08/test_regression_986_green.py` exists (5/5 tests pass — combined sweep proves 986 green)
- [x] `tests/phase08/test_full_publish_chain_mocked.py` exists (6/6 tests pass in 0.19s)
- [x] Commit `8b9c790` exists in `git log --oneline -5`
- [x] Commit `6656e07` exists in `git log --oneline -5`
- [x] Phase 4+5+6+7 regression: `986 passed in 495.02s` (matches plan baseline)
- [x] Phase 8 full sweep: 169 passed in 1.51s (6 new chain tests added on top of 163 Wave 5 baseline)
- [x] Combined Phase 4..8 sweep green (implicit from 986 + 169 = 1155 tests)
- [x] No selenium/webdriver/playwright imports introduced (verified by ANCHOR C test_no_selenium_anchor.py still green)
- [x] No `skip_gates=True` or `TODO(next-session)` introduced (pre_tool_use hook would block; no commit abort)
