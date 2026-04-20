"""Local FFmpeg Ken-Burns clip generator (REQ-091-04, Phase 9.1).

Replaces the network-bound ``ShotstackAdapter.create_ken_burns_clip`` call
with an offline ``ffmpeg`` subprocess so the ORCH-12 fallback shot path
runs without API dependency, cost, or latency.

D-10 / D-11 (09.1-CONTEXT.md):
    * ``subprocess.run`` ffmpeg — NO ``ffmpeg-python`` binding dependency.
    * ``shutil.which("ffmpeg")`` precondition — ``KenBurnsUnavailable``
      raised at construction time if missing.
    * ``ShotstackAdapter.create_ken_burns_clip`` kept as deprecated
      (Plan 03 Task 2 attaches ``warnings.warn(DeprecationWarning)``).

Pitfall 3 (09.1-RESEARCH.md §Pitfalls):
    ``zoompan`` on low-res input produces visible jitter. The filter
    chain MUST prepend ``scale=4000:-1,`` before ``zoompan=``. The
    ``test_cmd_construction_includes_scale_and_zoompan`` Wave 0 RED test
    pins this invariant.

Korean-first errors (나베랄 감마 tone):
    * ``KenBurnsUnavailable`` — "ffmpeg 바이너리를 찾을 수 없습니다 …"
    * ``FileNotFoundError`` — "입력 이미지 없음: … (대표님)"
    * ``RuntimeError``      — "ffmpeg 실패 (rc=…): …"
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("outputs/ken_burns")
DEFAULT_SUBPROCESS_TIMEOUT_S = 120


class KenBurnsUnavailable(RuntimeError):
    """Raised when ffmpeg binary is not on PATH at adapter construction time."""


class KenBurnsLocalAdapter:
    """Local ffmpeg pan/zoom Ken-Burns clip adapter.

    Parameters
    ----------
    circuit_breaker:
        Optional Phase 5 :class:`CircuitBreaker`. When supplied, the
        ``ffmpeg`` subprocess invocation is wrapped via
        ``circuit_breaker.call(...)`` so consecutive failures (e.g.
        codec errors) trip the breaker exactly like the network
        adapters (Kling / Runway / Shotstack).
    output_dir:
        Directory where the generated ``.mp4`` is written. Defaults to
        ``outputs/ken_burns`` (created on demand with
        ``mkdir(parents=True, exist_ok=True)``).
    """

    DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR

    def __init__(
        self,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
    ) -> None:
        if shutil.which("ffmpeg") is None:
            raise KenBurnsUnavailable(
                "ffmpeg 바이너리를 찾을 수 없습니다 — 대표님 PATH 확인 필요"
            )
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_clip(
        self,
        image: Path,
        duration_seconds: int = 5,
        resolution: tuple[int, int] = (720, 1280),
        fps: int = 30,
        zoom_rate: float = 0.0015,
    ) -> Path:
        """Render a Ken-Burns pan/zoom clip from a still ``image``.

        Returns the :class:`Path` of the generated ``.mp4`` under
        :attr:`output_dir` (``kb_<ms>.mp4`` — millisecond suffix avoids
        same-second collisions in unit tests).
        """

        image = Path(image)
        if not image.exists():
            raise FileNotFoundError(f"입력 이미지 없음: {image} (대표님)")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        out = self.output_dir / f"kb_{int(time.time() * 1000)}.mp4"

        cmd = self._build_command(
            image=image,
            output_path=out,
            duration_seconds=duration_seconds,
            resolution=resolution,
            fps=fps,
            zoom_rate=zoom_rate,
        )

        def _run() -> "subprocess.CompletedProcess[str]":
            # ``shell=False`` — Hook 3종 injection safety + RESEARCH Pitfall.
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEFAULT_SUBPROCESS_TIMEOUT_S,
                shell=False,
            )

        result = (
            self.circuit_breaker.call(_run)
            if self.circuit_breaker is not None
            else _run()
        )

        if result.returncode != 0:
            tail = (result.stderr or "")[-500:]
            raise RuntimeError(
                f"ffmpeg 실패 (rc={result.returncode}): {tail}"
            )

        logger.info(
            "KenBurnsLocalAdapter rendered clip: %s (duration=%ss, res=%sx%s)",
            out,
            duration_seconds,
            resolution[0],
            resolution[1],
        )
        return out

    # ------------------------------------------------------------------
    # Internal helpers (pure — unit-testable without subprocess)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_command(
        image: Path,
        output_path: Path,
        duration_seconds: int,
        resolution: tuple[int, int],
        fps: int,
        zoom_rate: float,
    ) -> list[str]:
        """Build the ffmpeg command list (pure — no side effects).

        Filter chain per 09.1-RESEARCH §3 (Bannerbear/Creatomate verified):
            ``scale=4000:-1,zoompan=z='min(zoom+{zoom_rate},1.5)':
             x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d={frames}:s={w}x{h}:fps={fps}``

        Pitfall 3 defence: ``scale=4000:-1`` MUST be the first filter —
        zoompan on low-res input without upscaling produces visible
        frame-to-frame jitter.
        """

        frames = duration_seconds * fps
        w, h = resolution
        filter_str = (
            f"scale=4000:-1,zoompan="
            f"z='min(zoom+{zoom_rate},1.5)':"
            f"x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):"
            f"d={frames}:s={w}x{h}:fps={fps}"
        )
        return [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", str(duration_seconds),
            str(output_path),
        ]


__all__ = [
    "KenBurnsLocalAdapter",
    "KenBurnsUnavailable",
    "DEFAULT_OUTPUT_DIR",
]
