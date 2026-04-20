"""Shotstack assembly + 720p render + ken-burns fallback adapter.

Implements three responsibilities for the ASSEMBLY gate (Plan 07):

* :meth:`ShotstackAdapter.render` — assemble
  :class:`scripts.orchestrator.voice_first_timeline.TimelineEntry` /
  :class:`TransitionEntry` items into Shotstack's JSON timeline, apply
  the D-17 filter order (color grade -> saturation -> film grain), and
  POST to the ``/render`` endpoint at ``"hd"`` (720p) by default per
  ORCH-11 Low-Res First.
* :meth:`ShotstackAdapter.upscale` — Phase 5 NOOP stub per RESEARCH §7
  lines 770-773. 720p is the shipping resolution; upscale is deferred
  to Phase 8 if analytics show quality-driven drop-off.
* :meth:`ShotstackAdapter.create_ken_burns_clip` — generate a
  static-image clip with scale + pan (ORCH-12 Fallback lane). Used when
  asset-sourcer returns a still and the regeneration loop has exhausted
  its retries (RESEARCH §9 lines 836-847).

All HTTP traffic runs through :class:`httpx.Client` so tests can mock the
client with :class:`unittest.mock.MagicMock` without a real network. The
adapter accepts an optional :class:`CircuitBreaker` for Plan 07 to wrap
both ``render`` and ``create_ken_burns_clip`` in failure protection.

API key resolution: ``api_key`` -> ``$SHOTSTACK_API_KEY``. Raises
``ValueError`` if missing.
"""
from __future__ import annotations

import os
import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from ..voice_first_timeline import TimelineEntry, TransitionEntry
from .models import ContinuityPrefix, ShotstackRenderRequest

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker


DEFAULT_OUTPUT_DIR = Path("outputs/shotstack")

# D-9 / D-19 Phase 6 WIKI-02: Continuity Bible prefix injected at filter[0].
# Source = wiki/continuity_bible/prefix.json; schema = models.ContinuityPrefix (D-20).
DEFAULT_CONTINUITY_PRESET_PATH = Path("wiki/continuity_bible/prefix.json")


def _load_continuity_preset(path: Path | None = None) -> ContinuityPrefix | None:
    """D-9/D-19: load ContinuityPrefix from prefix.json. Returns None when
    file absent (graceful degradation). ValidationError propagates on
    schema drift / out-of-range / malformed HEX (D-20 Pitfall 5 fail-fast).
    ``path`` overrides the module default (unit tests)."""
    p = path or DEFAULT_CONTINUITY_PRESET_PATH
    if not p.exists():
        return None
    return ContinuityPrefix.model_validate_json(p.read_text(encoding="utf-8"))


