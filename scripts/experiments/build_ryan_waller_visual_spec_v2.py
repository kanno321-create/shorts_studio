"""Ryan Waller v2 — visual_spec.json rebuild with Kling I2V mp4 clips + new narration.

Session #34: v1 used static PNGs + Ken Burns; v2 uses Kling 2.6 Pro I2V mp4 clips
(scene_sources now point to mp4). Also updated audio duration (116.04s → 64.39s
after SSML injection removal).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.api import visual_spec_builder  # noqa: E402

EPISODE_ID = "ryan-waller"
EPISODE_DIR = Path("output/ryan-waller")
SOURCES_DIR = EPISODE_DIR / "sources"
SCRIPT = EPISODE_DIR / "script.json"
TIMING = EPISODE_DIR / "narration_timing.json"
PRESET_MEMORY = Path(".claude/memory/project_channel_preset_incidents.md")
OUT_BLUEPRINT = EPISODE_DIR / "blueprint.json"
OUT_SOURCES_MANIFEST = EPISODE_DIR / "sources_manifest.json"
OUT_VISUAL_SPEC = EPISODE_DIR / "visual_spec.json"


def main() -> int:
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    timing = json.loads(TIMING.read_text(encoding="utf-8"))
    audio_duration_s = timing["total_duration_s"]

    channel_preset = visual_spec_builder.load_channel_preset(PRESET_MEMORY)
    print(f"[SPEC] channel_preset loaded: {list(channel_preset.keys())}")

    blueprint = {
        "niche_tag": "incidents",
        "category": "crime",
        "tone": "탐정 하오체 독백 + 조수 해요체 질문 (duo dialogue)",
        "target_emotion": "사법 불신 + 인간 공허",
        "scene_count": 6,
        "target_duration_sec": round(audio_duration_s),
        "title_display": {
            "line1": "6시간 취조",
            "line2": "눈을 잃은 용의자",
            "accent_words": ["6시간", "눈"],
            "accent_color": "#FF2200",
        },
        "source_strategy": "gpt-image-2 anchors + Kling 2.6 Pro I2V motion clips (세션 #34 v2 교정)",
    }
    OUT_BLUEPRINT.write_text(
        json.dumps(blueprint, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SPEC] blueprint.json written (target_duration={blueprint['target_duration_sec']}s)")

    # v2: scene_sources now point to Kling mp4 clips (not static PNGs)
    scene_sources = [
        "broll_02_christmas_night.mp4",
        "broll_01_interrogation.mp4",
        "broll_03_clock.mp4",
        "broll_04_fleeing.mp4",
        "broll_05_hospital.mp4",
        "broll_06_court_dismissed.mp4",
    ]
    sources_manifest = {
        "scene_sources": scene_sources,
        "intro_signature": "intro_signature.mp4",
        "outro_signature": None,
        "character_detective": "character_detective.png",
        "character_assistant": "character_assistant.png",
        "real_ratio": 1.0,
        "asset_source": "gpt-image-2 medium anchors + Kling 2.6 Pro I2V 5s clips (세션 #34 v2)",
    }
    OUT_SOURCES_MANIFEST.write_text(
        json.dumps(sources_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SPEC] sources_manifest.json written ({len(scene_sources)} mp4 scene_sources)")

    print(f"[SPEC] audio_duration_s={audio_duration_s:.2f}, episode_id={EPISODE_ID}")
    spec = visual_spec_builder.build(
        blueprint=blueprint,
        script=script,
        channel_preset=channel_preset,
        sources_manifest=sources_manifest,
        audio_duration_s=audio_duration_s,
        episode_id=EPISODE_ID,
    )
    spec_dict = spec.model_dump(by_alias=True)

    spec_dict["audioSrc"] = f"{EPISODE_ID}/narration.mp3"
    spec_dict["characterLeftSrc"] = f"{EPISODE_ID}/character_assistant.png"
    spec_dict["characterRightSrc"] = f"{EPISODE_ID}/character_detective.png"

    # v2 post-process: mp4 scene clips already carry Kling internal motion —
    # suppress Ken Burns `movement` on video clips so the external camera pan
    # doesn't fight the internal subject motion (feedback_kling_i2v_required_not_ken_burns).
    suppressed = 0
    for clip in spec_dict.get("clips", []):
        if clip.get("type") == "video" and clip.get("src", "").endswith(".mp4"):
            src = clip.get("src", "")
            # Intro signature keeps its None; only suppress b-roll Kling mp4
            if "broll" in src and clip.get("movement") is not None:
                clip["movement"] = None
                suppressed += 1
    print(f"[SPEC] suppressed Ken Burns movement on {suppressed} Kling video clips")

    OUT_VISUAL_SPEC.write_text(
        json.dumps(spec_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"✅ Visual spec v2 built:")
    print(f"   blueprint       : {OUT_BLUEPRINT}")
    print(f"   sources_manifest: {OUT_SOURCES_MANIFEST}")
    print(f"   visual_spec     : {OUT_VISUAL_SPEC}")
    print(f"   durationInFrames: {spec_dict.get('durationInFrames')}")
    print(f"   clip count      : {len(spec_dict.get('clips', []))}")
    print(f"   clip types      : {[c.get('type') for c in spec_dict.get('clips', [])]}")
    print(f"   transitionType  : {spec_dict.get('transitionType')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
