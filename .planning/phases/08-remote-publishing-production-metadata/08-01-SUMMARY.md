---
phase: 08-remote-publishing-production-metadata
plan: 01
subsystem: testing
tags: [pytest, youtube-api, github-api, mocks, fixtures, exceptions, publisher, scaffold, phase-7-continuity]

requires:
  - phase: 07-integration-test
    provides: "MockShotstack D-3 / Correction 2 allow_fault_injection=False default pattern + Phase-independent conftest precedent (D-13) + UTF-8 cp949 reconfigure idiom + 986/986 regression baseline"
provides:
  - "tests/phase08/ test package scaffold (3 __init__.py markers + 2 fixtures + 1 conftest with 6 shared fixtures)"
  - "MockYouTube resource double (videos/thumbnails/commentThreads) with Phase 7 default-safe fault injection contract"
  - "MockGitHub REST + subprocess git double (POST /user/repos + git_push + git_submodule_add) with idempotent 422 + askpass + path-collision fault modes"
  - "scripts/publisher/ namespace + CD-02 five-class exception hierarchy (PublishLockViolation / PublishWindowViolation / AIDisclosureViolation / SmokeTestCleanupFailure / GitHubRemoteError)"
  - "1-byte sample_shorts.mp4 fixture with deterministic sha256 5feceb66... for PUB-04 checksum tests"
  - "Canonical 4-field sample_production_metadata.json schema reference (script_seed/assets_origin/pipeline_version/checksum)"
affects: [08-02 github-remote, 08-03 oauth, 08-04 publish-lock-window-disclosure, 08-05 metadata-funnel, 08-06 smoke-gate, 08-07 e2e-regression, 08-08 phase-gate]

tech-stack:
  added:
    - "pytest test package tests/phase08/ (inherits pytest 7.x from Phase 5 pytest.ini)"
    - "stdlib-only mocks (zoneinfo + dataclasses + typing) — no new runtime deps"
  patterns:
    - "Phase-independent conftest (D-13) — zero imports from tests/phase05..07 conftests"
    - "allow_fault_injection=False default on mocks (Phase 7 Correction 2 inherited) — fault injection is explicit opt-in"
    - "Lazy adapter-library imports inside fault paths so mocks stay usable without googleapiclient / httplib2 installed"
    - "sys.path[0] insertion prelude per test module for mocks/ resolution (Phase 7 Plan 07-02 precedent)"
    - "UTF-8 stdout reconfigure with errors='replace' at conftest import (Windows cp949 safety)"

key-files:
  created:
    - tests/phase08/__init__.py
    - tests/phase08/mocks/__init__.py
    - tests/phase08/fixtures/__init__.py
    - tests/phase08/fixtures/sample_shorts.mp4
    - tests/phase08/fixtures/sample_production_metadata.json
    - tests/phase08/conftest.py
    - tests/phase08/test_scaffold.py
    - tests/phase08/mocks/youtube_mock.py
    - tests/phase08/mocks/test_youtube_mock.py
    - tests/phase08/mocks/github_mock.py
    - tests/phase08/mocks/test_github_mock.py
    - tests/phase08/test_exceptions_smoke.py
    - scripts/publisher/__init__.py
    - scripts/publisher/_placeholder.py
    - scripts/publisher/exceptions.py
  modified: []

key-decisions:
  - "D-10/D-13 honored: tests/phase08/conftest.py imports zero fixtures from phase05/06/07 conftests — fully independent per Phase 7 precedent."
  - "MockYouTube + MockGitHub default allow_fault_injection=False matches tests/phase07/mocks/shotstack_mock.py D-3 contract exactly; fault modes are strict opt-in."
  - "CD-02 exception hierarchy: 5 RuntimeError subclasses mirroring scripts/orchestrator/circuit_breaker.py CircuitBreakerOpenError style (structured attrs + narrative super().__init__ message). SeleniumForbidden deliberately NOT duplicated — pre_tool_use Hook owns that enforcement layer."
  - "sample_shorts.mp4 is 1 byte (b'0') rather than zero-byte because PUB-04 checksum tests need a non-empty stable sha256 digest (5feceb66...)."

