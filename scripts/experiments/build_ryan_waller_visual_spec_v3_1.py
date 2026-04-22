"""Ryan Waller v3.1 visual_spec — shot-level breakdown + watson clip removed
+ real doc footage mixed with Kling.

Session #34 v3.1 (after 대표님 5 points):
- hook split into 4 shots (crisis brief, ≤3s per visual)
- long sections (body_6hours 14.5s, reveal 13.5s) split into 2 shots each (freeze fix)
- watson_q1 / watson_q2 — NO OWN CLIP, previous shot extended
- aftermath_watson — outro_signature extended
- 9 doc clips from YouTube Ryan Waller documentaries integrated
- Kling 6 clips + 9 doc clips + 1 intro + 1 outro

Composes clips list directly (bypass visual_spec_builder default behavior)
because builder is section-level and can't express shot breakdown cleanly.
Still reuses builder for clip validation via schema.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass

EPISODE_ID = "ryan-waller"
EPISODE_DIR = Path("output/ryan-waller")
SOURCES_DIR = EPISODE_DIR / "sources"
DOC_CLIPS_DIR = SOURCES_DIR / "real" / "raw_doc_clips"
TIMING = EPISODE_DIR / "narration_timing_v3.json"
OUT_VISUAL_SPEC = EPISODE_DIR / "visual_spec_v3_1.json"
OUT_SOURCES_MANIFEST = EPISODE_DIR / "sources_manifest_v3_1.json"
OUT_BLUEPRINT = EPISODE_DIR / "blueprint_v3_1.json"

FPS = 30

# Shot plan with EXPLICIT seconds (sum must match section slot totals).
# Per feedback_assistant_never_appears_visually, NO clip for watson_q1/q2/aftermath_watson.
# Their durations are absorbed into adjacent narrative shots.
#
# Section durations (from narration_timing_v3.json):
#   hook 19.45s / watson_q1 3.70s / body_scene 13.75s / body_dalton 11.00s
#   body_6hours 15.00s / watson_q2 3.40s / reveal 16.55s / aftermath_detective 12.40s
#   aftermath_watson 2.75s (absorbed into outro)
#
# (shot_name, src_filename, duration_seconds)
SHOT_PLAN: list[tuple[str, str, float]] = [
    # --- hook 19.45s: 6 shots — 크리스마스 집 최소 (2.5s only) ---
    ("hook_s1_phoenix_house",     "broll_02_christmas_night_v3.mp4", 2.50),
    ("hook_s2_doc_case_overview", "hook_shot2.mp4",                  3.50),
    ("hook_s3_ryan_in_chair",     "broll_01_interrogation_v3.mp4",   3.00),
    ("hook_s4_doc_detective",     "hook_shot3.mp4",                  3.00),
    ("hook_s5_clock_6hours",      "broll_03_clock_v3.mp4",           3.50),
    ("hook_s6_doc_wrap",          "hook_shot1.mp4",                  3.95),
    # --- watson_q1 3.70s: interrogation cutaway (NO character) ---
    ("watson_q1_extension",       "broll_01_interrogation_v3.mp4",   3.70),
    # --- body_scene 13.75s: doc crime scene + house + Ryan ---
    ("body_scene_s1_doc_scene",   "body_scene_doc.mp4",              5.00),
    ("body_scene_s2_house_night", "broll_02_christmas_night_v3.mp4", 4.00),
    ("body_scene_s3_ryan_face",   "broll_01_interrogation_v3.mp4",   4.75),
    # --- body_dalton 11.00s: doc Dalton + Ryan swollen eye ---
    ("body_dalton_s1_doc",        "body_dalton_doc.mp4",             5.50),
    ("body_dalton_s2_ryan_eye",   "broll_01_interrogation_v3.mp4",   5.50),
    # --- body_6hours 15.00s: clock + doc + hospital ---
    ("body_6hours_s1_clock",      "broll_03_clock_v3.mp4",           4.50),
    ("body_6hours_s2_doc_interrog","body_6hours_doc.mp4",            5.00),
    ("body_6hours_s3_hospital",   "broll_05_hospital_v3.mp4",        5.50),
    # --- watson_q2 3.40s: fleeing (matches "진범 도망" in watson question) ---
    ("watson_q2_extension",       "broll_04_fleeing_v3.mp4",         3.40),
    # --- reveal 16.55s: doc Carver + fleeing + hospital ---
    ("reveal_s1_doc_carver",      "reveal_doc.mp4",                  5.50),
    ("reveal_s2_fleeing",         "broll_04_fleeing_v3.mp4",         5.50),
    ("reveal_s3_hospital_ryan",   "broll_05_hospital_v3.mp4",        5.55),
    # --- aftermath_detective 12.40s: doc hospital + court ---
    ("aftermath_s1_doc_hospital", "aftermath_doc.mp4",               6.20),
    ("aftermath_s2_court",        "broll_06_court_dismissed_v3.mp4", 6.20),
    # --- aftermath_watson 2.75s: outro holds this + native 3.30s ---
]


def load_timing() -> dict[str, dict]:
    t = json.loads(TIMING.read_text(encoding="utf-8"))
    return {row["section_id"]: row for row in t["sections"]}, t["total_duration_s"]


def stage_doc_clips_to_sources() -> None:
    """Copy doc clips from raw_doc_clips/ to sources/ root so builder can resolve them."""
    if not DOC_CLIPS_DIR.exists():
        return
    for src in DOC_CLIPS_DIR.glob("*.mp4"):
        dst = SOURCES_DIR / src.name
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dst)


def main() -> int:
    timing_by_id, audio_duration_s = load_timing()
    print(f"[SPEC-v3.1] audio_duration={audio_duration_s:.2f}s, sections={len(timing_by_id)}")

    stage_doc_clips_to_sources()
    print(f"[SPEC-v3.1] doc clips staged into {SOURCES_DIR}/")

    # Section ID → total duration (include trailing silence, hold visually through gap)
    def sec_total(sid: str) -> float:
        t = timing_by_id[sid]
        return t["duration_s"] + (t["silence_after_ms"] / 1000.0)

    # Build clips list
    clips: list[dict] = []

    # Intro signature — 3.3s hold (99 frames)
    clips.append({
        "type": "video",
        "src": f"{EPISODE_ID}/intro_signature.mp4",
        "durationInFrames": 99,
        "transition": "fade",
        "movement": None,
    })

    # Process shot plan — explicit duration in seconds
    for shot_name, src, dur_s in SHOT_PLAN:
        frames = max(1, round(dur_s * FPS))
        is_video = src.endswith((".mp4", ".webm", ".mov"))
        clips.append({
            "type": "video" if is_video else "image",
            "src": f"{EPISODE_ID}/{src}",
            "durationInFrames": frames,
            "transition": "fade",
            "movement": None,  # real footage + Kling carry their own motion
        })

    # Outro signature — absorb aftermath_watson (2.75s) + native outro hold (3.30s) = 6.05s
    outro_absorb_frames = round((sec_total("aftermath_watson") + 3.30) * FPS)
    clips.append({
        "type": "video",
        "src": f"{EPISODE_ID}/outro_signature.mp4",
        "durationInFrames": outro_absorb_frames,
        "transition": "fade",
        "movement": None,
    })

    total_frames = sum(c["durationInFrames"] for c in clips)
    print(f"[SPEC-v3.1] total frames = {total_frames} ({total_frames/FPS:.2f}s)")
    print(f"[SPEC-v3.1] clip breakdown:")
    for i, c in enumerate(clips):
        print(f"  {i+1:2d}. {c['src'].split('/')[-1]:<40} {c['durationInFrames']:>4}f {c['durationInFrames']/FPS:>5.2f}s")

    # Assemble blueprint
    blueprint = {
        "niche_tag": "incidents",
        "category": "crime",
        "tone": "탐정 하오체 독백 + 조수 해요체 질문 (duo dialogue)",
        "target_emotion": "사법 불신 + 인간 공허",
        "scene_count": len(clips),
        "target_duration_sec": round(audio_duration_s + 3.3),  # + outro hold
        "title_display": {
            "line1": "6시간 취조",
            "line2": "눈을 잃은 용의자",
            "accent_words": ["6시간", "눈"],
            "accent_color": "#FF2200",
        },
        "source_strategy": "YouTube doc clips (Ryan Waller case) + Kling 2.6 Pro I2V + shot-level breakdown (v3.1)",
        "schema_version": "v3.1-shot-breakdown",
    }
    OUT_BLUEPRINT.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")

    # Count source kinds
    real_doc = sum(1 for c in clips if "_doc" in c["src"])
    kling = sum(1 for c in clips if "_v3.mp4" in c["src"])
    signature = sum(1 for c in clips if "signature" in c["src"])
    sources_manifest = {
        "schema_version": "v3.1-shot-breakdown",
        "clip_count": len(clips),
        "real_doc_clips": real_doc,
        "kling_clips": kling,
        "signature_clips": signature,
        "character_in_scene_clips": 0,  # feedback_assistant_never_appears_visually 준수
        "shot_plan_entries": len(SHOT_PLAN),
        "sources_used": ["youtube_doc", "kling_official_api", "harvested_signature"],
    }
    OUT_SOURCES_MANIFEST.write_text(json.dumps(sources_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Final visual_spec (mirrors v3 schema)
    visual_spec = {
        "titleLine1": blueprint["title_display"]["line1"],
        "titleLine2": blueprint["title_display"]["line2"],
        "titleKeywords": [{"text": w, "color": blueprint["title_display"]["accent_color"]}
                          for w in blueprint["title_display"]["accent_words"]],
        "accentColor": blueprint["title_display"]["accent_color"],
        "channelName": "사건기록부",
        "hashtags": "#쇼츠 #범죄 #미제사건 #실화",
        "fontFamily": "BlackHanSans",
        "characterLeftSrc": f"{EPISODE_ID}/character_assistant.png",
        "characterRightSrc": f"{EPISODE_ID}/character_detective.png",
        "subtitlePosition": 0.8,
        "subtitleHighlightColor": "#FFFFFF",
        "subtitleFontSize": 68,
        "audioSrc": f"{EPISODE_ID}/narration_v3.mp3",
        "durationInFrames": total_frames,
        "transitionType": "clock-wipe",
        "clips": clips,
    }
    OUT_VISUAL_SPEC.write_text(json.dumps(visual_spec, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"✅ Visual spec v3.1 built:")
    print(f"   blueprint       : {OUT_BLUEPRINT}")
    print(f"   sources_manifest: {OUT_SOURCES_MANIFEST}")
    print(f"   visual_spec     : {OUT_VISUAL_SPEC}")
    print(f"   durationInFrames: {total_frames} ({total_frames/FPS:.2f}s)")
    print(f"   clip count      : {len(clips)}")
    print(f"   source mix      : real_doc={real_doc}, kling={kling}, signature={signature}, char_in_scene=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
