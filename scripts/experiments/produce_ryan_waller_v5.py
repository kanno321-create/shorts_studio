"""Ryan Waller v5 Producer — script-driven runtime prompt generation.

🔴 INVARIANT Rule 1 (enforced by code): first action = Read script_v5.json, log to stdout.
🔴 INVARIANT Rule 2 (enforced by code): every Kling T2I/I2V prompt is built ONLY from
   shot.text + shot.{emotion,situation,motion}_markers. No hardcoded anchor fallback.
   No external assets reused. Each shot gets a fresh Kling T2I anchor.

v5 visual modes:
  - "real_footage"   : Full Interrogation trim at shot.doc_source_timestamp_s
  - "kling_t2i_i2v"  : runtime T2I anchor → runtime I2V (prompts both built from shot)
  - "overlay_text"   : ffmpeg drawtext black-bg text card (shot.overlay_config)

Each mode produces `output/ryan-waller/sources/shot_final/<shot_id>_final.mp4`.
Parallel: Kling ops use ThreadPoolExecutor(max=3) per Plan rate-limit guard.
"""
from __future__ import annotations
import base64
import builtins as _b
import json
import os
import subprocess
import sys
import tempfile
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass
os.environ.setdefault("PYTHONUNBUFFERED", "1")

import jwt


def _p(*a, **k):
    k.setdefault("flush", True); _b.print(*a, **k)


SCRIPT_V5 = Path("output/ryan-waller/script_v5.json")
EP = Path("output/ryan-waller")
SHOT_FINAL = EP / "sources/shot_final"
KLING_ANCHORS = EP / "sources/anchors_v5"
KLING_RAW = Path("outputs/kling/ryan-waller-v5")
FULL_INTERROGATION = EP / "sources/real/raw_documentaries/ZI8G0KOOtqk_Ryan Waller Full Interrogation.mp4"
MANIFEST = EP / "producer_v5_manifest.json"
FONT_WIN = "C\\:/Windows/Fonts/malgunbd.ttf"

API_BASE = "https://api.klingai.com"
KLING_T2I_MODEL = "kling-v1-5"
KLING_I2V_MODEL = "kling-v2-6"
KLING_I2V_MODE = "pro"
KLING_I2V_DURATION = "10"
ASPECT = "9:16"
T2I_NEG = "text, letters, writing, gibberish, watermark, logo, caption, name card, stamp, cartoon, anime, illustration"
I2V_NEG = (
    "frozen pose, motionless subject, still photo, no action, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing, "
    "text overlay, watermark, logo, gibberish text, name card with text, stamp"
)
POLL_INTERVAL = 10
POLL_TIMEOUT = 900
MAX_WORKERS = 3


def load_dotenv() -> None:
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


def probe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


# ----- INVARIANT Rule 2: prompt builders read ONLY shot.{text,markers,visual_req} -----

def build_t2i_prompt(shot: dict) -> str:
    """Build Kling T2I anchor prompt from shot markers (NO external context)."""
    sits = [m.get("maps_to", "") for m in shot.get("situation_markers", []) if m.get("maps_to")]
    emos = [m.get("maps_to", "") for m in shot.get("emotion_markers", []) if m.get("maps_to")]
    scene = shot.get("visual_requirement_ko", "")
    subject_clause = ", ".join(sits[:3]) if sits else "dim scene"
    tone_clause = ", ".join(emos[:2]) if emos else "tonedown"
    prompt = (
        f"Cinematic crime noir still photograph. "
        f"Subject: {subject_clause}. "
        f"Scene intent: {scene}. "
        f"Tone: {tone_clause}, dim moody lighting, 9:16 vertical framing. "
        f"NO text, NO letters, NO captions, NO watermark, NO cartoon."
    )
    return prompt


