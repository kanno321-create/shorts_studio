"""Ryan Waller v4 TTS — Morgan (narrator) + Guri (assistant) + v4 fixes.

Session #35 v4 (INVARIANT Rule 1 — reads script_v4.json first):
- v3.2 TTS 패턴 기반 (generate_ryan_waller_tts_v3_2.py)
- v4 변경점:
  1. Input = script_v4.json (narration_full field per section)
  2. `reveal` emotion "tonedown_replaces_whisper" → preset="tonedown" + intensity=0.9
     (feedback_whisper_volume_normalize — v3.2 지적 #7 텐션 급락 방지)
  3. concat 후 `ffmpeg loudnorm=I=-16:LRA=11:TP=-1.5` 후처리 (섹션 경계 볼륨 정규화)
  4. narration_timing_v4.json 에 **shot-level timing** 추가 (char 비례 분배)
  5. 표준 output "[Agent TTS v4] reads script_v4 ..." — INVARIANT Rule 1 증거
"""
from __future__ import annotations

import builtins as _builtins
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass

os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _p(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _builtins.print(*args, **kwargs)


MORGAN_VOICE_ID = "tc_6256118ea1103af69f0a87ec"
GURI_VOICE_ID = "tc_6359e7ea258d1b6dc3abe6e6"

SCRIPT_V4_PATH = Path("output/ryan-waller/script_v4.json")
OUTPUT_DIR = Path("outputs/typecast/ryan-waller-v4")
FINAL_NARRATION_RAW = Path("output/ryan-waller/narration_v4_raw.mp3")
FINAL_NARRATION = Path("output/ryan-waller/narration_v4.mp3")
TIMING_MANIFEST = Path("output/ryan-waller/narration_timing_v4.json")

# v4 section_emotion → (preset, intensity) — whisper 제거, tonedown 기본
NARRATOR_EMOTION_V4 = {
    "tense":                        ("tonedown", 0.9),
    "tonedown":                     ("tonedown", 0.9),
    "tonedown_replaces_whisper":    ("tonedown", 0.9),
    "sad":                          ("sad",      1.0),
    "urgent":                       ("angry",    1.0),
    "normal":                       ("normal",   1.0),
}
ASSISTANT_EMOTION_V4 = {
    "urgent":   ("angry",  1.0),
    "tense":    ("angry",  1.0),
    "normal":   ("normal", 1.0),
    "sad":      ("sad",    1.0),
    "happy":    ("happy",  1.0),
}


def load_dotenv_minimal() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def synthesize_section(section: dict, idx: int) -> Path:
    """Typecast SDK direct call with PresetPrompt. v4 = whisper banned."""
    from typecast import Typecast
    from typecast.models import Output, TTSRequest, PresetPrompt

    speaker = section.get("speaker_id", "narrator")
    emotion_section = section.get("emotion_section", "tonedown")

    if speaker == "assistant":
        voice_id = GURI_VOICE_ID
        model = "ssfm-v21"
        preset, intensity = ASSISTANT_EMOTION_V4.get(emotion_section, ("normal", 1.0))
    else:
        voice_id = MORGAN_VOICE_ID
        model = "ssfm-v30"
        preset, intensity = NARRATOR_EMOTION_V4.get(emotion_section, ("tonedown", 0.9))

    text = section["narration_full"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"section_{idx:02d}_{section['section_id']}.mp3"

    client = Typecast(api_key=os.environ["TYPECAST_API_KEY"])
    req = TTSRequest(
        voice_id=voice_id,
        text=text,
        model=model,
        language="kor",
        prompt=PresetPrompt(emotion_preset=preset, emotion_intensity=intensity),
        output=Output(audio_format="mp3"),
    )
    resp = client.text_to_speech(request=req)
    out_path.write_bytes(resp.audio_data)

    _p(f"  [{idx:02d} {section['section_id']:<20s} {speaker:<9s} "
       f"voice={voice_id[:15]}... preset={preset:<8s} intensity={intensity}] chars={len(text)}")
    return out_path


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def concat_with_gaps(mp3_paths: list[Path], silence_ms_list: list[int],
                     output_path: Path) -> float:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="ryan_tts_v4_"))
    concat_list = tmp / "concat.txt"
    lines: list[str] = []
    silence_cache: dict[int, Path] = {}
    for i, p in enumerate(mp3_paths):
        lines.append(f"file '{Path(p).resolve().as_posix()}'")
        if i < len(mp3_paths) - 1:
            gap_ms = silence_ms_list[i] if i < len(silence_ms_list) else 400
            if gap_ms <= 0:
                continue
            if gap_ms not in silence_cache:
                sp = tmp / f"sil_{gap_ms}ms.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i",
                    "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-t", f"{gap_ms/1000:.3f}",
                    "-c:a", "libmp3lame", "-b:a", "192k",
                    str(sp),
                ], check=True, capture_output=True)
                silence_cache[gap_ms] = sp
            lines.append(f"file '{silence_cache[gap_ms].resolve().as_posix()}'")
    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-ar", "48000", "-ac", "2",
        str(output_path),
    ], check=True, capture_output=True)
    return probe_duration(output_path)


