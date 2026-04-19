"""GATE_DEPS DAG contract tests (Phase 5 Plan 01 Task 3)."""
from __future__ import annotations

import graphlib

from scripts.orchestrator import GATE_DEPS, GateName


def test_assembly_needs_voice_and_assets():
    """D-7 invariant: ASSEMBLY must wait for BOTH VOICE and ASSETS."""
    assert set(GATE_DEPS[GateName.ASSEMBLY]) == {GateName.VOICE, GateName.ASSETS}


def test_upload_needs_thumbnail_and_metadata():
    """UPLOAD cannot proceed until THUMBNAIL + METADATA both dispatched."""
    assert set(GATE_DEPS[GateName.UPLOAD]) == {GateName.THUMBNAIL, GateName.METADATA}


def test_idle_has_no_deps():
    """IDLE is the pipeline entry state; depends on nothing."""
    assert GATE_DEPS[GateName.IDLE] == ()


def test_complete_depends_on_all_operational():
    """COMPLETE aggregates all 13 operational gates (verify_all_dispatched)."""
    expected = {g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)}
    assert set(GATE_DEPS[GateName.COMPLETE]) == expected


def test_dag_acyclic():
    """graphlib.TopologicalSorter must succeed with 15 ordered nodes."""
    sorter = graphlib.TopologicalSorter(
        {g.name: {d.name for d in deps} for g, deps in GATE_DEPS.items()}
    )
    ordered = list(sorter.static_order())  # raises CycleError on cycle
    assert len(ordered) == 15


def test_every_gate_has_deps_entry():
    """No GateName may be missing from GATE_DEPS (would break ensure_dependencies)."""
    for g in GateName:
        assert g in GATE_DEPS, f"{g.name} missing from GATE_DEPS"
