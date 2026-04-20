"""RED stub for shorts_pipeline.py 500~800 line invariant (REQ-04 reinforcement).

Wave 2/4 must keep shorts_pipeline.py ≤ 800 lines. This test is the tripwire
that blocks merging if Wave 2 produced sprawl.
"""
from __future__ import annotations

from pathlib import Path


def test_shorts_pipeline_leq_800_lines() -> None:
    """Invariant: scripts/orchestrator/shorts_pipeline.py must stay ≤ 800 lines."""
    p = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "orchestrator"
        / "shorts_pipeline.py"
    )
    lines = p.read_text(encoding="utf-8").splitlines()
    n = len(lines)
    assert n <= 800, f"shorts_pipeline.py = {n} lines > 800 (대표님 500-800 상한 위반)"
