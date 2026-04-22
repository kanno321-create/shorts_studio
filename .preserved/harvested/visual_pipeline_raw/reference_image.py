"""Reference image downloader and validator."""

import os

import httpx
from PIL import Image


def download_reference_image(url: str, output_dir: str) -> str:
    """Download a reference image and validate it.

    Args:
        url: URL of the reference image.
        output_dir: Directory to save the image.

    Returns:
        Path to the saved reference image.

    Raises:
        RuntimeError: If download or validation fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "reference.jpg")

    response = httpx.get(url)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    # Validate the downloaded file is a valid image
    img = Image.open(output_path)
    img.verify()

    return output_path
