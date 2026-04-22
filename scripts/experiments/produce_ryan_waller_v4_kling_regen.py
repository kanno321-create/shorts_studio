"""Ryan Waller v4 Step 3d — Kling regen for Inspector-flagged 7 shots.

INVARIANT Rule 1: reads script_v4.json first.
After Agent 4 Inspector (v4 1st pass) flagged 4 fail + 3 concern:
  - Force-regenerate with corrected prompts (no baked text, Phoenix-desert aesthetic,
    stronger motion hints, different anchors where needed).
  - Overwrites existing shot_final/<shot_id>_final.mp4 + kling_raw/<shot_id>_kling_raw.mp4.
"""
from __future__ import annotations
import base64
import builtins as _b
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass
os.environ.setdefault("PYTHONUNBUFFERED", "1")

import jwt
import requests


def _p(*a, **k):
    k.setdefault("flush", True); _b.print(*a, **k)


SCRIPT_V4 = Path("output/ryan-waller/script_v4.json")
SOURCES = Path("output/ryan-waller/sources")
SHOT_FINAL = SOURCES / "shot_final"
KLING_RAW = Path("outputs/kling/ryan-waller-v4")

API_BASE = "https://api.klingai.com"
MODEL_NAME = "kling-v2-6"
MODE = "pro"
DURATION_STR = "10"
ASPECT_RATIO = "9:16"
CFG_SCALE = 0.5
NEG_PROMPT = (
    "frozen pose, motionless subject, still photo, no action, no movement, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing, "
    "text overlay, watermark, logo, "
    "gibberish text, fake letters, name card with text, stamp, "
    "snow, colonial architecture"
)
POLL_INTERVAL_S = 10
POLL_TIMEOUT_S = 900
MAX_WORKERS = 3

# 7 regen shots — (shot_id, anchor, new_prompt)
REGEN_SHOTS = [
    # Tier 1 — critical fails
    ("hook_s02_phoenix_arizona",
     "broll_02_christmas_night.png",
     "Aerial night shot over Phoenix Arizona suburban desert, flat horizon with distant city lights, "
     "stucco roofs and palm tree silhouettes, warm lights on houses, NO SNOW, NO COLONIAL ARCHITECTURE, "
     "slow push-in, cinematic desert night tone"),
    ("hook_s04_heather_body",
     "broll_01_interrogation.png",
     "Dim suburban living room interior at night, indoor scene only, a soft silhouette shape on the floor "
     "viewed from a distance through a doorway, warm lamp in corner, no outdoor visible, NO SNOW, "
     "subtle camera drift forward, cinematic moody lighting, no text"),
    ("body_scene_s01_heather_victim",
     "broll_01_interrogation.png",
     "Dim interior scene with a soft silhouette of a young woman standing near a window with curtain, "
     "soft backlight, melancholic memorial tone, subtle head turn, "
     "NO TEXT, NO LETTERS, NO NAME CARD, NO OVERLAYS, cinematic moody framing"),
    ("reveal_s01_carver_father_son",
     "broll_01_interrogation.png",
     "Two silhouetted male figures standing side by side in a dim interrogation room, "
     "one older with shorter gray hair, one younger, both in profile against a wall, "
     "solemn stance, subtle breath motion, "
     "NO TEXT, NO LABELS, NO NAMES, NO STAMPS, NO CAPTIONS, cinematic noir lighting"),
    # Tier 2 — concerns (prompt strengthening)
    ("reveal_s02_doorway_ambush",
     "broll_02_christmas_night.png",
     "Suburban front door slightly ajar at night, strong silhouette of a gun muzzle protruding through "
     "the narrow door gap, soft red Christmas porch lights framing edge, tense still atmosphere, "
     "camera holds, cinematic crime noir, NO TEXT, NO SNOW"),
    ("body_6hours_s03_real_killer_fleeing_phoenix",
     "broll_04_fleeing.png",
     "Aerial wide night shot over Arizona desert highway leaving Phoenix, lone vehicle on the straight "
     "road, red tail lights fading into the distance, sparse desert landscape, "
     "NO URBAN ALLEY, NO WET STREET, cinematic tone, slow drift"),
    ("aftermath_det_s01_brain_eye_loss",
     "broll_05_hospital.png",
     "Dim hospital room with a clear silhouette of a male patient wearing an eye patch and hospital gown, "
     "lying/sitting on a bed, soft window light from the side, IV stand beside, "
     "static camera hold, cinematic memorial somber tone, NO TEXT"),
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


def make_jwt(ak: str, sk: str) -> str:
    now = int(time.time())
    return jwt.encode({"iss": ak, "exp": now + 1800, "nbf": now - 5},
                      sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"})


def image_to_b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def probe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def create_task(ak, sk, image_path, prompt):
    token = make_jwt(ak, sk)
    body = {
        "model_name": MODEL_NAME, "mode": MODE, "duration": DURATION_STR,
        "aspect_ratio": ASPECT_RATIO, "cfg_scale": CFG_SCALE,
        "image": image_to_b64(image_path),
        "prompt": prompt, "negative_prompt": NEG_PROMPT,
    }
    r = requests.post(f"{API_BASE}/v1/videos/image2video",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"create HTTP {r.status_code}: {r.text[:400]}")
    d = r.json()
    tid = (d.get("data") or {}).get("task_id") or d.get("task_id")
    if not tid:
        raise RuntimeError(f"no task_id: {d}")
    return tid


def poll_task(ak, sk, task_id, shot_id):
    url = f"{API_BASE}/v1/videos/image2video/{task_id}"
    t0 = time.time()
    last = None
    while time.time() - t0 < POLL_TIMEOUT_S:
        token = make_jwt(ak, sk)
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if r.status_code >= 500:
            time.sleep(POLL_INTERVAL_S); continue
        if r.status_code >= 400:
            raise RuntimeError(f"poll HTTP {r.status_code}: {r.text[:400]}")
        d = r.json(); inner = d.get("data") or d
        status = inner.get("task_status") or inner.get("status")
        if status != last:
            _p(f"  [{shot_id[:35]:<35s}] task={task_id[:8]}... status={status} ({time.time()-t0:.0f}s)")
            last = status
        if status in ("succeed", "success", "completed", "done"):
            result = inner.get("task_result") or inner.get("result") or inner
            videos = result.get("videos") or []
            if videos:
                url2 = videos[0].get("url") or videos[0].get("video_url")
                if url2:
                    return url2
            url2 = inner.get("video_url") or inner.get("url")
            if url2:
                return url2
            raise RuntimeError(f"no url: {d}")
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"failed: {d}")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"{shot_id} {POLL_TIMEOUT_S}s")


