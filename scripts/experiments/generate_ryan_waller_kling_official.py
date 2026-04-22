"""Ryan Waller v3 — Kling 2.6 Pro via OFFICIAL Kuaishou API (not fal.ai proxy).

Session #34: 대표님 지시 — "kling에 직접들어가서해라 거기가 더 낫다. api크레딧도 많다".
KLING_ACCESS_KEY + KLING_SECRET_KEY (.env) → JWT HS256 → Bearer auth.

Endpoint (official Kuaishou Kling API — multiple regional bases tried):
  POST <base>/v1/videos/image2video          (create task)
  GET  <base>/v1/videos/image2video/<task_id> (poll status)

Kling 2.6 Pro model_name: `kling-v2-6` + mode="pro" + duration="10".

Idempotent: skips clips already present at output/ryan-waller/sources/.
"""
from __future__ import annotations

import base64
import os
import shutil
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass

# Force line-buffered output so background runs show progress
os.environ.setdefault("PYTHONUNBUFFERED", "1")

import jwt  # PyJWT
import requests

SOURCES_DIR = Path("output/ryan-waller/sources")
KLING_RAW_DIR = Path("outputs/kling/ryan-waller-official")
POLL_INTERVAL_S = 10
POLL_TIMEOUT_S = 900
DURATION_STR = "10"
MODE = "pro"          # Pro mode = Kling 2.6 Pro tier
MODEL_NAME = "kling-v2-6"
ASPECT_RATIO = "9:16"
CFG_SCALE = 0.5
NEG_PROMPT = (
    "static character, frozen pose, only camera movement, camera-only motion, "
    "motionless subject, still photo, no action, no movement, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing"
)

# Confirmed working base (probed 2026-04-23 — HTTP 200)
API_BASE = "https://api.klingai.com"


import builtins as _builtins

def _p(*args, **kwargs):
    """print + flush (counter Python stdout buffering under background runs)."""
    kwargs.setdefault("flush", True)
    _builtins.print(*args, **kwargs)

CLIPS = [
    ("broll_01_interrogation.png", "broll_01_interrogation_v3.mp4",
     "Static shot, camera holds still. A young man sits slumped in an "
     "interrogation chair under harsh overhead light, slowly blinks his "
     "swollen left eye, softly breathes out. Cinematic noir, cold tones."),
    ("broll_02_christmas_night.png", "broll_02_christmas_night_v3.mp4",
     "Static shot, camera holds still. A quiet suburban Phoenix house at "
     "night, faint Christmas lights gently flicker on the porch, cold mist "
     "softly drifts past the dark windows. Cinematic noir, deep shadows."),
    ("broll_03_clock.png", "broll_03_clock_v3.mp4",
     "Static shot, camera holds still. An old wall clock mounted on a dim "
     "interrogation room wall, the second hand slowly sweeps forward, soft "
     "shadow shifts across the dial. Cinematic noir, amber tungsten glow."),
    ("broll_04_fleeing.png", "broll_04_fleeing_v3.mp4",
     "Static shot, camera holds still. A lone silhouette walks away down a "
     "dark empty alley at night, shoulders gently rise and fall with heavy "
     "breath, coat softly moves in the breeze. Cinematic noir, blue wash."),
    ("broll_05_hospital.png", "broll_05_hospital_v3.mp4",
     "Static shot, camera holds still. An empty hospital corridor at late "
     "night, a single fluorescent light gently flickers overhead, polished "
     "floor softly reflects distant movement. Cinematic noir, cold cyan."),
    ("broll_06_court_dismissed.png", "broll_06_court_dismissed_v3.mp4",
     "Static shot, camera holds still. A courtroom judge's gavel rests on a "
     "wooden bench beside a stamped dismissal document, paper edges softly "
     "curl, dust particles slowly drift through a beam of light. Cinematic noir."),
]


