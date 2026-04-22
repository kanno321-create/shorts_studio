"""Phase 16-02 W1-RENDERER-CORE — RemotionRenderer public API contract.

Tests:
    * __init__ probe behavior — node missing → RemotionUnavailable
    * __init__ probe — remotion/ dir missing → RemotionUnavailable
    * __init__ probe — ffprobe missing → RemotionUnavailable
    * render() signature mirror FfmpegAssembler.render(timeline, resolution, aspect_ratio) → dict
    * render() result dict keys {url, status, renderer="remotion", duration_frames, size_mb}
    * upscale() NOOP returns {"status": "skipped", ...}

Scope: unit — no real subprocess invocation (monkeypatched).
"""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def remotion_stub(tmp_path: Path) -> Path:
    """Create a minimal remotion/ directory with package.json so constructor passes."""
    remotion_dir = tmp_path / "remotion"
    remotion_dir.mkdir()
    (remotion_dir / "package.json").write_text(
        '{"name":"shorts-remotion","dependencies":{"remotion":"^4.0.0"}}',
        encoding="utf-8",
    )
    (remotion_dir / "src").mkdir()
    (remotion_dir / "src" / "index.ts").write_text("// stub", encoding="utf-8")
    return tmp_path


def test_import_renderer_and_exceptions():
    """Import contract."""
    from scripts.orchestrator.api.remotion_renderer import (
        RemotionRenderer,
        RemotionUnavailable,
        RemotionValidationError,
        RemotionBaselineError,
    )
    assert RemotionRenderer is not None
    assert issubclass(RemotionUnavailable, RuntimeError)
    assert issubclass(RemotionValidationError, ValueError)
    assert issubclass(RemotionBaselineError, RuntimeError)


def test_init_raises_when_node_missing(remotion_stub, monkeypatch):
    """node missing on PATH → RemotionUnavailable."""
    from scripts.orchestrator.api import remotion_renderer as mod

    def fake_which(name):
        if name == "node":
            return None
        return f"/usr/bin/{name}"

    monkeypatch.setattr(mod.shutil, "which", fake_which)
    with pytest.raises(mod.RemotionUnavailable, match="node"):
        mod.RemotionRenderer(project_root=remotion_stub)


def test_init_raises_when_remotion_dir_missing(tmp_path, monkeypatch):
    """remotion/ directory missing → RemotionUnavailable."""
    from scripts.orchestrator.api import remotion_renderer as mod
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")
    with pytest.raises(mod.RemotionUnavailable, match="remotion"):
        mod.RemotionRenderer(project_root=tmp_path)  # no remotion/ dir


def test_init_raises_when_ffprobe_missing(remotion_stub, monkeypatch):
    """ffprobe missing on PATH → RemotionUnavailable (baseline 검증 불가)."""
    from scripts.orchestrator.api import remotion_renderer as mod

    def fake_which(name):
        if name == "ffprobe":
            return None
        return f"/usr/bin/{name}"

    monkeypatch.setattr(mod.shutil, "which", fake_which)
    with pytest.raises(mod.RemotionUnavailable, match="ffprobe"):
        mod.RemotionRenderer(project_root=remotion_stub)


def test_init_succeeds_when_all_deps_present(remotion_stub, monkeypatch):
    """All deps present → construct normally."""
    from scripts.orchestrator.api import remotion_renderer as mod
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")
    r = mod.RemotionRenderer(project_root=remotion_stub)
    assert r.remotion_dir.name == "remotion"
    assert r.timeout_s == 600
    assert r.first_render_timeout_s == 180


def test_upscale_is_noop(remotion_stub, monkeypatch):
    """upscale() is Phase 8 NOOP — returns skipped status."""
    from scripts.orchestrator.api import remotion_renderer as mod
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")
    r = mod.RemotionRenderer(project_root=remotion_stub)
    result = r.upscale("ignored")
    assert result["status"] == "skipped"
    assert "remotion" in result["reason"].lower() or "1080" in result["reason"]


def test_render_signature_matches_ffmpeg_assembler(remotion_stub, monkeypatch):
    """render() accepts (timeline, resolution, aspect_ratio) like FfmpegAssembler."""
    from scripts.orchestrator.api import remotion_renderer as mod
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")
    r = mod.RemotionRenderer(project_root=remotion_stub)
    # Signature check — Python inspect
    import inspect
    sig = inspect.signature(r.render)
    params = list(sig.parameters)
    # Must accept timeline (pos), resolution (kw-default), aspect_ratio (kw-default)
    assert "timeline" in params
    assert "resolution" in params
    assert "aspect_ratio" in params
    # Defaults mirror ffmpeg_assembler (resolution default, aspect_ratio="9:16")
    assert sig.parameters["aspect_ratio"].default == "9:16"


def test_render_result_contract_keys(remotion_stub, monkeypatch, tmp_path):
    """render() result dict must carry {url, status, renderer, duration_frames, size_mb}."""
    from scripts.orchestrator.api import remotion_renderer as mod
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")

    r = mod.RemotionRenderer(project_root=remotion_stub)

    # Stub internal pipeline — isolate contract surface from the subprocess details.
    fake_mp4 = tmp_path / "fake.mp4"
    fake_mp4.write_bytes(b"\x00" * 1024)

    def fake_extract(timeline, episode_dir):
        return ({"audioSrc_abs": None, "audioSrc": "j/narration.mp3", "clips": []},
                60.0, {"title": "t"}, {}, None, None)

    def fake_prepare(job_id, assets, series):
        pass

    def fake_build_props(*args, **kwargs):
        return {
            "audioSrc": "j/narration.mp3",
            "titleLine1": "Test",
            "channelName": "사건기록부",
            "subtitles": [],
            "durationInFrames": 1800,
        }

    def fake_validate(props):
        return None

    def fake_invoke_cli(props_path, output_path):
        output_path.write_bytes(b"\x00" * 2048)

    def fake_verify(final_path):
        return {"width": 1080, "height": 1920, "codec": "h264", "duration": 60.0}

    monkeypatch.setattr(r, "_extract_from_timeline", fake_extract)
    monkeypatch.setattr(r, "_prepare_remotion_assets", fake_prepare)
    monkeypatch.setattr(r, "_get_audio_duration_ffprobe", lambda p: 0.0)
    monkeypatch.setattr(r, "_pre_render_quality_gates", lambda *a, **k: None)
    monkeypatch.setattr(r, "_build_shorts_props", fake_build_props)
    monkeypatch.setattr(r, "_inject_character_props", lambda props, j, e: None)
    monkeypatch.setattr(r, "_validate_shorts_props", fake_validate)
    monkeypatch.setattr(r, "_invoke_remotion_cli", fake_invoke_cli)
    monkeypatch.setattr(r, "_cleanup_remotion_assets", lambda j: None)
    monkeypatch.setattr(r, "_verify_production_baseline", fake_verify)

    result = r.render(timeline=[], resolution="fhd", aspect_ratio="9:16")
    assert set(result.keys()) >= {"url", "status", "renderer", "duration_frames", "size_mb"}
    assert result["renderer"] == "remotion"
    assert result["status"] == "assembled"
    assert result["duration_frames"] == 1800
    assert result["size_mb"] >= 0