patterns-established:
  - "Pattern 1: tests/phase08 is a root-level pytest package (not a Python import package) — tests consume mocks via sys.path insertion prelude (Phase 7 Plan 07-02 precedent)."
  - "Pattern 2: Mock fault injection is two-condition gated — allow_fault_injection=True AND per-method trigger (duplicate-name, missing-askpass, path-collision, _fault_mode set). Default-safe unless both conditions met."
  - "Pattern 3: Adapter-library imports (googleapiclient, httplib2) are lazy inside fault paths so Wave 0 scaffold does not require the real adapter libraries to be installed."

requirements-completed: [PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, REMOTE-01, REMOTE-02, REMOTE-03]

duration: 13min
completed: 2026-04-19
---

# Phase 8 Plan 01: Wave 0 FOUNDATION Summary

**tests/phase08/ scaffold + MockYouTube/MockGitHub doubles + scripts/publisher/ namespace with CD-02 five-class exception hierarchy — Phase 7 default-safe mock contract extended to publishing infrastructure without disturbing 986/986 regression baseline.**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-04-19T13:17:26Z
- **Completed:** 2026-04-19T13:30:39Z
- **Tasks:** 3/3 (all green)
- **Files created:** 14 (zero modifications to Phase 4/5/6/7 production code)

## Accomplishments

- 13-test scaffold gate (Task 8-01-01) — 3 package markers + 2 fixture files + 6-fixture conftest all verified, `sample_shorts.mp4` sha256 locked to `5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9`, PUB-04 4-field JSON schema invariant anchored.
- 10-test MockYouTube contract (Task 8-01-02) — D-10 + Phase 7 Correction 2 `allow_fault_injection=False` default proven, videos/thumbnails/commentThreads happy paths deterministic, two fault modes (http_500 / httplib2) with lazy adapter imports.
- 16-test MockGitHub + exceptions surface (Task 8-01-03) — POST /user/repos 422 idempotent, git_push askpass fault, submodule path-collision fault, all 5 CD-02 exceptions (`PublishLockViolation`, `PublishWindowViolation`, `AIDisclosureViolation`, `SmokeTestCleanupFailure`, `GitHubRemoteError`) importable and attribute round-trip proven.
- 39/39 Phase 8 new tests PASS in 0.12s.
- Regression preserved: 986/986 Phase 4+5+6+7 suite still green (8:25 full sweep).

## Task Commits

Each task was committed atomically via `gsd-tools commit`:

1. **Task 8-01-01: scaffold + fixtures + conftest + test_scaffold** — `5fb2d38` (feat)
2. **Task 8-01-02: MockYouTube + test_youtube_mock** — `501777d` (feat)
3. **Task 8-01-03: MockGitHub + scripts.publisher namespace + 5-class exceptions + smoke tests** — `b53d218` (feat)

**Plan metadata (this file + STATE.md + ROADMAP.md + REQUIREMENTS.md):** pending final commit.

## Files Created

- `tests/phase08/__init__.py` — package marker (empty, one blank line)
- `tests/phase08/mocks/__init__.py` — subpackage marker
- `tests/phase08/fixtures/__init__.py` — subpackage marker
- `tests/phase08/fixtures/sample_shorts.mp4` — 1-byte placeholder with deterministic sha256 for PUB-04 checksum anchor
- `tests/phase08/fixtures/sample_production_metadata.json` — canonical PUB-04 4-field schema reference (`script_seed / assets_origin / pipeline_version / checksum`)
- `tests/phase08/conftest.py` — 6 fixtures (`tmp_publish_lock`, `mock_client_secret`, `mock_youtube_credentials`, `sample_mp4_path`, `fake_env_github_token`, `kst_clock_freeze`) + UTF-8 cp949 guard + Phase 7 `_REPO_ROOT` resolve-at-import pattern
- `tests/phase08/test_scaffold.py` — 13 tests asserting scaffold integrity + fixture round-trips
- `tests/phase08/mocks/youtube_mock.py` — `MockYouTube` class + 3 sub-resource stubs (`_VideosStub`, `_ThumbnailsStub`, `_CommentThreadsStub`) with lazy fault imports
- `tests/phase08/mocks/test_youtube_mock.py` — 10 tests for default-safe contract + happy paths + fault injection gating
- `tests/phase08/mocks/github_mock.py` — `MockGitHub` class modelling REST + subprocess git surface
- `tests/phase08/mocks/test_github_mock.py` — 10 tests covering 422 idempotent + askpass + submodule collision fault modes
- `tests/phase08/test_exceptions_smoke.py` — 6 tests exercising the 5-class CD-02 hierarchy import surface + attribute round-trips
- `scripts/publisher/__init__.py` — empty namespace marker
- `scripts/publisher/_placeholder.py` — W0 placeholder (removed at Wave 3 when publish_lock.py + kst_window.py land)
- `scripts/publisher/exceptions.py` — CD-02 five-class hierarchy

