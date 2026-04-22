"""AI visual generation module using fal.ai and Google Veo APIs.

Provides FalAIClient for video/image generation via Hailuo 2.3 Pro and
Vidu 2.0, VeoClient for Google Veo 3.1 Lite video generation,
CircuitBreaker for resilience, and BudgetManager for daily spend tracking
with per-provider breakdown.

All model IDs and costs are config-driven via stock-search-config.json.
No model IDs are hardcoded in this module.

Exit codes:
    Not a CLI script — imported as module by stock_fetch.py and scene pipeline.

Environment variables required:
    FAL_KEY — fal.ai API key (https://fal.ai/dashboard/keys)
    GOOGLE_API_KEY — Google API key for Veo (https://aistudio.google.com/apikey)
"""
import json
import os
import time
from datetime import date
from pathlib import Path

import fal_client
import httpx

try:
    from google import genai
    from google.genai import types
    VEO_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    VEO_AVAILABLE = False

ANTHROPIC_AVAILABLE = False


class FalAIClient:
    """fal.ai API client for video and image generation.

    Wraps fal_client.subscribe() for synchronous-feel queue-based API calls.
    Supports Hailuo 2.3 Pro (video), Vidu 2.0 (video fallback), and
    Imagen 4 Fast (thumbnail images).

    Args:
        config: fal_ai section from stock-search-config.json.

    Raises:
        ValueError: If FAL_KEY environment variable is not set.
    """

    def __init__(self, config: dict):
        """Initialize with config and validate FAL_KEY environment variable.

        Args:
            config: Provider config dict from stock-search-config.json['providers']['fal_ai'].
        """
        if not os.environ.get("FAL_KEY"):
            raise ValueError(
                "FAL_KEY environment variable required. "
                "Get your key at https://fal.ai/dashboard/keys"
            )
        self.config = config

    def generate_video(self, prompt: str, model_id: str = None, timeout: int = None) -> dict:
        """Generate a video clip using fal.ai model.

        Args:
            prompt: Text description of the desired video.
            model_id: fal.ai model ID. Defaults to config primary_model.
            timeout: Request timeout in seconds. Defaults to config primary_timeout.

        Returns:
            Result dict containing {"video": {"url": "...", "file_size": ..., ...}}.
        """
        if model_id is None:
            model_id = self.config.get(
                "primary_model", "fal-ai/minimax/hailuo-2.3/pro/text-to-video"
            )
        if timeout is None:
            timeout = self.config.get("primary_timeout", 120)

        result = fal_client.subscribe(
            model_id,
            arguments={
                "prompt": prompt,
                "prompt_optimizer": self.config.get("prompt_optimizer", True),
            },
            timeout=timeout,
        )
        return result

    def generate_image(self, prompt: str, model_id: str = None,
                       aspect_ratio: str = "16:9") -> dict:
        """Generate an image using fal.ai model (for thumbnails).

        Args:
            prompt: Text description of the desired image.
            model_id: fal.ai model ID. Defaults to config thumbnail_model.
            aspect_ratio: Image aspect ratio. Defaults to "16:9".

        Returns:
            Result dict containing {"images": [{"url": "...", "width": ..., "height": ...}]}.
        """
        if model_id is None:
            model_id = self.config.get(
                "thumbnail_model", "fal-ai/imagen4/preview/fast"
            )
        timeout = self.config.get("thumbnail_timeout", 30)

        result = fal_client.subscribe(
            model_id,
            arguments={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "num_images": 1,
            },
            timeout=timeout,
        )
        return result

    def generate_illustration(self, prompt: str, style: str = None) -> dict:
        """Generate manga-style illustration via FLUX Kontext Pro.

        Per D-13, D-14, D-15: Uses fal-ai/flux-pro/kontext/text-to-image
        with 720x1280 (9:16) size. $0.04/image.

        Args:
            prompt: Visual description for illustration.
            style: Optional style override. Defaults to config style_prefix.

        Returns:
            Result dict with images[0]["url"].
        """
        illus_config = self.config.get("illustration", {})
        model_id = illus_config.get("model", "fal-ai/flux-pro/kontext/text-to-image")
        timeout = illus_config.get("timeout", 30)
        width = illus_config.get("width", 720)
        height = illus_config.get("height", 1280)
        style_prefix = style or illus_config.get(
            "style_prefix",
            "Korean webtoon manga style, clean line art, vibrant colors: "
        )
        output_format = illus_config.get("output_format", "png")
        guidance_scale = illus_config.get("guidance_scale", 3.5)
        num_inference_steps = illus_config.get("num_inference_steps", 28)

        result = fal_client.subscribe(
            model_id,
            arguments={
                "prompt": f"{style_prefix}{prompt}",
                "image_size": {"width": width, "height": height},
                "num_images": 1,
                "output_format": output_format,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
            },
            timeout=timeout,
        )
        return result

    def generate_photorealistic(self, prompt: str, aspect_ratio: str = "9:16") -> dict:
        """Generate photorealistic image via FLUX 2 Pro for documentary scenes.

        Uses fal-ai/flux-2-pro (NOT Kontext) — ranked #1 for photorealism in 2026.
        Kontext is for image editing; FLUX 2 Pro is for raw photorealistic generation.
        Cost: $0.03/megapixel. 1080x1920 = ~$0.06/image.

        Per BFL official prompting guide: use camera/lens specs instead of vague
        "photorealistic" prefix for better results.

        Args:
            prompt: Detailed scene description. Include camera specs for best results:
                    e.g., "Shot on Sony A7IV, 35mm f/1.4, ..."
            aspect_ratio: "9:16" (default, shorts) or "16:9".

        Returns:
            Result dict with images[0]["url"].

        Sources:
            - https://docs.bfl.ml/guides/prompting_guide_flux2
            - https://fal.ai/models/fal-ai/flux-2-pro
        """
        # FLUX 2 Pro — photorealism specialist ($0.03/MP)
        # NOT Kontext (which is for image editing/style transfer)
        model_id = "fal-ai/flux-2-pro"
        timeout = self.config.get("primary_timeout", 60)

        result = fal_client.subscribe(
            model_id,
            arguments={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "num_images": 1,
                "output_format": "png",
                "safety_tolerance": 3,
            },
            timeout=timeout,
        )
        return result

    def generate_character_art(self, prompt: str, character_ref: str = None) -> dict:
        """Generate anthropomorphic character illustration for object_nag channel.

        Uses FLUX Kontext Pro for character illustrations (cartoon/Pixar style).
        Kontext is correct here — it excels at creative/illustrative generation.

        Args:
            prompt: Character description (e.g., "angry pizza slice yelling").
            character_ref: Optional path to reference image for consistency.

        Returns:
            Result dict with images[0]["url"].
        """
        illus_config = self.config.get("illustration", {})
        model_id = illus_config.get("model", "fal-ai/flux-pro/kontext/text-to-image")
        timeout = illus_config.get("timeout", 30)
        output_format = illus_config.get("output_format", "png")
        guidance_scale = illus_config.get("guidance_scale", 3.5)
        num_inference_steps = illus_config.get("num_inference_steps", 28)

        style_prefix = (
            "Cute anthropomorphic cartoon character, Pixar style, "
            "expressive eyes, vibrant colors, clean solid background, "
            "high quality illustration: "
        )

        result = fal_client.subscribe(
            model_id,
            arguments={
                "prompt": f"{style_prefix}{prompt}",
                "aspect_ratio": "9:16",
                "num_images": 1,
                "output_format": output_format,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
            },
            timeout=timeout,
        )
        return result


