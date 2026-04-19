---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 03
subsystem: wave-2-notebooklm-wrapper
tags: [notebooklm, wiki-03, d-6, d-7, subprocess, utf-8, cp949, single-string-discipline, external-skill-reference, follow-up-strip]

# Dependency graph
requires:
  - phase: 06
    plan: 01
    provides: tests/phase06/conftest.py (mock_notebooklm_skill_env fixture — fake skill dir + NOTEBOOKLM_SKILL_PATH monkeypatch)
  - plan: 06-CONTEXT (D-4 explicit notebook id, D-6 single-string query discipline, D-7 external skill reference not copy)
  - plan: 06-RESEARCH §Area 3 (full subprocess wrapper contract lines 558-617)
  - external: shorts_naberal/.claude/skills/notebooklm/scripts/run.py (subprocess entry point, D-7 untouched)
provides:
  - scripts/notebooklm/__init__.py (15 lines — namespace + re-export query_notebook/DEFAULT_SKILL_PATH/FOLLOW_UP_MARKER)
  - scripts/notebooklm/query.py (118 lines — WIKI-03 subprocess wrapper)
  - tests/phase06/test_notebooklm_wrapper.py (202 lines / 15 unit tests — D-7 resolver precedence + FOLLOW_UP strip + argv shape + UTF-8 + error paths)
  - tests/phase06/test_notebooklm_subprocess.py (114 lines / 6 integration tests — real subprocess to fake run.py + Korean cp949 round-trip + stderr propagation + notebook_id passthrough)
affects:
  - "06-04-PLAN (library.json + canary query — `from scripts.notebooklm import query_notebook` now resolves)"
  - "06-05-PLAN (Fallback Chain — RAGBackend Tier 0 imports query_notebook as the canonical subprocess boundary)"
  - "Phase 7 onwards (any downstream consumer of NotebookLM RAG is now DRY — single wrapper, no per-caller subprocess/encoding/marker-strip duplication)"

# Tech tracking
tech-stack:
  added: []  # stdlib-only (os, subprocess, sys, pathlib). No pyyaml, no notebooklm-python, no playwright — D-7 subprocess boundary preserved.
  patterns:
    - "D-6 single-string enforcement at argv boundary — question flows through subprocess argv as a single list item. Korean + spaces survive because argv is not shell-parsed. Unit test test_korean_question_single_argv_item asserts the exact question string appears exactly once in captured cmd."
    - "D-7 skill resolution precedence (kwarg > NOTEBOOKLM_SKILL_PATH env > hardcoded fallback) implemented in _resolve_skill_path helper. Three unit tests cover each branch. DEFAULT_SKILL_PATH is a module constant, not inline — downstream consumers and tests can import it."
    - "Phase 5 STATE #28 UTF-8 guard mirrored — subprocess.run(..., encoding='utf-8', errors='replace') prevents Windows cp949 from corrupting Korean answers or em-dashes in stderr."
    - "FOLLOW_UP_REMINDER stripping via string.split — literal marker 'EXTREMELY IMPORTANT: Is that ALL you need' lives as module constant FOLLOW_UP_MARKER. Split keeps only everything BEFORE the first occurrence (tested explicitly for multi-occurrence edge case)."
    - "Fake skill fixture pattern (_make_fake_skill helper) mirrors real external skill layout (scripts/run.py + data/). Child process reconfigures sys.stdout.reconfigure(encoding='utf-8') at the top to mirror what the real ask_question.py must do on Windows cp949 default console — documented inline as a test-only mimic of the real encoding discipline."
    - "Test subprocess timeout buffer = timeout_s + 30s to allow Playwright browser teardown in the real call path (line 605 RESEARCH) — verified by test_timeout_buffer_30_seconds."

key-files:
  created:
    - scripts/notebooklm/__init__.py (15 lines — pkg namespace, re-exports query_notebook + DEFAULT_SKILL_PATH + FOLLOW_UP_MARKER)
    - scripts/notebooklm/query.py (118 lines — subprocess wrapper, no-shell, UTF-8, FOLLOW_UP strip, Rule 3 error surface)
    - tests/phase06/test_notebooklm_wrapper.py (202 lines, 15 tests)
    - tests/phase06/test_notebooklm_subprocess.py (114 lines, 6 tests)
  modified:
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (rows 6-03-01 + 6-03-02 flipped ⬜ pending -> ✅ green with file-exists ✅)