## Decisions Made

- **D-13 (independent conftest) honored** — zero imports from `tests/phase05/conftest.py`, `tests/phase06/conftest.py`, or `tests/phase07/conftest.py`. `kst_clock_freeze` sanity-checks that `2026-04-20.weekday() == 0` at fixture setup time to catch stdlib drift.
- **D-10 default safety inherited from Phase 7 Correction 2** — both mocks default `allow_fault_injection=False`; fault path only activates when both that flag is True AND per-method trigger met (`_fault_mode` set, duplicate name, missing askpass, colliding submodule path).
- **CD-02 exception style** — all 5 subclasses inherit `RuntimeError` (not `Exception`) matching the `CircuitBreakerOpenError` style in `scripts/orchestrator/circuit_breaker.py`. Each carries structured attrs (`remaining_min`, `weekday/hour`, `video_id/reason`, `status_code/body`) and a narrative `super().__init__(...)` message. `SeleniumForbidden` deliberately omitted — that identifier is owned by `pre_tool_use.py` Hook enforcement and duplicating it here would fork-risk.
- **Lazy adapter imports** — `googleapiclient.errors.HttpError` and `httplib2.HttpLib2Error` are imported inside the fault path so the Wave 0 scaffold is usable on machines without those libraries installed (Waves 2+ will install them via `config/` setup).
- **1-byte not 0-byte MP4 fixture** — Phase 7 used zero-byte mock_shotstack.mp4 because no checksum test read its bytes. Phase 8 PUB-04 tests will `hashlib.sha256(mp4.read_bytes())`; a zero-byte file yields the same digest as any empty file, which is indistinguishable from an empty-read bug. 1-byte `b"0"` gives a stable, unique digest that cannot be silently produced by a buggy code path.

## Deviations from Plan

None — plan executed exactly as written. All 3 tasks shipped with the exact file list, acceptance criteria, and test shape specified in `08-01-PLAN.md`. Every `<acceptance_criteria>` bullet was verified before commit.

A few additive tests beyond the plan minimum were included as belt-and-suspenders:
- `test_scaffold.py` — added `test_kst_clock_freeze_sunday` + `test_kst_clock_freeze_rejects_invalid_weekday` (fixture full-range coverage)
- `test_youtube_mock.py` — added `test_videos_insert_increments_on_consecutive_calls` + `test_fault_injection_http_500_mode`
- `test_github_mock.py` — added `test_post_user_repos_requires_token` + `test_post_user_repos_duplicate_happy_path_without_fault_injection` + `test_git_push_default_off_tolerates_missing_askpass`
- `test_exceptions_smoke.py` — added `test_publish_window_violation_carries_weekday_hour` + `test_github_remote_error_carries_status_body` + `test_ai_disclosure_violation_is_runtimeerror`

These do not alter the contract — they lock in existing behavior already implied by the spec. Counted: 39 new tests total (plan estimate: ~24). Zero contract drift.

## Issues Encountered

- Plan `<read_first>` references `scripts/orchestrator/exceptions.py`, but that file does not exist — exception classes are co-located with their feature module (`circuit_breaker.py:57 CircuitBreakerOpenError`, `gates.py:106 OrchestratorError`, `harvest/conflict_parser.py:19 CONFLICT_MAP_COUNT_MISMATCH`). Resolved by reading `circuit_breaker.py` as the primary style anchor (RuntimeError subclass + structured attrs + narrative message). No action needed — the plan's referenced style was fully applicable and the CD-02 hierarchy shipped consistently. Recorded here only for the next executor's awareness; no correction needed in CONTEXT.

