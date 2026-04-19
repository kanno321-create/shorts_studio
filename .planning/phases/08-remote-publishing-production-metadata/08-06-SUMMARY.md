---
phase: 08-remote-publishing-production-metadata
plan: 06
subsystem: publishing
tags: [smoke-test, wave-5, mockyoutube, unlisted-only, videos-delete, cleanup, smoke-gate, code-shipping-only, d-11, pub-01, pub-02, pub-03, pub-04, pub-05]

# Dependency graph
requires:
  - phase: 08-01
    provides: tests/phase08 scaffold + tmp_publish_lock fixture + sample_shorts.mp4 (1-byte fixture) + MockYouTube
  - phase: 08-03
    provides: scripts.publisher.oauth.get_credentials + CLIENT_SECRET_PATH + TOKEN_PATH (real-path precondition)
  - phase: 08-04
    provides: Wave 3 LOCK + WINDOW + DISCLOSURE substrate (consumed by publish() through Wave 4)
  - phase: 08-05
    provides: publish() 5-gate orchestrator + build_insert_body + resumable_upload
provides:
  - scripts.publisher.smoke_test module — one-shot CLI (argparse --privacy=unlisted [choices-locked] + --cleanup/--no-cleanup BooleanOptionalAction + --dry-run MockYouTube)
  - run_smoke_test() function — ValueError on non-unlisted, FileNotFoundError on missing client_secret.json, SmokeTestCleanupFailure on delete non-2xx
  - _wait_for_processing() — 30s budget with 2s polling, timeout falls through to cleanup (cleanup is non-negotiable)
  - _delete_video() — wraps any delete exception in SmokeTestCleanupFailure carrying video_id
  - _build_smoke_plan() — timestamped title + unlisted + embeddable=False + publicStatsViewable=False + smoke-safe funnel
  - 15 MockYouTube-based tests covering all paths (happy + public/private ValueError + cleanup=False + delete failure + wait fast-path + wait timeout + plan invariants + --dry-run + --no-cleanup + real-path precondition)
affects:
  - 08-07 E2E regression baseline now includes 163 Phase 8 tests (148 Wave 4 baseline + 15 Wave 5)
  - 08-08 phase gate — Wave 5 code-shipping milestone complete; real smoke execution deferred to orchestrator per user-approved gate

# Tech tracking
tech-stack:
  added:
    - argparse.BooleanOptionalAction for --cleanup / --no-cleanup dual form (Python 3.9+)
    - argparse choices=["unlisted"] as literal whitelist enforcement (cannot pass --privacy=public even with -h suggestions)
    - Lazy MockYouTube import under --dry-run branch (sys.path.insert into tests/phase08 + from mocks.youtube_mock import MockYouTube)
  patterns:
    - "D-11 safety layered guard: argparse choices + run_smoke_test() ValueError + hardcoded _build_smoke_plan()['status']['privacyStatus']='unlisted' — three independent layers prevent accidental public upload"
    - "Cleanup is non-negotiable — _wait_for_processing timeout falls through silently, _delete_video runs regardless of processingStatus. The 30s wait is a best-effort optimisation, not a blocker"
    - "Real-path precondition BLOCKING guard — CLIENT_SECRET_PATH.exists() checked BEFORE get_credentials() so FileNotFoundError with actionable 대표님 message surfaces instead of deep OAuth flow stack trace"
    - "Module-level CLIENT_SECRET_PATH + TOKEN_PATH re-imported so tests monkeypatch st.CLIENT_SECRET_PATH — matches the monkeypatch-friendly pattern established in 08-05"
    - "time.sleep patching via st.time reference (no_sleep autouse fixture) keeps wall-clock time.time() intact for deadline loop termination"

key-files:
  created:
    - scripts/publisher/smoke_test.py  # 280 lines — CLI entry point + run_smoke_test() + _wait_for_processing + _delete_video + _build_smoke_plan
    - tests/phase08/test_smoke_cleanup.py  # 269 lines — 15 tests (happy + enforcement + cleanup + delete-fail + wait + plan invariants + dry-run + precondition)
  modified: []