def build_i2v_prompt(shot: dict) -> str:
    """Build Kling I2V motion prompt from shot markers (NO external context)."""
    sits = [m.get("maps_to", "") for m in shot.get("situation_markers", []) if m.get("maps_to")]
    motions = [m.get("maps_to", "") for m in shot.get("motion_markers", []) if m.get("maps_to")]
    emos = [m.get("maps_to", "") for m in shot.get("emotion_markers", []) if m.get("maps_to")]
    subject = ", ".join(sits[:2]) if sits else "scene"
    motion = ", ".join(motions[:2]) if motions else "subtle camera hold, slight natural drift"
    tone = ", ".join(emos[:2]) if emos else "tonedown"
    prompt = (
        f"Cinematic crime noir shot. "
        f"Subject: {subject}. "
        f"Motion: {motion}. "
        f"Tone: {tone}, dim moody lighting. "
        f"NO text, NO captions, NO stamps, NO name plates, NO cartoon."
    )
    return prompt


# ----- Kling T2I -----

def kling_t2i_create(ak: str, sk: str, prompt: str) -> str:
    token = make_jwt(ak, sk)
    body = {
        "model_name": KLING_T2I_MODEL,
        "prompt": prompt,
        "negative_prompt": T2I_NEG,
        "aspect_ratio": ASPECT,
        "n": 1,
    }
    r = requests.post(f"{API_BASE}/v1/images/generations",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"T2I create HTTP {r.status_code}: {r.text[:400]}")
    d = r.json()
    tid = (d.get("data") or {}).get("task_id") or d.get("task_id")
    if not tid:
        raise RuntimeError(f"T2I no task_id: {d}")
    return tid


def kling_t2i_poll(ak: str, sk: str, task_id: str, shot_id: str) -> str:
    url = f"{API_BASE}/v1/images/generations/{task_id}"
    t0 = time.time()
    last = None
    while time.time() - t0 < POLL_TIMEOUT:
        token = make_jwt(ak, sk)
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if r.status_code >= 500:
            time.sleep(POLL_INTERVAL); continue
        if r.status_code >= 400:
            raise RuntimeError(f"T2I poll HTTP {r.status_code}: {r.text[:400]}")
        d = r.json(); inner = d.get("data") or d
        status = inner.get("task_status") or inner.get("status")
        if status != last:
            _p(f"    [{shot_id[:30]:<30s}] T2I {task_id[:8]}... status={status} ({time.time()-t0:.0f}s)")
            last = status
        if status in ("succeed", "success", "completed", "done"):
            result = inner.get("task_result") or inner.get("result") or inner
            imgs = result.get("images") or []
            if imgs:
                u = imgs[0].get("url") or imgs[0].get("image_url")
                if u:
                    return u
            raise RuntimeError(f"T2I no url: {d}")
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"T2I failed: {d}")
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"T2I timeout: {shot_id}")


def download_to(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dst.open("wb") as fh:
            for c in r.iter_content(131072):
                if c: fh.write(c)


# ----- Kling I2V -----

def img_b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def kling_i2v_create(ak: str, sk: str, anchor: Path, prompt: str) -> str:
    token = make_jwt(ak, sk)
    body = {
        "model_name": KLING_I2V_MODEL,
        "mode": KLING_I2V_MODE,
        "duration": KLING_I2V_DURATION,
        "aspect_ratio": ASPECT,
        "cfg_scale": 0.5,
        "image": img_b64(anchor),
        "prompt": prompt,
        "negative_prompt": I2V_NEG,
    }
    r = requests.post(f"{API_BASE}/v1/videos/image2video",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"I2V create HTTP {r.status_code}: {r.text[:400]}")
    d = r.json()
    tid = (d.get("data") or {}).get("task_id") or d.get("task_id")
    if not tid:
        raise RuntimeError(f"I2V no task_id: {d}")
    return tid


def kling_i2v_poll(ak: str, sk: str, task_id: str, shot_id: str) -> str:
    url = f"{API_BASE}/v1/videos/image2video/{task_id}"
    t0 = time.time()
    last = None
    while time.time() - t0 < POLL_TIMEOUT:
        token = make_jwt(ak, sk)
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if r.status_code >= 500:
            time.sleep(POLL_INTERVAL); continue
        if r.status_code >= 400:
            raise RuntimeError(f"I2V poll HTTP {r.status_code}: {r.text[:400]}")
        d = r.json(); inner = d.get("data") or d
        status = inner.get("task_status") or inner.get("status")
        if status != last:
            _p(f"    [{shot_id[:30]:<30s}] I2V {task_id[:8]}... status={status} ({time.time()-t0:.0f}s)")
            last = status
        if status in ("succeed", "success", "completed", "done"):
            result = inner.get("task_result") or inner.get("result") or inner
            vids = result.get("videos") or []
            if vids:
                u = vids[0].get("url") or vids[0].get("video_url")
                if u:
                    return u
            u = inner.get("video_url") or inner.get("url")
            if u:
                return u
            raise RuntimeError(f"I2V no url: {d}")
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"I2V failed: {d}")
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"I2V timeout: {shot_id}")


