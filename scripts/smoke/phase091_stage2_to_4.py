"""Phase 9.1 Stage 2→4 smoke test (REQ-091-07).

Proves the Wave 1 adapter chain end-to-end::

    CharacterRegistry → NanoBananaAdapter → KlingI2VAdapter → MP4
                                          → VeoI2VAdapter (optional fallback)

Usage::

    python scripts/smoke/phase091_stage2_to_4.py --dry-run    # default, zero cost
    python scripts/smoke/phase091_stage2_to_4.py --live       # Kling 2.6 Pro, real API
    python scripts/smoke/phase091_stage2_to_4.py --live --use-veo  # Veo 3.1 Fast fallback

Cost cap (09.1-CONTEXT.md D-15): $1.00. Breaks early on overshoot with
Korean ``RuntimeError`` (CircuitBreaker-style abort). See
``.planning/phases/09.1-production-engine-wiring/09.1-06-stage2-4-smoke-PLAN.md``.

**2026-04-20 세션 #24 final stack**:
    Primary  = Kling 2.6 Pro ($0.35/5s, fal.ai kling-video/v2.6/pro)
    Fallback = Veo 3.1 Fast  ($0.50/5s, fal.ai veo3.1/fast) — 정밀/세세한
               motion 실패 시 대표님 지침에 따라 수동 --use-veo 플래그로 전환.
               auto-route 는 Phase 10 실패 패턴 축적 후 정식화 (Phase 9.1 out-of-scope).

Motion prompt 는 memory ``feedback_i2v_prompt_principles`` Template A
(3원칙 적용: camera lock / positive anatomy persistence / micro verb).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

# Windows cp949 stdout guard — Phase 8 smoke_test.py pattern. The Korean
# output + em-dash combinations fail on the default Windows console
# encoding; reconfigure to utf-8 when possible (harmless on POSIX).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError) as _enc_err:  # pragma: no cover
        # Non-fatal: fall back to ASCII-safe logging on the problematic
        # console. Recorded to stderr so we retain debuggability (Hook
        # 3종: NOT a silent except — error is surfaced).
        sys.stderr.write(
            f"[smoke] stdout reconfigure skipped: {_enc_err}\n"
        )

# Ensure repo root on sys.path when invoked directly
# (``python scripts/smoke/phase091_stage2_to_4.py`` from the project root).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.orchestrator.character_registry import CharacterRegistry  # noqa: E402

logger = logging.getLogger(__name__)

COST_CAP_USD = 1.00
NANOBANANA_COST_USD = 0.04
KLING_26_PRO_5S_COST_USD = 0.35  # fal.ai kling-video/v2.6/pro/image-to-video, 2026-04 실측
VEO_31_FAST_5S_COST_USD = 0.50   # fal.ai veo3.1/fast/image-to-video, $0.10/s × 5s

SCENE_PROMPT = (
    "Reference the character in the attached image. Generate a hyperrealistic "
    "9:16 vertical photograph of the SAME character in a modern Korean studio: "
    "warm natural lighting from left, holding a white ceramic coffee cup, "
    "warm smile looking slightly off-camera, shallow depth of field. "
    "Shot on ARRI Alexa Mini, film grain. No AI-generated look."
)

# Template A from memory ``feedback_i2v_prompt_principles`` — 27단어, 3원칙 전부 적용:
#   1) Camera lock 명시       ("The camera holds still")
#   2) Anatomy positive persistence ("both hands remaining on the mug")
#   3) Micro verb             ("gently brings ... toward her lips")
# 세션 #24 3-way 실측에서 Kling 2.6 Pro + Gen-4.5 둘 다 합격. Gen-3a Turbo 만 실패.
MOTION_PROMPT = (
    "The camera holds still as she gently brings the cup upward toward her lips, "
    "both hands remaining on the mug. Her smile stays soft and natural throughout."
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 9.1 Stage 2→4 smoke test "
            "(Nano Banana → Kling 2.6 Pro | Veo 3.1 Fast)."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="No API calls. Placeholder outputs. Default mode.",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help=(
            "Real API calls. Requires GOOGLE_API_KEY + (KLING_API_KEY 또는 FAL_KEY). "
            "--use-veo 추가 시 VEO_API_KEY 또는 FAL_KEY 필요. "
            "Cost bounded ≤ $1.00 (D-15)."
        ),
    )
    parser.add_argument(
        "--use-veo",
        action="store_true",
        help=(
            "Veo 3.1 Fast fallback adapter 사용 (정밀/세세한 motion 수동 선택). "
            "기본은 Kling 2.6 Pro primary. auto-route 은 Phase 10 소관."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="output/phase091_smoke",
        help="Output directory for scene PNG, clip MP4, manifest JSON.",
    )
    parser.add_argument(
        "--anchor-name",
        default="channel_profile",
        help="Character registry entry name to use as the I2V anchor.",
    )
    return parser.parse_args(argv)


def _resolve_anchor(anchor_name: str) -> Path:
    """Load the character registry and return the anchor image Path.

    Raises ``FileNotFoundError`` (Korean) if registry is missing OR the
    anchor entry is missing OR the referenced file does not exist.
    """
    registry = CharacterRegistry().load()
    path = registry.get_reference_path(anchor_name)
    if not path.exists():
        raise FileNotFoundError(
            f"'{anchor_name}' 캐릭터 레퍼런스 누락: {path} (대표님)"
        )
    return path


def _check_cost_cap(total_usd: float) -> None:
    """Raise a Korean ``RuntimeError`` if cumulative cost exceeds the cap.

    Called BEFORE each additional API call so overshoot is intercepted
    before money is spent on the next stage (D-15 CircuitBreaker pattern).
    """
    if total_usd > COST_CAP_USD:
        raise RuntimeError(
            f"비용 상한 초과 (대표님): ${total_usd:.2f} > ${COST_CAP_USD:.2f} — "
            f"CircuitBreaker open, 추가 호출 중단"
        )


def _require_env(keys: tuple[str, ...]) -> None:
    """Fail fast (Korean ValueError) if ALL env keys in the tuple are missing.

    The tuple is treated as alternates (any one satisfies the requirement),
    matching how the Kling / Veo adapters resolve ``KLING_API_KEY`` OR
    ``FAL_KEY``.
    """
    if not any(os.environ.get(k) for k in keys):
        joined = " 또는 ".join(keys)
        raise ValueError(f"{joined} 미설정 — 대표님 .env 확인 필요")


def _run_dry(
    output_dir: Path,
    anchor: Path,
    use_veo: bool,
) -> dict:
    """Dry-run: write placeholders, no API cost, no SDK import."""
    scene_placeholder = output_dir / "scene_placeholder.png"
    clip_placeholder = output_dir / "clip_placeholder.mp4"
    shutil.copy(anchor, scene_placeholder)
    clip_placeholder.write_bytes(b"")  # zero-byte placeholder OK
    return {
        "mode": "dry-run",
        "timestamp": int(time.time()),
        "anchor_path": str(anchor),
        "scene_path": str(scene_placeholder),
        "clip_path": str(clip_placeholder),
        "scene_prompt": SCENE_PROMPT,
        "motion_prompt": MOTION_PROMPT,
        "i2v_provider": "veo3.1-fast" if use_veo else "kling2.6-pro",
        "nanobanana_cost_usd": 0.0,
        "i2v_cost_usd": 0.0,
        "total_usd": 0.0,
        "cost_cap_usd": COST_CAP_USD,
    }


def _run_live(
    output_dir: Path,
    anchor: Path,
    use_veo: bool,
) -> dict:
    """Live: real Nano Banana + (Kling 2.6 Pro | Veo 3.1 Fast) calls.

    Lazy-imports the adapter modules so ``--dry-run`` on a system without
    google-genai / fal-client still exits 0.
    """
    _require_env(("GOOGLE_API_KEY",))
    # Both Kling and Veo adapters accept FAL_KEY as fallback for their
    # respective primary env vars.
    if use_veo:
        _require_env(("VEO_API_KEY", "FAL_KEY"))
    else:
        _require_env(("KLING_API_KEY", "FAL_KEY"))

    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter  # noqa: E402

    scene_path = output_dir / "scene.png"
    clip_path = output_dir / "clip.mp4"
    total_usd = 0.0

    # ------------------------------------------------------------------
    # Stage 2 — Nano Banana Pro scene generation.
    # ------------------------------------------------------------------
    logger.info("[smoke] Stage 2 — Nano Banana generate_scene 시작")
    nanobanana = NanoBananaAdapter()
    nanobanana.generate_scene(SCENE_PROMPT, output_path=scene_path)
    total_usd += NANOBANANA_COST_USD
    _check_cost_cap(total_usd)

    if not scene_path.exists() or scene_path.stat().st_size < 1024:
        size = scene_path.stat().st_size if scene_path.exists() else 0
        raise RuntimeError(
            f"Nano Banana 출력 scene.png 너무 작음 (대표님): {size} bytes"
        )

    logger.info(
        "[smoke] Stage 2 완료 — scene.png %.1f KB, 누적 $%.2f",
        scene_path.stat().st_size / 1024,
        total_usd,
    )

    # ------------------------------------------------------------------
    # Stage 4 — I2V clip generation (Kling 2.6 Pro primary | Veo 3.1 Fast).
    # ------------------------------------------------------------------
    if use_veo:
        from scripts.orchestrator.api.veo_i2v import VeoI2VAdapter  # noqa: E402

        logger.info(
            "[smoke] Stage 4 — Veo 3.1 Fast image_to_video 시작 (수동 fallback)"
        )
        adapter = VeoI2VAdapter()
        i2v_cost = VEO_31_FAST_5S_COST_USD
        provider = "veo3.1-fast"
    else:
        from scripts.orchestrator.api.kling_i2v import KlingI2VAdapter  # noqa: E402

        logger.info(
            "[smoke] Stage 4 — Kling 2.6 Pro image_to_video 시작 (primary)"
        )
        adapter = KlingI2VAdapter()
        i2v_cost = KLING_26_PRO_5S_COST_USD
        provider = "kling2.6-pro"

    raw_clip = adapter.image_to_video(
        prompt=MOTION_PROMPT,
        anchor_frame=scene_path,
        duration_seconds=5,
    )
    total_usd += i2v_cost
    _check_cost_cap(total_usd)

    if not raw_clip.exists() or raw_clip.stat().st_size < 100 * 1024:
        size = raw_clip.stat().st_size if raw_clip.exists() else 0
        raise RuntimeError(
            f"{provider} 출력 MP4 너무 작음 (대표님): {size} bytes"
        )

    # Consolidate the adapter's outputs/<provider>/ download under the smoke dir.
    shutil.move(str(raw_clip), str(clip_path))
    logger.info(
        "[smoke] Stage 4 완료 — clip.mp4 %.1f KB, 누적 $%.2f",
        clip_path.stat().st_size / 1024,
        total_usd,
    )

    return {
        "mode": "live",
        "timestamp": int(time.time()),
        "anchor_path": str(anchor),
        "scene_path": str(scene_path),
        "clip_path": str(clip_path),
        "scene_prompt": SCENE_PROMPT,
        "motion_prompt": MOTION_PROMPT,
        "i2v_provider": provider,
        "nanobanana_cost_usd": NANOBANANA_COST_USD,
        "i2v_cost_usd": i2v_cost,
        "total_usd": total_usd,
        "cost_cap_usd": COST_CAP_USD,
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    args = _parse_args(argv)

    # argparse mutex guarantees at most one of dry-run / live is set.
    mode_live = args.live
    mode_dry = args.dry_run or not args.live

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    anchor = _resolve_anchor(args.anchor_name)

    if mode_live:
        logger.info(
            "[smoke] --live mode — real API calls 시작 (cost cap $%.2f, provider=%s)",
            COST_CAP_USD,
            "veo3.1-fast" if args.use_veo else "kling2.6-pro",
        )
        t0 = time.time()
        manifest = _run_live(output_dir, anchor, use_veo=args.use_veo)
        manifest["wall_time_seconds"] = round(time.time() - t0, 2)
    else:
        logger.info("[smoke] --dry-run mode — placeholder outputs (cost 0)")
        assert mode_dry  # invariant: one of the two modes must be active
        manifest = _run_dry(output_dir, anchor, use_veo=args.use_veo)
        manifest["wall_time_seconds"] = 0.0

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"Smoke test 완료 (대표님) — 다음 경로에서 재생 가능합니다:\n"
        f"  scene:    {manifest['scene_path']}\n"
        f"  clip:     {manifest['clip_path']}\n"
        f"  provider: {manifest['i2v_provider']}\n"
        f"  manifest: {manifest_path}\n"
        f"  총 비용:  ${manifest['total_usd']:.2f} "
        f"(상한 ${COST_CAP_USD:.2f})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