key-decisions:
  - "Rule 2 deviation — plan prose sample for test_cleanup_false_skips_delete asserted `vid in [f'mock_video_id_{i}' for i in range(10)]` which would FALSE for MockYouTube's zero-padded `mock_video_id_001`/`002`/etc. format (3-digit pad). Replaced with `vid.startswith('mock_video_id_')` — more robust and matches the actual MockYouTube generator shape. Zero regression in intent (still proves cleanup=False skipped the delete path)."
  - "Rule 2 deviation — added test_real_path_raises_when_client_secret_missing beyond plan prose. RESEARCH Environment Availability identifies missing credentials as a BLOCKING precondition; the run_smoke_test(youtube=None) branch has a FileNotFoundError guard. A dedicated test locks the precondition behaviour so future refactors cannot silently swallow it."
  - "Rule 2 deviation — switched argparse --cleanup flag to BooleanOptionalAction so the CLI surfaces --cleanup / --no-cleanup symmetrically. Plan prose used `action='store_true', default=True` which makes opt-OUT impossible from the CLI. Added test_main_dry_run_no_cleanup_prints_upload_only to lock the upload-only path stdout contract."
  - "Added test_smoke_plan_has_production_metadata_required_fields + test_smoke_plan_has_pinned_comment beyond plan prose to anchor the PUB-04 + D-09 invariants on the smoke-plan side. Without these, a smoke_test.py refactor could drop production_metadata or pinned_comment and still pass all previous tests. Both tests are pure-function asserts (no MockYouTube invocation) so cost is minimal (~0.1ms each)."
  - "Code shipping only. Real YouTube API smoke execution is ORCHESTRATOR responsibility per user-approved D-11 Option A. smoke_test.py CLI is invocable; 대표님 confirmed 'config/client_secret.json + config/youtube_token.json already in place' (copied from shorts_naberal). When orchestrator runs `python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup` after this plan's code lands, it will exit 0 with `SMOKE_VIDEO_ID: <real-id>` and `SMOKE_STATUS: cleanup-complete`. That execution record lands in 08-06-SMOKE-EVIDENCE.md (orchestrator-created, not this executor)."

patterns-established:
  - "Layered D-11 enforcement — argparse choices (CLI surface) + ValueError guard (function surface) + hardcoded _build_smoke_plan() (data surface) — bypassing one requires bypassing all three"
  - "Test-monkeypatch friendly module reference — from scripts.publisher.oauth import CLIENT_SECRET_PATH, TOKEN_PATH, get_credentials at module scope rather than functioning call — tests can monkeypatch st.CLIENT_SECRET_PATH or st.get_credentials without touching oauth.py"
  - "Exception re-raising with preserved context — SmokeTestCleanupFailure(video_id, str(exc)) from exc keeps both the structured attributes AND the chained __cause__ for post-mortem"
  - "Cleanup-is-mandatory pattern — _wait_for_processing timeout is a silent fall-through (no raise) because the video exists on the channel whether processing succeeded or not, and cleanup must happen regardless"

requirements-completed: [PUB-01, PUB-02, PUB-03, PUB-04, PUB-05]

# Metrics
duration: 10min
completed: 2026-04-19
commits:
  - 63464ca feat(8-06): smoke_test.py CLI for Wave 5 unlisted upload + cleanup
  - d9509f8 test(8-06): MockYouTube coverage of smoke_test paths (15 tests)

tasks-count: 2
files-count: 2
---

# Phase 8 Plan 06: Wave 5 SMOKE TEST Summary

One-shot smoke CLI + MockYouTube coverage for the real-YouTube 1-shot upload + delete cleanup cycle. Code shipping only — real API execution is orchestrator responsibility per user-approved D-11 Option A gate.

## What Ships

### `scripts/publisher/smoke_test.py` (280 lines)

**CLI surface**:
```
python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup
python scripts/publisher/smoke_test.py --privacy=unlisted --no-cleanup
python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup --dry-run
```

**Enforcement layers** (defence-in-depth for D-11 safety):

1. **argparse** — `choices=["unlisted"]` makes `--privacy=public` unparseable.
2. **`run_smoke_test()`** — explicit `ValueError` on any privacy != "unlisted".
3. **`_build_smoke_plan()`** — hardcoded `"privacyStatus": "unlisted"` literal.

