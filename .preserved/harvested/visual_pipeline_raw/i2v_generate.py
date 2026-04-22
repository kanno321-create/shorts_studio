"""Image-to-video generation using Kling via fal.ai."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

import fal_client

KLING_ENDPOINT = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_NEGATIVE_PROMPT = (
    "static character, frozen pose, only camera movement, "
    "camera-only motion, motionless character"
)


def upload_for_fal(local_path: str) -> str:
    """Upload a local file to fal.ai storage.

    Args:
        local_path: Path to the local file.

    Returns:
        The fal.ai URL of the uploaded file.
    """
    return fal_client.upload_file(local_path)


def generate_video_clip(
    image_url: str,
    motion_prompt: str,
    output_path: str,
    *,
    duration: str = "5",
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
) -> str:
    """Generate a video clip from an image using Kling v2.6.

    Args:
        image_url: URL of the source image.
        motion_prompt: Text prompt describing the desired motion.
        output_path: Path where the generated video will be saved.
        duration: Video duration in seconds (default "5").
        negative_prompt: Negative prompt to avoid undesired outputs.

    Returns:
        The output_path where the video was saved.

    Raises:
        ValueError: If endpoint does not contain "v2.6".
        RuntimeError: If video generation fails.
    """
    if "v2.6" not in KLING_ENDPOINT:
        raise ValueError(
            f"Endpoint must use Kling v2.6 or higher: {KLING_ENDPOINT}"
        )

    os.environ.setdefault("FAL_KEY", os.environ.get("FAL_KEY", ""))

    result = fal_client.subscribe(
        KLING_ENDPOINT,
        arguments={
            "image_url": image_url,
            "prompt": motion_prompt,
            "duration": duration,
            "negative_prompt": negative_prompt,
        },
    )

    video_url = result.get("video", {}).get("url")
    if not video_url:
        raise RuntimeError("No video URL in Kling response")

    response = httpx.get(video_url)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
