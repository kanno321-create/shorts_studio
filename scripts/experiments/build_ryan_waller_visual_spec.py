"""Ryan Waller — visual_spec.json builder invocation.

Uses scripts.orchestrator.api.visual_spec_builder.build() to produce
`output/ryan-waller/visual_spec.json` matching zodiac-killer baseline shape.

Inputs:
- output/ryan-waller/script.json (scripter output)
- .claude/memory/project_channel_preset_incidents.md (Phase 16-04)
- output/ryan-waller/narration_timing.json (116.04s duration)
- output/ryan-waller/sources/ (6 b-roll + 1 intro signature + 2 characters)

Output:
- output/ryan-waller/visual_spec.json
- output/ryan-waller/sources_manifest.json
- output/ryan-waller/blueprint.json (minimal)
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
    # Inputs
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    timing = json.loads(TIMING.read_text(encoding="utf-8"))
    audio_duration_s = timing["total_duration_s"]

    channel_preset = visual_spec_builder.load_channel_preset(PRESET_MEMORY)
    print(f"[SPEC] channel_preset loaded: {list(channel_preset.keys())}")

    # Blueprint — minimal with title_display for 사건기록부 visual overlay
    blueprint = {
        "niche_tag": "incidents",
        "category": "crime",
        "tone": "탐정 하오체 독백 + 조수 해요체 질문 (duo dialogue)",
        "target_emotion": "사법 불신 + 인간 공허",
        "scene_count": 6,
        "target_duration_sec": 116,
        "title_display": {
            "line1": "6시간 취조",
            "line2": "눈을 잃은 용의자",
            "accent_words": ["6시간", "눈"],
            "accent_color": "#FF2200",
        },
        "source_strategy": "gpt-image-2 medium quality b-roll + harvested signature + characters (Veo 신규 호출 0건)",
    }
    OUT_BLUEPRINT.write_text(
        json.dumps(blueprint, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SPEC] blueprint.json written")

    # Sources manifest — scene_sources in narrative order, intro mp4, no outro mp4 (OutroCard programmatic)
    scene_sources = [
        "broll_02_christmas_night.png",       # Conflict (crime scene)
        "broll_01_interrogation.png",         # Misdirection
        "broll_03_clock.png",                  # Buildup time
        "broll_04_fleeing.png",                # Buildup escape
        "broll_05_hospital.png",               # Reveal (hospital corridor, TBI aftermath)
        "broll_06_court_dismissed.png",       # Aftermath (dismissed)
    ]
    sources_manifest = {
        "scene_sources": scene_sources,
        "intro_signature": "intro_signature.mp4",
        "outro_signature": None,  # OutroCard programmatic per Plan 16-03 Option A
        "character_detective": "character_detective.png",
        "character_assistant": "character_assistant.png",
        "real_ratio": 1.0,  # 6/6 real gpt-image-2 (not Veo/I2V)
        "asset_source": "gpt-image-2 medium quality + harvested (session #33)",
    }
    OUT_SOURCES_MANIFEST.write_text(
        json.dumps(sources_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SPEC] sources_manifest.json written ({len(scene_sources)} scene_sources)")

    # Build visual_spec
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

    # Override audioSrc + character paths to match our actual layout
    spec_dict["audioSrc"] = f"{EPISODE_ID}/narration.mp3"
    spec_dict["characterLeftSrc"] = f"{EPISODE_ID}/character_assistant.png"
    spec_dict["characterRightSrc"] = f"{EPISODE_ID}/character_detective.png"

    OUT_VISUAL_SPEC.write_text(
        json.dumps(spec_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"✅ Visual spec built:")
    print(f"   blueprint       : {OUT_BLUEPRINT}")
    print(f"   sources_manifest: {OUT_SOURCES_MANIFEST}")
    print(f"   visual_spec     : {OUT_VISUAL_SPEC}")
    print(f"   durationInFrames: {spec_dict.get('durationInFrames')}")
    print(f"   clip count      : {len(spec_dict.get('clips', []))}")
    print(f"   transitionType  : {spec_dict.get('transitionType')}")
    print(f"   titleLine1/2    : '{spec_dict.get('titleLine1')}' / '{spec_dict.get('titleLine2')}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