**Execution chain** (real-API path):

```
CLIENT_SECRET_PATH.exists()? ─ no → FileNotFoundError (BLOCKING)
       │ yes
       ▼
get_credentials() → googleapiclient.discovery.build("youtube","v3",...)
       │
       ▼
publish() 5-gate orchestrator ─→ video_id
       │
       ▼ (cleanup=True)
_wait_for_processing(30s, 2s polling)
       │
       ▼
_delete_video() ─ non-2xx → SmokeTestCleanupFailure(video_id, reason)
       │
       ▼
stdout: SMOKE_VIDEO_ID: <id>
        SMOKE_STATUS: cleanup-complete
```

### `tests/phase08/test_smoke_cleanup.py` (269 lines, 15 tests)

**Coverage matrix**:

| Path | Test |
|------|------|
| Happy path (MockYouTube) | `test_happy_path_upload_and_delete` |
| `privacy="public"` | `test_privacy_public_raises_value_error` |
| `privacy="private"` | `test_privacy_private_raises_value_error` |
| `cleanup=False` | `test_cleanup_false_skips_delete` |
| `videos.delete` raises | `test_delete_failure_raises_smoke_cleanup_failure` |
| Processing succeeded first poll | `test_wait_for_processing_returns_on_succeeded_immediately` |
| Processing never succeeds | `test_wait_for_processing_timeout_no_crash` |
| Plan unlisted + embeddable=False | `test_smoke_plan_sets_unlisted_embeddable_false` |
| Plan ai_disclosure | `test_smoke_plan_has_synthetic_media_disclosure` |
| Plan title SMOKE_TEST_ prefix | `test_smoke_plan_title_has_timestamp` |
| Plan production_metadata | `test_smoke_plan_has_production_metadata_required_fields` |
| Plan pinned comment | `test_smoke_plan_has_pinned_comment` |
| `main --dry-run --cleanup` | `test_main_dry_run_uses_mock_youtube` |
| `main --dry-run --no-cleanup` | `test_main_dry_run_no_cleanup_prints_upload_only` |
| Missing client_secret.json | `test_real_path_raises_when_client_secret_missing` |

## Validation

- `python -m pytest tests/phase08/test_smoke_cleanup.py -q --no-cov` → 15 passed in 1.24s
- `python -m pytest tests/phase08 -q --no-cov` → 163 passed in 1.51s (148 baseline + 15 new)
- `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 -q --no-cov` → **986 passed in 516.66s** (0:08:36) — full regression preserved
- `python -m py_compile scripts/publisher/smoke_test.py` → exit 0
- `grep -c "privacyStatus.*unlisted" scripts/publisher/smoke_test.py` = 4 (≥ 1 ✓)
- `grep -c 'choices=\["unlisted"\]' scripts/publisher/smoke_test.py` = 1 ✓
- `grep -c 'if privacy != "unlisted":' scripts/publisher/smoke_test.py` = 1 ✓
- `grep -c "PROCESSING_WAIT_SECONDS = 30" scripts/publisher/smoke_test.py` = 1 ✓
- `grep -c "SmokeTestCleanupFailure" scripts/publisher/smoke_test.py` = 6 (≥ 1 ✓)
- `grep -c "sys.stdout.reconfigure" scripts/publisher/smoke_test.py` = 1 (≥ 1 ✓)
- Test grep (happy/public/cleanup_false/delete_fail/wait_for_processing) = 6 (≥ 5 ✓)

## Deviations from Plan

### Auto-fixed (Rule 1/2) — 5 items

**1. [Rule 2 — Completeness] Added `BooleanOptionalAction` for --cleanup flag**

- **Found during:** Task 1 implementation
- **Issue:** Plan prose spec used `action="store_true", default=True` which makes `--no-cleanup` impossible — CLI surface becomes asymmetric.
- **Fix:** Switched to `action=argparse.BooleanOptionalAction, default=True` (Python 3.9+) so both `--cleanup` and `--no-cleanup` are accepted.
- **Files modified:** scripts/publisher/smoke_test.py
- **Commit:** 63464ca

