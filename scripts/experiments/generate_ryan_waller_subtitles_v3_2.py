"""Ryan Waller v3.1 subtitles — semantic-chunk (조사 병합) vs v3 mechanical split.

Session #34 v3.1 (대표님 "의미있는 구절끼리 한자막에 넣고해야된다"):
- Korean postposition (가/이/을/를/의/에/로/와/과) bound to previous word → merge
- Adjective/quantifier bound to following noun → merge
- Proper noun + location bigrams merged
- Number + unit ("여섯 시간") merged
- Max per cue: 5 단어 / 14 자 (v3 는 4/12 — relaxed for meaning priority)

Reads: script_v3.json + narration_timing_v3.json
Writes: subtitles_remotion_v3_1.{json,ass,srt}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass

SCRIPT_PATH = Path("output/ryan-waller/script_v3.json")
TIMING_PATH = Path("output/ryan-waller/narration_timing_v3_2.json")
OUT_JSON = Path("output/ryan-waller/subtitles_remotion_v3_2.json")
OUT_ASS = Path("output/ryan-waller/subtitles_remotion_v3_2.ass")
OUT_SRT = Path("output/ryan-waller/subtitles_remotion_v3_2.srt")

MAX_CHARS_PER_CUE = 14
MAX_WORDS_PER_CUE = 5

# Particles that, when word ends with any of these, should bind to the PREVIOUS word
# (Korean: previous word + particle = 같은 cue)
# In practice, particles are already attached (붙여쓰기 Korean).
# So we focus on: "current word shouldn't stand alone if it's a bound particle form"

# Modifiers that bind to the FOLLOWING word
PREPOSE_MODIFIERS = {
    "그", "이", "저", "그들", "이들", "저들", "여러",
    "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열",
    "스물", "서른", "마흔", "쉰", "백", "천",
    "많은", "적은", "큰", "작은", "긴", "짧은", "첫", "마지막", "모든", "각",
    "그의", "이의", "그녀의",
}

# Words that should always join previous (sentence enders, conjunctions)
APPEND_TO_PREV = {
    "그리고", "하지만", "그러나", "그래서",  # conjunction at sentence start — actually starts new cue, skip
}

# Unit suffixes that bind after a number
TIME_UNITS = re.compile(r"^(시간|분|초|년|월|일|주|세기|살|번|건|개|명|회|차|시|번째)$")


def char_len_with_spaces(ws: list[str]) -> int:
    return sum(len(w) for w in ws) + max(0, len(ws) - 1)


def is_pure_number(w: str) -> bool:
    # Korean number words or digits
    if re.match(r"^\d+\.?\d*$", w):
        return True
    if w in {"한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉",
             "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든",
             "아흔", "백", "천", "만", "억", "열한", "열두", "열여덟", "스물한"}:
        return True
    if re.match(r"^\d+[.,]?\d*(년|월|일|시|분|초|개|명|건|살|번|회|차|시간|분간|주|주년|원|달러|그램|킬로|미터)$", w):
        return True
    return False


def chunk_semantic(words: list[str]) -> list[list[str]]:
    """Merge particles/modifiers/numbers into adjacent words, then cap ≤14 chars / ≤5 words."""
    # Step 1: pre-merge — modifiers bind forward, numbers bind to units forward
    merged: list[str] = []
    i = 0
    while i < len(words):
        w = words[i]
        # Case: pure number followed by a unit word
        if is_pure_number(w) and i + 1 < len(words):
            nxt = words[i + 1]
            # strip terminal punctuation for unit check
            core = re.sub(r"[.,!?]+$", "", nxt)
            if TIME_UNITS.match(core):
                merged.append(f"{w} {nxt}")
                i += 2
                continue
        # Case: modifier binds forward
        if w in PREPOSE_MODIFIERS and i + 1 < len(words):
            merged.append(f"{w} {words[i+1]}")
            i += 2
            continue
        merged.append(w)
        i += 1

    # Step 2: greedy pack ≤5 merged units / ≤14 chars
    chunks: list[list[str]] = []
    current: list[str] = []
    for m in merged:
        trial = current + [m]
        if len(trial) > MAX_WORDS_PER_CUE or char_len_with_spaces(trial) > MAX_CHARS_PER_CUE:
            if current:
                chunks.append(current)
                current = [m]
            else:
                # single merged unit exceeds limit — emit alone
                chunks.append([m])
                current = []
        else:
            current = trial
    if current:
        chunks.append(current)

    # Step 3: merge trailing short chunk into previous if ≤1 unit and previous has room
    if len(chunks) >= 2 and len(chunks[-1]) == 1:
        combined = chunks[-2] + chunks[-1]
        if char_len_with_spaces(combined) <= MAX_CHARS_PER_CUE + 4:  # tail grace
            chunks[-2] = combined
            chunks.pop()

    return chunks


def fmt_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        ms = 0; s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        cs = 0; s += 1
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def main() -> int:
    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    timing = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    timing_by_id = {row["section_id"]: row for row in timing["sections"]}

    cues: list[dict] = []
    for section in script["sections"]:
        sid = section["section_id"]
        speaker = section.get("speaker_id", "narrator")
        emotion = section.get("emotion", "normal")
        narration: str = section["narration"]
        t = timing_by_id.get(sid)
        if t is None:
            continue
        t_start = t["start_s"]
        duration = max(t["duration_s"], 0.01)

        words = narration.split()
        groups = chunk_semantic(words)

        # Time distribution by character weight
        weights = [sum(len(w) for w in g) + max(0, len(g) - 1) for g in groups]
        total_w = sum(weights) or 1
        cursor = t_start
        for g, w_ in zip(groups, weights):
            cue_dur = duration * (w_ / total_w)
            # enforce min 0.6s readability
            cue_dur = max(cue_dur, 0.6)
            cue_start = cursor
            cue_end = min(cursor + cue_dur, t_start + duration)
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

    # JSON
    OUT_JSON.write_text(json.dumps({"cues": cues, "schema_version": "v3.1-semantic-merge"},
                                   ensure_ascii=False, indent=2), encoding="utf-8")

    # SRT
    srt_lines = []
    for i, c in enumerate(cues, 1):
        srt_lines.append(str(i))
        srt_lines.append(f"{fmt_srt(c['start_s'])} --> {fmt_srt(c['end_s'])}")
        srt_lines.append(c["text"])
        srt_lines.append("")
    OUT_SRT.write_text("\n".join(srt_lines), encoding="utf-8")

    # ASS
    ass_header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,"
        " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline,"
        " Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Narrator,Black Han Sans,68,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,2,2,60,60,900,1\n"
        "Style: Watson,Black Han Sans,68,&H00FFD166,&H000000FF,&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,2,2,60,60,900,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    ass_body = []
    for c in cues:
        style = "Watson" if c["speaker"] == "assistant" else "Narrator"
        ass_body.append(f"Dialogue: 0,{fmt_ass(c['start_s'])},{fmt_ass(c['end_s'])},{style},,0,0,0,,{c['text']}")
    OUT_ASS.write_text(ass_header + "\n".join(ass_body) + "\n", encoding="utf-8")

    avg_w = sum(len(c["words"]) for c in cues) / max(1, len(cues))
    avg_c = sum(len(c["text"]) for c in cues) / max(1, len(cues))
    max_c = max(len(c["text"]) for c in cues) if cues else 0
    print(f"✅ Subtitle v3.1 (semantic-merge) complete:")
    print(f"  JSON : {OUT_JSON} ({len(cues)} cues)")
    print(f"  ASS  : {OUT_ASS}")
    print(f"  SRT  : {OUT_SRT}")
    print(f"  avg words/cue: {avg_w:.1f} (target 2-5)")
    print(f"  avg chars/cue: {avg_c:.1f} (target ≤14)")
    print(f"  max chars/cue: {max_c} (tail grace ≤18)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
