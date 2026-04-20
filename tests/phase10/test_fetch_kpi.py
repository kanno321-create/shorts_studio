"""Plan 10-03 Task 2 tests — fetch_kpi.py (KPI-01 daily YouTube Analytics fetch).

Six behavior tests per plan PLAN.md `<behavior>` block:
    fetch-1  test_fetch_parses_youtube_analytics_response
    fetch-2  test_fetch_writes_csv_with_isoformat_timestamp
    fetch-3  test_fetch_dry_run_no_file_io
    fetch-4  test_fetch_handles_empty_rows
    fetch-5  test_fetch_raises_on_401_insufficient_scope
    fetch-6  test_fetch_cli_video_ids_accepts_multiple

All tests monkeypatch `_build_analytics_client` → fake client that yields
pre-canned response dicts. Zero real network/OAuth calls. Windows cp949-safe
(tests rely on conftest.py autouse guard from tests/phase10/conftest.py).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ------------------------------------------------------------------ fixtures

@pytest.fixture
def sample_response() -> dict:
    """One-row YouTube Analytics v2 reports().query() response shape."""
    return {
        "columnHeaders": [
            {"name": "video", "columnType": "DIMENSION", "dataType": "STRING"},
            {"name": "views", "columnType": "METRIC", "dataType": "INTEGER"},
            {"name": "averageViewDuration", "columnType": "METRIC", "dataType": "INTEGER"},
            {"name": "audienceWatchRatio", "columnType": "METRIC", "dataType": "FLOAT"},
        ],
        "rows": [["demo123", 1234, 27, 0.62]],
    }


@pytest.fixture
def empty_response() -> dict:
    return {
        "columnHeaders": [
            {"name": "video", "columnType": "DIMENSION", "dataType": "STRING"},
            {"name": "views", "columnType": "METRIC", "dataType": "INTEGER"},
        ],
        "rows": [],
    }


def _install_mock_client(monkeypatch, response: dict):
    """Replace fetch_kpi._build_analytics_client with a MagicMock returning fixture."""
    import scripts.analytics.fetch_kpi as fk

    mock_exec = MagicMock(return_value=response)
    mock_query = MagicMock()
    mock_query.execute = mock_exec
    mock_reports = MagicMock()
    mock_reports.query = MagicMock(return_value=mock_query)
    mock_client = MagicMock()
    mock_client.reports = MagicMock(return_value=mock_reports)

    monkeypatch.setattr(fk, "_build_analytics_client", lambda creds: mock_client)
    return mock_client, mock_reports


# ------------------------------------------------------------------ tests

def test_fetch_parses_youtube_analytics_response(monkeypatch, sample_response):
    """fetch-1: fetch_daily_metrics parses columnHeaders+rows into metric dict."""
    import scripts.analytics.fetch_kpi as fk
    _install_mock_client(monkeypatch, sample_response)

    out = fk.fetch_daily_metrics(
        credentials=MagicMock(),
        video_ids=["demo123"],
        start_date="2026-04-19",
        end_date="2026-04-20",
    )
    assert "demo123" in out
    m = out["demo123"]
    assert m["views"] == 1234.0
    assert m["avg_view_sec"] == 27.0
    assert m["completion_rate"] == pytest.approx(0.62)
    # retention_3s 은 audienceWatchRatio proxy 로 사용 (Plan 3 v1)
    assert m["retention_3s"] == pytest.approx(0.62)


def test_fetch_writes_csv_with_isoformat_timestamp(monkeypatch, sample_response, tmp_path):
    """fetch-2: --output-dir writes kpi_YYYY-MM-DD.csv with CSV header + row."""
    _install_mock_client(monkeypatch, sample_response)
    import scripts.analytics.fetch_kpi as fk

    # Use real main() with mocked oauth + mocked client
    monkeypatch.setattr(fk, "get_credentials", lambda: MagicMock())
    rc = fk.main([
        "--video-ids", "demo123",
        "--output-dir", str(tmp_path),
        "--days-back", "1",
    ])
    assert rc == 0

    csv_files = list(tmp_path.glob("kpi_*.csv"))
    assert len(csv_files) == 1, f"expected 1 CSV, got {csv_files}"
    csv_path = csv_files[0]
    # ISO-format date in filename (YYYY-MM-DD)
    assert csv_path.name.startswith("kpi_") and csv_path.name.endswith(".csv")
    name_date = csv_path.stem.replace("kpi_", "")
    assert len(name_date) == 10 and name_date[4] == "-" and name_date[7] == "-"

    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["video_id"] == "demo123"
    assert rows[0]["scan_date"] == name_date
    assert float(rows[0]["views"]) == 1234.0


def test_fetch_dry_run_no_file_io(monkeypatch, sample_response, tmp_path, capsys):
    """fetch-3: --dry-run emits stdout JSON and creates no file."""
    _install_mock_client(monkeypatch, sample_response)
    import scripts.analytics.fetch_kpi as fk

    # get_credentials must not be called in dry-run path
    def _should_not_run():
        raise AssertionError("get_credentials called during --dry-run")
    monkeypatch.setattr(fk, "get_credentials", _should_not_run)

    rc = fk.main([
        "--video-ids", "abc,def",
        "--output-dir", str(tmp_path),
        "--dry-run",
    ])
    assert rc == 0
    assert list(tmp_path.iterdir()) == [], "dry-run must not write files"
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["dry_run"] is True
    assert payload["video_ids"] == ["abc", "def"]


def test_fetch_handles_empty_rows(monkeypatch, empty_response, tmp_path):
    """fetch-4: rows=[] produces header-only CSV + exit 0."""
    _install_mock_client(monkeypatch, empty_response)
    import scripts.analytics.fetch_kpi as fk
    monkeypatch.setattr(fk, "get_credentials", lambda: MagicMock())

    rc = fk.main([
        "--video-ids", "ghost999",
        "--output-dir", str(tmp_path),
    ])
    assert rc == 0
    csv_files = list(tmp_path.glob("kpi_*.csv"))
    assert len(csv_files) == 1
    with csv_files[0].open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # Empty rows -> proxy dict of 0.0 written with video_id=ghost999 (one row, all zeros)
    assert len(rows) == 1
    assert rows[0]["video_id"] == "ghost999"
    assert float(rows[0]["views"]) == 0.0


def test_fetch_raises_on_401_insufficient_scope(monkeypatch, tmp_path):
    """fetch-5: HttpError with 401 + insufficient_scope is re-raised (no silent fallback)."""
    import scripts.analytics.fetch_kpi as fk

    class _FakeHttpError(Exception):
        def __str__(self):
            return "<HttpError 401 'insufficient_scope': Request had insufficient authentication scopes>"

    mock_query = MagicMock()
    mock_query.execute = MagicMock(side_effect=_FakeHttpError())
    mock_reports = MagicMock()
    mock_reports.query = MagicMock(return_value=mock_query)
    mock_client = MagicMock()
    mock_client.reports = MagicMock(return_value=mock_reports)
    monkeypatch.setattr(fk, "_build_analytics_client", lambda creds: mock_client)
    monkeypatch.setattr(fk, "get_credentials", lambda: MagicMock())

    with pytest.raises(_FakeHttpError):
        fk.main([
            "--video-ids", "demo123",
            "--output-dir", str(tmp_path),
        ])


def test_fetch_cli_video_ids_accepts_multiple(monkeypatch, sample_response, tmp_path):
    """fetch-6: --video-ids abc,def,ghi triggers 3 .query() calls (per-video filter)."""
    _, mock_reports = _install_mock_client(monkeypatch, sample_response)
    import scripts.analytics.fetch_kpi as fk
    monkeypatch.setattr(fk, "get_credentials", lambda: MagicMock())

    rc = fk.main([
        "--video-ids", "abc,def,ghi",
        "--output-dir", str(tmp_path),
    ])
    assert rc == 0
    assert mock_reports.query.call_count == 3
    # Verify each call received a per-video filter
    called_filters = [
        call.kwargs.get("filters", "")
        for call in mock_reports.query.call_args_list
    ]
    assert any("video==abc" in f for f in called_filters)
    assert any("video==def" in f for f in called_filters)
    assert any("video==ghi" in f for f in called_filters)


# ------------------------------------------------------------------ CLI surface

def test_fetch_missing_video_ids_exits_2(monkeypatch, tmp_path, capsys):
    """Plan 3: channel-wide auto-enumeration is deferred to Plan 6; --video-ids required."""
    import scripts.analytics.fetch_kpi as fk
    rc = fk.main([
        "--output-dir", str(tmp_path),
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "video-ids" in err.lower()


def test_fetch_module_has_stdout_reconfigure_guard():
    """cp949 Windows guard must be present at module load (Plan 3 acceptance)."""
    src = Path(__file__).resolve().parents[2] / "scripts" / "analytics" / "fetch_kpi.py"
    text = src.read_text(encoding="utf-8")
    assert "sys.stdout.reconfigure" in text
    assert 'encoding="utf-8"' in text or "encoding='utf-8'" in text


def test_fetch_uses_youtubeAnalytics_v2_service():
    """Plan 3 Open Q1 anchor — exact endpoint identifiers in source."""
    src = Path(__file__).resolve().parents[2] / "scripts" / "analytics" / "fetch_kpi.py"
    text = src.read_text(encoding="utf-8")
    assert "youtubeAnalytics" in text
    assert '"v2"' in text
    assert "get_credentials" in text
