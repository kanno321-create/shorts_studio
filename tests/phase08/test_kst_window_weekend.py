"""Wave 3 PUB-03 D-07 — KST weekend window 12:00-14:59.

Anchors CONTEXT D-07 (주말 12-15 KST) with exclusive upper bound.

Boundary matrix:
- Saturday 11:59 KST -> FAIL (before window)
- Saturday 12:00 KST -> PASS (start)
- Saturday 13:30 KST -> PASS (middle)
- Saturday 14:59 KST -> PASS (last valid minute)
- Saturday 15:00 KST -> FAIL (upper bound exclusive)
- Sunday 21:00 KST  -> FAIL (weekday peak does not apply on weekends)
- Violation carries weekday + hour attributes (CD-02 hierarchy).
"""
from __future__ import annotations

from datetime import datetime

import pytest

from scripts.publisher.exceptions import PublishWindowViolation
from scripts.publisher.kst_window import assert_in_window, KST


def _kst(year, month, day, hour, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=KST)


def test_saturday_1159_fails():
    """2026-04-25 is Saturday. 11:59 KST is outside weekend window."""
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 25, 11, 59))


def test_saturday_1200_passes():
    assert_in_window(now_kst=_kst(2026, 4, 25, 12, 0))


def test_saturday_1330_passes():
    assert_in_window(now_kst=_kst(2026, 4, 25, 13, 30))


def test_saturday_1459_passes():
    assert_in_window(now_kst=_kst(2026, 4, 25, 14, 59))


def test_saturday_1500_fails():
    """Upper bound exclusive (< 15)."""
    with pytest.raises(PublishWindowViolation) as exc_info:
        assert_in_window(now_kst=_kst(2026, 4, 25, 15, 0))
    assert exc_info.value.hour == 15


def test_sunday_1330_passes():
    """2026-04-26 is Sunday."""
    assert_in_window(now_kst=_kst(2026, 4, 26, 13, 30))


def test_sunday_2100_fails():
    """Weekday peak window does NOT apply on weekends."""
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 26, 21, 0))


def test_sunday_0900_fails():
    with pytest.raises(PublishWindowViolation):
        assert_in_window(now_kst=_kst(2026, 4, 26, 9, 0))


def test_violation_carries_weekday_and_hour():
    with pytest.raises(PublishWindowViolation) as exc_info:
        assert_in_window(now_kst=_kst(2026, 4, 25, 9, 0))   # Saturday
    assert exc_info.value.weekday == 5   # Saturday
    assert exc_info.value.hour == 9