class KlingClient:
    """Kling AI video generation client (Text-to-Video + Image-to-Video).

    PRIMARY video generation provider. Korean creator community standard.
    Supports T2V (text→video) and I2V (image→video) modes.
    I2V pattern: FLUX 2 Pro image → Kling I2V. Verified in child pipeline.

    Auth via KLING_ACCESS_KEY + KLING_SECRET_KEY → JWT token.
    API docs: https://docs.qingque.cn/d/home/eZQB8VeBU-CEx8FPz3Rvkinyb

    Args:
        config: kling section from stock-search-config.json.
    """

    def __init__(self, config: dict):
        access_key = os.environ.get("KLING_ACCESS_KEY")
        secret_key = os.environ.get("KLING_SECRET_KEY")
        if not access_key or not secret_key:
            raise ValueError(
                "KLING_ACCESS_KEY and KLING_SECRET_KEY required. "
                "Get keys at https://platform.klingai.com/"
            )
        self.access_key = access_key
        self.secret_key = secret_key
        self.config = config
        self.base_url = config.get("base_url", "https://api.klingai.com")

    def _get_token(self) -> str:
        """Generate JWT token for Kling API authentication."""
        import jwt
        now = int(time.time())
        payload = {
            "iss": self.access_key,
            "exp": now + 1800,
            "nbf": now - 5,
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def generate_video(self, prompt: str, output_path: str,
                       aspect_ratio: str = "9:16",
                       duration: int = None) -> dict:
        """Generate video from text prompt (T2V mode).

        Args:
            prompt: Text description of desired video.
            output_path: Where to save the result.
            aspect_ratio: "9:16" (shorts) or "16:9".
            duration: Clip duration in seconds (default from config).

        Returns:
            Dict with keys: output_path, duration, provider.
        """
        t2v_config = self.config.get("text_to_video", {})
        model = t2v_config.get("model", "kling-v3")
        mode = t2v_config.get("mode", "std")
        if duration is None:
            duration = t2v_config.get("duration", 5)
        timeout = t2v_config.get("timeout", 180)

        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Submit generation request
        resp = httpx.post(
            f"{self.base_url}/v1/videos/text2video",
            headers=headers,
            json={
                "model_name": model,
                "prompt": prompt,
                "cfg_scale": 0.5,
                "mode": mode,
                "aspect_ratio": aspect_ratio,
                "duration": str(duration),
            },
            timeout=60,
        )
        resp.raise_for_status()
        task_id = resp.json().get("data", {}).get("task_id")

        # Poll for completion
        video_url = self._poll_task(task_id, headers, timeout)

        # Download
        self._download(video_url, output_path)
        return {"output_path": output_path, "provider": "kling", "mode": "t2v"}

    def image_to_video(self, image_path: str, prompt: str, output_path: str,
                       aspect_ratio: str = "9:16",
                       duration: int = None) -> dict:
        """Generate video from image + prompt (I2V mode).

        T2I→I2V pattern: Feed a FLUX 2 Pro photorealistic still image
        and get animated video back. Verified in child/kids pipeline.

        Args:
            image_path: Path to input image (PNG/JPG).
            prompt: Motion/action description for the image.
            output_path: Where to save the result.
            aspect_ratio: "9:16" or "16:9".
            duration: Clip duration in seconds.

        Returns:
            Dict with keys: output_path, duration, provider.
        """
        i2v_config = self.config.get("image_to_video", {})
        model = i2v_config.get("model", "kling-v3")
        mode = i2v_config.get("mode", "std")
        if duration is None:
            duration = i2v_config.get("duration", 5)
        timeout = i2v_config.get("timeout", 180)

        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Read image as base64
        import base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Determine image type
        ext = Path(image_path).suffix.lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        image_data_url = f"data:{mime_type};base64,{image_b64}"

        resp = httpx.post(
            f"{self.base_url}/v1/videos/image2video",
            headers=headers,
            json={
                "model_name": model,
                "image": image_data_url,
                "prompt": prompt,
                "cfg_scale": 0.5,
                "mode": mode,
                "aspect_ratio": aspect_ratio,
                "duration": str(duration),
            },
            timeout=60,
        )
        resp.raise_for_status()
        task_id = resp.json().get("data", {}).get("task_id")

        video_url = self._poll_task(task_id, headers, timeout)
        self._download(video_url, output_path)
        return {"output_path": output_path, "provider": "kling", "mode": "i2v"}

    def _poll_task(self, task_id: str, headers: dict, timeout: int) -> str:
        """Poll Kling API for task completion."""
        start = time.time()
        while time.time() - start < timeout:
            resp = httpx.get(
                f"{self.base_url}/v1/videos/text2video/{task_id}",
                headers=headers,
                timeout=30,
            )
            data = resp.json().get("data", {})
            status = data.get("task_status")

            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    return videos[0].get("url", "")
                raise ValueError(f"Kling task succeeded but no video URL: {data}")
            elif status == "failed":
                raise ValueError(f"Kling generation failed: {data.get('task_status_msg')}")

            time.sleep(10)

        raise TimeoutError(f"Kling task {task_id} timed out after {timeout}s")

    def _download(self, url: str, output_path: str) -> None:
        """Download video from URL to local path."""
        resp = httpx.get(url, timeout=120)
        resp.raise_for_status()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)


