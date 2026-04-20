"""PIPELINE-02 zero-dep `.env` loader tests.

Covers every row of the RESEARCH §Pattern 2 edge-case matrix (13 rows) plus
two integration tests (public-API exposure + idempotency on duplicate call).

Design contract (mirrors ``scripts/experimental/test_complex_action.py:19``
``load_dotenv(PROJECT_ROOT / ".env", override=False)`` convention):

- ``os.environ.setdefault`` — pre-existing env wins (override=False semantics)
- Silent skip when ``.env`` missing — no exception raised
- UTF-8 BOM tolerated on first line (``utf-8-sig`` decode)
- CRLF line endings handled (rstrip ``\\r``)
- ``export KEY=VAL`` bash prefix stripped
- Surrounding matched quotes stripped (single OR double)
- ``#`` comments skipped (after leading whitespace)
- First ``=`` is the split token (values may contain additional ``=``)

Fixtures (``tests/phase11/conftest.py``):
- ``preserve_env`` — snapshots ``os.environ`` and restores after test
- ``tmp_path`` — pytest builtin (tmp dir isolated per test)

Import contract: ``_load_dotenv_if_present`` is a private symbol on
``scripts.orchestrator`` package (underscore prefix), but importable via
``from scripts.orchestrator import _load_dotenv_if_present`` for tests.
NOT in ``__all__``.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_env(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` using the given encoding (default utf-8)."""
    path.write_text(content, encoding=encoding)


def _run_loader(env_path: Path) -> None:
    """Helper: cd to ``env_path``'s parent, call loader, restore cwd.

    The loader reads ``Path(".env")`` relative to the CWD. Tests create
    ``tmp_path/.env`` and momentarily switch CWD to isolate from the real
    repo-root ``.env`` (which contains actual API keys that must not leak
    into the test's assertion surface).
    """
    from scripts.orchestrator import _load_dotenv_if_present  # type: ignore[attr-defined]

    cwd = os.getcwd()
    try:
        os.chdir(env_path.parent)
        _load_dotenv_if_present()
    finally:
        os.chdir(cwd)


# ---------------------------------------------------------------------------
# Edge cases 1-13 (RESEARCH §Pattern 2 matrix rows)
# ---------------------------------------------------------------------------


def test_basic_kv(tmp_path, preserve_env):
    """Row 1: KEY=value → os.environ['KEY'] == 'value'."""
    env = tmp_path / ".env"
    _write_env(env, "P11_BASIC_KEY=basic_value\n")
    os.environ.pop("P11_BASIC_KEY", None)

    _run_loader(env)

    assert os.environ["P11_BASIC_KEY"] == "basic_value"


def test_spaces_preserved_in_value(tmp_path, preserve_env):
    """Row 2: KEY=value with spaces → internal spaces preserved."""
    env = tmp_path / ".env"
    _write_env(env, "P11_SPACED=value with spaces\n")
    os.environ.pop("P11_SPACED", None)

    _run_loader(env)

    # Trailing whitespace stripped by regex \s*$; internal spaces preserved.
    assert os.environ["P11_SPACED"] == "value with spaces"


def test_double_quotes_stripped(tmp_path, preserve_env):
    """Row 3: KEY="quoted value" → surrounding double quotes removed."""
    env = tmp_path / ".env"
    _write_env(env, 'P11_DQ="quoted value"\n')
    os.environ.pop("P11_DQ", None)

    _run_loader(env)

    assert os.environ["P11_DQ"] == "quoted value"


def test_single_quotes_stripped(tmp_path, preserve_env):
    """Row 4: KEY='single' → surrounding single quotes removed."""
    env = tmp_path / ".env"
    _write_env(env, "P11_SQ='single'\n")
    os.environ.pop("P11_SQ", None)

    _run_loader(env)

    assert os.environ["P11_SQ"] == "single"


def test_multiple_equals_in_value(tmp_path, preserve_env):
    """Row 5: KEY=has=equals=signs → split on FIRST `=` only."""
    env = tmp_path / ".env"
    _write_env(env, "P11_MULTI=has=equals=signs\n")
    os.environ.pop("P11_MULTI", None)

    _run_loader(env)

    assert os.environ["P11_MULTI"] == "has=equals=signs"


def test_comments_ignored(tmp_path, preserve_env):
    """Row 6: `# comment` line → skipped; only KEY=v loaded."""
    env = tmp_path / ".env"
    _write_env(env, "# top comment\nP11_CMT=value\n")
    os.environ.pop("P11_CMT", None)

    _run_loader(env)

    assert os.environ["P11_CMT"] == "value"


