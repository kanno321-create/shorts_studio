"""Wave 3 PUB-03 D-07 — KST weekday window 20:00-22:59.

Anchors CONTEXT D-07 (평일 20-23 KST) + RESEARCH Pattern 4 + Anti-Patterns
(pytz deprecated -> zoneinfo only).

Boundary matrix (exclusive upper bound):
- 19:59 KST  -> FAIL  (before window)
- 20:00 KST  -> PASS  (start)
- 22:30 KST  -> PASS  (middle)
- 22:59 KST  -> PASS  (last valid minute)
- 23:00 KST  -> FAIL  (upper bound exclusive)
- weekday 12:00 KST -> FAIL  (weekend-only window does not apply to weekday)
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from scripts.publisher.exceptions import PublishWindowViolation
from scripts.publisher.kst_window import assert_in_window, KST


def _kst(year, month, day, hour, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=KST)


def test_monday_1959_fails():
    """2026-04-20 is Monday. 19:59 KST is outside the window (starts 20:00)."""
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 20, 19, 59))


def test_monday_2000_passes():
    assert_in_window(now_kst=_kst(2026, 4, 20, 20, 0))


def test_monday_2230_passes():
    assert_in_window(now_kst=_kst(2026, 4, 20, 22, 30))


def test_monday_2259_passes():
    assert_in_window(now_kst=_kst(2026, 4, 20, 22, 59))


def test_monday_2300_fails():
    """Upper bound is exclusive (< 23)."""
    with pytest.raises(PublishWindowViolation) as exc_info:
        assert_in_window(now_kst=_kst(2026, 4, 20, 23, 0))
    assert exc_info.value.hour == 23


def test_friday_2100_passes():
    """2026-04-24 is Friday."""
    assert_in_window(now_kst=_kst(2026, 4, 24, 21, 0))


def test_friday_0900_fails():
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 24, 9, 0))


def test_tuesday_2200_passes():
    assert_in_window(now_kst=_kst(2026, 4, 21, 22, 0))


def test_wednesday_1200_fails():
    """Weekday noon is NOT weekend window — weekday rules only (20-23)."""
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 22, 12, 0))


def test_thursday_0000_fails():
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 23, 0, 0))


def test_kst_is_zoneinfo_asia_seoul():
    assert KST == ZoneInfo("Asia/Seoul")


def test_no_pytz_import_in_source():
    from pathlib import Path
    source = Path("scripts/publisher/kst_window.py").read_text(encoding="utf-8")
    assert "import pytz" not in source, "Anti-Pattern: pytz deprecated; use zoneinfo"
    assert "from pytz" not in source
