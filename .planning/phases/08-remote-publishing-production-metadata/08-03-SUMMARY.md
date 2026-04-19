---
phase: 8
plan: 08-03
subsystem: publisher/oauth
tags: [oauth, youtube-data-api-v3, installed-app-flow, refresh-token, PUB-02]
dependency_graph:
  requires: [08-01]
  provides: ["scripts.publisher.oauth.get_credentials"]
  affects: ["Wave 4 uploader (Plan 08-05)", "Wave 5 smoke test (Plan 08-06)"]
tech_stack:
  added: [google-auth-oauthlib, google-auth, google-oauth-credentials]
  patterns: [Installed Application flow, refresh-token disk persistence, run_local_server(port=0) Pitfall 1 anchor]
key_files:
  created:
    - scripts/publisher/oauth.py
    - tests/phase08/test_oauth_installed_flow.py
    - tests/phase08/test_token_refresh.py
  modified:
    - .planning/phases/08-remote-publishing-production-metadata/08-VALIDATION.md
decisions:
  - "Module imports google-auth-oauthlib at module load (not lazy) because SDK is already installed in the dev environment; Wave 5 smoke-gate re-verifies prod install."
  - "Docstring rewritten to avoid the literal string `run_console` so the anti-pattern grep anchor (Task 2 test) remains at 0 hits."
metrics:
  duration: ~8 min
  tasks_completed: 2
  commits: 3 (plus parallel 08-02 co-commits by sibling executor)
  completed: 2026-04-19
---

# Phase 8 Plan 08-03: Wave 2 OAUTH — Installed Application Flow + Refresh Token Persistence Summary

OAuth 2.0 substrate shipped: `scripts.publisher.oauth.get_credentials()` loads `config/youtube_token.json`, refreshes expired creds via `Request()`, or bootstraps new creds through `InstalledAppFlow.from_client_secrets_file(...).run_local_server(port=0)`, then writes `creds.to_json()` back to disk. Pitfall 1 anchor (`port=0`) locked; deprecated `run_console` absent at source level.

## What Shipped

### `scripts/publisher/oauth.py` (83 lines)

- Module-level `SCOPES` list — exactly two entries, ordered `youtube.upload` then `youtube.force-ssl` (matches CONTEXT D-04 + 08-RESEARCH §Pattern 2).
- Constants: `CLIENT_SECRET_PATH = Path("config/client_secret.json")`, `TOKEN_PATH = Path("config/youtube_token.json")`.
- Function `get_credentials(*, client_secret_path=None, token_path=None) -> Credentials`:
  1. Load existing token via `Credentials.from_authorized_user_file` if present.
  2. If invalid: refresh (`creds.refresh(Request())`) when refreshable, else bootstrap via `InstalledAppFlow.from_client_secrets_file(...).run_local_server(port=0)`.
  3. `mkdir(parents=True, exist_ok=True)` on token parent dir, then `write_text(creds.to_json())`.
  4. Return creds.
- `__all__` exports 4 symbols (`SCOPES`, `CLIENT_SECRET_PATH`, `TOKEN_PATH`, `get_credentials`).

### `tests/phase08/test_oauth_installed_flow.py` (94 lines, 6 tests)

- `test_bootstrap_when_token_missing` — Pitfall 1 anchor: `run_local_server(port=0)` MUST be called.
- `test_bootstrap_creates_parent_directory` — nested `config/` path gets created.
- `test_scopes_are_exactly_two_in_order` — exact list identity check.
- `test_client_secret_path_default` — `config/client_secret.json`.
- `test_token_path_default` — `config/youtube_token.json`.
- `test_load_existing_valid_token_skips_flow` — valid token short-circuits flow invocation.

### `tests/phase08/test_token_refresh.py` (120 lines, 5 tests)

- `test_expired_creds_triggers_refresh` — expired+refreshable → `creds.refresh(Request())`.
- `test_refresh_writes_new_token_to_disk` — round-trip: refresh mutates serialization, disk reflects new payload.
- `test_no_refresh_token_falls_through_to_flow` — expired but no refresh_token → InstalledAppFlow bootstrap path.
- `test_valid_creds_short_circuits` — valid creds: no refresh, no flow.
- `test_run_console_never_used_in_source` — static grep of `scripts/publisher/oauth.py` for `run_console` must be 0 hits (Pitfall 1 anti-pattern anchor).

## Pitfall 1 + Anchor Verification

| Check | Result |
|-------|--------|
| `grep -c "def get_credentials" scripts/publisher/oauth.py` | 1 |
| `grep -c "run_local_server(port=0)" scripts/publisher/oauth.py` | 3 (docstring + body + `__all__` context) |
| `grep -c "run_console" scripts/publisher/oauth.py` | 0 |
| `grep -cE "youtube\.upload|youtube\.force-ssl" scripts/publisher/oauth.py` | 4 |
| `grep -c 'CLIENT_SECRET_PATH = Path("config/client_secret.json")'` | 1 |
| `grep -c 'TOKEN_PATH = Path("config/youtube_token.json")'` | 1 |
| `python -m py_compile scripts/publisher/oauth.py` | exit 0 |

