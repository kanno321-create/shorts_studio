---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/orchestrator/__init__.py
  - tests/phase11/test_dotenv_loader.py
autonomous: true
requirements: [PIPELINE-02]
must_haves:
  truths:
    - "Importing `scripts.orchestrator` triggers `.env` loading at import time (before any adapter `__init__` can check env)"
    - "Pre-existing `os.environ` values WIN over `.env` values (setdefault semantics; override=False)"
    - ".env file missing → silent skip, no exception, pipeline continues with existing env"
    - "Parser handles 13 edge cases per RESEARCH §Pattern 2 table (quoted/comments/BOM/export/CRLF/multiple-equals/etc.)"
    - "Zero new dependencies (no python-dotenv import anywhere in scripts/orchestrator/*)"
    - "Korean text values in .env survive round-trip (UTF-8 with BOM support)"
  artifacts:
    - path: "scripts/orchestrator/__init__.py"
      provides: "_load_dotenv_if_present() zero-dep loader called at package import time"
      contains: "def _load_dotenv_if_present"
    - path: "tests/phase11/test_dotenv_loader.py"
      provides: "13 edge-case tests covering every parser row in RESEARCH §Pattern 2"
      min_lines: 200
  key_links:
    - from: "scripts/orchestrator/__init__.py::_load_dotenv_if_present"
      to: "os.environ.setdefault"
      via: "per-line KEY=VALUE regex with quote-strip"
      pattern: "os\\.environ\\.setdefault"
    - from: "package import (scripts.orchestrator)"
      to: "_load_dotenv_if_present() call"
      via: "top-level statement, before any submodule imports"
      pattern: "_load_dotenv_if_present\\(\\)"
---

<objective>
PIPELINE-02: Add zero-dependency `.env` loader at `scripts/orchestrator/__init__.py` package init so env vars are loaded before any adapter `__init__` can check them. Resolves D10-PIPELINE-DEF-01 error #2 (adapters raise ValueError in pipeline constructor because env vars absent — they exist in `.env` but `.env` was never loaded).

Purpose: Wrapper `run_pipeline.cmd/.ps1` AND direct `py -m scripts.orchestrator.shorts_pipeline` calls AND direct pytest runs all see `.env` values automatically. PowerShell `set -a && source .env` manual step eliminated (대표님 double-click UX prerequisite).

Design per D-13 / D-14 / D-15 / D-16:
- No `python-dotenv` dependency (harness has no `requirements.txt`)
- `os.environ.setdefault` (override=False — pre-existing env wins; matches `scripts/experimental/test_*.py:19` convention)
- Silent skip when `.env` missing
- Placement at package `__init__.py` top (NOT inside `main()` per RESEARCH §Pitfall 2)

Output:
- `scripts/orchestrator/__init__.py` with `_load_dotenv_if_present()` function + call at top
- `tests/phase11/test_dotenv_loader.py` with 13 edge-case tests (all GREEN)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md
@scripts/orchestrator/__init__.py

<interfaces>
<!-- Current __init__.py structure (78 lines); insertion point is the TOP -->

From scripts/orchestrator/__init__.py (current L1-9):
```python
"""scripts.orchestrator — Phase 5 public API surface.

Downstream plans (08 hc_checks, 09 Hook extensions, 10 SC acceptance) and
all future callers import from this namespace, NOT from the individual
modules directly. The namespace collects every primitive produced by
Waves 0-4 plus the keystone :class:`ShortsPipeline` from Wave 5.
"""
from __future__ import annotations

from .checkpointer import Checkpoint, Checkpointer, sha256_file
# ... (cascading submodule imports)
```

