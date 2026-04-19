"""D-13: only score <= 3 escalates to FAILURES.md (Plan 09-04 target).

Wave 0 state: module not importable — pytest.importorskip skips entire module. Plan 09-04
ships filter_escalate() and these tests flip to green.
"""
from __future__ import annotations

import pytest

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py",
)


def test_filter_includes_score_1():
    """D-13: score 1 (lowest) included in escalation payload."""
    rows = [{"video_id": "a", "score": 1, "title": "t", "comment": "c"}]
    assert record_feedback.filter_escalate(rows) == rows


def test_filter_includes_score_2():
    """D-13: score 2 included."""
    rows = [{"video_id": "a", "score": 2, "title": "t", "comment": "c"}]
    assert len(record_feedback.filter_escalate(rows)) == 1


def test_filter_includes_score_3_boundary():
    """D-13 boundary: score == 3 escalates (<=)."""
    rows = [{"video_id": "a", "score": 3, "title": "t", "comment": "c"}]
    assert len(record_feedback.filter_escalate(rows)) == 1


def test_filter_excludes_score_4():
    """D-13: score 4 excluded (kpi_log.md only, no FAILURES escalation)."""
    rows = [{"video_id": "a", "score": 4, "title": "t", "comment": "c"}]
    assert record_feedback.filter_escalate(rows) == []


def test_filter_excludes_score_5():
    """D-13: score 5 excluded (top-tier, no FAILURES escalation)."""
    rows = [{"video_id": "a", "score": 5, "title": "t", "comment": "c"}]
    assert record_feedback.filter_escalate(rows) == []


def test_filter_mixed_six_rows(synthetic_taste_gate_april, monkeypatch):
    """D-13: synthetic sample has scores [5,4,4,3,2,1] → 3 escalated (3,2,1)."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    rows = record_feedback.parse_taste_gate("2026-04")
    escalated = record_feedback.filter_escalate(rows)
    assert len(escalated) == 3, f"D-13 expected 3 escalations (scores 1/2/3), got {len(escalated)}"
    assert all(r["score"] <= 3 for r in escalated)