class ShotstackAdapter:
    """Shotstack render adapter (ORCH-11 720p + ORCH-12 ken-burns fallback)."""

    # Sandbox endpoint keeps tests free of accidental production spend.
    # Production URL: ``https://api.shotstack.io/v1/render``; callers override
    # via the ``base_url`` constructor arg at deploy time.
    BASE_URL: str = "https://api.shotstack.io/stage/render"

    # ORCH-11: first-pass render is 720p. 9:16 vertical per Shorts format.
    DEFAULT_RESOLUTION: str = "hd"
    DEFAULT_ASPECT: str = "9:16"

    # D-17: color grade -> saturation -> film grain. Ordering matters —
    # applying saturation before color grade loses shadow detail; grain
    # must come last so it isn't resampled by the grade pass.
    FILTER_ORDER: tuple[str, str, str] = ("color_grade", "saturation", "film_grain")

    DEFAULT_TIMEOUT_S = 120

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        base_url: str | None = None,
        output_dir: Path | None = None,
    ) -> None:
        resolved = api_key or os.environ.get("SHOTSTACK_API_KEY")
        if not resolved:
            raise ValueError(
                "ShotstackAdapter: no API key supplied and SHOTSTACK_API_KEY is"
                " not set in the environment."
            )
        self._api_key = resolved
        self.circuit_breaker = circuit_breaker
        self.base_url = base_url or self.BASE_URL
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(
        self,
        timeline: list,
        resolution: str | None = None,
        aspect_ratio: str | None = None,
    ) -> dict:
        """Submit a Shotstack render job and return the response dict.

        ``timeline`` is a list of :class:`TimelineEntry` and / or
        :class:`TransitionEntry` dataclass instances. The helper
        :meth:`_build_timeline_payload` serialises them into Shotstack's
        JSON shape before the HTTP call.
        """

        resolution = resolution or self.DEFAULT_RESOLUTION
        aspect_ratio = aspect_ratio or self.DEFAULT_ASPECT

        # Parse-time validation. ShotstackRenderRequest pins the default
        # filter order at D-17; the adapter passes that list through
        # verbatim so a downstream render config can introspect what
        # was applied.
        serialised_entries = self._serialise_timeline_entries(timeline)
        req = ShotstackRenderRequest(
            timeline_entries=serialised_entries,
            resolution=resolution,  # type: ignore[arg-type]
            aspect_ratio=aspect_ratio,  # type: ignore[arg-type]
        )

        payload = self._build_timeline_payload(
            serialised_entries=req.timeline_entries,
            resolution=req.resolution,
            aspect_ratio=req.aspect_ratio,
            filters_order=req.filters_order,
        )

        return self._post_render(payload)

    def upscale(self, source_url: str) -> dict:
        """Phase 5 NOOP. Returns a ``{"status": "skipped", ...}`` dict.

        RESEARCH §7 (lines 770-773) documents the decision: Shotstack has
        no native upscale endpoint, Topaz Video AI requires a paid
        license, and Real-ESRGAN is too slow for 3-4 videos / week. 720p
        is accepted as the shipping asset. Upscale becomes a Phase 8
        optimisation only if analytics show quality-driven drop-off.
        """

        return {
            "status": "skipped",
            "reason": "Phase 8 optimization deferred — 720p ships as-is per ORCH-11",
            "source_url": source_url,
        }

    def create_ken_burns_clip(
        self,
        image_path: Path,
        duration_s: float,
        scale_from: float = 1.0,
        scale_to: float = 1.15,
        pan_direction: str = "left_to_right",
    ) -> Path:
        """Generate a pan+scale static-image clip (ORCH-12 Fallback lane).

        .. deprecated:: 9.1
           Phase 9.1 D-11: replaced by :class:`KenBurnsLocalAdapter` in
           ``scripts.orchestrator.api.ken_burns`` (offline ffmpeg, no
           API cost / latency / network). This method remains functional
           for Phase 7 fallback regression but will be removed in
           Phase 10 once the fallback chain fully migrates.

        Submits a single-clip Shotstack render where the asset is the
        still image and the effect is a zoomIn + pan. Returns the local
        :class:`Path` of the downloaded MP4.

        RESEARCH §9 lines 836-847 specifies this as the standard Fallback
        when the regeneration loop exhausts retries on an ASSETS /
        THUMBNAIL gate and asset-sourcer produces a stock still instead.
        """

        warnings.warn(
            "ShotstackAdapter.create_ken_burns_clip 는 Phase 9.1 D-11 에서 "
            "deprecated 처리되었습니다 — KenBurnsLocalAdapter "
            "(scripts.orchestrator.api.ken_burns) 사용 권장 (대표님). "
            "본 메서드는 Phase 10 재설계에서 완전 제거 예정.",
            DeprecationWarning,
            stacklevel=2,
        )

        effect_name = self._pan_direction_to_effect(pan_direction)

        payload = {
            "timeline": {
                "background": "#000000",
                "tracks": [
                    {
                        "clips": [
                            {
                                "asset": {
                                    "type": "image",
                                    "src": image_path.as_posix(),
                                },
                                "start": 0,
                                "length": duration_s,
                                "effect": effect_name,
                                "scale": {
                                    "from": scale_from,
                                    "to": scale_to,
                                },
                                "transition": {
                                    "in": "fade",
                                    "out": "fade",
                                },
                            }
                        ]
                    }
                ],
            },
            "output": {
                "format": "mp4",
                "resolution": self.DEFAULT_RESOLUTION,
                "aspectRatio": self.DEFAULT_ASPECT,
            },
        }

        response = self._post_render(payload)
        video_url = (
            (response.get("response") or {}).get("url")
            or response.get("url")
            or ""
        )
        return self._download_result(video_url, prefix="kenburns")

    # ------------------------------------------------------------------
    # Internal helpers (mockable seams)
    # ------------------------------------------------------------------

    def _serialise_timeline_entries(
        self, timeline: list
    ) -> list[dict[str, Any]]:
        """Translate TimelineEntry / TransitionEntry dataclass items to dicts.

        Dicts are intentionally flat so :class:`ShotstackRenderRequest` can
        store them in ``timeline_entries`` without caring about the
        dataclass subtype.
        """

        out: list[dict[str, Any]] = []
        for item in timeline:
            if isinstance(item, TimelineEntry):
                out.append(
                    {
                        "kind": "clip",
                        "start": item.start,
                        "end": item.end,
                        "clip_path": item.clip_path.as_posix(),
                        "speed": item.speed,
                        "audio_path": item.audio_path.as_posix(),
                    }
                )
            elif isinstance(item, TransitionEntry):
                out.append(
                    {
                        "kind": "transition",
                        "template": item.template,
                        "duration": item.duration,
                        "after_index": item.after_index,
                    }
                )
            elif isinstance(item, dict):
                # Tests sometimes pass pre-built dicts; accept them verbatim.
                out.append(item)
            else:  # pragma: no cover - defensive
                raise TypeError(
                    f"ShotstackAdapter.render: unsupported timeline item {type(item).__name__}"
                )
        return out

    def _build_timeline_payload(
        self,
        *,
        serialised_entries: list[dict[str, Any]],
        resolution: str,
        aspect_ratio: str,
        filters_order: list[str],
    ) -> dict[str, Any]:
        """Build Shotstack render JSON. D-9/D-19 WIKI-02: prepends
        ``"continuity_prefix"`` at filter[0] when preset loaded; D-17 tail
        preserved; idempotent; caller list not mutated."""

        # D-9/D-19: preset None when prefix.json absent → pass-through.
        preset = _load_continuity_preset()
        if preset is not None and (
            not filters_order or filters_order[0] != "continuity_prefix"
        ):
            filters_order = ["continuity_prefix", *filters_order]

        clips: list[dict[str, Any]] = []
        audio_tracks: list[dict[str, Any]] = []
        for entry in serialised_entries:
            if entry.get("kind") == "clip":
                clip_entry = {
                    "asset": {
                        "type": "video",
                        "src": entry["clip_path"],
                    },
                    "start": entry["start"],
                    "length": max(0.0, entry["end"] - entry["start"]),
                    "speed": entry["speed"],
                }
                clips.append(clip_entry)
                audio_tracks.append(
                    {
                        "asset": {
                            "type": "audio",
                            "src": entry["audio_path"],
                        },
                        "start": entry["start"],
                        "length": max(0.0, entry["end"] - entry["start"]),
                    }
                )
            elif entry.get("kind") == "transition":
                clips.append(
                    {
                        "asset": {
                            "type": "transition",
                            "template": entry["template"],
                        },
                        "start": entry.get("start", 0.0),
                        "length": entry["duration"],
                    }
                )
            else:
                clips.append(entry)

        return {
            "timeline": {
                "background": "#000000",
                "tracks": [
                    {"clips": clips},
                    {"clips": audio_tracks},
                ],
                "filters": list(filters_order),
                # D-20 preset params for downstream; None when prefix.json missing.
                "continuity_preset": (
                    preset.model_dump() if preset is not None else None
                ),
            },
            "output": {
                "format": "mp4",
                "resolution": resolution,
                "aspectRatio": aspect_ratio,
            },
        }

    def _post_render(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST ``payload`` to the Shotstack render endpoint.

        Tests patch ``httpx.Client`` so the real network is never touched.
        """

        headers = {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.DEFAULT_TIMEOUT_S) as client:
            resp = client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data

    def _download_result(self, video_url: str, *, prefix: str = "render") -> Path:
        """Download a completed render to :attr:`output_dir`."""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = self.output_dir / f"{prefix}_{stamp}.mp4"

        # Local-file URL (used by tests): skip the network round-trip.
        if video_url.startswith("file://"):
            src = Path(video_url.removeprefix("file://"))
            out.write_bytes(src.read_bytes() if src.exists() else b"")
            return out

        if not video_url:
            # No URL came back; touch an empty placeholder so callers can
            # see the expected path and log a clear failure reason.
            out.write_bytes(b"")
            return out

        with httpx.stream(
            "GET", video_url, timeout=self.DEFAULT_TIMEOUT_S, follow_redirects=True
        ) as resp:
            resp.raise_for_status()
            with out.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
        return out

    @staticmethod
    def _pan_direction_to_effect(direction: str) -> str:
        """Map a ``pan_direction`` label to a Shotstack effect name."""

        mapping = {
            "left_to_right": "zoomInSlow",
            "right_to_left": "zoomInSlowReverse",
            "top_to_bottom": "zoomInPanDown",
            "bottom_to_top": "zoomInPanUp",
        }
        return mapping.get(direction, "zoomIn")


__all__ = ["ShotstackAdapter"]
