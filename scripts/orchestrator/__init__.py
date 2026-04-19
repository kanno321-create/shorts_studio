"""scripts.orchestrator — Phase 5 public API surface.

Downstream plans (02 CircuitBreaker, 03 Checkpointer, 04 GateGuard,
05 VoiceFirstTimeline, 06 API adapters, 07 Pipeline, 08 hc_checks,
09 Hook extensions, 10 SC acceptance) import from this namespace, NOT
from scripts.orchestrator.gates directly.

Plan 07 (shorts_pipeline.py) will extend __all__ with CircuitBreaker,
Checkpointer, GateGuard, VoiceFirstTimeline, and ShortsPipeline.
"""
from __future__ import annotations

from .gates import (
    GATE_DEPS,
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

__all__ = [
    "GateName",
    "GATE_DEPS",
    "OrchestratorError",
    "InvalidGateTransition",
    "GateFailure",
    "MissingVerdict",
    "IncompleteDispatch",
    "GateDependencyUnsatisfied",
    "CircuitOpen",
    "RegenerationExhausted",
    "T2VForbidden",
    "InvalidI2VRequest",
]