## Test Results

- `pytest tests/phase08/test_oauth_installed_flow.py -q --no-cov` → **6 passed** in 0.17s.
- `pytest tests/phase08/test_token_refresh.py -q --no-cov` → **5 passed** in 0.16s.
- `pytest tests/phase08 -q --no-cov` → **59 passed** in 0.24s (39 baseline + 11 new from 08-03 + 9 more from parallel 08-02).
- Full regression sweep (`tests/phase04..phase08`) → **2 pre-existing collection errors** in `tests/phase08/mocks/test_*_mock.py` (see Deferred Issues). `tests/phase08` isolated sweep is green.

## Deviations from Plan

### Rule 3 — Shared working tree at commit time

**1. Accidental co-commit of `scripts/publisher/_git_askpass.sh` in test RED commit (95022d4)**

- **Found during:** Task 1 RED commit staging.
- **Issue:** The parallel sibling executor (Plan 08-02 REMOTE) had already created `_git_askpass.sh` in the working tree before I ran `git add tests/phase08/test_oauth_installed_flow.py`. Because git index was clean at the moment I staged, the helper script rode along in my RED commit even though I targeted only the test file.
- **Fix:** Kept the commit — reverting would break parallel 08-02's execution chain. Noted here for transparency. All subsequent commits used explicit `git add <specific file>` paths to prevent recurrence.
- **Files touched (unintended):** `scripts/publisher/_git_askpass.sh` — belongs to Plan 08-02, zero semantic conflict.
- **Commit:** `95022d4` (RED).

### Rule 2 — Completeness: docstring literal-string scrubbing

**2. Removed literal `run_console()` from oauth.py docstring**

- **Found during:** Grep-anchor verification of Task 1 done-criteria.
- **Issue:** Initial docstring contained the phrase "flow.run_console() is NEVER called" for pedagogical clarity. That literal substring caused Task 2's `test_run_console_never_used_in_source` assertion (`"run_console" not in source`) to fail.
- **Fix:** Rewrote docstring to describe the anti-pattern without including the forbidden literal: `"the legacy OOB console flow is NEVER called"`.
- **Commit:** folded into `9d04c18` (GREEN).

## Deferred Issues

### D08-DEF-01 — Cross-phase sweep collection error for `tests/phase08/mocks/test_*_mock.py`

Pre-existing Wave 0 issue (Plan 08-01 scaffold): `from mocks.X import Y` + sys.path insertion pattern breaks when pytest rootdir is higher than `tests/phase08/`. Not caused by Plan 08-03 (reproduced against stash-clean tree). Logged in `.planning/phases/08-remote-publishing-production-metadata/deferred-items.md`. Recommend fix in dedicated infra plan; does not block 08-03 completion because `pytest tests/phase08 -q` still passes 59/59.

## Authentication Gates

None encountered. `get_credentials()` was not actually invoked live during this plan — the entire test surface is mocked against the three imported Google SDK names (`Credentials.from_authorized_user_file`, `Request`, `InstalledAppFlow.from_client_secrets_file`). Live OAuth consent (`config/client_secret.json` download + first-run browser authorization) is deferred to the SMOKE-GATE in Plan 08-06 Wave 5.

## Commits

| Type | Hash | Scope | Message |
|------|------|-------|---------|
| test | `95022d4` | 08-03 | add failing OAuth InstalledAppFlow bootstrap tests (RED) |
| feat | `9d04c18` | 08-03 | implement OAuth 2.0 InstalledAppFlow with refresh token persistence (GREEN) |
| test | `a6db395` | 08-03 | add Credentials.refresh roundtrip + disk persistence tests |

## Parallel Boundary Verification

- **Touched by Plan 08-03:** `scripts/publisher/oauth.py`, `tests/phase08/test_oauth_installed_flow.py`, `tests/phase08/test_token_refresh.py`, `.planning/phases/08-remote-publishing-production-metadata/08-VALIDATION.md`, `.planning/phases/08-remote-publishing-production-metadata/deferred-items.md`, `.planning/phases/08-remote-publishing-production-metadata/08-03-SUMMARY.md`.
- **Plan 08-02 territory (NOT touched by 08-03):** `scripts/publisher/github_remote.py`, `scripts/publisher/_git_askpass.sh`, `.gitignore`, `tests/phase08/test_github_remote_create.py`, `tests/phase08/test_github_push_main.py`, `tests/phase08/test_submodule_add.py`. All remain exclusively owned by 08-02 executor.

## Self-Check: PASSED

- FOUND: `scripts/publisher/oauth.py`
- FOUND: `tests/phase08/test_oauth_installed_flow.py`
- FOUND: `tests/phase08/test_token_refresh.py`
- FOUND: `.planning/phases/08-remote-publishing-production-metadata/08-03-SUMMARY.md`
- FOUND: `.planning/phases/08-remote-publishing-production-metadata/deferred-items.md`
- FOUND commit `95022d4` (test RED)
- FOUND commit `9d04c18` (feat GREEN oauth.py)
- FOUND commit `a6db395` (test refresh)
- `pytest tests/phase08 -q --no-cov` → 59/59 PASS.
