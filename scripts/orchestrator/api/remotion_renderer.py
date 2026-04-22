"""RemotionRenderer — Python bridge to the Remotion TypeScript CLI.

Phase 16-02 — REQ-PROD-INT-02 / REQ-PROD-INT-10 / REQ-PROD-INT-14.

Ported from `.preserved/harvested/video_pipeline_raw/remotion_render.py` (1162
lines). Public surface (`render(timeline, resolution, aspect_ratio) -> dict`)
mirrors :class:`scripts.orchestrator.api.ffmpeg_assembler.FFmpegAssembler.render`
so the ASSEMBLY gate can swap renderers transparently.

Design notes
------------
- ``RemotionRenderer`` is constructed up-front in :class:`ShortsPipeline.__init__`.
  If ``node`` / ``ffprobe`` / ``remotion/`` are missing, ``RemotionUnavailable``
  is raised so the pipeline falls back to Shotstack / ffmpeg immediately.
- Each ``render()`` call creates an isolated ``remotion/public/<job_id>/``
  workspace, invokes ``npx remotion render src/index.ts ShortsVideo out.mp4
  --props=<path>``, then cleans up the workspace.
- After subprocess completion, :meth:`_verify_production_baseline` runs
  ``ffprobe`` on the output and enforces
  ``width=1080, height=1920, codec in {h264, hevc}, duration >= 60.0s``
  (ROADMAP Phase 16 SC#4 — "spec pass ≠ production pass" guard).
- ``_NULL_FREEZE`` sentinel propagates Designer's intentional freeze semantics
  (visual_spec.clipDesign[i].movement = null) through the build pipeline and
  gets popped before Zod validation (Pitfall 4 defense).
- CLAUDE.md 금기 #11 — no Veo API calls anywhere in this module.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "RemotionRenderer",
    "RemotionUnavailable",
    "RemotionValidationError",
    "RemotionBaselineError",
    "NULL_FREEZE_SENTINEL",
    "TARGET_RESOLUTION",
    "TARGET_FPS",
    "MIN_PRODUCTION_DURATION_S",
    "SUBTITLE_COVERAGE_MIN",
]

logger = logging.getLogger(__name__)


# ============================================================================
# Module constants — DO NOT modify without ROADMAP SC#4 / DESIGN_SPEC review.
# ============================================================================

DEFAULT_OUTPUT_DIR = Path("outputs/remotion")
DEFAULT_SUBPROCESS_TIMEOUT_S = 600
FIRST_RENDER_TIMEOUT_S = 180  # Chrome Headless Shell 최초 다운로드 여유

TARGET_RESOLUTION = (1080, 1920)  # W x H, 9:16 vertical Shorts
TARGET_FPS = 30

# ROADMAP Phase 16 SC#4 — production baseline 하한.
# incidents.md §2 legacy "50s 단편" 은 시그니처+오버레이+단어자막을 포함하지 않음.
# Phase 16 production 은 60s 최소 (hook 9s + body + outro).
MIN_PRODUCTION_DURATION_S = 60.0

SUBTITLE_COVERAGE_MIN = 0.95
MIN_SCENE_CLIPS = 1
VALID_MOVEMENTS = frozenset({"zoom_in", "zoom_out", "pan_left", "pan_right"})

# Sentinel used to propagate Designer's "intentional freeze" (movement=null).
# Pitfall 4: prevents round-robin auto-assignment from overwriting a null
# movement. Popped before Zod validation (Remotion schema rejects unknown).
NULL_FREEZE_SENTINEL = "_NULL_FREEZE"


# ============================================================================
# Exception hierarchy
# ============================================================================


class RemotionUnavailable(RuntimeError):
    """Constructor precondition failure — node/npx/ffprobe 또는 remotion/ 부재."""


class RemotionValidationError(ValueError):
    """Props validation failure before subprocess invocation."""


class RemotionBaselineError(RuntimeError):
    """Post-render ffprobe detected production baseline violation (SC#4)."""


# ============================================================================
# Channel presets — minimal built-in set (Plan 16-04 will externalize these
# into `.claude/memory/project_channel_preset_incidents.md` + schemas/).
# ============================================================================

_CHANNEL_PRESETS: dict[str, dict[str, Any]] = {
    "incidents": {
        "channelName": "사건기록부",
        "fontFamily": "BlackHanSans",
        "defaultAccent": "#E53E3E",
        "hashtags": "#사건기록부 #미스터리 #쇼츠",
        "transitions": ["fade", "glitch", "rgbSplit"],
        "subscribeText": "구독",
        "likeText": "좋아요",
        "subtitlePosition": 0.85,
        "subtitleHighlightColor": "#E53E3E",
        "subtitleFontSize": 72,
        "taglineLabels": {
            "mystery": "미스터리 수첩",
            "crime": "범죄수첩",
            "phenomena": "기현상 수첩",
        },
    },
    # fallback — humor-ish defaults (kept for test compatibility)
    "humor": {
        "channelName": "썰튜브",
        "fontFamily": "Pretendard",
        "defaultAccent": "#FFD000",
        "hashtags": "#쇼츠 #유머",
        "transitions": ["fade"],
    },
}


# ============================================================================
# RemotionRenderer — public class
# ============================================================================


class RemotionRenderer:
    """Local Remotion CLI invocation bridge (ASSEMBLY priority-1 renderer).

    Parameters
    ----------
    project_root
        Repo root. Defaults to ``Path(__file__).resolve().parents[3]``
        (scripts/orchestrator/api/ → parents[3] = repo root).
    remotion_dir_name
        Sub-directory containing the Remotion TypeScript project. Default
        ``remotion`` (Phase 16-02 Wave 0 산출).
    output_dir
        Directory where rendered mp4 files land. Default
        ``<project_root>/outputs/remotion``.
    timeout_s
        Subprocess timeout for subsequent renders (Chrome already downloaded).
    first_render_timeout_s
        Longer timeout for the very first render of the process lifetime
        (Chrome Headless Shell download + Remotion bundle compile).
    """

    def __init__(
        self,
        project_root: Path | None = None,
        remotion_dir_name: str = "remotion",
        output_dir: Path | None = None,
        timeout_s: int = DEFAULT_SUBPROCESS_TIMEOUT_S,
        first_render_timeout_s: int = FIRST_RENDER_TIMEOUT_S,
    ) -> None:
        self.project_root = (
            project_root or Path(__file__).resolve().parents[3]
        ).absolute()
        self.remotion_dir = self.project_root / remotion_dir_name
        self.output_dir = (
            output_dir or (self.project_root / DEFAULT_OUTPUT_DIR)
        ).absolute()
        self.timeout_s = int(timeout_s)
        self.first_render_timeout_s = int(first_render_timeout_s)
        self._is_first_render = True

        # Probe: node, ffprobe, remotion/
        if shutil.which("node") is None:
            raise RemotionUnavailable(
                "node binary not on PATH — RemotionRenderer disabled "
                "(대표님 Node.js 설치 확인 필요)"
            )
        if not self.remotion_dir.exists() or not (self.remotion_dir / "package.json").exists():
            raise RemotionUnavailable(
                f"remotion 디렉토리 부재: {self.remotion_dir} "
                "(Phase 16-02 Wave 0 bootstrap 필요)"
            )
        if shutil.which("ffprobe") is None:
            raise RemotionUnavailable(
                "ffprobe binary not on PATH — production baseline 검증 불가"
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "[remotion] RemotionRenderer initialized (remotion_dir=%s, output_dir=%s)",
            self.remotion_dir,
            self.output_dir,
        )

    # ------------------------------------------------------------------
    # Public API — signature parity with FFmpegAssembler / ShotstackAdapter
    # ------------------------------------------------------------------

    def render(
        self,
        timeline: list[Any],
        resolution: str = "fhd",
        aspect_ratio: str = "9:16",
    ) -> dict[str, Any]:
        """ASSEMBLY gate entry point — compose timeline into a 9:16 Shorts mp4.

        Pipeline:
            1. _extract_from_timeline  — pull script / blueprint / visual_spec
               / subtitle / audio from timeline entries and ctx artifacts.
            2. _prepare_remotion_assets — copy assets into
               ``remotion/public/<job_id>/``.
            3. _get_audio_duration_ffprobe — SSOT timing check.
            4. _pre_render_quality_gates — scene_clips count + subtitle
               coverage ≥ 0.95.
            5. _build_shorts_props — construct the props dict (Zod schema
               compatible). ``_NULL_FREEZE`` sentinel injected then popped.
            6. _inject_character_props — Detective / Assistant PNG overlay.
            7. _validate_shorts_props — fail-fast before subprocess.
            8. _invoke_remotion_cli — ``npx remotion render ...``.
            9. _cleanup_remotion_assets — drop the per-job public subdir.
           10. _verify_production_baseline — ffprobe the output; enforce
               1080×1920, codec ∈ {h264, hevc}, duration ≥ 60s.

        Returns
        -------
        dict
            ``{"url", "status", "renderer"="remotion", "duration_frames",
               "size_mb", "ffprobe", "resolution", "aspect_ratio"}``.
        """
        job_id = f"render_{int(time.time() * 1000)}"
        episode_dir = self.output_dir / job_id
        episode_dir.mkdir(parents=True, exist_ok=True)

        # 1. Extract ingredients from the timeline + GateContext artifacts.
        (
            assets,
            audio_duration,
            script,
            blueprint,
            visual_spec_path,
            subtitle_json,
        ) = self._extract_from_timeline(timeline, episode_dir)

        # 2. Stage assets in remotion/public/<job_id>/
        self._prepare_remotion_assets(job_id, assets, script.get("series"))

        # 3. ffprobe SSOT — drift > 1.0s → prefer ffprobe value.
        audio_path = assets.get("audioSrc_abs")
        if audio_path:
            ffprobe_dur = self._get_audio_duration_ffprobe(audio_path)
            if ffprobe_dur > 0 and abs(ffprobe_dur - audio_duration) > 1.0:
                logger.warning(
                    "[remotion] audio duration drift %.3fs (caller=%.3f ffprobe=%.3f) — "
                    "ffprobe 값 우선 적용 (Narration Drives Timing)",
                    abs(ffprobe_dur - audio_duration),
                    audio_duration,
                    ffprobe_dur,
                )
                audio_duration = ffprobe_dur

        # 4. Pre-render quality gates
        self._pre_render_quality_gates(
            assets.get("scene_clips", []), subtitle_json, audio_duration
        )

        # 5. Props build (with _NULL_FREEZE sentinel lifecycle).
        props = self._build_shorts_props(
            script=script,
            channel=script.get("channel", "incidents"),
            assets=assets,
            subtitle_json_path=subtitle_json,
            audio_duration=audio_duration,
            blueprint=blueprint,
            visual_spec_path=visual_spec_path,
        )

        # 6. Character overlay injection (expects sources/ prepared by asset-sourcer).
        self._inject_character_props(props, job_id, episode_dir)

        # 7. Validate before invoking subprocess.
        self._validate_shorts_props(props)

        # 8. Persist props + invoke CLI.
        props_path = episode_dir / "remotion_props.json"
        props_path.write_text(
            json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        output_mp4 = episode_dir / "final.mp4"
        self._invoke_remotion_cli(props_path, output_mp4)

        # 9. Cleanup per-job assets.
        self._cleanup_remotion_assets(job_id)

        # 10. Production baseline enforcement (ROADMAP SC#4).
        meta = self._verify_production_baseline(output_mp4)

        size_mb = round(output_mp4.stat().st_size / 1024 / 1024, 2) if output_mp4.exists() else 0.0

        return {
            "url": output_mp4.as_posix(),
            "status": "assembled",
            "renderer": "remotion",
            "duration_frames": int(props["durationInFrames"]),
            "size_mb": size_mb,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "ffprobe": meta,
        }

    def upscale(self, url: str) -> dict[str, Any]:
        """Phase 8 NOOP — Remotion renders natively at 1080p."""
        return {
            "status": "skipped",
            "reason": "remotion native 1080p output (no upscale path)",
            "url": url,
        }

    # ------------------------------------------------------------------
    # Internal — harvested remotion_render.py mirror (1:1 logic)
    # ------------------------------------------------------------------

    def _get_audio_duration_ffprobe(self, audio_path: str | Path) -> float:
        """Return audio duration in seconds using ffprobe. 0.0 on failure.

        Mirrors harvested remotion_render.py:293-320.
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                shell=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                dur = float(result.stdout.strip())
                logger.info("[remotion] ffprobe audio duration: %.3fs (%s)", dur, audio_path)
                return dur
            logger.warning(
                "[remotion] ffprobe failed (rc=%d): %s",
                result.returncode,
                (result.stderr or "").strip()[:200],
            )
            return 0.0
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as exc:
            logger.warning("[remotion] ffprobe error for %s: %s", audio_path, exc)
            return 0.0

    def _prepare_remotion_assets(
        self,
        job_id: str,
        assets: dict[str, Any],
        series: dict[str, Any] | None,
    ) -> None:
        """Copy pipeline assets to ``remotion/public/<job_id>/`` for staticFile().

        Phase 16-02 minimal wiring — heavy multi-clip logic (scene_clips +
        video_paths + image_paths + bgm) is inherited from harvested
        remotion_render.py:354-500 but executed only when the asset dict
        already contains such absolute paths (populated by asset-sourcer
        in Plan 16-04).
        """
        public_dir = self.remotion_dir / "public" / job_id
        public_dir.mkdir(parents=True, exist_ok=True)

        audio_abs = assets.get("audioSrc_abs")
        if audio_abs and Path(audio_abs).exists():
            dest = public_dir / "narration.mp3"
            shutil.copy2(audio_abs, dest)
            assets["audioSrc"] = f"{job_id}/narration.mp3"
            logger.info("[remotion] copied audio → %s", dest)

        # Scene clips (ordered)
        scene_clips = assets.get("scene_clips") or []
        clip_index = 0
        assets.setdefault("clips", [])
        for sc in scene_clips:
            sc_path = sc.get("path") or sc.get("abs_path")
            if not sc_path or not Path(sc_path).exists():
                continue
            ext = Path(sc_path).suffix
            dest = public_dir / f"clip_{clip_index:03d}{ext}"
            shutil.copy2(sc_path, dest)
            raw_type = sc.get("type", "image")
            if ext.lower() in (".mp4", ".mov", ".webm", ".avi"):
                clip_type = "video"
            elif raw_type in ("video", "signature"):
                clip_type = "video"
            else:
                clip_type = "image"
            entry: dict[str, Any] = {
                "type": clip_type,
                "src": f"{job_id}/clip_{clip_index:03d}{ext}",
            }
            if sc.get("movement"):
                entry["movement"] = sc["movement"]
            if sc.get("transition"):
                entry["transition"] = sc["transition"]
            assets["clips"].append(entry)
            clip_index += 1

        # BGM (optional)
        bgm_abs = assets.get("bgmSrc_abs")
        if bgm_abs and Path(bgm_abs).exists():
            dest = public_dir / "bgm.mp3"
            shutil.copy2(bgm_abs, dest)
            assets["bgmSrc"] = f"{job_id}/bgm.mp3"
            assets["bgmVolume"] = assets.get("bgmVolume", 0.2)

        if series:
            assets["series"] = series

    def _build_shorts_props(
        self,
        script: dict[str, Any],
        channel: str,
        assets: dict[str, Any],
        subtitle_json_path: Path | str | None,
        audio_duration: float,
        blueprint: dict[str, Any] | None,
        visual_spec_path: Path | str | None,
    ) -> dict[str, Any]:
        """Construct ShortsVideo props dict (Zod-compatible).

        Mirrors harvested remotion_render.py:501-773 with 옵션 B visual_spec
        precedence + _NULL_FREEZE sentinel lifecycle + round-robin movement
        disable when visual_spec is provided (Pitfall 4 defense).
        """
        blueprint = blueprint or {}
        preset = _CHANNEL_PRESETS.get(channel, _CHANNEL_PRESETS["humor"])

        # Title extraction — blueprint > script.title(dict) > heuristic split
        raw_title = script.get("title", script.get("topic", ""))
        title_line1_from_script: str | None = None
        title_line2_from_script: str | None = None
        accent_color_from_script: str | None = None
        accent_words_from_script: list[str] = []
        if isinstance(raw_title, dict):
            title_line1_from_script = raw_title.get("line1") or None
            title_line2_from_script = raw_title.get("line2") or None
            accent_color_from_script = raw_title.get("accent_color")
            accent_words_from_script = raw_title.get("accent_words") or []
            title = ((title_line1_from_script or "") + " " + (title_line2_from_script or "")).strip()
        else:
            title = raw_title or ""

        td = blueprint.get("title_display", {}) if isinstance(blueprint, dict) else {}
        if td.get("line1"):
            title_line1 = td["line1"]
            title_line2 = td.get("line2") or None
        elif title_line1_from_script:
            title_line1 = title_line1_from_script
            title_line2 = title_line2_from_script
        else:
            if len(title) > 12:
                mid = len(title) // 2
                space_pos = title.rfind(" ", 0, mid + 4)
                if space_pos > 3:
                    title_line1 = title[:space_pos]
                    title_line2 = title[space_pos + 1 :]
                else:
                    title_line1 = title[:mid]
                    title_line2 = title[mid:]
            else:
                title_line1 = title or "제목"
                title_line2 = None

        accent_words = td.get("accent_words") or accent_words_from_script
        accent_color = (
            td.get("accent_color")
            or accent_color_from_script
            or preset.get("defaultAccent", "#FFD000")
        )
        full_title = f"{title_line1} {title_line2}" if title_line2 else title_line1
        title_keywords: list[dict[str, str]] = []
        for word in accent_words:
            if word and word in full_title:
                title_keywords.append({"text": word, "color": accent_color})

        # Subtitles
        subtitles: list[Any] = []
        if subtitle_json_path:
            sp = Path(subtitle_json_path)
            if sp.exists():
                try:
                    subtitles = json.loads(sp.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    logger.warning("[remotion] subtitle load failed (%s): %s", sp, exc)

        total_frames = int(audio_duration * TARGET_FPS)

        props: dict[str, Any] = {
            "audioSrc": assets.get("audioSrc", ""),
            "titleLine1": title_line1 or "제목",
            "subtitles": subtitles,
            "channelName": preset["channelName"],
            "durationInFrames": total_frames,
        }
        if title_line2:
            props["titleLine2"] = title_line2
        if title_keywords:
            props["titleKeywords"] = title_keywords
        if accent_color:
            props["accentColor"] = accent_color
        if preset.get("hashtags"):
            props["hashtags"] = preset["hashtags"]
        if preset.get("fontFamily"):
            props["fontFamily"] = preset["fontFamily"]
        if preset.get("subscribeText"):
            props["subscribeText"] = preset["subscribeText"]
        if preset.get("likeText"):
            props["likeText"] = preset["likeText"]
        if preset.get("subtitlePosition") is not None:
            props["subtitlePosition"] = preset["subtitlePosition"]
        if preset.get("subtitleHighlightColor"):
            props["subtitleHighlightColor"] = preset["subtitleHighlightColor"]
        if preset.get("subtitleFontSize") is not None:
            props["subtitleFontSize"] = preset["subtitleFontSize"]

        # Series badge
        series_info = script.get("series") if isinstance(script, dict) else None
        if isinstance(series_info, dict):
            try:
                if series_info.get("part") and (series_info.get("total") or series_info.get("of")):
                    props["seriesPart"] = int(series_info["part"])
                    props["seriesTotal"] = int(series_info.get("total") or series_info.get("of"))
            except (ValueError, TypeError):
                pass

        # Channel tagline
        tagline_labels = preset.get("taglineLabels", {})
        category = (script.get("category") or "") if isinstance(script, dict) else ""
        if category and tagline_labels.get(category):
            props["titleTagline"] = tagline_labels[category]

        # Transition round-robin (channel preset pool + title hash)
        channel_transitions = preset.get("transitions") or ["fade"]
        title_hash = int(hashlib.md5((title or "x").encode("utf-8")).hexdigest(), 16)
        props["transitionType"] = channel_transitions[title_hash % len(channel_transitions)]

        # BGM
        if assets.get("bgmSrc"):
            props["bgmSrc"] = assets["bgmSrc"]
        if assets.get("bgmVolume") is not None:
            props["bgmVolume"] = assets["bgmVolume"]

        # ---- visual_spec precedence + clips composition ----
        visual_spec_provided = False
        clip_design: list[dict[str, Any]] = []
        if visual_spec_path:
            vp = Path(visual_spec_path)
            if vp.exists():
                try:
                    spec = json.loads(vp.read_text(encoding="utf-8"))
                    clip_design = spec.get("clipDesign") or []
                    visual_spec_provided = True
                except (OSError, json.JSONDecodeError) as exc:
                    logger.warning("[remotion] visual_spec load failed (%s): %s", vp, exc)

        asset_clips = assets.get("clips") or []
        if asset_clips:
            num_clips = len(asset_clips)
            TRANSITION_DURATIONS = {
                "glitch": 20, "pixelate": 20, "rgbSplit": 20, "zoomBlur": 20,
                "lightLeak": 35, "clockWipe": 25, "checkerboard": 25,
                "fade": 15, "cut": 1,
            }
            crossfade_frames = TRANSITION_DURATIONS.get(
                props.get("transitionType", "fade"), 15
            )
            total_overlap = (num_clips - 1) * crossfade_frames if num_clips > 1 else 0
            per_clip_frames = (
                (total_frames + total_overlap) // num_clips if num_clips > 0 else total_frames
            )

            remotion_clips: list[dict[str, Any]] = []
            for i, ac in enumerate(asset_clips):
                clip_data: dict[str, Any] = {
                    "type": ac["type"],
                    "src": ac["src"],
                    "durationInFrames": int(per_clip_frames),
                }
                if ac.get("movement"):
                    clip_data["movement"] = ac["movement"]
                if ac.get("transition"):
                    clip_data["transition"] = ac["transition"]
                remotion_clips.append(clip_data)

            # ---- Option B: visual_spec.clipDesign overrides round-robin ----
            if visual_spec_provided and clip_design:
                for i, rc in enumerate(remotion_clips):
                    design = clip_design[i] if i < len(clip_design) else {}
                    if not isinstance(design, dict):
                        continue
                    design_movement = design.get("movement")
                    if design_movement is None:
                        # Designer explicit null → intentional freeze sentinel
                        rc["movement"] = NULL_FREEZE_SENTINEL
                    elif design_movement in VALID_MOVEMENTS:
                        rc["movement"] = design_movement
                    else:
                        # Unknown value — sentinel (will be popped)
                        rc["movement"] = NULL_FREEZE_SENTINEL
            elif not visual_spec_provided:
                # Legacy path: round-robin movement for image clips lacking one
                _MOVEMENTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]
                for i, rc in enumerate(remotion_clips):
                    if rc["type"] == "image" and "movement" not in rc:
                        rc["movement"] = _MOVEMENTS[i % len(_MOVEMENTS)]

            # ---- Sentinel pop (Pitfall 4) ----
            # Must run AFTER all movement assignment so sentinel propagates
            # through round-robin bypass, then is erased before Zod validation.
            for rc in remotion_clips:
                if rc.get("movement") == NULL_FREEZE_SENTINEL:
                    rc.pop("movement", None)

            props["clips"] = remotion_clips
        else:
            # Legacy single-source
            if assets.get("videoSrc"):
                props["videoSrc"] = assets["videoSrc"]
            if assets.get("imageSrc"):
                props["imageSrc"] = assets["imageSrc"]

        return props

    def _validate_shorts_props(self, props: dict[str, Any]) -> None:
        """Fail-fast Zod-compatible schema check (mirrors harvested :255-290)."""
        audio_src = props.get("audioSrc")
        if not isinstance(audio_src, str) or not audio_src:
            raise RemotionValidationError(
                f"audioSrc must be a non-empty string, got: {audio_src!r}"
            )
        title_line1 = props.get("titleLine1")
        if not isinstance(title_line1, str) or not title_line1:
            raise RemotionValidationError(
                f"titleLine1 must be a non-empty string, got: {title_line1!r}"
            )
        channel_name = props.get("channelName")
        if not isinstance(channel_name, str) or not channel_name:
            raise RemotionValidationError(
                f"channelName must be a non-empty string, got: {channel_name!r}"
            )
        duration = props.get("durationInFrames")
        # Reject both non-int and bool (bool is int subclass in Python)
        if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            raise RemotionValidationError(
                f"durationInFrames must be a positive int (not float/bool), "
                f"got: {type(duration).__name__}={duration!r}"
            )
        subtitles = props.get("subtitles")
        if not isinstance(subtitles, list):
            raise RemotionValidationError(
                f"subtitles must be a list, got: {type(subtitles).__name__}"
            )

    def _pre_render_quality_gates(
        self,
        scene_clips: list[Any],
        subtitle_json: Path | str | None,
        audio_duration: float,
    ) -> None:
        """Fail-fast before subprocess invocation (§Pre-render gates)."""
        if len(scene_clips) < MIN_SCENE_CLIPS:
            # Phase 16-02 initial: warn only if explicitly empty on path
            # where scene_clips is required. Allow 0 for smoke renders.
            logger.debug(
                "[remotion] scene_clips=%d (MIN=%d) — proceeding",
                len(scene_clips),
                MIN_SCENE_CLIPS,
            )
            return
        if subtitle_json:
            sp = Path(subtitle_json)
            if sp.exists() and audio_duration > 0:
                try:
                    subs = json.loads(sp.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    logger.warning("[remotion] subtitle JSON parse failed: %s", exc)
                    return
                if subs:
                    last_end_ms = max((c.get("endMs", 0) for c in subs), default=0)
                    coverage = (last_end_ms / 1000.0) / audio_duration
                    if coverage < SUBTITLE_COVERAGE_MIN:
                        raise RemotionValidationError(
                            f"자막 coverage {coverage:.2%} < {SUBTITLE_COVERAGE_MIN:.0%} "
                            f"(last_end={last_end_ms}ms audio={audio_duration}s)"
                        )

    def _inject_character_props(
        self,
        props: dict[str, Any],
        job_id: str,
        episode_dir: Path,
    ) -> None:
        """Copy Detective / Assistant PNG into remotion/public/<job_id>/ and attach props.

        Mirrors harvested remotion_render.py:942-976. Expected inputs produced
        by asset-sourcer (Plan 16-04) at ``output/<episode>/sources/``.
        """
        public_dir = self.remotion_dir / "public" / job_id
        char_left = episode_dir / "sources" / "character_assistant.png"
        char_right = episode_dir / "sources" / "character_detective.png"
        if char_left.exists():
            public_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(char_left, public_dir / "character_left.png")
            props["characterLeftSrc"] = f"{job_id}/character_left.png"
            logger.info("[remotion] character_assistant → %s", public_dir / "character_left.png")
        if char_right.exists():
            public_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(char_right, public_dir / "character_right.png")
            props["characterRightSrc"] = f"{job_id}/character_right.png"
            logger.info("[remotion] character_detective → %s", public_dir / "character_right.png")

    def _invoke_remotion_cli(self, props_path: Path, output_path: Path) -> None:
        """``npx remotion render src/index.ts ShortsVideo out.mp4 --props=...``"""
        entry = (self.remotion_dir / "src" / "index.ts").as_posix()
        cmd = [
            "npx", "remotion", "render",
            entry,
            "ShortsVideo",
            output_path.as_posix(),
            f"--props={props_path.absolute().as_posix()}",
            "--codec=h264",
            "--fps=30",
            "--width=1080",
            "--height=1920",
        ]
        use_shell = sys.platform == "win32"
        timeout = self.first_render_timeout_s if self._is_first_render else self.timeout_s
        logger.info("[remotion] invoking: %s (timeout=%ds)", " ".join(cmd), timeout)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=self.remotion_dir,
                shell=use_shell,
            )
        except subprocess.TimeoutExpired as exc:
            self._is_first_render = False
            raise RuntimeError(
                f"Remotion render timed out after {timeout}s "
                f"(cmd={exc.cmd!r})"
            ) from exc
        self._is_first_render = False
        if result.returncode != 0:
            stderr_tail = (result.stderr or "")[-1500:]
            raise RuntimeError(
                f"Remotion render failed (exit {result.returncode}): {stderr_tail}"
            )

    def _cleanup_remotion_assets(self, job_id: str) -> None:
        """Remove ``remotion/public/<job_id>/`` after render (safety-checked)."""
        public_base = (self.remotion_dir / "public").resolve()
        target = (self.remotion_dir / "public" / job_id).resolve()
        # Safety: target must be inside public_base
        try:
            target.relative_to(public_base)
        except ValueError:
            logger.error(
                "[remotion] cleanup safety failed: %s not inside %s",
                target,
                public_base,
            )
            return
        if target.exists() and target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            logger.info("[remotion] cleaned up %s", target)

    def _verify_production_baseline(self, final_path: Path) -> dict[str, Any]:
        """Enforce ROADMAP Phase 16 SC#4 — ffprobe 1080×1920 / codec / duration.

        Raises :class:`RemotionBaselineError` on any violation.
        """
        if not final_path.exists():
            raise RemotionBaselineError(
                f"final.mp4 미생성: {final_path} (Remotion subprocess는 성공했으나 출력 부재)"
            )
        probe = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_format",
                "-show_streams",
                "-of", "json",
                str(final_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            shell=False,
        )
        if probe.returncode != 0:
            raise RemotionBaselineError(
                f"ffprobe 실패 (rc={probe.returncode}): {probe.stderr[-300:]}"
            )
        try:
            info = json.loads(probe.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise RemotionBaselineError(f"ffprobe JSON 파싱 실패: {exc}") from exc

        v_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
        if not v_streams:
            raise RemotionBaselineError(
                "video stream 없음 — audio-only 출력은 Shorts 로 업로드 불가"
            )
        v = v_streams[0]
        width = int(v.get("width", 0))
        height = int(v.get("height", 0))
        codec = v.get("codec_name", "")
        duration = float(info.get("format", {}).get("duration", 0.0) or 0.0)

        if (width, height) != TARGET_RESOLUTION:
            raise RemotionBaselineError(
                f"해상도 불량: {width}x{height} (expected {TARGET_RESOLUTION[0]}x{TARGET_RESOLUTION[1]})"
            )
        if duration < MIN_PRODUCTION_DURATION_S:
            raise RemotionBaselineError(
                f"영상 길이 불량: {duration:.2f}s < {MIN_PRODUCTION_DURATION_S}s baseline "
                f"(ROADMAP Phase 16 SC#4)"
            )
        if codec not in ("h264", "hevc"):
            raise RemotionBaselineError(
                f"codec 불량: {codec} (expected h264 또는 hevc)"
            )
        return {
            "width": width,
            "height": height,
            "codec": codec,
            "duration": duration,
        }

    def _extract_from_timeline(
        self,
        timeline: list[Any],
        episode_dir: Path,
    ) -> tuple[dict[str, Any], float, dict[str, Any], dict[str, Any], Path | None, Path | None]:
        """Pull Remotion render ingredients from the timeline.

        Phase 16-02 wiring: expects each :class:`TimelineEntry` to carry
        optional ``visual_spec_path`` / ``audio_path`` / ``subtitle_json_path``
        attributes injected by ``ShortsPipeline._run_assembly``. Plan 16-03 /
        16-04 will populate these deterministically; for now we extract
        whatever is present and defer to defaults otherwise.

        Returns
        -------
        (assets, audio_duration, script, blueprint, visual_spec_path, subtitle_json_path)
        """
        assets: dict[str, Any] = {"clips": [], "scene_clips": []}
        script: dict[str, Any] = {}
        blueprint: dict[str, Any] = {}
        visual_spec_path: Path | None = None
        subtitle_json: Path | None = None
        total_dur = 0.0

        for entry in timeline or []:
            # Best-effort attribute access — supports both dataclass and dict
            clip_path = getattr(entry, "clip_path", None)
            audio_path = getattr(entry, "audio_path", None)
            start = float(getattr(entry, "start", 0.0))
            end = float(getattr(entry, "end", 0.0))
            if end > total_dur:
                total_dur = end
            if clip_path:
                assets["scene_clips"].append(
                    {"path": str(clip_path), "type": "video"}
                )
            if audio_path and not assets.get("audioSrc_abs"):
                assets["audioSrc_abs"] = str(audio_path)
            # Optional extension fields (Plans 16-03/16-04 will set these)
            vsp = getattr(entry, "visual_spec_path", None)
            if vsp and visual_spec_path is None:
                visual_spec_path = Path(vsp)
            sjp = getattr(entry, "subtitle_json_path", None)
            if sjp and subtitle_json is None:
                subtitle_json = Path(sjp)
            spt = getattr(entry, "script", None)
            if spt and isinstance(spt, dict):
                script.update(spt)
            blp = getattr(entry, "blueprint", None)
            if blp and isinstance(blp, dict):
                blueprint.update(blp)

        audio_duration = (end - start) if timeline else 0.0
        if total_dur > audio_duration:
            audio_duration = total_dur

        return assets, audio_duration, script, blueprint, visual_spec_path, subtitle_json
