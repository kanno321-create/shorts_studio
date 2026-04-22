"""Clip timing calculator from section_timing.json."""

import json

FPS = 30


def compute_clip_durations(section_timing_path: str) -> list:
    """Compute clip durations and frame counts from section timing data.

    Args:
        section_timing_path: Path to section_timing.json file.

    Returns:
        List of dicts with index, section_type, duration_ms, durationInFrames.
    """
    with open(section_timing_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    results = []
    for i, section in enumerate(sections):
        duration_ms = section.get("duration_ms", 0)
        silence_after_ms = section.get("silence_after_ms", 0)
        total_ms = duration_ms + silence_after_ms
        frames = max(1, round(total_ms / 1000 * FPS))
        results.append({
            "index": i,
            "section_type": section.get("section_type", "unknown"),
            "duration_ms": total_ms,
            "durationInFrames": frames,
        })

    return results
