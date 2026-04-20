"""Phase 10 Plan 07 — SC#6 YPP trajectory appender tests (13 tests).

Verifies:
    - evaluate_gates() 3-milestone logic (pre-3m, 1st fail/pass, 2nd fail-subs/
      fail-retention/pass)
    - upsert_row() insert + idempotent replace on same year_month
    - update_mermaid() x-axis + line rewrite from parsed snapshots
    - append_failures() F-YPP-NN append with strict-prefix preservation
    - CLI --dry-run leaves trajectory.md + FAILURES.md byte-identical
    - months_since() calculation against PHASE_10_START = 2026-04-20
    - Missing TRAJECTORY_APPEND_MARKER raises RuntimeError (no silent fallback)

Scope (Phase 10 Plan 07 frontmatter):
    - scripts/analytics/trajectory_append.py
    - tests/phase10/test_trajectory_append.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

# ---------------------------------------------------------------- imports
from scripts.analytics.trajectory_append import (  # noqa: E402
    GATE_1_SUBS,
    GATE_2_RETENTION,
    GATE_2_SUBS,
    GATE_3_SUBS,
    GATE_3_VIEWS,
    PHASE_10_START,
    append_failures,
    evaluate_gates,
    main,
    months_since,
    parse_existing_snapshots,
    render_row,
    update_mermaid,
    upsert_row,
)


SCAFFOLD_TRAJECTORY = """---
node: trajectory
category: ypp
kind: monthly-snapshot
status: ready
tags: [ypp, trajectory, sc6]
last_updated: 2026-04-20
auto_update_by: scripts/analytics/trajectory_append.py
---

# YPP Trajectory — test fixture

**Phase 10 시작일**: 2026-04-20

## Monthly Snapshots

| Month | Subs | Rolling12mViews | 1stGate% | 2ndGateSubs% | 3rdGateSubs% | 3rdGateViews% | Notes |
|-------|-----:|----------------:|---------:|-------------:|-------------:|--------------:|-------|
<!-- TRAJECTORY_APPEND_MARKER -->

## Trajectory Chart

<!-- MERMAID_DATA_MARKER -->

```mermaid
xychart-beta
    title "YPP Subscribers Trajectory"
    x-axis [2026-04]
    y-axis "Subscribers" 0 --> 1100
    line [0]
```
"""

FAILURES_SEED = """# FAILURES.md — shorts_studio

> append-only. D-11.

## F-CTX-01 — seed

