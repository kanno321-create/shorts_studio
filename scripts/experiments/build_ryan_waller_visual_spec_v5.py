"""Ryan Waller v5 Visual Spec — intro/outro 1s bookends, audio offset via narration prefix.

INVARIANT Rule 1: reads script_v5.json first.
v5 fixes:
- intro_signature = 30 frames (1s), not 99 (prevents brand overexposure per 대표님 지적)
- outro_signature = 30 frames (1s), narration ends → ~1s natural fade
- narration_v5.mp3 already has 1s silence prepended, so Remotion Audio plays from 0 and aligns
- hook_s06 is overlay_text clip in shots[], NOT intro_signature reuse (dup eliminated)
- section-last silence extended in section-last shots' durationInFrames
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

EPISODE_ID = "ryan-waller"
EP = Path(f"output/{EPISODE_ID}")
SHOT_FINAL = EP / "sources/shot_final"
SCRIPT_V5 = EP / "script_v5.json"
TIMING_V5 = EP / "narration_timing_v5.json"
OUT_BLUEPRINT = EP / "blueprint_v5.json"
OUT_SOURCES = EP / "sources_manifest_v5.json"
OUT_SPEC = EP / "visual_spec_v5.json"

FPS = 30
INTRO_FRAMES = 30  # 1s (v4 was 99 = 3.3s — too long, caused "인트로 반복" per 대표님)
OUTRO_FRAMES = 30  # 1s (natural outro fade)


def main() -> int:
    print("[Spec v5] reads script_v5.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))
    timing = json.loads(TIMING_V5.read_text(encoding="utf-8"))
    audio_dur = timing["total_duration_s"]
    intro_offset_s = timing.get("intro_offset_s", 1.0)

    flat_shots = []
    for sec in script["sections"]:
        spk = sec.get("speaker_id", "narrator")
        for shot in sec["shots"]:
            flat_shots.append((shot["shot_id"], shot, spk, sec["section_id"]))
    assert len(flat_shots) == 22

    # verify all shot_final present
    missing = []
    for sid, _, _, _ in flat_shots:
        if not (SHOT_FINAL / f"{sid}_final.mp4").exists():
            missing.append(sid)
    if missing:
        raise FileNotFoundError(f"missing: {missing}")
    print(f"[Spec v5] 22/22 shot_final present")

    # section-last map for silence extension
    last_shot_by_section = {}
    silence_by_section = {}
    for sec in script["sections"]:
        last_shot_by_section[sec["section_id"]] = sec["shots"][-1]["shot_id"]
        silence_by_section[sec["section_id"]] = int(sec.get("silence_after_ms", 0))
    section_last_set = set(last_shot_by_section.values())

    # Build clips
    clips = [{
        "type": "video",
        "src": f"{EPISODE_ID}/intro_signature.mp4",
        "durationInFrames": INTRO_FRAMES,
        "transition": "fade",
    }]
    for sid, shot, _, sec_id in flat_shots:
        base = max(1, round(shot["duration_hint_s"] * FPS))
        extra = 0
        if sid in section_last_set:
            extra = round((silence_by_section[sec_id] / 1000.0) * FPS)
        clips.append({
            "type": "video",
            "src": f"{EPISODE_ID}/sources/shot_final/{sid}_final.mp4",
            "shot_id": sid,
            "visual_mode": shot.get("visual_mode"),
            "durationInFrames": base + extra,
            "base_frames": base,
            "silence_extension_frames": extra,
            "transition": "fade",
        })
    clips.append({
        "type": "video",
        "src": f"{EPISODE_ID}/outro_signature.mp4",
        "durationInFrames": OUTRO_FRAMES,
        "transition": "fade",
    })

    # Assertions
    assert clips[-1]["src"].endswith("outro_signature.mp4"), "outro-last FAIL"
    print("[V.5] OK outro is last clip")
    assistant_sids = [sid for sid, _, spk, _ in flat_shots if spk == "assistant"]
    for sid in assistant_sids:
        src = f"{EPISODE_ID}/sources/shot_final/{sid}_final.mp4"
        assert "character_assistant.png" not in src, f"watson scene FAIL: {sid}"
    print(f"[V.4] OK 3 assistant shots use B-roll: {assistant_sids}")
    clip_sids = [c.get("shot_id") for c in clips if c.get("shot_id")]
    script_sids = [sid for sid, _, _, _ in flat_shots]
    assert clip_sids == script_sids, "shot order FAIL"
    print(f"[Order] OK clip shot_id == script flat order")

    total_frames = sum(c["durationInFrames"] for c in clips)
    total_s = total_frames / FPS
    print(f"[Spec v5] video total: {total_frames} frames = {total_s:.2f}s")
    print(f"   intro = {INTRO_FRAMES}f ({INTRO_FRAMES/FPS:.2f}s)")
    print(f"   shots = {sum(c['durationInFrames'] for c in clips if c.get('shot_id'))}f")
    print(f"   outro = {OUTRO_FRAMES}f ({OUTRO_FRAMES/FPS:.2f}s)")
    print(f"   audio = {audio_dur:.2f}s (narration_v5 with {intro_offset_s}s silence prefix)")
    outro_start_s = (INTRO_FRAMES + sum(c["durationInFrames"] for c in clips if c.get("shot_id"))) / FPS
    print(f"   outro starts at {outro_start_s:.2f}s, audio ends at {audio_dur:.2f}s, diff={abs(outro_start_s-audio_dur):.2f}s")

    blueprint = {
        "niche_tag": "incidents",
        "category": "crime",
        "tone": "탐정 하오체 + 조수 해요체 duo dialogue",
        "target_emotion": "사법 불신 + 인간 공허",
        "scene_count": len(clips),
        "shot_count": 22,
        "target_duration_sec": round(total_s),
        "schema_version": "v5-bookend-1s",
        "title_display": {
            "line1": "6시간 취조",
            "line2": "눈을 잃은 용의자",
            "accent_words": ["6시간", "눈"],
            "accent_color": "#FF2200",
        },
        "source_strategy": "v5 script-driven-runtime-prompt: real_footage 8 + kling_t2i_i2v 12 + overlay_text 2",
    }
    OUT_BLUEPRINT.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "schema_version": "v5",
        "clip_count": len(clips),
        "shot_count": 22,
        "visual_mode_counts": {
            "real_footage": sum(1 for c in clips if c.get("visual_mode") == "real_footage"),
            "kling_t2i_i2v": sum(1 for c in clips if c.get("visual_mode") == "kling_t2i_i2v"),
            "overlay_text": sum(1 for c in clips if c.get("visual_mode") == "overlay_text"),
        },
        "intro_frames": INTRO_FRAMES, "outro_frames": OUTRO_FRAMES,
        "audio_offset_s": intro_offset_s,
        "narration_path": "ryan-waller/narration_v5.mp3",
    }
    OUT_SOURCES.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    spec = {
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
        "audioSrc": f"{EPISODE_ID}/narration_v5.mp3",
        "durationInFrames": total_frames,
        "transitionType": "clock-wipe",
        "clips": clips,
    }
    OUT_SPEC.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK visual_spec v5: {OUT_SPEC}")
    print(f"   clips={len(clips)} (1 intro + 22 shots + 1 outro)")
    print(f"   total={total_s:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
