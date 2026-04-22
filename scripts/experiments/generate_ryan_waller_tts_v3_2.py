"""Ryan Waller v3.2 TTS — Morgan (narrator) + Guri (assistant) + emotion prompt.

Session #34 v3.2 (대표님 지시):
1. Assistant voice = **Guri** (tc_6359e7ea258d1b6dc3abe6e6, ssfm-v21)
   v2/v3 는 Morgan 으로 통일했는데 reference voice_pool 은 Guri
2. Emotion 강화 — Typecast TTSRequest.emotion 필드는 존재 안 함 (v2/v3 가 silently dropped).
   실제 감정 제어는 `prompt` 필드 (style/emotion instruction). 섹션별 한국어 스타일
   prompt 를 추가해 narrator (sad/whisper/tense) & assistant (urgent) 반영.

Directly invokes Typecast SDK (bypass TypecastAdapter which didn't pass prompt).

Output: output/ryan-waller/narration_v3_2.mp3 + narration_timing_v3_2.json
"""
from __future__ import annotations

import builtins as _builtins
import json
import os
import subprocess
import sys
import tempfile
import time
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


MORGAN_VOICE_ID = "tc_6256118ea1103af69f0a87ec"      # narrator — ssfm-v30 full emotion set
GURI_VOICE_ID = "tc_6359e7ea258d1b6dc3abe6e6"        # assistant — ssfm-v21 (angry/happy/normal/sad)

SCRIPT_PATH = Path("output/ryan-waller/script_v3.json")
OUTPUT_DIR = Path("outputs/typecast/ryan-waller-v3_2")
FINAL_NARRATION = Path("output/ryan-waller/narration_v3_2.mp3")
TIMING_MANIFEST = Path("output/ryan-waller/narration_timing_v3_2.json")

