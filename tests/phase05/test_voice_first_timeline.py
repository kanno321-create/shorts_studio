"""Phase 5 Plan 05 — VoiceFirstTimeline.align() contract tests.

Covers:
    - ORCH-10: audio-first ordering, integrated render forbidden (D-10)
    - VIDEO-02: 4~8s clip duration bounds + [0.8, 1.25] speed band
    - Error surface: TimelineMismatch, InvalidClipDuration, ClipDurationMismatch,
      IntegratedRenderForbidden
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestrator.voice_first_timeline import (
    AudioSegment,
    ClipDurationMismatch,
    IntegratedRenderForbidden,
    InvalidClipDuration,
    TimelineEntry,
    TimelineMismatch,
    VideoCut,
    VoiceFirstTimeline,
)


# ---------------------------------------------------------------------------
# Helpers — keep test bodies focused on the contract, not boilerplate
# ---------------------------------------------------------------------------


def _aud(idx: int, dur: float) -> AudioSegment:
    """AudioSegment with contiguous placement: start=idx*dur, end=(idx+1)*dur."""
    return AudioSegment(
        index=idx,
        start=idx * dur,
        end=(idx + 1) * dur,
        duration=dur,
        path=Path(f"a{idx}.mp3"),
    )


def _vid(idx: int, dur: float) -> VideoCut:
    return VideoCut(
        index=idx,
        path=Path(f"v{idx}.mp4"),
        duration=dur,
        prompt="p",
        anchor_frame=Path(f"anchor{idx}.png"),
    )


# ---------------------------------------------------------------------------
# align() — matched inputs
# ---------------------------------------------------------------------------


def test_align_matched_counts():
    t = VoiceFirstTimeline()
    res = t.align(
        [_aud(0, 5.0), _aud(1, 5.0), _aud(2, 5.0)],
        [_vid(0, 5.0), _vid(1, 5.0), _vid(2, 5.0)],
    )
    assert len(res) == 3
    assert all(isinstance(e, TimelineEntry) for e in res)
    assert all(e.speed == 1.0 for e in res)


def test_align_preserves_start_end_from_audio():
    t = VoiceFirstTimeline()
    aud = _aud(0, 5.0)
    aud.start = 10.0
    aud.end = 15.0
    res = t.align([aud], [_vid(0, 5.0)])
    assert res[0].start == 10.0
    assert res[0].end == 15.0


def test_align_records_audio_and_video_paths():
    t = VoiceFirstTimeline()
    res = t.align([_aud(0, 5.0)], [_vid(0, 5.0)])
    assert res[0].audio_path == Path("a0.mp3")
    assert res[0].clip_path == Path("v0.mp4")


# ---------------------------------------------------------------------------
# align() — count mismatch (TimelineMismatch)
# ---------------------------------------------------------------------------


def test_align_count_mismatch_raises_timeline_mismatch():
    t = VoiceFirstTimeline()
    with pytest.raises(TimelineMismatch) as ei:
        t.align([_aud(0, 5.0), _aud(1, 5.0)], [_vid(0, 5.0)])
    assert "audio=2" in str(ei.value)
    assert "video=1" in str(ei.value)


def test_align_empty_audio_vs_one_video_raises():
    t = VoiceFirstTimeline()
    with pytest.raises(TimelineMismatch):
        t.align([], [_vid(0, 5.0)])


# ---------------------------------------------------------------------------
# align() — duration bound violations (InvalidClipDuration)
# ---------------------------------------------------------------------------


def test_align_audio_too_short_raises_invalid_clip_duration():
    t = VoiceFirstTimeline()
    with pytest.raises(InvalidClipDuration) as ei:
        t.align([_aud(0, 3.5)], [_vid(0, 3.5)])
    msg = str(ei.value)
    assert "3.5" in msg
    assert "segment 0" in msg


def test_align_audio_too_long_raises_invalid_clip_duration():
    t = VoiceFirstTimeline()
    with pytest.raises(InvalidClipDuration):
        t.align([_aud(0, 8.1)], [_vid(0, 8.1)])


def test_align_duration_4_0_passes():
    t = VoiceFirstTimeline()
    # Lower bound inclusive — must not raise.
    res = t.align([_aud(0, 4.0)], [_vid(0, 4.0)])
    assert len(res) == 1


def test_align_duration_8_0_passes():
    t = VoiceFirstTimeline()
    # Upper bound inclusive — must not raise.
    res = t.align([_aud(0, 8.0)], [_vid(0, 8.0)])
    assert len(res) == 1


# ---------------------------------------------------------------------------
# align() — speed band (ClipDurationMismatch)
# ---------------------------------------------------------------------------


def test_align_speed_too_fast_raises_clip_duration_mismatch():
    t = VoiceFirstTimeline()
    # audio 5.0 / video 3.0 -> speed 1.67 (> MAX_SPEED=1.25)
    with pytest.raises(ClipDurationMismatch) as ei:
        t.align([_aud(0, 5.0)], [_vid(0, 3.0)])
    msg = str(ei.value)
    assert "1.67" in msg or "1.6" in msg


def test_align_speed_too_slow_raises_clip_duration_mismatch():
    t = VoiceFirstTimeline()
    # audio 4.0 / video 6.0 -> speed 0.67 (< MIN_SPEED=0.8)
    with pytest.raises(ClipDurationMismatch):
        t.align([_aud(0, 4.0)], [_vid(0, 6.0)])


def test_align_speed_at_min_boundary_passes():
    t = VoiceFirstTimeline()
    # audio 4.0 / video 5.0 -> speed exactly 0.8
    res = t.align([_aud(0, 4.0)], [_vid(0, 5.0)])
    assert res[0].speed == pytest.approx(0.8)


def test_align_speed_at_max_boundary_passes():
    t = VoiceFirstTimeline()
    # audio 5.0 / video 4.0 -> speed exactly 1.25
    res = t.align([_aud(0, 5.0)], [_vid(0, 4.0)])
    assert res[0].speed == pytest.approx(1.25)


def test_align_zero_video_duration_raises_clip_duration_mismatch():
    t = VoiceFirstTimeline()
    # Video duration must be > 0 (would otherwise ZeroDivisionError).
    with pytest.raises(ClipDurationMismatch):
        t.align([_aud(0, 5.0)], [_vid(0, 0.0)])


# ---------------------------------------------------------------------------
# integrated_render() — D-10 structural guard
# ---------------------------------------------------------------------------


def test_integrated_render_forbidden():
    t = VoiceFirstTimeline()
    with pytest.raises(IntegratedRenderForbidden) as ei:
        t.integrated_render()
    assert "D-10" in str(ei.value)


def test_integrated_render_forbidden_ignores_args():
    t = VoiceFirstTimeline()
    # The guard must fire regardless of what the caller passes.
    with pytest.raises(IntegratedRenderForbidden):
        t.integrated_render(audio="x.mp3", video="y.mp4", simultaneous=True)


# ---------------------------------------------------------------------------
# Error message invariants — the error messages must reference invariants
# so a developer reading a stack trace can find the relevant rule fast.
# ---------------------------------------------------------------------------


def test_error_messages_reference_invariants():
    t = VoiceFirstTimeline()

    try:
        t.align([_aud(0, 5.0), _aud(1, 5.0)], [_vid(0, 5.0)])
    except TimelineMismatch as e:
        assert "audio=" in str(e) and "video=" in str(e)
    else:  # pragma: no cover — expected to raise
        pytest.fail("TimelineMismatch not raised")

    try:
        t.align([_aud(0, 3.5)], [_vid(0, 3.5)])
    except InvalidClipDuration as e:
        assert "segment" in str(e).lower()
    else:  # pragma: no cover — expected to raise
        pytest.fail("InvalidClipDuration not raised")


# ---------------------------------------------------------------------------
# Fixture interoperability — confirm the shared mock_audio_timestamps loads
# so downstream Plan 06/07 tests can rely on it.
# ---------------------------------------------------------------------------


def test_fixture_mock_audio_timestamps_loads(mock_audio_timestamps):
    assert "words" in mock_audio_timestamps
    assert mock_audio_timestamps["language"] == "ko"
    assert mock_audio_timestamps["total_duration_seconds"] > 0