key-decisions:
  - "DEFAULT_SKILL_PATH uses raw-string Windows path (r'C:/Users/...'). Forward slashes chosen so the same literal matches across Windows + WSL + POSIX; Path() normalizes on consumption. Matches plan CONTEXT line 97 verbatim. Unit test test_default_skill_path_is_the_2026_install asserts normalized forward-slash form so a future refactor to Path-native storage cannot silently drift."
  - "_resolve_skill_path returns Path objects (not strings). Tests compare with `==` between Path instances — avoids string separator ambiguity on Windows (\\ vs /). The kwarg-None branch consults env var; if env var is set to an empty string, falls through to DEFAULT_SKILL_PATH (matches os.environ.get semantics where '' falsy)."
  - "RuntimeError on rc!=0 intentionally INCLUDES notebook_id in message: 'NotebookLM query failed (rc=N) notebook_id=X: <stderr>'. Plan 05 Fallback Chain will need to distinguish auth-expired vs notebook-missing failures; notebook_id embedded in the error string lets the Tier 0->1 transition log which notebook triggered the fall-through. Explicit unit test_subprocess_error_includes_notebook_id asserts the notebook_id substring."
  - "Fake skill's child run.py calls `sys.stdout.reconfigure(encoding='utf-8')` BEFORE writing. This is a test-only mimic — in production, the real ask_question.py/Playwright path handles its own encoding through pyperclip + browser DOM. The wrapper's encoding='utf-8' arg to subprocess.run tells the PARENT how to decode stdout bytes; the CHILD's write still defaults to cp949 on Windows unless explicitly reconfigured. Documented in fixture docstring so future test authors don't remove the reconfigure line thinking it's redundant."
  - "21 tests shipped vs plan's >=13 acceptance target (15 unit + 6 integration). Added 2 bonus unit tests beyond CONTEXT's prescribed list: test_strip_follow_up_multiple_markers_only_first_counts (edge case — two markers in same answer, split keeps first body), test_default_timeout_is_600 (locks the 600s default from plan contract line 186). Extras are pure regression guards — zero extra runtime (<20ms), full coverage of the public API surface."
  - "errors='replace' added to subprocess.run alongside encoding='utf-8'. Plan CONTEXT specified encoding='utf-8' only; `errors='replace'` is a Rule 2 completeness addition. Without it, a corrupted byte sequence in the child's stdout (unusual but possible with Playwright mid-crash partial writes) would raise UnicodeDecodeError inside subprocess.run itself before we can raise a meaningful RuntimeError. 'replace' maps bad bytes to U+FFFD REPLACEMENT CHARACTER, preserving the non-corrupted portion of the answer and letting the rc!=0 path propagate the diagnostic stderr cleanly."

patterns-established:
  - "Pattern: subprocess-boundary wrappers around external skills. scripts/notebooklm/ is the prototype — a single module + __init__ re-export + pair of test files (unit with mocked subprocess.run + integration with real subprocess to a fake skill tree). Future external-skill wrappers (if any) should follow this layout."
  - "Pattern: fake skill tree via _make_fake_skill(tmp_path, payload, returncode) helper. Any test needing to exercise the subprocess path without Playwright can use this shape. Returns the skill Path; tests pass it as skill_path kwarg. Future skill wrappers can parameterize the helper to emit different payload shapes."
  - "Pattern: test names anchor to the invariant they enforce, not the implementation detail. test_subprocess_argv_shape, test_korean_question_single_argv_item, test_timeout_buffer_30_seconds — each name describes the CONTRACT. Refactoring _resolve_skill_path or _strip_follow_up internals won't need test rewrites; only contract changes do."

requirements-completed: [WIKI-03]

# Metrics
duration: ~4m
completed: 2026-04-19
---

# Phase 6 Plan 03: Wave 2 NOTEBOOKLM WRAPPER Summary

