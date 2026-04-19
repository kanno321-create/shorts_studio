# Phase 8 Deferred Items

Pre-existing issues discovered out-of-scope of the current plan execution. Tracked for later remediation.

## 2026-04-19 (Plan 08-03 execution)

### D08-DEF-01 — `tests/phase08/mocks/test_*_mock.py` collection fails on cross-phase sweep

- **Discovered during**: Plan 08-03 full-regression sweep
  (`pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08`)
- **Symptom**: `ModuleNotFoundError: No module named 'mocks.github_mock'` +
  `ModuleNotFoundError: No module named 'mocks.youtube_mock'` during collection.
- **Root cause**: The Wave 0 (Plan 08-01) `tests/phase08/mocks/test_*_mock.py`
  files use the Phase 7 `from mocks.X import Y` convention + `sys.path.insert(0, ...)`
  prelude. That pattern only resolves when pytest collects from within
  `tests/phase08/` (rootdir-relative). Cross-phase invocation (including
  `tests/phase04..07`) fails because the sys.path hack runs after collection
  has already begun resolving imports relative to a different rootdir.
- **Scope**: Pre-existing — NOT introduced by Plan 08-03. Reproduced with
  `git stash && pytest ...` (no local changes).
- **Impact**: Phase 8 isolated sweep (`pytest tests/phase08`) still green
  (59/59). Only cross-phase sweep affected.
- **Resolution path**: Either (a) add a `tests/__init__.py` + refactor
  `from mocks.X` → `from tests.phase08.mocks.X`, or (b) add a conftest-level
  `pytest_collection_modifyitems` that skips mock-tests when rootdir is not
  tests/phase08. Defer to a dedicated infra plan (candidate: late Wave 5
  housekeeping or a Phase 9 item).
- **Owner**: not-assigned (Phase 8 gate follow-up).
