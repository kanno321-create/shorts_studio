"""Tiny smoke: one gpt-image-2 edit + one nanobanana edit, to verify API wiring."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare_image_models import (  # noqa: E402
    REFERENCE,
    call_gpt_image2,
    call_nanobanana,
    GPT_MODEL,
    NB_MODEL,
)
from dotenv import load_dotenv  # noqa: E402
from google import genai  # noqa: E402
from openai import OpenAI  # noqa: E402

load_dotenv()

OUT = Path("outputs/compare_ducktape_vs_nanobanana/_smoke")
OUT.mkdir(parents=True, exist_ok=True)
ref_bytes = REFERENCE.read_bytes()
prompt = "the same detective character from the reference image, sitting at a desk, cinematic"

try:
    oi = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    m = call_gpt_image2(oi, ref_bytes, prompt, "low", OUT / "gpt_image2_smoke.png")
    print(f"[OK] gpt-image-2 smoke: {m}")
except Exception as e:
    print(f"[FAIL] gpt-image-2: {type(e).__name__}: {e}")

try:
    gc = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    m = call_nanobanana(gc, ref_bytes, prompt, OUT / "nanobanana_smoke.png")
    print(f"[OK] nano-banana smoke: {m}")
except Exception as e:
    print(f"[FAIL] nano-banana: {type(e).__name__}: {e}")
