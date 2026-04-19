"""KPI-06 + SC#2 — wiki/kpi/kpi_log.md Hybrid format validators (Plan 09-02 target).

Wave 0 RED state: kpi_log.md does not yet exist; each test skips via a file-existence
gate so collection succeeds. Plan 09-02 writes the Hybrid format (Part A Target Declaration
+ Part B Monthly Tracking) with YouTube Analytics v2 API contract and flips these to green.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
KPI_LOG = _REPO_ROOT / "wiki" / "kpi" / "kpi_log.md"


def _read_kpi_log() -> str:
    if not KPI_LOG.exists():
        pytest.skip(f"{KPI_LOG} not yet created — Plan 09-02 target", allow_module_level=False)
    return KPI_LOG.read_text(encoding="utf-8")


def test_kpi_log_exists():
    """SC#2: wiki/kpi/kpi_log.md exists (Plan 09-02 target)."""
    assert KPI_LOG.exists(), f"{KPI_LOG} not created (Plan 09-02 target)"


def test_target_declaration():
    """KPI-06: 3 KPI targets (3sec retention > 60% / completion > 40% / avg watch > 25sec) explicit."""
    content = _read_kpi_log()
    assert "60%" in content and ("3초 retention" in content or "3sec_retention" in content), "Missing 3-sec retention > 60% target"
    assert "40%" in content and ("완주율" in content or "completion" in content.lower()), "Missing completion rate > 40% target"
    assert "25" in content and ("평균 시청" in content or "avg" in content.lower()), "Missing avg watch > 25초 target"


def test_api_contract_present():
    """D-07: YouTube Analytics v2 endpoint + OAuth scope + metric names declared."""
    content = _read_kpi_log()
    assert "youtubeanalytics.googleapis.com/v2/reports" in content, "Missing YouTube Analytics v2 endpoint"
    assert "yt-analytics.readonly" in content, "Missing OAuth scope yt-analytics.readonly"
    assert "audienceWatchRatio" in content, "Missing metric audienceWatchRatio"
    assert "averageViewDuration" in content, "Missing metric averageViewDuration"


def test_hybrid_structure():
    """D-06: Hybrid format — Part A Target Declaration + Part B Monthly Tracking both present."""
    content = _read_kpi_log()
    assert "Part A" in content and "Target Declaration" in content, "Missing Part A Target Declaration section"
    assert "Part B" in content and ("Monthly Tracking" in content or "월별" in content), "Missing Part B Monthly Tracking section"
    for col in ["video_id", "title", "3sec_retention", "completion_rate", "avg_view_sec", "taste_gate_rank"]:
        assert col in content, f"Missing Part B column: {col}"


def test_failure_thresholds_declared():
    """D-06: "실패 정의" section with re-creation trigger thresholds."""
    content = _read_kpi_log()
    assert "실패" in content or "재제작" in content, "Missing failure/re-creation trigger definition"
    assert "50%" in content, "Missing 3sec retention < 50% re-creation threshold"
