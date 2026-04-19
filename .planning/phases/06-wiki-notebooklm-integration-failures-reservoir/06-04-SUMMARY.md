---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 04
subsystem: wave-2-library-registration
tags: [notebooklm, wiki-03, d-7, d-8, d-16, library-json, idempotent, utf-8, korean, external-skill-mutation]

# Dependency graph
requires:
  - phase: 06
    plan: 01
    provides: tests/phase06/conftest.py (library_json_delta fixture) + tests/phase06/fixtures/library_json_delta.json
  - phase: 06
    plan: 03
    provides: scripts.notebooklm package + __init__.py (Plan 04 adds library.py to the same package)
  - plan: 06-CONTEXT (D-4 notebook separation, D-7 reference-only, D-8 library.json append, D-16 Korean context)
  - plan: 06-RESEARCH §Area 2 (library.json schema lines 498-544, D-8 template verbatim)
  - external: shorts_naberal/.claude/skills/notebooklm/data/library.json (append target; existing 2 notebooks preserved)
provides:
  - scripts/notebooklm/library.py (173 lines — add_channel_bible_entry, load_library, dump_library, CHANNEL_BIBLE_ID, CHANNEL_BIBLE_TEMPLATE)
  - tests/phase06/test_library_json_channel_bible.py (246 lines / 15 unit tests — idempotency, D-8 schema, UTF-8 Korean, error surface, fixture alignment)
  - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/deferred-items.md (76 lines — D-04-01 URL blocker + auth-refresh contingency + D-15 measurement-only carry-over)
affects:
  - "06-05-PLAN (Fallback Chain RAGBackend Tier 0 — library.json lookup for naberal-shorts-channel-bible now resolves; subprocess failure path distinct from missing-id path)"
  - "Phase 7 E2E (first real URL substitution happens here; rerun add_channel_bible_entry with real URL; helper's idempotency preserves state)"
  - "Phase 9 deferred-items audit (D-15 SKILL line-count findings carry-over target)"

# Tech tracking
tech-stack:
  added: []  # stdlib-only (json, datetime, pathlib). No pyyaml, no notebooklm-python, no pydantic — library.json stays a plain dict.
  patterns:
    - "D-8 idempotent registration at external-skill library boundary. First call creates entry; Nth call refreshes updated_at only (+ url if changed). Caller-managed state (use_count, last_used, created_at) never clobbered by subsequent calls. Tested by test_idempotent_preserves_use_count_and_last_used: simulates downstream bump of use_count/last_used, then rerun of add_channel_bible_entry, asserts bumped values survive."
    - "D-7 path-only mutation of external repo. Module never imports from shorts_naberal — access is via absolute Path literal fed by the caller. grep -cE 'from\\s+shorts_naberal|import\\s+shorts_naberal' scripts/notebooklm/library.py == 0."
    - "D-16 Korean description preserved via ensure_ascii=False on dump_library. Korean 타겟팅 glyphs survive round-trip on disk (tested by test_korean_description_preserved_utf8: reads the written file bytes, asserts literal Korean present in raw UTF-8 text)."
    - "default-notebook pointer invariance. The helper intentionally never references active_notebook_id — grep returns 0. shorts-production-pipeline-bible remains the default; channel-bible is addressed explicitly by id at query time."
    - "Schema forward-compat. When an older library.json lacks a template field, the helper backfills it on first touch (loop over CHANNEL_BIBLE_TEMPLATE.items with isinstance(default, list) deep-copy). Prevents KeyError in downstream consumers after a schema bump."

key-files:
  created:
    - scripts/notebooklm/library.py (173 lines — idempotent channel-bible registration, stdlib-only)
    - tests/phase06/test_library_json_channel_bible.py (246 lines, 15 tests)
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/deferred-items.md (76 lines)
  modified:
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (row 6-04-01 flipped ⬜ pending -> ✅ green with file-exists ✅)
    - C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json (EXTERNAL REPO — naberal-shorts-channel-bible entry appended; existing 2 notebooks preserved byte-identical; active_notebook_id unchanged; see deferred-items.md §External-repo side-effect)

