"""Phase 10 Plan 08 — Rollback procedures tests.

Tests for ``scripts.rollback.stop_scheduler`` CLI — emergency shutdown covering:
- publish_lock future-timestamping (reverse-use of Phase 8 48h+jitter gate)
- Windows Task Scheduler unregister (PowerShell subprocess)
- --dry-run mode (zero side effects)
- non-Windows platform graceful skip
- CLI JSON output contract
- SHORTS_PUBLISH_LOCK_PATH env override

All tests are isolated: no real schtasks call, no real publish_lock.json write
outside tmp_path. subprocess.run + sys.platform monkey-patched where needed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# tests/phase10/conftest.py already inserts studios/shorts/ onto sys.path.


def _fixed_now() -> datetime:
    """Deterministic UTC clock used across tests."""
    return datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Test 1: block_publish writes future ISO
# ---------------------------------------------------------------------------
def test_block_publish_lock_writes_future_iso(tmp_path: Path) -> None:
    from scripts.rollback.stop_scheduler import block_publish
    lock_path = tmp_path / "publish_lock.json"
    now = _fixed_now()
    payload = block_publish(lock_path, hours=49, now=now)
    # File exists + payload returned matches file content
    assert lock_path.exists()
    on_disk = json.loads(lock_path.read_text(encoding="utf-8"))
    assert on_disk == payload
    # last_upload_iso is 49h in the future
    last = datetime.fromisoformat(on_disk["last_upload_iso"])
    expected = now + timedelta(hours=49)
    assert last == expected
    # And future relative to "now"
    assert last > now


# ---------------------------------------------------------------------------
# Test 2: block_publish preserves publish_lock.py schema
# ---------------------------------------------------------------------------
def test_block_publish_lock_preserves_schema(tmp_path: Path) -> None:
    from scripts.rollback.stop_scheduler import block_publish
    lock_path = tmp_path / "publish_lock.json"
    payload = block_publish(lock_path, hours=72, now=_fixed_now())
    # Schema contract must match scripts.publisher.publish_lock record_upload()
    assert payload["_schema"] == 1
    assert payload["jitter_applied_min"] == 0
    assert "last_upload_iso" in payload
    # Only these three keys — no pollution
    assert set(payload.keys()) == {"last_upload_iso", "jitter_applied_min", "_schema"}


# ---------------------------------------------------------------------------
# Test 3: unregister_windows_tasks calls PowerShell correctly on win32
# ---------------------------------------------------------------------------
def test_unregister_tasks_calls_powershell(monkeypatch: pytest.MonkeyPatch,
                                           tmp_path: Path) -> None:
    import scripts.rollback.stop_scheduler as ss
    ps1 = tmp_path / "windows_tasks.ps1"
    ps1.write_text("# fake ps1\n", encoding="utf-8")

    mock_run = MagicMock(return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout="ok", stderr=""
    ))
    monkeypatch.setattr(ss, "sys", type("S", (), {"platform": "win32"})())
    monkeypatch.setattr(ss.subprocess, "run", mock_run)

    result = ss.unregister_windows_tasks(ps1, dry_run=False)

    assert mock_run.call_count == 1
    call_args = mock_run.call_args[0][0]  # positional args[0] == cmd list
    assert call_args[0] == "powershell.exe"
    assert "-File" in call_args
    assert str(ps1) in call_args
    assert "-Unregister" in call_args
    assert result["unregistered"] is True
    assert result["returncode"] == 0
    assert result["platform"] == "win32"


# ---------------------------------------------------------------------------
# Test 4: --dry-run never invokes subprocess
# ---------------------------------------------------------------------------
def test_unregister_tasks_dry_run_no_subprocess(monkeypatch: pytest.MonkeyPatch,
                                                tmp_path: Path) -> None:
    import scripts.rollback.stop_scheduler as ss
    ps1 = tmp_path / "windows_tasks.ps1"
    ps1.write_text("# fake ps1\n", encoding="utf-8")

    mock_run = MagicMock()
    monkeypatch.setattr(ss, "sys", type("S", (), {"platform": "win32"})())
    monkeypatch.setattr(ss.subprocess, "run", mock_run)

    result = ss.unregister_windows_tasks(ps1, dry_run=True)

    # Zero subprocess calls — dry-run contract
    assert mock_run.call_count == 0
    assert result["dry_run"] is True
    assert result["unregistered"] is False
    assert "would_unregister" in result
    assert set(result["would_unregister"]) == {
        "ShortsStudio_Pipeline",
        "ShortsStudio_Upload",
        "ShortsStudio_NotifyFailure",
    }


# ---------------------------------------------------------------------------
# Test 5: main() invokes both publish_lock + unregister
# ---------------------------------------------------------------------------
def test_stop_scheduler_main_does_both(monkeypatch: pytest.MonkeyPatch,
                                       tmp_path: Path, capsys) -> None:
    import scripts.rollback.stop_scheduler as ss
    lock = tmp_path / "publish_lock.json"
    ps1 = tmp_path / "windows_tasks.ps1"
    ps1.write_text("# fake\n", encoding="utf-8")

    mock_run = MagicMock(return_value=subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    ))
    monkeypatch.setattr(ss, "sys", type("S", (), {"platform": "win32",
                                                   "stdout": sys.stdout})())
    monkeypatch.setattr(ss.subprocess, "run", mock_run)

    rc = ss.main([
        "--lock-path", str(lock),
        "--ps1", str(ps1),
        "--block-hours", "49",
    ])
    assert rc == 0
    # Lock file was written
    assert lock.exists()
    # Subprocess invoked exactly once for Unregister
    assert mock_run.call_count == 1
    # stdout JSON parseable
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "invocation_ts" in parsed
    assert "publish_lock" in parsed
    assert parsed["block_hours"] == 49
    assert parsed["tasks_unregister"]["unregistered"] is True


# ---------------------------------------------------------------------------
# Test 6: SHORTS_PUBLISH_LOCK_PATH env override respected
# ---------------------------------------------------------------------------
def test_stop_scheduler_respects_env_override(monkeypatch: pytest.MonkeyPatch,
                                              tmp_path: Path, capsys) -> None:
    import scripts.rollback.stop_scheduler as ss
    custom_lock = tmp_path / "custom_lock.json"
    monkeypatch.setenv("SHORTS_PUBLISH_LOCK_PATH", str(custom_lock))
    # Force non-win32 so we skip subprocess entirely
    monkeypatch.setattr(ss, "sys", type("S", (), {"platform": "linux",
                                                   "stdout": sys.stdout})())

    rc = ss.main(["--skip-unregister", "--block-hours", "49"])
    assert rc == 0
    assert custom_lock.exists()
    data = json.loads(custom_lock.read_text(encoding="utf-8"))
    assert data["_schema"] == 1
    assert "last_upload_iso" in data


# ---------------------------------------------------------------------------
# Test 7: non-Windows platform → PowerShell skip + reason
# ---------------------------------------------------------------------------
def test_stop_scheduler_platform_warning_on_non_windows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import scripts.rollback.stop_scheduler as ss
    ps1 = tmp_path / "windows_tasks.ps1"

    mock_run = MagicMock()
    monkeypatch.setattr(ss, "sys", type("S", (), {"platform": "linux"})())
    monkeypatch.setattr(ss.subprocess, "run", mock_run)

    result = ss.unregister_windows_tasks(ps1, dry_run=False)

    # Zero subprocess calls on non-Windows
    assert mock_run.call_count == 0
    assert result["unregistered"] is False
    assert result["platform"] == "linux"
    assert "non-Windows" in result["reason"]
    assert result["tasks"] == [
        "ShortsStudio_Pipeline",
        "ShortsStudio_Upload",
        "ShortsStudio_NotifyFailure",
    ]


# ---------------------------------------------------------------------------
# Test 8: CLI always emits JSON with required keys
# ---------------------------------------------------------------------------
def test_stop_scheduler_json_output(monkeypatch: pytest.MonkeyPatch,
                                    tmp_path: Path, capsys) -> None:
    import scripts.rollback.stop_scheduler as ss
    lock = tmp_path / "publish_lock.json"

    # Force non-win32 so we don't need subprocess mock
    monkeypatch.setattr(ss, "sys", type("S", (), {"platform": "darwin",
                                                   "stdout": sys.stdout})())

    rc = ss.main([
        "--lock-path", str(lock),
        "--dry-run",
        "--block-hours", "49",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)

    # Required top-level keys
    required_keys = {"invocation_ts", "dry_run", "block_hours"}
    assert required_keys.issubset(parsed.keys())
    # dry_run flag propagates
    assert parsed["dry_run"] is True
    # block_hours preserved
    assert parsed["block_hours"] == 49
    # publish_lock in dry-run mode must expose would-write preview
    assert "publish_lock_would_write" in parsed
    assert parsed["publish_lock_would_write"]["lock_path"] == str(lock)
    # tasks_unregister always present
    assert "tasks_unregister" in parsed
    assert parsed["tasks_unregister"]["platform"] == "darwin"
