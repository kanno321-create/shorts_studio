"""Ryan Waller v4 Step 6 — Duration Reconcile.

INVARIANT Rule 1: reads script_v4.json first.
Input:  narration_timing_v4.json (Step 4 산출, shot-level timing char 비례 분배)
        + script_v4.json (shots[*].duration_hint_s 갱신 대상)
Output: script_v4.json (in-place 갱신) + shot_timing_v4_summary.txt (검증용)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

SCRIPT_V4 = Path("output/ryan-waller/script_v4.json")
TIMING = Path("output/ryan-waller/narration_timing_v4.json")
SUMMARY = Path("output/ryan-waller/shot_timing_v4_summary.txt")


def main() -> int:
    print("[Step 6] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    timing = json.loads(TIMING.read_text(encoding="utf-8"))

    shot_timing_map = {row["shot_id"]: row for row in timing["shots"]}
    print(f"[Step 6] shot timings loaded: {len(shot_timing_map)}")

    updated = 0
    lines = [
        "shot_id                                        section_id            speaker    start_s   end_s duration_s  chars  text",
        "-" * 140,
    ]
    for sec in script["sections"]:
        for shot in sec["shots"]:
            sid = shot["shot_id"]
            if sid not in shot_timing_map:
                raise ValueError(f"shot_id {sid} not found in timing manifest")
            row = shot_timing_map[sid]
            shot["duration_hint_s"] = row["duration_s"]
            shot["start_s"] = row["start_s"]
            shot["end_s"] = row["end_s"]
            updated += 1
            lines.append(
                f"{sid:<48s} {row['section_id']:<20s} {row['speaker']:<10s} "
                f"{row['start_s']:>7.3f} {row['end_s']:>7.3f} {row['duration_s']:>8.3f}  "
                f"{row['char_count']:>4d}  {shot['text'][:40]}"
            )

    SCRIPT_V4.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    lines.append("")
    lines.append(f"total_duration_s = {timing['total_duration_s']:.2f}")
    lines.append(f"shots updated    = {updated}")
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")

    print(f"[Step 6] script_v4.json updated: {updated} shots")
    print(f"[Step 6] summary: {SUMMARY}")
    print(f"[Step 6] total narration duration: {timing['total_duration_s']:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
