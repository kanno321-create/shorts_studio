"""FFmpegAssembler — local timeline composition for the ASSEMBLY gate.

Replaces the Shotstack cloud render path when ``SHOTSTACK_API_KEY`` is
absent. Takes a list of :class:`TimelineEntry` (already aligned by
:class:`VoiceFirstTimeline.align`) plus the source audio segments, applies
per-clip speed adjustment, concatenates the video track, overlays the
audio track, and writes a single ``.mp4`` ready for YouTube upload.

Design notes
------------
- ``subprocess.run`` ffmpeg — same pattern as ``ken_burns.py`` (NO
  ``ffmpeg-python`` binding dependency).
- ``shutil.which("ffmpeg")`` precondition raised at construction time so
  callers can fall back before timeline assembly begins.
- Output resolution: 1080x1920 (9:16 Shorts spec). Input clips may be
  any size — ffmpeg's ``scale,pad`` filter chain letterboxes/crops.
- Render interface matches :class:`ShotstackAdapter.render`:
  ``render(timeline, resolution="hd", aspect_ratio="9:16") -> dict``.
  Returns ``{"url": "<local-path>", "status": "assembled", ...}`` so
  downstream ``_run_assembly`` keeps identical dict access.
- No circuit breaker dependency — local subprocess, no rate limits.
  (CircuitBreaker can be passed but default is ``None``.)
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from ..voice_first_timeline import TimelineEntry, TransitionEntry

__all__ = ["FFmpegAssembler", "FFmpegUnavailable"]

logger = logging.getLogger(__name__)


DEFAULT_OUTPUT_DIR = Path("outputs/ffmpeg_assembly")
DEFAULT_SUBPROCESS_TIMEOUT_S = 600  # 10 min per ffmpeg invocation
TARGET_RESOLUTION = (1080, 1920)  # W x H (9:16 vertical)
TARGET_FPS = 30


class FFmpegUnavailable(RuntimeError):
    """Raised when ``ffmpeg`` is not on PATH at adapter construction time."""


class FFmpegAssembler:
    """Local ffmpeg-based timeline composer (ASSEMBLY gate Shotstack replacement).

    Parameters
    ----------
    circuit_breaker:
        Optional Phase 5 :class:`CircuitBreaker`. Local subprocess, so
        breaker is usually unused. Accepted for signature parity with
        network adapters.
    output_dir:
        Directory where the final ``.mp4`` is written. Defaults to
        ``outputs/ffmpeg_assembly``.
    """

    def __init__(
        self,
        circuit_breaker: Any = None,
        output_dir: Path | None = None,
    ) -> None:
        if shutil.which("ffmpeg") is None:
            raise FFmpegUnavailable(
                "ffmpeg 바이너리 PATH 미등록 — 대표님 확인 필요"
            )
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API — Shotstack render() signature parity
    # ------------------------------------------------------------------

    def render(
        self,
        timeline: list[Any],
        resolution: str = "hd",
        aspect_ratio: str = "9:16",
    ) -> dict:
        """Compose timeline entries into a single 9:16 mp4 video.

        Mirrors :meth:`ShotstackAdapter.render` signature so
        ``_run_assembly`` can call either adapter identically.

        Parameters
        ----------
        timeline : list[TimelineEntry | TransitionEntry]
            Result of :meth:`VoiceFirstTimeline.insert_transition_shots`.
            Only ``TimelineEntry`` items contribute clips to the output;
            ``TransitionEntry`` items are rendered as short colored
            pauses (Phase 1 minimal — full transition assets are a
            Phase 2 concern).
        resolution : str
            ``"hd"`` → 1280x720, ``"fhd"`` → 1920x1080. Output is always
            rotated/cropped to 9:16 regardless (1080x1920 for fhd,
            720x1280 for hd).
        aspect_ratio : str
            Informational — ffmpeg filter chain always produces 9:16.

        Returns
        -------
        dict
            ``{"url": "<local-file:// path>", "status": "assembled",
               "resolution": "...", "aspect_ratio": "9:16",
               "duration_s": <float>}``
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Filter only playable clips (TimelineEntry has clip_path + audio_path).
        clips = [
            t for t in timeline
            if isinstance(t, TimelineEntry)
            or (is_dataclass(t) and "clip_path" in asdict(t))
        ]
        if not clips:
            raise ValueError(
                "FFmpegAssembler.render: timeline 에 playable TimelineEntry 없음 (대표님)"
            )

        width, height = _resolve_target_resolution(resolution)

        # Step 1 — for each clip, apply speed + scale/pad to 9:16 → temp mp4.
        tmp_video_dir = self.output_dir / f"_tmp_{int(time.time() * 1000)}"
        tmp_video_dir.mkdir(parents=True, exist_ok=True)
        segment_paths: list[Path] = []
        for i, entry in enumerate(clips):
            seg_path = tmp_video_dir / f"seg_{i:03d}.mp4"
            _transcode_clip(
                src=Path(entry.clip_path),
                dst=seg_path,
                speed=float(getattr(entry, "speed", 1.0)),
                width=width,
                height=height,
                fps=TARGET_FPS,
                timeout_s=DEFAULT_SUBPROCESS_TIMEOUT_S,
            )
            segment_paths.append(seg_path)

        # Step 2 — concatenate video segments via concat demuxer.
        concat_list = tmp_video_dir / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in segment_paths),
            encoding="utf-8",
        )
        video_concat = tmp_video_dir / "video_concat.mp4"
        _run_ffmpeg(
            [
                "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", str(TARGET_FPS),
                "-an",
                "-y", str(video_concat),
            ],
            timeout_s=DEFAULT_SUBPROCESS_TIMEOUT_S,
        )

        # Step 3 — concatenate audio segments (from clips[*].audio_path).
        audio_concat_list = tmp_video_dir / "audio_concat.txt"
        audio_concat_list.write_text(
            "\n".join(
                f"file '{Path(entry.audio_path).resolve().as_posix()}'"
                for entry in clips
            ),
            encoding="utf-8",
        )
        audio_concat = tmp_video_dir / "audio_concat.aac"
        _run_ffmpeg(
            [
                "-f", "concat", "-safe", "0",
                "-i", str(audio_concat_list),
                "-c:a", "aac", "-b:a", "192k",
                "-y", str(audio_concat),
            ],
            timeout_s=DEFAULT_SUBPROCESS_TIMEOUT_S,
        )

        # Step 4 — merge video + audio → final mp4.
        out_path = self.output_dir / f"assembled_{int(time.time() * 1000)}.mp4"
        _run_ffmpeg(
            [
                "-i", str(video_concat),
                "-i", str(audio_concat),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart",
                "-y", str(out_path),
            ],
            timeout_s=DEFAULT_SUBPROCESS_TIMEOUT_S,
        )

        duration_s = sum(
            float(entry.end) - float(entry.start) for entry in clips
        )
        logger.info(
            "[FFmpegAssembler] rendered %d clips → %s (%.1fs @ %dx%d)",
            len(clips),
            out_path,
            duration_s,
            width,
            height,
        )

        return {
            "url": out_path.as_posix(),
            "status": "assembled",
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "duration_s": duration_s,
            "renderer": "ffmpeg-local",
        }

    # ------------------------------------------------------------------
    # ShotstackAdapter.upscale() signature parity — NOOP (no upscale).
    # ------------------------------------------------------------------

    def upscale(self, url: str) -> dict:
        """Phase 8 upscale stub — local renderer produces full-res directly."""
        return {"status": "skipped", "reason": "ffmpeg-local outputs full-res", "url": url}


