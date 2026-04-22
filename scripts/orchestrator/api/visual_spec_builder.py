"""visual_spec_builder — blueprint + script + channel_preset + sources_manifest -> VisualSpec.

Phase 16-04 — REQ-PROD-INT-06.

asset-sourcer 가 이 모듈을 호출. 에이전트는 영화적 결정만 담당하고 수치 계산은 본 모듈이 수행
(Q2 답변: asset-sourcer 가 단일 source-of-truth, shorts-designer 중복 에이전트 없음).

참조 포트:
- `.preserved/harvested/video_pipeline_raw/` 의 build_shorts_props 논리
- `.preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json` schema SSOT

Public API:
    build(blueprint, script, channel_preset, sources_manifest,
          audio_duration_s, episode_id, visual_spec_override=None) -> VisualSpec
    load_channel_preset(memory_path: Path) -> dict
    VisualSpecBuildError (Exception)
"""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from .models import ClipDesign, TitleKeyword, VisualSpec

__all__ = [
    "build",
    "load_channel_preset",
    "VisualSpecBuildError",
    "FPS",
    "VALID_MOVEMENTS",
    "ROUND_ROBIN_MOVEMENTS",
    "VALID_TRANSITIONS",
]

logger = logging.getLogger(__name__)

FPS = 30
VALID_MOVEMENTS = ("zoom_in", "zoom_out", "pan_left", "pan_right")
ROUND_ROBIN_MOVEMENTS = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
VALID_TRANSITIONS = [
    "fade",
    "glitch",
    "rgb-split",
    "zoom-blur",
    "light-leak",
    "clock-wipe",
    "pixelate",
    "checkerboard",
]

# Default frames for intro/outro signatures (zodiac-killer baseline = 99 each).
DEFAULT_INTRO_FRAMES = 99
DEFAULT_OUTRO_FRAMES = 99
MIN_SCENE_FRAMES = 30  # 1s absolute floor per Pattern 4 (narration drives, but guard).

# Sentinel defaults (incidents production baseline).
_DEFAULT_CHANNEL_NAME = "사건기록부"
_DEFAULT_ACCENT_COLOR = "#FF2200"
_DEFAULT_FONT = "BlackHanSans"
_DEFAULT_SUB_POSITION = 0.8
_DEFAULT_SUB_HIGHLIGHT = "#FFFFFF"
_DEFAULT_SUB_FONTSIZE = 68
_DEFAULT_HASHTAGS = "#쇼츠 #범죄 #미제사건 #실화"


class VisualSpecBuildError(ValueError):
    """build() 실패 — 필수 입력 누락 또는 계약 위반."""


# ─────────────────────────────────────────────────────────────────────────────
# Preset loader
# ─────────────────────────────────────────────────────────────────────────────


def load_channel_preset(memory_path: Path) -> dict[str, Any]:
    """`.claude/memory/project_channel_preset_<channel>.md` 파싱.

    간이 regex 파서 — "## <key>\\n<value>" 패턴만 추출.
    복잡한 구조는 향후 YAML frontmatter 로 전환 고려 (Phase 17+).

    Args:
        memory_path: 박제 메모리 파일 경로.

    Returns:
        Preset dict. 파일 없으면 default 만 반환 (safe fallback).
    """
    preset: dict[str, Any] = {
        "channelName": _DEFAULT_CHANNEL_NAME,
        "accentColor": _DEFAULT_ACCENT_COLOR,
        "fontFamily": _DEFAULT_FONT,
        "subtitlePosition": _DEFAULT_SUB_POSITION,
        "subtitleHighlightColor": _DEFAULT_SUB_HIGHLIGHT,
        "subtitleFontSize": _DEFAULT_SUB_FONTSIZE,
        "hashtags_default": _DEFAULT_HASHTAGS,
        "transitions": list(VALID_TRANSITIONS),
    }

    if not memory_path.exists():
        logger.warning(
            "channel preset memory 미존재, default 사용: %s", memory_path
        )
        return preset

    text = memory_path.read_text(encoding="utf-8")

    # Simple regex: "## channelName\n사건기록부" or "## accentColor\n#FF2200"
    # Preset memory format has value on line directly below the "## <key>" header.
    patterns = [
        (r"^## channelName\s*\n([^\n]+)", "channelName", str),
        (r"^## accentColor\s*\n(#[0-9A-Fa-f]{6})", "accentColor", str),
        (r"^## subtitlePosition\s*\n([0-9]*\.?[0-9]+)", "subtitlePosition", float),
        (
            r"^## subtitleHighlightColor\s*\n(#[0-9A-Fa-f]{6})",
            "subtitleHighlightColor",
            str,
        ),
        (r"^## subtitleFontSize\s*\n([0-9]+)", "subtitleFontSize", int),
    ]
    for regex, key, cast in patterns:
        m = re.search(regex, text, re.MULTILINE)
        if m:
            raw = m.group(1).strip().rstrip(".")
            # Preset memory lines may look like "사건기록부 — 3 episode..."; take first token.
            if key == "channelName":
                raw = raw.split(" ", 1)[0].strip()
            try:
                preset[key] = cast(raw)
            except (TypeError, ValueError):
                logger.warning(
                    "channel preset parse skip: key=%s raw=%r", key, raw
                )

    # fontFamily: prefer "기본값: BlackHanSans" line if present.
    m = re.search(
        r"기본값\s*:\s*(BlackHanSans|DoHyeon|NotoSansKR)", text
    )
    if m:
        preset["fontFamily"] = m.group(1)

    return preset


