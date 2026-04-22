"""Visual pipeline runner: orchestrates T2I -> I2V for t2i_i2v channels."""

import json
import logging
import os
import sys
import time

import yaml
from pathlib import Path

# Ensure sibling modules are importable (directory uses hyphens, not a normal package)
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import clip_timing
import i2v_generate
import prompt_builder
import reference_image
import shot_planner
import t2i_generate

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "channels.yaml"
)


def _load_channel_config(channel: str) -> dict:
    """Load channel config from channels.yaml."""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    channels = cfg.get("channels", {})
    return channels.get(channel, {})


def run_visual_pipeline(
    slug: str,
    script: dict,
    output_dir: str,
    *,
    channel: str = "",
) -> list[dict] | None:
    """Run the full T2I -> I2V visual pipeline for a given script.

    Args:
        slug: Project slug identifier.
        script: Parsed script dict with sections, environment, reference_url, etc.
        output_dir: Directory where generated assets are saved.
        channel: Channel name (e.g. "wildlife", "documentary").

    Returns:
        List of clip dicts with clip_path, durationInFrames, section_index, type,
        and section_timing_frames. Returns None if the channel does not use t2i_i2v.
    """
    # 1. Check channel visual_mode
    ch_config = _load_channel_config(channel)
    if ch_config.get("visual_mode") != "t2i_i2v":
        logger.info(
            "Channel '%s' visual_mode is not t2i_i2v — skipping visual pipeline",
            channel,
        )
        return None

    os.makedirs(output_dir, exist_ok=True)

    # 2. Extract sections from script
    sections = script.get("sections", [])
    if not sections:
        logger.warning("No sections found in script for slug=%s", slug)
        return []

    # 3. Extract environment
    environment = script.get("environment", "natural environment")

    # 4. Download reference image
    reference_path = None
    ref_url = script.get("reference_url", "")
    if ref_url:
        try:
            reference_path = reference_image.download_reference_image(
                ref_url, output_dir
            )
            logger.info("Downloaded reference image: %s", reference_path)
        except Exception as e:
            logger.warning("Failed to download reference image: %s", e)
            reference_path = None
    else:
        logger.warning("No reference_url in script — proceeding without reference")

    # 5. Plan shot types
    shot_types = shot_planner.plan_shot_types(len(sections))

    # 6. Generate clips for each section
    subject_name = script.get("subject_name", "")
    results = []

    for i, section in enumerate(sections):
        try:
            visual_desc = section.get("visual_description", "subject in motion")
            camera_type = section.get("camera_type", "professional DSLR")
            camera_angle = section.get("camera_angle", "eye level")
            shot_type = shot_types[i] if i < len(shot_types) else "MEDIUM SHOT"

            # 6a. Build prompt
            scene_prompt = prompt_builder.build_scene_prompt(
                shot_type=shot_type,
                camera_type=camera_type,
                camera_angle=camera_angle,
                subject_action=visual_desc,
                environment=environment,
                dynamic_element="in motion, mid-action",
                reference_desc=subject_name,
            )

            # 6b. Validate action
            try:
                prompt_builder.validate_prompt_has_action(scene_prompt)
            except ValueError:
                logger.warning(
                    "Section %d prompt lacks action verb — appending default",
                    i,
                )
                scene_prompt += " running actively"

            # 6c. Generate image
            image_path = t2i_generate.generate_scene_image(
                reference_path or "",
                scene_prompt,
                os.path.join(output_dir, f"scene_{i:03d}.jpg"),
            )

            # 6d. Upload
            fal_url = i2v_generate.upload_for_fal(image_path)

            # 6e. Generate video
            clip_path = i2v_generate.generate_video_clip(
                fal_url,
                scene_prompt,
                os.path.join(output_dir, f"clip_{i:03d}.mp4"),
            )

            results.append(
                {
                    "clip_path": clip_path,
                    "section_index": i,
                    "type": "video",
                }
            )

            # 6f. Sleep between iterations
            if i < len(sections) - 1:
                time.sleep(2)

        except Exception as e:
            logger.error("Section %d failed: %s", i, e)
            continue

    # 7. Compute clip durations from section_timing.json
    timing_path = os.path.join(output_dir, "section_timing.json")
    timings = []
    if os.path.exists(timing_path):
        try:
            timings = clip_timing.compute_clip_durations(timing_path)
        except Exception as e:
            logger.error("Failed to compute clip durations: %s", e)

    # 8. Merge timing into results
    for result_item in results:
        idx = result_item["section_index"]
        if idx < len(timings):
            result_item["durationInFrames"] = timings[idx]["durationInFrames"]
            result_item["section_timing_frames"] = timings[idx]["durationInFrames"]
        else:
            # Fallback: default 5 seconds at 30fps
            result_item["durationInFrames"] = 150
            result_item["section_timing_frames"] = 150

    return results
