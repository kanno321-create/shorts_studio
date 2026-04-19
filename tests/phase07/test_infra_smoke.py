"""Wave 0 smoke — verifies tests/phase07/ scaffold and fixtures are in place.

Written as Phase 7 Wave 0 gate per 07-01-PLAN.md task 7-01-01.
"""
from __future__ import annotations

from pathlib import Path

import pytest


_FIXTURES = Path(__file__).resolve().parent / "fixtures"

_REQUIRED_FIXTURES = [
    "mock_kling.mp4",
    "mock_runway.mp4",
    "mock_typecast.wav",
    "mock_elevenlabs.wav",
    "mock_shotstack.mp4",
    "still_image.jpg",
]


def test_phase07_package_marker_exists():
    assert (Path(__file__).resolve().parent / "__init__.py").exists()


def test_fixtures_package_marker_exists():
    assert (_FIXTURES / "__init__.py").exists()


@pytest.mark.parametrize("name", _REQUIRED_FIXTURES)
def test_fixture_file_exists(name: str):
    p = _FIXTURES / name
    assert p.exists(), f"Wave 0 missing fixture: {p}"


def test_fake_env_fixture_sets_5_keys(_fake_env, monkeypatch):
    import os

    for var in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        assert os.environ.get(var) == "fake", f"{var} not set to 'fake' by _fake_env"


def test_tmp_session_id_is_deterministic(tmp_session_id):
    assert tmp_session_id == "tst_phase07_e2e"


def test_pass_verdict_shape(mock_pass_verdict):
    assert mock_pass_verdict.result == "PASS"
    assert mock_pass_verdict.score == 90


def test_fail_verdict_shape(mock_fail_verdict):
    assert mock_fail_verdict.result == "FAIL"
    assert mock_fail_verdict.evidence[0]["rule"] == "thumbnail_hook_weak"


def test_repo_root_fixture_points_to_studios_shorts(repo_root):
    assert repo_root.exists()
    assert (repo_root / "CLAUDE.md").exists(), f"repo_root not pointing to studios/shorts: {repo_root}"


def test_phase07_fixtures_fixture_points_to_fixtures_dir(phase07_fixtures):
    assert phase07_fixtures == _FIXTURES
