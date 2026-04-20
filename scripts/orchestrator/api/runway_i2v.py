"""Runway Gen-3 Alpha Turbo image-to-video adapter (VIDEO-04 backup).

Secondary I2V provider used when the Kling circuit trips OPEN
(:class:`KlingI2VAdapter` fails 3 times). Model is hard-narrowed to
``gen3_alpha_turbo`` per D-16 — the harvested ``runway_client.py`` supports
Gen-4.5 / Veo 3.1 too, but this adapter deliberately carries only one
model to keep the backup path boringly deterministic.

**Physical absence of T2V** (D-13 / VIDEO-01 / RESEARCH §8 line 785): the
harvested wrapper exposed a text-only generation method, but the Phase 5
rewrite deliberately strips it. The bottom-of-module assertion, the
mirror test in
``tests/phase05/test_kling_adapter.py``, and the
``.claude/deprecated_patterns.json`` regex are three independent signals
that no text-only sibling exists.

API key resolution order: constructor ``api_key`` -> ``$RUNWAY_API_KEY`` ->
``$RUNWAYML_API_SECRET`` (the SDK's canonical env var; accepted as an alias).
Raises ``ValueError`` if none resolves.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..gates import T2VForbidden
from .models import I2VRequest

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker


# ---------------------------------------------------------------------------
# Model / ratio / timeout defaults — derived from the harvested
# ``runway_client.py`` MODEL_REGISTRY (gen3_alpha_turbo row) per D-16.
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gen3a_turbo"  # 2026-04-20 대표님 dual-tier 결정: batch primary
# (flagship primary = gen4.5, 복합 prompt 품질 우위이나 $0.60/5s + 129s latency;
#  batch primary = gen3a_turbo, 품질 충분 + $0.25/5s + 21s latency = 6x throughput).
# 모델별 valid ratios 상이: gen3a_turbo ∈ {"16:9","9:16","768:1280","1280:768"}.
DEFAULT_RATIO = "768:1280"  # 9:16 vertical Shorts format (gen3a_turbo compatible)
DEFAULT_POLL_TIMEOUT_S = 600
DEFAULT_HTTP_TIMEOUT_S = 120
DEFAULT_OUTPUT_DIR = Path("outputs/runway")


class RunwayI2VAdapter:
    """Backup image-to-video provider (Runway Gen-3 Alpha Turbo).

    Parameters mirror :class:`KlingI2VAdapter` so Plan 07 can swap them 1:1
    in the failover path::

        try:
            clip = kling.image_to_video(prompt, anchor, duration)
        except (CircuitOpen, RuntimeError):
            clip = runway.image_to_video(prompt, anchor, duration)
    """

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
    ) -> None:
        resolved = (
            api_key
            or os.environ.get("RUNWAY_API_KEY")
            or os.environ.get("RUNWAYML_API_SECRET")
        )
        if not resolved:
            raise ValueError(
                "RunwayI2VAdapter: no API key supplied and neither RUNWAY_API_KEY"
                " nor RUNWAYML_API_SECRET is set in the environment."
            )
        self._api_key = resolved
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API — I2V only (D-13 physical absence of text-only mode).
    # ------------------------------------------------------------------

    def image_to_video(
        self,
        prompt: str,
        anchor_frame: Path | None,
        duration_seconds: int = 5,
    ) -> Path:
        """Generate a 4-8s clip from ``anchor_frame`` + motion prompt.

        Mirrors :meth:`KlingI2VAdapter.image_to_video` so the two adapters
        remain drop-in swappable in the failover path.
        """

        if anchor_frame is None:
            raise T2VForbidden(
                "D-13: anchor_frame REQUIRED; text-only generation was removed"
                " from the Runway adapter per RESEARCH §8 (VIDEO-01)."
            )
        if not isinstance(anchor_frame, Path):
            anchor_frame = Path(anchor_frame)

        req = I2VRequest(
            prompt=prompt,
            anchor_frame=anchor_frame,
            duration_seconds=duration_seconds,
        )

        kwargs: dict[str, Any] = {
            "model": DEFAULT_MODEL,
            "prompt_image": req.anchor_frame,
            "prompt_text": req.prompt,
            "ratio": DEFAULT_RATIO,
            "duration": req.duration_seconds,
        }
        return self._invoke_runway(kwargs)

    # ------------------------------------------------------------------
    # Internals — test-mockable seam
    # ------------------------------------------------------------------

    def _invoke_runway(self, kwargs: dict[str, Any]) -> Path:
        """Hit the Runway SDK with ``kwargs`` and download the resulting MP4.

        ``runwayml`` is imported lazily so test modules can patch this method
        without the SDK installed. Plan 07 wraps the call through the
        breaker, not this method directly — CircuitBreaker protection belongs
        at the adapter seam, not deeper.
        """

        from runwayml import RunwayML  # lazy import

        client = RunwayML(api_key=self._api_key)

        # Translate the pathlib.Path anchor into the data-URI form the SDK
        # expects. Harvested helper was ``_resolve_prompt_image`` / ``_file_to_data_uri``.
        prompt_image = kwargs["prompt_image"]
        if isinstance(prompt_image, Path):
            kwargs["prompt_image"] = self._file_to_data_uri(prompt_image)

        task = client.image_to_video.create(**kwargs)
        result = task.wait_for_task_output(timeout=DEFAULT_POLL_TIMEOUT_S)

        outputs = getattr(result, "output", None) or []
        if not outputs:
            raise RuntimeError(
                f"RunwayI2VAdapter: Runway task produced no output URLs: {result!r}"
            )
        return self._download_result(outputs[0])

    def _file_to_data_uri(self, path: Path) -> str:
        """Base64-encode a local file into a ``data:`` URI for the Runway SDK."""

        import base64
        import mimetypes

        mime, _ = mimetypes.guess_type(str(path))
        if mime is None:
            mime = "image/jpeg"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def _download_result(self, video_url: str) -> Path:
        """Download ``video_url`` into ``self.output_dir`` and return the path."""

        import httpx  # lazy

        self.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = self.output_dir / f"runway_{stamp}.mp4"
        with httpx.stream(
            "GET", video_url, timeout=DEFAULT_HTTP_TIMEOUT_S, follow_redirects=True
        ) as resp:
            resp.raise_for_status()
            with out.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
        return out


# ---------------------------------------------------------------------------
# Belt-and-suspenders D-13 enforcement (mirrors kling_i2v.py).
# ---------------------------------------------------------------------------

_FORBIDDEN_ATTR = "text_" + "to_" + "video"
assert not hasattr(RunwayI2VAdapter, _FORBIDDEN_ATTR), (
    "D-13 violation: RunwayI2VAdapter re-introduced a text-only generation method."
    " RESEARCH §8 line 785 specifically removed it from the Runway rewrite."
)


__all__ = [
    "RunwayI2VAdapter",
    "DEFAULT_MODEL",
    "DEFAULT_RATIO",
]
