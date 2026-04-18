"""Phase 4 Wave 0 pytest fixtures.

Provides session-scoped loaders for the 3 shared JSON banks + rubric schema,
plus a per-test agent_md_loader that parses frontmatter via stdlib.

All fixtures operate against the repo root (Path.cwd() must be studios/shorts/).
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

# Ensure repo root is importable (scripts.validate.*)
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402
from scripts.validate.rubric_stdlib_validator import validate_rubric  # noqa: E402


@pytest.fixture(scope="session")
def rubric_schema():
    """Load .claude/agents/_shared/rubric-schema.json once per session."""
    return json.loads(
        (_REPO_ROOT / ".claude/agents/_shared/rubric-schema.json").read_text("utf-8")
    )


@pytest.fixture(scope="session")
def supervisor_rubric_schema():
    """Load .claude/agents/_shared/supervisor-rubric-schema.json."""
    return json.loads(
        (_REPO_ROOT / ".claude/agents/_shared/supervisor-rubric-schema.json").read_text("utf-8")
    )


@pytest.fixture(scope="session")
def af_bank():
    """Load .claude/agents/_shared/af_bank.json."""
    return json.loads(
        (_REPO_ROOT / ".claude/agents/_shared/af_bank.json").read_text("utf-8")
    )


@pytest.fixture(scope="session")
def korean_samples():
    """Load .claude/agents/_shared/korean_speech_samples.json."""
    return json.loads(
        (_REPO_ROOT / ".claude/agents/_shared/korean_speech_samples.json").read_text("utf-8")
    )


@pytest.fixture
def agent_md_loader():
    """Return a loader(path_str) -> (meta_dict, body_str) using stdlib frontmatter parser."""

    def _load(path: str):
        p = pathlib.Path(path)
        if not p.is_absolute():
            p = _REPO_ROOT / p
        return parse_frontmatter(p)

    return _load


@pytest.fixture
def validate_rubric_fn():
    """Return the stdlib-only validate_rubric function directly."""
    return validate_rubric


@pytest.fixture
def repo_root():
    """Absolute Path to studios/shorts/ repo root."""
    return _REPO_ROOT
