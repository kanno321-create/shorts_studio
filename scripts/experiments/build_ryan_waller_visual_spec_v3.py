"""Ryan Waller v3 visual_spec — per-section duration mapping + real footage priority.

Session #34 v3: v2 used equal per-scene distribution. v3 maps each section
to its actual TTS duration (from narration_timing_v3.json) so clips match
what the narrator is saying at that moment. Each section gets 1 clip
picked in this order:

  1. Real footage from manifest_v3.json  (YouTube / Wikimedia downloaded)
  2. Kling 2.6 Pro 10s clip (broll_XX_*_v3.mp4, v3 iteration) if matching anchor exists
  3. Character PNG (watson turns — short static w/ Ken Burns)
  4. Fallback: first available sibling b-roll

Reads:
- output/ryan-waller/script_v3.json
- output/ryan-waller/narration_timing_v3.json
- output/ryan-waller/sources/real/manifest_v3.json (optional — missing OK)
Writes:
- output/ryan-waller/visual_spec_v3.json
- output/ryan-waller/sources_manifest_v3.json
- output/ryan-waller/blueprint_v3.json
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
REAL_RAW_DIR = SOURCES_DIR / "real" / "raw"
SCRIPT = EPISODE_DIR / "script_v3.json"
TIMING = EPISODE_DIR / "narration_timing_v3.json"
REAL_MANIFEST = SOURCES_DIR / "real" / "manifest_v3.json"
PRESET_MEMORY = Path(".claude/memory/project_channel_preset_incidents.md")
OUT_BLUEPRINT = EPISODE_DIR / "blueprint_v3.json"
OUT_SOURCES_MANIFEST = EPISODE_DIR / "sources_manifest_v3.json"
OUT_VISUAL_SPEC = EPISODE_DIR / "visual_spec_v3.json"

# Section → fallback Kling 2.6 Pro clip (v3 iteration, anchor name mapping). watson+cta use character.
SECTION_FALLBACK: dict[str, str] = {
    "hook": "broll_02_christmas_night_v3.mp4",
    "watson_q1": "character_assistant.png",
    "body_scene": "broll_02_christmas_night_v3.mp4",
    "body_dalton": "broll_01_interrogation_v3.mp4",
    "body_6hours": "broll_03_clock_v3.mp4",
    "watson_q2": "character_assistant.png",
    "reveal": "broll_04_fleeing_v3.mp4",
    "aftermath_detective": "broll_06_court_dismissed_v3.mp4",
    "aftermath_watson": "character_assistant.png",
}

# Fallback priority when primary not available (same extension bucket)
SIBLING_FALLBACKS = [
    "broll_05_hospital_v3.mp4",
    "broll_01_interrogation_v3.mp4",
    "broll_02_christmas_night_v3.mp4",
    "broll_06_court_dismissed_v3.mp4",
    "broll_04_fleeing_v3.mp4",
    "broll_03_clock_v3.mp4",
]


USABLE_REAL_EXTS = (".mp4", ".webm", ".mov", ".jpg", ".jpeg", ".png")


def _pick_clip_for_section(
    section_id: str,
    real_pick_by_section: dict[str, str],
) -> tuple[str, str]:
    """Return (filename, source_kind) where source_kind ∈ {real, kling, character, fallback}.

    Real footage only accepted if extension in USABLE_REAL_EXTS — rejects
    Wikimedia PDF/DJVU/bin false-positives (commons search returns books too).
    """
    # 1. Real footage wins — but only if usable video/image format
    if section_id in real_pick_by_section:
        real_path = Path(real_pick_by_section[section_id])
        ext = real_path.suffix.lower()
        if ext in USABLE_REAL_EXTS:
            target = SOURCES_DIR / real_path.name
            if not target.exists() and real_path.exists():
                import shutil as _sh
                _sh.copy2(real_path, target)
            if target.exists():
                return (target.name, "real")
        else:
            print(f"    [real-reject] {section_id}: {real_path.name} ext={ext!r} not usable")

    # 2. Primary Kling fallback for this section
    primary = SECTION_FALLBACK.get(section_id, "")
    if primary:
        primary_path = SOURCES_DIR / primary
        if primary_path.exists():
            source_kind = "character" if primary.endswith(".png") else "kling"
            return (primary, source_kind)

    # 3. Sibling Kling mp4 (pick first that exists)
    for sib in SIBLING_FALLBACKS:
        if (SOURCES_DIR / sib).exists():
            return (sib, "fallback-kling")

    # 4. Character PNG as ultimate
    if (SOURCES_DIR / "character_assistant.png").exists():
        return ("character_assistant.png", "fallback-character")

    raise RuntimeError(f"No clip available for section {section_id}")


def main() -> int:
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    timing = json.loads(TIMING.read_text(encoding="utf-8"))
    audio_duration_s = timing["total_duration_s"]
    timing_by_id = {row["section_id"]: row for row in timing["sections"]}

    real_pick_by_section: dict[str, str] = {}
    if REAL_MANIFEST.exists():
        rm = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
        for s in rm.get("sections", []):
            picks = s.get("picks", [])
            if picks:
                local = picks[0].get("local_path")
                if local and Path(local).exists():
                    real_pick_by_section[s["section_id"]] = local
        print(f"[SPEC-v3] real footage covers {len(real_pick_by_section)}/{len(script['sections'])} sections")
    else:
        print(f"[SPEC-v3] no real manifest — all sections will use Kling/character fallback")

    channel_preset = visual_spec_builder.load_channel_preset(PRESET_MEMORY)
    print(f"[SPEC-v3] channel_preset loaded: {list(channel_preset.keys())}")

    blueprint = {
        "niche_tag": "incidents",
        "category": "crime",
        "tone": "탐정 하오체 독백 + 조수 해요체 질문 (duo dialogue)",
        "target_emotion": "사법 불신 + 인간 공허",
        "scene_count": len(script["sections"]),
        "target_duration_sec": round(audio_duration_s),
        "title_display": {
            "line1": "6시간 취조",
            "line2": "눈을 잃은 용의자",
            "accent_words": ["6시간", "눈"],
            "accent_color": "#FF2200",
        },
        "source_strategy": "real footage (multi-source YouTube/Wikimedia) + Kling 2.6 Pro I2V 10s fallback",
        "schema_version": "v3-section-paragraph",
    }
    OUT_BLUEPRINT.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SPEC-v3] blueprint_v3.json written")

    # Build scene_sources in section order
    scene_sources: list[str] = []
    source_kinds: list[str] = []
    for section in script["sections"]:
        sid = section["section_id"]
        filename, kind = _pick_clip_for_section(sid, real_pick_by_section)
        scene_sources.append(filename)
        source_kinds.append(kind)
        print(f"  · {sid:<22} → {filename} [{kind}]")

    real_count = sum(1 for k in source_kinds if k == "real")
    kling_count = sum(1 for k in source_kinds if k.endswith("kling"))
    char_count = sum(1 for k in source_kinds if k.endswith("character"))
    real_ratio = real_count / max(1, len(source_kinds))

    sources_manifest = {
        "scene_sources": scene_sources,
        "source_kinds": source_kinds,
        "intro_signature": "intro_signature.mp4",
        "outro_signature": "outro_signature.mp4",  # copied from shorts_naberal (zodiac-killer reference)
        "character_detective": "character_detective.png",
        "character_assistant": "character_assistant.png",
        "real_ratio": round(real_ratio, 2),
        "real_count": real_count,
        "kling_count": kling_count,
        "character_count": char_count,
        "asset_source": f"real/multi-source ({real_count}) + Kling 10s v3 ({kling_count}) + character ({char_count})",
    }
    OUT_SOURCES_MANIFEST.write_text(json.dumps(sources_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SPEC-v3] sources_manifest_v3.json written — real_ratio={real_ratio:.2f}")

    # Invoke builder (equal distribution baseline)
    spec = visual_spec_builder.build(
        blueprint=blueprint,
        script=script,
        channel_preset=channel_preset,
        sources_manifest=sources_manifest,
        audio_duration_s=audio_duration_s,
        episode_id=EPISODE_ID,
    )
    spec_dict = spec.model_dump(by_alias=True)

    spec_dict["audioSrc"] = f"{EPISODE_ID}/narration_v3.mp3"
    spec_dict["characterLeftSrc"] = f"{EPISODE_ID}/character_assistant.png"
    spec_dict["characterRightSrc"] = f"{EPISODE_ID}/character_detective.png"

    # Post-process: re-distribute durationInFrames per section actual TTS duration
    # (builder uses equal split; v3 needs tight script-audio sync).
    # intro + body sections + outro (outro added by builder from sources_manifest).
    FPS = 30
    intro_frames = 0
    outro_frames = 0
    body_clips_idx: list[int] = []
    for idx, clip in enumerate(spec_dict.get("clips", [])):
        src = clip.get("src", "")
        if "intro_signature.mp4" in src:
            intro_frames = clip.get("durationInFrames", 0)
        elif "outro_signature.mp4" in src:
            outro_frames = clip.get("durationInFrames", 0)
        else:
            body_clips_idx.append(idx)

    # Section order matches scene_sources order (same as builder iteration)
    if len(body_clips_idx) == len(script["sections"]):
        # total audio frames + outro frames hold beyond audio ending
        total_body_frames = round(audio_duration_s * FPS) - intro_frames
        section_durations = []
        for sec in script["sections"]:
            tid = timing_by_id.get(sec["section_id"])
            if tid is None:
                section_durations.append(0.0)
                continue
            # Include trailing silence in the clip (visually hold frame)
            sec_dur = tid["duration_s"] + (tid["silence_after_ms"] / 1000.0)
            section_durations.append(sec_dur)
        total_sec = sum(section_durations)
        scale = total_body_frames / (total_sec * FPS) if total_sec > 0 else 1.0
        running = 0
        for i, clip_idx in enumerate(body_clips_idx):
            frames = max(1, round(section_durations[i] * FPS * scale))
            running += frames
            spec_dict["clips"][clip_idx]["durationInFrames"] = frames
        # Adjust last body clip to absorb rounding delta
        delta = total_body_frames - running
        if delta != 0 and body_clips_idx:
            last_idx = body_clips_idx[-1]
            new_frames = max(1, spec_dict["clips"][last_idx]["durationInFrames"] + delta)
            spec_dict["clips"][last_idx]["durationInFrames"] = new_frames

        # Update total durationInFrames = intro + body + outro
        spec_dict["durationInFrames"] = intro_frames + sum(
            spec_dict["clips"][i]["durationInFrames"] for i in body_clips_idx
        ) + outro_frames
        print(f"[SPEC-v3] Redistributed clip frames to section durations "
              f"(intro={intro_frames}, body={total_body_frames}, outro={outro_frames}, "
              f"total={spec_dict['durationInFrames']})")
    else:
        print(f"[SPEC-v3] WARN: body clip count ({len(body_clips_idx)}) ≠ section count "
              f"({len(script['sections'])}) — leaving equal distribution "
              f"(intro={intro_frames}, outro={outro_frames})")

    # Suppress Ken Burns movement on Kling mp4 clips (character PNG keeps movement)
    for clip in spec_dict.get("clips", []):
        if clip.get("type") == "video" and clip.get("src", "").endswith(".mp4"):
            src = clip.get("src", "")
            if "broll" in src and "_v3" in src and clip.get("movement") is not None:
                clip["movement"] = None

    OUT_VISUAL_SPEC.write_text(json.dumps(spec_dict, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"✅ Visual spec v3 built:")
    print(f"   blueprint       : {OUT_BLUEPRINT}")
    print(f"   sources_manifest: {OUT_SOURCES_MANIFEST}")
    print(f"   visual_spec     : {OUT_VISUAL_SPEC}")
    print(f"   durationInFrames: {spec_dict.get('durationInFrames')} @ {FPS}fps "
          f"= {spec_dict.get('durationInFrames', 0) / FPS:.2f}s")
    print(f"   clip count      : {len(spec_dict.get('clips', []))}")
    print(f"   real ratio      : {real_ratio:.0%}")
    print(f"   audioSrc        : {spec_dict.get('audioSrc')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
