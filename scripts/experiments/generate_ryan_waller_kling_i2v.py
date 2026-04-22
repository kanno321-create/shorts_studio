"""Ryan Waller Kling 2.6 Pro I2V — 6 b-roll anchor PNGs → 6 mp4 clips.

Session #34 FIX-4: v1 used static PNGs with Remotion Ken Burns only (failed).
v2 uses Kling I2V to add real intra-image motion per feedback_kling_i2v_required_not_ken_burns.

Prompts follow feedback_i2v_prompt_principles (Camera Lock + Positive Persistence
+ Micro Verb). Duration 5s each; cost ~$0.35 × 6 = $2.10; latency ~70s each.

Output:
- output/ryan-waller/sources/broll_{01..06}_<name>.mp4  (final v2 clips)
- outputs/kling/ryan-waller/...                          (raw downloads)
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.api.kling_i2v import KlingI2VAdapter  # noqa: E402

SOURCES_DIR = Path("output/ryan-waller/sources")
KLING_OUTPUT_DIR = Path("outputs/kling/ryan-waller")

# 6 b-roll prompts — Camera Lock + Positive Persistence + Micro Verb
# Each ≤ 30 words, single movement, cinematic noir tone consistent with anchor PNGs.
CLIPS = [
    {
        "anchor": "broll_01_interrogation.png",
        "output_name": "broll_01_interrogation.mp4",
        "prompt": (
            "Static shot, camera holds still. A young man sits slumped in an "
            "interrogation chair under harsh overhead light, slowly blinks his "
            "swollen left eye, softly breathes out. Cinematic noir, cold tones."
        ),
    },
    {
        "anchor": "broll_02_christmas_night.png",
        "output_name": "broll_02_christmas_night.mp4",
        "prompt": (
            "Static shot, camera holds still. A quiet suburban Phoenix house at "
            "night, faint Christmas lights gently flicker on the porch, cold mist "
            "softly drifts past the dark windows. Cinematic noir, deep shadows."
        ),
    },
    {
        "anchor": "broll_03_clock.png",
        "output_name": "broll_03_clock.mp4",
        "prompt": (
            "Static shot, camera holds still. An old wall clock mounted on a dim "
            "interrogation room wall, the second hand slowly sweeps forward, soft "
            "shadow shifts across the dial. Cinematic noir, amber tungsten glow."
        ),
    },
    {
        "anchor": "broll_04_fleeing.png",
        "output_name": "broll_04_fleeing.mp4",
        "prompt": (
            "Static shot, camera holds still. A lone silhouette walks away down a "
            "dark empty alley at night, shoulders gently rise and fall with heavy "
            "breath, coat softly moves in the breeze. Cinematic noir, blue wash."
        ),
    },
    {
        "anchor": "broll_05_hospital.png",
        "output_name": "broll_05_hospital.mp4",
        "prompt": (
            "Static shot, camera holds still. An empty hospital corridor at late "
            "night, a single fluorescent light gently flickers overhead, polished "
            "floor softly reflects distant movement. Cinematic noir, cold cyan."
        ),
    },
    {
        "anchor": "broll_06_court_dismissed.png",
        "output_name": "broll_06_court_dismissed.mp4",
        "prompt": (
            "Static shot, camera holds still. A courtroom judge's gavel rests on a "
            "wooden bench beside a stamped dismissal document, paper edges softly "
            "curl, dust particles slowly drift through a beam of light. Cinematic noir."
        ),
    },
]


def load_dotenv_minimal() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def main() -> int:
    load_dotenv_minimal()
    if not (os.environ.get("KLING_API_KEY") or os.environ.get("FAL_KEY")):
        raise EnvironmentError("Neither KLING_API_KEY nor FAL_KEY is set (check .env)")

    KLING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    adapter = KlingI2VAdapter(output_dir=KLING_OUTPUT_DIR)

    print(f"[KLING] Generating {len(CLIPS)} I2V clips (Kling 2.6 Pro, 5s each)")
    print(f"[KLING] Expected cost: ${len(CLIPS) * 0.35:.2f}")
    print(f"[KLING] Expected time: ~{len(CLIPS) * 70 / 60:.1f} min sequential")
    print()

    t0 = time.time()
    for i, clip in enumerate(CLIPS, 1):
        anchor_path = SOURCES_DIR / clip["anchor"]
        if not anchor_path.exists():
            raise FileNotFoundError(f"Anchor not found: {anchor_path}")

        print(f"[KLING {i}/{len(CLIPS)}] {clip['anchor']}")
        print(f"  prompt: {clip['prompt'][:80]}...")
        t_clip = time.time()

        raw_path = adapter.image_to_video(
            prompt=clip["prompt"],
            anchor_frame=anchor_path,
            duration_seconds=5,
        )

        elapsed = time.time() - t_clip
        print(f"  raw:    {raw_path} ({elapsed:.1f}s)")

        # Copy to canonical sources/ location
        final_path = SOURCES_DIR / clip["output_name"]
        shutil.copy2(raw_path, final_path)
        size_mb = final_path.stat().st_size / 1024 / 1024
        print(f"  final:  {final_path} ({size_mb:.2f} MB)")
        print()

    total = time.time() - t0
    print(f"✅ 6 Kling I2V clips generated in {total/60:.1f} min")
    print(f"   Sources dir: {SOURCES_DIR}")
    for clip in CLIPS:
        out = SOURCES_DIR / clip["output_name"]
        if out.exists():
            print(f"   - {out.name} ({out.stat().st_size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
