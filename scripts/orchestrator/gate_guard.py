"""GateGuard — single enforcement point for GATE dispatch (Plan 05-04).

Implements ORCH-03, ORCH-04, and the runtime half of ORCH-07 per Phase 5
CONTEXT D-3 / D-4 / D-7:

- ``dispatch(gate, verdict)`` raises GateFailure on FAIL verdict and
  MissingVerdict on None; on PASS it saves a checkpoint (if a Checkpointer
  is wired in) and adds the gate to the dispatched set.
- ``verify_all_dispatched()`` is the precondition for the COMPLETE transition
  (all 13 operational gates — TREND..MONITOR — must be dispatched).
- ``ensure_dependencies(gate)`` enforces the GATE_DEPS DAG at runtime.

Checkpointer integration is intentionally LAZY (parallel Wave 2 executor
note): Plan 05-03 lands the real Checkpointer alongside this module, and
Plan 05-07 composes them. GateGuard therefore accepts any duck-typed object
exposing ``.save(Checkpoint)`` (or ``None``), and ships its own minimal
``Checkpoint`` dataclass + ``sha256_file`` helper so tests can run without
the sibling module on disk.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .gates import (
    GATE_DEPS,
    GateDependencyUnsatisfied,
    GateFailure,
    GateName,
    MissingVerdict,
)

__all__ = ["Verdict", "Checkpoint", "GateGuard", "sha256_file"]


# ---------------------------------------------------------------------------
# Verdict dataclass — matches .claude/agents/_shared/rubric-schema.json draft-07
# ---------------------------------------------------------------------------


@dataclass
class Verdict:
    """Inspector output. Fields mirror rubric-schema.json required keys.

    ``result`` is ``"PASS"`` or ``"FAIL"``; ``score`` is 0-100; ``evidence``
    is a list of violation dicts; ``semantic_feedback`` is the VQQA gradient
    narrative for the Producer regeneration loop (RUB-03);
    ``inspector_name`` identifies the originating inspector (or the
    aggregated ``shorts-supervisor`` verdict).
    """

    result: Literal["PASS", "FAIL"]
    score: int
    evidence: list[dict]
    semantic_feedback: str
    inspector_name: str | None = None


# ---------------------------------------------------------------------------
# Local Checkpoint dataclass — duck-type compatible with Plan 05-03.
# ---------------------------------------------------------------------------


@dataclass
class Checkpoint:
    """Checkpoint payload. Plan 05-03 Checkpointer consumes this same shape."""

    session_id: str
    gate: str
    gate_index: int
    timestamp: str
    verdict: dict
    artifacts: dict


def sha256_file(path: Path) -> str:
    """Streaming SHA-256 of ``path`` (multi-GB safe; Windows-safe)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Operational gates — excludes IDLE + COMPLETE (D-4 verify_all_dispatched set).
# ---------------------------------------------------------------------------


_OPERATIONAL_GATES: frozenset[GateName] = frozenset(
    g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)
)


# ---------------------------------------------------------------------------
# GateGuard — the single enforcement point.
# ---------------------------------------------------------------------------


class GateGuard:
    """Enforces ORCH-03 / ORCH-04 / ORCH-07 runtime invariants.

    Pattern (CONTEXT D-3):
        1. ``ensure_dependencies(gate)`` — raises if a prereq is not dispatched.
        2. Producer emits artifact; Inspector produces ``Verdict``.
        3. ``dispatch(gate, verdict, artifact_path)`` — raises on None /
           FAIL; on PASS writes a checkpoint (if wired) and marks the gate
           dispatched.
        4. Before COMPLETE, ``verify_all_dispatched()`` must return True.

    ``checkpointer`` is optional: Plan 05-07 wires the real Plan 05-03
    Checkpointer. Passing ``None`` skips checkpoint I/O (used by unit
    tests and dry runs) but all other invariants still hold.
    """

    def __init__(self, checkpointer: Any | None, session_id: str) -> None:
        self.cp = checkpointer
        self.session_id = session_id
        self._dispatched: set[GateName] = set()

    @property
    def dispatched(self) -> set[GateName]:
        """Read-only view of the dispatched set (mutations don't leak)."""
        return set(self._dispatched)

    def dispatch(
        self,
        gate: GateName,
        verdict: Verdict | None,
        artifact_path: Path | None = None,
    ) -> None:
        """Single GATE transition point.

        Raises:
            MissingVerdict: ``verdict is None`` (Inspector was not called).
            GateFailure: ``verdict.result == "FAIL"`` (Inspector rejected).
        """
        if verdict is None:
            raise MissingVerdict(
                f"{gate.name}: Inspector must be called before dispatch (D-3)"
            )
        if verdict.result == "FAIL":
            raise GateFailure(gate, verdict.evidence)

        artifacts: dict = {}
        if artifact_path is not None and artifact_path.exists():
            artifacts = {
                # RESEARCH Pitfall 6: forward-slash paths for API/JSON.
                "path": str(artifact_path).replace("\\", "/"),
                "sha256": sha256_file(artifact_path),
            }

        cp = Checkpoint(
            session_id=self.session_id,
            gate=gate.name,
            gate_index=int(gate),
            timestamp=datetime.now(timezone.utc).isoformat(),
            verdict=asdict(verdict),
            artifacts=artifacts,
        )
        if self.cp is not None:
            self.cp.save(cp)
        self._dispatched.add(gate)

    def verify_all_dispatched(self) -> bool:
        """COMPLETE precondition (ORCH-04, D-4).

        Returns True only when every one of the 13 operational gates
        (TREND..MONITOR) is in the dispatched set. IDLE and COMPLETE are
        excluded by construction.
        """
        return _OPERATIONAL_GATES.issubset(self._dispatched)

    def ensure_dependencies(self, gate: GateName) -> None:
        """Runtime DAG check (ORCH-07, D-7).

        Raises ``GateDependencyUnsatisfied`` if any declared prerequisite
        in ``GATE_DEPS[gate]`` has not been dispatched. IDLE is the root
        and always treated as satisfied.
        """
        missing = [
            d
            for d in GATE_DEPS[gate]
            if d not in self._dispatched and d is not GateName.IDLE
        ]
        if missing:
            raise GateDependencyUnsatisfied(
                f"{gate.name} needs: {[g.name for g in missing]}"
            )

    def missing_for_complete(self) -> set[GateName]:
        """Diagnostic — gates still required before COMPLETE is reachable."""
        return set(_OPERATIONAL_GATES) - self._dispatched