key-decisions:
  - "list fields deep-copied via list(CHANNEL_BIBLE_TEMPLATE['topics']) on first-time insertion. Avoids accidental aliasing between CHANNEL_BIBLE_TEMPLATE and the library-json entry that would let test mutations leak into the module-level constant. Verified by run-isolation: each test's tmp_path library is independent."
  - "timestamp parameter uses explicit None default with _iso_now() fallback. Tests can pin timestamps for deterministic assertions (test_add_to_library_with_only_existing_notebook uses '2026-04-19T12:00:00+00:00'); production callers get current UTC. Pattern mirrors Phase 5 checkpointer STATE #29."
  - "FileNotFoundError message embeds the missing path (f'library.json not found: {library_path}'). Tests assert regex 'library.json' against the exception message (test_nonexistent_library_path_raises). Prevents silent fallthrough in fallback-chain callers — Plan 05 Tier 0 can distinguish 'external skill not installed' (hard fail → grep wiki) from 'skill installed but notebook missing' (soft fail → retry-able)."
  - "KeyError message embeds both the missing key AND the library path (f'malformed library.json (missing notebooks key): {library_path}'). Satisfies pytest.raises(KeyError, match='notebooks') while also aiding diagnostic logs when the helper is called against a corrupted fixture."
  - "15 tests shipped vs plan target >=11. Bonuses: test_idempotent_preserves_use_count_and_last_used (explicit contract for caller-managed state), test_entry_id_matches_constant (locks id == 'naberal-shorts-channel-bible'), test_library_updated_at_refreshed (top-level updated_at tracked), test_topics_list_length_5_matches_d8 (exact list equality, not just length). Zero runtime cost (<20ms); adds regression guards to more public invariants than the plan's minimum."
  - "Applied helper against real external library.json once (external-skill side effect). Verified on disk: 3 notebooks total (existing 2 byte-identical dict equality + new channel-bible with TBD placeholder URL), active_notebook_id unchanged, Korean description literal in file bytes (not \\uXXXX). Recorded in deferred-items.md §External-repo side-effect as the only shorts_naberal repo file Phase 6 is permitted to touch (D-7 + D-8)."

patterns-established:
  - "Pattern: (load, mutate, dump) triad for external-skill data files. load_library / dump_library are public helpers so tests can seed fixtures without duplicating the json.load/json.dump boilerplate. Any future external-skill data writer (e.g., Phase 7 prefix.json syncer) should follow this shape for symmetry."
  - "Pattern: idempotent Nth-call contract. 1st call = create; Nth call same input = refresh metadata only; Nth call different input = update target field + metadata. This pattern will likely repeat in any future registry-style helper (Phase 10 pattern aggregator's candidate-file writer, Phase 8 YouTube channel metadata syncer)."
  - "Pattern: deferred-items.md as the stated-blocker ledger. D-04-01 entry demonstrates the expected shape — status / current placeholder / why deferred / unblock procedure (numbered) / impact / resolution phase. Plans 05-11 should append here when they hit similar blockers rather than inventing per-plan tracking files."

requirements-completed: []  # WIKI-03 was already ticked by Plan 03; Plan 04 reinforces it but does not add a new REQ.

# Metrics
duration: ~5m
completed: 2026-04-19
---

# Phase 6 Plan 04: Wave 2 LIBRARY REGISTRATION Summary

**`scripts.notebooklm.library.add_channel_bible_entry` ships as the idempotent registration helper for the D-8 `naberal-shorts-channel-bible` notebook. The external skill's `library.json` now carries 3 entries (existing 2 byte-identical + channel-bible placeholder). D-7 preserved: zero cross-imports from shorts_naberal. Korean description survives UTF-8 round-trip. 15 tests green (11 plan-target + 4 bonus regression guards). Real URL substitution deferred to 대표님 action, tracked in `deferred-items.md` with a numbered unblock procedure. Plan 05 Fallback Chain `RAGBackend` Tier 0 library lookup now resolves.**

## Performance

- **Duration:** ~5 min
- **Tasks:** 2 / 2 complete (TDD RED → GREEN → REFACTOR not needed — helper was minimal)
- **Files created:** 3 (1 helper module + 1 test file + 1 deferred-items tracker)
- **Files modified (studios/shorts):** 1 (06-VALIDATION.md row 6-04-01 flipped)
- **Files modified (external shorts_naberal):** 1 (library.json D-8 append — tracked in deferred-items.md)
- **Tests added:** 15 (all green on first GREEN run; no iteration needed)
- **Phase 5 regression:** 329/329 PASS
- **Phase 6 full suite:** 72/72 PASS (15 Plan 01 + 21 Plan 02 + 21 Plan 03 + 15 Plan 04)