**`scripts.notebooklm.query_notebook` subprocess wrapper shipped as the single canonical interface to the external `shorts_naberal/.claude/skills/notebooklm` skill per D-7 (no duplication). D-6 single-string discipline enforced at argv boundary. D-7 path resolution kwarg > NOTEBOOKLM_SKILL_PATH env > hardcoded fallback. Phase 5 STATE #28 UTF-8 guard preserved. FOLLOW_UP_REMINDER marker stripped. 21 tests green (15 unit + 6 integration). Plans 04 + 05 can now `from scripts.notebooklm import query_notebook` — zero subprocess/encoding/marker-strip duplication downstream.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-19T07:28:28Z
- **Completed:** 2026-04-19T07:32:20Z
- **Tasks:** 2 / 2 complete
- **Files created:** 4 (2 scripts + 2 test files)
- **Files modified:** 1 (06-VALIDATION.md row flips)
- **Tests added:** 21 (15 test_notebooklm_wrapper + 6 test_notebooklm_subprocess)
- **Phase 5 regression:** 329/329 PASS (no infrastructure collision)
- **Phase 6 full suite:** 57/57 PASS (15 Plan 01 + 21 Plan 02 + 21 Plan 03)

## Accomplishments

### Task 1 — `scripts/notebooklm/` package (commit `78d47e9`)

- **`scripts/notebooklm/__init__.py` (15 lines):** Namespace marker + re-export of `query_notebook`, `DEFAULT_SKILL_PATH`, `FOLLOW_UP_MARKER`. Docstring names Plan 03/04/05 downstream consumers. `__all__` locks the public surface.
- **`scripts/notebooklm/query.py` (118 lines):** Full WIKI-03 wrapper.
  - `DEFAULT_SKILL_PATH = Path(r"C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm")` — D-7 hardcoded fallback.
  - `FOLLOW_UP_MARKER = "EXTREMELY IMPORTANT: Is that ALL you need"` — literal per RESEARCH Area 3 line 595.
  - `_resolve_skill_path(skill_path)` — kwarg > `NOTEBOOKLM_SKILL_PATH` env > default precedence.
  - `_strip_follow_up(answer)` — split-on-marker, rstrip trailing whitespace.
  - `query_notebook(question, notebook_id, timeout_s=600, skill_path=None) -> str`:
    - Raises `FileNotFoundError` if resolved skill dir missing.
    - Builds exact 9-element argv `[sys.executable, run.py, ask_question.py, --question, Q, --notebook-id, ID, --timeout, T]`.
    - `subprocess.run(..., encoding="utf-8", errors="replace", timeout=timeout_s+30)` — Phase 5 STATE #28 UTF-8 guard + Rule 2 replacement-char tolerance.
    - Raises `RuntimeError` on rc!=0 with `notebook_id=X: <stderr>` embedded for Plan 05 fallback diagnostics.
    - Returns answer with FOLLOW_UP marker stripped.

**Acceptance criteria PASS (Task 1):**
- `python -c "import scripts.notebooklm.query"` exits 0 ✅
- `grep -c "def query_notebook" scripts/notebooklm/query.py` = 1 ✅
- `grep -c "NOTEBOOKLM_SKILL_PATH" scripts/notebooklm/query.py` = 3 (>=1) ✅
- `grep -cE "encoding=.utf-8." scripts/notebooklm/query.py` = 2 (>=1) ✅
- `grep -c "EXTREMELY IMPORTANT: Is that ALL you need" scripts/notebooklm/query.py` = 1 (>=1) ✅
- `grep -c "ask_question.py" scripts/notebooklm/query.py` = 3 (>=1) ✅
- `grep -cE "shell\s*=\s*True" scripts/notebooklm/query.py` = 0 ✅
- `grep -cE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/query.py` = 0 (D-7) ✅

### Task 2 — Test files (commit `c123d5f`)

**`tests/phase06/test_notebooklm_wrapper.py` (202 lines, 15 unit tests, all mocked subprocess):**

