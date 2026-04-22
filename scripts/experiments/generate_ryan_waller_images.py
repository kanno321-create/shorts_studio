"""Ryan Waller — 6 core b-roll images via gpt-image-2.

Session #33 first production smoke. Generates cinematic noir true-crime
documentary-style images for Remotion composition. Each image rotated
across multiple sentences via Ken Burns pan/zoom variations.

Output:
- outputs/gpt_image2/ryan-waller/img_{01-06}_*.png
- output/ryan-waller/sources/broll_{01-06}.png (production copy)

Cost: 6 × medium quality × $0.034/img = ~$0.20
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter  # noqa: E402

OUT_DIR = Path("outputs/gpt_image2/ryan-waller")
SOURCES_DIR = Path("output/ryan-waller/sources")

IMAGE_PROMPTS = [
    # 1. Interrogation room blur — Misdirection core
    {
        "id": "interrogation_blur",
        "filename": "img_01_interrogation_blur.png",
        "broll_name": "broll_01_interrogation.png",
        "prompt": (
            "Cinematic noir style police interrogation room scene, profile view of "
            "a young man seated at a metal table with his head tilted, left eye "
            "visibly swollen and bruised, disoriented and slumped posture, "
            "heavily desaturated blue-gray CCTV footage aesthetic, harsh overhead "
            "fluorescent lighting casting deep shadows, motion blur suggesting "
            "consciousness fading, institutional beige walls, grainy 1980s "
            "documentary film texture, photographic realism, no text, no logos, "
            "no faces clearly visible"
        ),
    },
    # 2. Christmas night exterior — Conflict setup
    {
        "id": "christmas_night_exterior",
        "filename": "img_02_christmas_night.png",
        "broll_name": "broll_02_christmas_night.png",
        "prompt": (
            "Dark suburban American house exterior at night during Christmas, warm "
            "amber light bleeding through drawn curtains of upstairs windows, light "
            "dusting of snow on the lawn and mailbox, muted multicolored holiday "
            "string lights wrapped around the porch, ominous stillness, cold blue "
            "moonlight mixed with warm indoor glow, cinematic true crime documentary "
            "aesthetic, desaturated color grade, vertical composition, photographic "
            "realism, no text"
        ),
    },
    # 3. Clock 6 hours — Build-up time pressure
    {
        "id": "clock_6hours",
        "filename": "img_03_clock_6hours.png",
        "broll_name": "broll_03_clock.png",
        "prompt": (
            "Extreme close-up of a vintage analog wall clock, hour hand pointing "
            "past six, second hand with slight motion blur, harsh overhead "
            "fluorescent light reflecting off glass face, dust particles visible in "
            "the beam, cold institutional setting suggesting a police station "
            "corridor, muted gray-green color palette, cinematic noir documentary "
            "style, shallow depth of field, vertical composition, no text other "
            "than clock numerals"
        ),
    },
    # 4. Fleeing silhouette night — Build-up climax
    {
        "id": "fleeing_silhouette",
        "filename": "img_04_fleeing_silhouette.png",
        "broll_name": "broll_04_fleeing.png",
        "prompt": (
            "Two adult male silhouettes running away through a dark urban alleyway "
            "at night, seen from behind, ominous orange sodium streetlamp casting "
            "long distorted shadows forward, cold blue-gray atmospheric fog, "
            "rain-damp pavement reflecting scattered light, urgent motion blur on "
            "the figures, cinematic noir true crime documentary aesthetic, vertical "
            "composition, grainy 35mm film texture, photographic realism, no text, "
            "no logos"
        ),
    },
    # 5. Hospital corridor empty — Reveal lead-up
    {
        "id": "hospital_corridor",
        "filename": "img_05_hospital_corridor.png",
        "broll_name": "broll_05_hospital.png",
        "prompt": (
            "Long empty hospital corridor seen in deep perspective, cold blue-green "
            "fluorescent lighting, distant surgical gurneys and medical equipment "
            "barely visible, sterile institutional atmosphere with pale tiled "
            "floors, abandoned and silent, strong vanishing point perspective, "
            "cinematic shallow depth of field, 1980s documentary aesthetic, muted "
            "desaturated color grade, vertical composition, no text, no readable "
            "signage"
        ),
    },
    # 6. Court dismissed — Aftermath
    {
        "id": "court_dismissed",
        "filename": "img_06_court_dismissed.png",
        "broll_name": "broll_06_court_dismissed.png",
        "prompt": (
            "Close-up overhead shot of a legal court document with a large red "
            "DISMISSED stamp pressed diagonally across it, wooden judge's gavel "
            "resting on dark polished mahogany desk beside it, soft overhead "
            "spotlight creating dramatic shadows, paper texture and ink bleeding "
            "visible, cinematic low-angle depth-of-field, cinematic noir documentary "
            "aesthetic, cold color grade with strong accent of red from the stamp, "
            "vertical composition, only the word DISMISSED readable, no other text"
        ),
    },
]


def load_dotenv_minimal() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
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
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY not set (check .env)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    adapter = GPTImage2Adapter(output_dir=OUT_DIR)

    print(f"[IMG] Generating {len(IMAGE_PROMPTS)} images @ medium quality")
    print(f"[IMG] Output dir: {OUT_DIR}")
    print(f"[IMG] Sources mirror: {SOURCES_DIR}")
    print()

    generated: list[tuple[str, Path]] = []
    for i, spec in enumerate(IMAGE_PROMPTS, 1):
        out_path = OUT_DIR / spec["filename"]
        print(f"[IMG] {i}/{len(IMAGE_PROMPTS)}: {spec['id']}")
        print(f"       prompt preview: {spec['prompt'][:100]}...")
        try:
            result_path = adapter.generate_scene(
                prompt=spec["prompt"],
                output_path=out_path,
                quality="medium",
            )
        except Exception as e:  # noqa: BLE001 — log + continue; partial output acceptable
            print(f"[IMG] FAILED {spec['id']}: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        # Mirror to sources/
        broll_path = SOURCES_DIR / spec["broll_name"]
        shutil.copyfile(result_path, broll_path)
        print(f"       → {result_path} + {broll_path}")
        generated.append((spec["id"], broll_path))

    print()
    print(f"✅ Image generation complete: {len(generated)}/{len(IMAGE_PROMPTS)}")
    for gid, p in generated:
        print(f"   {gid:25s} → {p}")
    return 0 if len(generated) == len(IMAGE_PROMPTS) else 1


if __name__ == "__main__":
    sys.exit(main())
