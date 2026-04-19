"""Phase 7 integration-test shared fixtures (D-13: independent from phase05/06 conftests).

Per 07-CONTEXT.md §D-13 ('Phase 5/6 conftest 복사 금지 — Phase별 fixture 독립 원칙'),
every fixture here is purpose-built for Phase 7 E2E + fault-injection + harness-audit
scenarios. We intentionally do NOT re-export fixtures from tests/phase05 or tests/phase06
so each phase owns its own fixture contracts.

Fixtures provided
-----------------
- repo_root               : absolute Path to studios/shorts/ repo root
- phase07_fixtures        : absolute Path to tests/phase07/fixtures/
- _fake_env               : monkeypatches 5 adapter API keys to 'fake'
- tmp_session_id          : deterministic session id 'tst_phase07_e2e' (D-21)
- mock_pass_verdict       : scripts.orchestrator.Verdict with result=PASS score=90
- mock_fail_verdict       : scripts.orchestrator.Verdict with result=FAIL + evidence
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Resolve-at-import pattern from session #16 decision #40 (phase05/phase06 precedent).
# tests/phase07/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).resolve().parent / "fixtures"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def repo_root() -> Path:
    """Absolute path to studios/shorts repo root."""
    return _REPO_ROOT


@pytest.fixture
def phase07_fixtures() -> Path:
    """Absolute path to tests/phase07/fixtures/ directory."""
    return _FIXTURES


@pytest.fixture
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set 5 API keys to 'fake' so adapter constructors do not raise ValueError.

    Phase 5 precedent (tests/phase05/test_pipeline_e2e_mock.py:40-48). MagicMock
    adapters bypass real network; 'fake' value is never transmitted.
    """
    for var in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        monkeypatch.setenv(var, "fake")


@pytest.fixture
def tmp_session_id() -> str:
    """Deterministic session id for Phase 7 E2E runs (D-21)."""
    return "tst_phase07_e2e"


@pytest.fixture
def mock_pass_verdict():
    """Verdict(result=PASS, score=90) — shorts-supervisor canonical PASS."""
    from scripts.orchestrator import Verdict

    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


@pytest.fixture
def mock_fail_verdict():
    """Verdict(result=FAIL, score=20) with thumbnail_hook_weak evidence row."""
    from scripts.orchestrator import Verdict

    return Verdict(
        result="FAIL",
        score=20,
        evidence=[{"rule": "thumbnail_hook_weak", "detail": "no face, no caption"}],
        semantic_feedback="face + caption missing",
        inspector_name="ins-thumbnail-hook",
    )
