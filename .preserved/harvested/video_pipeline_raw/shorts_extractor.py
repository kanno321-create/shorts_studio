"""Shorts extractor — extract 2-3 shorts from longform video.
⚠️ LONGFORM→SHORTS 추출 전용. Phase 44+ 에서 longform/scripts/ 이동 + rename(longform_to_shorts_extractor.py) 예정.

Reads shorts_extraction[] from longform_script.json, extracts
audio/video segments, replaces CTA, and renders as 9:16 shorts.

Design docs (source of truth):
    - longform/PIPELINE.md lines 86-93 (Stage 7: Shorts Extraction)
    - longform/PIPELINE.md lines 130-140 (extraction strategy)

Exit codes:
    0 = success
    1 = input error
    2 = extraction error

CLI:
    shorts_extractor.py --script SCRIPT_PATH --video VIDEO_PATH --output-dir OUTPUT_DIR
                        [--timing-metadata METADATA_PATH] [--project-root PROJECT_ROOT]
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [shorts_extractor] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────

CHARS_PER_SECOND = 7.9
SHORTS_MIN_DURATION = 30
SHORTS_MAX_DURATION = 60

# Viral potential scores by type (higher = more viral)
VIRAL_SCORES = {
    "shocking_fact": 4,
    "evidence_teaser": 3,
    "suspect_quiz": 2,
    "comedy": 1,
}


def _find_segment_timing(
    segment_ids: list[str],
    timing_metadata: dict,
) -> tuple[float, float]:
    """Find start/end time for given segment IDs in timing metadata.

    Returns (start_s, end_s) relative to full narration.
    """
    cumulative_s = 0.0
    seg_start = None
    seg_end = None

    for ch in timing_metadata.get("chapters", []):
        for seg in ch.get("segments", []):
            gap = seg.get("gap_before_s", 0)
            duration = seg.get("duration_s", 0)
            start = cumulative_s + gap
            end = start + duration

            if seg.get("id") in segment_ids:
                if seg_start is None:
                    seg_start = start
                seg_end = end

            cumulative_s = end

    if seg_start is None:
        # Fallback: estimate from character position
        return 0, 45
    return seg_start, seg_end


def _find_segment_timing_from_script(
    segment_ids: list[str],
    script: dict,
) -> tuple[float, float]:
    """Estimate timing from script character counts when no timing_metadata."""
    cumulative_chars = 0
    seg_start_chars = None
    seg_end_chars = None

    for ch in script.get("chapters", []):
        for seg in ch.get("segments", []):
            text = seg.get("text", "")
            seg_chars = len(text)
            if seg.get("id") in segment_ids:
                if seg_start_chars is None:
                    seg_start_chars = cumulative_chars
                seg_end_chars = cumulative_chars + seg_chars
            cumulative_chars += seg_chars

    if seg_start_chars is None:
        return 0, 45

    return seg_start_chars / CHARS_PER_SECOND, seg_end_chars / CHARS_PER_SECOND


def extract_clip_ffmpeg(
    video_path: str,
    start_s: float,
    end_s: float,
    output_path: str,
):
    """Extract a segment from video using FFmpeg."""
    duration = end_s - start_s
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_s),
        "-i", video_path,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    logger.info("Extracted %.1f-%.1fs → %s", start_s, end_s, output_path)


def convert_16_9_to_9_16(
    input_path: str,
    output_path: str,
):
    """Convert 16:9 video to 9:16 with blurred background bars.

    Strategy: Center-crop main content + blurred fill on top/bottom.
    """
    # FFmpeg filter: scale to fill 1080x1920 with blur background
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920[fg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20:5[bg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Fallback: simple center-crop without blur
        logger.warning("Blur conversion failed, falling back to simple crop")
        simple_cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            output_path,
        ]
        subprocess.run(simple_cmd, check=True, capture_output=True)

    logger.info("Converted 16:9→9:16: %s", output_path)


def extract_shorts(
    script_path: str,
    video_path: str,
    output_dir: str,
    timing_metadata_path: str = None,
) -> list[str]:
    """Extract 2-3 shorts from longform video.

    Returns list of output file paths.
    """
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    timing_metadata = None
    if timing_metadata_path and os.path.exists(timing_metadata_path):
        with open(timing_metadata_path, "r", encoding="utf-8") as f:
            timing_metadata = json.load(f)

    shorts_extraction = script.get("shorts_extraction", [])
    if not shorts_extraction:
        logger.warning("No shorts_extraction entries in script")
        return []

    # Sort by viral potential
    shorts_extraction.sort(
        key=lambda x: VIRAL_SCORES.get(x.get("type", ""), 0),
        reverse=True,
    )

    # Limit to top 3
    shorts_extraction = shorts_extraction[:3]

    shorts_dir = os.path.join(output_dir, "shorts")
    os.makedirs(shorts_dir, exist_ok=True)

    output_paths = []

    for idx, entry in enumerate(shorts_extraction):
        se_type = entry.get("type", "unknown")
        source_segments = entry.get("source_segments", [])
        cta_override = entry.get("cta_override", "전체 수사는 채널 고정 영상에서")

        logger.info(
            "Extracting shorts %d: type=%s, segments=%s",
            idx + 1, se_type, source_segments,
        )

        # Find timing
        if timing_metadata:
            start_s, end_s = _find_segment_timing(source_segments, timing_metadata)
        else:
            start_s, end_s = _find_segment_timing_from_script(source_segments, script)

        duration = end_s - start_s

        # Clamp to shorts duration range
        if duration < SHORTS_MIN_DURATION:
            # Extend end
            end_s = start_s + SHORTS_MIN_DURATION
            logger.info("Extended to minimum %ds", SHORTS_MIN_DURATION)
        elif duration > SHORTS_MAX_DURATION:
            # Truncate
            end_s = start_s + SHORTS_MAX_DURATION
            logger.info("Truncated to maximum %ds", SHORTS_MAX_DURATION)

        # Extract 16:9 clip
        clip_16_9 = os.path.join(shorts_dir, f"_temp_shorts_{idx + 1}_16x9.mp4")
        try:
            extract_clip_ffmpeg(video_path, start_s, end_s, clip_16_9)
        except Exception as e:
            logger.error("FFmpeg extraction failed for shorts %d: %s", idx + 1, e)
            continue

        # Convert to 9:16
        output_path = os.path.join(shorts_dir, f"shorts_{idx + 1}.mp4")
        try:
            convert_16_9_to_9_16(clip_16_9, output_path)
        except Exception as e:
            logger.error("16:9→9:16 conversion failed for shorts %d: %s", idx + 1, e)
            continue

        # Cleanup temp
        if os.path.exists(clip_16_9):
            os.remove(clip_16_9)

        output_paths.append(output_path)
        logger.info(
            "Shorts %d complete: %s (type=%s, %.1f-%.1fs)",
            idx + 1, output_path, se_type, start_s, end_s,
        )

    return output_paths


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract shorts from longform video"
    )
    parser.add_argument("--script", required=True, help="Path to longform_script.json")
    parser.add_argument("--video", required=True, help="Path to final_longform.mp4")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--timing-metadata", default=None, help="Path to timing_metadata.json")
    args = parser.parse_args()

    try:
        paths = extract_shorts(
            args.script, args.video, args.output_dir, args.timing_metadata,
        )
        result = {
            "status": "success",
            "shorts_count": len(paths),
            "shorts_paths": paths,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        logger.error("Shorts extraction failed: %s", e)
        print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