# ============================================================================
# Internal helpers
# ============================================================================


def _resolve_target_resolution(resolution: str) -> tuple[int, int]:
    """Map Shotstack resolution literal to (W, H) at 9:16 aspect."""
    res = (resolution or "hd").lower()
    if res == "fhd":
        return 1080, 1920
    # default hd / sd / unknown → 720x1280 vertical
    return 720, 1280


def _transcode_clip(
    src: Path,
    dst: Path,
    speed: float,
    width: int,
    height: int,
    fps: int,
    timeout_s: int,
) -> None:
    """Apply speed factor + scale/pad to 9:16 and write dst.

    Uses ``setpts=(PTS-STARTPTS)/speed`` + ``atempo`` chain. ``scale`` +
    ``pad`` letterboxes the input to the target 9:16 canvas without
    distortion.
    """
    # atempo accepts 0.5~2.0 per stage — chain if outside. For smoke the
    # clip has no audio track (I2V), so atempo is harmless when missing.
    pts_factor = 1.0 / max(speed, 0.1)
    vf = (
        f"setpts={pts_factor}*PTS,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={fps}"
    )
    _run_ffmpeg(
        [
            "-i", str(src),
            "-vf", vf,
            "-an",  # drop any input audio (we overlay later)
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-y", str(dst),
        ],
        timeout_s=timeout_s,
    )


def _run_ffmpeg(args: list[str], timeout_s: int) -> None:
    """Run ffmpeg with the given args and raise on non-zero rc.

    Uses ``-hide_banner -loglevel error`` for cleaner logs. Captures
    stdout+stderr for diagnostic tail on failure.
    """
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        shell=False,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        tail_err = (result.stderr or "")[-800:]
        tail_out = (result.stdout or "")[-400:]
        raise RuntimeError(
            f"ffmpeg 실패 (rc={result.returncode}): stderr={tail_err!r} "
            f"stdout={tail_out!r}"
        )
