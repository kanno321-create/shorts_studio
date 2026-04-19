"""Wave 0 smoke — verifies tests/phase08/ scaffold + fixtures exist.

Task 8-01-01 gate test. Confirms:
- 3 __init__.py package markers exist
- sample_shorts.mp4 is exactly 1 byte (deterministic sha256)
- sample_production_metadata.json has the 4-field PUB-04 schema
- 6 conftest fixtures resolve at test time
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_phase08_package_marker_exists():
    assert (Path(__file__).resolve().parent / "__init__.py").exists()


def test_mocks_package_marker_exists():
    assert (Path(__file__).resolve().parent / "mocks" / "__init__.py").exists()


def test_fixtures_package_marker_exists():
    assert (_FIXTURES / "__init__.py").exists()


def test_sample_mp4_is_one_byte():
    p = _FIXTURES / "sample_shorts.mp4"
    assert p.exists()
    assert p.stat().st_size == 1, (
        f"Expected 1 byte for deterministic checksum, got {p.stat().st_size}"
    )


def test_sample_production_metadata_has_4_fields():
    p = _FIXTURES / "sample_production_metadata.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    required = {"script_seed", "assets_origin", "pipeline_version", "checksum"}
    missing = required - set(data.keys())
    assert not missing, f"PUB-04 4-field invariant broken: missing {missing}"


def test_tmp_publish_lock_fixture(tmp_publish_lock):
    # Path provided but file not yet written by the fixture itself.
    assert not tmp_publish_lock.exists()
    assert os.environ.get("SHORTS_PUBLISH_LOCK_PATH") == str(tmp_publish_lock)


def test_mock_client_secret_fixture(mock_client_secret):
    assert mock_client_secret.exists()
    data = json.loads(mock_client_secret.read_text(encoding="utf-8"))
    assert data["installed"]["redirect_uris"] == ["http://localhost"]


def test_mock_youtube_credentials_fixture(mock_youtube_credentials):
    assert mock_youtube_credentials.valid is True
    assert "fake-refresh" in mock_youtube_credentials.to_json()


def test_sample_mp4_path_fixture(sample_mp4_path):
    assert sample_mp4_path.name == "sample_shorts.mp4"
    assert sample_mp4_path.exists()


def test_fake_env_github_token_fixture(fake_env_github_token):
    assert os.environ.get("GITHUB_TOKEN") == fake_env_github_token
    assert fake_env_github_token.startswith("ghp_")


def test_kst_clock_freeze_fixture(kst_clock_freeze):
    frozen = kst_clock_freeze(weekday=0, hour=21)  # Monday 21:00 KST
    assert frozen.weekday() == 0
    assert frozen.hour == 21


def test_kst_clock_freeze_sunday(kst_clock_freeze):
    frozen = kst_clock_freeze(weekday=6, hour=13)  # Sunday 13:00 KST
    assert frozen.weekday() == 6
    assert frozen.hour == 13


def test_kst_clock_freeze_rejects_invalid_weekday(kst_clock_freeze):
    with pytest.raises(ValueError):
        kst_clock_freeze(weekday=7, hour=10)