## Accomplishments

### Task 1 (TDD) — `scripts/notebooklm/library.py` (commits `38fb098` RED + `b6df271` GREEN)

**RED phase** (`38fb098`): `tests/phase06/test_library_json_channel_bible.py` (246 lines, 15 tests) with `ModuleNotFoundError: No module named 'scripts.notebooklm.library'` collect-time failure — true RED.

**GREEN phase** (`b6df271`): `scripts/notebooklm/library.py` (173 lines) shipping:
- `CHANNEL_BIBLE_ID = "naberal-shorts-channel-bible"` (D-8)
- `CHANNEL_BIBLE_TEMPLATE` — 12-field dict verbatim from RESEARCH §Area 2 lines 528-544: id, url (`TBD-url-await-user`), name (`Naberal Shorts Channel Bible`), description (Korean verbatim), topics (5 items), content_types=[], use_cases=[], tags=[], created_at=None, updated_at=None, use_count=0, last_used=None.
- `_iso_now()` — UTC ISO 8601 seconds precision.
- `load_library(Path) -> dict` — raises FileNotFoundError with path in message.
- `dump_library(Path, dict) -> None` — `indent=2, ensure_ascii=False`, trailing newline.
- `add_channel_bible_entry(library_path, url="TBD-url-await-user", timestamp=None) -> dict`:
  - Raises FileNotFoundError if skill library.json missing.
  - Raises KeyError with path + 'notebooks' in message if malformed.
  - First call: deep-copies template lists, sets url/created_at/updated_at=now, inserts entry.
  - Nth call: backfills any missing template keys (forward-compat), updates url only if changed, refreshes updated_at. **Never clobbers** created_at / use_count / last_used.
  - Refreshes `library["updated_at"]` top-level marker.
  - **Never references** `active_notebook_id` (grep-verified: 0 occurrences).
  - Writes via dump_library, returns the post-update dict.

**Acceptance criteria PASS (Task 1):**
- `python -c "from scripts.notebooklm.library import add_channel_bible_entry, CHANNEL_BIBLE_ID, CHANNEL_BIBLE_TEMPLATE; assert CHANNEL_BIBLE_ID == 'naberal-shorts-channel-bible'; assert '한국' in CHANNEL_BIBLE_TEMPLATE['description']; print('OK')"` → OK ✅
- `grep -c "def add_channel_bible_entry" scripts/notebooklm/library.py` = 1 ✅
- `grep -c "ensure_ascii=False" scripts/notebooklm/library.py` = 3 (>=1) ✅
- `grep -c "naberal-shorts-channel-bible" scripts/notebooklm/library.py` = 2 (>=1) ✅
- `grep -c "active_notebook_id" scripts/notebooklm/library.py` = 0 ✅
- `grep -cE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/library.py` = 0 (D-7) ✅
- `grep -c "한국 시니어 타겟팅" scripts/notebooklm/library.py` = 1 (>=1) ✅

### Task 2 — Tests + deferred-items.md (commit `4ffa9ee` for deferred-items; tests were committed in `38fb098` RED)

**`tests/phase06/test_library_json_channel_bible.py` (246 lines, 15 tests):**

1. `test_add_to_library_with_only_existing_notebook` — 1st call creates entry + preserves existing notebook dict-equal.
2. `test_idempotent_same_url_preserves_created_at` — 2nd call same url refreshes updated_at only.
3. `test_different_url_updates_url_preserves_created_at` — url change updates url + updated_at, preserves created_at.
4. `test_idempotent_preserves_use_count_and_last_used` — caller-managed state survives Nth call.
5. `test_active_notebook_id_not_changed` — default pointer invariance.
6. `test_korean_description_preserved_utf8` — UTF-8 round-trip literal Korean on disk.
7. `test_missing_notebooks_key_raises` — KeyError with 'notebooks' in message.
8. `test_nonexistent_library_path_raises` — FileNotFoundError with 'library.json' in message.
9. `test_schema_shape_of_new_entry` — exact 12-key set.
10. `test_topics_list_length_5_matches_d8` — exact topics list equality (not just length).
11. `test_use_count_starts_zero_last_used_null` — fresh state + on-disk null verification.
12. `test_second_call_does_not_duplicate_key` — exactly 2 notebooks after 2 calls.
13. `test_entry_id_matches_constant` — internal id == CHANNEL_BIBLE_ID constant.
14. `test_fixture_delta_matches_template` — consumes library_json_delta fixture, asserts template-key alignment.
15. `test_library_updated_at_refreshed` — top-level updated_at tracked.

