# Phase 9 — Deferred Items

## D08-DEF-01 (inherited, pre-existing)

**Scope:** Combined sweep `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co` fails collection on `tests/phase08/mocks/test_*_mock.py` cross-phase import (`ModuleNotFoundError: No module named 'mocks.youtube_mock'`). 6 ERRORs, exit code 2.

**Verified pre-existing:** Same error count + same 1134 tests collected on commit `9916114` (pre-Task 9-00-03) — Phase 9 Wave 0 added zero production code.

**Reference:** Logged in STATE.md by Plan 08-03 / Plan 08-04 deviation notes on 2026-04-19.

**Action for Phase 9:** OUT OF SCOPE per deviation Rule scope boundary. Individual phase collection works:
- Phase 4: 244 tests
- Phase 5: 329 tests
- Phase 6: 236 tests
- Phase 7: 177 tests
- Phase 8: 205 tests (isolated collection is clean; cross-phase mocks/ import is the only failure mode)

**Resolution owner:** Phase 8 follow-up (not Phase 9). Possible fix: add `tests/__init__.py` or adjust `sys.path` in `tests/phase08/mocks/` per Plan 07-02 sys.path[0] insertion pattern.