def download_video(url, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dst.open("wb") as fh:
            for c in r.iter_content(131072):
                if c: fh.write(c)


def trim_to_dur(src, dst, target):
    dst.parent.mkdir(parents=True, exist_ok=True)
    sd = probe_duration(src)
    start = max(0.0, (sd - target) / 2.0) if sd > target + 0.5 else 0.0
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{target:.3f}",
        "-i", str(src),
        "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
               "setsar=1,setpts=PTS-STARTPTS",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-an",
        str(dst),
    ], check=True, capture_output=True)


def process_shot(shot_id, anchor_name, new_prompt, shot, ak, sk):
    anchor = SOURCES / anchor_name
    if not anchor.exists():
        raise FileNotFoundError(f"anchor missing: {anchor}")
    final = SHOT_FINAL / f"{shot_id}_final.mp4"
    raw = KLING_RAW / f"{shot_id}_kling_raw.mp4"
    # Force delete previous to avoid idempotent skip
    if final.exists():
        final.unlink()
    if raw.exists():
        raw.unlink()
    target = shot["duration_hint_s"]
    t0 = time.time()
    _p(f"  [{shot_id[:35]:<35s}] REGEN anchor={anchor_name} prompt_len={len(new_prompt)}")
    task_id = create_task(ak, sk, anchor, new_prompt)
    url = poll_task(ak, sk, task_id, shot_id)
    download_video(url, raw)
    trim_to_dur(raw, final, target)
    actual = probe_duration(final)
    _p(f"  [{shot_id[:35]:<35s}] DONE target={target:.3f}s actual={actual:.3f}s elapsed={time.time()-t0:.0f}s")
    return {"shot_id": shot_id, "status": "regen_ok", "anchor": anchor_name,
            "new_prompt": new_prompt[:160], "task_id": task_id,
            "target": target, "actual": actual, "elapsed_s": round(time.time()-t0,1)}


def main() -> int:
    load_dotenv_minimal()
    ak = os.environ.get("KLING_ACCESS_KEY")
    sk = os.environ.get("KLING_SECRET_KEY")
    if not ak or not sk:
        raise EnvironmentError("KLING keys missing")

    _p("[Agent 2 Regen v4] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    shots_by_id = {}
    for sec in script["sections"]:
        for s in sec["shots"]:
            shots_by_id[s["shot_id"]] = s

    pending = [(sid, a, p, shots_by_id[sid]) for sid, a, p in REGEN_SHOTS if sid in shots_by_id]
    _p(f"[Regen v4] {len(pending)} shots to regenerate, workers={MAX_WORKERS}")
    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(process_shot, sid, a, p, shot, ak, sk): sid
                for sid, a, p, shot in pending}
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                _p(f"  [{sid}] FAIL: {e!r}")
                results.append({"shot_id": sid, "status": "failed", "error": repr(e)})

    _p(f"\nDONE {len(results)} regen shots in {(time.time()-t0)/60:.1f} min")
    Path("output/ryan-waller/kling_v4_regen_runlog.json").write_text(
        json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(r.get("status") != "failed" for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
