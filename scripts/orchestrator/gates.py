"""Phase 5 Orchestrator v2 — canonical state machine contracts.

This module is the single source of truth for:
    - GateName enum (15 members, D-2 canonical order)
    - GATE_DEPS DAG (ORCH-07 dependency graph; ASSEMBLY needs VOICE+ASSETS,
      UPLOAD needs THUMBNAIL+METADATA, COMPLETE needs all 13 operational gates)
    - Exception hierarchy (OrchestratorError + 9 subclasses)
    - Import-time DAG validation via graphlib.TopologicalSorter

Requirements addressed:
    - ORCH-02 : 15 GATE IntEnum (12 operational + IDLE + COMPLETE per CONTEXT D-2)
    - ORCH-03 : GateGuard.dispatch contract exception surface (GateFailure,
                MissingVerdict, InvalidGateTransition)
    - ORCH-07 : DAG dependency declaration + acyclicity proof at import time

Downstream plans (02..10) import from `scripts.orchestrator` public namespace;
do NOT import directly from this module in pipeline / adapter code.

Python 3.11+ required (IntEnum member-ordering, graphlib stdlib).
"""
from __future__ import annotations

import graphlib
from enum import IntEnum


# ============================================================================
# Gate enumeration (D-2 canonical order — DO NOT RENUMBER)
# ============================================================================


class GateName(IntEnum):
    """15 pipeline states; operational range 1..13 (TREND..MONITOR).

    IDLE (0) and COMPLETE (14) are bookends — not operational GATEs.
    Values are stable and used by Checkpointer file naming
    (gate_{int(GateName):02d}.json) for natural lexical-sort resume.
    """

    IDLE = 0
    TREND = 1
    NICHE = 2
    RESEARCH_NLM = 3
    BLUEPRINT = 4
    SCRIPT = 5
    POLISH = 6
    VOICE = 7
    ASSETS = 8
    ASSEMBLY = 9
    THUMBNAIL = 10
    METADATA = 11
    UPLOAD = 12
    MONITOR = 13
    COMPLETE = 14


# ============================================================================
# Dependency DAG (ORCH-07, D-7)
# ============================================================================
#
# Each entry maps a gate to the tuple of gates that MUST be dispatched
# before it may run. Invariants enforced at import time by _validate_dag():
#   - ASSEMBLY depends on BOTH VOICE and ASSETS (D-7)
#   - UPLOAD depends on BOTH THUMBNAIL and METADATA
#   - COMPLETE depends on all 13 operational gates (verify_all_dispatched)
#   - graph is acyclic (graphlib.CycleError on violation)

GATE_DEPS: dict[GateName, tuple[GateName, ...]] = {
    GateName.IDLE: (),
    GateName.TREND: (GateName.IDLE,),
    GateName.NICHE: (GateName.TREND,),
    GateName.RESEARCH_NLM: (GateName.NICHE,),
    GateName.BLUEPRINT: (GateName.RESEARCH_NLM,),
    GateName.SCRIPT: (GateName.BLUEPRINT,),
    GateName.POLISH: (GateName.SCRIPT,),
    GateName.VOICE: (GateName.POLISH,),
    GateName.ASSETS: (GateName.POLISH,),
    GateName.ASSEMBLY: (GateName.VOICE, GateName.ASSETS),
    GateName.THUMBNAIL: (GateName.ASSEMBLY,),
    GateName.METADATA: (GateName.ASSEMBLY,),
    GateName.UPLOAD: (GateName.THUMBNAIL, GateName.METADATA),
    GateName.MONITOR: (GateName.UPLOAD,),
    GateName.COMPLETE: (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
        GateName.ASSEMBLY,
        GateName.THUMBNAIL,
        GateName.METADATA,
        GateName.UPLOAD,
        GateName.MONITOR,
    ),
}


# ============================================================================
# Exception hierarchy (ORCH-03 contract surface)
# ============================================================================


class OrchestratorError(Exception):
    """Base class for every orchestrator-originated error.

    Downstream callers MAY catch this to distinguish pipeline faults from
    library / network exceptions. Do NOT raise this class directly; raise a
    concrete subclass.
    """


class InvalidGateTransition(OrchestratorError):
    """Raised when the pipeline attempts an illegal GATE -> GATE move.

    Example: advancing from SCRIPT to ASSEMBLY (must pass through POLISH,
    VOICE, ASSETS first).
    """


class GateFailure(OrchestratorError):
    """Raised by GateGuard.dispatch when an Inspector verdict is FAIL.

    Carries the failing gate and evidence list so the regeneration loop (or
    higher-level handler) can decide whether to retry or escalate.
    """

    def __init__(self, gate: GateName, evidence: list[dict]) -> None:
        self.gate = gate
        self.evidence = evidence
        super().__init__(f"{gate.name} FAIL: {len(evidence)} violations")


class MissingVerdict(OrchestratorError):
    """Raised when dispatch() is called without a preceding Inspector verdict.

    Guarantees every GATE has been evaluated before transition. Plan 04
    GateGuard enforces this; downstream tests assert the raise.
    """


class IncompleteDispatch(OrchestratorError):
    """Raised at COMPLETE transition if not all 13 operational gates
    (TREND..MONITOR) are in the dispatched set (ORCH-04).
    """


class GateDependencyUnsatisfied(OrchestratorError):
    """Raised when a gate is started before its GATE_DEPS predecessors are
    fully dispatched. Example: ASSEMBLY before VOICE or ASSETS complete.
    """


class CircuitOpen(OrchestratorError):
    """Raised by CircuitBreaker.call() when the breaker is in OPEN state.

    Caller pattern: catch CircuitOpen, try fallback adapter (Runway if Kling
    fails, ElevenLabs if Typecast fails).
    """


class RegenerationExhausted(OrchestratorError):
    """Raised after 3 Producer retries all returned FAIL and the current gate
    has no fallback lane (i.e., not ASSETS/THUMBNAIL ken-burns eligible).
    Triggers append to .claude/failures/orchestrator.md (ORCH-12).
    """


class T2VForbidden(OrchestratorError):
    """Runtime guard. Should never fire if plan & Hook enforcement holds
    (VIDEO-01 / D-13: text-to-video code paths are physically absent).
    If raised, someone re-introduced T2V — treat as critical bug.
    """


class InvalidI2VRequest(OrchestratorError):
    """Raised when an I2VRequest violates VIDEO-02 constraints: duration
    outside [4, 8] seconds, move_count != 1, or missing anchor_frame.
    """


# ============================================================================
# Import-time DAG validation
# ============================================================================


def _validate_dag() -> None:
    """Assert GATE_DEPS is acyclic and covers every GateName.

    Executed at module bottom — if the DAG is malformed (cycle, missing gate)
    the import fails loudly with graphlib.CycleError or AssertionError,
    preventing broken pipelines from ever starting.
    """
    sorter = graphlib.TopologicalSorter(
        {g.name: {d.name for d in deps} for g, deps in GATE_DEPS.items()}
    )
    # static_order() internally calls prepare(); raises graphlib.CycleError
    # on cycle. Do not call prepare() separately — TopologicalSorter forbids
    # double-prepare and would raise ValueError on repeat invocation.
    ordered = list(sorter.static_order())
    expected = {g.name for g in GateName}
    actual = set(ordered)
    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        raise AssertionError(
            f"GATE_DEPS mismatch with GateName: missing={missing}, extra={extra}"
        )


_validate_dag()