**`.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/deferred-items.md` (76 lines):**
- **D-04-01: NotebookLM channel-bible notebook URL** — full numbered unblock procedure (6 steps, including the one-liner Claude-callable `python -c` snippet) + impact statement + resolution-phase guidance (Phase 6 or Phase 7).
- **External-repo side-effect: shorts_naberal library.json mutation** — explicit disclosure that D-8 append touches the external repo's library.json; this is the only permitted touch per D-7 + D-8; existing 2 notebooks + active_notebook_id untouched.
- **D-15 SKILL.md line-count audit findings** — measurement-only carry-over to Phase 9.
- **NotebookLM browser_state expiry** — auth-refresh contingency with unblock procedure.

**Acceptance criteria PASS (Task 2):**
- `pytest tests/phase06/test_library_json_channel_bible.py -q --no-cov` → `15 passed` ✅
- `grep -cE "^def test_" tests/phase06/test_library_json_channel_bible.py` = 15 (>=11) ✅
- `test -f .planning/phases/.../deferred-items.md` → exists ✅
- `grep -c "TBD-url-await-user" deferred-items.md` = 1 (>=1) ✅
- `grep -c "D-04-01" deferred-items.md` = 1 (>=1) ✅

## External Library.json State After Plan 04

The D-8 mutation of `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json` produced:

```
notebooks keys: ['crime-stories-+-typecast-emotion', 'naberal-shorts-channel-bible', 'shorts-production-pipeline-bible']
channel-bible url: TBD-url-await-user
active_notebook_id: shorts-production-pipeline-bible
channel-bible created_at: 2026-04-19T07:44:31+00:00
```

Verified on disk (visual inspection of `shorts_naberal/.claude/skills/notebooklm/data/library.json`):
- Lines 3-28: `shorts-production-pipeline-bible` — byte-identical to pre-Plan-04 state (all 12 fields + 11 topics + Korean description preserved).
- Lines 29-49: `crime-stories-+-typecast-emotion` — byte-identical (6 topics + Korean description preserved).
- Lines 50-69: `naberal-shorts-channel-bible` — NEW D-8 entry, URL=`TBD-url-await-user`, topics=5 per D-8, Korean description literal.
- Line 71: `active_notebook_id: shorts-production-pipeline-bible` — unchanged.

## D-7 Cross-Import Audit

```
$ grep -rnE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/library.py tests/phase06/test_library_json_channel_bible.py
# 0 hits
```

`scripts/notebooklm/library.py` references the external skill's library.json path via a literal Path argument supplied by the caller. No package-level coupling.

## pytest Output

```
$ python -m pytest tests/phase06/test_library_json_channel_bible.py -q --no-cov
15 passed in 0.11s

$ python -m pytest tests/phase06/ -q --no-cov
72 passed in 0.34s

$ python -m pytest tests/phase05/ -q --no-cov
329 passed in 17.52s
```

Phase 6 breakdown:
- Plan 01 (Wave 0 FOUNDATION): 15 tests
- Plan 02 (Wave 1 WIKI CONTENT): 21 tests
- Plan 03 (Wave 2 NOTEBOOKLM WRAPPER): 21 tests
- Plan 04 (Wave 2 LIBRARY REGISTRATION): **15 tests** — THIS PLAN

Grand total: Phase 5 (329) + Phase 6 (72) = **401 tests green**.

## Task Commits

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 RED | 15 failing tests | `38fb098` | tests/phase06/test_library_json_channel_bible.py (246 lines) |
| 1 GREEN | library.py helper | `b6df271` | scripts/notebooklm/library.py (173 lines) |
| 2 | deferred-items.md | `4ffa9ee` | .planning/phases/06-.../deferred-items.md (76 lines) |

