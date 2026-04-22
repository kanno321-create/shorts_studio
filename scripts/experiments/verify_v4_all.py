"""Ryan Waller v4 Step 10+11+12 — Freeze + Coverage + Mid-frame extract.

INVARIANT Rule 1: reads script_v4.json first.
- Step 10 Freeze: each shot_final mp4 via `ffmpeg freezedetect n=0.003 d=0.8`
- Step 12 Coverage: 22/22 shot_final exists + duration ≈ shot.duration_hint_s + silence
- Mid-frame: for Agent 4 Inspector — extract mid-frame of each shot_final
"""
from __future__ import annotations
import builtins as _b
import json
import re
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass


def _p(*a, **k):
    k.setdefault("flush", True); _b.print(*a, **k)


SCRIPT_V4 = Path("output/ryan-waller/script_v4.json")
SHOT_FINAL = Path("output/ryan-waller/sources/shot_final")
MIDFRAMES = Path("output/ryan-waller/inspect_v4/mid_frames")
FREEZE_REPORT = Path("output/ryan-waller/freeze_report_v4.json")
COVERAGE_REPORT = Path("output/ryan-waller/coverage_report_v4.json")


def probe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def freeze_detect(p: Path) -> list[dict]:
    r = subprocess.run(
        ["ffmpeg", "-i", str(p), "-vf", "freezedetect=n=0.003:d=0.8",
         "-map", "0:v:0", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    events = []
    for line in (r.stderr or "").splitlines():
        m = re.search(r"freeze_start:\s*([\d.]+)", line)
        if m:
            events.append({"type": "start", "t": float(m.group(1))})
        m = re.search(r"freeze_end:\s*([\d.]+)", line)
        if m:
            events.append({"type": "end", "t": float(m.group(1))})
        m = re.search(r"freeze_duration:\s*([\d.]+)", line)
        if m:
            events.append({"type": "duration", "t": float(m.group(1))})
    return events


def extract_midframe(src: Path, dst: Path, t: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", str(src),
        "-vframes", "1", "-q:v", "2",
        str(dst),
    ], check=True, capture_output=True)


def main() -> int:
    _p("[Verify v4] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))

    # Flat shot list with section silence (section-last gets extended)
    shots_info: list[dict] = []
    for sec in script["sections"]:
        sil = int(sec.get("silence_after_ms", 0)) / 1000.0
        last_id = sec["shots"][-1]["shot_id"]
        for shot in sec["shots"]:
            target = shot["duration_hint_s"]
            if shot["shot_id"] == last_id:
                target += sil
            shots_info.append({
                "shot_id": shot["shot_id"],
                "section_id": sec["section_id"],
                "expected_duration": round(target, 3),
            })

    # Step 12 Coverage
    coverage = []
    missing = []
    for info in shots_info:
        f = SHOT_FINAL / f"{info['shot_id']}_final.mp4"
        if not f.exists():
            missing.append(info["shot_id"])
            continue
        actual = probe_duration(f)
        diff = actual - info["expected_duration"]
        coverage.append({
            **info,
            "file": str(f),
            "actual_duration": round(actual, 3),
            "diff_s": round(diff, 3),
            "within_0.2s": abs(diff) <= 0.2,
        })
    coverage_pass = len(missing) == 0 and all(c["within_0.2s"] for c in coverage)
    out_cov = {
        "target": "22/22 shots + each within ±0.2s of expected_duration",
        "shot_count": len(coverage),
        "missing": missing,
        "all_within_tolerance": coverage_pass,
        "shots": coverage,
    }
    COVERAGE_REPORT.write_text(json.dumps(out_cov, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"[Step 12 Coverage] {len(coverage)}/22 shots, all_within_0.2s={coverage_pass}")
    if missing:
        _p(f"  MISSING: {missing}")

    # Step 10 Freeze per-shot
    freeze_by_shot = {}
    total_events = 0
    for info in shots_info:
        f = SHOT_FINAL / f"{info['shot_id']}_final.mp4"
        if not f.exists():
            continue
        ev = freeze_detect(f)
        freeze_by_shot[info["shot_id"]] = ev
        total_events += sum(1 for e in ev if e["type"] == "start")
    out_fz = {
        "target": "total freeze starts = 0",
        "total_freeze_events": total_events,
        "per_shot": freeze_by_shot,
    }
    FREEZE_REPORT.write_text(json.dumps(out_fz, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"[Step 10 Freeze] total freeze events = {total_events} (target 0)")

    # Mid-frame extract for Agent 4 Inspector
    _p(f"[Mid-frame] extracting 22 mid-frames for subagent vision ...")
    for info in shots_info:
        f = SHOT_FINAL / f"{info['shot_id']}_final.mp4"
        if not f.exists():
            continue
        dur = probe_duration(f)
        mid = dur / 2
        dst = MIDFRAMES / f"{info['shot_id']}_mid.jpg"
        extract_midframe(f, dst, mid)
    _p(f"[Mid-frame] written to {MIDFRAMES}/ ({len(shots_info)} frames)")

    _p()
    _p("OK verify v4 done:")
    _p(f"  coverage_report : {COVERAGE_REPORT}")
    _p(f"  freeze_report   : {FREEZE_REPORT}")
    _p(f"  mid_frames      : {MIDFRAMES}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
