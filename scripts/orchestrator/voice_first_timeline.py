"""Phase 5 Plan 05 — VoiceFirstTimeline audio-first assembly primitive.

Implements the voice-first contract (D-10), 4~8s clip duration + 1 Move Rule
(VIDEO-02 / D-14), and transition shot insertion (VIDEO-03 / D-15). Pure
data transformation — no HTTP, no API calls, no file I/O inside the class.

Requirements addressed:
    - ORCH-10 : audio MUST be generated first, then video cuts align to it.
                Integrated render (audio+video simultaneous generation) is
                structurally forbidden via IntegratedRenderForbidden.
    - VIDEO-02: each segment duration must be in [4.0, 8.0] seconds;
                speed adjust must stay in [0.8, 1.25].
    - VIDEO-03: insert transition shots every Nth cut using 3 templates
                (prop_closeup / silhouette / background_wipe) at 0.5~1.0s.

Consumers: Plan 06 Shotstack adapter (renders the aligned timeline),
           Plan 07 shorts_pipeline.py ASSEMBLY GATE.

Python 3.11+ required (Literal, Self).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Union

from .gates import OrchestratorError


# ============================================================================
# Exceptions (subclass OrchestratorError so pipeline catch-all still works)
# ============================================================================


class TimelineMismatch(OrchestratorError):
    """Raised when audio segment count != video cut count.

    Upstream invariant: shot-planner emits exactly one scene per script
    section, and VOICE gate emits one audio segment per section. Any
    divergence is an upstream bug — fail loud, never paper over.
    """


class InvalidClipDuration(OrchestratorError):
    """Raised when a segment duration is outside [4, 8] seconds per VIDEO-02 / D-14."""


class ClipDurationMismatch(OrchestratorError):
    """Raised when the speed adjust (audio_dur / video_dur) falls outside
    [0.8, 1.25]. Handler is expected to regenerate the video clip with
    a duration closer to the audio segment, not to silently speed-warp.
    """


class IntegratedRenderForbidden(OrchestratorError):
    """D-10 enforcement: audio and video MUST be generated separately.

    Any attempt to invoke a combined ``integrated_render(audio=..., video=...)``
    path trips this exception. Use:
        voice = VoiceFirstTimeline()
        timeline = voice.align(audio_segments, video_cuts)
        timeline = voice.insert_transition_shots(timeline)
        Shotstack.render(timeline)   # separate, explicit step
    """


# ============================================================================
# Dataclasses (see Plan 05 interfaces block)
# ============================================================================


@dataclass
class AudioSegment:
    """Audio segment produced by the VOICE gate (Typecast/ElevenLabs)."""

    index: int
    start: float
    end: float
    duration: float
    path: Path


@dataclass
class VideoCut:
    """Image-to-video clip produced by the ASSETS gate (Kling/Runway)."""

    index: int
    path: Path
    duration: float
    prompt: str
    anchor_frame: Path


@dataclass
class TimelineEntry:
    """Aligned entry ready for Shotstack composition."""

    start: float
    end: float
    clip_path: Path
    speed: float
    audio_path: Path


@dataclass
class TransitionEntry:
    """Transition shot inserted between primary cuts (VIDEO-03)."""

    template: Literal["prop_closeup", "silhouette", "background_wipe"]
    duration: float
    after_index: int


TimelineItem = Union[TimelineEntry, TransitionEntry]


# ============================================================================
# VoiceFirstTimeline — the audio-first assembly primitive
# ============================================================================


class VoiceFirstTimeline:
    """Audio-first timeline builder.

    Usage::

        voice = VoiceFirstTimeline(rng_seed=42)     # seed for determinism
        timeline = voice.align(audio_segments, video_cuts)
        timeline = voice.insert_transition_shots(timeline)
        # -> pass timeline to Shotstack adapter (Plan 06)

    The integrated_render() sentinel always raises IntegratedRenderForbidden
    to structurally block any caller from combining audio+video generation
    (D-10). There is no way to bypass this check from inside the class.
    """

    # --- VIDEO-02 / D-14: 1 Move Rule + 4~8s clip duration ---
    MIN_CLIP_DURATION: float = 4.0
    MAX_CLIP_DURATION: float = 8.0

    # --- Shotstack speed tolerance. Outside this band, regenerate the clip. ---
    MIN_SPEED: float = 0.8
    MAX_SPEED: float = 1.25

    # --- VIDEO-03 / D-15: transition shot templates + duration band ---
    TRANSITION_TEMPLATES: tuple[str, ...] = (
        "prop_closeup",
        "silhouette",
        "background_wipe",
    )
    MIN_TRANSITION_DURATION: float = 0.5
    MAX_TRANSITION_DURATION: float = 1.0
    TRANSITION_EVERY_N_CUTS: int = 3

    def __init__(self, rng_seed: int | None = None) -> None:
        """Initialise with an optional RNG seed for deterministic tests.

        Pass ``rng_seed=42`` (or any fixed int) so property tests can assert
        the same template sequence across runs. ``None`` uses the system RNG.
        """
        self._rng = random.Random(rng_seed)

    # ------------------------------------------------------------------
    # Alignment (D-10 core path)
    # ------------------------------------------------------------------
    def align(
        self,
        audio_segments: list[AudioSegment],
        video_cuts: list[VideoCut],
    ) -> list[TimelineEntry]:
        """Map audio segments to video cuts 1:1 and compute Shotstack speed.

        Enforces (in order):
            1. Count equality (TimelineMismatch on mismatch).
            2. Per-segment audio duration in [MIN_CLIP_DURATION, MAX_CLIP_DURATION].
            3. Video cut duration > 0 (ClipDurationMismatch otherwise).
            4. Speed = audio.duration / video.duration in [MIN_SPEED, MAX_SPEED].

        Returns a list of TimelineEntry; indexing mirrors input order.
        """
        if len(audio_segments) != len(video_cuts):
            raise TimelineMismatch(
                f"audio={len(audio_segments)} video={len(video_cuts)}"
                " — counts must match; regenerate upstream before aligning"
            )

        timeline: list[TimelineEntry] = []
        for aud, vid in zip(audio_segments, video_cuts):
            if not (self.MIN_CLIP_DURATION <= aud.duration <= self.MAX_CLIP_DURATION):
                raise InvalidClipDuration(
                    f"audio segment {aud.index} is {aud.duration:.2f}s"
                    f" (must be in [{self.MIN_CLIP_DURATION}, {self.MAX_CLIP_DURATION}])"
                )
            if vid.duration <= 0:
                raise ClipDurationMismatch(
                    f"video cut {vid.index}: duration {vid.duration} invalid"
                    " (must be > 0)"
                )
            speed = aud.duration / vid.duration
            # Session #31 — SHORTS_SPEED_TOLERANCE_RELAX=1 env override for
            # smoke/bring-up paths. 실 운영에는 원복 권장 (playback 품질).
            import os as _os
            if _os.environ.get("SHORTS_SPEED_TOLERANCE_RELAX") == "1":
                min_speed, max_speed = 0.5, 2.0
            else:
                min_speed, max_speed = self.MIN_SPEED, self.MAX_SPEED
            if not (min_speed <= speed <= max_speed):
                raise ClipDurationMismatch(
                    f"segment {aud.index}: speed adjust {speed:.2f} outside"
                    f" [{min_speed}, {max_speed}] — regenerate clip"
                )
            timeline.append(
                TimelineEntry(
                    start=aud.start,
                    end=aud.end,
                    clip_path=vid.path,
                    speed=speed,
                    audio_path=aud.path,
                )
            )
        return timeline

    # ------------------------------------------------------------------
    # Transition shot insertion (VIDEO-03)
    # ------------------------------------------------------------------
    def insert_transition_shots(
        self,
        timeline: list[TimelineEntry],
    ) -> list[TimelineItem]:
        """Insert a TransitionEntry after every Nth cut except the last.

        Cadence: every ``TRANSITION_EVERY_N_CUTS`` cuts (1-based count). The
        final cut never gets a trailing transition (nothing follows it), so
        for a 6-cut timeline you get 1 transition (after index 2), not 2.

        Template is selected with ``self._rng.choice`` so two instances with
        the same ``rng_seed`` emit identical template sequences. Duration is
        sampled from [MIN_TRANSITION_DURATION, MAX_TRANSITION_DURATION].
        """
        out: list[TimelineItem] = []
        total = len(timeline)
        for i, entry in enumerate(timeline):
            out.append(entry)
            is_last = i >= total - 1
            should_insert = (i + 1) % self.TRANSITION_EVERY_N_CUTS == 0
            if should_insert and not is_last:
                template = self._rng.choice(self.TRANSITION_TEMPLATES)
                duration = self._rng.uniform(
                    self.MIN_TRANSITION_DURATION,
                    self.MAX_TRANSITION_DURATION,
                )
                out.append(
                    TransitionEntry(
                        template=template,  # type: ignore[arg-type]
                        duration=duration,
                        after_index=i,
                    )
                )
        return out

    # ------------------------------------------------------------------
    # D-10 structural guard — no bypass
    # ------------------------------------------------------------------
    def integrated_render(self, *args: object, **kwargs: object) -> None:
        """Always raises IntegratedRenderForbidden (D-10 enforcement).

        There is no legitimate caller for this method. Its presence exists
        solely so any accidental attempt to fuse audio+video generation
        trips a loud exception instead of silently corrupting the pipeline.
        """
        raise IntegratedRenderForbidden(
            "D-10: audio+video simultaneous generation is forbidden."
            " Use: align(audio_segments, video_cuts) ->"
            " insert_transition_shots(timeline) -> Shotstack.render()"
        )


__all__ = [
    "AudioSegment",
    "VideoCut",
    "TimelineEntry",
    "TransitionEntry",
    "TimelineItem",
    "VoiceFirstTimeline",
    "TimelineMismatch",
    "InvalidClipDuration",
    "ClipDurationMismatch",
    "IntegratedRenderForbidden",
]
