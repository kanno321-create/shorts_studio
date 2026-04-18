"""Batch I2V: image -> Kling 2.6 Pro video clip.

Uses fal.ai API. Each image uploaded via fal_client.upload_file() to get public URL,
then submitted to kling-video/v2.5/pro/image-to-video. Polls until complete.

Usage:
  python _kling_i2v_batch.py --scenes-dir output/wildlife-mantis-shrimp-v2/ai_scenes \
    --script output/wildlife-mantis-shrimp-v2/script.json \
    --output-dir output/wildlife-mantis-shrimp-v2/kling_clips \
    --only-actions  # skip static/map scenes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(override=True)

import fal_client

# Use v2.5 pro which is the verified-working endpoint (child pipeline proven)
KLING_ENDPOINT = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"

# Shot types that need dynamic motion (animals, explosions, action)
# vs static scenes (maps, establishing shots that just need ken burns)
ACTION_KEYWORDS = [
    "strikes", "smashes", "lunges", "explodes", "detonate",
    "fire", "flame", "torpedo", "ripple", "shockwave", "snap",
    "dragging", "runs", "streaks", "drops",
]

MAP_KEYWORDS = ["MAP", "TACTICAL", "tactical", "map"]


def build_motion_prompt(visual_description: str, narration: str, scene_id: str = "") -> str:
    """Build a dynamic motion prompt for Kling I2V based on scene content.

    Every prompt must include CONCRETE subject motion + camera work.
    Never allow "camera-only motion" (see production-mistakes #14).
    """
    # Scene-specific motion based on scene_id
    motion_library = {
        # Wildlife scenes
        "discover_1": "The mantis shrimp's stalked eyes peek out from its burrow, swiveling independently to scan. Camera drifts slowly forward over the reef.",
        "discover_2": "The mantis shrimp fully emerges from its burrow, antennae twitching, body shifting in cautious movement. Camera slowly orbits around at eye level.",
        "observe_1": "The stalked eyes rotate independently, each eye tracking in different directions. Iridescent surface catches light with shimmering rainbow reflection. Camera slowly pushes in to extreme macro.",
        "observe_2": "The mantis shrimp shifts its body weight, tensing the raptorial clubs beneath its head. Small water particles drift past. Camera slowly pans from profile.",
        "action_1": "The mantis shrimp lunges forward with explosive speed, its raptorial club snaps outward and smashes into the snail shell. Visible shockwave ripples through the water. Shell fragments explode outward. Camera captures the strike in motion.",
        "action_2": "Shell fragments settle slowly in the water as the mantis shrimp pulls the snail meat from the shattered shell with smaller appendages. Debris swirls in the current. Camera slowly pulls back.",
        "action_3": "The mantis shrimp drags its prey backward toward the burrow, clutching the meat with its appendages. Camera follows from above at an angle.",
        "wonder_1": "The mantis shrimp's eyes peer out from the burrow entrance, watchful. Water ripples gently above. Camera slowly pulls back to reveal the full reef at golden hour.",
        # Documentary scenes
        "setup_1": "Calm water reflects the sunrise. Sailors move slowly on distant decks. Camera drifts forward slowly over the peaceful harbor. Gentle water movement.",
        "radar_warning": "Green radar blips blink and move across the screen as the cluster approaches. The soldier lifts the telephone receiver. Camera slowly pushes in on the radar display.",
        "torpedo_strike": "The Japanese torpedo bomber flies past, releasing its torpedo. Torpedo splashes into water and streaks toward the battleship. Massive water column erupts from the explosion. Debris and water rain down. Camera shakes violently.",
        "arizona_explosion": "Fireball erupts from the bow of the Arizona as the magazine detonates. Smoke column rises skyward. Debris flies outward. Sailors shield faces. Camera slowly pulls back to show scale.",
        "counterfire": "Sailors manning anti-aircraft guns fire upward, bright tracer rounds streaking across the sky. Shell casings fall to the deck. One Japanese plane trails smoke downward. Camera at deck level, gunners in action.",
        "aftermath": "Gentle oil sheen ripples on dark water. Distant fires glow through smoke. Camera slowly tilts upward from water to reveal the burning harbor skyline.",
    }

    # Use scene-specific motion if available, else generic
    specific_motion = motion_library.get(scene_id, "")
    if specific_motion:
        prompt = f"{specific_motion} Hyperrealistic cinematic quality."
    else:
        prompt = (
            f"{visual_description} "
            "Subject performs visible physical action. "
            "Camera slowly pushes in with subtle motion. "
            "Hyperrealistic natural movement."
        )

    return prompt


NEG_PROMPT = (
    "static character, frozen pose, only camera movement, camera-only motion, "
    "motionless subject, still photo, no action, no movement, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing"
)


def is_action_scene(scene_id: str, visual_desc: str) -> bool:
    """Determine if scene needs full I2V treatment vs static Ken Burns.

    Default: all scenes are I2V (dynamic). Only MAP/TACTICAL scenes stay static.
    Wildlife/documentary needs motion in every non-map scene (mem: no still animals).
    """
    text = f"{scene_id} {visual_desc}"
    # Maps stay static
    if any(kw in text for kw in MAP_KEYWORDS):
        return False
    # Everything else gets I2V
    return True


def submit_kling(image_url: str, prompt: str, duration_seconds: int = 10) -> dict:
    """Submit I2V job and wait for result."""
    handler = fal_client.submit(
        KLING_ENDPOINT,
        arguments={
            "prompt": prompt,
            "image_url": image_url,
            "duration": str(duration_seconds),  # "5" or "10"
            "negative_prompt": NEG_PROMPT,
            "cfg_scale": 0.5,
        },
    )
    print(f"   Submitted. Request ID: {handler.request_id}")
    result = handler.get()  # blocks until done
    return result


def download_video(url: str, output_path: Path) -> None:
    import httpx
    resp = httpx.get(url, follow_redirects=True, timeout=120)
    resp.raise_for_status()
    output_path.write_bytes(resp.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes-dir", required=True, help="Directory with scene images (01_*.jpg etc)")
    ap.add_argument("--script", required=True, help="script.json")
    ap.add_argument("--output-dir", required=True, help="Where to save Kling clips")
    ap.add_argument("--only-actions", action="store_true", help="Only process action scenes, skip static/maps")
    ap.add_argument("--only-ids", help="Comma-separated section_ids to process (debug)")
    ap.add_argument("--duration", type=int, default=10, choices=[5, 10])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not (os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")):
        print("ERROR: FAL_KEY not set", file=sys.stderr)
        sys.exit(1)

    scenes_dir = Path(args.scenes_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    script = json.loads(Path(args.script).read_text(encoding="utf-8"))
    only_ids = set(args.only_ids.split(",")) if args.only_ids else None

    manifest = []
    for i, section in enumerate(script["sections"]):
        scene_id = section["section_id"]
        if only_ids and scene_id not in only_ids:
            continue

        # Find matching image
        matches = list(scenes_dir.glob(f"{i+1:02d}_{scene_id}.*"))
        if not matches:
            matches = list(scenes_dir.glob(f"*{scene_id}*"))
        if not matches:
            print(f"[{i+1}] {scene_id}: no image found, SKIP")
            continue
        image_path = matches[0]

        visual = section.get("visual_description", "")
        is_action = is_action_scene(scene_id, visual)

        if args.only_actions and not is_action:
            print(f"[{i+1}] {scene_id}: static/map scene, SKIP (use Ken Burns in Remotion)")
            manifest.append({
                "index": i,
                "section_id": scene_id,
                "type": "static",
                "image": str(image_path.resolve()),
                "clip": None,
            })
            continue

        output_clip = out_dir / f"{i+1:02d}_{scene_id}.mp4"
        if output_clip.exists():
            print(f"[{i+1}] {scene_id}: clip already exists, SKIP")
            manifest.append({
                "index": i,
                "section_id": scene_id,
                "type": "i2v",
                "image": str(image_path.resolve()),
                "clip": str(output_clip.resolve()),
            })
            continue

        print(f"\n[{i+1}] {scene_id} (I2V {args.duration}s): {image_path.name}")
        prompt = build_motion_prompt(visual, section["narration"], scene_id)
        print(f"   Prompt: {prompt[:150]}...")

        if args.dry_run:
            print(f"   DRY RUN (would submit to {KLING_ENDPOINT})")
            continue

        try:
            # Upload image
            image_url = fal_client.upload_file(str(image_path))
            print(f"   Uploaded: {image_url[:80]}...")

            # Submit
            result = submit_kling(image_url, prompt, args.duration)
            video_url = result.get("video", {}).get("url") or result.get("url")
            if not video_url:
                print(f"   ERROR: no video URL in result: {result}")
                continue

            # Download
            download_video(video_url, output_clip)
            print(f"   OK: {output_clip.name} ({output_clip.stat().st_size // 1024}KB)")

            manifest.append({
                "index": i,
                "section_id": scene_id,
                "type": "i2v",
                "image": str(image_path.resolve()),
                "clip": str(output_clip.resolve()),
                "duration_s": args.duration,
                "prompt": prompt,
            })
        except Exception as e:
            print(f"   ERROR: {str(e)[:300]}")
            time.sleep(3)
            continue

    # Write manifest
    manifest_path = out_dir / "kling_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest: {manifest_path}")
    print(f"Clips generated: {sum(1 for m in manifest if m.get('clip'))}")
    print(f"Static scenes (Ken Burns): {sum(1 for m in manifest if m.get('type') == 'static')}")


if __name__ == "__main__":
    main()
