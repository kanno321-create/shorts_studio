"""Ryan Waller v3 subtitles — 2-4 word chunks (reference zodiac-killer 184-cue style).

Session #34 v3 redesign: v2 produced sentence-level cues (20-30 chars each),
Remotion auto-wrapped them to 2 lines → unreadable at 68pt font width. v3
chunks each section's narration into 2-4 word groups (≤12 chars guard) and
distributes start/end timestamps proportionally across that section's TTS
segment (from narration_timing_v3.json).

Reference SSOT: C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/subtitles_remotion.json
 (184 cues, avg 2-4 words per cue, ~10 chars).

Reads:
- output/ryan-waller/script_v3.json  (sections[].narration)
- output/ryan-waller/narration_timing_v3.json  (section start/end ms)
Writes:
- output/ryan-waller/subtitles_remotion_v3.json  (word-cue schema)
- output/ryan-waller/subtitles_remotion_v3.ass
- output/ryan-waller/subtitles_remotion_v3.srt
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

SCRIPT_PATH = Path("output/ryan-waller/script_v3.json")
TIMING_PATH = Path("output/ryan-waller/narration_timing_v3.json")
OUT_JSON = Path("output/ryan-waller/subtitles_remotion_v3.json")
OUT_ASS = Path("output/ryan-waller/subtitles_remotion_v3.ass")
OUT_SRT = Path("output/ryan-waller/subtitles_remotion_v3.srt")

MAX_CHARS_PER_CUE = 12
MAX_WORDS_PER_CUE = 4
MIN_WORDS_PER_CUE = 2


def chunk_words(words: list[str]) -> list[list[str]]:
    """Group words into 2-4 per cue, ≤12 chars total (including spaces).

    Strategy: greedy pack forward — add word if adding it keeps us ≤ MAX_CHARS
    AND we haven't reached MAX_WORDS. Flush when adding would exceed either.
    Final group shorter than MIN is merged into previous.
    """
    chunks: list[list[str]] = []
    current: list[str] = []

    def char_len(ws: list[str]) -> int:
        return sum(len(w) for w in ws) + max(0, len(ws) - 1)

    for w in words:
        if not current:
            current = [w]
            continue
        trial = current + [w]
        if len(trial) > MAX_WORDS_PER_CUE or char_len(trial) > MAX_CHARS_PER_CUE:
            chunks.append(current)
            current = [w]
        else:
            current = trial
    if current:
        chunks.append(current)

    # Merge tail under-min into previous (if any)
    if len(chunks) >= 2 and len(chunks[-1]) < MIN_WORDS_PER_CUE:
        merged = chunks[-2] + chunks[-1]
        if char_len(merged) <= MAX_CHARS_PER_CUE + 4:  # allow slight overflow on tail
            chunks[-2] = merged
            chunks.pop()
    return chunks


def format_srt_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_ass_timecode(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        cs = 0
        s += 1
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def main() -> int:
    if not TIMING_PATH.exists():
        raise FileNotFoundError(f"Missing timing manifest: {TIMING_PATH}")
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError(f"Missing script: {SCRIPT_PATH}")

    timing = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))

    # Build section_id -> timing row map
    timing_by_id = {row["section_id"]: row for row in timing["sections"]}

    cues: list[dict] = []
    for section in script["sections"]:
        sid = section["section_id"]
        speaker = section.get("speaker_id", "narrator")
        emotion = section.get("emotion", "normal")
        narration: str = section["narration"]
        t = timing_by_id.get(sid)
        if t is None:
            print(f"[SUB-v3] WARN: no timing for section {sid}; skipping")
            continue
        t_start: float = t["start_s"]
        t_end: float = t["end_s"]
        duration: float = max(t["duration_s"], 0.01)

        words = narration.split()
        groups = chunk_words(words)

        # Proportional time distribution by sum of character lengths
        weights = [sum(len(w) for w in g) + max(0, len(g) - 1) for g in groups]
        total_w = sum(weights) or 1
        cursor = t_start
        for g, w_ in zip(groups, weights):
            cue_dur = duration * (w_ / total_w)
            cue_start = cursor
            cue_end = min(cursor + cue_dur, t_end)
            cues.append({
                "start_s": round(cue_start, 3),
                "end_s": round(cue_end, 3),
                "text": " ".join(g),
                "words": g,
                "speaker": speaker,
                "section": sid,
                "emotion": emotion,
            })
            cursor = cue_end

    # Output JSON cue list (wraps in `cues` key to mirror v2 schema)
    OUT_JSON.write_text(
        json.dumps({"cues": cues, "schema_version": "v3-2to4-words"},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # SRT
    srt_lines: list[str] = []
    for i, c in enumerate(cues, 1):
        srt_lines.append(str(i))
        srt_lines.append(f"{format_srt_timecode(c['start_s'])} --> {format_srt_timecode(c['end_s'])}")
        srt_lines.append(c["text"])
        srt_lines.append("")
    OUT_SRT.write_text("\n".join(srt_lines), encoding="utf-8")

    # ASS
    ass_header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 2\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,"
        " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline,"
        " Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Narrator,Black Han Sans,68,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,2,2,60,60,900,1\n"
        "Style: Watson,Black Han Sans,68,&H00FFD166,&H000000FF,&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,2,2,60,60,900,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    ass_body: list[str] = []
    for c in cues:
        style = "Watson" if c["speaker"] == "assistant" else "Narrator"
        ass_body.append(
            f"Dialogue: 0,{format_ass_timecode(c['start_s'])},"
            f"{format_ass_timecode(c['end_s'])},{style},,0,0,0,,{c['text']}"
        )
    OUT_ASS.write_text(ass_header + "\n".join(ass_body) + "\n", encoding="utf-8")

    # Report
    avg_words = sum(len(c["words"]) for c in cues) / max(1, len(cues))
    avg_chars = sum(len(c["text"]) for c in cues) / max(1, len(cues))
    print("✅ Subtitle v3 complete (2-4 word chunks, reference-style):")
    print(f"  JSON : {OUT_JSON} ({len(cues)} cues)")
    print(f"  ASS  : {OUT_ASS}")
    print(f"  SRT  : {OUT_SRT}")
    print(f"  avg words/cue: {avg_words:.1f} (target 2-4)")
    print(f"  avg chars/cue: {avg_chars:.1f} (target ≤12)")
    print(f"  total duration: {max(c['end_s'] for c in cues):.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
