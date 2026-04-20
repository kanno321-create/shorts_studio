---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 02
subsystem: orchestrator-bootstrap
tags: [pipeline-02, dotenv, zero-dep, package-init, d-13, d-14, d-15]
requires:
  - PIPELINE-02
provides:
  - scripts.orchestrator._load_dotenv_if_present (callable at package import)
  - os.environ.setdefault semantics for .env values
  - BOM / CRLF / export-prefix / quoted-value tolerance
  - silent skip when .env missing
affects:
  - scripts/orchestrator/__init__.py (+69 net lines: 83 → 152)
  - tests/phase11/test_dotenv_loader.py (+258 new lines)
tech-stack:
  added: []
  patterns:
    - stdlib-only parser (os, re, pathlib)
    - utf-8-sig encoding for transparent BOM handling
    - regex split on FIRST `=` via non-greedy capture
    - os.environ.setdefault (override=False)
key-files:
  created:
    - tests/phase11/test_dotenv_loader.py
  modified:
    - scripts/orchestrator/__init__.py
decisions:
  - "D-13 zero-dep parser (no python-dotenv install; repo has no requirements.txt / pyproject.toml)"
  - "D-14 implementation location: package __init__.py top-level (runs before submodule imports)"
  - "D-15 setdefault semantics — pre-existing env wins (matches scripts/experimental/test_*.py convention)"
  - "Placement BEFORE submodule imports at L82 — fires earlier than any adapter __init__ can inspect env"
  - "utf-8-sig decode over manual BOM strip — idiomatic + handles BOM-free files identically"
metrics:
  duration: 6m
  completed: 2026-04-21
  tests_added: 15
  tests_regression_preserved: 244
  net_lines_added: 327 (+69 prod / +258 test)
---

# Phase 11 Plan 02: Zero-Dep `.env` Loader Summary

**One-liner:** PIPELINE-02 — `_load_dotenv_if_present()` at `scripts/orchestrator/__init__.py` package-init loads `.env` via pure-stdlib regex parser with `os.environ.setdefault` semantics, covering 13 edge cases (quoted / comment / BOM / export / CRLF / multi-equals / missing-file / pre-existing-env) — adapters downstream now observe env values automatically without any `python-dotenv` dependency.

## Objective

Eliminate D10-PIPELINE-DEF-01 error #2: adapters in `ShortsPipeline.__init__` raised `ValueError` because `.env` was never loaded at process start. Wrapper `run_pipeline.cmd/.ps1` (Plan 11-04), direct `py -m scripts.orchestrator.shorts_pipeline` invocations, and direct pytest runs now all see `.env` values automatically — no manual `set -a && source .env` prerequisite.

Design per CONTEXT D-13 / D-14 / D-15 / D-16:
- Zero external dependency (harness has no `requirements.txt` / `pyproject.toml`)
- `os.environ.setdefault` (override=False — pre-existing env wins)
- Silent skip when `.env` missing
- Placement at package `__init__.py` top-level (BEFORE submodule imports) per RESEARCH §Pitfall 2

## Tasks Completed

| Task | Commit     | Files                                                     | Tests |
| ---- | ---------- | --------------------------------------------------------- | ----- |
| 1    | `3924313`  | `tests/phase11/test_dotenv_loader.py` (+258 lines)        | 15 RED |
| 2    | `c52c118`  | `scripts/orchestrator/__init__.py` (+69 lines, 83 → 152)  | 15 GREEN |

## Acceptance Criteria — All Met

| # | Criterion                                                                         | Result |
| - | --------------------------------------------------------------------------------- | ------ |
| 1 | `def _load_dotenv_if_present` in `__init__.py`                                    | 1 match ✓ |
| 2 | Top-level call `^_load_dotenv_if_present()` (not inside a function)               | L76 ✓ |
| 3 | Zero-dep: `grep -c "python-dotenv\|from dotenv" ... __init__.py` returns 0        | 0 ✓ |
| 4 | No `^import dotenv` anywhere in file                                              | 0 ✓ |
| 5 | `os.environ.setdefault` call present (override=False semantics)                   | L71 (1 call + 2 docstring refs) ✓ |
| 6 | `pytest tests/phase11/test_dotenv_loader.py -v` → 15 passed                       | 15/15 ✓ |
| 7 | `pytest tests/phase04/ -q` regression preserved                                   | 244/244 ✓ |
| 8 | `from scripts.orchestrator import _load_dotenv_if_present` callable               | True ✓ |
| 9 | `import scripts.orchestrator` succeeds post-insertion                             | OK ✓ |

## 13 Edge Cases Covered (RESEARCH §Pattern 2 matrix)

| # | Test                                 | Input                      | Expected                    |
| - | ------------------------------------ | -------------------------- | --------------------------- |
| 1 | `test_basic_kv`                      | `KEY=value`                | `value`                     |
| 2 | `test_spaces_preserved_in_value`     | `KEY=value with spaces`    | `value with spaces`         |
| 3 | `test_double_quotes_stripped`        | `KEY="quoted value"`       | `quoted value`              |
| 4 | `test_single_quotes_stripped`        | `KEY='single'`             | `single`                    |
| 5 | `test_multiple_equals_in_value`      | `KEY=has=equals=signs`     | `has=equals=signs`          |
| 6 | `test_comments_ignored`              | `# comment`                | skipped                     |
| 7 | `test_indented_comments_ignored`     | `   # indented`            | skipped                     |
| 8 | `test_empty_lines_ignored`           | blank line                 | skipped                     |
| 9 | `test_export_prefix_stripped`        | `export KEY=value`         | `value` (bash compat)       |
| 10 | `test_utf8_bom_stripped`            | `\ufeffKEY=value`          | `value`                     |
| 11 | `test_crlf_handled`                 | `KEY=value\r\n`            | `value` (no \r)             |
| 12 | `test_missing_file_silent`          | no `.env` file             | silent + env unchanged      |
| 13 | `test_existing_env_wins`            | env=X, file=Y              | `X` (setdefault no-op)      |