Plan metadata commit (SUMMARY + STATE + ROADMAP + VALIDATION): pending (final step).

## Decisions Made

See `key-decisions` in frontmatter. Highlights:

- **list fields deep-copied on first insert** — prevents aliasing between template constant and entry dict. Run-isolated tests confirm.
- **Explicit timestamp parameter with _iso_now() fallback** — enables deterministic unit tests without monkeypatching datetime.
- **FileNotFoundError / KeyError messages embed the library path** — gives Plan 05 Fallback Chain Tier 0 the diagnostic to distinguish "skill not installed" from "skill installed but notebook missing".
- **15 tests vs plan target >=11** — 4 bonus regression guards at zero runtime cost.
- **Applied helper against real external library.json once** — reduces Plan 05 risk of integration surprise; external side effect explicitly disclosed in deferred-items.md.

## Deviations from Plan

None. Plan executed exactly as written. No Rule 1-4 deviations triggered.

Notes on plan compliance:
- Plan TDD flag `tdd="true"` honored: RED commit (`38fb098`) with failing tests landed before GREEN commit (`b6df271`) with implementation.
- Plan task 2 called for tests + deferred-items.md in a single logical task; tests were committed inside the RED phase (per TDD convention) and deferred-items.md was committed separately for atomicity. Net result: same files shipped, atomic commits preserved.
- REFACTOR phase was skipped — the GREEN helper was already minimal (173 lines, no duplication, no dead paths).

## Authentication Gates

None reached during Plan 04. The helper mutates library.json on disk via stdlib I/O only — no network, no Playwright, no auth.

The **potential** authentication gate (real URL substitution + first live query verification) is explicitly deferred to 대표님 action and documented in deferred-items.md §D-04-01. That gate surfaces in Plan 05 (Fallback Chain first live query) or Phase 7 E2E (mock pipeline integration) — whichever runs first with the real URL available.

## Verification Evidence

### Plan-required verification suite (§verification block lines 417-422)

1. **pytest Plan 04 tests:**
   ```
   $ python -m pytest tests/phase06/test_library_json_channel_bible.py -q --no-cov
   15 passed in 0.11s
   ```
2. **Module import:**
   ```
   $ python -c "from scripts.notebooklm.library import add_channel_bible_entry, CHANNEL_BIBLE_ID; from pathlib import Path; print('OK')"
   OK
   ```
3. **active_notebook_id grep (must be 0):**
   ```
   $ grep -c "active_notebook_id" scripts/notebooklm/library.py
   0
   ```
4. **deferred-items.md TBD-url-await-user grep:**
   ```
   $ grep -c "TBD-url-await-user" .planning/phases/06-.../deferred-items.md
   1
   ```

All 4 verification steps pass.

### Plan acceptance criteria

| Criterion | Result |
|-----------|--------|
| `python -c "import scripts.notebooklm.library"` exits 0 | PASS |
| `def add_channel_bible_entry` count = 1 | PASS |
| `ensure_ascii=False` count >= 1 | PASS (=3) |
| `naberal-shorts-channel-bible` count >= 1 | PASS (=2) |
| `active_notebook_id` count = 0 | PASS |
| shorts_naberal import pattern = 0 (D-7) | PASS |
| Korean '한국 시니어 타겟팅' count >= 1 | PASS (=1) |
| pytest Plan 04 tests exit 0 | PASS |
| test def count in Plan 04 test file >= 11 | PASS (=15) |
| deferred-items.md exists | PASS |
| TBD-url-await-user in deferred-items.md >= 1 | PASS (=1) |
| D-04-01 in deferred-items.md >= 1 | PASS (=1) |
| 06-VALIDATION.md row 6-04-01 flipped green | PASS |

## Known Stubs

None. Every created file contains substantive production code or genuine assertions:

- `scripts/notebooklm/library.py` (173 lines) — full idempotent helper with load/dump/add, no placeholders, no TODOs, no bare `pass` bodies.
- `tests/phase06/test_library_json_channel_bible.py` (246 lines) — 15 real assertions, no skipped or stubbed tests.
- `deferred-items.md` (76 lines) — documents real blockers with numbered unblock procedures. The `TBD-url-await-user` placeholder in the helper is **intentional and explicitly tracked** as D-04-01; its resolution is the 대표님 Google NotebookLM console action. Not a stub — it's a deferred-ideas item per CONTEXT §Deferred Ideas line 207.

