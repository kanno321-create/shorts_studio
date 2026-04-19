"""ORCH-11 Low-Res First tests (Plan 07).

Scenarios:

1. ``test_shotstack_render_called_with_hd`` — ``_run_assembly`` passes
   ``resolution="hd"`` to the Shotstack adapter.
2. ``test_upscale_after_render`` — ``render()`` runs strictly before
   ``upscale()`` (temporal ordering; D-11).
3. ``test_upscale_phase_8_stub_returns_skipped`` — the adapter-level
   ``ShotstackAdapter.upscale()`` is a NOOP returning
   ``{"status": "skipped", ...}`` per RESEARCH §7.
4. ``test_render_default_aspect_9_16`` — ``_run_assembly`` also pins
   ``aspect_ratio="9:16"`` for Shorts format.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator import (
    AudioSegment,
    GateName,
    ShortsPipeline,
    Verdict,
    VideoCut,
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


def _make_assembly_ready_pipeline(
    tmp_path: Path, shotstack: MagicMock
) -> ShortsPipeline:
    pipeline = ShortsPipeline(
        session_id="lr_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=MagicMock(),
        runway_adapter=MagicMock(),
        typecast_adapter=MagicMock(),
        elevenlabs_adapter=MagicMock(),
        shotstack_adapter=shotstack,
        producer_invoker=MagicMock(return_value={}),
        supervisor_invoker=lambda g, o: _pass_verdict(),
        asset_sourcer_invoker=lambda p: Path("/tmp/x"),
    )
    pipeline.ctx.audio_segments = [
        AudioSegment(0, 0.0, 5.0, 5.0, Path("a.mp3"))
    ]
    pipeline.ctx.video_cuts = [
        VideoCut(0, Path("v.mp4"), 5.0, "prompt", Path("anchor.png"))
    ]
    # Pre-dispatch every gate up to ASSETS so ASSEMBLY can run.
    for gate in GateName:
        if gate in (GateName.IDLE, GateName.COMPLETE):
            continue
        if gate.value <= GateName.ASSETS.value:
            pipeline.gate_guard._dispatched.add(gate)
    return pipeline


def test_shotstack_render_called_with_hd(
    tmp_path: Path, _fake_env: None
) -> None:
    """ORCH-11: ASSEMBLY gate passes resolution='hd' (720p) to Shotstack."""

    shotstack = MagicMock()
    shotstack.render.return_value = {
        "url": str(tmp_path / "out.mp4"),
        "id": "r1",
    }
    shotstack.upscale.return_value = {"status": "skipped"}

    pipeline = _make_assembly_ready_pipeline(tmp_path, shotstack)
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline._run_assembly(pipeline.ctx)

    shotstack.render.assert_called_once()
    call_kwargs = shotstack.render.call_args.kwargs
    assert call_kwargs.get("resolution") == "hd", (
        f"ORCH-11 violated: render not called with resolution='hd': "
        f"{shotstack.render.call_args}"
    )


def test_render_default_aspect_9_16(
    tmp_path: Path, _fake_env: None
) -> None:
    """ASSEMBLY passes aspect_ratio='9:16' (Shorts format)."""

    shotstack = MagicMock()
    shotstack.render.return_value = {"url": "u"}
    shotstack.upscale.return_value = {"status": "skipped"}

    pipeline = _make_assembly_ready_pipeline(tmp_path, shotstack)
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline._run_assembly(pipeline.ctx)

    call_kwargs = shotstack.render.call_args.kwargs
    assert call_kwargs.get("aspect_ratio") == "9:16"


def test_upscale_after_render(
    tmp_path: Path, _fake_env: None
) -> None:
    """Ordering: render() must run before upscale() (ORCH-11 D-11)."""

    calls: list[str] = []
    shotstack = MagicMock()
    shotstack.render = MagicMock(
        side_effect=lambda *a, **kw: (calls.append("render"), {"url": "u"})[1]
    )
    shotstack.upscale = MagicMock(
        side_effect=lambda *a, **kw: (calls.append("upscale"), {"status": "skipped"})[1]
    )

    pipeline = _make_assembly_ready_pipeline(tmp_path, shotstack)
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline._run_assembly(pipeline.ctx)

    assert "render" in calls
    assert "upscale" in calls
    assert calls.index("render") < calls.index("upscale"), (
        "render must run before upscale (ORCH-11 ordering)"
    )


def test_upscale_phase_8_stub_returns_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adapter-level test: ShotstackAdapter.upscale() is NOOP returning skipped."""

    monkeypatch.setenv("SHOTSTACK_API_KEY", "fake")
    from scripts.orchestrator.api.shotstack import ShotstackAdapter

    adapter = ShotstackAdapter(api_key="fake")
    result = adapter.upscale("https://example.com/src.mp4")
    assert result["status"] == "skipped"
    assert "Phase 8" in result["reason"] or "deferred" in result["reason"]
