"""HeyGen API v2 client for avatar video generation.

Uses httpx for direct HTTP calls. No official Python SDK exists.
Endpoints: upload audio, generate video, poll status, check quota, list avatars.

Environment variables required:
    HEYGEN_API_KEY -- HeyGen API key (https://heygen.com Settings > API)
"""
import os
import time
from pathlib import Path

import httpx


class HeyGenAPIError(Exception):
    """Raised when HeyGen API returns an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HeyGen API error ({status_code}): {message}")


class HeyGenClient:
    """HeyGen API v2 client.

    Provides methods for:
    - Uploading audio assets for lip-sync
    - Generating avatar videos
    - Polling video generation status
    - Checking remaining quota/credits
    - Listing available avatars
    - Downloading completed videos
    """

    BASE_URL = "https://api.heygen.com"
    UPLOAD_URL = "https://upload.heygen.com"

    def __init__(self, api_key: str = None):
        """Initialize HeyGen client.

        Args:
            api_key: HeyGen API key. Falls back to HEYGEN_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.environ.get("HEYGEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "HEYGEN_API_KEY required. Get your key at heygen.com Settings > API"
            )
        self.headers = {"x-api-key": self.api_key}

    def upload_audio(self, audio_path: str) -> str:
        """Upload audio file to HeyGen asset storage.

        Args:
            audio_path: Local path to MP3 audio file.

        Returns:
            audio_asset_id string from HeyGen.

        Raises:
            HeyGenAPIError: On API error response.
        """
        raw_bytes = Path(audio_path).read_bytes()
        url = f"{self.UPLOAD_URL}/v1/asset"
        headers = {**self.headers, "Content-Type": "audio/mpeg"}

        resp = httpx.post(url, headers=headers, content=raw_bytes)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HeyGenAPIError(
                status_code=resp.status_code,
                message=resp.text,
            ) from exc

        data = resp.json()
        return data["data"]["id"]

    def generate_video(
        self,
        avatar_id: str,
        audio_asset_id: str,
        width: int,
        height: int,
        title: str = None,
        background: dict = None,
    ) -> str:
        """Submit avatar video generation request.

        Args:
            avatar_id: HeyGen avatar ID.
            audio_asset_id: Uploaded audio asset ID.
            width: Output video width in pixels.
            height: Output video height in pixels.
            title: Optional video title.
            background: Background config dict. Defaults to white.

        Returns:
            video_id string for polling.

        Raises:
            HeyGenAPIError: On API error response.
        """
        body = {
            "title": title or f"avatar-{avatar_id[:20]}",
            "dimension": {"width": width, "height": height},
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "scale": 1.0,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "audio",
                        "audio_asset_id": audio_asset_id,
                    },
                    "background": background or {"type": "color", "value": "#FFFFFF"},
                }
            ],
        }

        url = f"{self.BASE_URL}/v2/video/generate"
        headers = {**self.headers, "Content-Type": "application/json"}

        resp = httpx.post(url, headers=headers, json=body)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HeyGenAPIError(
                status_code=resp.status_code,
                message=resp.text,
            ) from exc

        data = resp.json()
        return data["data"]["video_id"]

    def poll_video_status(
        self,
        video_id: str,
        initial_interval: float = 5.0,
        max_interval: float = 30.0,
        timeout: float = 600.0,
    ) -> dict:
        """Poll video generation status with exponential backoff.

        Args:
            video_id: Video ID from generate_video.
            initial_interval: First polling interval in seconds.
            max_interval: Maximum polling interval in seconds.
            timeout: Total timeout in seconds.

        Returns:
            Video status data dict with video_url, duration, etc.

        Raises:
            TimeoutError: If video not completed within timeout.
            RuntimeError: If video generation failed.
        """
        url = f"{self.BASE_URL}/v1/video_status.get"
        elapsed = 0.0
        interval = initial_interval

        while elapsed < timeout:
            resp = httpx.get(url, headers=self.headers, params={"video_id": video_id})
            resp.raise_for_status()
            data = resp.json().get("data", {})
            status = data.get("status")

            if status == "completed":
                return data
            elif status == "failed":
                raise RuntimeError(
                    f"HeyGen video generation failed: {data.get('error')}"
                )

            time.sleep(interval)
            elapsed += interval
            interval = min(interval * 1.5, max_interval)

        raise TimeoutError(
            f"HeyGen video generation timed out after {timeout}s "
            f"(video_id={video_id})"
        )

    def get_remaining_quota(self) -> int:
        """Check remaining API quota in seconds.

        Returns:
            Remaining quota in seconds. Divide by 60 for credits.
        """
        url = f"{self.BASE_URL}/v2/user/remaining_quota"
        resp = httpx.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["remaining_quota"]

    def list_avatars(self) -> list:
        """List available avatars.

        Returns:
            List of avatar dicts with avatar_id, avatar_name, etc.
        """
        url = f"{self.BASE_URL}/v2/avatars"
        resp = httpx.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["avatars"]

    def download_video(self, video_url: str, output_path: str) -> str:
        """Download completed video to local file.

        Args:
            video_url: HeyGen video URL (expires in 7 days).
            output_path: Local file path for the downloaded MP4.

        Returns:
            output_path on success.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", video_url) as resp:
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
        return output_path