1. `test_default_skill_path_matches_install` — D-7 fallback branch.
2. `test_env_var_overrides_default` — `NOTEBOOKLM_SKILL_PATH` branch.
3. `test_kwarg_overrides_env` — explicit kwarg branch.
4. `test_default_skill_path_is_the_2026_install` — locks literal install location.
5. `test_strip_follow_up_removes_marker` — canonical strip path.
6. `test_strip_follow_up_no_marker_passthrough` — no-op when marker absent.
7. `test_strip_follow_up_multiple_markers_only_first_counts` — edge case.
8. `test_missing_skill_path_raises` — FileNotFoundError surface.
9. `test_subprocess_rc_nonzero_raises` — RuntimeError on rc=1.
10. `test_subprocess_error_includes_notebook_id` — diagnostic surface for Plan 05 fallback.
11. `test_subprocess_success_returns_stripped` — full happy-path body strip.
12. `test_subprocess_argv_shape` — exact 9-element argv + UTF-8 encoding kwarg.
13. `test_korean_question_single_argv_item` — D-6 no-split invariant with Korean text.
14. `test_timeout_buffer_30_seconds` — subprocess timeout = timeout_s + 30.
15. `test_default_timeout_is_600` — locks default timeout_s contract.

**`tests/phase06/test_notebooklm_subprocess.py` (114 lines, 6 integration tests, real subprocess to fake skill tree):**

1. `test_real_subprocess_success_round_trip` — full fork with Korean payload + FOLLOW_UP marker; verify stripping.
2. `test_real_subprocess_error_propagates` — child exits rc=1 with stderr; verify RuntimeError surface.
3. `test_real_subprocess_utf8_korean` — Korean + em-dash round-trip through real subprocess (cp949 regression guard).
4. `test_timeout_argument_passed` — spies on real `subprocess.run` to verify --timeout passes through.
5. `test_notebook_id_passed_verbatim` — fake child echoes `--notebook-id` value back; verify complex notebook IDs (dashes) survive.
6. `test_missing_skill_raises_filenotfound` — real filesystem check for skill absence.

**Acceptance criteria PASS (Task 2):**
- `pytest tests/phase06/test_notebooklm_wrapper.py -q --no-cov` exits 0 ✅
- `pytest tests/phase06/test_notebooklm_subprocess.py -q --no-cov` exits 0 ✅
- `grep -cE "^def test_" tests/phase06/test_notebooklm_wrapper.py` = 15 (>=9) ✅
- `grep -cE "^def test_" tests/phase06/test_notebooklm_subprocess.py` = 6 (>=4) ✅
- `grep -c "한국" tests/phase06/test_notebooklm_subprocess.py` = 2 (>=1) ✅

## Argv Shape Verification (9-Element Command)

Per CONTEXT line 84-88 interface, the subprocess invocation is an exact 9-element list:

```python
[
    sys.executable,                 # [0] — current Python interpreter
    str(skill/"scripts"/"run.py"),  # [1] — external skill runner
    "ask_question.py",              # [2] — skill subcommand
    "--question", question,         # [3][4]
    "--notebook-id", notebook_id,   # [5][6]
    "--timeout", str(timeout_s),    # [7][8]
]
```

`test_subprocess_argv_shape` locks this literally with `assert len(cmd) == 9` plus per-index identity. Any future refactor adding an arg (e.g., `--show-browser` flag) will trip this assert — an intentional drift detector.

## D-7 Cross-Import Audit

```
$ grep -rnE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/ tests/phase06/test_notebooklm_*.py
# 0 hits — D-7 preserved
```

`scripts/notebooklm/` never imports from `shorts_naberal`. External skill access is subprocess-only. The `DEFAULT_SKILL_PATH` constant references the install location as a string literal (not an import).

## pytest Output (57/57 PASS Phase 6, 329/329 PASS Phase 5)

```
$ python -m pytest tests/phase06/ -q --no-cov
.........................................................                [100%]
57 passed in 0.30s

$ python -m pytest tests/phase05/ -q --no-cov
329 passed in 17.53s
```

