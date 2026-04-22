"""Pydantic v2 request contracts for Phase 5 API adapters.

Shape the inputs to ``KlingI2VAdapter.image_to_video``, ``TypecastAdapter.generate``,
and ``ShotstackAdapter.render`` at parse time so bad requests die before any
HTTP traffic. All invariants trace back to CONTEXT decisions:

* **D-13 (VIDEO-01)** — text-to-video code paths are physically forbidden;
  :class:`I2VRequest` therefore requires an ``anchor_frame`` and has no
  "T2V mode" flag or optional-anchor escape hatch.
* **D-14 (VIDEO-02)** — every I2V clip must be 4-8 seconds long and contain
  exactly one move. ``duration_seconds`` uses ``Field(ge=4, le=8)`` and
  ``move_count`` is ``Literal[1]`` so pydantic rejects out-of-band values
  before they reach the adapter.
* **D-17 (VIDEO-05)** — the Shotstack assembly filter order is
  ``color_grade -> saturation -> film_grain``.
  :class:`ShotstackRenderRequest` surfaces this as the default
  ``filters_order`` so a caller that omits the argument still gets the
  canonical sequence.
* **ORCH-11** — the Low-Res First render targets 720p (``resolution="hd"``)
  at 9:16 aspect. :class:`ShotstackRenderRequest` defaults both fields
  accordingly; a caller must explicitly opt in to a higher resolution.

These models are pure data — no HTTP, no file I/O, no CircuitBreaker. The
adapter classes in :mod:`scripts.orchestrator.api.kling_i2v` and friends
instantiate them at the top of each public method to weaponise pydantic's
validation as the contract enforcement layer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class I2VRequest(BaseModel):
    """Image-to-video request contract — enforces VIDEO-01, VIDEO-02 at parse time.

    Invariants (D-13, D-14):

    * ``anchor_frame`` REQUIRED (:class:`Path`) — no T2V-style generation allowed.
    * ``duration_seconds`` ∈ [4, 8] (the 1 Move Rule duration bound).
    * ``move_count`` == 1 (exactly 1 camera walking + 1 subject action).

    The ``arbitrary_types_allowed`` config entry is needed because
    :class:`pathlib.Path` is not a pydantic primitive; pydantic v2 requires
    explicit opt-in for any custom type in a model field.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    prompt: str = Field(
        min_length=1,
        description="Scene prompt (Korean narration or visual description).",
    )
    anchor_frame: Path = Field(
        description="D-13: REQUIRED anchor image path (no T2V).",
    )
    duration_seconds: int = Field(
        ge=4,
        le=8,
        description="VIDEO-02 / D-14: 4-8 second clip length.",
    )
    move_count: Literal[1] = Field(
        default=1,
        description="VIDEO-02 / D-14: exactly 1 move per clip.",
    )
    style_prefix: str | None = Field(
        default=None,
        description="Optional Continuity Bible style prefix (Phase 6 WIKI-02).",
    )
    negative_prompt: str | None = Field(
        default=None,
        description="Optional negative prompt (Kling / Runway style).",
    )


class TypecastRequest(BaseModel):
    """Typecast TTS request for one scene. Shapes the AudioSegment output."""

    scene_id: int = Field(ge=0)
    text: str = Field(min_length=1)
    emotion_style: str = Field(
        default="neutral",
        description="AUDIO-03: dynamic emotion parameter.",
    )
    voice_id: str = Field(
        default="detective_hao",
        description="Channel-specific voice id.",
    )
    # Session #31 — Typecast SDK v1 pydantic upgrade requires explicit model.
    # ssfm-v30 = 최신 한국어 모델 (Morgan/Guri 등 주요 incidents voice 지원).
    model: str = Field(
        default="ssfm-v30",
        description="Typecast model version. ssfm-v30 주 사용 (2026Q2 기준).",
    )


