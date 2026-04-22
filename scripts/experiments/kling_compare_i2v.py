"""Kling 2.6 Pro I2V — gpt-image-2 vs Nano Banana medium_b anchor 비교.

대표님 지시:
    - 두 anchor (gpt_image2_medium_b / nanobanana_medium_b) 로 각각 영상 생성
    - 프롬프트: 걸어오다 뒤돌아 되돌아감 + 담배 + 네온 깜빡임 + 물 튀김 + 눈동자 스캔
    - 동일 prompt, 동일 duration 으로 reference 에 따른 영상 품질 차이 관찰

병렬 submit + 각 handler.get() 대기. Kling 2.6 Pro latency ~70-100s @ 10s duration.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import fal_client
import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

ANCHOR_DIR = PROJECT_ROOT / "outputs" / "compare_ducktape_vs_nanobanana" / "prompt_2_alley_walk"
OUT_DIR = PROJECT_ROOT / "outputs" / "compare_ducktape_vs_nanobanana" / "kling_videos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ANCHORS = [
    ("gpt_image2", ANCHOR_DIR / "gpt_image2_medium_b.png"),
    ("nanobanana", ANCHOR_DIR / "nanobanana_medium_b.png"),
]

FAL_ENDPOINT = "fal-ai/kling-video/v2.6/pro/image-to-video"
DURATION = "10"

PROMPT = (
    "The detective walks forward through a rainy neon-lit alley at night, "
    "smoking a cigarette with visible curling smoke exhaled slowly. "
    "Water splashes upward from wet puddles under his boots with each step. "
    "Flickering neon signs pulse on and off in the background, "
    "casting cyan and magenta reflections on the wet ground. "
    "His eyes dart left and right alertly scanning the alley. "
    "At the midpoint he turns around and walks back the way he came. "
    "Cinematic noir lighting, shallow depth of field, film grain."
)

NEG_PROMPT = (
    "static character, frozen pose, only camera movement, camera-only motion, "
    "motionless subject, still photo, no action, no movement, "
    "cartoon, illustration, anime, ai artifacts, warping, morphing"
)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _download(url: str, out: Path) -> None:
    r = httpx.get(url, follow_redirects=True, timeout=240)
    r.raise_for_status()
    out.write_bytes(r.content)


def main() -> int:
    if not os.environ.get("FAL_KEY"):
        raise RuntimeError("FAL_KEY 미설정 (대표님 .env 확인)")

    for label, anchor in ANCHORS:
        if not anchor.exists():
            raise FileNotFoundError(f"anchor 없음: {anchor}")

    _log("=" * 60)
    _log(f"Kling 2.6 Pro I2V 비교 — duration={DURATION}s × 2 영상")
    _log("=" * 60)
    _log(f"Prompt ({len(PROMPT.split())} words): {PROMPT[:100]}...")
    _log("")

    # 1. Upload anchors + submit both jobs (병렬)
    handles: list[tuple[str, Path, object]] = []
    for label, anchor in ANCHORS:
        _log(f"[{label}] uploading anchor + submitting...")
        t0 = time.time()
        image_url = fal_client.upload_file(str(anchor))
        payload = {
            "image_url": image_url,
            "prompt": PROMPT,
            "duration": DURATION,
            "negative_prompt": NEG_PROMPT,
            "cfg_scale": 0.5,
        }
        handler = fal_client.submit(FAL_ENDPOINT, arguments=payload)
        elapsed = time.time() - t0
        _log(f"[{label}] submitted ({elapsed:.1f}s upload) → waiting for result...")
        handles.append((label, anchor, handler))

    # 2. Wait for each job and download
    results: list[dict] = []
    for label, anchor, handler in handles:
        t0 = time.time()
        try:
            result = handler.get()  # blocks until fal.ai completes
            elapsed = time.time() - t0
            video_url = (result.get("video", {}) or {}).get("url") or result.get("url")
            if not video_url:
                raise RuntimeError(f"no video URL in result: {result!r}")
            stamp = time.strftime("%Y%m%d_%H%M%S")
            out = OUT_DIR / f"kling26_{label}_{stamp}.mp4"
            _download(video_url, out)
            size_mb = out.stat().st_size / (1024 * 1024)
            _log(f"[{label}] ✓ {out.name}  {size_mb:.1f}MB  generation {elapsed:.1f}s")
            results.append({
                "label": label,
                "anchor": anchor.name,
                "output": str(out),
                "size_mb": round(size_mb, 2),
                "elapsed_sec": round(elapsed, 1),
                "status": "ok",
            })
        except Exception as err:  # noqa: BLE001 — log + continue
            _log(f"[{label}] ✗ {type(err).__name__}: {err}")
            results.append({
                "label": label,
                "anchor": anchor.name,
                "status": "error",
                "error": f"{type(err).__name__}: {err}",
            })

    _log("")
    _log("=" * 60)
    ok = sum(1 for r in results if r["status"] == "ok")
    _log(f"완료: {ok}/{len(results)} OK")
    for r in results:
        if r["status"] == "ok":
            _log(f"  {r['label']:12s} → {r['output']}")
    _log("비용 추정: Kling 2.6 Pro 10s × 2 ≈ $1.40 (5s $0.35 기준 2배 가정)")
    _log("=" * 60)
    return 0 if ok == len(results) else 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