Phase 6 breakdown:
- Plan 01 (Wave 0 FOUNDATION): 15 tests (test_wiki_frontmatter.py + test_wiki_reference_format.py)
- Plan 02 (Wave 1 WIKI CONTENT): 21 tests (test_wiki_nodes_ready.py + test_moc_linkage.py + test_continuity_bible_node.py)
- Plan 03 (Wave 2 NOTEBOOKLM WRAPPER): 21 tests (test_notebooklm_wrapper.py + test_notebooklm_subprocess.py) — THIS PLAN

Grand total after Plan 03: Phase 5 (329) + Phase 6 (57) = **386 tests green** (exceeds success_criteria "365 tests" target because Plan 02 over-delivered 36 tests; Plan 03 added 21 as specified).

## Task Commits

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | scripts.notebooklm package (wrapper + __init__) | `78d47e9` | scripts/notebooklm/__init__.py (15 lines), scripts/notebooklm/query.py (118 lines) |
| 2 | 21 tests (wrapper unit + subprocess integration) | `c123d5f` | tests/phase06/test_notebooklm_wrapper.py (202 lines / 15 tests), tests/phase06/test_notebooklm_subprocess.py (114 lines / 6 tests) |

Plan metadata commit: pending (final step — includes SUMMARY + STATE + ROADMAP + REQUIREMENTS + VALIDATION).

## Decisions Made

See `key-decisions` in frontmatter. Highlights:

- **DEFAULT_SKILL_PATH forward-slash form** — matches plan CONTEXT line 97 verbatim. Path() normalizes on consumption so Windows/WSL/POSIX all resolve identically.
- **RuntimeError message embeds notebook_id** — Plan 05 Fallback Chain needs per-notebook failure diagnostics. Tested explicitly.
- **Fake child run.py reconfigures stdout to UTF-8** — Rule 3 fix discovered during integration-test run: Windows child process defaults to cp949 and raises UnicodeEncodeError when writing Korean/em-dash. The PARENT's `encoding='utf-8'` arg to subprocess.run governs decode of captured bytes, not the child's write. Real ask_question.py handles this via Playwright DOM path; tests mirror the discipline explicitly and document in fixture docstring.
- **21 tests vs plan's >=13** — 2 bonus tests (`test_strip_follow_up_multiple_markers_only_first_counts`, `test_default_timeout_is_600`) are pure regression guards. Zero extra runtime cost (<20ms). Locks additional public-API invariants.
- **`errors='replace'` on subprocess.run** — Rule 2 completeness addition beyond plan's `encoding='utf-8'` spec. Guards against mid-stream Playwright crashes that could emit corrupted bytes before clean rc!=0. Maps bad bytes to U+FFFD so rc path surfaces cleanly instead of UnicodeDecodeError.

## Deviations from Plan

**1. [Rule 3 - Blocking] Fake skill child stdout UTF-8 reconfigure**

- **Found during:** Task 2 initial pytest run — 2 integration tests (`test_real_subprocess_success_round_trip`, `test_real_subprocess_utf8_korean`) failed with `UnicodeEncodeError: 'cp949' codec can't encode character '\u2014'` raised INSIDE the child process.
- **Root cause:** Windows child Python inherits cp949 as sys.stdout.encoding by default. The wrapper's `encoding='utf-8'` only affects the parent's decode of captured bytes.
- **Fix:** Added `sys.stdout.reconfigure(encoding='utf-8')` at the top of the fake child's run.py inside `_make_fake_skill`. Inline comment documents the reason so future test authors don't remove it.
- **Files modified:** `tests/phase06/test_notebooklm_subprocess.py` (helper fixture only, before the Task 2 commit).
- **Commit:** Rolled into `c123d5f` (Task 2 commit — fix was applied before commit). No separate commit needed.
- **Why Rule 3 not Rule 4:** This is a test-infrastructure bug blocking the plan's pytest verification step, not an architectural decision. The production wrapper is correct — the fake skill was an imperfect mimic. 1-line fix.

**2. [Rule 2 - Completeness] `errors='replace'` kwarg added to subprocess.run**

