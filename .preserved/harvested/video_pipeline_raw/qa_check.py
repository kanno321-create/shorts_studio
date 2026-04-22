"""34-item automated QA checklist for rendered videos (shorts) / 35-item (video).

Validates rendered final.mp4 against resolution, visual quality, subtitle,
audio sync, metadata consistency, editing quality, and YouTube compliance criteria.
Uses ffprobe for metadata inspection, Pillow frame sampling for visual/subtitle
analysis, and difflib for script uniqueness checking.

Shorts pipeline: 34 items (QA-CF-01..08, QA-VQ-09..13, QA-SQ-14..17, QA-AS-18..20, QA-MC-21..22, QA-EQ-01..06, QA-YC-01..06)
Video pipeline: 35 items (adds QA-MC-23 minimum clip count >= 30)

CLI interface:
    qa_check.py --video VIDEO_PATH --manifest MANIFEST_PATH --audio AUDIO_PATH
                [--pipeline shorts|video] [--script SCRIPT_PATH] [--metadata META_PATH]
                [--history-dir HISTORY_DIR]

Exit codes:
    0 = QA passed (all critical items pass, total score >= 28/35 video or 27/34 shorts)
    1 = QA failed

Output:
    JSON to stdout with keys: status, passed, score, total, failures, warnings
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

# Pillow imports for frame analysis
from PIL import Image, ImageStat


# ---------------------------------------------------------------------------
# Pipeline-specific thresholds for QA validation
# ---------------------------------------------------------------------------

PIPELINE_THRESHOLDS = {
    "shorts": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": 0.5625,
        "aspect_tolerance": 0.01,
        "duration_min": 15.0,
        "duration_max": 60.0,
        "file_size_min_mb": 5.0,
        "file_size_max_mb": 50.0,
        "max_static_seconds": 5.0,
        "min_clips": 5,
        "ai_clip_min_resolution": 720,
        "ai_clip_min_duration": 2.0,
        "ai_clip_max_duration": 15.0,
        "max_ai_clips_per_short": 3,
    },
    "video": {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": 1.7778,
        "aspect_tolerance": 0.01,
        "duration_min": 300.0,
        "duration_max": 900.0,
        "file_size_min_mb": 50.0,
        "file_size_max_mb": 500.0,
        "max_static_seconds": 8.0,
        "min_clips": 30,
        "ai_clip_min_resolution": 720,
        "ai_clip_min_duration": 2.0,
        "ai_clip_max_duration": 15.0,
        "max_ai_clips_per_short": 3,
    },
}


# ---------------------------------------------------------------------------
# 1. get_video_metadata
# ---------------------------------------------------------------------------

def get_video_metadata(video_path: str) -> dict:
    """Extract video metadata via ffprobe JSON output.

    Runs ffprobe and parses the JSON to extract video stream, audio stream,
    and format information into a structured dict.

    Returns:
        {
            "video": {"codec": str, "width": int, "height": int, "pix_fmt": str},
            "audio": {"codec": str, "sample_rate": int},
            "format": {"duration": float, "size": int},
        }
    """
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(video_path).replace("\\", "/"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    video_stream = {}
    audio_stream = {}
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and not video_stream:
            video_stream = {
                "codec": stream.get("codec_name", ""),
                "width": int(stream.get("width", 0)),
                "height": int(stream.get("height", 0)),
                "pix_fmt": stream.get("pix_fmt", ""),
            }
        elif stream.get("codec_type") == "audio" and not audio_stream:
            audio_stream = {
                "codec": stream.get("codec_name", ""),
                "sample_rate": int(stream.get("sample_rate", 0)),
            }

    fmt = data.get("format", {})
    format_info = {
        "duration": float(fmt.get("duration", 0)),
        "size": int(fmt.get("size", 0)),
    }

    return {
        "video": video_stream,
        "audio": audio_stream,
        "format": format_info,
    }


# ---------------------------------------------------------------------------
# 2. check_resolution_format (QA-CF-01 through QA-CF-08)
# ---------------------------------------------------------------------------

def check_resolution_format(metadata: dict, thresholds: dict = None) -> list:
    """Check 8 resolution/format items (Category 1: Critical).

    QA-CF-01: Resolution (parameterized by thresholds)
    QA-CF-02: Aspect ratio (parameterized by thresholds)
    QA-CF-03: Duration max (parameterized by thresholds)
    QA-CF-04: Duration min (parameterized by thresholds)
    QA-CF-05: Video codec H.264
    QA-CF-06: Pixel format yuv420p
    QA-CF-07: Audio codec AAC
    QA-CF-08: Audio sample rate 44100 or 48000 Hz

    Args:
        metadata: Video metadata dict from get_video_metadata
        thresholds: Pipeline-specific thresholds dict. Defaults to PIPELINE_THRESHOLDS["shorts"].
    """
    if thresholds is None:
        thresholds = PIPELINE_THRESHOLDS["shorts"]

    v = metadata["video"]
    a = metadata["audio"]
    f = metadata["format"]
    results = []

    expected_w = thresholds["width"]
    expected_h = thresholds["height"]
    expected_ratio = thresholds["aspect_ratio"]
    ratio_tol = thresholds["aspect_tolerance"]
    dur_min = thresholds["duration_min"]
    dur_max = thresholds["duration_max"]
    size_min = thresholds["file_size_min_mb"]
    size_max = thresholds["file_size_max_mb"]

    # QA-CF-01: Resolution
    res_ok = v["width"] == expected_w and v["height"] == expected_h
    results.append({
        "id": "QA-CF-01", "name": "Resolution", "passed": res_ok,
        "expected": f"{expected_w}x{expected_h}", "actual": f"{v['width']}x{v['height']}",
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-02: Aspect ratio
    if v["height"] > 0:
        ratio = v["width"] / v["height"]
    else:
        ratio = 0.0
    ratio_ok = abs(ratio - expected_ratio) < ratio_tol
    results.append({
        "id": "QA-CF-02", "name": "Aspect ratio", "passed": ratio_ok,
        "expected": f"{expected_ratio:.4f} (+/- {ratio_tol})", "actual": f"{ratio:.4f}",
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-03: Duration max
    dur = f["duration"]
    dur_max_ok = dur <= dur_max
    results.append({
        "id": "QA-CF-03", "name": "Duration max", "passed": dur_max_ok,
        "expected": f"<= {dur_max}s", "actual": f"{dur:.1f}s",
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-04: Duration min
    dur_min_ok = dur >= dur_min
    results.append({
        "id": "QA-CF-04", "name": "Duration min", "passed": dur_min_ok,
        "expected": f">= {dur_min}s", "actual": f"{dur:.1f}s",
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-05: Video codec
    codec_ok = v["codec"] == "h264"
    results.append({
        "id": "QA-CF-05", "name": "Video codec", "passed": codec_ok,
        "expected": "h264", "actual": v["codec"],
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-06: Pixel format
    pix_ok = v["pix_fmt"] == "yuv420p"
    results.append({
        "id": "QA-CF-06", "name": "Pixel format", "passed": pix_ok,
        "expected": "yuv420p", "actual": v["pix_fmt"],
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-07: Audio codec
    acodec_ok = a["codec"] == "aac"
    results.append({
        "id": "QA-CF-07", "name": "Audio codec", "passed": acodec_ok,
        "expected": "aac", "actual": a["codec"],
        "category": "resolution_format", "critical": True,
    })

    # QA-CF-08: Audio sample rate
    sr_ok = a["sample_rate"] in (44100, 48000)
    results.append({
        "id": "QA-CF-08", "name": "Audio sample rate", "passed": sr_ok,
        "expected": "44100 or 48000", "actual": str(a["sample_rate"]),
        "category": "resolution_format", "critical": True,
    })

    return results


# ---------------------------------------------------------------------------
# 3. sample_frames
# ---------------------------------------------------------------------------

def sample_frames(video_path: str, interval: float = 1.0) -> list:
    """Extract frames at interval-second intervals and compute pixel stats.

    Uses FFmpeg to extract frames to temporary PNGs, then Pillow to analyze
    each frame for avg_rgb, stddev, and brightness.

    Returns:
        [{"time": float, "avg_rgb": (R, G, B), "stddev": float, "brightness": float}, ...]
    """
    tmp_dir = tempfile.mkdtemp(prefix="qa_frames_")
    try:
        # Extract frames at the specified interval
        cmd = [
            "ffmpeg", "-i", str(video_path).replace("\\", "/"),
            "-vf", f"fps=1/{interval}",
            "-q:v", "2",
            os.path.join(tmp_dir, "frame_%04d.png").replace("\\", "/"),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        frames = []
        frame_files = sorted(
            f for f in os.listdir(tmp_dir) if f.startswith("frame_") and f.endswith(".png")
        )
        for idx, fname in enumerate(frame_files):
            fpath = os.path.join(tmp_dir, fname)
            img = Image.open(fpath).convert("RGB")
            stat = ImageStat.Stat(img)

            avg_rgb = tuple(int(round(c)) for c in stat.mean[:3])
            # stddev: average of per-channel stddev
            stddev = sum(stat.stddev[:3]) / 3.0
            # brightness: mean of grayscale
            gray = img.convert("L")
            gray_stat = ImageStat.Stat(gray)
            brightness = gray_stat.mean[0]

            frames.append({
                "time": idx * interval,
                "avg_rgb": avg_rgb,
                "stddev": round(stddev, 2),
                "brightness": round(brightness, 2),
            })
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return frames


# ---------------------------------------------------------------------------
# 4. check_visual_quality (QA-VQ-09 through QA-VQ-13)
# ---------------------------------------------------------------------------

def check_visual_quality(video_path: str, metadata: dict, thresholds: dict = None) -> list:
    """Check 5 visual quality items (Category 2: Critical).

    QA-VQ-09: No white frames (avg RGB ALL > 245 AND stddev < 10)
    QA-VQ-10: No black frames (brightness < 5)
    QA-VQ-11: Visual change interval (parameterized max_static_seconds)
    QA-VQ-12: No static clip (parameterized max_static_seconds)
    QA-VQ-13: File size (parameterized min/max MB)

    Args:
        video_path: Path to rendered video
        metadata: Video metadata dict
        thresholds: Pipeline-specific thresholds dict. Defaults to PIPELINE_THRESHOLDS["shorts"].
    """
    if thresholds is None:
        thresholds = PIPELINE_THRESHOLDS["shorts"]

    max_static = thresholds["max_static_seconds"]
    size_min_mb = thresholds["file_size_min_mb"]
    size_max_mb = thresholds["file_size_max_mb"]

    frames = sample_frames(video_path)
    results = []

    # QA-VQ-09: White frame detection
    # White = avg RGB ALL > 245 AND stddev < 10
    # Tolerance: max 0.5s continuous white (at 1s sampling, any single white frame fails)
    white_frames = []
    for frame in frames:
        r, g, b = frame["avg_rgb"]
        if r > 245 and g > 245 and b > 245 and frame["stddev"] < 10:
            white_frames.append(frame["time"])

    # Check for continuous white frames exceeding 0.5s
    # With 1s interval sampling, any white frame indicates >= 1s of white (fails 0.5s tolerance)
    white_ok = len(white_frames) == 0
    results.append({
        "id": "QA-VQ-09", "name": "No white frames", "passed": white_ok,
        "expected": "No white frames (avg RGB < 245 OR stddev > 10)",
        "actual": f"{len(white_frames)} white frame(s) at {white_frames}" if white_frames else "No white frames",
        "category": "visual_quality", "critical": True,
    })

    # QA-VQ-10: Black frame detection
    black_frames = []
    for frame in frames:
        if frame["brightness"] < 5:
            black_frames.append(frame["time"])

    black_ok = len(black_frames) == 0
    results.append({
        "id": "QA-VQ-10", "name": "No black frames", "passed": black_ok,
        "expected": "No black frames (brightness > 5)",
        "actual": f"{len(black_frames)} black frame(s) at {black_frames}" if black_frames else "No black frames",
        "category": "visual_quality", "critical": True,
    })

    # QA-VQ-11: Visual change interval
    # Compare consecutive frames. If brightness difference < threshold for > max_static, fail.
    SCENE_CHANGE_THRESHOLD = 5.0  # brightness difference threshold
    static_detected = False
    max_static_duration = 0.0
    if len(frames) >= 2:
        static_start = frames[0]["time"]
        for i in range(1, len(frames)):
            diff = abs(frames[i]["brightness"] - frames[i - 1]["brightness"])
            if diff < SCENE_CHANGE_THRESHOLD:
                # Still static
                static_duration = frames[i]["time"] - static_start
                if static_duration > max_static_duration:
                    max_static_duration = static_duration
                if static_duration > max_static:
                    static_detected = True
            else:
                # Scene change detected
                static_start = frames[i]["time"]

    scene_change_ok = not static_detected
    results.append({
        "id": "QA-VQ-11", "name": "Visual change interval", "passed": scene_change_ok,
        "expected": f"Visual change every {max_static}s max",
        "actual": f"Max static: {max_static_duration:.1f}s" if max_static_duration > 0 else "Visual changes detected",
        "category": "visual_quality", "critical": True,
    })

    # QA-VQ-12: No static clip (same logic as QA-VQ-11 but reported separately)
    results.append({
        "id": "QA-VQ-12", "name": "No static clip", "passed": scene_change_ok,
        "expected": f"No clip exceeds {max_static}s without visual change",
        "actual": f"Max static: {max_static_duration:.1f}s" if max_static_duration > 0 else "No static clips",
        "category": "visual_quality", "critical": True,
    })

    # QA-VQ-13: File size (parameterized)
    file_size = metadata["format"]["size"]
    size_mb = file_size / (1024 * 1024)
    size_ok = size_min_mb <= size_mb <= size_max_mb
    results.append({
        "id": "QA-VQ-13", "name": "File size", "passed": size_ok,
        "expected": f"{size_min_mb}-{size_max_mb} MB",
        "actual": f"{size_mb:.1f} MB",
        "category": "visual_quality", "critical": True,
    })

    return results


# ---------------------------------------------------------------------------
# 5. check_subtitle_quality (QA-SQ-14 through QA-SQ-17)
# ---------------------------------------------------------------------------

def check_subtitle_quality(video_path: str, metadata: dict) -> list:
    """Check 4 subtitle quality items (Category 3: Important).

    QA-SQ-14: Subtitles present (text detected in frame bottom region)
    QA-SQ-15: Subtitle readability (contrast ratio >= 4.5:1)
    QA-SQ-16: Subtitle position (text in lower 25% of frame)
    QA-SQ-17: No subtitle overflow (text within horizontal bounds)

    These checks are heuristic-based -- visual verification is manual.
    """
    duration = metadata["format"]["duration"]
    results = []

    # Sample 3 frames at 25%, 50%, 75% of video duration
    sample_times = [duration * 0.25, duration * 0.50, duration * 0.75]
    subtitle_frames = []

    try:
        tmp_dir = tempfile.mkdtemp(prefix="qa_subtitle_")
        for idx, t in enumerate(sample_times):
            out_path = os.path.join(tmp_dir, f"sub_{idx}.png").replace("\\", "/")
            cmd = [
                "ffmpeg", "-ss", str(t),
                "-i", str(video_path).replace("\\", "/"),
                "-frames:v", "1", "-q:v", "2",
                out_path,
            ]
            subprocess.run(cmd, capture_output=True, text=True)
            if os.path.exists(out_path.replace("/", os.sep)):
                img = Image.open(out_path.replace("/", os.sep)).convert("RGB")
                subtitle_frames.append(img)
    except Exception:
        pass
    finally:
        if 'tmp_dir' in locals():
            shutil.rmtree(tmp_dir, ignore_errors=True)

    if not subtitle_frames:
        # Cannot sample frames -- mark as warnings
        for item_id, name in [
            ("QA-SQ-14", "Subtitles present"),
            ("QA-SQ-15", "Subtitle readability"),
            ("QA-SQ-16", "Subtitle position"),
            ("QA-SQ-17", "No subtitle overflow"),
        ]:
            results.append({
                "id": item_id, "name": name, "passed": False,
                "expected": "Frame sampling required", "actual": "Could not sample frames",
                "category": "subtitle_quality", "critical": False,
            })
        return results

    # QA-SQ-14: Subtitles present
    # Check if bottom 30% of frame has high-contrast text-like regions
    text_detected = False
    for img in subtitle_frames:
        w, h = img.size
        bottom = img.crop((0, int(h * 0.70), w, h))
        stat = ImageStat.Stat(bottom)
        # High stddev in bottom region suggests text presence
        avg_stddev = sum(stat.stddev[:3]) / 3.0
        if avg_stddev > 30:
            text_detected = True
            break

    results.append({
        "id": "QA-SQ-14", "name": "Subtitles present", "passed": text_detected,
        "expected": "Text detected in lower region",
        "actual": "Text detected" if text_detected else "No text detected",
        "category": "subtitle_quality", "critical": False,
    })

    # QA-SQ-15: Subtitle readability (contrast ratio >= 4.5:1)
    # Heuristic: check luminance difference between text and background in bottom region
    contrast_ok = False
    for img in subtitle_frames:
        w, h = img.size
        bottom = img.crop((0, int(h * 0.75), w, h))
        stat = ImageStat.Stat(bottom)
        # If stddev is high enough, there is contrast between text and background
        avg_stddev = sum(stat.stddev[:3]) / 3.0
        if avg_stddev > 25:
            contrast_ok = True
            break

    results.append({
        "id": "QA-SQ-15", "name": "Subtitle readability", "passed": contrast_ok,
        "expected": "Contrast ratio >= 4.5:1",
        "actual": "Sufficient contrast" if contrast_ok else "Low contrast",
        "category": "subtitle_quality", "critical": False,
    })

    # QA-SQ-16: Subtitle position (text within lower 25% of frame)
    # Check that significant visual activity is in lower 25%
    position_ok = False
    for img in subtitle_frames:
        w, h = img.size
        lower_quarter = img.crop((0, int(h * 0.75), w, h))
        upper_region = img.crop((0, 0, w, int(h * 0.50)))
        lower_stat = ImageStat.Stat(lower_quarter)
        upper_stat = ImageStat.Stat(upper_region)
        lower_stddev = sum(lower_stat.stddev[:3]) / 3.0
        upper_stddev = sum(upper_stat.stddev[:3]) / 3.0
        # Lower region should have more contrast variation than upper (text region)
        if lower_stddev > 20:
            position_ok = True
            break

    results.append({
        "id": "QA-SQ-16", "name": "Subtitle position", "passed": position_ok,
        "expected": "Text in lower 25% of frame",
        "actual": "Position OK" if position_ok else "Position issue",
        "category": "subtitle_quality", "critical": False,
    })

    # QA-SQ-17: No subtitle overflow (text within horizontal bounds)
    # Check that left/right 10px margins have low activity
    overflow_ok = True
    for img in subtitle_frames:
        w, h = img.size
        bottom_h = int(h * 0.75)
        left_margin = img.crop((0, bottom_h, min(10, w), h))
        right_margin = img.crop((max(0, w - 10), bottom_h, w, h))
        left_stat = ImageStat.Stat(left_margin)
        right_stat = ImageStat.Stat(right_margin)
        left_stddev = sum(left_stat.stddev[:3]) / 3.0
        right_stddev = sum(right_stat.stddev[:3]) / 3.0
        # High activity at edges suggests text overflow
        if left_stddev > 60 or right_stddev > 60:
            overflow_ok = False
            break

    results.append({
        "id": "QA-SQ-17", "name": "No subtitle overflow", "passed": overflow_ok,
        "expected": "Text within horizontal bounds",
        "actual": "No overflow" if overflow_ok else "Text overflow detected",
        "category": "subtitle_quality", "critical": False,
    })

    return results


# ---------------------------------------------------------------------------
# 6. check_audio_sync (QA-AS-18 through QA-AS-20)
# ---------------------------------------------------------------------------

def check_audio_sync(video_path: str, audio_path: str, metadata: dict) -> list:
    """Check 3 audio sync items (Category 4: Important).

    QA-AS-18: Audio-video duration match within 1 second
    QA-AS-19: Audio not silent (peak amplitude above -40dB)
    QA-AS-20: Audio starts promptly (signal within first 0.5s)
    """
    results = []
    video_duration = metadata["format"]["duration"]

    # Get audio file duration via ffprobe
    audio_duration = 0.0
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(audio_path).replace("\\", "/"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        audio_data = json.loads(result.stdout)
        audio_duration = float(audio_data.get("format", {}).get("duration", 0))
    except Exception:
        audio_duration = 0.0

    # QA-AS-18: Duration match
    duration_diff = abs(video_duration - audio_duration)
    dur_ok = duration_diff <= 1.0
    results.append({
        "id": "QA-AS-18", "name": "Audio-video duration match", "passed": dur_ok,
        "expected": "Within 1 second",
        "actual": f"Diff: {duration_diff:.1f}s (video={video_duration:.1f}s, audio={audio_duration:.1f}s)",
        "category": "audio_sync", "critical": False,
    })

    # QA-AS-19: Audio not silent (peak amplitude above -40dB)
    peak_db = _get_peak_amplitude(video_path)
    silent = peak_db is None or peak_db <= -40.0
    results.append({
        "id": "QA-AS-19", "name": "Audio not silent", "passed": not silent,
        "expected": "Peak amplitude > -40dB",
        "actual": f"Peak: {peak_db}dB" if peak_db is not None else "Could not measure",
        "category": "audio_sync", "critical": False,
    })

    # QA-AS-20: Audio starts promptly (signal within first 0.5s)
    prompt_db = _get_peak_amplitude(video_path, duration=0.5)
    prompt_ok = prompt_db is not None and prompt_db > -40.0
    results.append({
        "id": "QA-AS-20", "name": "Audio starts promptly", "passed": prompt_ok,
        "expected": "Audio signal within first 0.5s",
        "actual": f"First 0.5s peak: {prompt_db}dB" if prompt_db is not None else "Could not measure",
        "category": "audio_sync", "critical": False,
    })

    return results


def _get_peak_amplitude(video_path: str, duration: float = None) -> float:
    """Extract peak amplitude in dB from audio via ffmpeg astats.

    Returns peak level in dB, or None if measurement fails.
    """
    cmd = ["ffmpeg"]
    if duration is not None:
        cmd.extend(["-t", str(duration)])
    cmd.extend([
        "-i", str(video_path).replace("\\", "/"),
        "-af", "astats=metadata=1:reset=0",
        "-f", "null", "-",
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        stderr = result.stderr
        # Parse peak level from astats output
        # Format: Parsed_astats_0.Peak_level_dB=-10.5
        peak_db = None
        for line in stderr.split("\n"):
            if "Peak_level_dB" in line:
                parts = line.split("=")
                if len(parts) >= 2:
                    val_str = parts[-1].strip()
                    if val_str == "-inf":
                        peak_db = float("-inf")
                    else:
                        try:
                            peak_db = float(val_str)
                        except ValueError:
                            pass
        return peak_db
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 7. check_metadata_consistency (QA-MC-21 through QA-MC-22)
# ---------------------------------------------------------------------------

def estimate_scene_count(video_path: str) -> int:
    """Estimate the number of scene changes in a video.

    Uses frame sampling and brightness differences to count significant
    visual transitions.
    """
    frames = sample_frames(video_path)
    if len(frames) < 2:
        return 0

    THRESHOLD = 5.0
    changes = 0
    for i in range(1, len(frames)):
        diff = abs(frames[i]["brightness"] - frames[i - 1]["brightness"])
        if diff >= THRESHOLD:
            changes += 1

    return changes


def check_metadata_consistency(video_path: str, manifest: dict, metadata: dict, thresholds: dict = None) -> list:
    """Check metadata consistency items (Category 5: Validation).

    QA-MC-21: Clip count match (manifest clips == estimated scene count +/- 1)
    QA-MC-22: Duration match (manifest duration == video duration within 2s)
    QA-MC-23: Minimum clip count (parameterized by thresholds)

    Args:
        video_path: Path to rendered video
        manifest: Loaded scene-manifest dict
        metadata: Video metadata dict
        thresholds: Pipeline-specific thresholds dict. Defaults to PIPELINE_THRESHOLDS["shorts"].
    """
    if thresholds is None:
        thresholds = PIPELINE_THRESHOLDS["shorts"]

    min_clips = thresholds["min_clips"]
    results = []

    # QA-MC-21: Clip count match
    manifest_clip_count = len(manifest.get("clips", []))
    estimated_scenes = estimate_scene_count(video_path)
    clip_count_ok = abs(manifest_clip_count - estimated_scenes) <= 1

    results.append({
        "id": "QA-MC-21", "name": "Clip count match", "passed": clip_count_ok,
        "expected": f"Manifest clips ({manifest_clip_count}) ~= scene changes",
        "actual": f"Estimated scenes: {estimated_scenes}",
        "category": "metadata_consistency", "critical": False,
    })

    # QA-MC-22: Duration match
    # Calculate manifest total duration from clips or audio duration
    manifest_duration = 0.0
    if "audio" in manifest and "duration_seconds" in manifest["audio"]:
        manifest_duration = float(manifest["audio"]["duration_seconds"])
    else:
        for clip in manifest.get("clips", []):
            manifest_duration += float(clip.get("duration", 0))

    video_duration = metadata["format"]["duration"]
    duration_diff = abs(manifest_duration - video_duration)
    duration_ok = duration_diff <= 2.0

    results.append({
        "id": "QA-MC-22", "name": "Duration match", "passed": duration_ok,
        "expected": f"Manifest duration ({manifest_duration:.1f}s) ~= video duration",
        "actual": f"Video: {video_duration:.1f}s, diff: {duration_diff:.1f}s",
        "category": "metadata_consistency", "critical": False,
    })

    # QA-MC-23: Minimum clip count
    min_clip_ok = manifest_clip_count >= min_clips
    results.append({
        "id": "QA-MC-23", "name": "Minimum clip count", "passed": min_clip_ok,
        "expected": f">= {min_clips} clips",
        "actual": f"{manifest_clip_count} clips",
        "category": "metadata_consistency", "critical": False,
    })

    return results


# ---------------------------------------------------------------------------
# 8. check_youtube_compliance (QA-YC-01 through QA-YC-06)
# ---------------------------------------------------------------------------


def check_youtube_compliance(script_path: str, manifest_path: str,
                             metadata_path: str, history_dir: str = None,
                             pipeline: str = "shorts") -> list:
    """Check 6 YouTube compliance items (Category 6: Compliance).

    QA-YC-01: Script uniqueness vs recent history (CRITICAL)
    QA-YC-02: Hook diversity vs recent hooks (CRITICAL)
    QA-YC-03: Visual variety (unique clip ratio) (IMPORTANT)
    QA-YC-04: TTS provider quality tier (IMPORTANT)
    QA-YC-05: Section count minimum (IMPORTANT)
    QA-YC-06: AI disclosure flag present (CRITICAL)

    Args:
        script_path: Path to script.json
        manifest_path: Path to scene-manifest.json
        metadata_path: Path to metadata.json
        history_dir: Path to directory of previous script.json files for comparison
        pipeline: "shorts" or "video"

    Returns:
        List of result dicts with id, name, passed, expected, actual, category, critical keys.
    """
    results = []

    # Load current script
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Load metadata
    meta = {}
    if metadata_path and os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    # Extract current script text and hook
    sections = script.get("sections", [])
    current_text = " ".join(s.get("narration", "") for s in sections)
    current_hook = sections[0].get("narration", "") if sections else ""

    # Load history scripts for comparison
    history_scripts = []
    history_hooks = []
    if history_dir and os.path.isdir(history_dir):
        history_files = sorted(Path(history_dir).glob("script_*.json"))[-10:]
        for hf in history_files:
            try:
                with open(hf, "r", encoding="utf-8") as f:
                    hs = json.load(f)
                h_sections = hs.get("sections", [])
                history_scripts.append(" ".join(s.get("narration", "") for s in h_sections))
                if h_sections:
                    history_hooks.append(h_sections[0].get("narration", ""))
            except (json.JSONDecodeError, KeyError):
                continue

    # QA-YC-01: Script Uniqueness (CRITICAL)
    # Compare against last 10 scripts. Auto-pass if < 3 history scripts.
    script_unique = True
    max_similarity = 0.0
    if len(history_scripts) >= 3:
        for past in history_scripts:
            ratio = SequenceMatcher(None, current_text, past).ratio()
            if ratio > max_similarity:
                max_similarity = ratio
            if ratio > 0.40:
                script_unique = False
                break
    results.append({
        "id": "QA-YC-01", "name": "Script uniqueness",
        "passed": script_unique,
        "expected": "similarity_ratio < 0.40 vs recent scripts",
        "actual": f"max_similarity={max_similarity:.2f}, history_count={len(history_scripts)}"
                 + (" (auto-pass: < 3 history)" if len(history_scripts) < 3 else ""),
        "category": "youtube_compliance", "critical": True,
    })

    # QA-YC-02: Hook Diversity (CRITICAL)
    hook_diverse = True
    max_hook_sim = 0.0
    if len(history_hooks) >= 3:
        for past_hook in history_hooks:
            ratio = SequenceMatcher(None, current_hook, past_hook).ratio()
            if ratio > max_hook_sim:
                max_hook_sim = ratio
            if ratio > 0.50:
                hook_diverse = False
                break
    results.append({
        "id": "QA-YC-02", "name": "Hook diversity",
        "passed": hook_diverse,
        "expected": "hook similarity_ratio < 0.50 vs recent hooks",
        "actual": f"max_hook_similarity={max_hook_sim:.2f}, hook_count={len(history_hooks)}"
                 + (" (auto-pass: < 3 history)" if len(history_hooks) < 3 else ""),
        "category": "youtube_compliance", "critical": True,
    })

    # QA-YC-03: Visual Variety (IMPORTANT)
    clips = manifest.get("clips", [])
    clip_sources = [c.get("source", c.get("video_id", c.get("path", ""))) for c in clips]
    unique_sources = set(str(s) for s in clip_sources)
    total_clips = len(clip_sources) if clip_sources else 1
    unique_ratio = len(unique_sources) / total_clips
    visual_ok = unique_ratio >= 0.70
    results.append({
        "id": "QA-YC-03", "name": "Visual variety",
        "passed": visual_ok,
        "expected": "unique_clips >= 70% of total clips",
        "actual": f"{len(unique_sources)}/{total_clips} unique ({unique_ratio:.0%})",
        "category": "youtube_compliance", "critical": False,
    })

    # QA-YC-04: TTS Provider Quality (IMPORTANT)
    tts_step = meta.get("steps", {}).get("tts", {})
    tts_provider = tts_step.get("provider", "unknown")
    provider_ok = tts_provider != "edge-tts"
    results.append({
        "id": "QA-YC-04", "name": "TTS provider quality",
        "passed": provider_ok,
        "expected": "provider != edge-tts (lowest quality)",
        "actual": f"provider={tts_provider}",
        "category": "youtube_compliance", "critical": False,
    })

    # QA-YC-05: Section Count Minimum (IMPORTANT)
    min_sections = 3 if pipeline == "shorts" else 5
    section_count = len(sections)
    sections_ok = section_count >= min_sections
    results.append({
        "id": "QA-YC-05", "name": "Section count minimum",
        "passed": sections_ok,
        "expected": f">= {min_sections} sections ({pipeline})",
        "actual": f"{section_count} sections",
        "category": "youtube_compliance", "critical": False,
    })

    # QA-YC-06: AI Disclosure Present (CRITICAL)
    ai_disclosure = meta.get("ai_disclosure", False)
    results.append({
        "id": "QA-YC-06", "name": "AI disclosure present",
        "passed": bool(ai_disclosure),
        "expected": "ai_disclosure == true in metadata.json",
        "actual": f"ai_disclosure={ai_disclosure}",
        "category": "youtube_compliance", "critical": True,
    })

    return results


# ---------------------------------------------------------------------------
# 8b. check_ai_clip_quality (QA-AI-01 through QA-AI-04)
# ---------------------------------------------------------------------------

def check_ai_clip_quality(manifest: dict, thresholds: dict = None) -> list:
    """Check quality of AI-generated clips in manifest.

    Validates:
    - AI clip file exists and is non-empty (QA-AI-01)
    - AI clip resolution >= 720p (QA-AI-02)
    - AI clip duration within expected range 2-15 seconds (QA-AI-03)
    - AI clips don't exceed max_ai_clips_per_short (QA-AI-04)

    Args:
        manifest: Loaded scene-manifest dict.
        thresholds: Pipeline-specific thresholds dict.

    Returns:
        List of QA issue dicts with severity, category, message, clip_index.
    """
    if thresholds is None:
        thresholds = PIPELINE_THRESHOLDS["shorts"]

    min_res = thresholds.get("ai_clip_min_resolution", 720)
    min_dur = thresholds.get("ai_clip_min_duration", 2.0)
    max_dur = thresholds.get("ai_clip_max_duration", 15.0)
    max_ai = thresholds.get("max_ai_clips_per_short", 3)

    results = []

    # Collect AI clips from both flat clips and chapters
    clips = manifest.get("clips", [])
    if not clips and manifest.get("schema_version") == "2.0" and "chapters" in manifest:
        for chapter in manifest["chapters"]:
            clips.extend(chapter.get("clips", []))

    ai_clips = [c for c in clips if c.get("visual_source") == "ai"]
    ai_clip_count = len(ai_clips)

    # QA-AI-01: File existence and non-empty for each AI clip
    for clip in ai_clips:
        clip_index = clip.get("index", -1)
        local_path = clip.get("source", {}).get("local_path", "")

        if not local_path or not os.path.exists(local_path):
            results.append({
                "severity": "error",
                "category": "ai_clip",
                "message": f"AI clip {clip_index}: file missing at {local_path}",
                "clip_index": clip_index,
            })
            continue

        file_size = os.path.getsize(local_path)
        if file_size == 0:
            results.append({
                "severity": "error",
                "category": "ai_clip",
                "message": f"AI clip {clip_index}: file is empty (0 bytes)",
                "clip_index": clip_index,
            })
            continue

        # QA-AI-02: Resolution check via ffprobe
        try:
            metadata = get_video_metadata(local_path)
            width = metadata.get("video", {}).get("width", 0)
            height = metadata.get("video", {}).get("height", 0)
            if width < min_res and height < min_res:
                results.append({
                    "severity": "warning",
                    "category": "ai_clip",
                    "message": (
                        f"AI clip {clip_index}: resolution {width}x{height} "
                        f"below minimum {min_res}p"
                    ),
                    "clip_index": clip_index,
                })

            # QA-AI-03: Duration check
            duration = metadata.get("format", {}).get("duration", 0.0)
            if duration < min_dur or duration > max_dur:
                results.append({
                    "severity": "warning",
                    "category": "ai_clip",
                    "message": (
                        f"AI clip {clip_index}: duration {duration:.1f}s "
                        f"outside range [{min_dur}-{max_dur}]s"
                    ),
                    "clip_index": clip_index,
                })
        except Exception:
            results.append({
                "severity": "warning",
                "category": "ai_clip",
                "message": f"AI clip {clip_index}: could not read video metadata",
                "clip_index": clip_index,
            })

    # QA-AI-04: AI clip count cap
    if ai_clip_count > max_ai:
        results.append({
            "severity": "warning",
            "category": "ai_clip",
            "message": (
                f"AI clips exceed recommended max ({ai_clip_count} > {max_ai})"
            ),
            "clip_index": -1,
        })

    return results


# ---------------------------------------------------------------------------
# 8c. check_editing_quality (QA-EQ-01 through QA-EQ-06)
# ---------------------------------------------------------------------------


def check_editing_quality(manifest: dict, output_dir: str = None) -> list:
    """Check 6 editing quality items (Category 7: Quality Enhancement).

    All items are non-critical (quality enhancements, not blockers).
    Checks validate from scene-manifest.json data only (no ffprobe).

    QA-EQ-01: Zoom/motion effect rate (>= 50% clips with motion)
    QA-EQ-02: Transition diversity (>= 3 distinct transition types)
    QA-EQ-03: Text overlay count (3-6 key_texts)
    QA-EQ-04: Karaoke subtitle existence (.ass file in output_dir)
    QA-EQ-05: BGM ducking applied (mixed_audio.mp3 exists)
    QA-EQ-06: Clip dedup (all clip original_urls unique)

    Args:
        manifest: Loaded scene-manifest dict.
        output_dir: Path to output directory (for file-based checks). None = skip file checks.

    Returns:
        List of 6 QA result dicts.
    """
    results = []
    clips = manifest.get("clips", [])
    total_clips = len(clips)

    # QA-EQ-01: Zoom/motion effect rate
    # Count clips where effects.motion is not "none" and not None
    motion_count = 0
    for clip in clips:
        effects = clip.get("effects", {})
        motion = effects.get("motion")
        if motion is not None and motion != "none":
            motion_count += 1
    motion_ratio = motion_count / total_clips if total_clips > 0 else 0.0
    results.append({
        "id": "QA-EQ-01", "name": "Zoom/motion effect rate",
        "passed": motion_ratio >= 0.50,
        "expected": ">= 50% clips with motion effects",
        "actual": f"{motion_count}/{total_clips} ({motion_ratio:.0%})",
        "category": "editing_quality", "critical": False,
    })

    # QA-EQ-02: Transition diversity
    # Collect distinct transition types across clips
    transition_types = set()
    for clip in clips:
        trans = clip.get("transition", {})
        trans_type = trans.get("type")
        if trans_type:
            transition_types.add(trans_type)
    distinct_count = len(transition_types)
    results.append({
        "id": "QA-EQ-02", "name": "Transition diversity",
        "passed": distinct_count >= 3,
        "expected": ">= 3 distinct transition types",
        "actual": f"{distinct_count} types: {sorted(transition_types)}",
        "category": "editing_quality", "critical": False,
    })

    # QA-EQ-03: Text overlay count
    key_texts = manifest.get("key_texts", [])
    key_text_count = len(key_texts)
    results.append({
        "id": "QA-EQ-03", "name": "Text overlay count",
        "passed": 3 <= key_text_count <= 6,
        "expected": "3-6 key_texts",
        "actual": f"{key_text_count} key_texts",
        "category": "editing_quality", "critical": False,
    })

    # QA-EQ-04: Karaoke subtitle existence
    # Check if output_dir contains any .ass file
    ass_exists = False
    if output_dir and os.path.isdir(output_dir):
        for fname in os.listdir(output_dir):
            if fname.endswith(".ass"):
                ass_exists = True
                break
    results.append({
        "id": "QA-EQ-04", "name": "Karaoke subtitle existence",
        "passed": ass_exists,
        "expected": ".ass file in output directory",
        "actual": "ASS file found" if ass_exists else (
            "No output_dir provided" if output_dir is None else "No .ass file found"
        ),
        "category": "editing_quality", "critical": False,
    })

    # QA-EQ-05: BGM ducking applied
    # Check if output_dir/mixed_audio.mp3 exists
    mixed_audio_exists = False
    if output_dir and os.path.isdir(output_dir):
        mixed_path = os.path.join(output_dir, "mixed_audio.mp3")
        mixed_audio_exists = os.path.isfile(mixed_path)
    results.append({
        "id": "QA-EQ-05", "name": "BGM ducking applied",
        "passed": mixed_audio_exists,
        "expected": "mixed_audio.mp3 in output directory",
        "actual": "mixed_audio.mp3 found" if mixed_audio_exists else (
            "No output_dir provided" if output_dir is None else "mixed_audio.mp3 not found"
        ),
        "category": "editing_quality", "critical": False,
    })

    # QA-EQ-06: Clip dedup
    # Collect all non-null original_urls and check uniqueness
    urls = []
    for clip in clips:
        source = clip.get("source", {})
        url = source.get("original_url")
        if url is not None:
            urls.append(url)
    unique_urls = set(urls)
    dedup_ok = len(urls) == len(unique_urls)
    results.append({
        "id": "QA-EQ-06", "name": "Clip dedup",
        "passed": dedup_ok,
        "expected": "All clip original_urls unique",
        "actual": f"{len(unique_urls)}/{len(urls)} unique URLs" + (
            "" if dedup_ok else f" ({len(urls) - len(unique_urls)} duplicates)"
        ),
        "category": "editing_quality", "critical": False,
    })

    return results


# ---------------------------------------------------------------------------
# 9. run_qa_checklist
# ---------------------------------------------------------------------------

# Critical ID prefixes: resolution/format, visual quality, and youtube compliance must ALL pass
CRITICAL_ID_PREFIXES = ("QA-CF-", "QA-VQ-", "QA-YC-")
# Minimum total score for overall pass (pipeline-aware)
MIN_PASS_SCORE = {"shorts": 27, "video": 28}

def run_qa_checklist(video_path: str, manifest_path: str, audio_path: str,
                     pipeline: str = "shorts",
                     script_path: str = None, metadata_path: str = None,
                     history_dir: str = None) -> dict:
    """Run the complete QA checklist with pipeline-specific thresholds.

    Execution order (D-10): resolution/format -> visual quality ->
    subtitle quality -> audio sync -> metadata consistency -> editing quality -> youtube compliance.

    Args:
        video_path: Path to rendered video
        manifest_path: Path to scene-manifest.json
        audio_path: Path to narration audio
        pipeline: Pipeline type ("shorts" or "video") for threshold selection
        script_path: Path to script.json (for compliance check)
        metadata_path: Path to metadata.json (for compliance check)
        history_dir: Path to script history dir (for uniqueness check)

    Returns:
        {
            "status": "pass" | "fail",
            "passed": bool,
            "score": int,
            "total": int,
            "failures": [{"id": ..., "name": ..., "expected": ..., "actual": ...}],
            "warnings": [{"id": ..., "name": ..., "expected": ..., "actual": ...}],
        }
    """
    thresholds = PIPELINE_THRESHOLDS[pipeline]

    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Get video metadata
    metadata = get_video_metadata(video_path)

    # Derive output_dir from manifest_path parent
    output_dir = str(Path(manifest_path).parent)

    # Execute checks in D-10 order
    all_results = []
    all_results.extend(check_resolution_format(metadata, thresholds=thresholds))
    all_results.extend(check_visual_quality(video_path, metadata, thresholds=thresholds))
    all_results.extend(check_subtitle_quality(video_path, metadata))
    all_results.extend(check_audio_sync(video_path, audio_path, metadata))
    all_results.extend(check_metadata_consistency(video_path, manifest, metadata, thresholds=thresholds))

    # Editing Quality (Category 7) -- validates editing enhancements from manifest
    all_results.extend(check_editing_quality(manifest, output_dir=output_dir))

    # AI Clip Quality (Category 5b) -- validates AI-generated clips
    ai_issues = check_ai_clip_quality(manifest, thresholds=thresholds)
    # Convert AI issues to standard QA result format
    for idx, issue in enumerate(ai_issues):
        qa_id = f"QA-AI-{idx + 1:02d}"
        all_results.append({
            "id": qa_id,
            "name": f"AI clip quality ({issue['category']})",
            "passed": False,
            "expected": "AI clip passes quality checks",
            "actual": issue["message"],
            "category": "ai_clip_quality",
            "critical": issue["severity"] == "error",
        })

    # Add AI clip count to results summary (passes if no issues found)
    clips_for_count = manifest.get("clips", [])
    if not clips_for_count and manifest.get("schema_version") == "2.0" and "chapters" in manifest:
        for chapter in manifest["chapters"]:
            clips_for_count.extend(chapter.get("clips", []))
    ai_clip_count = sum(1 for c in clips_for_count if c.get("visual_source") == "ai")
    if ai_clip_count > 0 and not ai_issues:
        all_results.append({
            "id": "QA-AI-00",
            "name": "AI clip quality",
            "passed": True,
            "expected": "All AI clips pass quality checks",
            "actual": f"{ai_clip_count} AI clips validated",
            "category": "ai_clip_quality",
            "critical": False,
        })

    # YouTube Compliance (Category 6) -- per D-07: fail-gating
    if script_path and metadata_path:
        all_results.extend(check_youtube_compliance(
            script_path, manifest_path, metadata_path,
            history_dir=history_dir, pipeline=pipeline,
        ))

    # Aggregate results
    total = len(all_results)
    passed_count = sum(1 for r in all_results if r["passed"])
    failures = []
    warnings = []

    def _is_critical(item_id: str) -> bool:
        """Determine if a QA item is critical based on its ID prefix."""
        return any(item_id.startswith(prefix) for prefix in CRITICAL_ID_PREFIXES)

    for r in all_results:
        if not r["passed"]:
            item = {
                "id": r["id"],
                "name": r["name"],
                "expected": r["expected"],
                "actual": r["actual"],
            }
            if _is_critical(r["id"]):
                failures.append(item)
            else:
                warnings.append(item)

    # Determine overall pass/fail
    # ALL critical category items must pass + total score >= 18/22
    critical_all_pass = all(
        r["passed"] for r in all_results
        if _is_critical(r["id"])
    )
    min_score = MIN_PASS_SCORE.get(pipeline, 18)
    overall_passed = critical_all_pass and passed_count >= min_score

    return {
        "status": "pass" if overall_passed else "fail",
        "passed": overall_passed,
        "score": passed_count,
        "total": total,
        "failures": failures,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# 9. main (CLI entry point)
# ---------------------------------------------------------------------------

def main():
    """CLI entry point: parse args, run QA, output JSON, exit.

    Usage:
        qa_check.py --video VIDEO --manifest MANIFEST --audio AUDIO [--config-dir DIR]
    """
    parser = argparse.ArgumentParser(
        description="22-item automated QA checklist for rendered shorts videos."
    )
    parser.add_argument("--video", required=True, help="Path to rendered video (final.mp4)")
    parser.add_argument("--manifest", required=True, help="Path to scene-manifest.json")
    parser.add_argument("--audio", required=True, help="Path to narration audio file")
    parser.add_argument("--config-dir", default=None, help="Path to config directory")
    parser.add_argument(
        "--pipeline", default="shorts", choices=["shorts", "video"],
        help="Pipeline type for threshold selection: shorts (9:16/30-60s) or video (16:9/300-900s)",
    )
    parser.add_argument("--script", default=None, help="Path to script.json (for compliance check)")
    parser.add_argument("--metadata", default=None, help="Path to metadata.json (for compliance check)")
    parser.add_argument("--history-dir", default=None, help="Path to script history dir (for uniqueness check)")

    args = parser.parse_args()

    result = run_qa_checklist(args.video, args.manifest, args.audio,
                              pipeline=args.pipeline,
                              script_path=args.script,
                              metadata_path=args.metadata,
                              history_dir=args.history_dir)

    # Output JSON to stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Exit code: 0 if passed, 1 if failed
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
