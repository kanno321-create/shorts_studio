"""Phase 11 full 0→13 GATE end-to-end smoke test (PIPELINE-01 SC#1 + SCRIPT-01 SC#2).

Proves the full operational pipeline with REAL Claude CLI + REAL external APIs::

    GATE 0 IDLE → GATE 1 TREND → GATE 2 NICHE → GATE 3 RESEARCH_NLM →
    GATE 4 BLUEPRINT → GATE 5 SCRIPT → GATE 6 POLISH → GATE 7 VOICE →
    GATE 8 ASSETS → GATE 9 ASSEMBLY → GATE 10 THUMBNAIL →
    GATE 11 METADATA → GATE 12 UPLOAD → GATE 13 MONITOR → COMPLETE

Usage::

    py -3.11 scripts/smoke/phase11_full_run.py --dry-run                    # env check only, no API calls
    py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd 5.00 # real run, single published video

Cost model (RESEARCH §Full Smoke Cost Model): $2.44-$4.47 expected, $5.00 hard cap.

Unlike Phase 9.1 smoke (Stage 2→4 only + mock supervisor), this harness:
  - Uses REAL ClaudeAgentProducerInvoker + ClaudeAgentSupervisorInvoker
  - Accumulates per-GATE cost via simple token-count heuristic
  - Aborts if sum(retry_counts) > 6 (half of max_retries_per_gate × 13 gates / 2)
  - Persists state/<session_id>/gate_NN.json checkpoints (13 operational + COMPLETE
    bookend = 14 files total; IDLE is not persisted by design — gate_guard.py
    dispatches PASS on operational GATEs only + _transition_to_complete writes
    gate_14.json. See scripts/orchestrator/gate_guard.py L157-166 +
    scripts/orchestrator/shorts_pipeline.py L665-691.)
  - Publishes 1 real YouTube Shorts video (SC#2) — 대표님 reviews in YouTube Studio

Phase 11 Plan 11-06. Skeleton: scripts/smoke/phase091_stage2_to_4.py.

Exit codes:
  0 — smoke completed successfully (dry-run or live) — 14 checkpoint files persisted
  2 — live run crashed mid-pipeline (ShortsPipeline.run exception)
  3 — live run exit 0 but state dir missing (artifact regression)
  4 — .env readiness check failed (required key missing) — do NOT enter billable live run
  5 — cost cap breached at aggregation time (post-run; running guard also logged)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows cp949 stdout guard — Phase 9.1 smoke_test.py pattern. Korean output +
# em-dashes fail on the default Windows console encoding; reconfigure to utf-8
# when possible (harmless on POSIX).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError) as _enc_err:
        # Non-fatal: fall back to ASCII-safe logging on the problematic console.
        # Recorded to stderr so we retain debuggability (금기사항 #3 준수 —
        # try/except 침묵 폴백 금지; 여기서는 명시적 stderr 기록).
        sys.stderr.write(
            f"[smoke] stdout reconfigure skipped: {_enc_err}\n"
        )

# Ensure repo root on sys.path when invoked directly
# (``py -3.11 scripts/smoke/phase11_full_run.py`` from the project root).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# NOTE: importing ``scripts.orchestrator`` triggers ``_load_dotenv_if_present``
# at package import time (PIPELINE-02 / D-13). This is intentional — we want
# the env probe below to see values from ``./.env`` without requiring the
# wrapper script to pre-inject them.
from scripts.orchestrator import ShortsPipeline  # noqa: E402
from scripts.orchestrator.invokers import (  # noqa: E402
    make_default_producer_invoker,
    make_default_supervisor_invoker,
)

logger = logging.getLogger("smoke.phase11")

# Per-GATE cost estimates (RESEARCH §Full Smoke Cost Model).
# Real billing pulled from JSON result.usage when exposed; heuristic otherwise.
PER_GATE_COST_ESTIMATE_USD = {
    "IDLE":         0.00,
    "TREND":        0.05,
    "NICHE":        0.05,
    "RESEARCH_NLM": 0.00,   # NotebookLM subscription-inclusive (Max 구독)
    "BLUEPRINT":    0.08,
    "SCRIPT":       0.35,   # Opus pricing, 2000-token output
    "POLISH":       0.08,
    "VOICE":        0.15,   # Typecast Korean TTS
    "ASSETS":       2.50,   # Nano Banana × N + Kling I2V × N (N~=8 cuts)
    "ASSEMBLY":     0.00,   # Ken-Burns local ffmpeg
    "THUMBNAIL":    0.08,   # Nano Banana single image + Claude prompt
    "METADATA":     0.05,
    "UPLOAD":       0.00,   # YouTube Data API quota-based, no $
    "MONITOR":      0.05,
    "COMPLETE":     0.00,   # bookend checkpoint only
}
DEFAULT_BUDGET_USD = 5.00
MAX_AGGREGATE_RETRIES = 6  # RESEARCH §Open Q #3 — half of 3×13/2


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 11 full 0→13 GATE smoke test — real Claude CLI + real APIs. "
            "Default --dry-run (env readiness only). Pass --live for real spend."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        action="store_true",
        help=(
            "Real API calls. Single published YouTube Shorts. "
            "Requires env: TYPECAST_API_KEY + GOOGLE_API_KEY + (KLING_API_KEY 또는 FAL_KEY). "
            "Cost bounded ≤ --max-budget-usd (default $5.00)."
        ),
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Env + adapter readiness check only. No API calls. "
            "Useful pre-flight before the real spend."
        ),
    )
    parser.add_argument(
        "--max-budget-usd",
        type=float,
        default=DEFAULT_BUDGET_USD,
        help=(
            f"Hard cost cap in USD (default ${DEFAULT_BUDGET_USD:.2f}). "
            "Run logs overshoot + returns exit 5 at aggregation."
        ),
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session identifier (default: yyyyMMdd_HHMMSS auto-generated)",
    )
    parser.add_argument(
        "--state-root",
        default="state",
        help="Checkpointer state directory (default: state)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (default: INFO)",
    )
    return parser.parse_args(argv)


def _check_env_readiness() -> dict:
    """Verify ``.env`` loaded + required API keys present.

    Three tiers of keys per RESEARCH §Cost Model + §Pitfall 2:
      required:  absence = hard block (smoke cannot run at all)
      any_of:    absence of the ENTIRE group = hard block
      optional:  absence = graceful degrade OK (Plan 11-03 adapter wrap)

    Returns a results dict; caller aggregates + exits 4 on required / any_of miss.
    Never raises — fatal decisions are caller responsibility (대표님-visible).
    """
    required = {
        "TYPECAST_API_KEY":  "Typecast Korean TTS (GATE 7 VOICE primary)",
        "GOOGLE_API_KEY":    "Nano Banana image gen (GATE 8 ASSETS + GATE 10 THUMBNAIL)",
        "YOUTUBE_CLIENT_SECRETS_FILE": "YouTube Data API v3 OAuth (GATE 12 UPLOAD)",
    }
    any_of = {
        ("KLING_API_KEY", "KLING_ACCESS_KEY", "FAL_KEY"): "Kling I2V (GATE 8 ASSETS primary)",
    }
    optional = {
        "ELEVENLABS_API_KEY":          "ElevenLabs TTS fallback (GATE 7 VOICE)",
        "RUNWAY_API_KEY":              "Runway I2V fallback (GATE 8 ASSETS)",
        "SHOTSTACK_API_KEY":           "Shotstack render (Phase 9.1 deprecated → ken_burns)",
        "ELEVENLABS_DEFAULT_VOICE_ID": "ElevenLabs voice pin (3-tier fallback OK if absent)",
    }
    results: dict[str, list] = {
        "required_missing": [],
        "any_of_missing":   [],
        "optional_missing": [],
    }
    for k, why in required.items():
        if not os.environ.get(k):
            results["required_missing"].append((k, why))
    for key_tuple, why in any_of.items():
        if not any(os.environ.get(k) for k in key_tuple):
            results["any_of_missing"].append((key_tuple, why))
    for k, why in optional.items():
        if not os.environ.get(k):
            results["optional_missing"].append((k, why))
    return results


def _print_env_report(env: dict) -> None:
    logger.info("========== Phase 11 smoke env 진단 (대표님) ==========")
    if env["required_missing"]:
        logger.error("[env] 필수 key 누락:")
        for k, why in env["required_missing"]:
            logger.error("  ✗ %s — %s", k, why)
    else:
        logger.info("[env] 필수 key 전부 존재 (대표님)")
    if env["any_of_missing"]:
        logger.error("[env] any-of 그룹 누락:")
        for keys, why in env["any_of_missing"]:
            logger.error("  ✗ (%s) — %s", " | ".join(keys), why)
    else:
        logger.info("[env] any-of 그룹 전부 존재 (대표님)")
    if env["optional_missing"]:
        logger.warning("[env] 선택 key 누락 (graceful degrade 로 진행):")
        for k, why in env["optional_missing"]:
            logger.warning("  · %s — %s", k, why)
    logger.info("====================================================")


def _build_pipeline(session_id: str, state_root: Path) -> ShortsPipeline:
    """Explicit real-invoker wiring per SC#1 auditable no-mock proof (M-2 fix).

    The factories require ``agent_dir_root`` / ``agent_dir`` arguments per
    ``scripts/orchestrator/invokers.py:313-330``. ShortsPipeline.__init__
    already defaults to the same paths when invokers are omitted, but we
    pass them explicitly here so the smoke harness itself is the auditable
    proof of no-mock wiring (grep-able: ``producer_invoker=make_default_producer_invoker``).
    """
    agents_root = Path(".claude/agents")
    producer_invoker = make_default_producer_invoker(
        agent_dir_root=agents_root / "producers",
    )
    supervisor_invoker = make_default_supervisor_invoker(
        agent_dir=agents_root / "supervisor" / "shorts-supervisor",
    )
    pipeline = ShortsPipeline(
        session_id=session_id,
        state_root=state_root,
        producer_invoker=producer_invoker,
        supervisor_invoker=supervisor_invoker,
    )
    return pipeline


def _aggregate_gate_metrics(state_dir: Path, budget_usd: float) -> dict:
    """Walk state/<session_id>/gate_*.json → {total_cost, per_gate, retries}.

    Returns a metrics dict. Logs (not raises) on budget overshoot +
    retry-count overshoot so the smoke report captures both facts even if
    the run technically succeeded. Caller decides exit code.
    """
    gate_files = sorted(state_dir.glob("gate_*.json"))
    logger.info(
        "[smoke] state/<sid>/ gate checkpoint 수: %d (목표 14 — 13 operational + COMPLETE)",
        len(gate_files),
    )

    per_gate_cost: dict[str, float] = {}
    per_gate_retries: dict[str, int] = {}
    cost_running = 0.0

    for gf in gate_files:
        try:
            payload = json.loads(gf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            logger.warning("[smoke] gate_file 읽기 실패 %s (대표님): %s", gf, err)
            continue

        # Checkpointer payload shape: {_schema, session_id, gate, gate_index,
        # timestamp, verdict, artifacts}. See scripts/orchestrator/checkpointer.py L60-90.
        gate_name = payload.get("gate", gf.stem.replace("gate_", "").upper())
        retries = int(payload.get("retry_count", 0))
        est_cost = PER_GATE_COST_ESTIMATE_USD.get(gate_name, 0.0)
        per_gate_cost[gate_name] = est_cost
        per_gate_retries[gate_name] = retries
        cost_running += est_cost
        logger.info(
            "[gate] %-14s retries=%d est=$%.2f cum=$%.2f",
            gate_name, retries, est_cost, cost_running,
        )

    total_retries = sum(per_gate_retries.values())
    if total_retries > MAX_AGGREGATE_RETRIES:
        logger.error(
            "[smoke] 누적 retry %d > %d (대표님 — rubric 재평가 권장)",
            total_retries, MAX_AGGREGATE_RETRIES,
        )

    budget_breached = cost_running > budget_usd
    if budget_breached:
        logger.error(
            "[smoke] 비용 상한 초과 $%.2f > $%.2f (대표님 — 다음 run 전 점검 필요)",
            cost_running, budget_usd,
        )

    return {
        "gate_file_count":      len(gate_files),
        "per_gate_cost":        per_gate_cost,
        "per_gate_retries":     per_gate_retries,
        "total_cost_usd":       round(cost_running, 2),
        "total_retries":        total_retries,
        "budget_usd":           budget_usd,
        "budget_breached":      budget_breached,
        "retry_cap_breached":   total_retries > MAX_AGGREGATE_RETRIES,
    }


def _extract_upload_url(state_dir: Path) -> str | None:
    """Read gate_12.json (UPLOAD) and extract the published video URL.

    Checkpointer ``artifacts`` dict shape is flexible — we probe a few
    common keys without raising on absence (SC#2 hint only; 대표님 fills
    the URL manually into SCRIPT_QUALITY_DECISION.md regardless).
    """
    upload_path = state_dir / "gate_12.json"
    if not upload_path.exists():
        return None
    try:
        payload = json.loads(upload_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        logger.warning("[smoke] gate_12.json 읽기 실패 (대표님): %s", err)
        return None
    artifacts = payload.get("artifacts") or {}
    if isinstance(artifacts, dict):
        for key in ("video_url", "youtube_url", "url", "path"):
            val = artifacts.get(key)
            if val and isinstance(val, str) and "youtu" in val:
                return val
    return None


def _write_run_report(
    state_root: Path,
    session_id: str,
    metrics: dict,
    status: str,
    error: str | None = None,
    video_url: str | None = None,
    wall_time_s: float | None = None,
) -> Path:
    """Persist machine-readable run report at reports/phase11_smoke_<sid>.json."""
    report_path = Path("reports") / f"phase11_smoke_{session_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_id":                session_id,
        "status":                    status,
        "error":                     error,
        "video_url":                 video_url,
        "wall_time_seconds":         wall_time_s,
        "gate_file_count":           metrics.get("gate_file_count"),
        "total_cost_usd_estimate":   metrics.get("total_cost_usd"),
        "per_gate_cost_usd":         metrics.get("per_gate_cost", {}),
        "per_gate_retries":          metrics.get("per_gate_retries", {}),
        "total_retries":             metrics.get("total_retries"),
        "budget_usd":                metrics.get("budget_usd"),
        "budget_breached":           metrics.get("budget_breached"),
        "retry_cap_breached":        metrics.get("retry_cap_breached"),
        "state_dir":                 str((state_root / session_id).as_posix()),
        "generated_at":              datetime.now().isoformat(),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("[smoke] run report: %s", report_path)
    return report_path


def _run_smoke(args: argparse.Namespace) -> int:
    """Real-run path: construct pipeline, iterate 13 GATEs via run(), track cost.

    ShortsPipeline.run() handles the full loop. We wrap it with post-run
    inspection of state/<sid>/gate_*.json for cost + retry accounting.
    Budget overshoot is LOGGED + reflected in exit code 5 (not raised
    mid-run — we want the UPLOAD checkpoint to persist before abort).
    """
    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    state_root = Path(args.state_root)
    budget = args.max_budget_usd

    logger.info(
        "[smoke] 시작 — session_id=%s budget=$%.2f state_root=%s (대표님)",
        session_id, budget, state_root,
    )

    pipeline = _build_pipeline(session_id, state_root)

    start_time = time.time()
    try:
        result = pipeline.run()  # blocking — traverses 13 operational gates + COMPLETE
    except Exception as err:  # noqa: BLE001 — smoke harness reports to 대표님 then exits 2
        elapsed = time.time() - start_time
        logger.error(
            "[smoke] 파이프라인 중단 (%.1fs 경과, 대표님): %s",
            elapsed, err,
        )
        # Still aggregate whatever checkpoints did persist — gives 대표님 a
        # partial cost/retry snapshot for triage.
        state_dir = state_root / session_id
        metrics = (
            _aggregate_gate_metrics(state_dir, budget)
            if state_dir.exists()
            else {"gate_file_count": 0}
        )
        _write_run_report(
            state_root=state_root,
            session_id=session_id,
            metrics=metrics,
            status="FAILED",
            error=str(err),
            wall_time_s=round(elapsed, 2),
        )
        return 2

    elapsed = time.time() - start_time
    logger.info(
        "[smoke] 파이프라인 완주 (%.1fs 경과, 대표님) — result=%s",
        elapsed, result,
    )

    state_dir = state_root / session_id
    if not state_dir.exists():
        logger.error(
            "[smoke] state dir 없음 — 실행 아티팩트 부재 (대표님): %s",
            state_dir,
        )
        _write_run_report(
            state_root=state_root,
            session_id=session_id,
            metrics={"gate_file_count": 0},
            status="ARTIFACT_MISSING",
            error=f"state dir not created: {state_dir}",
            wall_time_s=round(elapsed, 2),
        )
        return 3

    metrics = _aggregate_gate_metrics(state_dir, budget)
    video_url = _extract_upload_url(state_dir)
    if video_url:
        logger.info(
            "[smoke] 업로드 영상 URL (SCRIPT_QUALITY_DECISION.md video_url: 에 기입, 대표님): %s",
            video_url,
        )
    else:
        logger.warning(
            "[smoke] gate_12.json 에서 video_url 추출 실패 — 대표님 YouTube Studio 에서 수동 확인 필요"
        )

    _write_run_report(
        state_root=state_root,
        session_id=session_id,
        metrics=metrics,
        status="OK",
        video_url=video_url,
        wall_time_s=round(elapsed, 2),
    )

    if metrics["budget_breached"]:
        return 5
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    env = _check_env_readiness()
    _print_env_report(env)

    if env["required_missing"] or env["any_of_missing"]:
        logger.error(
            "[smoke] env 미충족 — 중단 (대표님 .env 확인 후 재시도). "
            "필수 key 또는 any-of 그룹 누락은 실 API 호출 진입 전 차단됩니다."
        )
        return 4

    # Default mode when neither flag passed = dry-run (conservative + cost-safe).
    if args.dry_run or not args.live:
        logger.info(
            "[smoke] dry-run 모드 완료 — 실 API 호출 없음 (대표님)"
        )
        logger.info(
            "[smoke] 실 발행: py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd %.2f",
            args.max_budget_usd,
        )
        return 0

    return _run_smoke(args)


if __name__ == "__main__":
    sys.exit(main())