Seed content for append_failures tests.
"""


@pytest.fixture
def tmp_trajectory(tmp_path: Path) -> Path:
    p = tmp_path / "trajectory.md"
    p.write_text(SCAFFOLD_TRAJECTORY, encoding="utf-8")
    return p


@pytest.fixture
def tmp_failures(tmp_path: Path) -> Path:
    p = tmp_path / "FAILURES.md"
    p.write_text(FAILURES_SEED, encoding="utf-8")
    return p


# ---------------------------------------------------------------- evaluate_gates

def test_evaluate_gates_before_3months_no_warnings():
    result = evaluate_gates({"subs": 10, "views_12m": 100, "retention_3s": 0.3}, 2)
    assert result["warnings"] == []
    assert result["pivot_required"] is False
    assert result["month_since_start"] == 2


def test_evaluate_gates_first_gate_fail_subs_under_100():
    result = evaluate_gates({"subs": 50, "views_12m": 10000, "retention_3s": 0.3}, 3)
    assert any("1st gate FAIL" in w for w in result["warnings"])
    assert result["pivot_required"] is True


def test_evaluate_gates_first_gate_pass_subs_over_100():
    result = evaluate_gates({"subs": 150, "views_12m": 50000, "retention_3s": 0.62}, 3)
    assert result["warnings"] == []
    assert result["pivot_required"] is False


def test_evaluate_gates_second_gate_fail_low_subs():
    result = evaluate_gates({"subs": 200, "views_12m": 500000, "retention_3s": 0.70}, 6)
    # subs (200) < 300 must fire; retention pass (0.70 >= 0.60)
    assert any("2nd gate FAIL" in w and "subs" in w for w in result["warnings"])
    assert result["pivot_required"] is True


def test_evaluate_gates_second_gate_fail_low_retention():
    result = evaluate_gates({"subs": 400, "views_12m": 900000, "retention_3s": 0.50}, 6)
    # subs pass (400 >= 300); retention (0.50 < 0.60) fires
    assert any("2nd gate FAIL" in w and "retention" in w for w in result["warnings"])
    assert result["pivot_required"] is True


def test_evaluate_gates_second_gate_pass():
    result = evaluate_gates({"subs": 400, "views_12m": 1_000_000, "retention_3s": 0.65}, 6)
    assert result["warnings"] == []
    assert result["pivot_required"] is False


# ---------------------------------------------------------------- upsert_row

def test_append_row_inserts_below_marker(tmp_trajectory: Path):
    row = render_row("2026-05", {"subs": 23, "views_12m": 15000}, "first row")
    assert upsert_row(tmp_trajectory, "2026-05", row) is True
    text = tmp_trajectory.read_text(encoding="utf-8")
    # Row must appear after marker
    head, tail = text.split("<!-- TRAJECTORY_APPEND_MARKER -->", 1)
    assert "| 2026-05 |" in tail
    # Row must not appear before marker
    assert "| 2026-05 |" not in head


def test_append_row_idempotent_same_month(tmp_trajectory: Path):
    row1 = render_row("2026-05", {"subs": 23, "views_12m": 15000}, "v1")
    upsert_row(tmp_trajectory, "2026-05", row1)
    row2 = render_row("2026-05", {"subs": 50, "views_12m": 20000}, "v2")
    assert upsert_row(tmp_trajectory, "2026-05", row2) is True
    text = tmp_trajectory.read_text(encoding="utf-8")
    # Only one row for 2026-05 should remain (replaced)
    assert text.count("| 2026-05 |") == 1
    # New values must be present
    assert "50" in text
    assert "v2" in text
    assert "v1" not in text


# ---------------------------------------------------------------- update_mermaid

def test_mermaid_data_updated_from_three_snapshots(tmp_trajectory: Path):
    for ym, subs in [("2026-04", 0), ("2026-05", 23), ("2026-06", 75)]:
        row = render_row(ym, {"subs": subs, "views_12m": subs * 400})
        upsert_row(tmp_trajectory, ym, row)
    snaps = parse_existing_snapshots(tmp_trajectory)
    assert snaps == [("2026-04", 0), ("2026-05", 23), ("2026-06", 75)]
    update_mermaid(tmp_trajectory, snaps)
    text = tmp_trajectory.read_text(encoding="utf-8")
    assert "x-axis [2026-04, 2026-05, 2026-06]" in text
    assert "line [0, 23, 75]" in text


# ---------------------------------------------------------------- append_failures

def test_pivot_warning_appends_failures(tmp_failures: Path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime(2026, 7, 25, 9, 0, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    warnings = ["1st gate FAIL — subs 50 < 100 — 니치/훅 iteration 필요"]
    entry_id = append_failures(tmp_failures, "2026-07", warnings, now)
    assert entry_id == "F-YPP-01"
    text = tmp_failures.read_text(encoding="utf-8")
    # Seed preserved (strict prefix)
    assert text.startswith(FAILURES_SEED), "FAILURES.md append must be strict-prefix"
    # F-YPP-01 entry present
    assert "## F-YPP-01" in text
    assert "2026-07" in text
    assert "1st gate FAIL" in text
    # Subsequent append increments id
    entry_id2 = append_failures(tmp_failures, "2026-08", ["2nd gate FAIL — subs 200 < 300"], now)
    assert entry_id2 == "F-YPP-02"


# ---------------------------------------------------------------- CLI

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_cli_dry_run_no_mutation(tmp_trajectory: Path, tmp_failures: Path):
    before_traj = hashlib.sha256(tmp_trajectory.read_bytes()).hexdigest()
    before_fail = hashlib.sha256(tmp_failures.read_bytes()).hexdigest()
    rc = main([
        "--subs", "150",
        "--views-12m", "125000",
        "--retention-3s", "0.62",
        "--year-month", "2026-07",
        "--trajectory", str(tmp_trajectory),
        "--failures", str(tmp_failures),
        "--dry-run",
    ])
    assert rc == 0
    after_traj = hashlib.sha256(tmp_trajectory.read_bytes()).hexdigest()
    after_fail = hashlib.sha256(tmp_failures.read_bytes()).hexdigest()
    assert before_traj == after_traj, "--dry-run must NOT mutate trajectory.md"
    assert before_fail == after_fail, "--dry-run must NOT mutate FAILURES.md"


def test_cli_month_since_start_calculation():
    # PHASE_10_START = 2026-04-20; 2026-07 (month=7) → months_since = 3
    assert months_since(PHASE_10_START, date(2026, 7, 1)) == 3
    assert months_since(PHASE_10_START, date(2026, 4, 1)) == 0
    assert months_since(PHASE_10_START, date(2027, 4, 1)) == 12


def test_cli_missing_markers_raises(tmp_path: Path):
    bad = tmp_path / "bad.md"
    bad.write_text("# no marker here\n", encoding="utf-8")
    row = render_row("2026-05", {"subs": 10, "views_12m": 1000})
    with pytest.raises(RuntimeError, match="TRAJECTORY_APPEND_MARKER"):
        upsert_row(bad, "2026-05", row)


# ---------------------------------------------------------------- threshold constants sanity

def test_threshold_constants_match_context_lock():
    """CONTEXT §Exit Criterion threshold lock — 100/300/0.60/1000/10M."""
    assert GATE_1_SUBS == 100
    assert GATE_2_SUBS == 300
    assert GATE_2_RETENTION == 0.60
    assert GATE_3_SUBS == 1000
    assert GATE_3_VIEWS == 10_000_000
    assert PHASE_10_START == date(2026, 4, 20)