# ─────────────────────────────────────────────────────────────────────────────
# Main entry
# ─────────────────────────────────────────────────────────────────────────────


def build(
    blueprint: dict[str, Any],
    script: dict[str, Any],
    channel_preset: dict[str, Any],
    sources_manifest: dict[str, Any],
    audio_duration_s: float,
    episode_id: str,
    visual_spec_override: dict[str, Any] | None = None,
) -> VisualSpec:
    """blueprint + script + preset + sources -> VisualSpec.

    Args:
        blueprint: blueprint.json dict (title_display / source_strategy etc.).
        script: script.json dict (sections / title etc.).
        channel_preset: load_channel_preset() 결과 dict.
        sources_manifest: SourcesManifest-shape dict (scene_sources list 필수).
        audio_duration_s: TTS ffprobe 실측 narration.mp3 초.
        episode_id: "zodiac-killer" — src path prefix.
        visual_spec_override: 전수 override (asset-sourcer 이 직접 결정 시 우선 적용).

    Returns:
        Validated VisualSpec Pydantic instance.
    """
    if visual_spec_override is not None:
        # Designer single source of truth override — 전수 전달, 그대로 검증.
        return VisualSpec.model_validate(visual_spec_override)

    if audio_duration_s <= 0:
        raise VisualSpecBuildError(
            f"audio_duration_s > 0 필수: {audio_duration_s}"
        )
    if not episode_id:
        raise VisualSpecBuildError("episode_id 필수")

    # 1) title lines
    td: dict[str, Any] = blueprint.get("title_display", {}) or {}
    title_line1 = td.get("line1") or _heuristic_title_line1(script)
    title_line2 = td.get("line2") or _heuristic_title_line2(script)
    accent_words: list[str] = td.get("accent_words") or []
    accent_color: str = td.get("accent_color") or channel_preset.get(
        "accentColor", _DEFAULT_ACCENT_COLOR
    )

    # 2) titleKeywords[]
    full_title = f"{title_line1}{title_line2}"
    title_keywords: list[TitleKeyword] = []
    for w in accent_words:
        if w and w in full_title:
            title_keywords.append(TitleKeyword(text=w, color=accent_color))
    if not title_keywords:
        # Fallback — first 2-char chunk from title_line2 as keyword.
        fallback_text = title_line2[:2] if title_line2 else title_line1[:2]
        if fallback_text:
            title_keywords.append(
                TitleKeyword(text=fallback_text, color=accent_color)
            )

    # 3) transitionType round-robin by title hash
    title_hash = int(
        hashlib.sha1(full_title.encode("utf-8")).hexdigest()[:8], 16
    )
    transition_type = VALID_TRANSITIONS[title_hash % len(VALID_TRANSITIONS)]

    # 4) clips[]
    clips = _build_clips(
        sources_manifest=sources_manifest,
        channel_preset=channel_preset,
        audio_duration_s=audio_duration_s,
        episode_id=episode_id,
        title_hash=title_hash,
    )

    return VisualSpec(
        titleLine1=title_line1,
        titleLine2=title_line2,
        titleKeywords=title_keywords,
        accentColor=accent_color,
        channelName=channel_preset.get("channelName", _DEFAULT_CHANNEL_NAME),
        hashtags=channel_preset.get("hashtags_default", _DEFAULT_HASHTAGS),
        fontFamily=channel_preset.get("fontFamily", _DEFAULT_FONT),
        characterLeftSrc=f"{episode_id}/character_assistant.png",
        characterRightSrc=f"{episode_id}/character_detective.png",
        subtitlePosition=float(
            channel_preset.get("subtitlePosition", _DEFAULT_SUB_POSITION)
        ),
        subtitleHighlightColor=channel_preset.get(
            "subtitleHighlightColor", _DEFAULT_SUB_HIGHLIGHT
        ),
        subtitleFontSize=int(
            channel_preset.get("subtitleFontSize", _DEFAULT_SUB_FONTSIZE)
        ),
        audioSrc=f"{episode_id}/narration.mp3",
        durationInFrames=int(round(audio_duration_s * FPS)),
        transitionType=transition_type,
        clips=clips,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Clip builder
# ─────────────────────────────────────────────────────────────────────────────


def _build_clips(
    sources_manifest: dict[str, Any],
    channel_preset: dict[str, Any],
    audio_duration_s: float,
    episode_id: str,
    title_hash: int,
) -> list[ClipDesign]:
    """scene_sources[] 순서 + intro/outro signature 를 clipDesign 으로 매핑."""
    scene_srcs: list[str] = sources_manifest.get("scene_sources", []) or []
    if not scene_srcs:
        raise VisualSpecBuildError(
            "scene_sources 빈 리스트 — asset-sourcer 미산출 (Pitfall 5)"
        )

    total_frames = int(round(audio_duration_s * FPS))
    intro_frames = DEFAULT_INTRO_FRAMES
    outro_src = sources_manifest.get("outro_signature")
    outro_frames = DEFAULT_OUTRO_FRAMES if outro_src else 0
    body_frames_total = max(
        MIN_SCENE_FRAMES, total_frames - intro_frames - outro_frames
    )
    per_scene = max(MIN_SCENE_FRAMES, body_frames_total // max(1, len(scene_srcs)))

    clips: list[ClipDesign] = []

    # Intro signature clip (movement=None = freeze)
    intro_src = sources_manifest.get(
        "intro_signature", f"{episode_id}/intro_signature.mp4"
    )
    clips.append(
        ClipDesign(
            type="video",
            src=_to_relative(intro_src, episode_id),
            durationInFrames=intro_frames,
            transition="fade",
            movement=None,
        )
    )

    # Body scenes — round-robin movement for images, None for video
    for i, src in enumerate(scene_srcs):
        rel = _to_relative(src, episode_id)
        is_video = rel.lower().endswith((".mp4", ".mov", ".webm"))
        movement = (
            None
            if is_video
            else ROUND_ROBIN_MOVEMENTS[
                (title_hash + i) % len(ROUND_ROBIN_MOVEMENTS)
            ]
        )
        clips.append(
            ClipDesign(
                type="video" if is_video else "image",
                src=rel,
                durationInFrames=per_scene,
                transition="fade",
                movement=movement,
            )
        )

    # Outro signature — only if provided (Option A = programmatic OutroCard.tsx)
    if outro_src:
        clips.append(
            ClipDesign(
                type="video",
                src=_to_relative(outro_src, episode_id),
                durationInFrames=outro_frames,
                transition="fade",
                movement=None,
            )
        )

    return clips


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _to_relative(src: str, episode_id: str) -> str:
    """절대경로/상대경로 혼용 입력을 `<episode_id>/<basename>` 로 정규화.

    Remotion `public/<episode_id>/` 에 복사된 자산 참조 규칙.
    """
    if not src:
        raise VisualSpecBuildError("빈 src")
    p = Path(src)
    return f"{episode_id}/{p.name}"


def _heuristic_title_line1(script: dict[str, Any]) -> str:
    """script.title / hook / topic 에서 1번째 라인 heuristic 추출."""
    t = script.get("title") or script.get("hook") or script.get("topic") or "미해결 사건"
    if isinstance(t, dict):
        return (
            t.get("line1")
            or t.get("main")
            or t.get("primary")
            or "미해결 사건"
        )
    return str(t).split("\n", 1)[0][:30]


def _heuristic_title_line2(script: dict[str, Any]) -> str:
    """script.title 2번째 라인 heuristic 추출. 없으면 topic 기반 fallback."""
    t = script.get("title") or script.get("hook") or script.get("topic") or ""
    if isinstance(t, dict):
        return t.get("line2") or t.get("sub") or "의 진실"
    parts = str(t).split("\n")
    if len(parts) > 1:
        return parts[1][:30]
    # Fallback: script.sections 첫 문장의 3자
    sections = script.get("sections") or []
    if sections and isinstance(sections[0], dict):
        txt = sections[0].get("text") or sections[0].get("narration") or ""
        if txt:
            return str(txt)[:8] or "의 진실"
    return "의 진실"
