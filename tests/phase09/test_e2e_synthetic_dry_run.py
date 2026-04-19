"""SC#4 — end-to-end synthetic dry-run (Plan 09-05 finalized).

Wave 3 state: Plan 09-04 shipped ``scripts.taste_gate.record_feedback`` with
its public API (``main`` / ``parse_taste_gate`` / ``filter_escalate`` /
``build_failures_block`` / ``TASTE_GATE_DIR`` / ``FAILURES_PATH``). This
module exercises the full pipeline end-to-end against the Plan 09-00
synthetic fixture (``synthetic_taste_gate_april``) and proves four
invariants:

1. ``main(["--month", "2026-04"])`` appends a ``### [taste_gate] 2026-04``
   block to FAILURES.md while preserving the prior content as a strict
   prefix (D-11 append-only Hook compat) and escalating only the three
   score ≤ 3 rows (jkl012/mno345/pqr678) — abc123/def456/ghi789 MUST NOT
   appear under ``#### 세부 코멘트``.
2. ``main(["--month", "2026-04", "--dry-run"])`` is byte-identical on
   disk (no writes).
3. ``parse_taste_gate`` + ``filter_escalate`` returns exactly 3 rows
   whose scores sort to ``[1, 2, 3]`` (D-13 anchor).
4. ``build_failures_block`` uses a KST-anchored timestamp (``+09:00``
   offset OR literal ``KST`` marker) so monthly rollups are timezone
   unambiguous.
"""
from __future__ import annotations

from pathlib import Path

from scripts.taste_gate import record_feedback

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_e2e_parse_filter_append(
    synthetic_taste_gate_april,
    tmp_failures_md,
    freeze_kst_2026_04_01,
    monkeypatch,
):
    """SC#4: synthetic dry-run → record_feedback.py → FAILURES.md has new
    ``[taste_gate] 2026-04`` entry; D-12 prefix-preservation proven + D-13
    escalation filter isolates bottom-3 rows only.
    """
    monkeypatch.setattr(
        record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent
    )
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)

    prior = tmp_failures_md.read_text(encoding="utf-8")
    rc = record_feedback.main(["--month", "2026-04"])
    assert rc == 0, f"record_feedback.main returned {rc}, expected 0"

    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after.startswith(
        prior
    ), "D-12: prior FAILURES content must be preserved as strict prefix"
    assert (
        "### [taste_gate] 2026-04" in after
    ), "New [taste_gate] 2026-04 section header not found"

    # Bottom-3 must appear in the appended block
    for vid in ("jkl012", "mno345", "pqr678"):
        assert vid in after, f"bottom-3 video_id {vid!r} missing from FAILURES.md"

    # Top-3 must NOT appear under the escalation block header
    # (the 세부 코멘트 sub-section only lists D-13 filter-passing rows).
    tail = after.split("### [taste_gate] 2026-04", 1)[1]
    details = tail.split("#### 세부 코멘트", 1)[1]
    for forbidden in ("abc123", "def456", "ghi789"):
        assert (
            forbidden not in details
        ), f"top-3 video_id {forbidden!r} leaked into escalation 세부 코멘트 (D-13 violation)"


def test_e2e_dry_run_no_write(
    synthetic_taste_gate_april, tmp_failures_md, monkeypatch
):
    """SC#4: --dry-run prints the proposed block but MUST NOT modify
    FAILURES.md on disk. Byte equality proves the Hook append-only
    contract is not invoked unnecessarily.
    """
    monkeypatch.setattr(
        record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent
    )
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)
    prior = tmp_failures_md.read_text(encoding="utf-8")
    rc = record_feedback.main(["--month", "2026-04", "--dry-run"])
    assert rc == 0
    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after == prior, "--dry-run must NOT modify FAILURES.md"


def test_e2e_escalation_count_exactly_3(synthetic_taste_gate_april, monkeypatch):
    """D-13 anchor: exactly 3 rows survive the score ≤ 3 filter, and
    their scores sort to ``[1, 2, 3]``.
    """
    monkeypatch.setattr(
        record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent
    )
    rows = record_feedback.parse_taste_gate("2026-04")
    escalated = record_feedback.filter_escalate(rows)
    assert len(escalated) == 3, (
        f"D-13 expects exactly 3 escalations (score <= 3), got {len(escalated)}: "
        f"{[r['video_id'] for r in escalated]}"
    )
    scores = sorted(r["score"] for r in escalated)
    assert scores == [1, 2, 3], f"escalated scores should be [1,2,3], got {scores}"


def test_e2e_korean_timestamp_format(
    synthetic_taste_gate_april, freeze_kst_2026_04_01, monkeypatch
):
    """KST timezone anchor: the generated block MUST contain either the
    ISO offset ``+09:00`` or the literal string ``KST`` so any downstream
    reader can disambiguate the timestamp timezone without inspecting
    code.
    """
    monkeypatch.setattr(
        record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent
    )
    rows = record_feedback.parse_taste_gate("2026-04")
    escalated = record_feedback.filter_escalate(rows)
    block = record_feedback.build_failures_block("2026-04", escalated)
    assert (
        "+09:00" in block or "KST" in block
    ), "Block must carry KST timezone marker (+09:00 or 'KST')"