class VeoClient:
    """Google Veo 3.1 Lite video generation client.

    Uses google-genai SDK for synchronous polling-based video generation.
    Auth via GOOGLE_API_KEY environment variable.

    Args:
        config: veo section from stock-search-config.json.

    Raises:
        ValueError: If GOOGLE_API_KEY environment variable is not set.
    """

    def __init__(self, config: dict):
        """Initialize with config and validate GOOGLE_API_KEY.

        Args:
            config: Provider config dict from stock-search-config.json['providers']['veo'].
        """
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable required. "
                "Get your key at https://aistudio.google.com/apikey"
            )
        self.client = genai.Client(api_key=api_key)
        self.config = config

    def generate_video(self, prompt: str, output_path: str,
                       aspect_ratio: str = "9:16",
                       duration: int = None,
                       *,
                       volume: float = 0.0) -> dict:
        """Generate a video clip using Google Veo 3.1 Lite.

        Submits a generation request and polls until completion or timeout.
        Saves the generated video to output_path.

        Args:
            prompt: English text description for video generation.
            output_path: Local file path to save the generated video.
            aspect_ratio: Video aspect ratio ("9:16" for shorts, "16:9" for general).
            duration: Video duration in seconds. Defaults to config default_duration.
            volume: Reserved for future Veo API audio controls (Phase 42 RF-14, PRD Task 6
                    wording). Current Veo API does not accept a volume parameter; actual
                    mute is enforced at the OffthreadVideo layer (ShortsVideo.tsx
                    volume={0}, line 485/538). Keyword-only to preserve Phase 30 D-03
                    backward compatibility for positional callers.

        Returns:
            Dict with local_path and provider keys.

        Raises:
            TimeoutError: If generation exceeds config timeout (default 120s).
        """
        # Phase 42 RF-14: reserved parameter — intentionally unused until Veo API supports it.
        # Swallowing here prevents lint "unused arg" warnings without breaking signature.
        _ = volume
        model = self.config.get("model", "veo-3.1-lite-generate-preview")
        timeout = self.config.get("timeout", 120)
        if duration is None:
            duration = int(self.config.get("default_duration", 6))
        duration = max(4, min(8, duration))  # Veo 허용 범위: 4~8초

        # Lite 모델은 duration_seconds 미지원 — 파라미터 제외
        is_lite = "lite" in model.lower()
        video_config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution="720p",
            number_of_videos=1,
        )
        if not is_lite:
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                duration_seconds=duration,
                resolution="720p",
                number_of_videos=1,
            )

        operation = self.client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=video_config,
        )

        start = time.time()
        while not operation.done:
            if time.time() - start > timeout:
                raise TimeoutError(
                    f"Veo generation timed out after {timeout}s"
                )
            time.sleep(10)
            operation = self.client.operations.get(operation)

        generated_video = operation.response.generated_videos[0]
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # video.save()는 원격 URI에서 NotImplementedError 발생 — httpx로 직접 다운로드
        video_uri = getattr(generated_video.video, "uri", None)
        if video_uri:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            dl_url = f"{video_uri}&key={api_key}" if "?" in video_uri else f"{video_uri}?key={api_key}"
            resp = httpx.get(dl_url, timeout=60, follow_redirects=True)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)
        else:
            generated_video.video.save(output_path)

        try:
            from ui.components.api_usage_tracker import record_api_call
            record_api_call('veo', 'generate_video', cost_usd=0.50)
        except Exception:
            pass
        return {"local_path": output_path, "provider": "veo"}