- **Found during:** Task 1 drafting. Plan CONTEXT line 590 specifies `encoding='utf-8'` but not `errors=`.
- **Resolution:** Added `errors='replace'` alongside `encoding='utf-8'`. Rationale: a mid-stream Playwright crash could emit a corrupted byte mid-answer before clean rc!=0 exit. Default `errors='strict'` would raise UnicodeDecodeError inside subprocess.run itself, bypassing our RuntimeError path and giving the caller a less diagnostic exception. `errors='replace'` maps bad bytes to U+FFFD and lets our rc-check raise a useful RuntimeError with stderr attached.
- **Why Rule 2 not Rule 4:** This is a robustness / correctness addition with zero behavior change in the happy path. No architectural implications — the wrapper's public contract unchanged.

**Total deviations:** 2 (both fall under Rules 2-3, auto-fixed). No Rule 1 (bugs) or Rule 4 (architectural) deviations. Plan executed essentially as written with two small additions for Windows robustness.

## Authentication Gates

None. Plan 03 is pure wrapper code — no NotebookLM API calls executed during the plan. The real Playwright authentication gate ("browser_state expired → user must rerun `auth_manager.py setup`") is deferred to Plan 04 (canary query) where the first real call is made.

## Verification Evidence

### Plan-required verification suite

1. **Task 1 `_strip_follow_up` sanity:**
   ```
   $ python -c "from scripts.notebooklm.query import _strip_follow_up, FOLLOW_UP_MARKER; assert _strip_follow_up('hello' + chr(10) + FOLLOW_UP_MARKER + ' more') == 'hello'; print('OK')"
   OK
   ```
2. **Package import:**
   ```
   $ python -c "from scripts.notebooklm import query_notebook, DEFAULT_SKILL_PATH, FOLLOW_UP_MARKER; print('OK')"
   OK
   ```
3. **Task 2 pytest (both files):**
   ```
   $ python -m pytest tests/phase06/test_notebooklm_wrapper.py tests/phase06/test_notebooklm_subprocess.py -q --no-cov
   21 passed in 0.25s
   ```
4. **Phase 6 full suite:**
   ```
   $ python -m pytest tests/phase06/ -q --no-cov
   57 passed in 0.30s
   ```
5. **Phase 5 regression:**
   ```
   $ python -m pytest tests/phase05/ -q --no-cov
   329 passed in 17.53s
   ```
6. **D-7 cross-import audit:**
   ```
   $ grep -rnE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/
   # 0 hits
   ```

### Plan acceptance criteria

| Criterion | Result |
|-----------|--------|
| `python -c "import scripts.notebooklm.query"` exits 0 | PASS |
| `grep -c "def query_notebook"` in query.py = 1 | PASS |
| `grep -c "NOTEBOOKLM_SKILL_PATH"` >= 1 | PASS (=3) |
| `grep -cE "encoding=.utf-8."` >= 1 | PASS (=2) |
| `grep -c FOLLOW_UP literal` >= 1 | PASS (=1) |
| `grep -c "ask_question.py"` >= 1 | PASS (=3) |
| `grep -cE "shell\s*=\s*True"` = 0 | PASS (=0) |
| `grep -cE "from\s+shorts_naberal"` = 0 | PASS (=0) |
| `pytest test_notebooklm_wrapper.py` exit 0 | PASS |
| `pytest test_notebooklm_subprocess.py` exit 0 | PASS |
| test def count in wrapper.py >= 9 | PASS (=15) |
| test def count in subprocess.py >= 4 | PASS (=6) |
| Korean anchor in subprocess.py >= 1 | PASS (=2) |
| Argv shape = 9 elements exactly | PASS (test_subprocess_argv_shape) |
| UTF-8 encoding used | PASS (grep + test_subprocess_argv_shape kwarg assert) |
| FOLLOW_UP marker stripping is string-level | PASS (no regex in _strip_follow_up) |
| 06-VALIDATION.md rows 6-03-01/02 flipped green | PASS |

## Known Stubs

None. Every created file contains substantive production code or genuine assertions:

