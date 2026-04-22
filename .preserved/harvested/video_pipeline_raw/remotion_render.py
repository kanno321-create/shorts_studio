"""Remotion graphic card renderer for the video pipeline.

Reads scene-manifest.json, identifies clips with source.type == "remotion",
writes per-clip props JSON files, invokes `npx remotion render` for each,
and updates the manifest with rendered local_path values.

Exit codes:
    0 = success (at least some clips rendered, or no remotion clips)
    1 = error (all remotion clips failed, or fatal error)

Outputs:
    - Rendered .mp4 clips in output-dir (e.g., output/stock/card_000.mp4)
    - Updated scene-manifest.json with local_path for rendered clips
    - JSON result to stdout: {status, rendered, failed, clips: [...]}

CLI:
    remotion_render.py --manifest MANIFEST --output-dir OUTPUT_DIR --project-root PROJECT_ROOT
"""
import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [remotion_render] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def find_remotion_clips(manifest: dict) -> list:
    """Find all clips in manifest where source.type == 'remotion'.

    Supports both v1.0 flat clips and v2.0 chapters structure.

    Args:
        manifest: Parsed scene-manifest.json dict.

    Returns:
        List of (clip_dict, chapter_index, clip_index_in_chapter) tuples.
        For flat clips, chapter_index is None.
    """
    results = []

    # v2.0 chapters structure
    if manifest.get("schema_version") == "2.0" and "chapters" in manifest:
        for ch_idx, chapter in enumerate(manifest["chapters"]):
            for cl_idx, clip in enumerate(chapter.get("clips", [])):
                if clip.get("source", {}).get("type") == "remotion":
                    results.append((clip, ch_idx, cl_idx))

    # v1.0 flat clips (or v2.0 backward-compat flat array)
    for cl_idx, clip in enumerate(manifest.get("clips", [])):
        if clip.get("source", {}).get("type") == "remotion":
            results.append((clip, None, cl_idx))

    return results


def write_props_file(clip: dict, output_dir: str, index: int, fps: int = 30) -> str:
    """Write Remotion props JSON file for a single clip.

    Merges graphic_props with calculated durationInFrames.
    Uses ensure_ascii=False for Korean text preservation.

    Args:
        clip: Clip dict from scene-manifest.json.
        output_dir: Directory to write props file.
        index: Clip index for filename.
        fps: Frames per second (default 30).

    Returns:
        Path to the written props file.
    """
    source = clip["source"]
    graphic_props = source.get("graphic_props", {})
    duration = clip.get("duration", 3.0)
    duration_in_frames = int(duration * fps)

    props = {**graphic_props, "durationInFrames": duration_in_frames}

    os.makedirs(output_dir, exist_ok=True)
    props_path = os.path.join(output_dir, f"card_{index:03d}_props.json")

    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2, ensure_ascii=False)

    logger.info("Wrote props file: %s (durationInFrames=%d)", props_path, duration_in_frames)
    return props_path


def build_render_command(
    project_root: str,
    composition_id: str,
    output_path: str,
    props_file: str,
    width: int,
    height: int,
    fps: int,
    timeout: int,
) -> list:
    """Build npx remotion render command list.

    All paths use forward slashes for Windows compatibility.

    Args:
        project_root: Project root directory.
        composition_id: Remotion composition ID (e.g., 'TitleCard').
        output_path: Output .mp4 file path.
        props_file: Path to props JSON file.
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frames per second.
        timeout: Render timeout in milliseconds.

    Returns:
        Command list suitable for subprocess.run().
    """
    entry_point = os.path.join(project_root, "remotion", "src", "index.ts")
    # Convert all paths to forward slashes for npx on Windows
    entry_point = entry_point.replace("\\", "/")
    output_path_safe = output_path.replace("\\", "/")
    props_file_safe = props_file.replace("\\", "/")

    return [
        "npx", "remotion", "render",
        entry_point,
        composition_id,
        output_path_safe,
        f"--props={props_file_safe}",
        f"--width={width}",
        f"--height={height}",
        f"--fps={fps}",
        f"--timeout={timeout}",
        "--codec=h264",
    ]


