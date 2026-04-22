"""Ryan Waller v5 Subtitles — shot-boundary cues with v5 timing (+1s intro offset).

INVARIANT Rule 1: reads script_v5.json first.
Uses narration_timing_v5.json (shots shifted +1s from intro prepend).
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

SCRIPT_V5 = Path("output/ryan-waller/script_v5.json")
TIMING_V5 = Path("output/ryan-waller/narration_timing_v5.json")
OUT_JSON = Path("output/ryan-waller/subtitles_remotion_v5.json")
OUT_ASS = Path("output/ryan-waller/subtitles_remotion_v5.ass")
OUT_SRT = Path("output/ryan-waller/subtitles_remotion_v5.srt")

MAX_CHARS, MAX_WORDS = 14, 5
PREPOSE = {
    "그","이","저","그들","이들","저들","여러","한","두","세","네","다섯","여섯","일곱","여덟","아홉","열",
    "스물","서른","마흔","쉰","백","천","많은","적은","큰","작은","긴","짧은","첫","마지막","모든","각",
    "그의","이의","그녀의",
}
TIME_UNITS = re.compile(r"^(시간|분|초|년|월|일|주|세기|살|번|건|개|명|회|차|시|번째)$")


def char_len(ws): return sum(len(w) for w in ws) + max(0, len(ws) - 1)


def is_num(w):
    if re.match(r"^\d+\.?\d*$", w): return True
    if w in {"한","두","세","네","다섯","여섯","일곱","여덟","아홉","열","스물","서른","마흔","쉰","예순",
             "일흔","여든","아흔","백","천","만","억","열한","열두","열여덟","스물한"}: return True
    if re.match(r"^\d+[.,]?\d*(년|월|일|시|분|초|개|명|건|살|번|회|차|시간|분간|주|주년|원|달러)$", w): return True
    return False


def chunk(words):
    merged = []
    i = 0
    while i < len(words):
        w = words[i]
        if is_num(w) and i + 1 < len(words):
            core = re.sub(r"[.,!?]+$", "", words[i + 1])
            if TIME_UNITS.match(core):
                merged.append(f"{w} {words[i+1]}"); i += 2; continue
        if w in PREPOSE and i + 1 < len(words):
            merged.append(f"{w} {words[i+1]}"); i += 2; continue
        merged.append(w); i += 1
    groups, cur = [], []
    for m in merged:
        trial = cur + [m]
        if len(trial) > MAX_WORDS or char_len(trial) > MAX_CHARS:
            if cur: groups.append(cur); cur = [m]
            else: groups.append([m]); cur = []
        else: cur = trial
    if cur: groups.append(cur)
    if len(groups) >= 2 and len(groups[-1]) == 1:
        combined = groups[-2] + groups[-1]
        if char_len(combined) <= MAX_CHARS + 4:
            groups[-2] = combined; groups.pop()
    return groups


def fmt_srt(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000: ms = 0; sec += 1
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def fmt_ass(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    cs = int(round((s - int(s)) * 100))
    if cs == 100: cs = 0; sec += 1
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"


def main():
    print("[Subtitle v5] reads script_v5.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))
    timing = json.loads(TIMING_V5.read_text(encoding="utf-8"))
    tmap = {r["shot_id"]: r for r in timing["shots"]}
    spk = {}
    for sec in script["sections"]:
        for s in sec["shots"]:
            spk[s["shot_id"]] = sec.get("speaker_id", "narrator")

    cues = []
    for sec in script["sections"]:
        for shot in sec["shots"]:
            sid = shot["shot_id"]
            t = tmap[sid]
            ss, sdur = t["start_s"], max(t["duration_s"], 0.01)
            words = shot["text"].split()
            groups = chunk(words)
            weights = [char_len(g) for g in groups]
            tw = sum(weights) or 1
            cur = ss
            for g, wv in zip(groups, weights):
                cd = max(sdur * (wv / tw), 0.5)
                ce = min(cur + cd, ss + sdur)
                cues.append({"start_s": round(cur, 3), "end_s": round(ce, 3),
                             "text": " ".join(g), "words": g,
                             "speaker": spk[sid], "shot_id": sid,
                             "section": sec["section_id"]})
                cur = ce

    OUT_JSON.write_text(json.dumps({
        "schema_version": "v5-shot-boundary-with-intro-offset",
        "cue_count": len(cues), "cues": cues,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    for i, c in enumerate(cues, 1):
        lines += [str(i), f"{fmt_srt(c['start_s'])} --> {fmt_srt(c['end_s'])}", c["text"], ""]
    OUT_SRT.write_text("\n".join(lines), encoding="utf-8")

    ass_h = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour,"
        " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline,"
        " Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Narrator,Black Han Sans,68,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,2,2,60,60,900,1\n"
        "Style: Watson,Black Han Sans,68,&H00FFD166,&H000000FF,&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,2,2,60,60,900,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    body = []
    for c in cues:
        style = "Watson" if c["speaker"] == "assistant" else "Narrator"
        body.append(f"Dialogue: 0,{fmt_ass(c['start_s'])},{fmt_ass(c['end_s'])},{style},,0,0,0,,{c['text']}")
    OUT_ASS.write_text(ass_h + "\n".join(body) + "\n", encoding="utf-8")

    print(f"OK Subtitle v5 — {len(cues)} cues, 22 shots")
    print(f"  first cue start={cues[0]['start_s']}s (should be ~1.0s)")
    print(f"  last cue end   ={cues[-1]['end_s']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
