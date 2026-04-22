"""Phase 16-02 W1-RENDERER-CORE — _verify_production_baseline (Pitfall 1).

Principle: "spec pass ≠ production pass". After Remotion render, ffprobe the
output and enforce:
    * width=1080, height=1920 (Shorts 9:16)
    * codec in {h264, hevc}
    * duration ≥ MIN_PRODUCTION_DURATION_S (= 60.0, ROADMAP Phase 16 SC#4)
    * RemotionBaselineError on any violation
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def renderer(tmp_path, monkeypatch):
    from scripts.orchestrator.api import remotion_renderer as mod
    remotion_dir = tmp_path / "remotion"
    remotion_dir.mkdir()
    (remotion_dir / "package.json").write_text('{"name":"x"}', encoding="utf-8")
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")
    return mod.RemotionRenderer(project_root=tmp_path)


def _stub_ffprobe(monkeypatch, width, height, codec, duration):
    """Stub subprocess.run for ffprobe calls with fixed output."""
    from scripts.orchestrator.api import remotion_renderer as mod

    class FakeResult:
        returncode = 0
        stderr = ""

        @property
        def stdout(self):
            return json.dumps({
                "streams": [
                    {"codec_type": "video", "width": width, "height": height, "codec_name": codec}
                ],
                "format": {"duration": str(duration)},
            })

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeResult())


def test_min_production_duration_is_sixty_seconds():
    """ROADMAP Phase 16 SC#4 — MIN_PRODUCTION_DURATION_S = 60.0 (not 50.0)."""
    from scripts.orchestrator.api import remotion_renderer as mod
    assert mod.MIN_PRODUCTION_DURATION_S == 60.0


def test_target_resolution_is_1080x1920():
    from scripts.orchestrator.api import remotion_renderer as mod
    assert mod.TARGET_RESOLUTION == (1080, 1920)


def test_baseline_passes_for_valid_output(renderer, tmp_path, monkeypatch):
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)
    _stub_ffprobe(monkeypatch, 1080, 1920, "h264", 60.5)
    meta = renderer._verify_production_baseline(final)
    assert meta["width"] == 1080
    assert meta["height"] == 1920
    assert meta["codec"] == "h264"
    assert meta["duration"] == 60.5


def test_baseline_passes_for_hevc(renderer, tmp_path, monkeypatch):
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)
    _stub_ffprobe(monkeypatch, 1080, 1920, "hevc", 90.0)
    meta = renderer._verify_production_baseline(final)
    assert meta["codec"] == "hevc"


def test_baseline_rejects_wrong_resolution(renderer, tmp_path, monkeypatch):
    from scripts.orchestrator.api.remotion_renderer import RemotionBaselineError
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)
    _stub_ffprobe(monkeypatch, 720, 1280, "h264", 60.5)  # 720p not 1080p
    with pytest.raises(RemotionBaselineError, match="해상도|1080|1920"):
        renderer._verify_production_baseline(final)


def test_baseline_rejects_short_duration(renderer, tmp_path, monkeypatch):
    """50s < 60s (MIN_PRODUCTION_DURATION_S) → fail."""
    from scripts.orchestrator.api.remotion_renderer import RemotionBaselineError
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)
    _stub_ffprobe(monkeypatch, 1080, 1920, "h264", 50.0)
    with pytest.raises(RemotionBaselineError, match="길이|60"):
        renderer._verify_production_baseline(final)


def test_baseline_rejects_exactly_below_sixty(renderer, tmp_path, monkeypatch):
    """59.99s < 60.0 → fail (strict)."""
    from scripts.orchestrator.api.remotion_renderer import RemotionBaselineError
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)
    _stub_ffprobe(monkeypatch, 1080, 1920, "h264", 59.99)
    with pytest.raises(RemotionBaselineError):
        renderer._verify_production_baseline(final)


def test_baseline_rejects_unknown_codec(renderer, tmp_path, monkeypatch):
    from scripts.orchestrator.api.remotion_renderer import RemotionBaselineError
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)
    _stub_ffprobe(monkeypatch, 1080, 1920, "vp9", 60.5)
    with pytest.raises(RemotionBaselineError, match="codec"):
        renderer._verify_production_baseline(final)


def test_baseline_rejects_missing_file(renderer, tmp_path):
    from scripts.orchestrator.api.remotion_renderer import RemotionBaselineError
    missing = tmp_path / "nonexistent.mp4"
    with pytest.raises(RemotionBaselineError, match="미생성|생성"):
        renderer._verify_production_baseline(missing)


def test_baseline_rejects_missing_video_stream(renderer, tmp_path, monkeypatch):
    """ffprobe returns audio-only → no video stream → error."""
    from scripts.orchestrator.api import remotion_renderer as mod
    from scripts.orchestrator.api.remotion_renderer import RemotionBaselineError
    final = tmp_path / "out.mp4"
    final.write_bytes(b"\x00" * 1024)

    class FakeResult:
        returncode = 0
        stderr = ""
        stdout = json.dumps({"streams": [{"codec_type": "audio"}], "format": {"duration": "60.0"}})

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeResult())
    with pytest.raises(RemotionBaselineError, match="video|stream"):
        renderer._verify_production_baseline(final)
