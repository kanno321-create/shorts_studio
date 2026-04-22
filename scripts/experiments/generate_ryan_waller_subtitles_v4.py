"""Ryan Waller v4 Step 5 — Subtitles (shot-level cues, drift-proof).

INVARIANT Rule 1: reads script_v4.json first.
v4 변경점 (v3.2 → v4):
- Input = script_v4.json (shots) + narration_timing_v4.json (shot-level timing)
- 각 shot.text → semantic chunk (v3.2 로직 유지) → cue
- cue 경계 = shot 경계 (Plan V.5 — 드리프트 방지)
- speaker 는 shot 의 parent section.speaker_id
Writes: subtitles_remotion_v4.{json,ass,srt}
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

SCRIPT_V4 = Path("output/ryan-waller/script_v4.json")
TIMING_V4 = Path("output/ryan-waller/narration_timing_v4.json")
OUT_JSON = Path("output/ryan-waller/subtitles_remotion_v4.json")
OUT_ASS = Path("output/ryan-waller/subtitles_remotion_v4.ass")
OUT_SRT = Path("output/ryan-waller/subtitles_remotion_v4.srt")

MAX_CHARS_PER_CUE = 14
MAX_WORDS_PER_CUE = 5

PREPOSE_MODIFIERS = {
    "그", "이", "저", "그들", "이들", "저들", "여러",
    "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열",
    "스물", "서른", "마흔", "쉰", "백", "천",
    "많은", "적은", "큰", "작은", "긴", "짧은", "첫", "마지막", "모든", "각",
    "그의", "이의", "그녀의",
}
TIME_UNITS = re.compile(r"^(시간|분|초|년|월|일|주|세기|살|번|건|개|명|회|차|시|번째)$")


def char_len(ws: list[str]) -> int:
    return sum(len(w) for w in ws) + max(0, len(ws) - 1)


def is_pure_number(w: str) -> bool:
    if re.match(r"^\d+\.?\d*$", w):
        return True
    if w in {"한","두","세","네","다섯","여섯","일곱","여덟","아홉",
             "열","스물","서른","마흔","쉰","예순","일흔","여든","아흔",
             "백","천","만","억","열한","열두","열여덟","스물한"}:
        return True
    if re.match(r"^\d+[.,]?\d*(년|월|일|시|분|초|개|명|건|살|번|회|차|시간|분간|주|주년|원|달러|그램|킬로|미터)$", w):
        return True
    return False


def chunk_semantic(words: list[str]) -> list[list[str]]:
    merged: list[str] = []
    i = 0
    while i < len(words):
        w = words[i]
        if is_pure_number(w) and i + 1 < len(words):
            core = re.sub(r"[.,!?]+$", "", words[i + 1])
            if TIME_UNITS.match(core):
                merged.append(f"{w} {words[i+1]}"); i += 2; continue
        if w in PREPOSE_MODIFIERS and i + 1 < len(words):
            merged.append(f"{w} {words[i+1]}"); i += 2; continue
        merged.append(w); i += 1

    chunks: list[list[str]] = []
    current: list[str] = []
    for m in merged:
        trial = current + [m]
        if len(trial) > MAX_WORDS_PER_CUE or char_len(trial) > MAX_CHARS_PER_CUE:
            if current:
                chunks.append(current); current = [m]
            else:
                chunks.append([m]); current = []
        else:
            current = trial
    if current:
        chunks.append(current)

    if len(chunks) >= 2 and len(chunks[-1]) == 1:
        combined = chunks[-2] + chunks[-1]
        if char_len(combined) <= MAX_CHARS_PER_CUE + 4:
            chunks[-2] = combined; chunks.pop()
    return chunks


def fmt_srt(s: float) -> str:
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000: ms = 0; sec += 1
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def fmt_ass(s: float) -> str:
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    cs = int(round((s - int(s)) * 100))
    if cs == 100: cs = 0; sec += 1
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"


def main() -> int:
    print("[Agent Subtitle v4] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    timing = json.loads(TIMING_V4.read_text(encoding="utf-8"))
    shot_timing_by_id = {r["shot_id"]: r for r in timing["shots"]}

    # speaker lookup via parent section
    speaker_by_shot: dict[str, str] = {}
    for sec in script["sections"]:
        for shot in sec["shots"]:
            speaker_by_shot[shot["shot_id"]] = sec.get("speaker_id", "narrator")

    cues: list[dict] = []
    for sec in script["sections"]:
        for shot in sec["shots"]:
            sid = shot["shot_id"]
            t = shot_timing_by_id[sid]
            shot_start = t["start_s"]
            shot_dur = max(t["duration_s"], 0.01)
            words = shot["text"].split()
            groups = chunk_semantic(words)
            weights = [char_len(g) for g in groups]
            total_w = sum(weights) or 1
            cursor = shot_start
            for g, wv in zip(groups, weights):
                cue_dur = max(shot_dur * (wv / total_w), 0.5)
                cue_end = min(cursor + cue_dur, shot_start + shot_dur)
                cues.append({
                    "start_s": round(cursor, 3),
                    "end_s": round(cue_end, 3),
                    "text": " ".join(g),
                    "words": g,
                    "speaker": speaker_by_shot[sid],
                    "shot_id": sid,
                    "section": sec["section_id"],
                })
                cursor = cue_end

    OUT_JSON.write_text(json.dumps({
        "schema_version": "v4-shot-boundary-semantic-merge",
        "cue_count": len(cues),
        "cues": cues,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # SRT
    lines = []
    for i, c in enumerate(cues, 1):
        lines += [str(i), f"{fmt_srt(c['start_s'])} --> {fmt_srt(c['end_s'])}", c["text"], ""]
    OUT_SRT.write_text("\n".join(lines), encoding="utf-8")

    # ASS
    ass_header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n"
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
    body = []
    for c in cues:
        style = "Watson" if c["speaker"] == "assistant" else "Narrator"
        body.append(f"Dialogue: 0,{fmt_ass(c['start_s'])},{fmt_ass(c['end_s'])},{style},,0,0,0,,{c['text']}")
    OUT_ASS.write_text(ass_header + "\n".join(body) + "\n", encoding="utf-8")

    avg_w = sum(len(c["words"]) for c in cues) / max(1, len(cues))
    avg_c = sum(len(c["text"]) for c in cues) / max(1, len(cues))
    max_c = max(len(c["text"]) for c in cues) if cues else 0
    print(f"OK Subtitle v4 (shot-boundary semantic-merge):")
    print(f"  JSON : {OUT_JSON} ({len(cues)} cues, {len(set(c['shot_id'] for c in cues))} shots)")
    print(f"  ASS  : {OUT_ASS}")
    print(f"  SRT  : {OUT_SRT}")
    print(f"  avg words/cue: {avg_w:.1f}  avg chars/cue: {avg_c:.1f}  max chars: {max_c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
