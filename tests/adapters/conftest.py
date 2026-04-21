"""Phase 14 — tests/adapters/ 공용 fixture.

Contract 테스트 3종 (veo_i2v / elevenlabs / shotstack) 이 Phase 5 conftest
의 ``repo_root`` + Phase 7 mocks 를 공통적으로 의존하므로 본 conftest 에서
re-export 합니다. Production code 는 절대 건드리지 않고 monkeypatch 만
사용합니다.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

# Phase 5/7 fixture 재사용을 위한 PYTHONPATH 보강.
# tests/adapters/conftest.py -> parents[2] = studios/shorts/
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Phase 14 root — tests/phase05/conftest.py 와 동일 계약."""
    return REPO_ROOT


@pytest.fixture
def _fake_env(monkeypatch):
    """Phase 5 precedent — 알려진 adapter env key 를 wipe 후 fake 값 주입.

    Contract 테스트는 monkeypatch 경유로 env 를 설정하므로 본 fixture 는
    baseline wipe + 공통 fake 값을 제공합니다. 실패 시 명시적 raise — 침묵
    폴백 금지 (CLAUDE.md 금기사항 #3).
    """
    for key in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "VEO_API_KEY",
        "FAL_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "ELEVEN_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KLING_API_KEY", "fake-kling")
    monkeypatch.setenv("VEO_API_KEY", "fake-veo")
    monkeypatch.setenv("TYPECAST_API_KEY", "fake-tc")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-el")
    monkeypatch.setenv("SHOTSTACK_API_KEY", "fake-ss")