**2. [Rule 1 — Bug] test_cleanup_false_skips_delete id format assertion**

- **Found during:** Task 2 verification
- **Issue:** Plan prose asserted `vid in [f"mock_video_id_{i}" for i in range(10)]` but MockYouTube generates zero-padded ids like `mock_video_id_001`/`002` (3-digit pad per tests/phase08/mocks/youtube_mock.py:130). Plan's assertion would always FAIL.
- **Fix:** Replaced with `vid.startswith("mock_video_id_")` (robust to any pad width).
- **Files modified:** tests/phase08/test_smoke_cleanup.py
- **Commit:** d9509f8

**3. [Rule 2 — Completeness] Added real-path precondition test**

- **Found during:** Task 2 implementation
- **Issue:** BLOCKING precondition (CLIENT_SECRET_PATH.exists() check) was not covered in plan's proposed tests.
- **Fix:** Added `test_real_path_raises_when_client_secret_missing` — monkeypatches st.CLIENT_SECRET_PATH to a non-existent Path and asserts FileNotFoundError with "client_secret.json" substring.
- **Files modified:** tests/phase08/test_smoke_cleanup.py
- **Commit:** d9509f8

**4. [Rule 2 — Completeness] Added --no-cleanup dry-run test**

- **Found during:** Task 2 implementation
- **Issue:** Plan only tested `main(["--privacy=unlisted", "--cleanup", "--dry-run"])` but the upload-only stdout path (`SMOKE_STATUS: upload-only`) was not covered.
- **Fix:** Added `test_main_dry_run_no_cleanup_prints_upload_only` — locks the upload-only output contract AND the get_credentials-never-called guarantee under --no-cleanup.
- **Files modified:** tests/phase08/test_smoke_cleanup.py
- **Commit:** d9509f8

**5. [Rule 2 — Completeness] Added production_metadata + pinned_comment plan invariant tests**

- **Found during:** Task 2 implementation
- **Issue:** PUB-04 (production_metadata script_seed + assets_origin) and D-09 (pinned_comment funnel) invariants in _build_smoke_plan() were not covered. A silent refactor dropping either field would pass the plan's proposed tests.
- **Fix:** Added `test_smoke_plan_has_production_metadata_required_fields` and `test_smoke_plan_has_pinned_comment`.
- **Files modified:** tests/phase08/test_smoke_cleanup.py
- **Commit:** d9509f8

## Code Shipped vs Execution Pending

**Code shipped in this plan (executor responsibility):**

- [x] `scripts/publisher/smoke_test.py` CLI + `run_smoke_test()` + `_wait_for_processing()` + `_delete_video()` + `_build_smoke_plan()`
- [x] `tests/phase08/test_smoke_cleanup.py` with 15 MockYouTube-based tests
- [x] Phase 8 full suite 163/163 passing
- [x] Phase 4-7 986/986 regression preserved

**Execution pending (orchestrator responsibility per user-approved D-11 Option A):**

- [ ] Real YouTube API smoke run: `python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup`
- [ ] `08-06-SMOKE-EVIDENCE.md` creation with video_id + delete confirmation timestamp
- [ ] Channel state verification: `videos.list(id=<vid>)` returns 404 after delete

대표님 confirmed: `config/client_secret.json` + `config/youtube_token.json` already in place (copied from shorts_naberal). Orchestrator can invoke the CLI immediately after this plan commits without additional OAuth bootstrap.

## Self-Check: PASSED

**Files verified:**
- FOUND: scripts/publisher/smoke_test.py (280 lines)
- FOUND: tests/phase08/test_smoke_cleanup.py (269 lines)

**Commits verified:**
- FOUND: 63464ca (feat(8-06): smoke_test.py CLI)
- FOUND: d9509f8 (test(8-06): MockYouTube coverage)

**Tests verified:**
- tests/phase08/test_smoke_cleanup.py: 15 passed
- tests/phase08: 163 passed (148 baseline + 15 new)
- tests/phase04-07: 986 passed (regression preserved)

**Acceptance grep checks:** all ≥ minimums (see Validation section above).