# Section emotion → (voice_id, model, emotion, style_prompt_kr)
# style prompt = Korean natural description. Typecast prompt field accepts natural-language
# style guidance and blends with emotion selection.
NARRATOR_EMOTION_PROMPT = {
    "tense":    ("tonedown", "긴장감과 무게감으로, 느리고 또렷하게 말합니다."),
    "tonedown": ("tonedown", "차분하고 묵직한 톤으로, 사실을 담담히 전달합니다."),
    "whisper":  ("whisper",  "속삭이듯 낮게, 진실을 드러내는 무거운 톤입니다."),
    "sad":      ("sad",      "슬픔과 허무 속에서, 천천히 말끝을 흐립니다."),
    "urgent":   ("angry",    "긴박한 호흡으로 강하게 강조합니다."),
    "normal":   ("normal",   "중립적이고 또렷한 톤입니다."),
}
# Guri ssfm-v21 only supports angry/happy/normal/sad — map urgent→angry, tense→angry, etc.
ASSISTANT_EMOTION_PROMPT = {
    "urgent":   ("angry", "놀라움과 의문 섞인 격한 질문 어조로 말합니다."),
    "tense":    ("angry", "긴장된 의문의 어조로 묻습니다."),
    "empathetic":("normal", "친근하고 궁금증을 유발하는 부드러운 어조로 마무리합니다."),
    "normal":   ("normal", "또렷한 질문 어조로 말합니다."),
    "sad":      ("sad",   "애잔한 어조로 말합니다."),
    "happy":    ("happy", "밝은 호기심으로 말합니다."),
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
    """Call Typecast SDK directly with PresetPrompt(emotion_preset, emotion_intensity)."""
    from typecast import Typecast
    from typecast.models import Output, TTSRequest, PresetPrompt

    speaker = section.get("speaker_id", "narrator")
    emotion_in = section.get("emotion", "normal")

    if speaker == "assistant":
        voice_id = GURI_VOICE_ID
        model = "ssfm-v21"
        emotion_tag, _ = ASSISTANT_EMOTION_PROMPT.get(emotion_in, ("normal", ""))
        intensity = 1.0  # Guri v21 — tested baseline; increase per section if needed
    else:
        voice_id = MORGAN_VOICE_ID
        model = "ssfm-v30"
        emotion_tag, _ = NARRATOR_EMOTION_PROMPT.get(emotion_in, ("normal", ""))
        # 대표님 "감정 더 넣어서" — boost narrator intensity per emotion category
        intensity = {
            "whisper": 1.0,
            "sad":     1.0,
            "tonedown":0.9,
            "angry":   1.0,
            "toneup":  1.0,
            "happy":   1.0,
            "normal":  1.0,
        }.get(emotion_tag, 1.0)

    text = section["narration"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"section_{idx:02d}_{speaker}.mp3"

    client = Typecast(api_key=os.environ["TYPECAST_API_KEY"])
    req = TTSRequest(
        voice_id=voice_id,
        text=text,
        model=model,
        language="kor",
        prompt=PresetPrompt(
            emotion_preset=emotion_tag,
            emotion_intensity=intensity,
        ),
        output=Output(audio_format="mp3"),
    )
    resp = client.text_to_speech(request=req)
    out_path.write_bytes(resp.audio_data)

    _p(f"  [{idx:02d} {speaker:<9} voice={voice_id[:15]}… model={model:<9} "
       f"preset={emotion_tag:<8} intensity={intensity}] chars={len(text):>3}")
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
    tmp = Path(tempfile.mkdtemp(prefix="ryan_tts_v3_2_"))
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


def main() -> int:
    load_dotenv_minimal()
    if not os.environ.get("TYPECAST_API_KEY"):
        raise EnvironmentError("TYPECAST_API_KEY missing")

    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    sections = script["sections"]
    _p(f"[TTS-v3.2] {len(sections)} sections — Morgan (narrator) + Guri (assistant)")

    mp3_paths: list[Path] = []
    timing_rows: list[dict] = []
    running = 0.0
    silence_gaps_ms: list[int] = []

    for i, sec in enumerate(sections, 1):
        out = synthesize_section(sec, i)
        d = probe_duration(out)
        timing_rows.append({
            "scene_id": i,
            "section_id": sec["section_id"],
            "speaker": sec.get("speaker_id", "narrator"),
            "emotion_original": sec.get("emotion", "normal"),
            "voice_id": GURI_VOICE_ID if sec.get("speaker_id") == "assistant" else MORGAN_VOICE_ID,
            "text": sec["narration"],
            "char_count": len(sec["narration"]),
            "start_s": running,
            "end_s": running + d,
            "duration_s": d,
            "silence_after_ms": sec.get("silence_after_ms", 400),
            "mp3_path": str(out),
        })
        running += d
        gap = sec.get("silence_after_ms", 400)
        if i < len(sections):
            silence_gaps_ms.append(int(gap))
            running += gap / 1000.0
        mp3_paths.append(out)

    _p(f"[TTS-v3.2] concatenating with section silences...")
    total = concat_with_gaps(mp3_paths, silence_gaps_ms, FINAL_NARRATION)
    _p(f"[TTS-v3.2] narration_v3_2.mp3 duration: {total:.2f}s")

    # Recompute actual timing from probed file (start/end relative to final mp3)
    actual_start = 0.0
    for i, row in enumerate(timing_rows):
        row["start_s"] = actual_start
        row["end_s"] = actual_start + row["duration_s"]
        actual_start += row["duration_s"]
        if i < len(timing_rows) - 1:
            actual_start += row["silence_after_ms"] / 1000.0

    TIMING_MANIFEST.write_text(json.dumps({
        "narration_mp3_path": str(FINAL_NARRATION),
        "total_duration_s": total,
        "section_count": len(sections),
        "voice_ids": {"narrator": MORGAN_VOICE_ID, "assistant": GURI_VOICE_ID},
        "schema_version": "v3.2-dual-voice-emotion-prompt",
        "sections": timing_rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"[TTS-v3.2] timing manifest: {TIMING_MANIFEST}")

    _p()
    _p("✅ TTS v3.2 complete:")
    _p(f"   narration_v3_2.mp3 : {FINAL_NARRATION} ({total:.2f}s)")
    _p(f"   timing manifest    : {TIMING_MANIFEST}")
    _p(f"   narrator = Morgan (ssfm-v30), assistant = Guri (ssfm-v21)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