def test_indented_comments_ignored(tmp_path, preserve_env):
    """Row 7: `   # indented` → skipped (leading whitespace OK before `#`)."""
    env = tmp_path / ".env"
    _write_env(env, "   # indented comment\nP11_IND=value\n")
    os.environ.pop("P11_IND", None)

    _run_loader(env)

    assert os.environ["P11_IND"] == "value"


def test_empty_lines_ignored(tmp_path, preserve_env):
    """Row 8: blank / whitespace-only lines → skipped."""
    env = tmp_path / ".env"
    _write_env(env, "\n\nP11_EMPTY=value\n\n\n")
    os.environ.pop("P11_EMPTY", None)

    _run_loader(env)

    assert os.environ["P11_EMPTY"] == "value"


def test_export_prefix_stripped(tmp_path, preserve_env):
    """Row 9: `export KEY=value` bash compat → prefix stripped."""
    env = tmp_path / ".env"
    _write_env(env, "export P11_EXP=value\n")
    os.environ.pop("P11_EXP", None)

    _run_loader(env)

    assert os.environ["P11_EXP"] == "value"


def test_utf8_bom_stripped(tmp_path, preserve_env):
    """Row 10: UTF-8 BOM on first line → tolerated (utf-8-sig decode)."""
    env = tmp_path / ".env"
    # Write BOM explicitly via bytes to guarantee its presence.
    env.write_bytes("\ufeffP11_BOM=value\n".encode("utf-8"))
    os.environ.pop("P11_BOM", None)

    _run_loader(env)

    assert os.environ["P11_BOM"] == "value"


def test_crlf_handled(tmp_path, preserve_env):
    """Row 11: `KEY=value\\r\\n` → trailing \\r stripped."""
    env = tmp_path / ".env"
    env.write_bytes(b"P11_CRLF=value\r\n")
    os.environ.pop("P11_CRLF", None)

    _run_loader(env)

    assert os.environ["P11_CRLF"] == "value"


def test_missing_file_silent(tmp_path, preserve_env):
    """Row 12: `.env` missing → no exception, env unchanged."""
    # Create an empty dir with no .env file.
    env_dir = tmp_path / "nonexistent_dir"
    env_dir.mkdir()

    from scripts.orchestrator import _load_dotenv_if_present  # type: ignore[attr-defined]

    # Snapshot env BEFORE invocation; silent skip must not mutate env.
    env_snapshot = dict(os.environ)

    cwd = os.getcwd()
    try:
        os.chdir(env_dir)
        # Must NOT raise.
        _load_dotenv_if_present()
    finally:
        os.chdir(cwd)

    # Env unchanged.
    assert dict(os.environ) == env_snapshot


def test_existing_env_wins(tmp_path, preserve_env):
    """Row 13: pre-existing env wins over .env value (setdefault semantics)."""
    env = tmp_path / ".env"
    _write_env(env, "P11_EXIST=from_env_file\n")
    os.environ["P11_EXIST"] = "from_shell"

    _run_loader(env)

    # setdefault: shell value wins.
    assert os.environ["P11_EXIST"] == "from_shell"


# ---------------------------------------------------------------------------
# Integration tests (public-API exposure + idempotency)
# ---------------------------------------------------------------------------


def test_idempotent_on_duplicate_call(tmp_path, preserve_env):
    """Bonus: calling loader twice preserves first value (setdefault no-op).

    This also guarantees safe re-import / re-call in pytest contexts where
    the package import may be triggered multiple times.
    """
    env = tmp_path / ".env"
    _write_env(env, "P11_IDEM=first\n")
    os.environ.pop("P11_IDEM", None)

    _run_loader(env)
    assert os.environ["P11_IDEM"] == "first"

    # Rewrite to "second" — existing value should still win on 2nd call.
    _write_env(env, "P11_IDEM=second\n")
    _run_loader(env)
    assert os.environ["P11_IDEM"] == "first"  # setdefault preserves first


def test_loader_exposed_via_package(preserve_env):
    """Public API contract: `_load_dotenv_if_present` importable + callable.

    Guarantees Task 2's placement at package `__init__.py` top-level exposes
    the symbol for downstream test harnesses.
    """
    from scripts.orchestrator import _load_dotenv_if_present  # noqa: F401

    assert callable(_load_dotenv_if_present)