Semantic: submodule imports at L10+ trigger adapter module imports which eventually trigger `ShortsPipeline.__init__` at instantiation time. If `_load_dotenv_if_present()` is placed AFTER the submodule imports, the env is still set before any CALLER does `ShortsPipeline(session_id=...)`. But to be safe (and to handle cases where submodules do module-level env reads), we place it FIRST — right after the docstring + `__future__` import.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Write 13 RED tests for zero-dep .env loader</name>
  <files>tests/phase11/test_dotenv_loader.py</files>
  <read_first>
    - scripts/orchestrator/__init__.py (full 84 lines — understand current import sequence)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 2 (L212-243 — exact 13-row edge-case table)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-13 / D-14 / D-15 / D-16
    - tests/phase11/conftest.py (from Plan 11-01 — uses `tmp_env_file` + `preserve_env` fixtures)
    - scripts/experimental/test_complex_action.py (L19 area — `load_dotenv(override=False)` precedent)
  </read_first>
  <behavior>
    - Test 1 `test_basic_kv`: `.env` with `KEY=value` → `os.environ['KEY'] == 'value'`
    - Test 2 `test_spaces_preserved_in_value`: `KEY=value with spaces` → `'value with spaces'`
    - Test 3 `test_double_quotes_stripped`: `KEY="quoted value"` → `'quoted value'`
    - Test 4 `test_single_quotes_stripped`: `KEY='single'` → `'single'`
    - Test 5 `test_multiple_equals_in_value`: `KEY=has=equals=signs` → `'has=equals=signs'` (split on FIRST `=` only)
    - Test 6 `test_comments_ignored`: `# comment\nKEY=v` → only KEY loaded
    - Test 7 `test_indented_comments_ignored`: `   # indented\nKEY=v` → only KEY loaded
    - Test 8 `test_empty_lines_ignored`: `\n\nKEY=v\n` → only KEY loaded
    - Test 9 `test_export_prefix_stripped`: `export KEY=value` → `KEY=value` (bash compat)
    - Test 10 `test_utf8_bom_stripped`: `\ufeff KEY=value` as first line → `KEY=value`
    - Test 11 `test_crlf_handled`: `KEY=value\r\n` → `'value'` (no trailing \r)
    - Test 12 `test_missing_file_silent`: no `.env` file → no exception + env unchanged
    - Test 13 `test_existing_env_wins`: pre-set `os.environ['KEY']='X'` + `.env` has `KEY=Y` → after load, env still `'X'`
    - Bonus Test 14 `test_dotenv_loader_runs_before_adapter_import`: re-import scripts.orchestrator with cleared env + `.env` present → after import, env populated (covers RESEARCH §Pitfall 2)
    - Bonus Test 15 `test_idempotent_on_duplicate_call`: calling `_load_dotenv_if_present()` twice yields same env state (setdefault no-op on second call)
  </behavior>
  <action>
    Create `tests/phase11/test_dotenv_loader.py`:
    ```python
    """PIPELINE-02 zero-dep .env loader tests (13 edge cases + 2 integration)."""
    from __future__ import annotations

    import importlib
    import os
    import sys
    from pathlib import Path

    import pytest


    # We import the function from scripts.orchestrator; the function is
    # created by Task 2 of this plan. Until then, import will fail / raise.


    def _write_env(path: Path, content: str, encoding: str = "utf-8") -> None:
        path.write_text(content, encoding=encoding)


    def _run_loader(env_path: Path, preserve_env):
        """Helper: cd to env_path's parent, call loader, assert no exception."""
        from scripts.orchestrator import _load_dotenv_if_present  # type: ignore[attr-defined]
        cwd = os.getcwd()
        try:
            os.chdir(env_path.parent)
            _load_dotenv_if_present()
        finally:
            os.chdir(cwd)


    def test_basic_kv(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "P11_BASIC_KEY=basic_value\n")
        os.environ.pop("P11_BASIC_KEY", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_BASIC_KEY"] == "basic_value"


    def test_spaces_preserved_in_value(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "P11_SPACED=value with spaces\n")
        os.environ.pop("P11_SPACED", None)
        _run_loader(env, preserve_env)
        # trailing whitespace stripped by regex \s*$; internal preserved
        assert os.environ["P11_SPACED"] == "value with spaces"


    def test_double_quotes_stripped(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, 'P11_DQ="quoted value"\n')
        os.environ.pop("P11_DQ", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_DQ"] == "quoted value"


    def test_single_quotes_stripped(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "P11_SQ='single'\n")
        os.environ.pop("P11_SQ", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_SQ"] == "single"


    def test_multiple_equals_in_value(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "P11_MULTI=has=equals=signs\n")
        os.environ.pop("P11_MULTI", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_MULTI"] == "has=equals=signs"


    def test_comments_ignored(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "# top comment\nP11_CMT=value\n")
        os.environ.pop("P11_CMT", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_CMT"] == "value"


    def test_indented_comments_ignored(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "   # indented comment\nP11_IND=value\n")
        os.environ.pop("P11_IND", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_IND"] == "value"


    def test_empty_lines_ignored(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "\n\nP11_EMPTY=value\n\n\n")
        os.environ.pop("P11_EMPTY", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_EMPTY"] == "value"


    def test_export_prefix_stripped(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "export P11_EXP=value\n")
        os.environ.pop("P11_EXP", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_EXP"] == "value"


    def test_utf8_bom_stripped(tmp_path, preserve_env):
        env = tmp_path / ".env"
        # write BOM explicitly
        env.write_bytes("\ufeffP11_BOM=value\n".encode("utf-8"))
        os.environ.pop("P11_BOM", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_BOM"] == "value"


    def test_crlf_handled(tmp_path, preserve_env):
        env = tmp_path / ".env"
        env.write_bytes(b"P11_CRLF=value\r\n")
        os.environ.pop("P11_CRLF", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_CRLF"] == "value"


    def test_missing_file_silent(tmp_path, preserve_env):
        # no .env file created
        env_dir = tmp_path / "nonexistent_dir"
        env_dir.mkdir()
        from scripts.orchestrator import _load_dotenv_if_present  # type: ignore[attr-defined]
        cwd = os.getcwd()
        try:
            os.chdir(env_dir)
            # must NOT raise
            _load_dotenv_if_present()
        finally:
            os.chdir(cwd)


    def test_existing_env_wins(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "P11_EXIST=from_env_file\n")
        os.environ["P11_EXIST"] = "from_shell"
        _run_loader(env, preserve_env)
        # setdefault: shell value wins
        assert os.environ["P11_EXIST"] == "from_shell"


    def test_idempotent_on_duplicate_call(tmp_path, preserve_env):
        env = tmp_path / ".env"
        _write_env(env, "P11_IDEM=first\n")
        os.environ.pop("P11_IDEM", None)
        _run_loader(env, preserve_env)
        assert os.environ["P11_IDEM"] == "first"
        # Rewrite to "second" — existing value should still win on 2nd call
        _write_env(env, "P11_IDEM=second\n")
        _run_loader(env, preserve_env)
        assert os.environ["P11_IDEM"] == "first"  # setdefault preserves first


    def test_loader_exposed_via_package(preserve_env):
        """Public API: _load_dotenv_if_present importable from package namespace."""
        from scripts.orchestrator import _load_dotenv_if_present  # noqa: F401
        assert callable(_load_dotenv_if_present)
    ```
    Tests are all RED until Task 2 creates `_load_dotenv_if_present`.
  </action>
  <verify>
    <automated>pytest tests/phase11/test_dotenv_loader.py --collect-only -q 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `tests/phase11/test_dotenv_loader.py` exists
    - Collection shows 14 tests (13 edge cases + exposure test)
    - `pytest tests/phase11/test_dotenv_loader.py -v 2>&1 | grep -c "ImportError\|AttributeError\|FAILED"` ≥ 1 (RED expected)
  </acceptance_criteria>
  <done>14 RED tests seeded; each test asserts one row of RESEARCH §Pattern 2 edge-case matrix.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement _load_dotenv_if_present at package init — GREEN all 14 tests</name>
  <files>scripts/orchestrator/__init__.py</files>
  <read_first>
    - scripts/orchestrator/__init__.py (full 84 lines)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 2 (L601-653 code example)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pitfall 2 (placement reasoning)
    - tests/phase11/test_dotenv_loader.py (from Task 1 — exact behavioral contract)
  </read_first>
  <behavior>
    - All 14 tests in test_dotenv_loader.py GREEN after this change
    - Function located at TOP of __init__.py (before submodule imports at L10+)
    - Function called ONCE at module level (import-time trigger)
    - No regression: `pytest tests/phase04/ tests/phase05/ -q` stays green (244/244 + Phase 5 baseline)
    - `_load_dotenv_if_present` name NOT in `__all__` (private symbol, but importable for tests)
  </behavior>
  <action>
    Edit `scripts/orchestrator/__init__.py` by INSERTING the loader function + call IMMEDIATELY after the module docstring and `from __future__ import annotations`, and BEFORE the first `from .checkpointer import ...` line.

    EXACT INSERT BLOCK (paste between current L8 `from __future__ import annotations` and current L10 `from .checkpointer import ...`):

    ```python
    from __future__ import annotations

    import os
    import re
    from pathlib import Path


    def _load_dotenv_if_present() -> None:
        """Zero-dep ``.env`` loader. Idempotent. override=False semantics.

        Reads ``./env`` relative to current working directory and populates
        :data:`os.environ` using :meth:`os.environ.setdefault` (pre-existing
        env wins — matches python-dotenv ``override=False`` and
        ``scripts/experimental/test_*.py`` convention).

        Parser contract (verified by tests/phase11/test_dotenv_loader.py):
            - Comments (``#`` anywhere after leading whitespace) skipped
            - Empty / whitespace-only lines skipped
            - ``export KEY=VAL`` bash prefix stripped
            - Values may contain ``=`` (split on FIRST ``=`` only)
            - Surrounding matched ``"`` or ``'`` quotes stripped from value
            - UTF-8 BOM on first line tolerated (``utf-8-sig`` decode)
            - CRLF line endings tolerated (rstrip ``\\r``)

        Silent skip when ``.env`` missing — tests / CI without the file
        continue with pre-existing environment.

        PIPELINE-02 / Phase 11 D-13, D-14, D-15. Called at package import
        time so adapters constructed by :class:`ShortsPipeline` see env
        values loaded from disk.
        """
        env_path = Path(".env")
        if not env_path.exists():
            return
        try:
            raw = env_path.read_text(encoding="utf-8-sig")  # strips BOM if present
        except OSError:
            return
        line_re = re.compile(
            r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"
        )
        for raw_line in raw.splitlines():
            line = raw_line.rstrip("\r")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = line_re.match(line)
            if not m:
                continue
            key, value = m.group(1), m.group(2)
            # Strip surrounding matched quotes (single OR double).
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


    # Run at package import time — before any adapter ``__init__`` can
    # look at os.environ. See RESEARCH §Pitfall 2 for placement reasoning.
    _load_dotenv_if_present()


    from .checkpointer import Checkpoint, Checkpointer, sha256_file
    # ... (rest of existing imports follow unchanged)
    ```

    Do NOT add `_load_dotenv_if_present` to `__all__` — private by convention (underscore prefix) but importable as `from scripts.orchestrator import _load_dotenv_if_present` for tests.

    After edit, run in order:
    ```
    pytest tests/phase11/test_dotenv_loader.py -v       # 14 GREEN
    pytest tests/phase04/ tests/phase05/ -q             # baseline preserved
    python -c "from scripts.orchestrator import _load_dotenv_if_present; print('OK')"  # import path works
    python -c "import scripts.orchestrator; print(scripts.orchestrator.__file__)"  # package still imports
    ```
  </action>
  <verify>
    <automated>pytest tests/phase11/test_dotenv_loader.py tests/phase04/ -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def _load_dotenv_if_present" scripts/orchestrator/__init__.py` returns 1 match (function defined)
    - `grep -n "^_load_dotenv_if_present()" scripts/orchestrator/__init__.py` returns 1 match (top-level call, not inside a function)
    - `grep -c "python-dotenv\|from dotenv" scripts/orchestrator/__init__.py` returns 0 (no external dep)
    - `grep -c "^import dotenv" scripts/orchestrator/__init__.py` returns 0 (tightens zero-dep check against all three import vectors)
    - `grep -n "os.environ.setdefault" scripts/orchestrator/__init__.py` returns ≥1 match (override=False semantics)
    - `pytest tests/phase11/test_dotenv_loader.py -v` → 14 passed
    - `pytest tests/phase04/ -q` → 244/244 passed
    - `python -c "from scripts.orchestrator import _load_dotenv_if_present; print(callable(_load_dotenv_if_present))"` outputs `True`
  </acceptance_criteria>
  <done>14 GREEN dotenv tests + 244/244 phase04 baseline + `_load_dotenv_if_present` callable at package import.</done>
</task>

</tasks>

<verification>
**Per-plan verify:**
```bash
pytest tests/phase11/test_dotenv_loader.py -v                          # 14 GREEN
pytest tests/phase04/ -q                                               # 244/244 baseline
python -c "from scripts.orchestrator import _load_dotenv_if_present"   # import works
```

**PIPELINE-02 linkage to SC#4:** `pytest tests/phase11/test_dotenv_loader.py -v → all GREEN` is the automated signal for SC#4.
</verification>

<success_criteria>
- [ ] `_load_dotenv_if_present` function defined at top of `scripts/orchestrator/__init__.py`
- [ ] Function called at package import time (top-level statement, before submodule imports)
- [ ] Zero-dep (no `dotenv` / `python-dotenv` import)
- [ ] `os.environ.setdefault` (override=False semantics — existing env wins)
- [ ] All 14 edge-case tests GREEN
- [ ] 244/244 phase04 regression baseline preserved
</success_criteria>

<output>
After completion, create `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-02-SUMMARY.md` with:
- Files modified + net line delta on `__init__.py` (~78 → ~110)
- Test count before/after (250 → 264)
- Confirmation that `.env` is auto-loaded at package import
- Zero-dep compliance check (grep shows no dotenv import)
</output>
