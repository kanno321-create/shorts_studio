"""One-shot experiment: gpt-image-2 (ducktape) vs Nano Banana character consistency.

Reference character: output/channel_art/profile_kr_bright.png (detective)
Matrix: 5 prompts x 2 models x 5 quality slots (low/med_a/med_b/high_a/high_b) = 50 images.

For Nano Banana, quality tier does not exist in API — we reuse the same call for all
5 slots to measure seed variance (deterministic vs stochastic).

Output tree:
    outputs/compare_ducktape_vs_nanobanana/
        prompt_<n>_<slug>/<model>_<quality>_<variant>.png
        run_log.json
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from openai import OpenAI

load_dotenv()

REFERENCE = Path("output/channel_art/profile_kr_bright.png")
OUT_DIR = Path("outputs/compare_ducktape_vs_nanobanana")

PROMPTS: list[tuple[str, str]] = [
    (
        "desk_writing",
        "the same detective character from the reference image, "
        "sitting at a lit desk, writing in a leather-bound case file, "
        "single warm desk-lamp lighting, focused expression, "
        "cinematic, preserve exact face, beard, hat and trench coat",
    ),
    (
        "alley_walk",
        "the same detective character from the reference image, "
        "walking through a rainy neon-lit alley at night, "
        "trench coat flowing in wind, determined stride, "
        "cinematic low angle, preserve exact face, beard, hat",
    ),
    (
        "magnifying",
        "the same detective character from the reference image, "
        "holding a magnifying glass, examining a document under a desk lamp, "
        "intense concentration, close-up, "
        "preserve exact face, beard, hat and trench coat",
    ),
    (
        "window_pensive",
        "the same detective character from the reference image, "
        "standing by a tall window overlooking city lights at night, "
        "hands in pockets, pensive mood, silhouette backlight, "
        "preserve exact face, beard, hat and trench coat",
    ),
    (
        "briefing",
        "the same detective character from the reference image, "
        "speaking seriously across a table, pointing at a map, "
        "stern briefing expression, warm office lighting, "
        "preserve exact face, beard, hat and trench coat",
    ),
]

QUALITY_SLOTS: list[tuple[str, str]] = [
    ("low", "a"),
    ("medium", "a"),
    ("medium", "b"),
    ("high", "a"),
    ("high", "b"),
]

GPT_MODEL = "gpt-image-2"
NB_MODEL = "gemini-2.5-flash-image"


def call_gpt_image2(
    client: OpenAI,
    reference_bytes: bytes,
    prompt: str,
    quality: str,
    out: Path,
) -> dict:
    t0 = time.time()
    result = client.images.edit(
        model=GPT_MODEL,
        image=("reference.png", io.BytesIO(reference_bytes), "image/png"),
        prompt=prompt,
        size="1024x1024",
        quality=quality,
        n=1,
    )
    b64 = result.data[0].b64_json
    out.write_bytes(base64.b64decode(b64))
    usage = getattr(result, "usage", None)
    return {
        "elapsed_sec": round(time.time() - t0, 2),
        "usage": usage.model_dump() if usage and hasattr(usage, "model_dump") else None,
        "bytes": out.stat().st_size,
    }


def call_nanobanana(
    client: genai.Client,
    reference_bytes: bytes,
    prompt: str,
    out: Path,
) -> dict:
    t0 = time.time()
    response = client.models.generate_content(
        model=NB_MODEL,
        contents=[
            genai_types.Part.from_bytes(data=reference_bytes, mime_type="image/png"),
            prompt,
        ],
        config=genai_types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        raise RuntimeError("Nano Banana: candidate 없음")
    parts = getattr(candidates[0].content, "parts", None) or []
    for part in parts:
        inline = getattr(part, "inline_data", None)
        data = getattr(inline, "data", None) if inline else None
        if data:
            out.write_bytes(data)
            return {
                "elapsed_sec": round(time.time() - t0, 2),
                "bytes": out.stat().st_size,
            }
    raise RuntimeError("Nano Banana: 이미지 part 없음")


def main() -> int:
    if not REFERENCE.exists():
        raise FileNotFoundError(f"레퍼런스 이미지 없음 (대표님): {REFERENCE}")

    openai_key = os.environ.get("OPENAI_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY 미설정 (대표님 .env 확인)")
    if not google_key:
        raise RuntimeError("GOOGLE_API_KEY 미설정 (대표님 .env 확인)")

    reference_bytes = REFERENCE.read_bytes()
    print(f"[reference] {REFERENCE} ({len(reference_bytes):,} bytes)")

    openai_client = OpenAI(api_key=openai_key)
    google_client = genai.Client(api_key=google_key)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log: list[dict] = []

    for pidx, (pname, ptext) in enumerate(PROMPTS, 1):
        prompt_dir = OUT_DIR / f"prompt_{pidx}_{pname}"
        prompt_dir.mkdir(exist_ok=True)
        print(f"\n=== Prompt {pidx}/5: {pname} ===")

        for quality, variant in QUALITY_SLOTS:
            slot = f"{quality}_{variant}"

            # --- gpt-image-2 ---
            gpt_out = prompt_dir / f"gpt_image2_{slot}.png"
            rec = {
                "prompt": pname,
                "model": GPT_MODEL,
                "quality": quality,
                "variant": variant,
                "path": str(gpt_out),
            }
            try:
                meta = call_gpt_image2(
                    openai_client, reference_bytes, ptext, quality, gpt_out
                )
                rec.update(status="ok", **meta)
                print(f"  [OK] {GPT_MODEL} {slot}  {meta['elapsed_sec']}s")
            except Exception as err:  # noqa: BLE001 — log and continue
                rec.update(status="error", error=f"{type(err).__name__}: {err}")
                print(f"  [FAIL] {GPT_MODEL} {slot}: {err}")
            log.append(rec)

            # --- nano-banana (same call regardless of quality slot) ---
            nb_out = prompt_dir / f"nanobanana_{slot}.png"
            rec_nb = {
                "prompt": pname,
                "model": NB_MODEL,
                "quality": quality,
                "variant": variant,
                "path": str(nb_out),
            }
            try:
                meta = call_nanobanana(google_client, reference_bytes, ptext, nb_out)
                rec_nb.update(status="ok", **meta)
                print(f"  [OK] {NB_MODEL} {slot}  {meta['elapsed_sec']}s")
            except Exception as err:  # noqa: BLE001 — log and continue
                rec_nb.update(status="error", error=f"{type(err).__name__}: {err}")
                print(f"  [FAIL] {NB_MODEL} {slot}: {err}")
            log.append(rec_nb)

            time.sleep(0.4)  # light rate-limit safety

    log_path = OUT_DIR / "run_log.json"
    log_path.write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    ok = sum(1 for r in log if r.get("status") == "ok")
    fail = len(log) - ok
    print(f"\n=== DONE: {ok} OK / {fail} FAIL / total {len(log)} ===")
    print(f"log: {log_path}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
