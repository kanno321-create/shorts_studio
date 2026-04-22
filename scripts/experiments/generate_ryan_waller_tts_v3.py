"""Ryan Waller v3 TTS — section-level narration paragraph calls (not sentence).

Session #34 v3 redesign: v2 invoked Typecast 20 times (one per sentence) with
400-700ms silence between each → robotic "read one word at a time" result.
v3 invokes once per section (9 calls total) with 0-700ms silence only at
section boundaries. Matches reference zodiac-killer structure
(C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/script.json).

Reads: output/ryan-waller/script_v3.json  (sections[].narration)
Writes:
- outputs/typecast/ryan-waller-v3/section_NN.mp3
- output/ryan-waller/narration_v3.mp3  (concat, final)
- output/ryan-waller/narration_timing_v3.json  (section-level AudioSegment manifest)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.api.typecast import TypecastAdapter  # noqa: E402

MORGAN_VOICE_ID = "tc_6256118ea1103af69f0a87ec"  # incidents-narrator, ssfm-v30
SCRIPT_PATH = Path("output/ryan-waller/script_v3.json")
OUTPUT_DIR = Path("outputs/typecast/ryan-waller-v3")
FINAL_NARRATION = Path("output/ryan-waller/narration_v3.mp3")
TIMING_MANIFEST = Path("output/ryan-waller/narration_timing_v3.json")


def load_dotenv_minimal() -> None:
    if os.environ.get("TYPECAST_API_KEY"):
        return
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


# Map channel-incidents emotion names → Typecast ssfm-v30 enum
TYPECAST_EMOTION_MAP = {
    "normal": "normal",
    "tonedown": "tonedown",
    "tense": "tense",
    "whisper": "whisper",
    "sad": "sad",
    "urgent": "urgent",
    "toneup": "toneup",
    "empathetic": "urgent",  # fallback (SDK no empathetic slot)
    "happy": "happy",
}


def build_scenes_from_sections(script: dict) -> list[dict]:
    """One Typecast scene per section — narration field goes in verbatim."""
    scenes: list[dict] = []
    for i, section in enumerate(script["sections"], start=1):
        emotion_in = section.get("emotion", "normal")
        tc_emotion = TYPECAST_EMOTION_MAP.get(emotion_in, "normal")
        scenes.append({
            "scene_id": i,
            "text": section["narration"],
            "emotion_style": tc_emotion,
            "voice_id": MORGAN_VOICE_ID,
            "model": "ssfm-v30",
            "_section_id": section["section_id"],
            "_speaker": section.get("speaker_id", "narrator"),
            "_emotion_original": emotion_in,
            "_silence_after_ms": int(section.get("silence_after_ms", 400)),
        })
    return scenes


def concat_with_section_silence(
    segments: list, output_path: Path, silence_gaps_ms: list[int]
) -> float:
    """Concat MP3 segments with per-section silence gaps via ffmpeg concat demuxer.
    Returns total duration seconds.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(prefix="ryan_tts_v3_concat_"))

    concat_list = tmpdir / "concat.txt"
    lines: list[str] = []
    silence_cache: dict[int, Path] = {}

    for i, seg in enumerate(segments):
        seg_path = Path(seg.path).resolve()
        lines.append(f"file '{seg_path.as_posix()}'")
        if i < len(segments) - 1:
            gap_ms = silence_gaps_ms[i] if i < len(silence_gaps_ms) else 400
            if gap_ms <= 0:
                continue
            if gap_ms not in silence_cache:
                sil_path = tmpdir / f"sil_{gap_ms}ms.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-t", f"{gap_ms / 1000:.3f}",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(sil_path),
                ], check=True, capture_output=True)
                silence_cache[gap_ms] = sil_path
            lines.append(f"file '{silence_cache[gap_ms].as_posix()}'")

    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-ar", "48000", "-ac", "2",
        str(output_path),
    ], check=True, capture_output=True)

    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def main() -> int:
    load_dotenv_minimal()
    if not os.environ.get("TYPECAST_API_KEY"):
        raise EnvironmentError("TYPECAST_API_KEY not set (check .env)")
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError(f"Script v3 not found: {SCRIPT_PATH}")

    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    scenes = build_scenes_from_sections(script)
    print(f"[TTS-v3] {len(scenes)} SECTIONS (was 20 sentences in v2)")
    print(f"[TTS-v3] Output dir: {OUTPUT_DIR}")
    for s in scenes:
        print(f"  · section {s['_section_id']:<22} "
              f"({s['_speaker']:<9} {s['emotion_style']:<8} "
              f"chars={len(s['text']):>3} gap={s['_silence_after_ms']}ms)")

    adapter = TypecastAdapter(output_dir=OUTPUT_DIR)
    adapter_scenes = [
        {k: v for k, v in s.items() if not k.startswith("_")}
        for s in scenes
    ]

    print(f"[TTS-v3] Invoking Typecast Morgan ({len(adapter_scenes)} calls)...")
    segments = adapter.generate(adapter_scenes)
    print(f"[TTS-v3] Generated {len(segments)} segments")

    silence_gaps_ms = [s["_silence_after_ms"] for s in scenes]
    print(f"[TTS-v3] Concatenating via ffmpeg with section silence gaps...")
    total = concat_with_section_silence(segments, FINAL_NARRATION, silence_gaps_ms)
    print(f"[TTS-v3] narration_v3.mp3 duration: {total:.2f}s")

    timing = {
        "narration_mp3_path": str(FINAL_NARRATION),
        "total_duration_s": total,
        "section_count": len(segments),
        "voice_id_primary": MORGAN_VOICE_ID,
        "schema_version": "v3-section-paragraph",
        "sections": [
            {
                "scene_id": scenes[i]["scene_id"],
                "section_id": scenes[i]["_section_id"],
                "speaker": scenes[i]["_speaker"],
                "emotion_original": scenes[i]["_emotion_original"],
                "emotion_typecast": scenes[i]["emotion_style"],
                "text": scenes[i]["text"],
                "char_count": len(scenes[i]["text"]),
                "start_s": segments[i].start,
                "end_s": segments[i].end,
                "duration_s": segments[i].duration,
                "silence_after_ms": scenes[i]["_silence_after_ms"],
                "mp3_path": str(segments[i].path),
            }
            for i in range(len(segments))
        ],
    }
    TIMING_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    TIMING_MANIFEST.write_text(
        json.dumps(timing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[TTS-v3] timing manifest: {TIMING_MANIFEST}")

    print()
    print("✅ TTS v3 complete:")
    print(f"   narration_v3.mp3  : {FINAL_NARRATION} ({total:.2f}s)")
    print(f"   timing manifest   : {TIMING_MANIFEST}")
    print(f"   per-section mp3s  : {OUTPUT_DIR} ({len(segments)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
