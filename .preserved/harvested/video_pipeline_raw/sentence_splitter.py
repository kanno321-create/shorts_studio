"""SRT parser and sentence-boundary clip splitter for video effects pipeline.

Provides subtitle-timestamp-based clip boundary logic that replaces fixed-time
clip splitting. Used by scene-designer agent for sentence-aware scene cuts.

Per D-14: Cut at sentence boundaries from subtitles.srt.
Per D-15: Target average clip length 2-3 seconds.
Per RESEARCH 5.1: Cut point = sentence_start - visual_lead (0.1-0.2s).
"""
from __future__ import annotations

import re
from typing import Optional


# SRT timestamp regex: HH:MM:SS,mmm
_TS_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")

# SRT block regex: index, timestamps, text lines
_BLOCK_RE = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n"
    r"((?:(?!\d+\s*\n\d{2}:\d{2}:\d{2}).+\n?)+)",
    re.MULTILINE,
)


def _ts_to_seconds(ts: str) -> float:
    """Convert SRT timestamp 'HH:MM:SS,mmm' to float seconds."""
    m = _TS_RE.match(ts)
    if not m:
        raise ValueError(f"Invalid SRT timestamp: {ts}")
    h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return h * 3600 + mi * 60 + s + ms / 1000.0


def parse_srt(srt_content: str) -> list[dict]:
    """Parse SRT subtitle content into structured entries.

    Returns list of dicts: [{"index": int, "start": float, "end": float, "text": str}]
    Timestamps converted from HH:MM:SS,mmm to float seconds.
    Multi-line subtitle text joined with space.
    """
    if not srt_content or not srt_content.strip():
        return []

    results: list[dict] = []
    for match in _BLOCK_RE.finditer(srt_content):
        index = int(match.group(1))
        start = _ts_to_seconds(match.group(2))
        end = _ts_to_seconds(match.group(3))
        # Join multi-line text with space, strip each line
        text_block = match.group(4).strip()
        text = " ".join(line.strip() for line in text_block.split("\n") if line.strip())
        results.append({
            "index": index,
            "start": start,
            "end": end,
            "text": text,
        })

    return results


def _find_split_point(text: str) -> Optional[float]:
    """Find the best split point in text as a ratio (0.0-1.0) of the text length.

    Prefers comma or period closest to the midpoint.
    Returns None if no suitable split point found.
    """
    if not text:
        return None

    mid = len(text) / 2.0
    best_pos = None
    best_dist = float("inf")

    for i, ch in enumerate(text):
        if ch in (",", ".", ";", ":", "!"):
            dist = abs(i - mid)
            if dist < best_dist:
                best_dist = dist
                best_pos = i

    if best_pos is not None and best_pos > 0 and best_pos < len(text) - 1:
        return (best_pos + 1) / len(text)

    # Fallback: split at midpoint
    return 0.5


def compute_clip_boundaries(
    srt_entries: list[dict],
    audio_duration: float,
    max_clip_duration: float = 4.0,
    visual_lead: float = 0.15,
) -> list[dict]:
    """Compute clip split points from SRT sentence boundaries.

    Per D-14: Cut at sentence boundaries from subtitles.srt.
    Per D-15: Target average clip length 2-3 seconds.

    Algorithm:
    1. Each SRT entry becomes a candidate clip boundary
    2. If a sentence exceeds max_clip_duration, split at comma/period within text
    3. Apply visual_lead: cut point = sentence_start - visual_lead (clamped to >= 0)
    4. Adjust last clip to fill remaining audio_duration

    Returns list of dicts: [{"start": float, "end": float, "duration": float, "sentence_text": str}]
    """
    if not srt_entries:
        return [{"start": 0.0, "end": audio_duration, "duration": audio_duration, "sentence_text": ""}]

    # Step 1: Build raw boundaries from SRT entries, splitting long ones
    raw_segments: list[dict] = []

    for entry in srt_entries:
        seg_start = entry["start"]
        seg_end = entry["end"]
        seg_duration = seg_end - seg_start
        seg_text = entry["text"]

        if seg_duration <= max_clip_duration:
            raw_segments.append({
                "start": seg_start,
                "end": seg_end,
                "text": seg_text,
            })
        else:
            # Split long sentence at clause boundary
            split_ratio = _find_split_point(seg_text)
            if split_ratio is None:
                split_ratio = 0.5

            split_time = seg_start + seg_duration * split_ratio

            # First part
            raw_segments.append({
                "start": seg_start,
                "end": split_time,
                "text": seg_text,
            })
            # Second part
            raw_segments.append({
                "start": split_time,
                "end": seg_end,
                "text": seg_text,
            })

    # Step 2: Apply visual lead and build final clip boundaries
    clips: list[dict] = []

    for i, seg in enumerate(raw_segments):
        if i == 0:
            clip_start = 0.0
        else:
            # Visual lead: cut slightly before sentence starts
            clip_start = max(0.0, seg["start"] - visual_lead)

        if i == len(raw_segments) - 1:
            clip_end = audio_duration
        else:
            # End at the next clip's start (with visual lead)
            next_seg = raw_segments[i + 1]
            clip_end = max(0.0, next_seg["start"] - visual_lead)

        # Ensure clips don't overlap or have negative duration
        if clips:
            clip_start = clips[-1]["end"]

        duration = clip_end - clip_start
        if duration <= 0:
            # Skip zero-duration clips
            continue

        clips.append({
            "start": round(clip_start, 3),
            "end": round(clip_end, 3),
            "duration": round(duration, 3),
            "sentence_text": seg["text"],
        })

    # Step 3: Adjust last clip to exactly match audio_duration
    if clips:
        clips[-1]["end"] = round(audio_duration, 3)
        clips[-1]["duration"] = round(audio_duration - clips[-1]["start"], 3)

    return clips
