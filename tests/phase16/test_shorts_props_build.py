"""Phase 16-02 W1-RENDERER-CORE — _build_shorts_props output contract.

Tests the title line split, keyword accenting, durationInFrames arithmetic,
clipDesign preservation, and titleKeywords structure.
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


def test_build_shorts_props_uses_blueprint_title(renderer):
    """blueprint.title_display.line1/line2 가 있으면 우선 적용."""
    script = {"title": "전체 제목 무시"}
    blueprint = {
        "title_display": {
            "line1": "50년 미제",
            "line2": "암호 살인마",
            "accent_words": ["미제", "살인마"],
            "accent_color": "#FF2200",
        }
    }
    props = renderer._build_shorts_props(
        script=script,
        channel="incidents",
        assets={"audioSrc": "job/narration.mp3", "clips": []},
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint=blueprint,
        visual_spec_path=None,
    )
    assert props["titleLine1"] == "50년 미제"
    assert props["titleLine2"] == "암호 살인마"
    assert props["accentColor"] == "#FF2200"


def test_build_shorts_props_duration_in_frames_is_int(renderer):
    """durationInFrames = int(audio_duration * 30), type must be int (not float)."""
    props = renderer._build_shorts_props(
        script={"title": "테스트"},
        channel="incidents",
        assets={"audioSrc": "j/a.mp3", "clips": []},
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint={},
        visual_spec_path=None,
    )
    assert props["durationInFrames"] == 1800
    assert isinstance(props["durationInFrames"], int)


def test_build_shorts_props_duration_fractional_audio(renderer):
    """audio_duration=60.5s → durationInFrames=1815 (int truncation)."""
    props = renderer._build_shorts_props(
        script={"title": "테스트"},
        channel="incidents",
        assets={"audioSrc": "j/a.mp3", "clips": []},
        subtitle_json_path=None,
        audio_duration=60.5,
        blueprint={},
        visual_spec_path=None,
    )
    assert props["durationInFrames"] == 1815


def test_build_shorts_props_title_keywords_structure(renderer):
    """titleKeywords 가 blueprint.accent_words 기반으로 {text, color} 배열로 변환."""
    script = {"title": "서문"}
    blueprint = {
        "title_display": {
            "line1": "50년 미제",
            "line2": "암호 살인마",
            "accent_words": ["미제", "살인마"],
            "accent_color": "#FF2200",
        }
    }
    props = renderer._build_shorts_props(
        script=script,
        channel="incidents",
        assets={"audioSrc": "j/a.mp3", "clips": []},
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint=blueprint,
        visual_spec_path=None,
    )
    keywords = props.get("titleKeywords", [])
    assert isinstance(keywords, list)
    assert len(keywords) == 2
    for kw in keywords:
        assert "text" in kw and "color" in kw
        assert kw["color"] == "#FF2200"


def test_build_shorts_props_required_fields(renderer):
    """audioSrc / titleLine1 / channelName / subtitles / durationInFrames 모두 존재."""
    props = renderer._build_shorts_props(
        script={"title": "테스트"},
        channel="incidents",
        assets={"audioSrc": "j/narration.mp3", "clips": []},
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint={},
        visual_spec_path=None,
    )
    assert props["audioSrc"] == "j/narration.mp3"
    assert props["titleLine1"]
    assert props["channelName"]
    assert isinstance(props["subtitles"], list)
    assert isinstance(props["durationInFrames"], int)


def test_build_shorts_props_clips_duration_distributed(renderer):
    """multi-clip asset → props['clips'] 에 durationInFrames 분배."""
    assets = {
        "audioSrc": "j/a.mp3",
        "clips": [
            {"type": "image", "src": "j/clip_000.jpg"},
            {"type": "image", "src": "j/clip_001.jpg"},
            {"type": "image", "src": "j/clip_002.jpg"},
        ],
    }
    props = renderer._build_shorts_props(
        script={"title": "T"},
        channel="incidents",
        assets=assets,
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint={},
        visual_spec_path=None,
    )
    assert "clips" in props
    assert len(props["clips"]) == 3
    for clip in props["clips"]:
        assert clip["type"] in ("image", "video")
        assert isinstance(clip["durationInFrames"], int)
        assert clip["durationInFrames"] > 0