class ShotstackRenderRequest(BaseModel):
    """Shotstack render call — ORCH-11 Low-Res First, D-17 filter order.

    ``resolution`` defaults to ``"hd"`` (720p) to keep the first-pass render
    cheap per ORCH-11; callers that want 4K must explicitly pass ``"4k"`` and
    pay for the upscale. ``filters_order`` defaults to the canonical D-17
    sequence; overriding it is allowed for tests but should never happen in
    production.
    """

    timeline_entries: list[dict] = Field(min_length=1)
    resolution: Literal["sd", "hd", "full-hd", "4k"] = Field(
        default="hd",
        description="ORCH-11: 'hd' == 720p (the Low-Res First target).",
    )
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = Field(
        default="9:16",
        description="Shorts format.",
    )
    filters_order: list[str] = Field(
        default_factory=lambda: ["color_grade", "saturation", "film_grain"],
        description="D-17: color grade -> saturation -> film grain.",
    )


# ---------------------------------------------------------------------------
# Phase 6 Plan 06: Continuity Bible Prefix (D-20 / WIKI-02)
# ---------------------------------------------------------------------------

HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]
"""6-digit hex color like ``#1A2E4A``. Consumed by :class:`ContinuityPrefix`."""


class ContinuityPrefix(BaseModel):
    """D-20: Continuity Bible prefix schema — channel-identity fingerprint.

    All fields enforce D-10's 5 components at parse time so a missing or
    drifted component fails before any render attempt:

    * ``color_palette`` + ``warmth``  -> D-10(a) color palette
    * ``focal_length_mm`` + ``aperture_f``  -> D-10(b) camera lens
    * ``visual_style``  -> D-10(c) locked literal
    * ``audience_profile``  -> D-10(d) + D-16 Korean senior descriptor
    * ``bgm_mood``  -> D-10(e) 3 presets

    Serialized form lives at ``wiki/continuity_bible/prefix.json``;
    :mod:`scripts.orchestrator.api.shotstack` loads it at render time and
    injects ``"continuity_prefix"`` at the first position of
    :attr:`ShotstackRenderRequest.filters_order` per D-19.

    ``extra="forbid"`` ensures schema drift in ``prefix.json`` surfaces at
    parse time rather than corrupting renders silently (Pitfall 5).
    """

    model_config = ConfigDict(extra="forbid")

    color_palette: list[HexColor] = Field(min_length=3, max_length=5, description="D-10(a): 3-5 HEX anchors.")
    warmth: Annotated[float, Field(ge=-1.0, le=1.0)] = Field(description="D-10(a): -1 cool .. +1 warm.")
    focal_length_mm: Annotated[int, Field(ge=18, le=85)] = Field(description="D-10(b): typical 35 or 50.")
    aperture_f: Annotated[float, Field(ge=1.4, le=16.0)] = Field(description="D-10(b): f-stop.")
    visual_style: Literal["photorealistic", "cinematic", "documentary"] = Field(description="D-10(c).")
    audience_profile: str = Field(min_length=10, description="D-10(d)+D-16 Korean senior descriptor.")
    bgm_mood: Literal["ambient", "tension", "uplift"] = Field(description="D-10(e): 3 presets.")


# ============================================================================
# Phase 16-04 — REQ-PROD-INT-04 / 06 / 09
# VisualSpec Pydantic 모델 (zodiac-killer baseline 동일 스키마)
# ============================================================================

from typing import Optional

from pydantic import PositiveInt, confloat, field_validator


class TitleKeyword(BaseModel):
    """VisualSpec.titleKeywords[] 엔트리 — text + HEX color."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    color: str

    @field_validator("color")
    @classmethod
    def _hex_color(cls, v: str) -> str:
        if not (
            len(v) == 7
            and v.startswith("#")
            and all(c in "0123456789abcdefABCDEF" for c in v[1:])
        ):
            raise ValueError(f"color 는 #RRGGBB 형식: {v!r}")
        return v


class ClipDesign(BaseModel):
    """VisualSpec.clips[] 엔트리 — 단일 clip design (video|image).

    Pitfall 4: ``movement=None`` 은 의도적 freeze (Remotion ``_NULL_FREEZE`` sentinel).
    Pitfall 6: ``durationInFrames`` 은 positive int 만 허용 (float 금지).
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["video", "image"]
    src: str = Field(..., min_length=1)
    durationInFrames: PositiveInt
    transition: Literal[
        "fade",
        "glitch",
        "rgb-split",
        "zoom-blur",
        "light-leak",
        "clock-wipe",
        "pixelate",
        "checkerboard",
    ]
    movement: Optional[
        Literal["zoom_in", "zoom_out", "pan_left", "pan_right"]
    ] = None

    @field_validator("durationInFrames", mode="before")
    @classmethod
    def _no_float(cls, v: object) -> object:
        if isinstance(v, bool):
            # bool is subclass of int — reject to avoid True/False leaks
            raise ValueError("durationInFrames: bool 금지")
        if isinstance(v, float):
            if not v.is_integer():
                raise ValueError(
                    f"durationInFrames 는 positive int, float 금지 (Pitfall 6): {v}"
                )
            return int(v)
        return v


