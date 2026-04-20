"""Veo 3.1 Fast image-to-video adapter (fallback for Kling 2.6 Pro).

2026-04-20 세션 #24 final: **Fallback I2V = Veo 3.1 Fast** (fal.ai
``veo3.1/fast/image-to-video``). 정밀/세세한 motion (예: 얼굴 micro-expression,
손가락 articulation, 머리카락 simulation) 에서 Kling 2.6 Pro 가 실패할 때
자동 전환.

대표님 지시 (세션 #24): "정밀하고 세세한걸 만들때는 kling이 실패하면
veo 3.1로하면된다". Memory: ``project_video_stack_runway_gen4_5`` §Stack Final.

비용: $0.10/s (no audio, 720p/1080p) = **$0.50/5s clip**.
Latency: 미실측, 60-120s 추정 (2026-04 fal.ai).

**Physical absence of T2V** (D-13 / VIDEO-01): 이 class 는 ``image_to_video``
단 하나의 public 생성 메서드만 보유. text-only 분기 절대 금지.

API key resolution: 생성자 ``api_key`` -> ``$VEO_API_KEY`` -> ``$FAL_KEY``
(fal.ai 공식 env var; Kling adapter 와 동일 경로 재사용).
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
# Module constants (2026-04 fal.ai Veo 3.1 Fast)
# ---------------------------------------------------------------------------

FAL_ENDPOINT = "fal-ai/veo3.1/fast/image-to-video"

# Veo 3.1 는 Runway 와 달리 negative_prompt 지원 불명확. 일단 미주입
# (research: 2026-04 runway_i2v_prompt_engineering 문서에서 negative prompt
# 역효과 경고. Veo 계열도 동일 주의).

DEFAULT_TIMEOUT_S = 300
DEFAULT_OUTPUT_DIR = Path("outputs/veo")


class VeoI2VAdapter:
    """Fallback image-to-video provider (Google Veo 3.1 Fast via fal.ai).

    Parameters mirror :class:`KlingI2VAdapter` so shorts_pipeline can swap
    them 1:1 in the failover path::

        try:
            clip = kling.image_to_video(prompt, anchor, duration)
        except (CircuitOpen, RuntimeError):
            clip = veo.image_to_video(prompt, anchor, duration)

    Used when Kling 2.6 Pro 의 motion quality 가 부족한 케이스 (대표님
    "정밀하고 세세한" 요구). Phase 10 운영 중 실패 패턴 수집 후 auto-route
    조건 정식 확정.
    """

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
    ) -> None:
        resolved = (
            api_key
            or os.environ.get("VEO_API_KEY")
            or os.environ.get("FAL_KEY")
        )
        if not resolved:
            raise ValueError(
                "VeoI2VAdapter: API key 미설정 — VEO_API_KEY 또는 FAL_KEY "
                "환경 변수 설정 필요 (대표님)."
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

        Mirrors :meth:`KlingI2VAdapter.image_to_video` signature so the two
        adapters remain drop-in swappable in the Kling→Veo failover path.
        """

        if anchor_frame is None:
            raise T2VForbidden(
                "D-13: anchor_frame REQUIRED; text-only generation is "
                "physically forbidden (VIDEO-01). Veo adapter mirrors Kling "
                "constraint."
            )
        if not isinstance(anchor_frame, Path):
            anchor_frame = Path(anchor_frame)

        req = I2VRequest(
            prompt=prompt,
            anchor_frame=anchor_frame,
            duration_seconds=duration_seconds,
        )

        payload: dict[str, Any] = {
            "image_url": req.anchor_frame.as_posix(),
            "prompt": req.prompt,
            "duration": str(req.duration_seconds),
            # Veo 3.1 Fast: 720p default, no audio per 대표님 스택 (ElevenLabs
            # 별도 경로). aspect_ratio 는 anchor 종횡비 자동 사용.
        }

        return self._submit_and_poll(payload)

    # ------------------------------------------------------------------
    # Internals — test-mockable seam
    # ------------------------------------------------------------------

    def _submit_and_poll(self, payload: dict[str, Any]) -> Path:
        """Submit payload to fal.ai, poll to completion, download MP4.

        ``fal_client`` lazy import — matches KlingI2VAdapter pattern.
        """

        import fal_client

        previous = os.environ.get("FAL_KEY")
        os.environ["FAL_KEY"] = self._api_key
        try:
            image_path = Path(payload["image_url"])
            if image_path.exists():
                payload["image_url"] = fal_client.upload_file(str(image_path))

            handler = fal_client.submit(FAL_ENDPOINT, arguments=payload)
            result = handler.get()
        finally:
            if previous is None:
                os.environ.pop("FAL_KEY", None)
            else:
                os.environ["FAL_KEY"] = previous

        video_url = (result.get("video", {}) or {}).get("url") or result.get("url")
        if not video_url:
            raise RuntimeError(
                f"VeoI2VAdapter: fal.ai result 에 video URL 없음 (대표님): {result!r}"
            )

        return self._download_result(video_url)

    def _download_result(self, video_url: str) -> Path:
        """Download video_url into self.output_dir and return the path."""

        import httpx

        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = self.output_dir / f"veo_{ts}.mp4"

        with httpx.stream("GET", video_url, timeout=DEFAULT_TIMEOUT_S) as resp:
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)

        return out_path


# Physical T2V guard — same pattern as kling_i2v.py.
# 이 모듈에 image_to_video 만 존재하고 text_to_video/t2v 는 절대 정의되지 않음을
# 테스트 모듈 + pre_tool_use.py deprecated_patterns.json 이 3중 검증.
assert not hasattr(VeoI2VAdapter, "text_to_video"), (
    "VIDEO-01 위반: VeoI2VAdapter 에 text_to_video 가 정의됨. "
    "D-13 anchor_frame 필수 규율 위반."
)
