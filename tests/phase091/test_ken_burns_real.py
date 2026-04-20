"""RED (conditional) smoke test for REQ-091-04 — real ffmpeg Ken-Burns.

Skipped if ffmpeg is not on PATH. Wave 1 Plan 03 must make this pass when ffmpeg
is installed (FFmpeg 8.0.1-full_build verified on dev machine per Research §3).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg binary missing from PATH")
def test_real_ffmpeg_produces_mp4(tmp_path: Path, fixture_png_bytes: bytes) -> None:
    """REQ-091-04: real ffmpeg produces a non-trivial .mp4 from a 1x1 PNG."""
    from scripts.orchestrator.api.ken_burns import KenBurnsLocalAdapter

    img = tmp_path / "input.png"
    img.write_bytes(fixture_png_bytes)
    adapter = KenBurnsLocalAdapter(output_dir=tmp_path)
    out = adapter.generate_clip(img, duration_seconds=2)
    assert out.exists()
    assert out.stat().st_size > 1024