class VisualSpec(BaseModel):
    """Phase 16-04 VisualSpec — zodiac-killer baseline 과 동일 스키마.

    ``extra='forbid'`` + Literal enum + custom validators 로
    스키마 drift 를 parse 시점에 차단 (Pitfall 5).
    Q4 매핑: characterLeftSrc = assistant (왓슨/조수),
    characterRightSrc = detective (Morgan/탐정). 의미 고정.
    """

    model_config = ConfigDict(extra="forbid")

    titleLine1: str = Field(..., min_length=1, max_length=30)
    titleLine2: str = Field(..., min_length=1, max_length=30)
    titleKeywords: list[TitleKeyword]
    accentColor: str
    channelName: str = Field(..., min_length=1)
    hashtags: str
    fontFamily: Literal["BlackHanSans", "DoHyeon", "NotoSansKR"]
    characterLeftSrc: str
    characterRightSrc: str
    subtitlePosition: confloat(ge=0.0, le=1.0)  # type: ignore[valid-type]
    subtitleHighlightColor: str
    subtitleFontSize: PositiveInt = Field(..., ge=24, le=128)
    audioSrc: str = Field(..., min_length=1)
    durationInFrames: PositiveInt
    transitionType: Literal[
        "fade",
        "glitch",
        "rgb-split",
        "zoom-blur",
        "light-leak",
        "clock-wipe",
        "pixelate",
        "checkerboard",
    ]
    clips: list[ClipDesign] = Field(..., min_length=1)

    @field_validator("accentColor", "subtitleHighlightColor")
    @classmethod
    def _hex_color(cls, v: str) -> str:
        if not (
            len(v) == 7
            and v.startswith("#")
            and all(c in "0123456789abcdefABCDEF" for c in v[1:])
        ):
            raise ValueError(f"색상 #RRGGBB 형식: {v!r}")
        return v

    @field_validator("characterLeftSrc")
    @classmethod
    def _left_is_assistant(cls, v: str) -> str:
        """Q4: 좌측은 assistant (왓슨/조수) — character_assistant.png 로 종료."""
        if not v.endswith("character_assistant.png"):
            raise ValueError(
                f"characterLeftSrc 는 character_assistant.png 로 끝나야 함 "
                f"(Q4 좌=조수): {v!r}"
            )
        return v

    @field_validator("characterRightSrc")
    @classmethod
    def _right_is_detective(cls, v: str) -> str:
        """Q4: 우측은 detective (Morgan/탐정) — character_detective.png 로 종료."""
        if not v.endswith("character_detective.png"):
            raise ValueError(
                f"characterRightSrc 는 character_detective.png 로 끝나야 함 "
                f"(Q4 우=탐정): {v!r}"
            )
        return v


class SourcesManifest(BaseModel):
    """output/<episode>/sources/ 디렉토리 계약.

    asset-sourcer 산출 + gate_guard 검증. Pitfall 5 (scene_sources ≥ 5 강제)
    + feedback_veo_supplementary_only (veo_supplement ≤ 2).
    """

    model_config = ConfigDict(extra="forbid")

    character_detective: str
    character_assistant: str
    intro_signature: str
    outro_signature: Optional[str] = None
    scene_sources: list[str] = Field(..., min_length=5)
    scene_sources_count: PositiveInt = Field(..., ge=5)
    real_image_count: int = Field(..., ge=0)
    veo_supplement_count: int = Field(..., ge=0, le=2)
    signature_reuse_count: int = Field(..., ge=0, le=2)
    real_ratio: confloat(ge=0.0, le=1.0)  # type: ignore[valid-type]


__all__ = [
    "I2VRequest",
    "TypecastRequest",
    "ShotstackRenderRequest",
    "ContinuityPrefix",
    "HexColor",
    # Phase 16-04
    "TitleKeyword",
    "ClipDesign",
    "VisualSpec",
    "SourcesManifest",
]