def loudnorm(input_path: Path, output_path: Path) -> float:
    """Apply EBU R128 loudnorm — I=-16 (broadcast), LRA=11, TP=-1.5 (digital headroom)."""
    subprocess.run([
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-ar", "48000", "-ac", "2",
        str(output_path),
    ], check=True, capture_output=True)
    return probe_duration(output_path)


def distribute_shot_timing(section: dict, section_start: float,
                           section_duration: float) -> list[dict]:
    """Char-count 비례 분배로 shots[] 의 start_s / end_s 계산."""
    shots = section["shots"]
    total_chars = sum(len(s["text"]) for s in shots)
    if total_chars == 0:
        return []
    rows = []
    running = section_start
    for shot in shots:
        w = len(shot["text"]) / total_chars
        d = section_duration * w
        rows.append({
            "shot_id": shot["shot_id"],
            "section_id": section["section_id"],
            "speaker": section.get("speaker_id", "narrator"),
            "text": shot["text"],
            "char_count": len(shot["text"]),
            "start_s": round(running, 3),
            "end_s": round(running + d, 3),
            "duration_s": round(d, 3),
        })
        running += d
    return rows


def main() -> int:
    load_dotenv_minimal()
    if not os.environ.get("TYPECAST_API_KEY"):
        raise EnvironmentError("TYPECAST_API_KEY missing from .env")

    # INVARIANT Rule 1 — reads script_v4.json first
    _p(f"[Agent TTS v4] reads script_v4.json (INVARIANT Rule 1)")
    script_v4 = json.loads(SCRIPT_V4_PATH.read_text(encoding="utf-8"))
    sections = script_v4["sections"]
    total_shots = sum(len(s["shots"]) for s in sections)
    _p(f"[Agent TTS v4] sections={len(sections)} shots={total_shots}")

    mp3_paths: list[Path] = []
    section_timing: list[dict] = []
    silence_gaps_ms: list[int] = []

    # Synthesize each section
    for i, sec in enumerate(sections, 1):
        out = synthesize_section(sec, i)
        d = probe_duration(out)
        section_timing.append({
            "scene_id": i,
            "section_id": sec["section_id"],
            "speaker": sec.get("speaker_id", "narrator"),
            "emotion_section": sec.get("emotion_section", "tonedown"),
            "voice_id": GURI_VOICE_ID if sec.get("speaker_id") == "assistant" else MORGAN_VOICE_ID,
            "narration": sec["narration_full"],
            "char_count": len(sec["narration_full"]),
            "duration_s": d,
            "silence_after_ms": sec.get("silence_after_ms", 400),
            "mp3_path": str(out),
        })
        if i < len(sections):
            silence_gaps_ms.append(int(sec.get("silence_after_ms", 400)))
        mp3_paths.append(out)

    # Concat with silences → raw; then loudnorm → final
    _p(f"[Agent TTS v4] concatenating {len(mp3_paths)} sections with silences...")
    raw_total = concat_with_gaps(mp3_paths, silence_gaps_ms, FINAL_NARRATION_RAW)
    _p(f"[Agent TTS v4] raw concat duration: {raw_total:.2f}s")

    _p(f"[Agent TTS v4] applying loudnorm I=-16 LRA=11 TP=-1.5 (v4 fix for whisper drop)...")
    total = loudnorm(FINAL_NARRATION_RAW, FINAL_NARRATION)
    _p(f"[Agent TTS v4] narration_v4.mp3 final duration: {total:.2f}s")

    # Populate section start_s / end_s on final timeline
    running = 0.0
    for i, row in enumerate(section_timing):
        row["start_s"] = round(running, 3)
        row["end_s"] = round(running + row["duration_s"], 3)
        running += row["duration_s"]
        if i < len(section_timing) - 1:
            running += row["silence_after_ms"] / 1000.0

    # Distribute shot timing within each section
    shot_timing: list[dict] = []
    for sec, row in zip(sections, section_timing):
        shot_timing.extend(
            distribute_shot_timing(sec, row["start_s"], row["duration_s"])
        )

    TIMING_MANIFEST.write_text(json.dumps({
        "schema_version": "v4-shot-level-timing",
        "narration_mp3_path": str(FINAL_NARRATION),
        "narration_raw_mp3_path": str(FINAL_NARRATION_RAW),
        "total_duration_s": total,
        "section_count": len(sections),
        "shot_count": total_shots,
        "voice_ids": {"narrator": MORGAN_VOICE_ID, "assistant": GURI_VOICE_ID},
        "loudnorm_applied": True,
        "loudnorm_spec": "I=-16 LRA=11 TP=-1.5",
        "whisper_replaced_with_tonedown": True,
        "sections": section_timing,
        "shots": shot_timing,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"[Agent TTS v4] timing manifest: {TIMING_MANIFEST}")

    _p()
    _p("OK TTS v4 complete:")
    _p(f"   narration_v4.mp3   : {FINAL_NARRATION} ({total:.2f}s, loudnormed)")
    _p(f"   timing manifest    : {TIMING_MANIFEST}")
    _p(f"   shots timed        : {total_shots}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
