"""Phase 16-02 W1-RENDERER-CORE — narration audio drives video timing (Pitfall 5).

Principle: caller-supplied audio_duration can drift from the actual mp3 length.
ffprobe is SSOT for timing. If diff > 1.0s, warn and use ffprobe value.

durationInFrames = int(audio_duration * 30) — must match ffprobe-truthed value
within 30 frames (1.0s at 30fps).
"""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def renderer(tmp_path, monkeypatch):
    from scripts.orchestrator.api import remotion_renderer as mod
    remotion_dir = tmp_path / "remotion"
    remotion_dir.mkdir()
    (remotion_dir / "package.json").write_text('{"name":"x"}', encoding="utf-8")
    monkeypatch.setattr(mod.shutil, "which", lambda n: f"/usr/bin/{n}")
    return mod.RemotionRenderer(project_root=tmp_path)


def test_get_audio_duration_ffprobe_success(renderer, monkeypatch):
    """ffprobe OK → returns parsed float."""
    import subprocess
    from scripts.orchestrator.api import remotion_renderer as mod

    class FakeResult:
        returncode = 0
        stdout = "30.500\n"
        stderr = ""

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeResult())
    dur = renderer._get_audio_duration_ffprobe("fake.mp3")
    assert dur == 30.5


def test_get_audio_duration_ffprobe_failure_returns_zero(renderer, monkeypatch):
    """ffprobe failure → returns 0.0 (not exception)."""
    from scripts.orchestrator.api import remotion_renderer as mod

    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "no such file"

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: FakeResult())
    dur = renderer._get_audio_duration_ffprobe("missing.mp3")
    assert dur == 0.0


def test_get_audio_duration_ffprobe_timeout_returns_zero(renderer, monkeypatch):
    """ffprobe timeout → returns 0.0 (graceful)."""
    import subprocess
    from scripts.orchestrator.api import remotion_renderer as mod

    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="ffprobe", timeout=10)

    monkeypatch.setattr(mod.subprocess, "run", raise_timeout)
    dur = renderer._get_audio_duration_ffprobe("slow.mp3")
    assert dur == 0.0


def test_render_warns_on_duration_drift_and_prefers_ffprobe(
    renderer, tmp_path, monkeypatch, caplog
):
    """
    Scenario:
        caller passes audio_duration=60.0
        ffprobe reports 30.5s (drift > 1.0s)
    Expected:
        * logger.warning emitted
        * audio_duration updated to ffprobe value (30.5)
        * durationInFrames = int(30.5 * 30) = 915
    """
    import inspect
    from scripts.orchestrator.api import remotion_renderer as mod

    # Stub ffprobe → 30.5
    monkeypatch.setattr(renderer, "_get_audio_duration_ffprobe", lambda p: 30.5)

    fake_mp4 = tmp_path / "fake.mp4"

    captured: dict = {}

    def fake_build_props(
        script, channel, assets, subtitle_json_path, audio_duration, blueprint, visual_spec_path
    ):
        captured["audio_duration"] = audio_duration
        return {
            "audioSrc": "j/a.mp3",
            "titleLine1": "T",
            "channelName": "C",
            "subtitles": [],
            "durationInFrames": int(audio_duration * 30),
        }

    def fake_extract(timeline, episode_dir):
        return (
            {"audioSrc_abs": "/abs/narration.mp3", "audioSrc": "j/narration.mp3", "clips": []},
            60.0,  # caller-supplied (wrong) duration
            {"title": "t"},
            {},
            None,
            None,
        )

    monkeypatch.setattr(renderer, "_extract_from_timeline", fake_extract)
    monkeypatch.setattr(renderer, "_prepare_remotion_assets", lambda *a, **k: None)
    monkeypatch.setattr(renderer, "_pre_render_quality_gates", lambda *a, **k: None)
    monkeypatch.setattr(renderer, "_build_shorts_props", fake_build_props)
    monkeypatch.setattr(renderer, "_inject_character_props", lambda *a, **k: None)
    monkeypatch.setattr(renderer, "_validate_shorts_props", lambda *a, **k: None)
    monkeypatch.setattr(
        renderer,
        "_invoke_remotion_cli",
        lambda pp, op: op.write_bytes(b"\x00" * 100),
    )
    monkeypatch.setattr(renderer, "_cleanup_remotion_assets", lambda j: None)
    monkeypatch.setattr(
        renderer,
        "_verify_production_baseline",
        lambda p: {"width": 1080, "height": 1920, "codec": "h264", "duration": 30.5},
    )

    with caplog.at_level(logging.WARNING):
        result = renderer.render(timeline=[], resolution="fhd", aspect_ratio="9:16")

    # ffprobe value (30.5) preferred over caller (60.0)
    assert captured["audio_duration"] == 30.5
    assert result["duration_frames"] == 915  # int(30.5*30)
    # warning emitted
    messages = "\n".join(r.message for r in caplog.records)
    assert "duration" in messages.lower() or "ffprobe" in messages.lower()
