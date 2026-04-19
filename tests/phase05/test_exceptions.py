"""OrchestratorError exception-hierarchy tests (Phase 5 Plan 01 Task 3)."""
from __future__ import annotations

import pytest

from scripts.orchestrator import (
    CircuitOpen,
    GateDependencyUnsatisfied,
    GateFailure,
    GateName,
    IncompleteDispatch,
    InvalidGateTransition,
    InvalidI2VRequest,
    MissingVerdict,
    OrchestratorError,
    RegenerationExhausted,
    T2VForbidden,
)


def test_all_subclass_base():
    """All 9 concrete exceptions must subclass OrchestratorError for catch-all."""
    for cls in (
        InvalidGateTransition,
        GateFailure,
        MissingVerdict,
        IncompleteDispatch,
        GateDependencyUnsatisfied,
        CircuitOpen,
        RegenerationExhausted,
        T2VForbidden,
        InvalidI2VRequest,
    ):
        assert issubclass(cls, OrchestratorError)


def test_gate_failure_carries_evidence():
    """GateFailure must preserve gate + evidence for regeneration loop."""
    evidence = [{"rule": "HC-2", "detail": "too long"}]
    with pytest.raises(GateFailure) as ei:
        raise GateFailure(GateName.SCRIPT, evidence)
    assert ei.value.gate == GateName.SCRIPT
    assert ei.value.evidence == evidence
    assert "SCRIPT" in str(ei.value)
