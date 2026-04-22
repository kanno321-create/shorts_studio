"""Longform subtitle generator — chapter-by-chapter word-level subtitles with speaker tagging.
⚠️ LONGFORM 전용 — Shorts 파이프라인 사용 금지. Phase 44+ 에서 longform/scripts/ 이동 예정.

Generates subtitles from chapter audio files using faster-whisper,
then tags each cue with speaker info from timing_metadata.json.

Design docs (source of truth):
    - longform/PIPELINE.md lines 67-70 (Stage 4-C: Subtitles)
    - longform/SCRIPT_SKILL.md lines 45-66 (game-style dialogue box subtitles)

Exit codes:
    0 = success
    1 = input error
    2 = subtitle generation error

CLI:
    longform_subtitle.py --timing-metadata METADATA_PATH --chapters-dir CHAPTERS_DIR --output-dir OUTPUT_DIR
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Sibling imports
sys.path.insert(0, str(Path(__file__).parent))
import word_subtitle  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [longform_subtitle] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Speaker colors (from design doc: longform/config/channels.yaml incidents.longform)
SPEAKER_COLORS = {
    "detective": "#FFFFFF",
    "assistant": "#FFD000",
    "mascot": "#FFD000",  # mascot = assistant alias
}


def _build_speaker_timeline(chapter_meta: dict) -> list[dict]:
    """Build a timeline of speaker changes from timing metadata.

    Returns list of {start_s, end_s, speaker} dicts, sorted by start_s.
    The start/end times are cumulative within the chapter.
    """
    timeline = []
    cumulative_s = 0.0

    for seg in chapter_meta.get("segments", []):
        duration = seg.get("duration_s", 0)
        gap = seg.get("gap_before_s", 0)
        start = cumulative_s + gap
        end = start + duration
        timeline.append({
            "start_s": start,
            "end_s": end,
            "speaker": seg.get("speaker", "detective"),
        })
        cumulative_s = end

    return timeline


def _tag_speaker_for_cue(cue_start_ms: int, cue_end_ms: int, timeline: list[dict]) -> str:
    """Determine which speaker a subtitle cue belongs to based on timing overlap.

    Returns speaker name with maximum temporal overlap.
    """
    cue_start_s = cue_start_ms / 1000.0
    cue_end_s = cue_end_ms / 1000.0

    best_speaker = "detective"
    best_overlap = 0.0

    for entry in timeline:
        overlap_start = max(cue_start_s, entry["start_s"])
        overlap_end = min(cue_end_s, entry["end_s"])
        overlap = max(0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = entry["speaker"]

    return best_speaker


def generate_longform_subtitles(
    timing_metadata_path: str,
    chapters_dir: str,
    output_dir: str,
    script_path: str = None,
) -> dict:
    """Generate word-level subtitles for all chapters with speaker tagging.

    Args:
        timing_metadata_path: Path to timing_metadata.json from longform_tts.py.
        chapters_dir: Directory containing ch{N}_audio.mp3 files.
        output_dir: Directory to write subtitle files.
        script_path: Optional path to longform_script.json for Whisper hints.

    Returns:
        Summary dict with per-chapter results.
    """
    # Load timing metadata
    with open(timing_metadata_path, "r", encoding="utf-8") as f:
        timing = json.load(f)

    # Load script for Whisper initial_prompt hints
    script_texts = {}
    if script_path and os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            script = json.load(f)
        for ch in script.get("chapters", []):
            ch_id = ch.get("id", "")
            texts = [s.get("text", "") for s in ch.get("segments", [])]
            script_texts[ch_id] = " ".join(texts)

    os.makedirs(output_dir, exist_ok=True)

    results = {
        "chapters": [],
        "total_cue_count": 0,
    }

    for chapter_meta in timing.get("chapters", []):
        ch_id = chapter_meta.get("id", "unknown")
        audio_file = chapter_meta.get("audio_file")

        if not audio_file or not os.path.exists(audio_file):
            # Try to find by convention
            audio_file = os.path.join(chapters_dir, f"{ch_id}_audio.mp3")
            if not os.path.exists(audio_file):
                logger.warning("Audio not found for chapter %s, skipping", ch_id)
                continue

        logger.info("Processing subtitles for chapter %s", ch_id)

        # Build speaker timeline for this chapter
        timeline = _build_speaker_timeline(chapter_meta)

        # Generate word-level SRT using existing word_subtitle
        srt_path = os.path.join(output_dir, f"{ch_id}.srt")
        initial_prompt = script_texts.get(ch_id)

        try:
            sub_result = word_subtitle.generate_word_subtitles(
                audio_path=audio_file,
                output_path=srt_path,
                initial_prompt=initial_prompt,
                language="ko",
            )
        except Exception as e:
            logger.error("Subtitle generation failed for %s: %s", ch_id, e)
            continue

        # Read the generated Remotion JSON.
        # word_subtitle.py writes to: {output_dir}/subtitles_remotion.json
        # (NOT {base}_remotion.json as one might expect)
        remotion_json_candidates = [
            os.path.join(output_dir, "subtitles_remotion.json"),
            srt_path.rsplit(".", 1)[0] + "_remotion.json",
        ]
        cues = []
        for candidate in remotion_json_candidates:
            if os.path.exists(candidate) and os.path.getsize(candidate) > 10:
                with open(candidate, "r", encoding="utf-8") as f:
                    cues = json.load(f)
                logger.info("Loaded Remotion JSON from %s (%d cues)", candidate, len(cues))
                # Remove the file so the next chapter doesn't re-read it
                break
        if not cues:
            logger.warning("No Remotion JSON found for %s, subtitle cues will be empty", ch_id)

        # Tag each cue with speaker info
        tagged_cues = []
        for cue in cues:
            speaker = _tag_speaker_for_cue(
                cue.get("startMs", 0),
                cue.get("endMs", 0),
                timeline,
            )
            tagged_cue = dict(cue)
            tagged_cue["speaker"] = speaker
            tagged_cue["speakerColor"] = SPEAKER_COLORS.get(speaker, "#FFFFFF")
            tagged_cues.append(tagged_cue)

        # Write tagged Remotion JSON
        tagged_json_path = os.path.join(output_dir, f"{ch_id}_remotion.json")
        with open(tagged_json_path, "w", encoding="utf-8") as f:
            json.dump(tagged_cues, f, ensure_ascii=False, indent=2)

        # Write tagged SRT with speaker tags
        tagged_srt_path = os.path.join(output_dir, f"{ch_id}_tagged.srt")
        _write_tagged_srt(tagged_cues, tagged_srt_path)

        ch_result = {
            "id": ch_id,
            "srt_path": srt_path,
            "remotion_json_path": tagged_json_path,
            "tagged_srt_path": tagged_srt_path,
            "cue_count": len(tagged_cues),
            "duration_seconds": sub_result.get("duration_seconds", 0),
        }
        results["chapters"].append(ch_result)
        results["total_cue_count"] += len(tagged_cues)

        logger.info(
            "Chapter %s: %d cues, %.1fs",
            ch_id, len(tagged_cues), sub_result.get("duration_seconds", 0),
        )

    return results


def _write_tagged_srt(cues: list[dict], output_path: str):
    """Write SRT file with [탐정]/[조수] speaker tags."""
    speaker_labels = {
        "detective": "[탐정]",
        "assistant": "[조수]",
        "mascot": "[조수]",
    }

    with open(output_path, "w", encoding="utf-8") as f:
        for i, cue in enumerate(cues, 1):
            start_ms = cue.get("startMs", 0)
            end_ms = cue.get("endMs", 0)
            words = cue.get("words", [])
            speaker = cue.get("speaker", "detective")
            label = speaker_labels.get(speaker, "")

            start_str = _ms_to_srt_time(start_ms)
            end_str = _ms_to_srt_time(end_ms)
            text = " ".join(words)
            if label:
                text = f"{label} {text}"

            f.write(f"{i}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")


def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format HH:MM:SS,mmm."""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate longform subtitles with speaker tagging"
    )
    parser.add_argument(
        "--timing-metadata", required=True,
        help="Path to timing_metadata.json from longform_tts.py",
    )
    parser.add_argument(
        "--chapters-dir", required=True,
        help="Directory containing chapter audio MP3s",
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Output directory for subtitle files",
    )
    parser.add_argument(
        "--script", default=None,
        help="Path to longform_script.json for Whisper hints",
    )
    args = parser.parse_args()

    try:
        result = generate_longform_subtitles(
            args.timing_metadata,
            args.chapters_dir,
            args.output_dir,
            args.script,
        )
        summary = {
            "status": "success",
            "chapter_count": len(result["chapters"]),
            "total_cue_count": result["total_cue_count"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        logger.error("Longform subtitle generation failed: %s", e)
        print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
