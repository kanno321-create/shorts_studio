"""Phase 11 shared fixtures.

Provides fixtures for PIPELINE-01 (stdin invoker), PIPELINE-02 (.env loader),
PIPELINE-03 (adapter degrade), PIPELINE-04 (wrapper), AUDIT-05 (idempotency),
and SCRIPT-01 (quality decision capture).

Phase 5/6/10 conftest pattern followed: `_REPO_ROOT` import-time resolve +
`sys.path` insert so tests can `import scripts.orchestrator.invokers`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

import pytest

# Windows cp949 stdout guard — Korean text round-trip safety.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# tests/phase11/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def tmp_env_file(tmp_path: Path) -> Path:
    """Return Path to an empty tmp `.env` — tests fill contents as needed."""
    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")
    return env_path


@pytest.fixture
def mock_cli_runner() -> MagicMock:
    """Drop-in replacement for `cli_runner` test seam (returns canned JSON)."""
    runner = MagicMock()
    runner.return_value = '{"status": "ok"}'
    return runner


@pytest.fixture
def fake_claude_cli_runner_factory() -> Callable[[str], MagicMock]:
    """Build a cli_runner that returns a given canned JSON payload."""

    def _build(payload: str) -> MagicMock:
        runner = MagicMock()
        runner.return_value = payload
        return runner

    return _build


@pytest.fixture
def preserve_env():
    """Restore `os.environ` after test — prevents `.env` loader leakage."""
    saved = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)
