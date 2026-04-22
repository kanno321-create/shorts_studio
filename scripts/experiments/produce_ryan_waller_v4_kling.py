"""Ryan Waller v4 Step 3b — Case C Kling I2V producer (parallel max 3).

INVARIANT Rule 1: reads script_v4.json first.
Case C (9 shots): new Kling 2.6 Pro I2V call per shot, anchor = existing broll_0X.png.
Each result → ffmpeg trim to shot.duration_hint_s → shot_final/<shot_id>_final.mp4

Parallel: ThreadPoolExecutor with 3 workers (Plan max 3 / Kling rate limit).
Idempotent: skip shots whose final mp4 already exists.
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
    "static character, frozen pose, only camera movement, camera-only motion, "
    "motionless subject, still photo, no action, no movement, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing, "
    "text overlay, watermark, logo"
)
POLL_INTERVAL_S = 10
POLL_TIMEOUT_S = 900
MAX_WORKERS = 3

# Case C — shot_id → (anchor_png, prompt_override_optional)
CASE_C_SHOTS = [
    ("hook_s02_phoenix_arizona",           "broll_02_christmas_night.png"),
    ("hook_s04_heather_body",              "broll_02_christmas_night.png"),
    ("hook_s05_interrogation_6hours",      "broll_01_interrogation.png"),
    ("body_scene_s01_heather_victim",      "broll_02_christmas_night.png"),
    ("body_scene_s02_phoenix_shooting",    "broll_02_christmas_night.png"),
    ("watson_q2_s01_flee_shock",           "broll_04_fleeing.png"),
    ("reveal_s01_carver_father_son",       "broll_06_court_dismissed.png"),
    ("reveal_s02_doorway_ambush",          "broll_02_christmas_night.png"),
    ("aftermath_watson_s01_cta",           "broll_01_interrogation.png"),
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
    payload = {"iss": ak, "exp": now + 1800, "nbf": now - 5}
    return jwt.encode(payload, sk, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"})


def image_to_b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def create_task(ak: str, sk: str, image_path: Path, prompt: str) -> str:
    token = make_jwt(ak, sk)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "model_name": MODEL_NAME, "mode": MODE, "duration": DURATION_STR,
        "aspect_ratio": ASPECT_RATIO, "cfg_scale": CFG_SCALE,
        "image": image_to_b64(image_path),
        "prompt": prompt, "negative_prompt": NEG_PROMPT,
    }
    r = requests.post(f"{API_BASE}/v1/videos/image2video",
                      headers=headers, json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"create_task HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    tid = (data.get("data") or {}).get("task_id") or data.get("task_id") \
        or (data.get("data") or {}).get("id")
    if not tid:
        raise RuntimeError(f"no task_id: {data}")
    return tid


def poll_task(ak: str, sk: str, task_id: str, shot_id: str) -> str:
    url = f"{API_BASE}/v1/videos/image2video/{task_id}"
    t0 = time.time()
    last = None
    while time.time() - t0 < POLL_TIMEOUT_S:
        token = make_jwt(ak, sk)
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if r.status_code >= 500:
            time.sleep(POLL_INTERVAL_S); continue
        if r.status_code >= 400:
            raise RuntimeError(f"poll HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        inner = data.get("data") or data
        status = inner.get("task_status") or inner.get("status") \
            or (inner.get("task") or {}).get("status")
        if status != last:
            _p(f"  [{shot_id[:35]:<35s}] task={task_id[:8]}... status={status} ({time.time()-t0:.0f}s)")
            last = status
        if status in ("succeed", "success", "completed", "done"):
            result = inner.get("task_result") or inner.get("result") \
                or (inner.get("task") or {}).get("result") or inner
            videos = result.get("videos") or []
            if videos and isinstance(videos, list):
                url2 = videos[0].get("url") or videos[0].get("video_url")
                if url2:
                    return url2
            url2 = inner.get("video_url") or inner.get("url")
            if url2:
                return url2
            raise RuntimeError(f"succeed but no video url: {data}")
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"task failed: {data}")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"poll timeout {POLL_TIMEOUT_S}s for {shot_id}")


def download_video(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with dst.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=131072):
                if chunk:
                    fh.write(chunk)


def trim_to_shot(raw: Path, dst: Path, target_dur: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    src_dur = probe_duration(raw)
    start = max(0.0, (src_dur - target_dur) / 2.0) if src_dur > target_dur + 0.5 else 0.0
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{target_dur:.3f}",
        "-i", str(raw),
        "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
               "setsar=1,setpts=PTS-STARTPTS",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an",
        str(dst),
    ], check=True, capture_output=True)


def process_shot(shot_id: str, anchor_name: str, shot: dict, ak: str, sk: str) -> dict:
    anchor = SOURCES / anchor_name
    if not anchor.exists():
        raise FileNotFoundError(f"anchor missing: {anchor}")
    final = SHOT_FINAL / f"{shot_id}_final.mp4"
    if final.exists():
        dur = probe_duration(final)
        return {"shot_id": shot_id, "status": "skipped_exists",
                "final": str(final), "duration": dur}
    prompt = shot.get("i2v_prompt_en") or ""
    if not prompt:
        raise ValueError(f"shot {shot_id} missing i2v_prompt_en")
    target = shot["duration_hint_s"]
    t0 = time.time()
    _p(f"  [{shot_id[:35]:<35s}] create task, anchor={anchor_name}")
    task_id = create_task(ak, sk, anchor, prompt)
    video_url = poll_task(ak, sk, task_id, shot_id)
    raw = KLING_RAW / f"{shot_id}_kling_raw.mp4"
    download_video(video_url, raw)
    trim_to_shot(raw, final, target)
    actual = probe_duration(final)
    _p(f"  [{shot_id[:35]:<35s}] DONE final={final.name} "
       f"target={target:.3f}s actual={actual:.3f}s elapsed={time.time()-t0:.0f}s")
    return {"shot_id": shot_id, "status": "kling_i2v_new",
            "anchor": anchor_name, "task_id": task_id, "raw": str(raw),
            "final": str(final), "target_duration": target, "actual_duration": actual,
            "prompt": prompt[:120], "elapsed_s": round(time.time() - t0, 1)}


def main() -> int:
    load_dotenv_minimal()
    ak = os.environ.get("KLING_ACCESS_KEY")
    sk = os.environ.get("KLING_SECRET_KEY")
    if not ak or not sk:
        raise EnvironmentError("KLING_ACCESS_KEY/KLING_SECRET_KEY missing in .env")

    _p("[Agent 2 Producer v4 Kling] reads script_v4.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V4.read_text(encoding="utf-8"))
    shots_by_id: dict[str, dict] = {}
    for sec in script["sections"]:
        for shot in sec["shots"]:
            shots_by_id[shot["shot_id"]] = shot

    SHOT_FINAL.mkdir(parents=True, exist_ok=True)
    KLING_RAW.mkdir(parents=True, exist_ok=True)

    pending = []
    for sid, anchor in CASE_C_SHOTS:
        if sid not in shots_by_id:
            raise KeyError(f"shot_id {sid} not in script_v4")
        pending.append((sid, anchor, shots_by_id[sid]))

    _p(f"[Kling I2V] {len(pending)} shots, parallel workers={MAX_WORKERS}")
    _p(f"[Kling I2V] endpoint={API_BASE} model={MODEL_NAME} mode={MODE} duration={DURATION_STR}s")
    t0 = time.time()
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(process_shot, sid, anchor, shot, ak, sk): sid
                for sid, anchor, shot in pending}
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                results.append(fut.result())
            except Exception as exc:
                _p(f"  [{sid}] FAILED: {exc!r}")
                results.append({"shot_id": sid, "status": "failed", "error": repr(exc)})

    _p(f"\nDONE {len(results)} shots in {(time.time()-t0)/60:.1f} min")
    # Write per-run manifest
    out_manifest = Path("output/ryan-waller/kling_v4_runlog.json")
    out_manifest.write_text(json.dumps({
        "endpoint": API_BASE, "model": MODEL_NAME, "mode": MODE,
        "duration_s": DURATION_STR, "parallel_workers": MAX_WORKERS,
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"[Kling I2V] runlog: {out_manifest}")
    for r in results:
        st = r.get("status", "?")
        sid = r.get("shot_id", "?")
        if st == "failed":
            _p(f"  FAIL {sid}: {r.get('error','?')}")
    return 0 if all(r.get("status") != "failed" for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
