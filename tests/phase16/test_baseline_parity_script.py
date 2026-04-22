"""Phase 16-04 W1-PARITY-SCRIPT — verify_baseline_parity.py unit tests.

ffprobe subprocess 는 mock 으로 대체 (CI 에서 ffmpeg 없을 수 있음).
compare_to_baselines() 논리 직접 검증.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.validate.verify_baseline_parity import (
    MIN_AUDIO_SAMPLE_RATE,
    MIN_DURATION_S,
    MIN_VIDEO_BITRATE_KBPS,
    REQUIRED_AUDIO_CHANNELS,
    TARGET_H,
    TARGET_W,
    VideoMeta,
    compare_to_baselines,
    within,
)


def _make_meta(
    *,
    width: int = TARGET_W,
    height: int = TARGET_H,
    duration_s: float = 75.0,
    codec: str = "h264",
    fps: float = 30.0,
    bitrate_kbps: int = 8000,
    audio_channels: int = 2,
    audio_sample_rate: int = 48000,
    subtitle_tracks: int = 1,
) -> VideoMeta:
    return VideoMeta(
        path="our.mp4",
        width=width,
        height=height,
        duration_s=duration_s,
        codec=codec,
        fps=fps,
        bitrate_kbps=bitrate_kbps,
        file_size_mb=5.0,
        subtitle_tracks=subtitle_tracks,
        audio_channels=audio_channels,
        audio_sample_rate=audio_sample_rate,
    )


def test_within_tolerance_helper() -> None:
    """within() ±10% 판정."""
    assert within(100, 100)
    assert within(109, 100)
    assert not within(111, 100)
    assert within(0, 0)
    assert not within(1, 0)


def test_all_pass_path() -> None:
    """정상 케이스 — resolution/duration/codec/audio/bitrate 전수 통과."""
    ours = _make_meta()
    baselines = [
        _make_meta(bitrate_kbps=8000, fps=30.0),
        _make_meta(bitrate_kbps=7500, fps=30.0),
    ]
    report = compare_to_baselines(ours, baselines)
    assert report["summary"]["all_pass"] is True
    assert report["summary"]["fail_count"] == 0


def test_fail_resolution() -> None:
    """720x1280 해상도 → resolution FAIL."""
    ours = _make_meta(width=720, height=1280)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["resolution"]["pass"] is False
    assert report["summary"]["all_pass"] is False


def test_fail_duration_too_short() -> None:
    """duration=30s (< MIN_DURATION_S=60.0) → duration FAIL."""
    ours = _make_meta(duration_s=30.0)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["duration"]["pass"] is False
    # Also verify threshold absolute value
    assert report["criteria"]["duration"]["target_min"] == MIN_DURATION_S


def test_fail_duration_too_long() -> None:
    """duration=200s → duration FAIL."""
    ours = _make_meta(duration_s=200.0)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["duration"]["pass"] is False


def test_fail_mono_audio() -> None:
    """audio_channels=1 (mono) → audio_channels FAIL (SC#5 stereo required)."""
    ours = _make_meta(audio_channels=1)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["audio_channels"]["pass"] is False
    assert report["criteria"]["audio_channels"]["expected"] == REQUIRED_AUDIO_CHANNELS


def test_fail_low_sample_rate() -> None:
    """audio_sample_rate=22050 < 44100 → FAIL."""
    ours = _make_meta(audio_sample_rate=22050)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["audio_sample_rate"]["pass"] is False
    assert report["criteria"]["audio_sample_rate"]["expected_min"] == MIN_AUDIO_SAMPLE_RATE


def test_fail_session32_shock_bitrate() -> None:
    """519 kbps (session #32 shock 재현) → min_video_bitrate FAIL."""
    ours = _make_meta(bitrate_kbps=519)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["min_video_bitrate"]["pass"] is False
    assert report["criteria"]["min_video_bitrate"]["threshold_kbps"] == MIN_VIDEO_BITRATE_KBPS


def test_fail_no_subtitle() -> None:
    """subtitle_tracks=0 → subtitle_track_present FAIL."""
    ours = _make_meta(subtitle_tracks=0)
    report = compare_to_baselines(ours, [])
    assert report["criteria"]["subtitle_track_present"]["pass"] is False


def test_baseline_relative_bitrate_tolerance() -> None:
    """ours=8800, baseline avg=8000 → within 10% PASS."""
    ours = _make_meta(bitrate_kbps=8800)
    baselines = [_make_meta(bitrate_kbps=8000), _make_meta(bitrate_kbps=8000)]
    report = compare_to_baselines(ours, baselines)
    assert report["criteria"]["bitrate_vs_baseline"]["pass"] is True


def test_baseline_relative_bitrate_out_of_tolerance() -> None:
    """ours=16000, baseline avg=8000 → out of 10% FAIL (but absolute pass so bitrate_vs_baseline alone FAIL)."""
    ours = _make_meta(bitrate_kbps=16000)
    baselines = [_make_meta(bitrate_kbps=8000), _make_meta(bitrate_kbps=8000)]
    report = compare_to_baselines(ours, baselines)
    assert report["criteria"]["bitrate_vs_baseline"]["pass"] is False


def test_report_structure_has_expected_keys() -> None:
    """report 딕셔너리 구조 안정성."""
    ours = _make_meta()
    report = compare_to_baselines(ours, [])
    assert "ours" in report
    assert "baselines" in report
    assert "criteria" in report
    assert "summary" in report
    expected_abs_keys = {
        "resolution",
        "duration",
        "codec",
        "audio_channels",
        "audio_sample_rate",
        "min_video_bitrate",
        "subtitle_track_present",
    }
    assert expected_abs_keys.issubset(set(report["criteria"].keys()))


def test_cli_nonexistent_our_mp4_exit1() -> None:
    """--our-mp4 /nonexistent.mp4 --dry-run → exit 1."""
    from scripts.validate.verify_baseline_parity import main

    rc = main(["--our-mp4", "/nonexistent.mp4", "--dry-run"])
    assert rc == 1
