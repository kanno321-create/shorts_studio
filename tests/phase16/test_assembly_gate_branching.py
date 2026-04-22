"""Phase 16-02 W2-ASSEMBLY — _run_assembly 3-branch cascade verification.

Tests ShortsPipeline._run_assembly renderer selection priority:
    remotion > shotstack > ffmpeg_assembler.

Uses unittest.mock to construct a minimally-wired ShortsPipeline instance
and inject each renderer combination. Validates:
    * correct renderer picked based on presence/absence
    * RuntimeError when all three are None
    * renderer metadata injected into render_result
    * Shotstack goes through circuit breaker, Remotion/ffmpeg don't
    * upscale() called after render() (Phase 4 regression preserved)
"""
from __future__ import annotations

import types
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


def _build_pipeline_skeleton(
    *,
    remotion: MagicMock | None = None,
    shotstack: MagicMock | None = None,
    ffmpeg: MagicMock | None = None,
) -> MagicMock:
    """Construct a MagicMock ShortsPipeline instance with renderer slots wired."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    pipeline = MagicMock(spec=ShortsPipeline)
    pipeline.remotion_renderer = remotion
    pipeline.shotstack = shotstack
    pipeline.ffmpeg_assembler = ffmpeg
    pipeline.shotstack_breaker = MagicMock()
    pipeline.shotstack_breaker.call.side_effect = lambda fn: fn()
    pipeline.timeline = MagicMock()
    pipeline.timeline.align.return_value = []
    pipeline.timeline.insert_transition_shots.return_value = []
    pipeline.supervisor_invoker = MagicMock(return_value=MagicMock(status="pass"))
    pipeline.gate_guard = MagicMock()
    return pipeline


def _make_renderer_mock(name: str, url: str = "out.mp4") -> MagicMock:
    r = MagicMock(name=f"{name}_renderer")
    r.render.return_value = {"url": url, "status": "assembled", "renderer": name}
    r.upscale.return_value = {"status": "skipped"}
    return r


@pytest.fixture
def ctx():
    """Minimal GateContext-like stub."""
    c = MagicMock()
    c.audio_segments = []
    c.video_cuts = []
    c.artifacts = {}
    return c


def test_import_pipeline_has_remotion_renderer_attr():
    """ShortsPipeline.__init__ sets self.remotion_renderer (or None)."""
    import inspect
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    src = inspect.getsource(ShortsPipeline)
    assert "self.remotion_renderer" in src
    assert "from .api.remotion_renderer import RemotionRenderer" in src


def test_cascade_picks_remotion_when_available(ctx):
    """All three present → picks remotion."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    rem = _make_renderer_mock("remotion")
    shot = _make_renderer_mock("shotstack")
    ff = _make_renderer_mock("ffmpeg")
    pipeline = _build_pipeline_skeleton(remotion=rem, shotstack=shot, ffmpeg=ff)
    # Call the real _run_assembly method with the mock instance
    ShortsPipeline._run_assembly(pipeline, ctx)
    rem.render.assert_called_once()
    shot.render.assert_not_called()
    ff.render.assert_not_called()


def test_cascade_picks_shotstack_when_remotion_missing(ctx):
    """remotion=None, shotstack+ffmpeg present → picks shotstack (via breaker)."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    shot = _make_renderer_mock("shotstack")
    ff = _make_renderer_mock("ffmpeg")
    pipeline = _build_pipeline_skeleton(remotion=None, shotstack=shot, ffmpeg=ff)
    ShortsPipeline._run_assembly(pipeline, ctx)
    shot.render.assert_called_once()
    ff.render.assert_not_called()
    # Shotstack must go through circuit breaker
    pipeline.shotstack_breaker.call.assert_called_once()


def test_cascade_picks_ffmpeg_when_only_ffmpeg_available(ctx):
    """remotion=shotstack=None → picks ffmpeg."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    ff = _make_renderer_mock("ffmpeg")
    pipeline = _build_pipeline_skeleton(remotion=None, shotstack=None, ffmpeg=ff)
    ShortsPipeline._run_assembly(pipeline, ctx)
    ff.render.assert_called_once()
    # ffmpeg does NOT go through circuit breaker
    pipeline.shotstack_breaker.call.assert_not_called()


def test_cascade_raises_when_all_renderers_none(ctx):
    """All three None → RuntimeError with diagnostic."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    pipeline = _build_pipeline_skeleton(remotion=None, shotstack=None, ffmpeg=None)
    with pytest.raises(RuntimeError, match="Remotion/Shotstack/ffmpeg"):
        ShortsPipeline._run_assembly(pipeline, ctx)


def test_remotion_called_at_fhd_resolution(ctx):
    """Remotion renderer must be invoked with resolution='fhd' (1080p native)."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    rem = _make_renderer_mock("remotion")
    pipeline = _build_pipeline_skeleton(remotion=rem, shotstack=None, ffmpeg=None)
    ShortsPipeline._run_assembly(pipeline, ctx)
    _, kwargs = rem.render.call_args
    assert kwargs.get("resolution") == "fhd"
    assert kwargs.get("aspect_ratio") == "9:16"


def test_shotstack_called_at_hd_resolution_through_breaker(ctx):
    """Shotstack must be invoked with resolution='hd' via circuit breaker (ORCH-11)."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    shot = _make_renderer_mock("shotstack")
    pipeline = _build_pipeline_skeleton(remotion=None, shotstack=shot, ffmpeg=None)
    ShortsPipeline._run_assembly(pipeline, ctx)
    _, kwargs = shot.render.call_args
    assert kwargs.get("resolution") == "hd"


def test_upscale_called_after_render(ctx):
    """Phase 4 regression — renderer.upscale() MUST be called after render."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    rem = _make_renderer_mock("remotion")
    pipeline = _build_pipeline_skeleton(remotion=rem, shotstack=None, ffmpeg=None)
    # Sequence tracking
    call_order: list[str] = []
    rem.render.side_effect = lambda *a, **k: call_order.append("render") or {
        "url": "out.mp4",
        "status": "assembled",
        "renderer": "remotion",
    }
    rem.upscale.side_effect = lambda *a, **k: call_order.append("upscale") or {
        "status": "skipped"
    }
    ShortsPipeline._run_assembly(pipeline, ctx)
    assert call_order == ["render", "upscale"]


def test_renderer_metadata_default_injected_when_missing(ctx):
    """If renderer.render() returns dict without 'renderer' key, pipeline stamps class name."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline
    rem = MagicMock(name="remotion_renderer")
    rem.render.return_value = {"url": "out.mp4", "status": "assembled"}  # NO renderer key
    rem.upscale.return_value = {"status": "skipped"}
    pipeline = _build_pipeline_skeleton(remotion=rem, shotstack=None, ffmpeg=None)
    ShortsPipeline._run_assembly(pipeline, ctx)
    # gate_guard receives supervisor_invoker verdict; metadata must be stamped
    # on render_result. Inspect supervisor_invoker call args.
    pipeline.supervisor_invoker.assert_called_once()
    _, rr = pipeline.supervisor_invoker.call_args[0]
    assert "renderer" in rr
