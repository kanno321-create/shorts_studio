"""Phase 8 publishing shared fixtures (D-13: independent from phase05/06/07 conftests).

Per 08-CONTEXT.md D-10/D-13 + Phase 7 precedent: purpose-built Phase 8 fixtures.
No imports from tests/phase05 / tests/phase06 / tests/phase07 conftests.

Fixtures provided
-----------------
- tmp_publish_lock           : tmp_path/publish_lock.json redirected via SHORTS_PUBLISH_LOCK_PATH
- mock_client_secret         : minimal client_secret.json for InstalledAppFlow tests
- mock_youtube_credentials   : object with .valid=True and .to_json()
- sample_mp4_path            : absolute Path to 1-byte tests/phase08/fixtures/sample_shorts.mp4
- fake_env_github_token      : monkeypatched GITHUB_TOKEN=ghp_fake_token_for_tests_only
- kst_clock_freeze           : callable(weekday, hour) -> frozen KST datetime
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# UTF-8 safeguard for Windows cp949 per Phase 6 Plan 06-09 STATE #28 + Pitfall 3
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Resolve-at-import _REPO_ROOT pattern (Phase 7 precedent).
# tests/phase08/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
KST = ZoneInfo("Asia/Seoul")

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def tmp_publish_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirects .planning/publish_lock.json to tmp_path for isolation."""
    lock = tmp_path / "publish_lock.json"
    monkeypatch.setenv("SHORTS_PUBLISH_LOCK_PATH", str(lock))
    return lock


@pytest.fixture
def mock_client_secret(tmp_path: Path) -> Path:
    """Synthesizes a minimal client_secret.json shape for InstalledAppFlow testing."""
    p = tmp_path / "client_secret.json"
    p.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "fake.apps.googleusercontent.com",
                    "project_id": "fake-proj",
                    "client_secret": "fake-secret",
                    "redirect_uris": ["http://localhost"],
                }
            }
        ),
        encoding="utf-8",
    )
    return p


@pytest.fixture
def mock_youtube_credentials(monkeypatch: pytest.MonkeyPatch):
    """Returns an object with .valid=True and .to_json() for refresh-skip paths."""

    class _Creds:
        valid = True
        expired = False
        refresh_token = "fake-refresh"

        def to_json(self) -> str:
            return '{"refresh_token":"fake-refresh","valid":true}'

        def refresh(self, request) -> None:
            self.valid = True

    return _Creds()


@pytest.fixture
def sample_mp4_path() -> Path:
    """Absolute path to the 1-byte sample_shorts.mp4 fixture."""
    return _FIXTURES / "sample_shorts.mp4"


@pytest.fixture
def fake_env_github_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """Injects GITHUB_TOKEN=ghp_fake_token_for_tests_only into env for the test."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake_token_for_tests_only")
    return "ghp_fake_token_for_tests_only"


@pytest.fixture
def kst_clock_freeze(monkeypatch: pytest.MonkeyPatch):
    """Returns a callable taking (weekday, hour) to produce a frozen KST datetime.

    weekday: 0..6 (Mon..Sun). Uses 2026-04-20 (Monday) as base and offsets days.
    Callers can use the returned datetime as the reference "now" value in their
    kst_window tests; downstream plans may monkeypatch datetime.now via this hook.
    """
    # Validate 2026-04-20 is Monday (sanity check — if date/lib ever drifts).
    assert datetime(2026, 4, 20).weekday() == 0, "2026-04-20 must be Monday"

    def _freeze(weekday: int, hour: int) -> datetime:
        if not 0 <= weekday <= 6:
            raise ValueError(f"weekday must be 0..6, got {weekday}")
        if not 0 <= hour <= 23:
            raise ValueError(f"hour must be 0..23, got {hour}")
        # 2026-04-20 Monday .. 2026-04-26 Sunday
        day = 20 + weekday
        frozen = datetime(2026, 4, day, hour, 0, 0, tzinfo=KST)
        return frozen

    return _freeze
