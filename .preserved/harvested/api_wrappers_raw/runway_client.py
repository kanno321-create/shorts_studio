"""Runway ML video generation client — Gen-4.5 / Gen-4 Turbo for shorts + longform.

Memory rationale (2026-04-17):
  * project_runway_gen45_confirmed — Gen-4.5 ≈ $0.12/s routine, Veo 3.1 ≈ $0.40/s premium (core scenes only)
  * feedback_veo_cost_priority — Veo reserved for high-fidelity moments, Runway handles the bulk
  * feedback_veo_supplementary_only — AI video is SUPPLEMENTARY. 1차 자료 (Wikimedia/BBC/Guardian) 우선

Pattern: FLUX Pro Kontext T2I → Runway Gen-4.5 I2V (motion injected). Veo 3.1 Lite kept for
re-create-impossible scenes (detective/assistant duo, signature intros).

SDK: ``runwayml`` v4.12.0 (Apr 2026). Canonical env var is ``RUNWAYML_API_SECRET``; this module
also accepts ``RUNWAY_API_KEY`` (historical alias from .env).

Exit codes:
    Module — imported by video-sourcer / ai_visual_generate.

Environment variables:
    RUNWAY_API_KEY or RUNWAYML_API_SECRET — Runway API secret.
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    import httpx
    from runwayml import RunwayML
    from runwayml._exceptions import (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        RateLimitError,
    )
    from runwayml.lib.polling import TaskFailedError, TaskTimeoutError

    RUNWAY_AVAILABLE = True
except ImportError as _import_exc:  # pragma: no cover - install hint only
    RunwayML = None  # type: ignore[assignment]
    APIConnectionError = Exception  # type: ignore[assignment]
    APIStatusError = Exception  # type: ignore[assignment]
    APITimeoutError = Exception  # type: ignore[assignment]
    AuthenticationError = Exception  # type: ignore[assignment]
    BadRequestError = Exception  # type: ignore[assignment]
    RateLimitError = Exception  # type: ignore[assignment]
    TaskFailedError = Exception  # type: ignore[assignment]
    TaskTimeoutError = Exception  # type: ignore[assignment]
    httpx = None  # type: ignore[assignment]
    RUNWAY_AVAILABLE = False
    _IMPORT_ERROR = _import_exc

logger = logging.getLogger(__name__)


# --- Model registry ------------------------------------------------------

# Gen-4.5 = default for routine shorts (9:16). Good quality, lower cost, supports T2V + I2V.
# Gen-4 Turbo = cheaper iteration (I2V only).
# Veo 3.1 / Veo 3.1 Fast = kept for cinematic signature scenes routed through Runway as well.
# Seedance 2 + Gen-3a Turbo = not used by default for incidents/humor/politics; available for
# specific creative asks.

ShortsRatio = Literal["720:1280"]  # 9:16 vertical, all Gen-4.5 / Gen-4 Turbo / Veo routes
LandscapeRatio = Literal["1280:720"]


@dataclass(frozen=True)
class ModelSpec:
    """Runway model capability + cost reference."""

    model_id: str
    supports_t2v: bool
    supports_i2v: bool
    shorts_ratios: tuple[str, ...]
    max_duration_s: int
    cost_per_second_usd: float


MODEL_REGISTRY: dict[str, ModelSpec] = {
    # Gen-4.5: routine video gen per memory project_runway_gen45_confirmed.
    # ratios: 720:1280 (shorts 9:16) + 1280:720 (longform 16:9, session 77+).
    "gen4.5": ModelSpec(
        model_id="gen4.5",
        supports_t2v=True,
        supports_i2v=True,
        shorts_ratios=("720:1280", "1280:720"),
        max_duration_s=10,
        cost_per_second_usd=0.12,
    ),
    # Gen-4 Turbo: I2V only, cheaper iteration
    "gen4_turbo": ModelSpec(
        model_id="gen4_turbo",
        supports_t2v=False,
        supports_i2v=True,
        shorts_ratios=("720:1280", "1280:720"),
        max_duration_s=10,
        cost_per_second_usd=0.05,
    ),
    # Veo 3.1: premium — Veo 3.1 Lite routed through direct Google API remains preferred
    # for signature scenes; this entry exists so Runway can also host Veo 3.1 tasks.
    "veo3.1": ModelSpec(
        model_id="veo3.1",
        supports_t2v=True,
        supports_i2v=True,
        shorts_ratios=("720:1280", "1080:1920", "1280:720", "1920:1080"),
        max_duration_s=8,
        cost_per_second_usd=0.40,
    ),
    "veo3.1_fast": ModelSpec(
        model_id="veo3.1_fast",
        supports_t2v=True,
        supports_i2v=True,
        shorts_ratios=("720:1280", "1080:1920", "1280:720", "1920:1080"),
        max_duration_s=8,
        cost_per_second_usd=0.20,
    ),
}


DEFAULT_MODEL = "gen4.5"
DEFAULT_SHORTS_RATIO = "720:1280"
DEFAULT_DURATION_S = 5
DEFAULT_POLL_TIMEOUT_S = 600  # 10 min — Runway queue can take a while under load


# --- Errors -------------------------------------------------------------


class RunwayClientError(Exception):
    """Base error raised by the RunwayClient wrapper."""


class RunwayNotInstalledError(RunwayClientError):
    """Raised when runwayml SDK is unavailable at runtime."""


class RunwayUnsupportedError(RunwayClientError):
    """Raised when the requested (model, capability, ratio) triple is invalid."""


# --- Client -------------------------------------------------------------


class RunwayClient:
    """Thin wrapper around ``runwayml.RunwayML`` matching the project's I2V / T2V needs.

    Responsibilities:
        * Resolve API key from either ``RUNWAY_API_KEY`` or ``RUNWAYML_API_SECRET``
        * Validate model / ratio / duration against ``MODEL_REGISTRY``
        * Convert local image paths to data URIs so they can be passed to the SDK
        * Poll the task to completion and download the resulting MP4 to disk
        * Return a ``GenerationResult`` with path + cost + task metadata for budget tracking

    The orchestrator agent + video-sourcer call this for "routine" video generation; Veo 3.1
    Lite through the direct Google API remains preferred for Veo-specific signature shots.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        default_model: str = DEFAULT_MODEL,
        default_ratio: str = DEFAULT_SHORTS_RATIO,
        default_duration_s: int = DEFAULT_DURATION_S,
        poll_timeout_s: int = DEFAULT_POLL_TIMEOUT_S,
        http_timeout_s: int = 120,
    ) -> None:
        if not RUNWAY_AVAILABLE:
            raise RunwayNotInstalledError(
                "runwayml SDK not installed. Run: pip install runwayml"
            ) from _IMPORT_ERROR
        resolved = api_key or os.environ.get("RUNWAY_API_KEY") or os.environ.get(
            "RUNWAYML_API_SECRET"
        )
        if not resolved:
            raise RunwayClientError(
                "Runway API key not found. Set RUNWAY_API_KEY or RUNWAYML_API_SECRET "
                "in the environment."
            )
        self._client = RunwayML(api_key=resolved)
        self.default_model = default_model
        self.default_ratio = default_ratio
        self.default_duration_s = default_duration_s
        self.poll_timeout_s = poll_timeout_s
        self.http_timeout_s = http_timeout_s

    # --- public API ------------------------------------------------------

    def image_to_video(
        self,
        *,
        prompt_image: str | Path,
        prompt_text: str,
        output_path: Path,
        model: str | None = None,
        ratio: str | None = None,
        duration_s: int | None = None,
        seed: int | None = None,
    ) -> GenerationResult:
        """Generate a video clip from one image + text prompt and download it to ``output_path``.

        ``prompt_image`` can be either an HTTPS URL or a local file path; local paths are
        converted to data URIs (the SDK accepts either).
        """
        model_id = model or self.default_model
        spec = MODEL_REGISTRY.get(model_id)
        if spec is None:
            raise RunwayUnsupportedError(f"Unknown model '{model_id}'. Known: {list(MODEL_REGISTRY)}")
        if not spec.supports_i2v:
            raise RunwayUnsupportedError(f"Model '{model_id}' does not support image_to_video.")

        ratio_str = ratio or self.default_ratio
        if ratio_str not in spec.shorts_ratios:
            raise RunwayUnsupportedError(
                f"Model '{model_id}' does not support ratio '{ratio_str}'. "
                f"Supported: {spec.shorts_ratios}"
            )

        dur = duration_s or self.default_duration_s
        if dur < 2 or dur > spec.max_duration_s:
            raise RunwayUnsupportedError(
                f"Duration {dur}s out of range for '{model_id}' (2-{spec.max_duration_s})."
            )

        if len(prompt_text) > 1000:
            raise RunwayUnsupportedError("prompt_text must be ≤ 1000 characters.")

        prompt_image_value = _resolve_prompt_image(prompt_image)

        logger.info(
            "[runway] image_to_video model=%s ratio=%s duration=%ds",
            model_id,
            ratio_str,
            dur,
        )

        kwargs: dict = {
            "model": model_id,
            "prompt_image": prompt_image_value,
            "prompt_text": prompt_text,
            "ratio": ratio_str,
            "duration": dur,
        }
        if seed is not None:
            kwargs["seed"] = seed

        task = self._client.image_to_video.create(**kwargs)
        return self._await_and_download(task, output_path, spec, dur)

    def text_to_video(
        self,
        *,
        prompt_text: str,
        output_path: Path,
        model: str | None = None,
        ratio: str | None = None,
        duration_s: int | None = None,
        seed: int | None = None,
    ) -> GenerationResult:
        """Generate a video clip from text-only prompt and download it to ``output_path``."""
        model_id = model or self.default_model
        spec = MODEL_REGISTRY.get(model_id)
        if spec is None:
            raise RunwayUnsupportedError(f"Unknown model '{model_id}'. Known: {list(MODEL_REGISTRY)}")
        if not spec.supports_t2v:
            raise RunwayUnsupportedError(f"Model '{model_id}' does not support text_to_video.")

        ratio_str = ratio or self.default_ratio
        if ratio_str not in spec.shorts_ratios:
            raise RunwayUnsupportedError(
                f"Model '{model_id}' does not support ratio '{ratio_str}'. "
                f"Supported: {spec.shorts_ratios}"
            )

        dur = duration_s or self.default_duration_s
        if dur < 2 or dur > spec.max_duration_s:
            raise RunwayUnsupportedError(
                f"Duration {dur}s out of range for '{model_id}' (2-{spec.max_duration_s})."
            )

        if len(prompt_text) > 1000:
            raise RunwayUnsupportedError("prompt_text must be ≤ 1000 characters.")

        logger.info(
            "[runway] text_to_video model=%s ratio=%s duration=%ds",
            model_id,
            ratio_str,
            dur,
        )

        kwargs: dict = {
            "model": model_id,
            "prompt_text": prompt_text,
            "ratio": ratio_str,
            "duration": dur,
        }
        if seed is not None:
            kwargs["seed"] = seed

        task = self._client.text_to_video.create(**kwargs)
        return self._await_and_download(task, output_path, spec, dur)

    # --- internals -------------------------------------------------------

    def _await_and_download(
        self,
        task,
        output_path: Path,
        spec: ModelSpec,
        duration_s: int,
    ) -> GenerationResult:
        started = time.monotonic()
        try:
            result = task.wait_for_task_output(timeout=self.poll_timeout_s)
        except TaskFailedError as exc:
            raise RunwayClientError(
                f"Runway task failed: {getattr(exc, 'task_details', exc)}"
            ) from exc
        except TaskTimeoutError as exc:
            raise RunwayClientError(
                f"Runway task timed out after {self.poll_timeout_s}s"
            ) from exc
        except (APITimeoutError, APIConnectionError) as exc:
            raise RunwayClientError(f"Runway network error: {exc}") from exc
        except RateLimitError as exc:
            raise RunwayClientError(f"Runway rate limit hit: {exc}") from exc
        except AuthenticationError as exc:
            raise RunwayClientError(f"Runway auth failed: {exc}") from exc
        except (BadRequestError, APIStatusError) as exc:
            raise RunwayClientError(f"Runway request rejected: {exc}") from exc

        elapsed = time.monotonic() - started

        # SDK returns a `Task` where `output` is a list of asset URLs (first URL = video MP4).
        outputs = getattr(result, "output", None) or []
        if not outputs:
            raise RunwayClientError(
                f"Runway task succeeded but returned no output URLs. Task: {result}"
            )
        video_url = outputs[0]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        _download_url(video_url, output_path, timeout=self.http_timeout_s)

        cost_usd = round(spec.cost_per_second_usd * duration_s, 3)
        logger.info(
            "[runway] generated %s in %.1fs (cost ~$%.2f)",
            output_path,
            elapsed,
            cost_usd,
        )
        return GenerationResult(
            path=output_path,
            model=spec.model_id,
            duration_s=duration_s,
            cost_usd=cost_usd,
            task_id=getattr(result, "id", None),
            video_url=video_url,
            elapsed_s=round(elapsed, 2),
        )