Zero `TODO`, `FIXME`, `not implemented`, `pass`-only function bodies, `skip_gates`, `TODO(next-session)`, or lowercase `t2v` tokens in any new file.

## Deferred Issues

**1 explicit deferred item recorded (not a Plan 04 failure — a scoped-out dependency).**

- **D-04-01:** Real NotebookLM URL substitution awaits 대표님 action. Helper ships with `TBD-url-await-user` placeholder; idempotency contract ensures the real-URL call is a no-risk refresh when it arrives. Tracked in `deferred-items.md` with 6-step unblock procedure. Resolution phase: Phase 6 execute or Phase 7 E2E.

## Next Plan Readiness

**Plan 05 (Wave 2 Fallback Chain) unblocked:**
- `scripts.notebooklm.library.CHANNEL_BIBLE_ID` is the canonical notebook identifier for `RAGBackend` Tier 0. Fallback chain imports it as a constant (no hardcoded string duplication).
- External library.json now carries the entry, so any future `library.load_library(path)["notebooks"]["naberal-shorts-channel-bible"]` lookup succeeds with the placeholder URL — distinguishes "notebook not registered" from "notebook registered but URL placeholder" at Tier 0 diagnostic layer.
- `add_channel_bible_entry` is reusable by Plan 05 tests that need to seed a fake library.json with the channel-bible entry.

**Plan 06 (Wave 3 ContinuityPrefix pydantic schema) unblocked:**
- No direct dependency — Plan 06 builds `scripts/orchestrator/api/models.py::ContinuityPrefix` from scratch. Plan 04's library work is orthogonal.

**Recommended next action:** `/gsd:execute-phase 6` to advance to Plan 05 Wave 2 Fallback Chain.

## Self-Check: PASSED

Verified on disk:
- `scripts/notebooklm/library.py` — FOUND (173 lines, `def add_channel_bible_entry` + `CHANNEL_BIBLE_ID` + `CHANNEL_BIBLE_TEMPLATE` + Korean description literal)
- `tests/phase06/test_library_json_channel_bible.py` — FOUND (246 lines, 15 test defs)
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/deferred-items.md` — FOUND (76 lines, D-04-01 + external-repo disclosure + D-15 + auth-refresh sections)
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md` — MODIFIED (row 6-04-01 flipped ✅ green)
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json` — MODIFIED (3 notebooks now; existing 2 byte-identical; active_notebook_id unchanged)

Verified in git log:
- `38fb098` (Task 1 RED — failing tests) — FOUND via `git log --oneline`
- `b6df271` (Task 1 GREEN — library.py helper) — FOUND via `git log --oneline`
- `4ffa9ee` (Task 2 — deferred-items.md) — FOUND via `git log --oneline`

Verified at runtime:
- `python -c "from scripts.notebooklm.library import add_channel_bible_entry, CHANNEL_BIBLE_ID, CHANNEL_BIBLE_TEMPLATE; print('OK')"` → OK
- `pytest tests/phase06/test_library_json_channel_bible.py -q --no-cov` → 15 passed
- `pytest tests/phase06/ -q --no-cov` → 72 passed (15 Plan 01 + 21 Plan 02 + 21 Plan 03 + 15 Plan 04)
- `pytest tests/phase05/ -q --no-cov` → 329 passed (regression preserved)
- `grep -rnE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/library.py` → 0 hits (D-7 preserved)
- `grep -c "active_notebook_id" scripts/notebooklm/library.py` → 0 (helper never touches the default)
- No drift tokens in new files (skip_gates / TODO(next-session) / lowercase-t2v / text_to_video / text2video / segments[] — 0 hits)

**Phase 6 Plan 04 complete. Wave 2 LIBRARY REGISTRATION shipped. Ready for Plan 05 Wave 2 Fallback Chain.**

---
*Phase: 06-wiki-notebooklm-integration-failures-reservoir*
*Plan: 04 (Wave 2 LIBRARY REGISTRATION)*
*Completed: 2026-04-19*