def render_clip(
    clip: dict,
    index: int,
    output_dir: str,
    project_root: str,
    width: int,
    height: int,
    fps: int,
    is_first_render: bool,
) -> dict:
    """Render a single Remotion clip.

    Args:
        clip: Clip dict from scene-manifest.json.
        index: Global clip index.
        output_dir: Directory for rendered .mp4 files.
        project_root: Project root for Remotion entry point.
        width: Video width.
        height: Video height.
        fps: Frames per second.
        is_first_render: True for first render (longer timeout for Chrome download).

    Returns:
        Dict with status, output_path, duration_seconds, and error (if failed).
    """
    source = clip["source"]
    composition_id = source.get("composition_id", "TitleCard")
    output_path = os.path.join(output_dir, f"card_{index:03d}.mp4")

    # Write props file
    props_file = write_props_file(clip, output_dir, index, fps)

    # First render gets longer timeout (Chrome headless download)
    timeout = 120000 if is_first_render else 60000

    cmd = build_render_command(
        project_root, composition_id, output_path, props_file,
        width, height, fps, timeout,
    )

    logger.info("Rendering clip %d: composition=%s, timeout=%dms", index, composition_id, timeout)
    logger.info("Command: %s", " ".join(cmd))

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout / 1000 + 30,  # subprocess timeout slightly longer than Remotion timeout
        )
        elapsed = time.time() - start_time
        logger.info("Clip %d render completed in %.1fs (exit code %d)", index, elapsed, result.returncode)

        if result.returncode != 0:
            logger.error("Clip %d render FAILED: %s", index, result.stderr[-500:] if result.stderr else "no stderr")
            return {
                "status": "failed",
                "index": index,
                "composition_id": composition_id,
                "error": result.stderr[-500:] if result.stderr else "unknown error",
                "duration_seconds": round(elapsed, 1),
            }

        # Success — update clip source with local_path
        clip["source"]["local_path"] = output_path

        # Clean up props file on success
        if os.path.exists(props_file):
            os.remove(props_file)
            logger.info("Cleaned up props file: %s", props_file)

        return {
            "status": "success",
            "index": index,
            "composition_id": composition_id,
            "output_path": output_path,
            "duration_seconds": round(elapsed, 1),
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        logger.error("Clip %d render TIMED OUT after %.1fs", index, elapsed)
        return {
            "status": "failed",
            "index": index,
            "composition_id": composition_id,
            "error": f"Render timed out after {elapsed:.1f}s",
            "duration_seconds": round(elapsed, 1),
        }


# ---------------------------------------------------------------------------
# ShortsVideo full render — replaces FFmpeg video_assemble + layout_compose
# ---------------------------------------------------------------------------

# Channel presets for ShortsVideo composition
# Channel presets — config/channels.yaml 싱글 소스 (knowledge 누락 해결)
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent / "config"))
try:
    import channel_registry as _cr
    CHANNEL_PRESETS = _cr.remotion_presets()
except Exception:
    CHANNEL_PRESETS = {}


def validate_shorts_props(props: dict) -> None:
    """Validate required fields in ShortsVideo props before render.

    Args:
        props: Props dict matching shortsVideoSchema.

    Raises:
        ValueError: If any required field is missing or invalid.
    """
    # audioSrc: non-empty string
    audio_src = props.get("audioSrc")
    if not isinstance(audio_src, str) or not audio_src:
        raise ValueError(f"audioSrc must be a non-empty string, got: {audio_src!r}")

    # titleLine1: non-empty string
    title_line1 = props.get("titleLine1")
    if not isinstance(title_line1, str) or not title_line1:
        raise ValueError(f"titleLine1 must be a non-empty string, got: {title_line1!r}")

    # channelName: non-empty string
    channel_name = props.get("channelName")
    if not isinstance(channel_name, str) or not channel_name:
        raise ValueError(f"channelName must be a non-empty string, got: {channel_name!r}")

    # durationInFrames: positive integer
    duration = props.get("durationInFrames")
    if not isinstance(duration, int) or duration <= 0:
        raise ValueError(f"durationInFrames must be a positive integer, got: {duration!r}")

    # subtitles: must be a list (can be empty)
    subtitles = props.get("subtitles")
    if not isinstance(subtitles, list):
        raise ValueError(f"subtitles must be a list, got: {type(subtitles).__name__}")

    logger.info("Props validation passed: audioSrc=%s, durationInFrames=%d, subtitles=%d cues",
                audio_src, duration, len(subtitles))


