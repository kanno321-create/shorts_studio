"""scripts.orchestrator — Phase 5 public API surface.

Downstream plans (08 hc_checks, 09 Hook extensions, 10 SC acceptance) and
all future callers import from this namespace, NOT from the individual
modules directly. The namespace collects every primitive produced by
Waves 0-4 plus the keystone :class:`ShortsPipeline` from Wave 5.
"""
from __future__ import annotations

from .checkpointer import Checkpoint, Checkpointer, sha256_file
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)
from .gate_guard import GateGuard, Verdict
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
from .shorts_pipeline import GATE_INSPECTORS, GateContext, ShortsPipeline
from .voice_first_timeline import (
    AudioSegment,
    ClipDurationMismatch,
    IntegratedRenderForbidden,
    InvalidClipDuration,
    TimelineEntry,
    TimelineMismatch,
    TransitionEntry,
    VideoCut,
    VoiceFirstTimeline,
)

__all__ = [
    # gates.py
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
    # circuit_breaker.py
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    # checkpointer.py
    "Checkpointer",
    "Checkpoint",
    "sha256_file",
    # gate_guard.py
    "GateGuard",
    "Verdict",
    # voice_first_timeline.py
    "VoiceFirstTimeline",
    "AudioSegment",
    "VideoCut",
    "TimelineEntry",
    "TransitionEntry",
    "TimelineMismatch",
    "InvalidClipDuration",
    "ClipDurationMismatch",
    "IntegratedRenderForbidden",
    # shorts_pipeline.py (Wave 5 keystone)
    "ShortsPipeline",
    "GateContext",
    "GATE_INSPECTORS",
]
