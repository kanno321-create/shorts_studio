"""GateName enum contract tests (Phase 5 Plan 01 Task 3)."""
from __future__ import annotations

from scripts.orchestrator import GateName


def test_fifteen_members():
    assert len(list(GateName)) == 15


def test_endpoints():
    assert GateName.IDLE == 0
    assert GateName.COMPLETE == 14


def test_thirteen_operational_gates():
    """Operational = all GATEs except IDLE bookend and COMPLETE bookend."""
    operational = [g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]
    assert len(operational) == 13


def test_canonical_order_matches_d2():
    """D-2 canonical order; mismatch = broken contract for downstream plans."""
    expected = [
        "IDLE",
        "TREND",
        "NICHE",
        "RESEARCH_NLM",
        "BLUEPRINT",
        "SCRIPT",
        "POLISH",
        "VOICE",
        "ASSETS",
        "ASSEMBLY",
        "THUMBNAIL",
        "METADATA",
        "UPLOAD",
        "MONITOR",
        "COMPLETE",
    ]
    actual = [g.name for g in sorted(GateName, key=int)]
    assert actual == expected


def test_intenum_ordering():
    """IntEnum comparison must work for Checkpointer gate_index sort."""
    assert GateName.TREND < GateName.NICHE < GateName.ASSEMBLY < GateName.COMPLETE
