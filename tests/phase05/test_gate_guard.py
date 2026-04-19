"""Unit tests for GateGuard.dispatch / ensure_dependencies (Plan 05-04).

Verifies ORCH-03 + ORCH-07 runtime invariants per CONTEXT D-3 / D-7:
    - dispatch(gate, None)      -> MissingVerdict
    - dispatch(gate, FAIL)      -> GateFailure (no checkpoint, not marked)
    - dispatch(gate, PASS)      -> Checkpointer.save + mark dispatched
    - dispatch(gate, PASS, art) -> artifacts dict has sha256 + forward-slash path
    - ensure_dependencies(TREND)    -> no raise (TREND depends only on IDLE)
    - ensure_dependencies(ASSEMBLY) -> raise when VOICE missing
    - ensure_dependencies(ASSEMBLY) -> no raise when VOICE + ASSETS dispatched
    - dispatched property is a read-only view (mutations do not leak)
    - Verdict dataclass field shape matches rubric-schema.json

Plan 05-03 Checkpointer is landing in parallel (Wave 2); these tests use
a minimal local ``_FakeCheckpointer`` that implements the same save(cp)
contract so the tests run today without importing the sibling module.
Plan 05-07 will wire the real Checkpointer in pipeline composition.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.orchestrator import (
    GateDependencyUnsatisfied,
    GateFailure,
    GateName,
    MissingVerdict,
)
from scripts.orchestrator.gate_guard import Checkpoint, GateGuard, Verdict


# ---------------------------------------------------------------------------
# Fake Checkpointer — mirrors the Plan 05-03 save(Checkpoint) -> Path contract.
# ---------------------------------------------------------------------------


class _FakeCheckpointer:
    """Minimal Plan-05-03-compatible Checkpointer stub for Wave 2 parallel."""

    SCHEMA_VERSION = 1

    def __init__(self, state_root: Path) -> None:
        self.root = state_root

    def save(self, cp: Checkpoint) -> Path:
        target_dir = self.root / cp.session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"gate_{cp.gate_index:02d}.json"
        tmp = target.with_suffix(".tmp")
        payload = {"_schema": self.SCHEMA_VERSION, **asdict(cp)}
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp, target)
        return target


def _pass_verdict(score: int = 92) -> Verdict:
    return Verdict(
        result="PASS",
        score=score,
        evidence=[],
        semantic_feedback="all clean",
        inspector_name="shorts-supervisor",
    )


def _fail_verdict(violations: int = 2) -> Verdict:
    return Verdict(
        result="FAIL",
        score=42,
        evidence=[
            {"rule": f"HC-{i}", "line": 10 + i, "detail": "problem"}
            for i in range(violations)
        ],
        semantic_feedback="structural failures",
        inspector_name="shorts-supervisor",
    )


def _make_guard(tmp_state_dir: Path, session_id: str = "s1") -> GateGuard:
    return GateGuard(_FakeCheckpointer(tmp_state_dir), session_id)


# ---------------------------------------------------------------------------
# dispatch() — missing / FAIL / PASS behavior
# ---------------------------------------------------------------------------


def test_dispatch_none_verdict_raises_missing(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    with pytest.raises(MissingVerdict) as ei:
        g.dispatch(GateName.TREND, None)
    assert "TREND" in str(ei.value)


def test_dispatch_fail_verdict_raises_gate_failure(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    v = _fail_verdict(violations=3)
    with pytest.raises(GateFailure) as ei:
        g.dispatch(GateName.TREND, v)
    assert ei.value.gate == GateName.TREND
    assert len(ei.value.evidence) == 3
    assert ei.value.evidence[0]["rule"] == "HC-0"


def test_dispatch_fail_does_not_checkpoint(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    with pytest.raises(GateFailure):
        g.dispatch(GateName.TREND, _fail_verdict())
    session_dir = tmp_state_dir / "s1"
    assert not session_dir.exists() or not list(session_dir.glob("gate_*.json"))


def test_dispatch_fail_does_not_mark_dispatched(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    with pytest.raises(GateFailure):
        g.dispatch(GateName.TREND, _fail_verdict())
    assert GateName.TREND not in g.dispatched


def test_dispatch_pass_saves_checkpoint(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    g.dispatch(GateName.TREND, _pass_verdict())
    target = tmp_state_dir / "s1" / "gate_01.json"
    assert target.exists()


def test_dispatch_pass_marks_dispatched(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    g.dispatch(GateName.TREND, _pass_verdict())
    assert GateName.TREND in g.dispatched


def test_dispatch_artifact_sha256_recorded(tmp_state_dir, tmp_path):
    artifact = tmp_path / "asset.json"
    artifact.write_bytes(b"hello world")
    g = _make_guard(tmp_state_dir)
    g.dispatch(GateName.TREND, _pass_verdict(), artifact_path=artifact)
    data = json.loads(
        (tmp_state_dir / "s1" / "gate_01.json").read_text(encoding="utf-8")
    )
    # Known SHA-256 for b"hello world" (Pitfall 6 forward-slash check below).
    assert (
        data["artifacts"]["sha256"]
        == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )
    assert "\\" not in data["artifacts"]["path"]


def test_dispatch_no_artifact_yields_empty_dict(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    g.dispatch(GateName.TREND, _pass_verdict())
    data = json.loads(
        (tmp_state_dir / "s1" / "gate_01.json").read_text(encoding="utf-8")
    )
    assert data["artifacts"] == {}


def test_dispatch_without_checkpointer_still_marks_dispatched(tmp_state_dir):
    """GateGuard(None, ...) — dry-run mode: still tracks dispatched set."""
    g = GateGuard(None, "s1")
    g.dispatch(GateName.TREND, _pass_verdict())
    assert GateName.TREND in g.dispatched


# ---------------------------------------------------------------------------
# ensure_dependencies() — ORCH-07 runtime DAG check
# ---------------------------------------------------------------------------


def test_ensure_dependencies_passes_for_trend(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    # TREND depends only on IDLE (the root — always satisfied).
    g.ensure_dependencies(GateName.TREND)  # must not raise


def test_ensure_dependencies_raises_for_assembly_without_voice(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    for gname in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.ASSETS,
    ):
        g.dispatch(gname, _pass_verdict())
    with pytest.raises(GateDependencyUnsatisfied) as ei:
        g.ensure_dependencies(GateName.ASSEMBLY)
    assert "VOICE" in str(ei.value)


def test_ensure_dependencies_passes_when_voice_and_assets_done(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    for gname in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
    ):
        g.dispatch(gname, _pass_verdict())
    g.ensure_dependencies(GateName.ASSEMBLY)  # must not raise


def test_ensure_dependencies_upload_requires_thumbnail_and_metadata(tmp_state_dir):
    """UPLOAD depends on THUMBNAIL + METADATA per GATE_DEPS."""
    g = _make_guard(tmp_state_dir)
    # Dispatch everything up to and including ASSEMBLY.
    for gname in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
        GateName.ASSEMBLY,
    ):
        g.dispatch(gname, _pass_verdict())
    with pytest.raises(GateDependencyUnsatisfied):
        g.ensure_dependencies(GateName.UPLOAD)


# ---------------------------------------------------------------------------
# dispatched property + Verdict shape contract
# ---------------------------------------------------------------------------


def test_dispatched_is_read_only_view(tmp_state_dir):
    g = _make_guard(tmp_state_dir)
    g.dispatch(GateName.TREND, _pass_verdict())
    view = g.dispatched
    view.clear()  # mutating the snapshot MUST NOT affect internal state.
    assert GateName.TREND in g.dispatched


def test_verdict_fields_match_rubric_schema():
    """Contract: Verdict shape mirrors .claude/agents/_shared/rubric-schema.json."""
    v = Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="ok",
        inspector_name="shorts-supervisor",
    )
    d = asdict(v)
    assert set(d.keys()) == {
        "result",
        "score",
        "evidence",
        "semantic_feedback",
        "inspector_name",
    }


def test_verdict_inspector_name_optional():
    """rubric-schema.json inspector_name is optional — default None."""
    v = Verdict(result="PASS", score=70, evidence=[], semantic_feedback="")
    assert v.inspector_name is None
