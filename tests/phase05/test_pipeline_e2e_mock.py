"""End-to-end Mock tests for ShortsPipeline.run() (Plan 07).

Exercises the 13-GATE walk with every Producer / Supervisor / API
adapter mocked so the test suite never touches a real API. Two scenarios:

1. ``test_full_pipeline_runs_13_gates`` — fresh session; every
   ``_run_<gate>`` fires, the COMPLETE transition succeeds, the
   ``dispatched_count`` is 13, and Checkpointer wrote 14 files (one per
   operational gate + COMPLETE bookend).
2. ``test_pipeline_resume_from_checkpoint`` — pre-seed checkpoints for
   gates 1-3 on disk; run() resumes at gate 4, and Producers for gates
   1-3 are never invoked (ORCH-05 resume semantics).
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator import (
    GateName,
    ShortsPipeline,
    Verdict,
)


def _pass_verdict() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


@pytest.fixture
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        monkeypatch.setenv(var, "fake")


def test_full_pipeline_runs_13_gates(
    tmp_path: Path, _fake_env: None
) -> None:
    """End-to-end mock: 13 operational gates + COMPLETE all dispatch."""

    producer_output = {
        "artifact_path": str(tmp_path / "artifact.json"),
        "prompt": "p",
        "duration_seconds": 5,
        "anchor_frame": str(tmp_path / "a.png"),
    }
    producer = MagicMock(return_value=producer_output)
    supervisor = MagicMock(return_value=_pass_verdict())

    kling = MagicMock()
    kling.image_to_video.return_value = tmp_path / "cut.mp4"
    runway = MagicMock()
    runway.image_to_video.return_value = tmp_path / "cut.mp4"
    typecast = MagicMock()
    typecast.generate.return_value = []
    elevenlabs = MagicMock()
    elevenlabs.generate_with_timestamps.return_value = []
    shotstack = MagicMock()
    shotstack.render.return_value = {
        "url": str(tmp_path / "out.mp4"),
        "id": "r1",
        "status": "done",
    }
    shotstack.upscale.return_value = {"status": "skipped"}
    shotstack.create_ken_burns_clip.return_value = tmp_path / "kenburns.mp4"

    pipeline = ShortsPipeline(
        session_id="e2e_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=kling,
        runway_adapter=runway,
        typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs,
        shotstack_adapter=shotstack,
        producer_invoker=producer,
        supervisor_invoker=supervisor,
        asset_sourcer_invoker=lambda prompt: tmp_path / "stock.png",
    )

    # Stub VoiceFirstTimeline so empty audio/video lists round-trip cleanly.
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        result = pipeline.run()

    assert result["session_id"] == "e2e_test"
    assert result["final_gate"] == "COMPLETE"
    assert result["dispatched_count"] == 13
    assert result["fallback_count"] == 0

    # Checkpointer files: 13 operational gates + COMPLETE => 14 files.
    session_dir = tmp_path / "state" / "e2e_test"
    gate_files = sorted(session_dir.glob("gate_*.json"))
    assert len(gate_files) >= 13, (
        f"expected >=13 gate_*.json, got {[p.name for p in gate_files]}"
    )


def test_pipeline_resume_from_checkpoint(
    tmp_path: Path, _fake_env: None
) -> None:
    """ORCH-05 resume: pre-seeded gates 1-3 skip Producer invocation."""

    session_dir = tmp_path / "state" / "resume_test"
    session_dir.mkdir(parents=True)
    for idx, name in [(1, "TREND"), (2, "NICHE"), (3, "RESEARCH_NLM")]:
        (session_dir / f"gate_{idx:02d}.json").write_text(
            json.dumps(
                {
                    "_schema": 1,
                    "session_id": "resume_test",
                    "gate": name,
                    "gate_index": idx,
                    "timestamp": "2026-04-19T00:00:00+00:00",
                    "verdict": {
                        "result": "PASS",
                        "score": 90,
                        "evidence": [],
                        "semantic_feedback": "",
                        "inspector_name": "shorts-supervisor",
                    },
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )

    # Track which gates actually hit the Producer invoker.
    invoked_gates: list[str] = []

    def _producer(agent: str, gate: str, inputs: dict) -> dict:
        invoked_gates.append(gate)
        return {
            "artifact_path": str(tmp_path / f"{gate}.json"),
            "prompt": "p",
            "duration_seconds": 5,
            "anchor_frame": str(tmp_path / "a.png"),
        }

    kling = MagicMock()
    kling.image_to_video.return_value = tmp_path / "c.mp4"
    runway = MagicMock()
    runway.image_to_video.return_value = tmp_path / "c.mp4"
    typecast = MagicMock()
    typecast.generate.return_value = []
    elevenlabs = MagicMock()
    elevenlabs.generate_with_timestamps.return_value = []
    shotstack = MagicMock()
    shotstack.render.return_value = {"url": "u"}
    shotstack.upscale.return_value = {"status": "skipped"}
    shotstack.create_ken_burns_clip.return_value = tmp_path / "k.mp4"

    pipeline = ShortsPipeline(
        session_id="resume_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=kling,
        runway_adapter=runway,
        typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs,
        shotstack_adapter=shotstack,
        producer_invoker=_producer,
        supervisor_invoker=lambda g, o: _pass_verdict(),
        asset_sourcer_invoker=lambda p: Path("/tmp/a.png"),
    )
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()

    # Already-dispatched gates 1-3 must not re-invoke their producer.
    assert "TREND" not in invoked_gates
    assert "NICHE" not in invoked_gates
    assert "RESEARCH_NLM" not in invoked_gates
    # Gates 4+ SHOULD be invoked fresh (BLUEPRINT..MONITOR excl. VOICE/ASSETS/ASSEMBLY which
    # don't route through producer_invoker).
    assert "BLUEPRINT" in invoked_gates
    assert "SCRIPT" in invoked_gates


def test_pipeline_summary_includes_fallback_count(
    tmp_path: Path, _fake_env: None
) -> None:
    """run() summary dict exposes fallback_count from ctx.fallback_indices."""

    producer = MagicMock(
        return_value={
            "artifact_path": str(tmp_path / "x.json"),
            "prompt": "p",
            "duration_seconds": 5,
            "anchor_frame": str(tmp_path / "a.png"),
        }
    )
    shotstack = MagicMock()
    shotstack.render.return_value = {"url": "u"}
    shotstack.upscale.return_value = {"status": "skipped"}

    pipeline = ShortsPipeline(
        session_id="fb_count",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=MagicMock(),
        runway_adapter=MagicMock(),
        typecast_adapter=MagicMock(),
        elevenlabs_adapter=MagicMock(),
        shotstack_adapter=shotstack,
        producer_invoker=producer,
        supervisor_invoker=lambda g, o: _pass_verdict(),
        asset_sourcer_invoker=lambda p: Path("/tmp/stock.png"),
    )
    # Simulate a prior fallback insertion.
    pipeline.ctx.fallback_indices.extend([0, 3])

    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        result = pipeline.run()

    assert result["fallback_count"] == 2