def load_dotenv_minimal() -> None:
    env = Path(".env")
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def make_jwt_token(ak: str, sk: str) -> str:
    now = int(time.time())
    payload = {"iss": ak, "exp": now + 1800, "nbf": now - 5}
    return jwt.encode(payload, sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"})


def image_to_base64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def discover_base(ak: str, sk: str) -> str:
    """Return confirmed API_BASE (probed 2026-04-23 — https://api.klingai.com)."""
    _ = ak, sk  # future-proof signature
    _p(f"[KLING-official] Using confirmed base: {API_BASE}")
    return API_BASE


def create_task(base: str, ak: str, sk: str, image_path: Path, prompt: str) -> str:
    token = make_jwt_token(ak, sk)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "model_name": MODEL_NAME,
        "mode": MODE,
        "duration": DURATION_STR,
        "aspect_ratio": ASPECT_RATIO,
        "cfg_scale": CFG_SCALE,
        "image": image_to_base64(image_path),  # inline base64 (no external hosting needed)
        "prompt": prompt,
        "negative_prompt": NEG_PROMPT,
    }
    r = requests.post(f"{base}/v1/videos/image2video", headers=headers, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"create_task HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    # common response shapes
    task_id = (
        (data.get("data") or {}).get("task_id")
        or data.get("task_id")
        or (data.get("data") or {}).get("id")
    )
    if not task_id:
        raise RuntimeError(f"no task_id in response: {data}")
    return task_id


def poll_task(base: str, ak: str, sk: str, task_id: str) -> str:
    """Return video URL when task succeeds. Raises on failure/timeout."""
    url = f"{base}/v1/videos/image2video/{task_id}"
    t0 = time.time()
    last_status = None
    while time.time() - t0 < POLL_TIMEOUT_S:
        token = make_jwt_token(ak, sk)  # rotate JWT per poll (cheap)
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code >= 500:
            time.sleep(POLL_INTERVAL_S)
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"poll HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        inner = data.get("data") or data
        status = (
            inner.get("task_status")
            or inner.get("status")
            or (inner.get("task") or {}).get("status")
        )
        if status != last_status:
            _p(f"    task {task_id[:8]}… status={status} ({time.time()-t0:.0f}s)")
            last_status = status
        if status in ("succeed", "success", "completed", "done"):
            result = (
                inner.get("task_result")
                or inner.get("result")
                or (inner.get("task") or {}).get("result")
                or inner
            )
            videos = result.get("videos") or []
            if videos and isinstance(videos, list):
                video_url = videos[0].get("url") or videos[0].get("video_url")
                if video_url:
                    return video_url
            # fallback shapes
            video_url = inner.get("video_url") or inner.get("url")
            if video_url:
                return video_url
            raise RuntimeError(f"succeeded but no video URL: {data}")
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"task failed: {data}")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"poll timeout after {POLL_TIMEOUT_S}s")


def download(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"kling_official_{stamp}.mp4"
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with out.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=131072):
                if chunk:
                    fh.write(chunk)
    return out


def main() -> int:
    load_dotenv_minimal()
    ak = os.environ.get("KLING_ACCESS_KEY")
    sk = os.environ.get("KLING_SECRET_KEY")
    if not ak or not sk:
        raise EnvironmentError("KLING_ACCESS_KEY / KLING_SECRET_KEY missing in .env")

    KLING_RAW_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    _p("[KLING-official] Discovering API base...")
    base = discover_base(ak, sk)
    _p(f"[KLING-official] Using base: {base}")
    _p()

    todo = [(a, o, p) for a, o, p in CLIPS if not (SOURCES_DIR / o).exists()]
    skip = len(CLIPS) - len(todo)
    if skip:
        _p(f"[KLING-official] {skip} clip(s) already exist — skipping")

    _p(f"[KLING-official] Generating {len(todo)} Kling 2.6 Pro clips, {DURATION_STR}s, mode={MODE}")
    _p(f"[KLING-official] Expected cost: credit-based (dashboard check)")
    _p()

    t0 = time.time()
    for i, (anchor_name, output_name, prompt) in enumerate(todo, 1):
        anchor_path = SOURCES_DIR / anchor_name
        if not anchor_path.exists():
            raise FileNotFoundError(f"Anchor not found: {anchor_path}")
        _p(f"[KLING-official {i}/{len(todo)}] {anchor_name}")
        _p(f"  prompt: {prompt[:80]}...")
        t_clip = time.time()
        try:
            task_id = create_task(base, ak, sk, anchor_path, prompt)
            _p(f"  task_id: {task_id}")
            video_url = poll_task(base, ak, sk, task_id)
            raw_path = download(video_url, KLING_RAW_DIR)
        except Exception as exc:
            _p(f"  ERROR: {exc!r}")
            raise
        elapsed = time.time() - t_clip
        final = SOURCES_DIR / output_name
        shutil.copy2(raw_path, final)
        size_mb = final.stat().st_size / 1024 / 1024
        _p(f"  raw : {raw_path.name}")
        _p(f"  final: {final} ({size_mb:.2f} MB, {elapsed:.0f}s total)")
        _p()

    total = time.time() - t0
    _p(f"✅ {len(todo)} Kling 2.6 Pro clips (official API) in {total/60:.1f} min")
    for a, o, _ in CLIPS:
        p = SOURCES_DIR / o
        if p.exists():
            _p(f"   · {p.name} ({p.stat().st_size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
