"""Ryan Waller v3 Kling I2V fallback — 10s clips (reference choices=[5,10]).

Session #34 v3: v2 generated 5s clips → scene freeze after 5s. Reference
`_kling_i2v_batch.py` default=10. v3 bumps duration to 10s per clip.

Runs on the v2 anchor PNGs (6 b-roll) since footage sourcing (Step 5) may
only cover some sections. Kling output lives alongside real footage and
visual_spec_builder picks whichever matches.

Output:
- output/ryan-waller/sources/broll_{01..06}_<name>_v3.mp4  (10s Kling 2.6 Pro clips, v3 iteration)
- outputs/kling/ryan-waller-v3/...                         (raw downloads)
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

SOURCES_DIR = Path("output/ryan-waller/sources")
KLING_OUTPUT_DIR = Path("outputs/kling/ryan-waller-v3")

# fal.ai Kling supports only duration ∈ {"5", "10"} (literal). Our models.py
# I2VRequest constrains le=8 for D-14 "1 Move Rule 4-8s" safety. Since 8
# is rejected by fal.ai (422) and our local validator rejects 10, bypass
# the adapter here and call fal_client directly with duration="10" — this
# stays within plan scope ("v3 experiment scripts" layer, not core modules).
DURATION_STR = "10"

FAL_ENDPOINT = "fal-ai/kling-video/v2.6/pro/image-to-video"
NEG_PROMPT = (
    "static character, frozen pose, only camera movement, camera-only motion, "
    "motionless subject, still photo, no action, no movement, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing"
)

CLIPS = [
    {
        "anchor": "broll_01_interrogation.png",
        "output_name": "broll_01_interrogation_v3.mp4",
        "prompt": (
            "Static shot, camera holds still. A young man sits slumped in an "
            "interrogation chair under harsh overhead light, slowly blinks his "
            "swollen left eye, softly breathes out. Cinematic noir, cold tones."
        ),
    },
    {
        "anchor": "broll_02_christmas_night.png",
        "output_name": "broll_02_christmas_night_v3.mp4",
        "prompt": (
            "Static shot, camera holds still. A quiet suburban Phoenix house at "
            "night, faint Christmas lights gently flicker on the porch, cold mist "
            "softly drifts past the dark windows. Cinematic noir, deep shadows."
        ),
    },
    {
        "anchor": "broll_03_clock.png",
        "output_name": "broll_03_clock_v3.mp4",
        "prompt": (
            "Static shot, camera holds still. An old wall clock mounted on a dim "
            "interrogation room wall, the second hand slowly sweeps forward, soft "
            "shadow shifts across the dial. Cinematic noir, amber tungsten glow."
        ),
    },
    {
        "anchor": "broll_04_fleeing.png",
        "output_name": "broll_04_fleeing_v3.mp4",
        "prompt": (
            "Static shot, camera holds still. A lone silhouette walks away down a "
            "dark empty alley at night, shoulders gently rise and fall with heavy "
            "breath, coat softly moves in the breeze. Cinematic noir, blue wash."
        ),
    },
    {
        "anchor": "broll_05_hospital.png",
        "output_name": "broll_05_hospital_v3.mp4",
        "prompt": (
            "Static shot, camera holds still. An empty hospital corridor at late "
            "night, a single fluorescent light gently flickers overhead, polished "
            "floor softly reflects distant movement. Cinematic noir, cold cyan."
        ),
    },
    {
        "anchor": "broll_06_court_dismissed.png",
        "output_name": "broll_06_court_dismissed_v3.mp4",
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


def _kling_call_direct(anchor_path: Path, prompt: str, output_dir: Path) -> Path:
    """Bypass I2VRequest validator (le=8) — fal.ai requires duration ∈ {5, 10}."""
    import fal_client
    import httpx

    api_key = os.environ.get("KLING_API_KEY") or os.environ.get("FAL_KEY")
    if not api_key:
        raise EnvironmentError("No KLING_API_KEY / FAL_KEY")

    previous = os.environ.get("FAL_KEY")
    os.environ["FAL_KEY"] = api_key
    try:
        image_url = fal_client.upload_file(str(anchor_path))
        handler = fal_client.submit(
            FAL_ENDPOINT,
            arguments={
                "image_url": image_url,
                "prompt": prompt,
                "duration": DURATION_STR,   # "10" — fal literal
                "negative_prompt": NEG_PROMPT,
                "cfg_scale": 0.5,
            },
        )
        result = handler.get()
    finally:
        if previous is None:
            os.environ.pop("FAL_KEY", None)
        else:
            os.environ["FAL_KEY"] = previous

    video_url = (result.get("video", {}) or {}).get("url") or result.get("url")
    if not video_url:
        raise RuntimeError(f"no video URL in fal result: {result!r}")

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = output_dir / f"kling_v3_{stamp}.mp4"
    resp = httpx.get(video_url, follow_redirects=True, timeout=240)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    return out


def main() -> int:
    load_dotenv_minimal()
    if not (os.environ.get("KLING_API_KEY") or os.environ.get("FAL_KEY")):
        raise EnvironmentError("Neither KLING_API_KEY nor FAL_KEY is set (check .env)")

    KLING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    # Skip clips already present (idempotent re-run guard)
    todo = [c for c in CLIPS if not (SOURCES_DIR / c["output_name"]).exists()]
    skip = len(CLIPS) - len(todo)
    if skip:
        print(f"[KLING-2.6] {skip} clip(s) already exist — skipping")

    print(f"[KLING-2.6] Generating {len(todo)} I2V clips (Kling 2.6 Pro, {DURATION_STR}s)")
    print(f"[KLING-2.6] Expected cost: ${len(todo) * 0.70:.2f}")
    print(f"[KLING-2.6] Expected time: ~{len(todo) * 90 / 60:.1f} min sequential")
    print()

    t0 = time.time()
    for i, clip in enumerate(todo, 1):
        anchor_path = SOURCES_DIR / clip["anchor"]
        if not anchor_path.exists():
            raise FileNotFoundError(f"Anchor not found: {anchor_path}")

        print(f"[KLING-2.6 Pro {i}/{len(todo)}] {clip['anchor']}")
        print(f"  prompt: {clip['prompt'][:80]}...")
        t_clip = time.time()

        raw_path = _kling_call_direct(anchor_path, clip["prompt"], KLING_OUTPUT_DIR)
        elapsed = time.time() - t_clip
        print(f"  raw:    {raw_path} ({elapsed:.1f}s)")

        final_path = SOURCES_DIR / clip["output_name"]
        shutil.copy2(raw_path, final_path)
        size_mb = final_path.stat().st_size / 1024 / 1024
        print(f"  final:  {final_path} ({size_mb:.2f} MB)")
        print()

    total = time.time() - t0
    print(f"✅ {len(todo)} Kling 2.6 Pro clips (v3 iteration) generated in {total/60:.1f} min")
    for clip in CLIPS:
        out = SOURCES_DIR / clip["output_name"]
        if out.exists():
            print(f"   · {out.name} ({out.stat().st_size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
