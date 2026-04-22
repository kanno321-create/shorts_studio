"""Ryan Waller v5 — Reconcile script_v5.duration_hint_s with narration_timing_v5 shots timing.

INVARIANT Rule 1: reads script_v5.json first.
Fix: script_v5 was hand-authored with drifted duration values. Overwrite all shot
duration_hint_s with the accurate char-proportional allocation from timing_v5 (which
was derived from probed narration_v4 sections).

Also: v5 timing_v5 shot start_s/end_s include the +1s intro offset. Here we only sync
duration_s (independent of offset), leaving start/end offsets intact for subtitle use.
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

SCRIPT_V5 = Path("output/ryan-waller/script_v5.json")
TIMING_V5 = Path("output/ryan-waller/narration_timing_v5.json")


def main() -> int:
    print("[Reconcile v5] reads script_v5.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))
    timing = json.loads(TIMING_V5.read_text(encoding="utf-8"))
    tmap = {r["shot_id"]: r for r in timing["shots"]}
    updated = 0; drift_total = 0.0
    for sec in script["sections"]:
        for shot in sec["shots"]:
            sid = shot["shot_id"]
            if sid not in tmap:
                raise ValueError(f"shot {sid} not in timing")
            correct = tmap[sid]["duration_s"]
            before = shot.get("duration_hint_s", 0)
            drift = abs(correct - before)
            drift_total += drift
            shot["duration_hint_s"] = correct
            updated += 1
            if drift > 0.05:
                print(f"  {sid:<45s} was={before:.3f}s → now={correct:.3f}s (drift {drift:.3f}s)")
    SCRIPT_V5.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Reconcile v5] {updated} shots reconciled; total drift={drift_total:.2f}s")
    # sanity
    total_shots = sum(s["duration_hint_s"] for sec in script["sections"] for s in sec["shots"])
    total_silences = sum(int(sec.get("silence_after_ms", 0)) / 1000.0 for sec in script["sections"])
    expected_narr = 99.79  # from narration_v4
    print(f"  shots sum = {total_shots:.2f}s")
    print(f"  silences  = {total_silences:.2f}s")
    print(f"  sum+sil   = {total_shots + total_silences:.2f}s (vs narration_v4 99.79s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
