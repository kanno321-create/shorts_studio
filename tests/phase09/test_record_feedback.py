"""KPI-05 parser — scripts/taste_gate/record_feedback.py (Plan 09-04 target).

Wave 0 state: module not importable — pytest.importorskip skips entire module. Plan 09-04
ships record_feedback.py with parse_taste_gate / filter_escalate / build_failures_block /
append_to_failures / main and these tests flip to green.
"""
from __future__ import annotations

import pytest

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py",
)


def test_parse_six_rows(synthetic_taste_gate_april, monkeypatch):
    """KPI-05: parse_taste_gate returns 6 evaluated rows from fixture."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    rows = record_feedback.parse_taste_gate("2026-04")
    assert len(rows) == 6, f"Expected 6 rows, got {len(rows)}"


def test_parse_extracts_required_fields(synthetic_taste_gate_april, monkeypatch):
    """KPI-05: each row has video_id, title, score, comment extracted."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    rows = record_feedback.parse_taste_gate("2026-04")
    row0 = rows[0]
    assert row0["video_id"] == "abc123"
    assert isinstance(row0["score"], int)
    assert 1 <= row0["score"] <= 5
    assert "comment" in row0
    assert "title" in row0


def test_parse_raises_on_missing_file(tmp_path, monkeypatch):
    """Pitfall 5: explicit Korean error on missing file (not silent)."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", tmp_path)
    with pytest.raises(record_feedback.TasteGateParseError) as exc:
        record_feedback.parse_taste_gate("2026-04")
    assert "파일 없음" in str(exc.value)


def test_parse_raises_on_malformed_score(tmp_path, monkeypatch):
    """Pitfall 5: score outside 1-5 → explicit Korean raise or skip-with-warning behavior."""
    bad = tmp_path / "taste_gate_2026-04.md"
    bad.write_text(
        "| 1 | abc123 | \"t\" | 68% | 42% | 27초 | 9 | c | tag |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", tmp_path)
    # Malformed score 9 must not silently pass — either raise or skip with warning.
    # If skipped via underscore pattern, rows should be empty → raises "평가된 행이 없습니다".
    # Implementation in Plan 09-04 resolves this path.
    with pytest.raises(record_feedback.TasteGateParseError):
        record_feedback.parse_taste_gate("2026-04")
