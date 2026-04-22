"""Phase 16-02 W1-RENDERER-CORE — _validate_shorts_props contract.

Tests that malformed props raise RemotionValidationError with actionable messages.
"""
from __future__ import annotations

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


@pytest.fixture
def valid_props():
    return {
        "audioSrc": "job/narration.mp3",
        "titleLine1": "50년 미제",
        "channelName": "사건기록부",
        "durationInFrames": 1800,
        "subtitles": [],
    }


def test_validate_accepts_valid_props(renderer, valid_props):
    renderer._validate_shorts_props(valid_props)  # no raise


def test_validate_rejects_empty_audio_src(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["audioSrc"] = ""
    with pytest.raises(RemotionValidationError, match="audioSrc"):
        renderer._validate_shorts_props(valid_props)


def test_validate_rejects_none_audio_src(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["audioSrc"] = None
    with pytest.raises(RemotionValidationError):
        renderer._validate_shorts_props(valid_props)


def test_validate_rejects_float_duration_in_frames(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["durationInFrames"] = 1800.0  # must be int
    with pytest.raises(RemotionValidationError, match="durationInFrames"):
        renderer._validate_shorts_props(valid_props)


def test_validate_rejects_zero_duration_in_frames(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["durationInFrames"] = 0
    with pytest.raises(RemotionValidationError):
        renderer._validate_shorts_props(valid_props)


def test_validate_rejects_none_subtitles(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["subtitles"] = None
    with pytest.raises(RemotionValidationError, match="subtitles"):
        renderer._validate_shorts_props(valid_props)


def test_validate_rejects_missing_title_line1(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["titleLine1"] = ""
    with pytest.raises(RemotionValidationError, match="titleLine1"):
        renderer._validate_shorts_props(valid_props)


def test_validate_rejects_missing_channel_name(renderer, valid_props):
    from scripts.orchestrator.api.remotion_renderer import RemotionValidationError
    valid_props["channelName"] = ""
    with pytest.raises(RemotionValidationError, match="channelName"):
        renderer._validate_shorts_props(valid_props)