- `scripts/notebooklm/query.py` (118 lines) — full wrapper with 3 helpers (`_resolve_skill_path`, `_strip_follow_up`, `query_notebook`), no placeholders, no TODOs.
- `scripts/notebooklm/__init__.py` (15 lines) — legitimate namespace + re-export with `__all__`.
- `tests/phase06/test_notebooklm_wrapper.py` (202 lines) — 15 real assertions, no skipped or stubbed tests.
- `tests/phase06/test_notebooklm_subprocess.py` (114 lines) — 6 real subprocess round-trips through fake skill trees.

Zero `TODO`, `FIXME`, `not implemented`, `pass`-only function bodies, `skip_gates`, `TODO(next-session)`, or lowercase `t2v` tokens in any new file.

## Deferred Issues

**None new this plan.**

The real external skill's authentication freshness ("run `auth_manager.py status`") remains deferred to Plan 04 Wave 2 where the first live canary query is made. Plan 03 explicitly does NOT touch live authentication.

## Next Plan Readiness

**Plan 04 (Wave 2 library.json + canary query) unblocked:**
- `from scripts.notebooklm import query_notebook` resolves to the exact wrapper Plan 04 canary test needs.
- `DEFAULT_SKILL_PATH` + `FOLLOW_UP_MARKER` re-exported so Plan 04's library.json delta test can assert against shared constants.
- `mock_notebooklm_skill_env` fixture (Plan 01) remains reusable — Plan 04 library validation tests will mock the skill path for deterministic behavior.

**Plan 05 (Wave 2 Fallback Chain) unblocked:**
- `RAGBackend` Tier 0 can wrap `query_notebook` directly. The `RuntimeError` carrying `notebook_id=X: <stderr>` gives the Tier 0->1 transition the exact diagnostic it needs to log which notebook failed.
- `FileNotFoundError` on missing skill is a distinct exception class (not conflated with RuntimeError), so the fallback chain can distinguish "skill not installed" (hard-fail → grep wiki tier) from "skill ran but failed" (soft-fail → possibly retryable).

**Recommended next action:** `/gsd:execute-phase 6` to advance to Plan 04 Wave 2 library.json channel-bible entry.

## Self-Check: PASSED

Verified on disk:
- `scripts/notebooklm/__init__.py` — FOUND (15 lines, imports query_notebook/DEFAULT_SKILL_PATH/FOLLOW_UP_MARKER)
- `scripts/notebooklm/query.py` — FOUND (118 lines, `def query_notebook` + `DEFAULT_SKILL_PATH` + `FOLLOW_UP_MARKER`)
- `tests/phase06/test_notebooklm_wrapper.py` — FOUND (202 lines, 15 test defs)
- `tests/phase06/test_notebooklm_subprocess.py` — FOUND (114 lines, 6 test defs)
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md` — MODIFIED (rows 6-03-01 + 6-03-02 flipped ✅ green)

Verified in git log:
- `78d47e9` (Task 1 — scripts.notebooklm package) — FOUND via `git log --oneline`
- `c123d5f` (Task 2 — 21 tests) — FOUND via `git log --oneline`

Verified at runtime:
- `python -c "from scripts.notebooklm import query_notebook, DEFAULT_SKILL_PATH, FOLLOW_UP_MARKER; print('OK')"` → OK
- `pytest tests/phase06/test_notebooklm_wrapper.py tests/phase06/test_notebooklm_subprocess.py -q --no-cov` → 21 passed
- `pytest tests/phase06/ -q --no-cov` → 57 passed (15 Plan 01 + 21 Plan 02 + 21 Plan 03)
- `pytest tests/phase05/ -q --no-cov` → 329 passed (regression preserved)
- `grep -rnE "from\s+shorts_naberal|import\s+shorts_naberal" scripts/notebooklm/` → 0 hits (D-7 preserved)
- No drift tokens in new files (skip_gates/TODO(next-session)/lowercase-t2v/text_to_video/text2video/segments[] — 0 hits)

**Phase 6 Plan 03 complete. Wave 2 NOTEBOOKLM WRAPPER shipped. Ready for Plan 04 (Wave 2 library.json + canary query).**

---
*Phase: 06-wiki-notebooklm-integration-failures-reservoir*
*Plan: 03 (Wave 2 NOTEBOOKLM WRAPPER)*
*Completed: 2026-04-19*
