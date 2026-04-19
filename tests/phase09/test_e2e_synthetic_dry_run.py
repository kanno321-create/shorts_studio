"""SC#4 — end-to-end synthetic dry-run (Plan 09-05 target).

Wave 0 state: module not importable — pytest.importorskip skips entire module. Plan 09-05
activates the end-to-end chain (synthetic_taste_gate_april → record_feedback.main() → tmp
FAILURES.md gains `[taste_gate] 2026-04` entry while preserving prior prefix).
"""
from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py; Plan 09-05 activates E2E",
)


def test_e2e_parse_filter_append(synthetic_taste_gate_april, tmp_failures_md, freeze_kst_2026_04_01, monkeypatch):
    """SC#4: synthetic dry-run → record_feedback.py → FAILURES.md has new [taste_gate] 2026-04 entry."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)

    prior = tmp_failures_md.read_text(encoding="utf-8")
    rc = record_feedback.main(["--month", "2026-04"])
    assert rc == 0, f"record_feedback.main returned {rc}, expected 0"

    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after.startswith(prior), "D-12: prior FAILURES content must be preserved as prefix"
    assert "### [taste_gate] 2026-04" in after, "New [taste_gate] 2026-04 section not found"


def test_e2e_dry_run_no_write(synthetic_taste_gate_april, tmp_failures_md, monkeypatch):
    """SC#4: --dry-run prints block but does NOT write FAILURES.md."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)
    prior = tmp_failures_md.read_text(encoding="utf-8")
    rc = record_feedback.main(["--month", "2026-04", "--dry-run"])
    assert rc == 0
    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after == prior, "--dry-run must NOT modify FAILURES.md"