Plus 2 integration tests:
- `test_idempotent_on_duplicate_call` — second `_load_dotenv_if_present()` preserves first value
- `test_loader_exposed_via_package` — public API contract (callable from namespace)

## Validation

```
$ py -3.11 -m pytest tests/phase11/test_dotenv_loader.py -v
...
15 passed in 0.86s

$ py -3.11 -m pytest tests/phase04/ -q
...
244 passed in 0.45s

$ py -3.11 -c "from scripts.orchestrator import _load_dotenv_if_present; print(callable(_load_dotenv_if_present))"
True

$ grep -c "python-dotenv\|from dotenv" scripts/orchestrator/__init__.py
0

$ grep -c "^import dotenv" scripts/orchestrator/__init__.py
0
```

## Implementation Details

**Parser regex:** `r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"`

- `^\s*` — leading whitespace tolerated (indented lines OK)
- `(?:export\s+)?` — optional bash `export` prefix (stripped)
- `([A-Za-z_][A-Za-z0-9_]*)` — POSIX identifier for KEY
- `=` — literal, FIRST occurrence is the split token
- `(.*?)\s*$` — non-greedy value with trailing whitespace stripped

**Quote stripping:** Values may be surrounded by matched single OR double quotes — stripped once via `value[0] == value[-1] and value[0] in ("'", '"')`. Partial / mismatched quotes (e.g. `KEY="value'`) are left intact, matching python-dotenv behavior.

**BOM handling:** `encoding="utf-8-sig"` transparently strips a UTF-8 BOM on the first line if present; otherwise behaves identically to `utf-8`. This avoids conditional BOM-detection branching.

**CRLF handling:** `line.rstrip("\r")` runs before regex match so Windows-authored `.env` files (typical on the target Windows 11 environment) parse correctly.

**Silent missing-file skip:** `Path(".env").exists()` guard + `try/except OSError` around `read_text` ensures both "no file" and "permission denied" / "file disappeared mid-call" paths raise nothing — the pipeline falls back to the pre-existing environment.

**Idempotency:** `os.environ.setdefault` never overwrites, so repeated calls are no-ops once a key is set. This also means pre-existing env (CI/CD, Windows Task Scheduler actions, shell `set KEY=X` commands) takes precedence — matches D-15 + RESEARCH §Pattern 2 rationale.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Docstring Grep False-Positive] Removed `python-dotenv` mentions from docstrings**
- **Found during:** Task 2 acceptance criteria verification
- **Issue:** Initial docstrings mentioned `python-dotenv` twice as pure prose describing what we intentionally DO NOT depend on. Acceptance criterion `grep -c "python-dotenv\|from dotenv" returns 0` is a literal grep that does not distinguish docstring references from real imports — returned 2 hits.
- **Fix:** Reworded docstrings to use "pure stdlib" and "override=False semantics" phrasing instead. Semantic meaning preserved; literal grep now returns 0.
- **Files modified:** `scripts/orchestrator/__init__.py` (docstring sections L11 and L25 reworded)
- **Commit:** Folded into Task 2 commit `c52c118` (same Edit session)

No other deviations. Plan executed as written.

## Files Modified Summary

| File                                        | Before | After | Delta |
| ------------------------------------------- | -----: | ----: | ----: |
| `scripts/orchestrator/__init__.py`          |     83 |   152 |   +69 |
| `tests/phase11/test_dotenv_loader.py`       |   (new) |  258 |  +258 |
| **Total**                                   |     83 |   410 |  +327 |

## Relationship to D10-PIPELINE-DEF-01

Error #2 in the 5-error chain was: adapters raise `ValueError` in `ShortsPipeline.__init__` because `os.environ["KLING_API_KEY"]` etc. were absent — values existed in `.env` but `.env` was never loaded. With this plan shipped:

1. `py -m scripts.orchestrator.shorts_pipeline ...` — Python's module resolver triggers `scripts.orchestrator` package import → `_load_dotenv_if_present()` fires BEFORE any submodule imports → adapter `__init__` sees populated env.
2. `pytest tests/...` — same package-import chain triggers loader.
3. `run_pipeline.cmd` / `run_pipeline.ps1` (Plan 11-04) — wrapper runs `py -m scripts.orchestrator.shorts_pipeline`, same chain as #1.
4. `python -c "import scripts.orchestrator.api.kling_i2v; ..."` (hypothetical direct submodule import) — Python still loads the package `__init__.py` first per its import machinery, so loader fires.

Paired with Plan 11-03 (adapter graceful degrade), adapters will both (a) see env when present AND (b) degrade gracefully when env remains absent — covering both the happy path and the CI / missing-key scenarios.

## Self-Check: PASSED

- `scripts/orchestrator/__init__.py` exists with `_load_dotenv_if_present` function ✓
- `tests/phase11/test_dotenv_loader.py` exists with 15 tests ✓
- Commit `3924313` present in `git log` ✓
- Commit `c52c118` present in `git log` ✓
- `pytest tests/phase11/test_dotenv_loader.py` — 15 passed ✓
- `pytest tests/phase04/` — 244 passed (regression preserved) ✓
