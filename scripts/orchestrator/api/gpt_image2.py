"""GPT-Image-2 ("ducktape") image adapter — Stage 2 primary (2026-04-22 확정).

Generates scene anchor images / thumbnails via OpenAI's ``gpt-image-2`` model
(released 2026-04-21 as "ChatGPT Images 2.0"). Signature mirrors
:class:`NanoBananaAdapter` so Phase 5 orchestrator can swap providers without
reshaping the return value (REQ-IMG2-01 drop-in compatibility).

결정 근거: ``project_image_stack_gpt_image2`` 메모리 — 2026-04-22 실측 판정.
I2V 특성상 anchor 퀄리티가 영상 퀄리티 상한을 결정하며, gpt-image-2 의
photorealism 이 Nano Banana 를 압도함이 Kling 2.6 Pro I2V 비교로 검증됨.

API key resolution order:
    constructor ``api_key`` -> ``$OPENAI_API_KEY`` -> ValueError

Costs (2026-04-22 기준, OpenAI API pricing):
    * Low 1024² ≈ $0.006/image
    * Medium 1024² ≈ $0.034/image  (asset-sourcer default)
    * High 1024² ≈ $0.21/image    (thumbnail-designer default)

Two public methods:
    * :meth:`generate_scene` — text-to-image (``images.generate`` endpoint),
      NB-compatible signature for drop-in replacement.
    * :meth:`edit_scene` — image-to-image (``images.edit`` endpoint), uses a
      reference PNG to enforce character consistency.
"""
from __future__ import annotations

import base64
import io
import logging
import os
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

# Module-level import so tests can monkeypatch `gpt_mod.OpenAI` directly.
# Wrapped in try/except so module imports cleanly even if SDK is absent
# (unit tests replace `OpenAI` wholesale).
try:
    from openai import OpenAI  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — test env monkeypatches this symbol
    OpenAI = None  # type: ignore[assignment]

DEFAULT_OUTPUT_DIR = Path("outputs/gpt_image2")

Quality = Literal["low", "medium", "high"]

_SAFETY_KEYWORDS = ("SAFETY", "BLOCK", "PROHIBITED", "CONTENT_POLICY")
_SOFTEN_BLOCKLIST = {"blood", "gore", "violence", "naked", "nude"}
_SOFTEN_PATTERN = re.compile(
    r"\b(" + "|".join(_SOFTEN_BLOCKLIST) + r")\b",
    re.IGNORECASE,
)


