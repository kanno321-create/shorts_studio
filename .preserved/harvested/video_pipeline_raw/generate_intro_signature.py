"""Session 43 — 사건기록부 channel intro signature Veo generation.

Generates a reusable 8-second Veo clip for the Hook ('오늘의 기록입니다') moment
of every incidents channel short. Saves to output/_shared/signatures/ for future
reuse, and copies to current episode sources/.

Concept:
- 1940s neo-noir private detective's dim office
- Over-the-shoulder shot from behind — only fedora hat silhouette + gloved hands
- Leather case notebook being opened, brass fountain pen, warm amber desk lamp
- Rain-streaked window in soft-focus background
- No face, no text (channel name added via Remotion overlay later)
"""
import os
import shutil
import sys
from pathlib import Path

# Load .env manually (GOOGLE_API_KEY required) — dotenv not installed in video-pipeline venv
_env_path = Path(".env")
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

sys.path.insert(0, str(Path("scripts/video-pipeline").resolve()))
from ai_visual_generate import VeoClient  # noqa: E402

PROMPT = (
    "A tall mysterious private detective standing alone in a deeply atmospheric dim "
    "noir office at night, vertical 9:16 cinematic frame, single continuous 8-second "
    "shot. The air feels cold, still, and solitary. The shot opens with a "
    "three-quarter back angle — he is turned mostly away from camera, only the "
    "faintest sliver of his side profile visible. He wears a long dark trench coat "
    "and a classic 1940s black fedora hat, standing tall and perfectly still. "
    "In his hands he holds an open leather-bound case notebook, his head tilted "
    "downward reading it with quiet measured concentration. For the first three "
    "seconds he stands motionless studying the notebook. Then with deliberate "
    "slow grace he begins to rotate his entire body toward the camera, still "
    "holding the open notebook, his head remaining bowed downward the whole time "
    "so his face stays hidden beneath the deep shadow of the fedora brim. By the "
    "final two seconds he has fully turned to face the camera directly. At the "
    "very last moment he lifts only his eyes — not his head — from beneath the "
    "shadowed brim, his face still tilted slightly downward, and fixes the viewer "
    "with a quiet still gravitas-heavy upward gaze locked straight into the camera, "
    "a silent weighted stare from under the hat shadow. Deep dark atmospheric noir "
    "office background with moody midnight blue and black shadows. Strong warm amber "
    "rim light from a distant tall window behind him catches the edges of his coat "
    "shoulders and fedora brim, creating a dramatic silhouette outline against the "
    "darkness. Faint rain streaks softly visible on the tall window, soft warm amber "
    "streetlight glow bleeding through from outside. Very slow subtle cinematic "
    "push-in. Cinematic neo-noir true crime documentary style, 1980s detective film "
    "color grading, deep midnight blues contrasted against warm amber rim lights, "
    "high contrast chiaroscuro shadows, rich dark browns and brass tones, shallow "
    "depth of field, subtle film grain, low camera angle looking slightly up at him. "
    "No cigarette, no smoke, no text, no logos, no modern elements, no gore. "
    "Atmosphere of solitary gravitas, quiet authority, mystery, and a measured "
    "silent weight at the final moment."
)

veo_config = {
    "model": "veo-3.1-lite-generate-preview",
    "default_duration": 8,
    "timeout": 240,
}

print("[1/4] Initializing VeoClient...")
veo = VeoClient(veo_config)

shared_dir = Path("output/_shared/signatures")
shared_dir.mkdir(parents=True, exist_ok=True)
shared_path = shared_dir / "incidents_intro_v4_silent_glare.mp4"

print(f"[2/4] Generating Veo 3.1 Lite signature clip (duration=8s, ~60-120s wait)...")
result = veo.generate_video(PROMPT, str(shared_path), duration=8)
print(f"[3/4] Generated: {result}")

if not shared_path.exists():
    print(f"ERROR: output file missing at {shared_path}")
    sys.exit(1)

size_mb = shared_path.stat().st_size / (1024 * 1024)
print(f"[OK] Shared signature saved: {shared_path} ({size_mb:.2f} MB)")

# Copy to current episode sources
episode_source = Path("output/kitakyushu-matsunaga/sources/veo_03_intro_signature.mp4")
shutil.copy2(shared_path, episode_source)
print(f"[4/4] Copied to episode: {episode_source}")

print("\n=== INTRO SIGNATURE READY ===")
print(f"Shared: {shared_path}")
print(f"Episode: {episode_source}")
