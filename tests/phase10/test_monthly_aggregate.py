"""Plan 10-03 Task 2 tests — monthly_aggregate.py (KPI-02 month-end rollup).

Six behavior tests per plan PLAN.md `<behavior>` block:
    agg-1  test_monthly_aggregate_reads_daily_csvs
    agg-2  test_monthly_aggregate_composite_score_correct
    agg-3  test_monthly_aggregate_appends_kpi_log_row
    agg-4  test_monthly_aggregate_idempotent_month
    agg-5  test_monthly_aggregate_dry_run
    agg-6  test_monthly_aggregate_handles_empty_daily_dir

All tests operate on tmp_path synthetic CSVs + a tmp kpi_log.md fixture copy so
the real wiki/kpi/kpi_log.md is never mutated.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


# ------------------------------------------------------------------ helpers

def _write_daily_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["video_id", "scan_date", "views", "avg_view_sec",
                         "completion_rate", "retention_3s"])
        for r in rows:
            writer.writerow([
                r["video_id"], r["scan_date"], r["views"],
                r["avg_view_sec"], r["completion_rate"], r["retention_3s"],
            ])


@pytest.fixture
def seed_daily_dir(tmp_path: Path) -> Path:
    """Three synthetic daily CSVs for 2026-04-01..03, two videos each."""
    d = tmp_path / "kpi_daily"
    _write_daily_csv(d / "kpi_2026-04-01.csv", [
        {"video_id": "abc", "scan_date": "2026-04-01", "views": 1000,
         "avg_view_sec": 24, "completion_rate": 0.40, "retention_3s": 0.60},
        {"video_id": "def", "scan_date": "2026-04-01", "views": 500,
         "avg_view_sec": 18, "completion_rate": 0.30, "retention_3s": 0.50},
    ])
    _write_daily_csv(d / "kpi_2026-04-02.csv", [
        {"video_id": "abc", "scan_date": "2026-04-02", "views": 1200,
         "avg_view_sec": 26, "completion_rate": 0.42, "retention_3s": 0.62},
        {"video_id": "def", "scan_date": "2026-04-02", "views": 550,
         "avg_view_sec": 19, "completion_rate": 0.31, "retention_3s": 0.52},
    ])
    _write_daily_csv(d / "kpi_2026-04-03.csv", [
        {"video_id": "abc", "scan_date": "2026-04-03", "views": 1100,
         "avg_view_sec": 25, "completion_rate": 0.41, "retention_3s": 0.61},
        {"video_id": "def", "scan_date": "2026-04-03", "views": 525,
         "avg_view_sec": 18.5, "completion_rate": 0.305, "retention_3s": 0.51},
    ])
    return d


@pytest.fixture
def seed_kpi_log(tmp_path: Path) -> Path:
    """Minimal kpi_log.md replica with PART_B_APPEND_MARKER."""
    p = tmp_path / "kpi_log.md"
    p.write_text(
        "# KPI Log\n\n## Part A: Target Declaration\n- 3s: > 60%\n\n"
        "## Part B: Monthly Tracking\n\n"
        "### Part B.2: Month-level Aggregate\n\n"
        "| Month | Videos | Avg 3s Retention | Avg Completion | Avg View (s) | Top Composite | Notes |\n"
        "|-------|--------|------------------|----------------|--------------|---------------|-------|\n"
        "<!-- PART_B_APPEND_MARKER -->\n\n"
        "## Related\n- foo\n",
        encoding="utf-8",
    )
    return p


# ------------------------------------------------------------------ tests

def test_monthly_aggregate_reads_daily_csvs(seed_daily_dir):
    """agg-1: aggregate_month produces dict[video_id, mean_metrics]."""
    import scripts.analytics.monthly_aggregate as ma
    out = ma.aggregate_month(seed_daily_dir, "2026-04")
    assert set(out.keys()) == {"abc", "def"}
    # sample counts
    assert out["abc"]["sample_count"] == 3
    assert out["def"]["sample_count"] == 3
    # means should be close to expected
    assert out["abc"]["retention_3s"] == pytest.approx((0.60 + 0.62 + 0.61) / 3)
    assert out["abc"]["completion_rate"] == pytest.approx((0.40 + 0.42 + 0.41) / 3)


def test_monthly_aggregate_composite_score_correct():
    """agg-2: composite = 0.5r + 0.3c + 0.2(v/60)."""
    import scripts.analytics.monthly_aggregate as ma
    m = {"retention_3s": 0.6, "completion_rate": 0.4, "avg_view_sec": 30.0}
    expected = 0.5 * 0.6 + 0.3 * 0.4 + 0.2 * (30.0 / 60.0)
    assert ma.composite_score(m) == pytest.approx(expected)

    # Edge: zero-metric dict
    assert ma.composite_score({}) == pytest.approx(0.0)

    # Edge: partial keys
    assert ma.composite_score({"retention_3s": 1.0}) == pytest.approx(0.5)


def test_monthly_aggregate_appends_kpi_log_row(seed_daily_dir, seed_kpi_log):
    """agg-3: append_kpi_log_row inserts a row directly after PART_B_APPEND_MARKER."""
    import scripts.analytics.monthly_aggregate as ma
    videos = ma.aggregate_month(seed_daily_dir, "2026-04")
    appended = ma.append_kpi_log_row(seed_kpi_log, "2026-04", videos)
    assert appended is True

    text = seed_kpi_log.read_text(encoding="utf-8")
    marker_idx = text.index("<!-- PART_B_APPEND_MARKER -->")
    after = text[marker_idx:]
    # New row begins with `| 2026-04 |`
    assert "| 2026-04 |" in after
    # Top composite line contains 'top: abc' (abc has higher retention + completion)
    assert "top: abc" in after or "top: abc," in after or "top: abc |" in after


def test_monthly_aggregate_idempotent_month(seed_daily_dir, seed_kpi_log):
    """agg-4: second call with same month does not add a duplicate row."""
    import scripts.analytics.monthly_aggregate as ma
    videos = ma.aggregate_month(seed_daily_dir, "2026-04")
    assert ma.append_kpi_log_row(seed_kpi_log, "2026-04", videos) is True
    first_text = seed_kpi_log.read_text(encoding="utf-8")

    # second invocation should be a no-op
    assert ma.append_kpi_log_row(seed_kpi_log, "2026-04", videos) is False
    assert seed_kpi_log.read_text(encoding="utf-8") == first_text

    # Row for 2026-04 appears exactly once
    count = sum(1 for line in first_text.splitlines() if line.startswith("| 2026-04 |"))
    assert count == 1


def test_monthly_aggregate_dry_run(seed_daily_dir, seed_kpi_log, capsys):
    """agg-5: --dry-run prints JSON + does not mutate kpi_log.md."""
    import scripts.analytics.monthly_aggregate as ma
    original = seed_kpi_log.read_text(encoding="utf-8")

    rc = ma.main([
        "--year-month", "2026-04",
        "--daily-dir", str(seed_daily_dir),
        "--kpi-log", str(seed_kpi_log),
        "--dry-run",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["year_month"] == "2026-04"
    assert payload["dry_run"] is True
    assert payload["videos_aggregated"] == 2
    # kpi_log.md unchanged
    assert seed_kpi_log.read_text(encoding="utf-8") == original


def test_monthly_aggregate_handles_empty_daily_dir(tmp_path, seed_kpi_log, capsys):
    """agg-6: no daily CSVs produces videos_aggregated=0 + exit 0 (no-data row appended)."""
    empty = tmp_path / "empty_dir"
    empty.mkdir()
    import scripts.analytics.monthly_aggregate as ma

    rc = ma.main([
        "--year-month", "2026-04",
        "--daily-dir", str(empty),
        "--kpi-log", str(seed_kpi_log),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    # Main prints JSON summary; allow additional warn lines (just parse last {...})
    summary_start = out.rindex("{")
    payload = json.loads(out[summary_start:])
    assert payload["year_month"] == "2026-04"
    assert payload["videos_aggregated"] == 0
    # Row appended with 'no data' text
    assert "no data" in seed_kpi_log.read_text(encoding="utf-8")


# ------------------------------------------------------------------ CLI surface

def test_monthly_aggregate_module_has_stdout_reconfigure_guard():
    """cp949 Windows guard present at module load."""
    src = Path(__file__).resolve().parents[2] / "scripts" / "analytics" / "monthly_aggregate.py"
    text = src.read_text(encoding="utf-8")
    assert "sys.stdout.reconfigure" in text


def test_monthly_aggregate_exports_composite_score_symbol():
    """composite_score must be importable (Plan 6 research loop imports it)."""
    from scripts.analytics.monthly_aggregate import composite_score  # noqa: F401
    assert callable(composite_score)


def test_monthly_aggregate_marker_constant_matches_kpi_log():
    """PART_B_MARKER constant in source must match the wiki/kpi/kpi_log.md literal."""
    import scripts.analytics.monthly_aggregate as ma
    assert ma.PART_B_MARKER == "<!-- PART_B_APPEND_MARKER -->"

    repo_root = Path(__file__).resolve().parents[2]
    kpi_log = repo_root / "wiki" / "kpi" / "kpi_log.md"
    if kpi_log.exists():
        assert ma.PART_B_MARKER in kpi_log.read_text(encoding="utf-8")


def test_monthly_aggregate_raises_when_marker_missing(tmp_path):
    """append_kpi_log_row raises RuntimeError when MARKER missing."""
    bad = tmp_path / "bad_kpi_log.md"
    bad.write_text("# KPI Log without marker\n\n| Month | Videos |\n|---|---|\n", encoding="utf-8")
    import scripts.analytics.monthly_aggregate as ma
    with pytest.raises(RuntimeError, match="PART_B_APPEND_MARKER"):
        ma.append_kpi_log_row(bad, "2026-04", {})
