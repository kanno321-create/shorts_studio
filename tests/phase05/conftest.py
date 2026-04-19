"""Phase 5 shared pytest fixtures.

Uses STATE.md session #16 decision #40 pattern: resolve _REPO_ROOT at
import time to avoid pytest ScopeMismatch when module-scoped fixtures
would otherwise depend on function-scoped ones.

Fixtures provided:
    - tmp_state_dir        : per-test isolated state/ directory (Checkpointer)
    - sample_verdict_pass  : rubric-schema draft-07 Verdict with result=PASS
    - sample_verdict_fail  : Verdict with result=FAIL + 2 evidence entries
    - mock_audio_timestamps: word-level timings for VoiceFirstTimeline tests
    - repo_root            : absolute Path to studios/shorts/ repo root
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

# Resolve repo root at import time — session #16 decision #40 pattern.
# tests/phase05/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def tmp_state_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Per-test isolated Checkpointer root; yielded as a Path."""
    state = tmp_path / "state"
    state.mkdir(parents=True, exist_ok=True)
    return state


@pytest.fixture
def sample_verdict_pass() -> dict:
    """Rubric-schema Verdict with result=PASS."""
    return _load_fixture("verdict_pass.json")


@pytest.fixture
def sample_verdict_fail() -> dict:
    """Rubric-schema Verdict with result=FAIL + evidence[]."""
    return _load_fixture("verdict_fail.json")


@pytest.fixture
def mock_audio_timestamps() -> dict:
    """Word-level audio timings for VoiceFirstTimeline (Plan 05) tests."""
    return _load_fixture("mock_audio_timestamps.json")


@pytest.fixture
def repo_root() -> pathlib.Path:
    """Absolute Path to studios/shorts/ repo root."""
    return _REPO_ROOT
