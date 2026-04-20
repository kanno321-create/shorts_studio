"""Nano Banana Pro image adapter (REQ-091-02, Phase 9.1).

Generates scene anchor images via Google's ``nano-banana-pro-preview`` model
(google-genai SDK). Signature mirrors :class:`KlingI2VAdapter` /
:class:`RunwayI2VAdapter` so the asset-sourcer producer can swap providers
without reshaping the return value.

Reference pattern (NOT copied line-for-line): ``shorts_naberal/scripts/
video-pipeline/_nanobanana_from_script_v3.py`` (145 lines). Safety fallback
+ inline_data bytes persistence ported from that working module
(feedback_clean_slate_rebuild: patterns only, no code duplication).

API key resolution order:
    constructor ``api_key`` -> ``$GOOGLE_API_KEY`` -> ``$GEMINI_API_KEY`` -> ValueError

Costs (Phase 9.1 D-15 budget): $0.04/image via nano-banana-pro-preview.
"""
from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

# Module-level import so tests can monkeypatch `nb_mod.genai` directly.
# Wrapped in try/except so module imports cleanly even if SDK is absent
# (unit tests never require the real SDK; they replace `genai` wholesale).
try:
    from google import genai  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — test env monkeypatches this symbol
    genai = None  # type: ignore[assignment]

DEFAULT_OUTPUT_DIR = Path("outputs/nanobanana")

_SAFETY_KEYWORDS = ("SAFETY", "BLOCK", "PROHIBITED")
_SOFTEN_BLOCKLIST = {"blood", "gore", "violence", "naked", "nude"}
_SOFTEN_PATTERN = re.compile(
    r"\b(" + "|".join(_SOFTEN_BLOCKLIST) + r")\b",
    re.IGNORECASE,
)


class NanoBananaAdapter:
    """Scene anchor image generator (Google ``nano-banana-pro-preview``).

    Parameters
    ----------
    api_key:
        Explicit API key. If omitted, falls back to ``$GOOGLE_API_KEY`` then
        ``$GEMINI_API_KEY``. Raises ``ValueError`` (Korean message) if none
        resolves.
    circuit_breaker:
        Optional :class:`CircuitBreaker` wrapping the raw SDK call. Matches
        the Kling/Runway adapter pattern so Phase 5 breakers apply uniformly.
    output_dir:
        Directory for generated PNG files. Created on first write.
    """

    DEFAULT_MODEL = "nano-banana-pro-preview"
    DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
    ) -> None:
        resolved = (
            api_key
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        if not resolved:
            raise ValueError(
                "NanoBananaAdapter: GOOGLE_API_KEY 미설정 — 대표님 .env 확인 필요"
            )
        self._api_key = resolved
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_scene(
        self,
        prompt: str,
        output_path: Path | None = None,
        model: str | None = None,
    ) -> Path:
        """Generate one scene image and persist it as PNG.

        Returns the output path. If the first SDK call raises an exception
        whose message contains ``SAFETY`` / ``BLOCK`` / ``PROHIBITED``
        (case-insensitive), the prompt is softened and retried exactly once.
        Any other exception propagates unchanged (no silent-except).
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out = (
            Path(output_path)
            if output_path
            else self.output_dir / f"scene_{int(time.time())}.png"
        )
        out.parent.mkdir(parents=True, exist_ok=True)

        target_model = model or self.DEFAULT_MODEL

        try:
            self._invoke_and_save(prompt, target_model, out)
            return out
        except Exception as err:  # noqa: BLE001 — classify then re-raise
            upper = str(err).upper()
            is_safety = any(kw in upper for kw in _SAFETY_KEYWORDS)
            if not is_safety:
                # Non-safety error — propagate unchanged (no silent-except).
                raise
            logger.warning(
                "[nanobanana] safety fallback 발동 — 프롬프트 softening 후 "
                "재시도 (대표님): %s",
                err,
            )
            softer = self._soften(prompt)
            try:
                self._invoke_and_save(softer, target_model, out)
                return out
            except Exception as retry_err:
                raise RuntimeError(
                    f"Nano Banana safety retry 실패 (대표님): {retry_err}"
                ) from retry_err

    # ------------------------------------------------------------------
    # Internals — test-mockable seams
    # ------------------------------------------------------------------

    def _invoke_and_save(self, prompt: str, model: str, out: Path) -> None:
        """Call the SDK and save the first image part to ``out``.

        Uses module-level ``genai`` symbol so unit tests can monkeypatch
        ``nb_mod.genai`` with a MagicMock. Accesses ``genai.types`` via
        attribute path (not a separate import) so the same monkeypatch
        transparently stubs :class:`GenerateContentConfig`.
        """
        if genai is None:
            raise RuntimeError(
                "Nano Banana SDK (google-genai) 미설치 — "
                "`pip install google-genai` 필요 (대표님)"
            )

        client = genai.Client(api_key=self._api_key)

        def _call():
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

        response = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        self._save_first_image(response, out)

    @staticmethod
    def _save_first_image(response, out: Path) -> None:
        """Walk ``candidates[0].content.parts`` and write first image bytes."""
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            raise RuntimeError(
                "Nano Banana 응답에 candidate 없음 (대표님 응답 확인 필요)"
            )
        parts = getattr(candidates[0].content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None) if inline else None
            if data:
                out.write_bytes(data)
                return
        raise RuntimeError(
            "Nano Banana 응답에 이미지 part 없음 (대표님 응답 확인 필요)"
        )

    @staticmethod
    def _soften(prompt: str) -> str:
        """Prepend SFW prefix and neutralise blocked tokens."""
        softened = _SOFTEN_PATTERN.sub("cinematic", prompt)
        return "Family-friendly, non-violent, SFW reimagining: " + softened


__all__ = ["NanoBananaAdapter", "DEFAULT_OUTPUT_DIR"]