class CircuitBreaker:
    """Circuit breaker pattern for AI generation resilience (per D-04a).

    States:
        CLOSED  — Normal operation, all requests allowed.
        OPEN    — Too many failures, all requests blocked.
        HALF_OPEN — Recovery test, one request allowed.

    Transitions:
        CLOSED -> OPEN: After failure_threshold consecutive failures.
        OPEN -> HALF_OPEN: After recovery_timeout seconds since last failure.
        HALF_OPEN -> CLOSED: On success.
        HALF_OPEN -> OPEN: On failure.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures to trip breaker.
            recovery_timeout: Seconds to wait before attempting recovery.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution.

        Returns:
            True if execution is allowed, False if blocked.
        """
        if self.state == self.CLOSED:
            return True
        elif self.state == self.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = self.HALF_OPEN
                return True
            return False
        elif self.state == self.HALF_OPEN:
            return True
        return False

    def record_success(self):
        """Record a successful execution. Resets failure count and state."""
        self.failure_count = 0
        self.state = self.CLOSED

    def record_failure(self):
        """Record a failed execution. May trip breaker to OPEN state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN


class BudgetManager:
    """Daily budget manager for AI generation cost tracking (per D-05).

    Tracks daily spend in a JSON file that resets each day. Prevents
    AI generation when the daily cap is exhausted, forcing stock-only mode.

    Budget file format:
        {"date": "2026-03-31", "spent": 2.40}
    """

    def __init__(self, daily_cap: float = 7.0, budget_file: str = None):
        """Initialize budget manager.

        Args:
            daily_cap: Maximum daily spend in USD.
            budget_file: Path to JSON budget file. Defaults to .ai_budget.json.
        """
        self.daily_cap = daily_cap
        self.budget_file = budget_file or ".ai_budget.json"
        self._load()

    def _load(self):
        """Load budget state from file, resetting if date has changed."""
        today = date.today().isoformat()
        try:
            with open(self.budget_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == today:
                self.spent = data.get("spent", 0.0)
                self.by_provider = data.get("by_provider", {})
            else:
                self.spent = 0.0
                self.by_provider = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.spent = 0.0
            self.by_provider = {}
        self.date_str = today

    def _save(self):
        """Persist budget state to file."""
        os.makedirs(os.path.dirname(self.budget_file) or ".", exist_ok=True)
        with open(self.budget_file, "w", encoding="utf-8") as f:
            json.dump({
                "date": self.date_str,
                "spent": self.spent,
                "by_provider": self.by_provider,
            }, f, indent=2)

    def remaining(self) -> float:
        """Return remaining budget for today.

        Returns:
            Remaining budget in USD, minimum 0.0.
        """
        return max(0.0, self.daily_cap - self.spent)

    def can_spend(self, amount: float) -> bool:
        """Check if the given amount can be spent within daily budget.

        Args:
            amount: Amount to check in USD.

        Returns:
            True if remaining budget is sufficient.
        """
        return self.remaining() >= amount

    def record_spend(self, amount: float, provider: str = "unknown"):
        """Record a spend and persist to file.

        Args:
            amount: Amount spent in USD.
            provider: Provider name for per-provider tracking (e.g., "veo", "hailuo").
        """
        self.spent += amount
        self.by_provider[provider] = self.by_provider.get(provider, 0.0) + amount
        self._save()


def generate_ai_clip(
    prompt: str,
    output_path: str,
    client: FalAIClient,
    circuit_breaker: CircuitBreaker,
    budget_manager: BudgetManager,
    model_id: str = None,
    timeout: int = 120,
    cost_per_clip: float = 0.40,
) -> dict:
    """Generate a single AI video clip with circuit breaker and budget checks.

    Args:
        prompt: Text description for AI video generation.
        output_path: Local file path to save the generated video.
        client: FalAIClient instance.
        circuit_breaker: CircuitBreaker instance for resilience.
        budget_manager: BudgetManager instance for cost tracking.
        model_id: Optional model ID override.
        timeout: Request timeout in seconds.
        cost_per_clip: Cost per generation attempt in USD.

    Returns:
        Dict with local_path, provider, generation_time_s, video_url.

    Raises:
        RuntimeError: If circuit breaker is OPEN or budget is exhausted.
    """
    if not circuit_breaker.can_execute():
        raise RuntimeError("Circuit breaker OPEN — AI generation blocked, use stock fallback")

    if not budget_manager.can_spend(cost_per_clip):
        raise RuntimeError("Daily budget exhausted — switching to stock-only mode")

    # Deduct on submission (D-05b: deduct on submit, not on success)
    budget_manager.record_spend(cost_per_clip)

    start_time = time.time()
    try:
        result = client.generate_video(prompt, model_id=model_id, timeout=timeout)

        video_url = result["video"]["url"]

        # Download the generated video
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.get(video_url)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(response.content)

        elapsed = time.time() - start_time
        circuit_breaker.record_success()

        # Extract provider name from model_id
        used_model = model_id or client.config.get("primary_model", "unknown")
        provider = used_model.split("/")[1] if "/" in used_model else used_model

        return {
            "local_path": output_path,
            "provider": provider,
            "generation_time_s": round(elapsed, 2),
            "video_url": video_url,
        }

    except Exception:
        circuit_breaker.record_failure()
        raise


def generate_ai_clip_with_fallback(
    prompt: str,
    output_path: str,
    client: FalAIClient,
    circuit_breaker: CircuitBreaker,
    budget_manager: BudgetManager,
    config: dict,
    *,
    veo_client: "VeoClient | None" = None,
    circuit_breaker_veo: "CircuitBreaker | None" = None,
    veo_config: dict = None,
) -> dict:
    """Generate an AI clip with 3-tier fallback chain (per D-04).

    Tries Veo 3.1 Lite first (Tier 0), then Hailuo 2.3 Pro (Tier 1),
    then Vidu 2.0 (Tier 2). If all fail, raises RuntimeError to signal
    that stock fallback is needed.

    Veo components are keyword-only with None defaults for full backwards
    compatibility with existing callers (per D-03, Pitfall 3).

    Args:
        prompt: Text description for AI video generation.
        output_path: Local file path to save the generated video.
        client: FalAIClient instance for Hailuo/Vidu.
        circuit_breaker: CircuitBreaker instance for fal.ai.
        budget_manager: BudgetManager instance for cost tracking.
        config: fal_ai config section with model IDs and costs.
        veo_client: VeoClient instance (or None to skip Veo tier).
        circuit_breaker_veo: CircuitBreaker instance for Veo (or None to skip).
        veo_config: Veo provider config dict (or None for defaults).

    Returns:
        Dict with local_path, provider, generation_time_s, video_url.

    Raises:
        RuntimeError: If all tiers fail.
    """
    # Tier 0: Veo 3.1 Lite (per D-01)
    if (veo_client is not None
            and circuit_breaker_veo is not None
            and circuit_breaker_veo.can_execute()
            and VEO_AVAILABLE):
        vc = veo_config or {}
        duration = int(vc.get("default_duration", 6))
        cost_per_second = vc.get("cost_per_second", 0.05)
        veo_cost = duration * cost_per_second
        veo_daily_budget = vc.get("daily_budget", 5.0)

        # Check Veo-specific budget (per VEO-04: $5 daily Veo cap)
        veo_spent = budget_manager.by_provider.get("veo", 0.0)
        if veo_spent + veo_cost <= veo_daily_budget and budget_manager.can_spend(veo_cost):
            try:
                # Prompt refinement (per VEO-05)
                refined = refine_prompt_for_veo(prompt)
                veo_prompt = refined["prompt"]

                aspect_ratio = vc.get("shorts_aspect_ratio", "9:16")
                budget_manager.record_spend(veo_cost, provider="veo")
                result = veo_client.generate_video(
                    veo_prompt, output_path,
                    aspect_ratio=aspect_ratio, duration=duration,
                )
                circuit_breaker_veo.record_success()
                return result
            except Exception:
                circuit_breaker_veo.record_failure()
                # Fall through to Tier 1

    # Tier 1: Hailuo 2.3 Pro (existing fal.ai primary)
    primary_model = config.get("primary_model", "fal-ai/minimax/hailuo-2.3/pro/text-to-video")
    primary_timeout = config.get("primary_timeout", 120)
    primary_cost = config.get("primary_cost", 0.40)

    try:
        return generate_ai_clip(
            prompt, output_path, client, circuit_breaker, budget_manager,
            model_id=primary_model, timeout=primary_timeout, cost_per_clip=primary_cost,
        )
    except RuntimeError:
        # Re-raise circuit breaker and budget errors (not retryable)
        raise
    except Exception:
        pass  # Tier 1 failed, try Tier 2

    # Tier 2: Vidu 2.0 (existing fal.ai fallback)
    fallback_model = config.get("fallback_model", "fal-ai/vidu/q2/text-to-video")
    fallback_timeout = config.get("fallback_timeout", 30)
    fallback_cost = config.get("fallback_cost", 0.19)

    try:
        return generate_ai_clip(
            prompt, output_path, client, circuit_breaker, budget_manager,
            model_id=fallback_model, timeout=fallback_timeout, cost_per_clip=fallback_cost,
        )
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(
            f"All AI tiers failed (Veo, {primary_model}, {fallback_model}). "
            f"Last error: {e}. Use stock fallback."
        ) from e


# ---------------------------------------------------------------------------
# Prompt Refinement for Veo — 5요소 공식 기반
# ---------------------------------------------------------------------------
#
# 리서치 결과 (RESEARCH_VEO_PROMPT_GUIDE.md) 적용:
# [Shot/Camera] + [Subject] + [Action] + [Setting] + [Style/Mood]
# - Subject front-loading, force-based verbs, 150-300자, 영어 전용
# - negative prompt 미지원 → positive 표현만 사용
# ---------------------------------------------------------------------------

_SENSITIVE_KEYWORDS = [
    "충돌", "사고", "폭발", "총", "살인", "전쟁", "폭력", "시체",
    "자살", "학대", "테러", "납치", "강간", "고문", "마약",
]

# 씬 역할별 카메라/액션 프리셋
_SCENE_PRESETS: dict[str, dict[str, str]] = {
    "hook": {
        "shot": "Close-up, slow dolly in",
        "action": "stares intensely at camera, expression shifts from neutral to surprise",
        "lighting": "Dramatic side lighting with sharp shadows",
    },
    "establishing": {
        "shot": "Wide establishing shot, slow pan right",
        "action": "stands confidently, surveying the scene",
        "lighting": "Natural ambient lighting, golden hour warmth",
    },
    "detail": {
        "shot": "Medium close-up, static camera",
        "action": "gestures emphatically while explaining, leaning forward",
        "lighting": "Soft diffused studio lighting",
    },
    "context": {
        "shot": "Medium shot, gentle tracking left",
        "action": "walks purposefully through the space, glancing around",
        "lighting": "Cool blue-tinted ambient lighting",
    },
    "reaction": {
        "shot": "Close-up, handheld camera with subtle movement",
        "action": "reacts with widened eyes, mouth slightly open in disbelief",
        "lighting": "Warm overhead lighting",
    },
    "cta": {
        "shot": "Medium shot, static camera",
        "action": "points directly at camera with a confident smile",
        "lighting": "Bright, even studio lighting",
    },
}

# 채널별 스타일/무드 프리셋
_CHANNEL_STYLES: dict[str, dict[str, str]] = {
    "humor": {
        "subject": "a young Korean man in casual streetwear",
        "setting": "a busy Korean convenience store with colorful snack shelves",
        "style": "Slightly comedic tone, warm saturated colors, social media vertical style",
    },
    "politics": {
        "subject": "a stern Korean politician in a dark navy suit",
        "setting": "a formal government press conference room with Korean flags",
        "style": "News broadcast documentary style, sharp focus, desaturated color grading",
    },
    "trend": {
        "subject": "a stylish young Korean person in trendy oversized outfit",
        "setting": "a modern minimalist Seoul cafe with large windows",
        "style": "Modern lifestyle aesthetic, cinematic warm color grading, soft bokeh background",
    },
    "sseoltube": {
        "subject": "a middle-aged Korean person in everyday clothing",
        "setting": "a cozy Korean apartment living room at night",
        "style": "Intimate storytelling mood, warm dim lighting, documentary feel",
    },
    "incidents": {
        "subject": "a serious-faced Korean reporter in a dark coat",
        "setting": "a dimly lit urban street at night with police tape",
        "style": "Dark cinematic thriller tone, desaturated cool blue grading, handheld camera feel",
    },
    "product_review": {
        "subject": "a friendly Korean reviewer holding a product",
        "setting": "a clean white studio desk with soft ring light",
        "style": "Clean product photography style, bright even lighting, sharp focus",
    },
}

_DEFAULT_STYLE = {
    "subject": "a Korean person in modern casual clothing",
    "setting": "a contemporary urban Seoul street",
    "style": "Cinematic color grading, natural lighting, social media vertical format",
}


def refine_prompt_for_veo(
    visual_description: str,
    topic_context: str = "",
    channel: str = "",
    scene_role: str = "",
) -> dict:
    """한국어 씬 설명을 Veo 5요소 공식 영어 프롬프트로 변환한다.

    5요소: [Shot/Camera] + [Subject] + [Action] + [Setting] + [Style/Mood]
    150-300자, 영어, positive 표현, force-based verbs.

    visual_description이 프롬프트의 핵심 Subject+Action+Setting이 된다.
    프리셋은 카메라 앵글/조명 보조로만 사용.

    Args:
        visual_description: script.json의 visual 필드 또는 블루프린트 씬 설명.
        topic_context: 영상 주제 (영어 키워드 추출용).
        channel: 채널명 (humor/politics/trend 등). 스타일 자동 선택.
        scene_role: 씬 역할 (hook/establishing/detail/context/reaction/cta).

    Returns:
        Dict: prompt (str), is_sensitive (bool), safety_note (str).
    """
    is_sensitive = any(kw in visual_description for kw in _SENSITIVE_KEYWORDS)
    safety_note = "sensitive keyword detected, Veo may reject" if is_sensitive else ""

    # 씬 역할 감지
    role = scene_role.lower() if scene_role else ""
    if not role:
        for key in _SCENE_PRESETS:
            if key in visual_description.lower():
                role = key
                break
    if not role:
        role = "detail"

    # 프리셋 로드 (카메라/조명 보조만)
    scene = _SCENE_PRESETS.get(role, _SCENE_PRESETS["detail"])
    ch_style = _CHANNEL_STYLES.get(channel, _DEFAULT_STYLE)

    # visual_description → 영어 변환 (한국어 키워드 매핑)
    desc_en = _translate_visual_desc(visual_description, topic_context)

    # 5요소 공식: visual_description이 핵심부, 프리셋은 보조
    if desc_en and desc_en.strip():
        prompt = (
            f"{scene['shot']}, {desc_en}. "
            f"{scene['lighting']}. "
            f"{ch_style['style']}. "
            f"Aspect ratio 9:16."
        )
    else:
        # visual_description이 빈 경우에만 프리셋 폴백
        prompt = (
            f"{scene['shot']} of {ch_style['subject']}, "
            f"{scene['action']}. "
            f"Setting: {ch_style['setting']}. "
            f"{scene['lighting']}. "
            f"{ch_style['style']}. "
            f"Aspect ratio 9:16."
        )

    return {
        "prompt": prompt,
        "is_sensitive": is_sensitive,
        "safety_note": safety_note,
    }


# 한국어 씬 설명 → 영어 변환용 키워드 매핑
_KO_EN_VISUAL_MAP: dict[str, str] = {
    # 장소/환경
    "병원": "hospital",
    "법원": "courthouse",
    "경찰서": "police station",
    "학교": "school building",
    "거리": "urban street",
    "사막": "vast desert landscape",
    "바다": "ocean shore",
    "숲": "dense forest",
    "공원": "public park",
    "아파트": "apartment building",
    "집": "residential house",
    "교도소": "prison",
    "감옥": "jail cell",
    "야간": "nighttime",
    "새벽": "dawn",
    # 사물/증거
    "증거": "forensic evidence on a table",
    "포렌식": "forensic analysis equipment",
    "DNA": "DNA helix visualization",
    "지문": "fingerprint analysis close-up",
    "신발": "shoe evidence on display",
    "옷": "clothing evidence laid out",
    "칼": "sharp object as evidence",
    "컴퓨터": "computer screen glowing in dark room",
    "채팅": "online chat interface on monitor",
    "메신저": "messenger app conversation",
    "CCTV": "CCTV surveillance footage",
    "카메라": "security camera footage",
    "사진": "photograph as evidence",
    "문서": "official documents spread on desk",
    "보고서": "investigation report",
    # 분석/과학
    "분석": "scientific analysis visualization",
    "모래": "sand particles under microscope",
    "형광": "fluorescent dye under UV light",
    "혈흔": "trace evidence markers",
    "약물": "laboratory chemical analysis",
    # 인물/행동
    "탐정": "detective in long coat",
    "경찰": "police officers",
    "수사관": "investigator examining evidence",
    "피해자": "empty chair with personal belongings",
    "용의자": "shadowy silhouette figure",
    "기자": "news reporter with microphone",
    "판사": "judge in courtroom",
    # 감정/분위기
    "긴장": "tense atmosphere",
    "충격": "dramatic moment",
    "슬픔": "somber mood",
    "공포": "eerie atmosphere",
    "미스터리": "mysterious foggy scene",
    "어둠": "darkness with faint light",
    # 건물/구조
    "폐가": "abandoned decrepit house",
    "보존": "preserved old building behind fence",
    "석상": "stone statue in quiet setting",
    "지장보살": "small Buddhist Jizo statue by a riverbank",
}


def _translate_visual_desc(desc: str, topic_context: str = "") -> str:
    """한국어 visual 설명에서 영어 프롬프트 핵심부를 생성한다.

    키워드 매핑 + 원문 구조를 최대한 반영하여
    씬별로 구체적인 영어 프롬프트를 만든다.
    """
    if not desc:
        return ""

    # 1) 매핑되는 키워드 수집
    matched_parts: list[str] = []
    for ko, en in _KO_EN_VISUAL_MAP.items():
        if ko in desc:
            matched_parts.append(en)

    # 2) 이미 영어가 섞여 있으면 추출 (예: "MI5", "DNA", "CCTV")
    import re
    english_phrases = re.findall(r'[A-Za-z][A-Za-z0-9\s\-]{2,}', desc)
    for phrase in english_phrases:
        phrase = phrase.strip()
        if phrase and phrase.lower() not in [p.lower() for p in matched_parts]:
            matched_parts.append(phrase)

    if not matched_parts:
        # 매핑 실패 시 topic_context를 기반으로 일반적 프롬프트 생성
        if topic_context:
            return f"a scene depicting {topic_context}"
        return ""

    # 3) 조합: 매칭된 영어 키워드를 자연스러운 씬 설명으로 조립
    scene_desc = ", ".join(matched_parts[:5])  # 최대 5개 키워드
    return f"a detailed scene showing {scene_desc}"
