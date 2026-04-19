"""Unit tests for GateGuard.verify_all_dispatched (Plan 05-04).

Verifies ORCH-04 / CONTEXT D-4: COMPLETE transition precondition.

Covered:
    - Empty dispatched set -> False
    - All 13 operational gates dispatched -> True
    - One gate missing -> False
    - IDLE alone (bookend) is not sufficient
    - missing_for_complete() diagnostic reports the gap correctly
    - COMPLETE itself is NOT required (it is the transition target)
    - Operational count is exactly 13 (sanity against RESEARCH §2)
"""
from __future__ import annotations

from scripts.orchestrator import GateName
from scripts.orchestrator.gate_guard import GateGuard, Verdict


def _pass() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


def test_empty_dispatch_is_false(tmp_state_dir):
    g = GateGuard(None, "s1")
    assert g.verify_all_dispatched() is False


def test_all_13_operational_dispatch_is_true(tmp_state_dir):
    g = GateGuard(None, "s1")
    operational = [
        gate for gate in GateName if gate not in (GateName.IDLE, GateName.COMPLETE)
    ]
    assert len(operational) == 13
    for gate in operational:
        g.dispatch(gate, _pass())
    assert g.verify_all_dispatched() is True


def test_missing_one_gate_is_false(tmp_state_dir):
    g = GateGuard(None, "s1")
    operational = [
        gate for gate in GateName if gate not in (GateName.IDLE, GateName.COMPLETE)
    ]
    for gate in operational[:-1]:  # all except the last (MONITOR)
        g.dispatch(gate, _pass())
    assert g.verify_all_dispatched() is False


def test_idle_dispatched_alone_is_not_sufficient(tmp_state_dir):
    g = GateGuard(None, "s1")
    # Dispatch only IDLE (unusual — IDLE is the root, not operational).
    g.dispatch(GateName.IDLE, _pass())
    assert g.verify_all_dispatched() is False


def test_missing_for_complete_reports_gap(tmp_state_dir):
    g = GateGuard(None, "s1")
    g.dispatch(GateName.TREND, _pass())
    missing = g.missing_for_complete()
    assert GateName.NICHE in missing
    assert GateName.MONITOR in missing
    assert GateName.TREND not in missing
    assert GateName.IDLE not in missing
    assert GateName.COMPLETE not in missing


def test_complete_itself_not_required(tmp_state_dir):
    g = GateGuard(None, "s1")
    operational = [
        gate for gate in GateName if gate not in (GateName.IDLE, GateName.COMPLETE)
    ]
    for gate in operational:
        g.dispatch(gate, _pass())
    # Deliberately do NOT dispatch COMPLETE — it is the transition target.
    assert g.verify_all_dispatched() is True
    assert GateName.COMPLETE not in g.missing_for_complete()


def test_operational_count_is_exactly_13():
    """Sanity check against RESEARCH §2 (13 operational excluding IDLE + COMPLETE)."""
    operational = [g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]
    assert len(operational) == 13