## Anchor Guarantees (carried into Wave 1+)

- `sample_shorts.mp4` sha256 = `5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9` — stable across CI runs.
- `scripts/publisher/exceptions.py` ships exactly 5 classes named per CD-02 canonical list. Adding a 6th without updating CONTEXT is a drift signal.
- No `selenium` / `webdriver` / `playwright` tokens exist in any Phase 8 file (grep count 0).
- No `skip_gates` / `TODO(next-session)` tokens exist in any Phase 8 file (grep count 0).
- `tests/phase08/conftest.py` imports nothing from `tests/phase05/conftest.py`, `tests/phase06/conftest.py`, or `tests/phase07/conftest.py` (D-13 independence).

## Next Phase Readiness

Downstream Plans 08-02..08-08 are now unblocked:

- **08-02 (Wave 1 REMOTE):** `MockGitHub` ready for `test_github_remote_create.py` + `test_github_push_main.py` + `test_submodule_add.py`. `fake_env_github_token` fixture provides `GITHUB_TOKEN` env injection.
- **08-03 (Wave 2 OAUTH):** `mock_client_secret` + `mock_youtube_credentials` fixtures ready for `test_oauth_installed_flow.py` + `test_token_refresh.py`.
- **08-04 (Wave 3 LOCK+WINDOW+DISCLOSURE):** `tmp_publish_lock` + `kst_clock_freeze` fixtures ready. `PublishLockViolation` + `PublishWindowViolation` + `AIDisclosureViolation` exception classes importable. `_placeholder.py` will be deleted by Plan 08-04 when `publish_lock.py` + `kst_window.py` land.
- **08-05 (Wave 4 METADATA+FUNNEL):** `sample_mp4_path` fixture + `sample_production_metadata.json` schema reference ready. `MockYouTube.commentThreads().insert(...)` pinned-comment contract exercised.
- **08-06 (Wave 5 SMOKE-GATE):** `MockYouTube` videos().delete contract proven via `_deleted` list assertion. `SmokeTestCleanupFailure` exception ready for the cleanup-failure path.
- **08-07 (Wave 6 E2E+REGRESSION):** 986/986 Phase 4+5+6+7 regression preserved → Phase 8 E2E will inherit a clean baseline for the full sweep.
- **08-08 (Wave 7 PHASE GATE):** TRACEABILITY matrix scaffold unaffected.

---

## Self-Check: PASSED

**Files exist:**
- FOUND: tests/phase08/__init__.py
- FOUND: tests/phase08/mocks/__init__.py
- FOUND: tests/phase08/fixtures/__init__.py
- FOUND: tests/phase08/fixtures/sample_shorts.mp4 (1 byte, sha256 5feceb66...)
- FOUND: tests/phase08/fixtures/sample_production_metadata.json (4-field schema)
- FOUND: tests/phase08/conftest.py (6 fixtures)
- FOUND: tests/phase08/test_scaffold.py (13 tests green)
- FOUND: tests/phase08/mocks/youtube_mock.py
- FOUND: tests/phase08/mocks/test_youtube_mock.py (10 tests green)
- FOUND: tests/phase08/mocks/github_mock.py
- FOUND: tests/phase08/mocks/test_github_mock.py (10 tests green)
- FOUND: tests/phase08/test_exceptions_smoke.py (6 tests green)
- FOUND: scripts/publisher/__init__.py
- FOUND: scripts/publisher/_placeholder.py
- FOUND: scripts/publisher/exceptions.py (5 classes)

**Commits exist:**
- FOUND: 5fb2d38 (Task 1 scaffold)
- FOUND: 501777d (Task 2 MockYouTube)
- FOUND: b53d218 (Task 3 MockGitHub + exceptions)

**Acceptance criteria:**
- 39/39 Phase 8 tests PASS
- 986/986 Phase 4+5+6+7 regression PRESERVED
- 5-class exception hierarchy importable
- No selenium / webdriver / playwright tokens (grep count 0)
- No skip_gates / TODO(next-session) tokens (grep count 0)

---
*Phase: 08-remote-publishing-production-metadata*
*Completed: 2026-04-19*