# ----- ffmpeg helpers -----

def ffmpeg_trim_scale(src: Path, dst: Path, start: float, dur: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
        "-vf", "scale=1080:-2:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,"
               "setsar=1,setpts=PTS-STARTPTS",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-an",
        str(dst),
    ], check=True, capture_output=True)


def build_overlay_clip(shot: dict, dst: Path) -> None:
    cfg = shot["overlay_config"]
    duration = shot["duration_hint_s"]
    bg = cfg.get("bg_color", "#0a0a0a")
    lines = cfg["lines"]
    with tempfile.TemporaryDirectory(prefix=f"ov_{shot['shot_id'][:10]}_") as tmp:
        tdir = Path(tmp)
        text_paths = []
        for i, ln in enumerate(lines):
            p = tdir / f"t{i}.txt"
            p.write_text(ln["text"], encoding="utf-8")
            text_paths.append((p, ln))
        filters = []
        for p, ln in text_paths:
            esc = p.as_posix().replace(":", r"\:")
            y_ratio = ln.get("y_ratio", 0.5)
            filters.append(
                f"drawtext=fontfile='{FONT_WIN}':textfile='{esc}':"
                f"fontsize={ln['fontsize']}:fontcolor={ln['color']}:"
                f"x=(w-text_w)/2:y=h*{y_ratio}-text_h/2"
            )
        vf = ",".join(filters) + f",fade=t=in:st=0:d=0.3,fade=t=out:st={max(0,duration-0.3):.3f}:d=0.3"
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={bg}:size=1080x1920:duration={duration}:rate=30",
            "-vf", vf,
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", "-r", "30",
            str(dst),
        ], check=True, capture_output=True)


# ----- per-shot processor -----

def process_real_footage(shot: dict) -> dict:
    sid = shot["shot_id"]
    ts = float(shot.get("doc_source_timestamp_s", 0))
    dur = shot["duration_hint_s"]
    dst = SHOT_FINAL / f"{sid}_final.mp4"
    ffmpeg_trim_scale(FULL_INTERROGATION, dst, ts, dur)
    actual = probe_duration(dst)
    _p(f"  [real_footage   ] {sid:<45s} ts={ts}s dur={dur}s actual={actual:.3f}s")
    return {"shot_id": sid, "mode": "real_footage", "src": str(FULL_INTERROGATION),
            "ts_s": ts, "dur_s": dur, "actual_s": actual}


def process_overlay(shot: dict) -> dict:
    sid = shot["shot_id"]
    dst = SHOT_FINAL / f"{sid}_final.mp4"
    build_overlay_clip(shot, dst)
    actual = probe_duration(dst)
    _p(f"  [overlay_text   ] {sid:<45s} dur={shot['duration_hint_s']}s actual={actual:.3f}s")
    return {"shot_id": sid, "mode": "overlay_text", "actual_s": actual,
            "overlay_config": shot["overlay_config"]}


