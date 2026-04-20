"""Pipeline state enums (REQ-091-01, Phase 9.1).

Exposes the canonical ``Verdict`` enum consumed by the Claude Agent SDK
supervisor invoker. Kept in a dedicated module (NOT ``gate_guard.py``)
because the Phase 5 ``gate_guard.Verdict`` is a rubric-schema dataclass
carrying ``result: Literal["PASS","FAIL"]`` + evidence/score payloads,
whereas the 9.1 invoker needs a simple enum identity match for
JSON-parsed LLM supervisor verdicts.

Design note
-----------
The two ``Verdict`` types coexist intentionally:

* ``scripts.orchestrator.gate_guard.Verdict`` — dataclass (rubric-schema
  draft-07 shape). Consumed by ``ShortsPipeline._producer_loop`` and
  ``GateGuard.dispatch`` via ``verdict.result == "PASS"`` / "FAIL".
* ``scripts.orchestrator.state.Verdict`` — Enum (PASS/FAIL/RETRY).
  Returned by :class:`ClaudeAgentSupervisorInvoker` for identity-based
  checks (``is Verdict.FAIL``). Includes a ``.result`` property so enum
  instances remain compatible with the pipeline's dataclass-style reads
  (defensive: when Phase 10 wires the live supervisor, the enum return
  type will flow through ``_producer_loop.verdict.result``).
"""
from __future__ import annotations

from enum import Enum

__all__ = ["Verdict"]


class Verdict(Enum):
    """Supervisor verdict identifier.

    Members:
        PASS  — Inspector consensus accepts the Producer output.
        FAIL  — Inspector consensus rejects; regeneration loop triggers.
        RETRY — Transient failure (rate limit, partial output); caller
                retries without FAIL bookkeeping.

    The ``.result`` property returns the rubric-schema-compatible string
    form so this enum can be used interchangeably with the Phase 5
    dataclass Verdict wherever ``verdict.result == "PASS"`` reads occur.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    RETRY = "RETRY"

    @property
    def result(self) -> str:
        """Rubric-schema compatible string form (PASS / FAIL).

        ``RETRY`` normalises to ``"FAIL"`` so the regeneration loop in
        :meth:`ShortsPipeline._producer_loop` advances retry counters
        rather than silently passing through.
        """
        return "PASS" if self is Verdict.PASS else "FAIL"
