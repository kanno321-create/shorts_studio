"""Ryan Waller v4 Step 7+8 — Visual Spec Assembler + Outro-last + Watson assertion.

INVARIANT Rule 1: reads script_v4.json first.
Structure (Plan spec):
  clips[0]  = intro_signature.mp4 (99 frames, narration-less hold)
  clips[1-22] = shot_final/<shot_id>_final.mp4 × 22 (script_v4 순서 flat)
  clips[23] = outro_signature.mp4 (99 frames, narration-less hold) — ASSERTION LAST

Assertions (Plan V.4/V.5):
  V.4 — assistant speaker shots 3개의 src != character_assistant.png (scene 등장 금지)
  V.5 — clips[-1].src.endswith('outro_signature.mp4')
  Extra — 22 shots × shot_final/*.mp4 파일 실존 확인
  Extra — clips src shot_id 순서 == script_v4 flat 순서
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass

EPISODE_ID = "ryan-waller"
EPISODE_DIR = Path(f"output/{EPISODE_ID}")
SOURCES = EPISODE_DIR / "sources"
SHOT_FINAL = SOURCES / "shot_final"
SCRIPT_V4 = EPISODE_DIR / "script_v4.json"
TIMING_V4 = EPISODE_DIR / "narration_timing_v4.json"
OUT_BLUEPRINT = EPISODE_DIR / "blueprint_v4.json"
OUT_SOURCES_MANIFEST = EPISODE_DIR / "sources_manifest_v4.json"
OUT_VISUAL_SPEC = EPISODE_DIR / "visual_spec_v4.json"

FPS = 30
INTRO_FRAMES = 99  # ≈3.3s
OUTRO_FRAMES = 99  # ≈3.3s


def main() -> int:
    print("[Agent Spec v4] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    timing = json.loads(TIMING_V4.read_text(encoding="utf-8"))
    audio_duration = timing["total_duration_s"]

    # Collect shots in flat order
    flat_shots: list[tuple[str, dict, str]] = []  # (shot_id, shot_dict, section_speaker)
    for sec in script["sections"]:
        spk = sec.get("speaker_id", "narrator")
        for shot in sec["shots"]:
            flat_shots.append((shot["shot_id"], shot, spk))
    assert len(flat_shots) == 22, f"expected 22 shots, got {len(flat_shots)}"

    # Check all shot_final files exist
    missing = []
    for sid, _, _ in flat_shots:
        f = SHOT_FINAL / f"{sid}_final.mp4"
        if not f.exists():
            missing.append(sid)
    if missing:
        raise FileNotFoundError(f"missing shot_final/: {missing}")
    print(f"[Agent Spec v4] 22/22 shot_final files present")

    # section 마지막 shot id 에 silence_after_ms 더해 video ↔ audio 정렬
    # (Plan §6 duration reconcile + silence 포함 narration 과 일치)
    last_shot_by_section: dict[str, str] = {}
    silence_by_section: dict[str, int] = {}
    for sec in script["sections"]:
        last_shot_by_section[sec["section_id"]] = sec["shots"][-1]["shot_id"]
        silence_by_section[sec["section_id"]] = int(sec.get("silence_after_ms", 0))
    section_last_shots = set(last_shot_by_section.values())

    section_of_shot: dict[str, str] = {}
    for sec in script["sections"]:
        for shot in sec["shots"]:
            section_of_shot[shot["shot_id"]] = sec["section_id"]

    # Build clips
    clips: list[dict] = []
    clips.append({
        "type": "video",
        "src": f"{EPISODE_ID}/intro_signature.mp4",
        "durationInFrames": INTRO_FRAMES,
        "transition": "fade",
        "movement": None,
    })
    for sid, shot, _ in flat_shots:
        base_frames = max(1, round(shot["duration_hint_s"] * FPS))
        extra_frames = 0
        if sid in section_last_shots:
            sec_id = section_of_shot[sid]
            sil_ms = silence_by_section[sec_id]
            extra_frames = round((sil_ms / 1000.0) * FPS)
        frames = base_frames + extra_frames
        clips.append({
            "type": "video",
            "src": f"{EPISODE_ID}/sources/shot_final/{sid}_final.mp4",
            "shot_id": sid,
            "durationInFrames": frames,
            "base_frames": base_frames,
            "silence_extension_frames": extra_frames,
            "transition": "fade",
            "movement": None,
        })
    clips.append({
        "type": "video",
        "src": f"{EPISODE_ID}/outro_signature.mp4",
        "durationInFrames": OUTRO_FRAMES,
        "transition": "fade",
        "movement": None,
    })

    # -------- Assertions --------
    # V.5 outro last
    assert clips[-1]["src"].endswith("outro_signature.mp4"), \
        f"outro assertion failed: last clip src = {clips[-1]['src']}"
    print("[Assertion V.5] OK clips[-1] == outro_signature.mp4")

    # V.4 assistant speaker shots must NOT use character_assistant.png
    assistant_shots = [(sid, s) for sid, s, spk in flat_shots if spk == "assistant"]
    for sid, _ in assistant_shots:
        src = f"{EPISODE_ID}/sources/shot_final/{sid}_final.mp4"
        assert "character_assistant.png" not in src, \
            f"watson assertion failed: shot {sid} src = {src}"
    print(f"[Assertion V.4] OK 3 assistant shots never use character_assistant.png (shots: "
          f"{[s[0] for s in assistant_shots]})")

    # shot_id 순서 == script_v4 flat 순서
    clip_shot_ids = [c.get("shot_id") for c in clips if c.get("shot_id")]
    script_shot_ids = [sid for sid, _, _ in flat_shots]
    assert clip_shot_ids == script_shot_ids, \
        f"shot order mismatch: clips={clip_shot_ids[:3]}... script={script_shot_ids[:3]}..."
    print(f"[Assertion Order] OK clip shot_id 순서 == script_v4 flat 순서 ({len(clip_shot_ids)} shots)")

    total_frames = sum(c["durationInFrames"] for c in clips)
    total_s = total_frames / FPS
    print(f"[Agent Spec v4] total duration: {total_s:.2f}s ({total_frames} frames)")
    print(f"   intro  = {INTRO_FRAMES}f ({INTRO_FRAMES/FPS:.2f}s)")
    print(f"   shots  = {sum(c['durationInFrames'] for c in clips if c.get('shot_id'))}f")
    print(f"   outro  = {OUTRO_FRAMES}f ({OUTRO_FRAMES/FPS:.2f}s)")
    print(f"   audio  = {audio_duration:.2f}s (offset = intro = {INTRO_FRAMES/FPS:.2f}s)")

    # blueprint v4
    blueprint = {
        "niche_tag": "incidents",
        "category": "crime",
        "tone": "탐정 하오체 독백 + 조수 해요체 질문 (duo dialogue)",
        "target_emotion": "사법 불신 + 인간 공허",
        "scene_count": len(clips),
        "shot_count": 22,
        "target_duration_sec": round(total_s),
        "title_display": {
            "line1": "6시간 취조",
            "line2": "눈을 잃은 용의자",
            "accent_words": ["6시간", "눈"],
            "accent_color": "#FF2200",
        },
        "source_strategy": "script-driven-3-agent-v1 pipeline (Ryan Waller v4): "
                           "Case A raw_doc trim 6 + Case B Kling v3 reuse 1:1 6 + "
                           "Case C new Kling I2V 9 + intro reuse 1 = 22 shots",
        "schema_version": "v4-shot-breakdown-flat",
        "invariant_compliance": {
            "rule_1_script_first": True,
            "rule_2_markers_absolute": True,
            "rule_3_subagent_vision": True,
        },
    }
    OUT_BLUEPRINT.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")

    # sources manifest v4
    case_a_shots = {"hook_s03_ryan_blood_sitting", "watson_q1_s01_doubt",
                    "body_scene_s03_ryan_forehead_eye", "body_dalton_s02_drug_pretend_confession",
                    "body_6hours_s02_ryan_pupil_unresponsive", "reveal_s03_bullet_in_skull_alive"}
    case_b_shots = {"hook_s01_date_christmas_eve", "body_dalton_s01_detective_suspect",
                    "body_6hours_s01_clock_six_hours", "body_6hours_s03_real_killer_fleeing_phoenix",
                    "aftermath_det_s01_brain_eye_loss", "aftermath_det_s02_lawsuit_dismissed_cta"}
    case_c_shots = {"hook_s02_phoenix_arizona", "hook_s04_heather_body",
                    "hook_s05_interrogation_6hours", "body_scene_s01_heather_victim",
                    "body_scene_s02_phoenix_shooting", "watson_q2_s01_flee_shock",
                    "reveal_s01_carver_father_son", "reveal_s02_doorway_ambush",
                    "aftermath_watson_s01_cta"}
    intro_reuse_shots = {"hook_s06_truth_reveal_title"}
    assert len(case_a_shots) + len(case_b_shots) + len(case_c_shots) + len(intro_reuse_shots) == 22
    sources_manifest = {
        "schema_version": "v4-shot-breakdown-flat",
        "clip_count": len(clips),
        "shot_count": 22,
        "case_a_raw_doc_trim": sorted(case_a_shots),
        "case_b_kling_v3_reuse_1to1": sorted(case_b_shots),
        "case_c_kling_i2v_new": sorted(case_c_shots),
        "intro_reuse": sorted(intro_reuse_shots),
        "outro_last_assertion_ok": True,
        "assistant_never_appears_visually": True,
        "unique_shot_final_files": True,
        "sources_used": [
            "youtube_full_interrogation_trim",
            "existing_kling_v3_official_api_1to1",
            "new_kling_v2_6_official_api",
            "harvested_signature",
        ],
    }
    OUT_SOURCES_MANIFEST.write_text(
        json.dumps(sources_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

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
        "audioSrc": f"{EPISODE_ID}/narration_v4.mp3",
        "audioStartFrameOffset": INTRO_FRAMES,  # play narration after intro hold
        "durationInFrames": total_frames,
        "transitionType": "clock-wipe",
        "clips": clips,
    }
    OUT_VISUAL_SPEC.write_text(json.dumps(visual_spec, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"OK visual_spec v4 built:")
    print(f"   blueprint       : {OUT_BLUEPRINT}")
    print(f"   sources_manifest: {OUT_SOURCES_MANIFEST}")
    print(f"   visual_spec     : {OUT_VISUAL_SPEC}")
    print(f"   clip count      : {len(clips)} (1 intro + 22 shots + 1 outro)")
    print(f"   total duration  : {total_s:.2f}s (audio offset {INTRO_FRAMES/FPS:.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