def process_kling(shot: dict, ak: str, sk: str) -> dict:
    sid = shot["shot_id"]
    t0 = time.time()
    _p(f"  [kling_t2i_i2v  ] {sid:<45s} START")
    # 1) T2I anchor
    t2i_prompt = build_t2i_prompt(shot)
    _p(f"    [{sid[:30]:<30s}] T2I prompt: {t2i_prompt[:100]}...")
    tid1 = kling_t2i_create(ak, sk, t2i_prompt)
    t2i_url = kling_t2i_poll(ak, sk, tid1, sid)
    anchor = KLING_ANCHORS / f"{sid}_anchor.png"
    download_to(t2i_url, anchor)
    # 2) I2V motion
    i2v_prompt = build_i2v_prompt(shot)
    _p(f"    [{sid[:30]:<30s}] I2V prompt: {i2v_prompt[:100]}...")
    tid2 = kling_i2v_create(ak, sk, anchor, i2v_prompt)
    i2v_url = kling_i2v_poll(ak, sk, tid2, sid)
    raw = KLING_RAW / f"{sid}_raw.mp4"
    download_to(i2v_url, raw)
    # 3) Trim
    dst = SHOT_FINAL / f"{sid}_final.mp4"
    ffmpeg_trim_scale(raw, dst, 0, shot["duration_hint_s"])
    actual = probe_duration(dst)
    elapsed = time.time() - t0
    _p(f"  [kling_t2i_i2v  ] {sid:<45s} DONE t2i+i2v elapsed={elapsed:.0f}s actual={actual:.3f}s")
    return {"shot_id": sid, "mode": "kling_t2i_i2v",
            "t2i_prompt": t2i_prompt, "i2v_prompt": i2v_prompt,
            "anchor": str(anchor), "raw": str(raw),
            "t2i_task": tid1, "i2v_task": tid2,
            "dur_s": shot["duration_hint_s"], "actual_s": actual,
            "elapsed_s": round(elapsed, 1)}


def main() -> int:
    load_dotenv()
    ak = os.environ.get("KLING_ACCESS_KEY")
    sk = os.environ.get("KLING_SECRET_KEY")
    if not ak or not sk:
        raise EnvironmentError("KLING keys missing")

    # 🔴 INVARIANT Rule 1 FIRST ACTION
    _p("[Producer v5] reads script_v5.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))
    flat_shots = []
    for sec in script["sections"]:
        for shot in sec["shots"]:
            flat_shots.append(shot)
    total = len(flat_shots)
    _p(f"[Producer v5] {total} shots loaded from script_v5")

    SHOT_FINAL.mkdir(parents=True, exist_ok=True)
    KLING_ANCHORS.mkdir(parents=True, exist_ok=True)
    KLING_RAW.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    # Phase 1 — sync modes (fast, no API)
    _p(f"\n[Phase 1] real_footage + overlay_text (sync)")
    for shot in flat_shots:
        mode = shot.get("visual_mode")
        if mode == "real_footage":
            results.append(process_real_footage(shot))
        elif mode == "overlay_text":
            results.append(process_overlay(shot))

    # Phase 2 — Kling T2I + I2V (parallel max 3)
    kling_shots = [s for s in flat_shots if s.get("visual_mode") == "kling_t2i_i2v"]
    _p(f"\n[Phase 2] kling_t2i_i2v ({len(kling_shots)} shots, workers={MAX_WORKERS})")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(process_kling, s, ak, sk): s["shot_id"] for s in kling_shots}
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                results.append(fut.result())
            except Exception as exc:
                _p(f"  [{sid}] FAIL: {exc!r}")
                results.append({"shot_id": sid, "mode": "kling_t2i_i2v",
                                "status": "failed", "error": repr(exc)})
    _p(f"[Phase 2] done in {(time.time()-t0)/60:.1f} min")

    # Log + manifest
    MANIFEST.write_text(json.dumps({
        "pipeline": "v5-script-driven-runtime-prompt",
        "total_shots": total,
        "real_footage_count": sum(1 for r in results if r.get("mode") == "real_footage"),
        "kling_t2i_i2v_count": sum(1 for r in results if r.get("mode") == "kling_t2i_i2v"
                                   and r.get("status") != "failed"),
        "overlay_text_count": sum(1 for r in results if r.get("mode") == "overlay_text"),
        "failed": [r for r in results if r.get("status") == "failed"],
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"\n[Producer v5] manifest: {MANIFEST}")
    _p(f"[Producer v5] shot_final/ files: {len(list(SHOT_FINAL.glob('*.mp4')))}")

    fails = [r for r in results if r.get("status") == "failed"]
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
