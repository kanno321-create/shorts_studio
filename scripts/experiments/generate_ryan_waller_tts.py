"""Ryan Waller narration TTS — Typecast Morgan voice + emotion per sentence.

Session #33 first production smoke. Drives Typecast SDK via
`scripts.orchestrator.api.typecast.TypecastAdapter` to generate per-sentence
MP3 files from `output/ryan-waller/script.json`, then concatenates into
`output/ryan-waller/narration.mp3` with channel-incidents pause discipline
(comma 300-400ms, terminal 400-700ms).

Voice strategy:
- All sentences: Morgan (incidents-narrator), voice_id=tc_6256118ea1103af69f0a87ec
- Watson (assistant) sentences: emotion_style="urgent" for pacing contrast
- Detective: emotion per sentence (normal/tonedown/tense/whisper/sad)

Output:
- outputs/typecast/ryan-waller/scene_NNN.mp3 (20 files)
- output/ryan-waller/narration.mp3 (concat, final)
- output/ryan-waller/narration_timing.json (AudioSegment manifest)

Usage:
  python scripts/experiments/generate_ryan_waller_tts.py
"""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.api.typecast import TypecastAdapter  # noqa: E402

MORGAN_VOICE_ID = "tc_6256118ea1103af69f0a87ec"  # incidents-narrator, ssfm-v30
SCRIPT_PATH = Path("output/ryan-waller/script.json")
OUTPUT_DIR = Path("outputs/typecast/ryan-waller")
FINAL_NARRATION = Path("output/ryan-waller/narration.mp3")
TIMING_MANIFEST = Path("output/ryan-waller/narration_timing.json")


def load_dotenv_minimal() -> None:
    """Load TYPECAST_API_KEY from .env if not already set."""
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


def build_scenes_from_script(script: dict) -> list[dict]:
    """Flatten script.sections[].sentences[] into Typecast scene list."""
    scenes: list[dict] = []
    scene_id = 1
    for section in script["sections"]:
        for sentence in section["sentences"]:
            speaker = sentence["speaker_id"]
            emotion = sentence.get("emotion", "normal")
            # Map channel-incidents emotions → Typecast SDK emotions
            # Morgan supports: normal, tonedown, tense, whisper, sad, urgent, toneup
            if speaker == "assistant":
                # Watson uses urgent for question contrast
                tc_emotion = "urgent" if emotion in ("tense", "urgent") else emotion
            else:
                tc_emotion = emotion

            scenes.append({
                "scene_id": scene_id,
                "text": sentence["text"],
                "emotion_style": tc_emotion,
                "voice_id": MORGAN_VOICE_ID,
                "model": "ssfm-v30",
                "_speaker": speaker,
                "_section_id": section["id"],
                "_silence_after_ms": sentence.get("silence_after_ms", 400),
            })
            scene_id += 1
    return scenes


def concat_with_timing(
    segments: list, output_path: Path, silence_gaps_ms: list[int]
) -> float:
    """Concat MP3s via ffmpeg concat demuxer, inserting per-sentence silence.

    Returns total duration seconds.
    """
    import tempfile

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(prefix="ryan_tts_concat_"))

    # Pre-generate silence MP3s of varying durations
    concat_list = tmpdir / "concat.txt"
    lines: list[str] = []
    silence_cache: dict[int, Path] = {}

    for i, seg in enumerate(segments):
        seg_path = Path(seg.path).resolve()
        lines.append(f"file '{seg_path.as_posix()}'")
        # Append silence after this segment (except the last)
        if i < len(segments) - 1:
            gap_ms = silence_gaps_ms[i] if i < len(silence_gaps_ms) else 400
            if gap_ms not in silence_cache:
                sil_path = tmpdir / f"sil_{gap_ms}ms.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=channel_layout=stereo:sample_rate=48000",
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

    # Probe duration
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
        raise FileNotFoundError(f"Script not found: {SCRIPT_PATH}")

    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    scenes = build_scenes_from_script(script)
    print(f"[TTS] {len(scenes)} scenes generated from script.json")
    print(f"[TTS] Output dir: {OUTPUT_DIR}")

    adapter = TypecastAdapter(output_dir=OUTPUT_DIR)

    # Strip internal fields before passing to adapter
    adapter_scenes = [
        {k: v for k, v in s.items() if not k.startswith("_")}
        for s in scenes
    ]

    print(f"[TTS] Invoking Typecast API (Morgan voice, {len(adapter_scenes)} calls)...")
    segments = adapter.generate(adapter_scenes)
    print(f"[TTS] Generated {len(segments)} segments")

    # Collect per-segment silence gaps (from script metadata)
    silence_gaps_ms = [s["_silence_after_ms"] for s in scenes]

    print(f"[TTS] Concatenating via ffmpeg with silence gaps...")
    total_duration = concat_with_timing(segments, FINAL_NARRATION, silence_gaps_ms)
    print(f"[TTS] narration.mp3 duration: {total_duration:.2f}s")

    # Write timing manifest (for subtitle-producer consumption)
    timing_manifest = {
        "narration_mp3_path": str(FINAL_NARRATION),
        "total_duration_s": total_duration,
        "scene_count": len(segments),
        "voice_id_primary": MORGAN_VOICE_ID,
        "sentences": [
            {
                "scene_id": scenes[i]["scene_id"],
                "text": scenes[i]["text"],
                "speaker": scenes[i]["_speaker"],
                "section": scenes[i]["_section_id"],
                "emotion": scenes[i]["emotion_style"],
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
        json.dumps(timing_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[TTS] timing manifest: {TIMING_MANIFEST}")

    print()
    print(f"✅ TTS complete:")
    print(f"   narration.mp3  : {FINAL_NARRATION} ({total_duration:.2f}s)")
    print(f"   timing manifest: {TIMING_MANIFEST}")
    print(f"   per-scene mp3s : {OUTPUT_DIR} ({len(segments)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
