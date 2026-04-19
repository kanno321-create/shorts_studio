"""Phase 6 shared pytest fixtures.

Follows Phase 5 STATE decision #40 pattern: resolve _REPO_ROOT at import
time so module-scoped fixtures do not ScopeMismatch against function-scoped
``repo_root``.

Fixtures provided:
    - repo_root                 : absolute Path to studios/shorts/ repo root
    - fixtures_dir              : Path to tests/phase06/fixtures/
    - tmp_wiki_dir              : per-test sandbox wiki root with 5 empty category subdirs
    - wiki_node_valid_text      : raw text of the valid D-17 sample
    - wiki_node_missing_text    : raw text of the intentionally-incomplete sample
    - library_json_delta        : parsed D-8 naberal-shorts-channel-bible entry
    - mock_notebooklm_skill_env : per-test NOTEBOOKLM_SKILL_PATH pointing at a fake skill dir
    - failures_sample_text      : raw text of FAIL-NNN schema sample
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

# tests/phase06/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def repo_root() -> pathlib.Path:
    """Absolute Path to studios/shorts/ repo root."""
    return _REPO_ROOT


@pytest.fixture
def fixtures_dir() -> pathlib.Path:
    """Absolute Path to tests/phase06/fixtures/."""
    return _FIXTURES


@pytest.fixture
def tmp_wiki_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Per-test sandbox wiki root with 5 empty D-2 category subdirs."""
    root = tmp_path / "wiki"
    for cat in ("algorithm", "ypp", "render", "kpi", "continuity_bible"):
        (root / cat).mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def wiki_node_valid_text() -> str:
    """Raw text of tests/phase06/fixtures/wiki_node_valid.md (valid D-17)."""
    return (_FIXTURES / "wiki_node_valid.md").read_text(encoding="utf-8")


@pytest.fixture
def wiki_node_missing_text() -> str:
    """Raw text of the intentionally-incomplete D-17 sample (missing source_notebook)."""
    return (_FIXTURES / "wiki_node_missing_fields.md").read_text(encoding="utf-8")


@pytest.fixture
def library_json_delta() -> dict:
    """Parsed D-8 library.json append entry (naberal-shorts-channel-bible)."""
    return json.loads(
        (_FIXTURES / "library_json_delta.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def mock_notebooklm_skill_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> pathlib.Path:
    """Point NOTEBOOKLM_SKILL_PATH at a fake skill dir.

    Prevents tests from hitting the real external secondjob_naberal Playwright
    skill. Returns the fake path so tests can assert subprocess call-shape.
    """
    fake = tmp_path / "fake_skill"
    (fake / "scripts").mkdir(parents=True)
    (fake / "data").mkdir()
    (fake / "scripts" / "run.py").write_text(
        "print('fake answer')\n", encoding="utf-8"
    )
    (fake / "data" / "library.json").write_text(
        json.dumps({"notebooks": {}}), encoding="utf-8"
    )
    monkeypatch.setenv("NOTEBOOKLM_SKILL_PATH", str(fake))
    return fake


@pytest.fixture
def failures_sample_text() -> str:
    """Raw text of the FAIL-NNN schema sample (for Plan 09 aggregator tests)."""
    return (_FIXTURES / "failures_sample.md").read_text(encoding="utf-8")