class GPTImage2Adapter:
    """Stage 2 primary image generator (OpenAI ``gpt-image-2``).

    Parameters
    ----------
    api_key:
        Explicit API key. If omitted, falls back to ``$OPENAI_API_KEY``.
        Raises ``ValueError`` (Korean message) if none resolves.
    circuit_breaker:
        Optional :class:`CircuitBreaker` wrapping the raw SDK call. Matches
        the Nano Banana adapter pattern so Phase 5 breakers apply uniformly.
    output_dir:
        Directory for generated PNG files. Created on first write.
    """

    DEFAULT_MODEL = "gpt-image-2"
    DEFAULT_QUALITY: Quality = "medium"
    DEFAULT_SIZE = "1024x1024"
    DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
    ) -> None:
        resolved = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved:
            raise ValueError(
                "GPTImage2Adapter: OPENAI_API_KEY 미설정 — 대표님 .env 확인 필요"
            )
        self._api_key = resolved
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API — text-to-image (NanoBananaAdapter drop-in compatible)
    # ------------------------------------------------------------------

    def generate_scene(
        self,
        prompt: str,
        output_path: Path | None = None,
        model: str | None = None,
        quality: Quality | None = None,
    ) -> Path:
        """Generate one scene image from ``prompt`` and persist as PNG.

        Mirrors :meth:`NanoBananaAdapter.generate_scene` signature for
        drop-in replacement. Returns the output path. If the first SDK call
        raises an exception whose message contains ``SAFETY`` / ``BLOCK`` /
        ``PROHIBITED`` / ``CONTENT_POLICY`` (case-insensitive), the prompt
        is softened and retried exactly once. Any other exception propagates
        unchanged (no silent-except, per CLAUDE.md 금기 #3).
        """
        out = self._resolve_out_path(output_path)
        target_model = model or self.DEFAULT_MODEL
        target_quality: Quality = quality or self.DEFAULT_QUALITY

        try:
            self._generate_and_save(prompt, target_model, target_quality, out)
            return out
        except Exception as err:  # noqa: BLE001 — classify then re-raise
            if not self._is_safety_error(err):
                raise
            logger.warning(
                "[gpt-image-2] safety fallback 발동 — 프롬프트 softening 후 "
                "재시도 (대표님): %s",
                err,
            )
            softer = self._soften(prompt)
            try:
                self._generate_and_save(softer, target_model, target_quality, out)
                return out
            except Exception as retry_err:
                raise RuntimeError(
                    f"gpt-image-2 safety retry 실패 (대표님): {retry_err}"
                ) from retry_err

    # ------------------------------------------------------------------
    # Public API — image-to-image with reference (character consistency)
    # ------------------------------------------------------------------

    def edit_scene(
        self,
        prompt: str,
        reference_image: Path,
        output_path: Path | None = None,
        model: str | None = None,
        quality: Quality | None = None,
    ) -> Path:
        """Generate scene image bound to ``reference_image`` for character
        consistency. Uses OpenAI ``images.edit`` endpoint.

        Same safety-retry semantics as :meth:`generate_scene`.
        """
        if not reference_image.exists():
            raise FileNotFoundError(
                f"GPTImage2Adapter: reference_image 없음 (대표님): {reference_image}"
            )

        out = self._resolve_out_path(output_path)
        target_model = model or self.DEFAULT_MODEL
        target_quality: Quality = quality or self.DEFAULT_QUALITY
        reference_bytes = reference_image.read_bytes()

        try:
            self._edit_and_save(
                prompt, reference_bytes, target_model, target_quality, out
            )
            return out
        except Exception as err:  # noqa: BLE001 — classify then re-raise
            if not self._is_safety_error(err):
                raise
            logger.warning(
                "[gpt-image-2] edit safety fallback — 프롬프트 softening (대표님): %s",
                err,
            )
            softer = self._soften(prompt)
            try:
                self._edit_and_save(
                    softer, reference_bytes, target_model, target_quality, out
                )
                return out
            except Exception as retry_err:
                raise RuntimeError(
                    f"gpt-image-2 edit safety retry 실패 (대표님): {retry_err}"
                ) from retry_err

    # ------------------------------------------------------------------
    # Internals — test-mockable seams
    # ------------------------------------------------------------------

    def _resolve_out_path(self, output_path: Path | None) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out = (
            Path(output_path)
            if output_path
            else self.output_dir / f"scene_{int(time.time())}.png"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        return out

    def _generate_and_save(
        self, prompt: str, model: str, quality: Quality, out: Path
    ) -> None:
        """Call images.generate and save the first image part to ``out``."""
        if OpenAI is None:
            raise RuntimeError(
                "gpt-image-2 SDK (openai) 미설치 — "
                "`pip install openai` 필요 (대표님)"
            )
        client = OpenAI(api_key=self._api_key)

        def _call():
            return client.images.generate(
                model=model,
                prompt=prompt,
                size=self.DEFAULT_SIZE,
                quality=quality,
                n=1,
            )

        response = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        self._save_first_image(response, out)

    def _edit_and_save(
        self,
        prompt: str,
        reference_bytes: bytes,
        model: str,
        quality: Quality,
        out: Path,
    ) -> None:
        """Call images.edit with reference and save first image part."""
        if OpenAI is None:
            raise RuntimeError(
                "gpt-image-2 SDK (openai) 미설치 — "
                "`pip install openai` 필요 (대표님)"
            )
        client = OpenAI(api_key=self._api_key)

        def _call():
            return client.images.edit(
                model=model,
                image=("reference.png", io.BytesIO(reference_bytes), "image/png"),
                prompt=prompt,
                size=self.DEFAULT_SIZE,
                quality=quality,
                n=1,
            )

        response = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        self._save_first_image(response, out)

    @staticmethod
    def _save_first_image(response, out: Path) -> None:
        """Decode ``response.data[0].b64_json`` and write PNG bytes."""
        data = getattr(response, "data", None) or []
        if not data:
            raise RuntimeError(
                "gpt-image-2 응답에 data 없음 (대표님 응답 확인 필요)"
            )
        b64 = getattr(data[0], "b64_json", None)
        if not b64:
            raise RuntimeError(
                "gpt-image-2 응답에 b64_json 없음 (대표님 응답 확인 필요)"
            )
        out.write_bytes(base64.b64decode(b64))

    @staticmethod
    def _is_safety_error(err: Exception) -> bool:
        upper = str(err).upper()
        return any(kw in upper for kw in _SAFETY_KEYWORDS)

    @staticmethod
    def _soften(prompt: str) -> str:
        """Prepend SFW prefix and neutralise blocked tokens."""
        softened = _SOFTEN_PATTERN.sub("cinematic", prompt)
        return "Family-friendly, non-violent, SFW reimagining: " + softened


__all__ = ["GPTImage2Adapter", "DEFAULT_OUTPUT_DIR", "Quality"]
