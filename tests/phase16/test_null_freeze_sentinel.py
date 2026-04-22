"""Phase 16-02 W1-RENDERER-CORE — _NULL_FREEZE sentinel lifecycle (Pitfall 4).

Rule (harvested remotion_render.py:754-758):
    Designer's visual_spec.clipDesign[i].movement = null (JSON null / Python None)
    is an INTENTIONAL freeze. Must NOT be replaced with round-robin movement.

    Lifecycle:
        stage 1 (visual_spec inject): sc.movement = "_NULL_FREEZE" (sentinel)
        stage 2 (build_shorts_props):  propagate sentinel through to final clips
        stage 3 (before Zod validate): pop() movement key entirely if == "_NULL_FREEZE"

    Rationale: Zod schema rejects unknown values in movement enum. The sentinel
    protects us from the auto round-robin fallback path, then gets erased
    before subprocess invocation.
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


def test_null_freeze_sentinel_constant_exists():
    """Module exports NULL_FREEZE_SENTINEL constant."""
    from scripts.orchestrator.api import remotion_renderer as mod
    assert mod.NULL_FREEZE_SENTINEL == "_NULL_FREEZE"


def test_null_movement_is_popped_from_final_clip(renderer, tmp_path):
    """visual_spec clipDesign[i].movement=null → final clips[i] has no movement key."""
    visual_spec = {
        "titleLine1": "X",
        "titleLine2": "Y",
        "channelName": "사건기록부",
        "audioSrc": "j/a.mp3",
        "clipDesign": [
            {"movement": "zoom_in"},
            {"movement": None},  # JSON null = Python None → intentional freeze
            {"movement": "pan_left"},
        ],
    }
    spec_path = tmp_path / "visual_spec.json"
    spec_path.write_text(json.dumps(visual_spec), encoding="utf-8")

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
        visual_spec_path=spec_path,
    )
    clips = props["clips"]
    assert len(clips) == 3
    # Clip 0: movement preserved
    assert clips[0].get("movement") == "zoom_in"
    # Clip 1: movement KEY REMOVED (null freeze)
    assert "movement" not in clips[1], f"clip[1] still has movement: {clips[1]}"
    # Clip 2: movement preserved
    assert clips[2].get("movement") == "pan_left"


def test_invalid_movement_is_also_popped(renderer, tmp_path):
    """Unknown movement values should NOT pass through to Zod (pop or sentinel pop)."""
    visual_spec = {
        "clipDesign": [
            {"movement": "invalid_value"},
            {"movement": "zoom_in"},
        ],
    }
    spec_path = tmp_path / "visual_spec.json"
    spec_path.write_text(json.dumps(visual_spec), encoding="utf-8")
    assets = {
        "audioSrc": "j/a.mp3",
        "clips": [
            {"type": "image", "src": "j/clip_000.jpg"},
            {"type": "image", "src": "j/clip_001.jpg"},
        ],
    }
    props = renderer._build_shorts_props(
        script={"title": "T"},
        channel="incidents",
        assets=assets,
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint={},
        visual_spec_path=spec_path,
    )
    # invalid_value → sentinel → popped
    assert "movement" not in props["clips"][0] or props["clips"][0]["movement"] in (
        "zoom_in", "zoom_out", "pan_left", "pan_right",
    )
    # valid value preserved
    assert props["clips"][1].get("movement") == "zoom_in"


def test_sentinel_never_leaks_to_final_props(renderer, tmp_path):
    """Across many clipDesign shapes, _NULL_FREEZE sentinel must NEVER appear in final props."""
    visual_spec = {
        "clipDesign": [
            {"movement": None},
            {"movement": "zoom_in"},
            {"movement": None},
            {"movement": "pan_right"},
            {"movement": None},
        ],
    }
    spec_path = tmp_path / "visual_spec.json"
    spec_path.write_text(json.dumps(visual_spec), encoding="utf-8")
    assets = {
        "audioSrc": "j/a.mp3",
        "clips": [
            {"type": "image", "src": f"j/clip_{i:03d}.jpg"} for i in range(5)
        ],
    }
    props = renderer._build_shorts_props(
        script={"title": "T"},
        channel="incidents",
        assets=assets,
        subtitle_json_path=None,
        audio_duration=60.0,
        blueprint={},
        visual_spec_path=spec_path,
    )
    props_json = json.dumps(props)
    assert "_NULL_FREEZE" not in props_json, (
        "SENTINEL LEAK: _NULL_FREEZE appeared in final props — "
        "would break Zod validation downstream"
    )
