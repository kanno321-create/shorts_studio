"""Wave 3 PUB-03 — 48h+ jitter lock enforcement.

Anchors RESEARCH Pattern 3 (atomic `os.replace`) + CONTEXT D-06 (filesystem JSON
lock at ``.planning/publish_lock.json`` with SHORTS_PUBLISH_LOCK_PATH env override
for test isolation via the ``tmp_publish_lock`` fixture from conftest).

Boundary case matrix:
- No lock file              -> passes (first-ever upload)
- 47h elapsed, 0 jitter     -> raises (~1h remaining)
- 48h+1s elapsed, 0 jitter  -> passes
- 49h elapsed, 0 jitter     -> passes
- 59h59m elapsed, 720m jit  -> raises (60h required)
- 60h+1s elapsed, 720m jit  -> passes
- record_upload writes atomic dict with _schema=1 + no .tmp residue
- random.randint bounds respected
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from scripts.publisher.exceptions import PublishLockViolation
import scripts.publisher.publish_lock as pl


def _write_lock(lock_path: Path, last: datetime, jitter_min: int = 0) -> None:
    lock_path.write_text(json.dumps({
        "last_upload_iso": last.isoformat(),
        "jitter_applied_min": jitter_min,
        "_schema": 1,
    }, ensure_ascii=False), encoding="utf-8")


def test_no_lock_file_passes(tmp_publish_lock):
    assert not tmp_publish_lock.exists()
    pl.assert_can_publish()   # does not raise


def test_47h_elapsed_zero_jitter_raises(tmp_publish_lock):
    last = datetime.now(timezone.utc) - timedelta(hours=47)
    _write_lock(tmp_publish_lock, last, jitter_min=0)
    with pytest.raises(PublishLockViolation) as exc_info:
        pl.assert_can_publish()
    assert exc_info.value.remaining_min >= 1
    assert exc_info.value.remaining_min <= 60   # ~1h remaining


def test_48h_exact_zero_jitter_passes(tmp_publish_lock):
    last = datetime.now(timezone.utc) - timedelta(hours=48, seconds=1)
    _write_lock(tmp_publish_lock, last, jitter_min=0)
    pl.assert_can_publish()   # 48h+1s elapsed, 0 jitter -> passes


def test_49h_zero_jitter_passes(tmp_publish_lock):
    last = datetime.now(timezone.utc) - timedelta(hours=49)
    _write_lock(tmp_publish_lock, last, jitter_min=0)
    pl.assert_can_publish()


def test_48h_720min_jitter_requires_60h(tmp_publish_lock):
    """48h + 720min jitter = 60h total required; 59h59m MUST still block."""
    last = datetime.now(timezone.utc) - timedelta(hours=59, minutes=59)
    _write_lock(tmp_publish_lock, last, jitter_min=720)   # 48h+12h = 60h
    with pytest.raises(PublishLockViolation) as exc_info:
        pl.assert_can_publish()
    assert exc_info.value.remaining_min >= 1


def test_48h_720min_jitter_60h_passes(tmp_publish_lock):
    last = datetime.now(timezone.utc) - timedelta(hours=60, seconds=1)
    _write_lock(tmp_publish_lock, last, jitter_min=720)
    pl.assert_can_publish()


def test_record_upload_writes_atomic(tmp_publish_lock):
    pl.record_upload(now_utc=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
                     jitter_min=300)
    assert tmp_publish_lock.exists()
    data = json.loads(tmp_publish_lock.read_text(encoding="utf-8"))
    assert data["last_upload_iso"].startswith("2026-04-19T12:00:00")
    assert data["jitter_applied_min"] == 300
    assert data["_schema"] == 1


def test_record_upload_no_tmp_residue(tmp_publish_lock):
    pl.record_upload(jitter_min=0)
    tmp_file = tmp_publish_lock.with_suffix(".tmp")
    assert not tmp_file.exists(), "os.replace atomic guarantee violated"


def test_record_upload_jitter_bounds(tmp_publish_lock, monkeypatch):
    """Default random.randint MUST stay within [0, MAX_JITTER_MIN]."""
    monkeypatch.setattr(pl.random, "randint", lambda a, b: b)   # max
    pl.record_upload()
    data = json.loads(tmp_publish_lock.read_text(encoding="utf-8"))
    assert data["jitter_applied_min"] == pl.MAX_JITTER_MIN


def test_min_elapsed_hours_is_48():
    assert pl.MIN_ELAPSED_HOURS == 48


def test_max_jitter_min_is_720():
    assert pl.MAX_JITTER_MIN == 720