def get_audio_duration_ffprobe(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe.

    Args:
        audio_path: Path to audio file.

    Returns:
        Duration in seconds, or 0.0 on failure.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            logger.info("ffprobe audio duration: %.3fs (%s)", duration, audio_path)
            return duration
        else:
            logger.warning("ffprobe failed (exit %d): %s", result.returncode,
                         result.stderr.strip() if result.stderr else "no output")
            return 0.0
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.warning("ffprobe error for %s: %s", audio_path, e)
        return 0.0


def cleanup_remotion_assets(project_root: str, job_id: str) -> None:
    """Delete remotion/public/<job_id>/ directory after successful render.

    Safety check: only deletes directories inside remotion/public/.

    Args:
        project_root: Project root directory.
        job_id: Job identifier (directory name under remotion/public/).
    """
    import shutil

    public_base = os.path.join(project_root, "remotion", "public")
    target_dir = os.path.join(public_base, job_id)

    # Safety: resolve paths and verify target is inside remotion/public/
    resolved_base = os.path.realpath(public_base)
    resolved_target = os.path.realpath(target_dir)

    if not resolved_target.startswith(resolved_base + os.sep):
        logger.error("Safety check failed: %s is not inside %s — skipping cleanup",
                     resolved_target, resolved_base)
        return

    if not os.path.isdir(resolved_target):
        logger.info("Cleanup: directory does not exist, nothing to do: %s", resolved_target)
        return

    shutil.rmtree(resolved_target)
    logger.info("Cleaned up remotion assets: %s", resolved_target)


def prepare_remotion_assets(
    output_dir: str,
    project_root: str,
    video_path: str | None = None,
    audio_path: str | None = None,
    image_path: str | None = None,
    video_paths: list[str] | None = None,
    image_paths: list[str] | None = None,
    bgm_path: str | None = None,
    channel: str | None = None,
    *,
    scene_clips: list[dict] | None = None,
) -> dict:
    """Copy pipeline assets to remotion/public/<job_id>/ for staticFile() access.

    Args:
        output_dir: Pipeline output directory (used as job ID).
        project_root: Project root directory.
        video_path: Path to main video clip (optional, legacy single-source).
        audio_path: Path to narration.mp3.
        image_path: Path to main image (optional, legacy single-source).
        video_paths: List of video clip paths (multi-clip mode).
        image_paths: List of image paths (multi-clip mode).
        bgm_path: Explicit BGM file path (optional, auto-selects from channel if None).
        channel: Channel name for auto BGM selection ("humor", "politics", "trend").

    Returns:
        Dict with relative asset paths (relative to remotion/public/).
    """
    import shutil

    # Create a job-specific folder in remotion/public/
    job_id = os.path.basename(os.path.normpath(output_dir))
    public_dir = os.path.join(project_root, "remotion", "public", job_id)
    os.makedirs(public_dir, exist_ok=True)

    assets: dict = {"job_id": job_id, "clips": []}

    if audio_path and os.path.exists(audio_path):
        dest = os.path.join(public_dir, "narration.mp3")
        shutil.copy2(audio_path, dest)
        assets["audioSrc"] = f"{job_id}/narration.mp3"
        logger.info("Copied audio: %s → %s", audio_path, dest)

    # Multi-clip mode: copy all videos and images
    clip_index = 0

    if scene_clips:
        # Phase 6-7: Ordered clips with metadata (movement, transition)
        for sc in scene_clips:
            sc_path = sc.get("path", "")
            if not sc_path or not os.path.exists(sc_path):
                continue
            ext = os.path.splitext(sc_path)[1]
            dest = os.path.join(public_dir, f"clip_{clip_index:03d}{ext}")
            shutil.copy2(sc_path, dest)
            # Normalize clip type: Remotion only understands "video" and "image"
            raw_type = sc.get("type", "image")
            if ext.lower() in (".mp4", ".mov", ".webm", ".avi"):
                clip_type = "video"
            elif raw_type in ("video", "signature"):
                clip_type = "video"
            else:
                clip_type = "image"
            clip_entry: dict = {
                "type": clip_type,
                "src": f"{job_id}/clip_{clip_index:03d}{ext}",
            }
            if sc.get("movement"):
                clip_entry["movement"] = sc["movement"]
            if sc.get("transition"):
                clip_entry["transition"] = sc["transition"]
            # Phase 42: pass-through real_footage fields (sceneType, bracketCaption, etc.)
            for opt_key in ("sceneType", "speakerLines", "bracketCaption",
                            "bracketCaptionStartMs", "bracketCaptionEndMs",
                            "realFootageSubtitles", "graphicConfig"):
                if opt_key in sc:
                    clip_entry[opt_key] = sc[opt_key]
            # Phase 42: pass-through source metadata (type, license, youtube_id, mosaic_applied)
            if sc.get("source"):
                clip_entry["source"] = sc["source"]
            assets["clips"].append(clip_entry)
            logger.info("Copied scene clip %d (%s): %s → %s",
                        clip_index, clip_entry["type"], sc_path, dest)
            clip_index += 1
    else:
        if video_paths:
            for vp in video_paths:
                if vp and os.path.exists(vp):
                    ext = os.path.splitext(vp)[1]
                    dest = os.path.join(public_dir, f"clip_{clip_index:03d}{ext}")
                    shutil.copy2(vp, dest)
                    assets["clips"].append({
                        "type": "video",
                        "src": f"{job_id}/clip_{clip_index:03d}{ext}",
                    })
                    logger.info("Copied video clip %d: %s → %s", clip_index, vp, dest)
                    clip_index += 1

        if image_paths:
            for ip in image_paths:
                if ip and os.path.exists(ip):
                    ext = os.path.splitext(ip)[1]
                    dest = os.path.join(public_dir, f"clip_{clip_index:03d}{ext}")
                    shutil.copy2(ip, dest)
                    assets["clips"].append({
                        "type": "image",
                        "src": f"{job_id}/clip_{clip_index:03d}{ext}",
                    })
                    logger.info("Copied image clip %d: %s → %s", clip_index, ip, dest)
                    clip_index += 1

    # Legacy single-source fallback (when no multi-clip)
    if not assets["clips"]:
        if video_path and os.path.exists(video_path):
            ext = os.path.splitext(video_path)[1]
            dest = os.path.join(public_dir, f"video{ext}")
            shutil.copy2(video_path, dest)
            assets["videoSrc"] = f"{job_id}/video{ext}"
            logger.info("Copied video: %s → %s", video_path, dest)

        if image_path and os.path.exists(image_path):
            ext = os.path.splitext(image_path)[1]
            dest = os.path.join(public_dir, f"image{ext}")
            shutil.copy2(image_path, dest)
            assets["imageSrc"] = f"{job_id}/image{ext}"
            logger.info("Copied image: %s → %s", image_path, dest)

    # BGM: explicit path > channel default from remotion/public/bgm/{channel}.mp3
    resolved_bgm = bgm_path
    if not resolved_bgm and channel:
        default_bgm = os.path.join(project_root, "remotion", "public", "bgm", f"{channel}.mp3")
        if os.path.exists(default_bgm):
            resolved_bgm = default_bgm
            logger.info("Auto-selected default BGM for channel '%s': %s", channel, default_bgm)

    if resolved_bgm and os.path.exists(resolved_bgm):
        dest = os.path.join(public_dir, "bgm.mp3")
        shutil.copy2(resolved_bgm, dest)
        assets["bgmSrc"] = f"{job_id}/bgm.mp3"
        assets["bgmVolume"] = 0.2
        logger.info("Copied BGM: %s → %s", resolved_bgm, dest)

    logger.info("Prepared %d clips for Remotion render", len(assets["clips"]))
    return assets


def build_shorts_props(
    script: dict,
    channel: str,
    assets: dict,
    subtitle_json_path: str | None = None,
    audio_duration: float = 30.0,
    fps: int = 30,
    blueprint: dict | None = None,
    *,
    visual_spec_provided: bool = False,
) -> dict:
    """Build ShortsVideo props JSON from pipeline artifacts.

    Args:
        script: Parsed script.json dict.
        channel: Channel name ("humor", "politics", "trend").
        assets: Asset paths dict from prepare_remotion_assets().
        subtitle_json_path: Path to subtitles_remotion.json.
        audio_duration: Audio duration in seconds.
        fps: Frames per second.
        blueprint: Blueprint dict with title_display (accent_words, accent_color).

    Returns:
        Props dict matching shortsVideoSchema.
    """
    raw_title = script.get("title", script.get("topic", ""))
    # Extract script.title dict values (v5+ schema)
    title_line1_from_script: str | None = None
    title_line2_from_script: str | None = None
    accent_color_from_script: str | None = None
    accent_words_from_script: list = []
    if isinstance(raw_title, dict):
        title_line1_from_script = raw_title.get("line1", "") or None
        title_line2_from_script = raw_title.get("line2", "") or None
        accent_color_from_script = raw_title.get("accent_color")
        accent_words_from_script = raw_title.get("accent_words", []) or []
        title = ((title_line1_from_script or "") + " " + (title_line2_from_script or "")).strip()
    else:
        title = raw_title or ""
    sections = script.get("sections", [])

    # Title line split: blueprint > script.title dict > heuristic split
    td = (blueprint or {}).get("title_display", {})
    if td.get("line1"):
        title_line1 = td["line1"]
        title_line2 = td.get("line2") or None
    elif title_line1_from_script:
        # script.title is a dict — use its explicit line1/line2
        title_line1 = title_line1_from_script
        title_line2 = title_line2_from_script
    else:
        # Fallback: heuristic split of flat title string
        if len(title) > 12:
            mid = len(title) // 2
            space_pos = title.rfind(" ", 0, mid + 4)
            if space_pos > 3:
                title_line1 = title[:space_pos]
                title_line2 = title[space_pos + 1:]
            else:
                title_line1 = title[:mid]
                title_line2 = title[mid:]
        else:
            title_line1 = title
            title_line2 = None

    # Channel preset (needed for accent defaults below)
    preset = CHANNEL_PRESETS.get(channel, CHANNEL_PRESETS["humor"])

    # Build titleKeywords: blueprint > script.title > empty
    title_keywords = []
    accent_words = td.get("accent_words") or accent_words_from_script
    accent_color = td.get("accent_color") or accent_color_from_script or preset.get("defaultAccent", "#FFD000")
    full_title = f"{title_line1} {title_line2}" if title_line2 else title_line1
    for word in accent_words:
        if word in full_title:
            title_keywords.append({"text": word, "color": accent_color})
    if title_keywords:
        logger.info("Title keywords from blueprint: %s", title_keywords)

    # Load subtitle cues
    subtitles = []
    if subtitle_json_path and os.path.exists(subtitle_json_path):
        with open(subtitle_json_path, "r", encoding="utf-8") as f:
            subtitles = json.load(f)
        logger.info("Loaded %d subtitle cues from %s", len(subtitles), subtitle_json_path)
    elif subtitle_json_path is None:
        logger.info("No subtitle_json_path provided — rendering without subtitles")

    # `description` intentionally left blank (session 73 D-73-01): auto-deriving it
    # from the first body narration pinned that line to every frame's bottom bar
    # (ShortsVideo.tsx renders it for the full duration), violating Shorts safe-zone.
    # Callers who still want a bottom-bar description must set it explicitly on props.
    description = ""

    total_frames = int(audio_duration * fps)

    props = {
        "audioSrc": assets.get("audioSrc", ""),
        "titleLine1": title_line1,
        "subtitles": subtitles,
        "channelName": preset["channelName"],
        "hashtags": preset["hashtags"],
        "durationInFrames": total_frames,
    }

    if title_line2:
        props["titleLine2"] = title_line2
    if title_keywords:
        props["titleKeywords"] = title_keywords
    if description:
        props["description"] = description
    if accent_color:
        props["accentColor"] = accent_color

    # Series info (Part N of M) — displayed as badge on bottom bar
    series_info = script.get("series") or {}
    if isinstance(series_info, dict):
        series_part = series_info.get("part")
        series_total = series_info.get("total") or series_info.get("of")
        if series_part and series_total:
            try:
                props["seriesPart"] = int(series_part)
                props["seriesTotal"] = int(series_total)
                logger.info("Series badge: Part %d of %d", props["seriesPart"], props["seriesTotal"])
            except (ValueError, TypeError):
                logger.warning("Invalid series part/total: %s/%s", series_part, series_total)

    # 폰트 패밀리 (일본어 채널: Noto Sans JP)
    if preset.get("fontFamily"):
        props["fontFamily"] = preset["fontFamily"]

    # 구독/좋아요 텍스트 (일본어 채널은 일본어로)
    if preset.get("subscribeText"):
        props["subscribeText"] = preset["subscribeText"]
    if preset.get("likeText"):
        props["likeText"] = preset["likeText"]

    # 카테고리별 수첩 태그라인 (채널별 라벨 오버라이드 지원)
    category = script.get("category", "")
    _CATEGORY_LABELS_DEFAULT = {
        "mystery": "미스터리 수첩",
        "crime": "범죄수첩",
        "phenomena": "기현상 수첩",
    }
    # 채널 프리셋에 taglineLabels가 있으면 우선 사용 (일본어 등)
    tagline_labels = preset.get("taglineLabels", _CATEGORY_LABELS_DEFAULT)
    cat_label = tagline_labels.get(category)
    if cat_label:
        props["titleTagline"] = cat_label
        logger.info("Title tagline: %s", props["titleTagline"])

    # 자막 스타일 (채널별 — incidents: 하단 차분한 톤)
    if preset.get("subtitlePosition") is not None:
        props["subtitlePosition"] = preset["subtitlePosition"]
    if preset.get("subtitleHighlightColor"):
        props["subtitleHighlightColor"] = preset["subtitleHighlightColor"]
    if preset.get("subtitleFontSize") is not None:
        props["subtitleFontSize"] = preset["subtitleFontSize"]

    # Transition type: auto-select from channel preset (round-robin per title hash)
    channel_transitions = preset.get("transitions", ["fade"])
    if channel_transitions:
        import hashlib
        title_hash = int(hashlib.md5(title.encode()).hexdigest(), 16)
        props["transitionType"] = channel_transitions[title_hash % len(channel_transitions)]
        logger.info("Auto-selected transition: %s (channel=%s)", props["transitionType"], channel)

    # BGM (optional — ducking handled in ShortsVideo.tsx)
    if assets.get("bgmSrc"):
        props["bgmSrc"] = assets["bgmSrc"]
    if assets.get("bgmVolume") is not None:
        props["bgmVolume"] = assets["bgmVolume"]

    # Multi-clip mode: distribute duration across clips
    asset_clips = assets.get("clips", [])
    if asset_clips:
        num_clips = len(asset_clips)
        # Transition duration varies by type (must match ShortsVideo.tsx getTransitionConfig)
        TRANSITION_DURATIONS = {
            "glitch": 20, "pixelate": 20, "rgbSplit": 20, "zoomBlur": 20,
            "lightLeak": 35, "clockWipe": 25, "checkerboard": 25,
            "fade": 15, "cut": 1,
        }
        transition = props.get("transitionType", "fade")
        crossfade_frames = TRANSITION_DURATIONS.get(transition, 15)
        # Total overlap = (num_clips - 1) * crossfade_frames
        total_overlap = (num_clips - 1) * crossfade_frames if num_clips > 1 else 0

        # Phase 49: section_timing-based per-clip durations for t2i_i2v channels
        has_section_timing = any(ac.get("section_timing_frames") for ac in asset_clips)

        if has_section_timing:
            # Per-section clip durations from section_timing.json (not equal split)
            remotion_clips = []
            for ac in asset_clips:
                clip_frames = ac.get("section_timing_frames", total_frames // max(num_clips, 1))
                clip_data: dict = {
                    "type": ac["type"],
                    "src": ac["src"],
                    "durationInFrames": clip_frames,
                }
                if ac.get("movement"):
                    clip_data["movement"] = ac["movement"]
                if ac.get("transition"):
                    clip_data["transition"] = ac["transition"]
                remotion_clips.append(clip_data)
            per_clip_frames = remotion_clips[0]["durationInFrames"] if remotion_clips else total_frames  # for logging
        else:
            # Existing equal-split behavior (unchanged for other channels)
            per_clip_frames = (total_frames + total_overlap) // num_clips if num_clips > 0 else total_frames

            remotion_clips = []
            for ac in asset_clips:
                clip_data: dict = {
                    "type": ac["type"],
                    "src": ac["src"],
                    "durationInFrames": per_clip_frames,
                }
                if ac.get("movement"):
                    clip_data["movement"] = ac["movement"]
                if ac.get("transition"):
                    clip_data["transition"] = ac["transition"]
                remotion_clips.append(clip_data)

        # Phase 6-7: Apply movement and per-clip transition from script sections
        _MOVEMENTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]
        content_sections = [s for s in sections if s.get("narration")]
        for i, rc in enumerate(remotion_clips):
            sec = content_sections[i] if i < len(content_sections) else {}
            vd_raw = sec.get("visual_directing", {}) if sec else {}
            vd = vd_raw if isinstance(vd_raw, dict) else {}

            # Phase 6: Ken Burns movement for image clips (skip if already set)
            if rc["type"] == "image" and "movement" not in rc:
                if visual_spec_provided:
                    # 옵션 B: visual_spec.json 이 single source of truth.
                    # Designer 가 이 clip 의 movement 를 명시하지 않았다면 = 의도적 freeze.
                    # 자동 round-robin 할당을 하지 않는다 (FAIL-DES-008 근본 방지).
                    pass
                else:
                    # Legacy path: script.visual_directing + round-robin fallback
                    movement = vd.get("camera_movement") if vd else None
                    if not movement:
                        movement = _MOVEMENTS[i % len(_MOVEMENTS)]
                    rc["movement"] = movement

            # Phase 7: per-clip transition override (skip if already set)
            if "transition" not in rc:
                transition_out = sec.get("transition_out") if sec else None
                if transition_out:
                    rc["transition"] = transition_out

        # 옵션 B: Designer 가 명시적으로 "movement 없음 (freeze)" 을 의도한 clip 은
        # render_shorts_video 에서 sentinel "_NULL_FREEZE" 가 주입된다.
        # Remotion Zod 검증 전에 sentinel 을 제거해야 한다.
        for rc in remotion_clips:
            if rc.get("movement") == "_NULL_FREEZE":
                rc.pop("movement", None)

        props["clips"] = remotion_clips
        logger.info("Multi-clip mode: %d clips, %d frames each (crossfade=%d)",
                     num_clips, per_clip_frames, crossfade_frames)
    else:
        # Legacy single-source
        if assets.get("videoSrc"):
            props["videoSrc"] = assets["videoSrc"]
        if assets.get("imageSrc"):
            props["imageSrc"] = assets["imageSrc"]

    # Validate before returning
    validate_shorts_props(props)

    return props


def render_shorts_video(
    script: dict,
    channel: str,
    output_dir: str,
    project_root: str,
    audio_path: str,
    audio_duration: float,
    subtitle_json_path: str | None = None,
    video_path: str | None = None,
    image_path: str | None = None,
    scene_clips: list[dict] | None = None,
    *,
    video_paths: list[str] | None = None,
    image_paths: list[str] | None = None,
    bgm_path: str | None = None,
    blueprint: dict | None = None,
    visual_spec_path: str | None = None,
    fps: int = 30,
) -> str:
    """Render a full ShortsVideo composition via Remotion CLI.

    This replaces the FFmpeg video_assemble + layout_compose pipeline.

    Args:
        script: Parsed script.json dict.
        channel: Channel name.
        output_dir: Pipeline output directory.
        project_root: Project root directory.
        audio_path: Path to narration.mp3.
        audio_duration: Audio duration in seconds.
        subtitle_json_path: Path to subtitles_remotion.json (optional).
        video_path: Path to main video clip (optional, legacy).
        image_path: Path to main image (optional, legacy).
        video_paths: List of video clip paths (multi-clip mode).
        image_paths: List of image paths (multi-clip mode).
        bgm_path: Explicit BGM file path (optional, auto-selects from channel).
        blueprint: Blueprint dict with title_display for accent keywords.
        visual_spec_path: Path to visual_spec.json from Designer agent (옵션 B).
            If provided together with scene_clips, the Designer's clipDesign[]
            movement/transition decisions become the single source of truth.
            Round-robin auto-assignment (legacy) is disabled for that render.
            Clips whose Designer movement is null (intentional freeze) are
            marked with a sentinel that is stripped before Remotion Zod
            validation. See FAIL-DES-008 / FAIL-EDT-008 for context.
        fps: Frames per second.

    Returns:
        Path to rendered final.mp4.

    Raises:
        RuntimeError: If Remotion render fails.
    """
    logger.info("=== Remotion ShortsVideo render start ===")

    # 1a. 옵션 B: Inject Designer's visual_spec.clipDesign into scene_clips.
    # This must happen BEFORE prepare_remotion_assets so that the movement
    # values flow into assets["clips"] and then into build_shorts_props.
    visual_spec_provided = False
    if visual_spec_path and os.path.exists(visual_spec_path) and scene_clips:
        try:
            with open(visual_spec_path, "r", encoding="utf-8") as f:
                visual_spec = json.load(f)
            clip_design = visual_spec.get("clipDesign", [])
            if not clip_design:
                logger.warning(
                    "visual_spec.clipDesign is empty — falling back to round-robin movement"
                )
            else:
                _VALID_MOVEMENTS = {"zoom_in", "zoom_out", "pan_left", "pan_right"}
                for i, sc in enumerate(scene_clips):
                    if i >= len(clip_design):
                        logger.warning(
                            "visual_spec.clipDesign[%d] missing for scene_clip[%d] — freeze",
                            i, i,
                        )
                        sc.setdefault("movement", "_NULL_FREEZE")
                        continue
                    cd = clip_design[i]
                    design_movement = cd.get("movement")
                    if design_movement in _VALID_MOVEMENTS:
                        sc["movement"] = design_movement
                    else:
                        # Designer explicitly set movement to null/None → freeze.
                        # Use sentinel so prepare_remotion_assets copies it,
                        # build_shorts_props strips it before Zod validation.
                        sc["movement"] = "_NULL_FREEZE"
                    design_transition = cd.get("transition")
                    if design_transition and "transition" not in sc:
                        sc["transition"] = design_transition
                visual_spec_provided = True
                logger.info(
                    "visual_spec applied: %d clipDesign entries (single source of truth)",
                    len(clip_design),
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.error(
                "Failed to load visual_spec from %s: %s — falling back to round-robin",
                visual_spec_path, e,
            )
    elif visual_spec_path and not scene_clips:
        logger.warning(
            "visual_spec_path provided but scene_clips is empty — visual_spec ignored"
        )

    # 1. Copy assets to remotion/public/
    assets = prepare_remotion_assets(
        output_dir=output_dir,
        project_root=project_root,
        video_path=video_path,
        audio_path=audio_path,
        image_path=image_path,
        video_paths=video_paths,
        image_paths=image_paths,
        bgm_path=bgm_path,
        channel=channel,
        scene_clips=scene_clips,
    )

    # 1b. Verify audio duration via ffprobe
    ffprobe_duration = get_audio_duration_ffprobe(audio_path)
    if ffprobe_duration > 0.0:
        diff = abs(ffprobe_duration - audio_duration)
        if diff > 1.0:
            logger.warning(
                "Audio duration mismatch: caller=%.3fs, ffprobe=%.3fs (diff=%.3fs) — using ffprobe value",
                audio_duration, ffprobe_duration, diff,
            )
            audio_duration = ffprobe_duration
        else:
            logger.info("Audio duration verified: caller=%.3fs, ffprobe=%.3fs (diff=%.3fs)",
                       audio_duration, ffprobe_duration, diff)

    # 1a-guard. Quality gates: validate critical assets before render
    # (a) Scene clips must not be empty
    clip_count = len(assets.get("clips", []))
    if clip_count == 0:
        raise RuntimeError(
            "⚠️ Quality Gate FAIL: 0 scene clips detected. "
            "Video-Sourcer must provide at least 1 clip. Aborting render."
        )
    logger.info("Quality gate: %d scene clips OK", clip_count)

    # (b) Subtitle coverage must be >= 95%
    if subtitle_json_path and os.path.exists(subtitle_json_path):
        try:
            with open(subtitle_json_path, "r", encoding="utf-8") as f:
                subs = json.load(f)
            cues = subs if isinstance(subs, list) else subs.get("cues", subs.get("words", []))
            if len(cues) == 0:
                raise RuntimeError(
                    "⚠️ Quality Gate FAIL: 0 subtitle cues in subtitles_remotion.json. "
                    "Run word_subtitle.py --script to regenerate."
                )
            last_end_ms = max(c.get("endMs", c.get("end_ms", 0)) for c in cues)
            audio_ms = audio_duration * 1000
            coverage = (last_end_ms / audio_ms * 100) if audio_ms > 0 else 0
            if coverage < 95:
                raise RuntimeError(
                    f"⚠️ Quality Gate FAIL: subtitle coverage {coverage:.1f}% < 95%. "
                    f"Last subtitle ends at {last_end_ms}ms, audio is {audio_ms:.0f}ms. "
                    "Run word_subtitle.py --script to regenerate."
                )
            logger.info("Quality gate: subtitle coverage %.1f%% OK (%d cues)", coverage, len(cues))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Quality gate: could not verify subtitles: %s", e)

    # 1b. Copy character avatars to remotion/public/ if they exist
    job_id = os.path.basename(os.path.normpath(output_dir))
    public_char_dir = os.path.join(project_root, "remotion", "public", job_id)
    char_left_path = os.path.join(output_dir, "sources", "character_assistant.png")
    char_right_path = os.path.join(output_dir, "sources", "character_detective.png")
    _char_left_prop = None
    _char_right_prop = None
    if os.path.exists(char_left_path):
        os.makedirs(public_char_dir, exist_ok=True)
        shutil.copy2(char_left_path, os.path.join(public_char_dir, "character_left.png"))
        _char_left_prop = f"{job_id}/character_left.png"
        logger.info("Character left avatar copied: %s", char_left_path)
    if os.path.exists(char_right_path):
        os.makedirs(public_char_dir, exist_ok=True)
        shutil.copy2(char_right_path, os.path.join(public_char_dir, "character_right.png"))
        _char_right_prop = f"{job_id}/character_right.png"
        logger.info("Character right avatar copied: %s", char_right_path)

    # 2. Build props
    props = build_shorts_props(
        script=script,
        channel=channel,
        assets=assets,
        subtitle_json_path=subtitle_json_path,
        audio_duration=audio_duration,
        fps=fps,
        blueprint=blueprint,
        visual_spec_provided=visual_spec_provided,
    )

    # 2b. Inject character avatar props
    if _char_left_prop:
        props["characterLeftSrc"] = _char_left_prop
    if _char_right_prop:
        props["characterRightSrc"] = _char_right_prop

    # 3. Write props JSON
    props_path = os.path.join(output_dir, "remotion_props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2, ensure_ascii=False)
    logger.info("Props written: %s (durationInFrames=%d)", props_path, props["durationInFrames"])

    # 4. Build render command — all paths must be absolute (cwd=remotion/)
    entry_point = os.path.join(project_root, "remotion", "src", "index.ts").replace("\\", "/")
    output_path = os.path.abspath(os.path.join(output_dir, "final.mp4")).replace("\\", "/")
    props_path_safe = os.path.abspath(props_path).replace("\\", "/")

    cmd = [
        "npx", "remotion", "render",
        entry_point,
        "ShortsVideo",
        output_path,
        f"--props={props_path_safe}",
        "--codec=h264",
        f"--fps={fps}",
        "--width=1080",
        "--height=1920",
    ]

    # Windows에서 npx는 npx.cmd이므로 shell=True 필요
    use_shell = sys.platform == "win32"

    logger.info("Render command: %s", " ".join(cmd))

    # 5. Execute render
    start_time = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,  # 10분 타임아웃 (커스텀 전환 효과 렌더 시 추가 시간 필요)
        cwd=os.path.join(project_root, "remotion"),
        shell=use_shell,
    )
    elapsed = time.time() - start_time

    if result.returncode != 0:
        stderr = result.stderr[-1000:] if result.stderr else "no stderr"
        logger.error("Remotion render FAILED (exit %d, %.1fs): %s", result.returncode, elapsed, stderr)
        raise RuntimeError(f"Remotion render failed (exit {result.returncode}): {stderr}")

    final_path = os.path.join(output_dir, "final.mp4")
    if not os.path.exists(final_path):
        raise RuntimeError(f"Remotion render completed but file not found: {final_path}")

    file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
    logger.info("=== Remotion render complete: %.1fs, %.1f MB ===", elapsed, file_size_mb)

    # 6. Post-render cleanup
    # Delete remotion_props.json
    if os.path.exists(props_path):
        os.remove(props_path)
        logger.info("Cleaned up props file: %s", props_path)

    # Delete remotion/public/<job_id>/ assets
    job_id = assets.get("job_id", "")
    if job_id:
        cleanup_remotion_assets(project_root, job_id)

    return final_path


def main():
    """CLI entry point: render all Remotion clips in a scene manifest.

    Usage:
        remotion_render.py --manifest MANIFEST --output-dir OUTPUT_DIR --project-root PROJECT_ROOT
    """
    parser = argparse.ArgumentParser(
        description="Render Remotion graphic card clips from scene manifest"
    )
    parser.add_argument(
        "--manifest", required=True,
        help="Path to scene-manifest.json"
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory for rendered .mp4 clips (e.g., output/stock/)"
    )
    parser.add_argument(
        "--project-root", required=True,
        help="Project root directory (for Remotion entry point path)"
    )

    args = parser.parse_args()

    # Validate manifest file exists
    if not os.path.exists(args.manifest):
        print(json.dumps({
            "status": "error",
            "error": "manifest_not_found",
            "message": f"Manifest file not found: {args.manifest}",
        }))
        sys.exit(1)

    try:
        # Load manifest
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Determine resolution from manifest format field
        fmt = manifest.get("format", {})
        width = fmt.get("width", 1080)
        height = fmt.get("height", 1920)
        fps = fmt.get("fps", 30)

        # Find Remotion clips
        remotion_clips = find_remotion_clips(manifest)

        if not remotion_clips:
            logger.info("No Remotion clips found in manifest — nothing to render")
            print(json.dumps({
                "status": "success",
                "rendered": 0,
                "failed": 0,
                "clips": [],
            }))
            sys.exit(0)

        logger.info("Found %d Remotion clips to render (resolution=%dx%d, fps=%d)",
                     len(remotion_clips), width, height, fps)

        # Render each clip
        rendered_count = 0
        failed_count = 0
        clip_results = []

        for i, (clip, ch_idx, cl_idx) in enumerate(remotion_clips):
            clip_index = clip.get("index", i)
            is_first = (i == 0)

            result = render_clip(
                clip, clip_index, args.output_dir, args.project_root,
                width, height, fps, is_first,
            )
            clip_results.append(result)

            if result["status"] == "success":
                rendered_count += 1
            else:
                failed_count += 1

        # Write updated manifest back
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info("Rendering complete: %d rendered, %d failed", rendered_count, failed_count)

        # Determine exit code
        if rendered_count == 0 and failed_count > 0:
            # All failed
            print(json.dumps({
                "status": "error",
                "rendered": 0,
                "failed": failed_count,
                "clips": clip_results,
            }))
            sys.exit(1)

        print(json.dumps({
            "status": "success",
            "rendered": rendered_count,
            "failed": failed_count,
            "clips": clip_results,
        }))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": type(e).__name__,
            "message": str(e),
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
