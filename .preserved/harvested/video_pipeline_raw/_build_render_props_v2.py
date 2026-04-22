"""Build render_props.json for Remotion with section_timing-based clip durations.

Each section's clip duration = actual TTS narration duration (from section_timing.json),
NOT equal split. Static scenes use images with Ken Burns (zoom/pan in Remotion).
I2V scenes use Kling clips.

Usage:
  python _build_render_props_v2.py --output-dir output/wildlife-mantis-shrimp-v2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FPS = 30


def _rel_to_output(file_path: Path, output_dir: Path) -> str:
    """Return path relative to output_dir.parent (= project `output/` root).

    Falls back to resolving against project `output/` or absolute path if not under parent.
    """
    abs_path = file_path.resolve()
    # Try relative to output_dir.parent first (e.g. "wildlife-mantis-shrimp-v2/...")
    try:
        return abs_path.relative_to(output_dir.parent.resolve()).as_posix()
    except ValueError:
        pass
    # Try relative to project root if output_dir.parent doesn't contain it
    try:
        return abs_path.relative_to(output_dir.resolve()).as_posix()
    except ValueError:
        pass
    return abs_path.as_posix()


def build(output_dir: Path, channel_name: str, channel_logo: str = None,
          accent: str = "#2E8B57", subtitle_color: str = "#4ADE80",
          hashtags: str = "#shorts"):
    """Build render_props.json referencing the actual clips + section timing."""
    script = json.loads((output_dir / "script.json").read_text(encoding="utf-8"))
    timing = json.loads((output_dir / "section_timing.json").read_text(encoding="utf-8"))

    # Check for Kling clips manifest
    kling_manifest_path = output_dir / "kling_clips" / "kling_manifest.json"
    kling_manifest = {}
    if kling_manifest_path.exists():
        manifest = json.loads(kling_manifest_path.read_text(encoding="utf-8"))
        for entry in manifest:
            kling_manifest[entry["section_id"]] = entry

    # AI scenes dir
    scenes_dir_a = output_dir / "ai_scenes"
    scenes_dir_b = output_dir / "ai_scenes_v2"
    scenes_dir = scenes_dir_b if scenes_dir_b.exists() else scenes_dir_a

    clips = []
    total_frames = 0
    for i, sec_timing in enumerate(timing["sections"]):
        scene_id = sec_timing["section_id"]

        # Duration = narration + half of silence_after (for smooth transition)
        duration_ms = sec_timing["duration_ms"] + sec_timing.get("silence_after_ms", 0)
        duration_frames = max(30, int((duration_ms / 1000) * FPS))  # min 1s

        clip = kling_manifest.get(scene_id, {})
        clip_path = clip.get("clip")
        image_path = clip.get("image")

        # If no manifest entry, fall back to image lookup
        if not image_path:
            matches = list(scenes_dir.glob(f"{i+1:02d}_{scene_id}.*"))
            if not matches:
                matches = list(scenes_dir.glob(f"*{scene_id}*"))
            if matches:
                image_path = str(matches[0].resolve())

        if clip_path and Path(clip_path).exists():
            # I2V clip from Kling
            clips.append({
                "type": "video",
                "src": _rel_to_output(Path(clip_path), output_dir),
                "durationInFrames": duration_frames,
                "transition": "fade",
                "sceneId": scene_id,
                "mode": "i2v",
            })
        elif image_path and Path(image_path).exists():
            # Static image with Ken Burns (handled client-side in Remotion)
            clips.append({
                "type": "image",
                "src": _rel_to_output(Path(image_path), output_dir),
                "durationInFrames": duration_frames,
                "transition": "fade",
                "sceneId": scene_id,
                "mode": "ken-burns",
                # Alternate zoom direction for variety
                "kenBurns": {
                    "direction": "in" if i % 2 == 0 else "out",
                    "startScale": 1.0 if i % 2 == 0 else 1.15,
                    "endScale": 1.15 if i % 2 == 0 else 1.0,
                },
            })
        else:
            print(f"WARN: No clip or image for {scene_id}")
            continue

        total_frames += duration_frames
        print(f"[{i+1}] {scene_id}: {duration_ms}ms -> {duration_frames}f ({clips[-1]['mode']})")

    # Narration MP3
    audio_src = _rel_to_output(output_dir / "narration.mp3", output_dir)

    # Simplified subtitles (per section — Remotion handles word-level later)
    subtitles = []
    for sec_timing in timing["sections"]:
        # Split narration into chunks of ~5 words
        words = sec_timing["narration"].split()
        chunk_size = 5
        chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]
        start = sec_timing["start_ms"]
        per_chunk = sec_timing["duration_ms"] // max(1, len(chunks))
        for ci, chunk in enumerate(chunks):
            cs = start + ci * per_chunk
            ce = cs + per_chunk
            subtitles.append({
                "startMs": cs,
                "endMs": ce,
                "words": chunk,
                "highlightIndex": 0,
            })

    props = {
        "clips": clips,
        "audioSrc": audio_src,
        "titleLine1": script.get("title", {}).get("line1", ""),
        "titleLine2": script.get("title", {}).get("line2", ""),
        "subtitles": subtitles,
        "channelName": channel_name,
        "channelLogoSrc": channel_logo,
        "hashtags": hashtags,
        "accentColor": accent,
        "fontFamily": "Inter",
        "subtitlePosition": 0.82,
        "subtitleHighlightColor": subtitle_color,
        "subtitleFontSize": 48,
        "subscribeText": "Subscribe",
        "likeText": "Like",
        "durationInFrames": total_frames,
        "transitionType": "fade",
    }

    output_path = output_dir / "render_props.json"
    output_path.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    print(f"\nrender_props.json: {output_path}")
    print(f"Total frames: {total_frames} ({total_frames/FPS:.1f}s)")
    print(f"I2V clips: {sum(1 for c in clips if c['mode'] == 'i2v')}")
    print(f"Ken Burns clips: {sum(1 for c in clips if c['mode'] == 'ken-burns')}")
    return props


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--channel-name", default="HistoryMoment")
    ap.add_argument("--channel-logo", default=None)
    ap.add_argument("--accent", default="#B8860B")
    ap.add_argument("--subtitle-color", default="#FFD700")
    ap.add_argument("--hashtags", default="#shorts #history #documentary")
    args = ap.parse_args()

    build(
        Path(args.output_dir),
        channel_name=args.channel_name,
        channel_logo=args.channel_logo,
        accent=args.accent,
        subtitle_color=args.subtitle_color,
        hashtags=args.hashtags,
    )


if __name__ == "__main__":
    main()
