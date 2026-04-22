"""Text-to-image generation using Gemini (Nano Banana Pro)."""

import os
import time

from dotenv import load_dotenv

load_dotenv(override=True)

from google import genai
from google.genai import types
from PIL import Image

GEMINI_MODEL = "gemini-3-pro-image-preview"

_MAX_RETRIES = 3
_RETRY_DELAYS = [1, 2, 4]


def generate_scene_image(
    reference_path: str,
    scene_prompt: str,
    output_path: str,
    *,
    aspect_ratio: str = "9:16",
) -> str:
    """Generate a scene image using Gemini with a reference image.

    Args:
        reference_path: Path to the reference image file.
        scene_prompt: Text prompt describing the desired scene.
        output_path: Path where the generated image will be saved.
        aspect_ratio: Aspect ratio for generation (default "9:16").

    Returns:
        The output_path where the image was saved.

    Raises:
        RuntimeError: If no image is returned after retries.
    """
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    ref_image = Image.open(reference_path)

    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_image(ref_image),
                            types.Part.from_text(scene_prompt),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            # Find image part in response
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data is not None:
                    image_data = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    return output_path

            raise RuntimeError("No image part found in Gemini response")

        except Exception as e:
            if "429" in str(e) and attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAYS[attempt])
                last_error = e
                continue
            raise RuntimeError(
                f"Failed to generate image: {e}"
            ) from e

    raise RuntimeError(f"Max retries exceeded: {last_error}")