# --- helpers ------------------------------------------------------------


@dataclass(frozen=True)
class GenerationResult:
    """Returned by every RunwayClient generation call. Used by BudgetManager + audit logs."""

    path: Path
    model: str
    duration_s: int
    cost_usd: float
    task_id: str | None
    video_url: str
    elapsed_s: float


def _resolve_prompt_image(prompt_image: str | Path) -> str:
    """Accept HTTPS URL or local path; return either URL or data URI.

    Runway's `promptImage` accepts both HTTPS URLs and data URIs.
    """
    if isinstance(prompt_image, Path):
        return _file_to_data_uri(prompt_image)
    if prompt_image.startswith(("http://", "https://", "data:")):
        return prompt_image
    # Heuristic: looks like a local path string
    p = Path(prompt_image)
    if p.exists():
        return _file_to_data_uri(p)
    raise RunwayUnsupportedError(
        f"prompt_image must be an HTTPS URL, data URI, or existing local file. Got: {prompt_image!r}"
    )


def _file_to_data_uri(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        # Fallback: assume jpeg for common short-form stills
        mime = "image/jpeg"
    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _download_url(url: str, dest: Path, *, timeout: int) -> None:
    """Stream-download a URL to ``dest``. Runway asset URLs are pre-signed HTTPS links."""
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as resp:
        resp.raise_for_status()
        with dest.open("wb") as f:
            for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                f.write(chunk)


__all__ = [
    "RunwayClient",
    "GenerationResult",
    "ModelSpec",
    "MODEL_REGISTRY",
    "DEFAULT_MODEL",
    "DEFAULT_SHORTS_RATIO",
    "DEFAULT_DURATION_S",
    "RunwayClientError",
    "RunwayNotInstalledError",
    "RunwayUnsupportedError",
    "RUNWAY_AVAILABLE",
]
