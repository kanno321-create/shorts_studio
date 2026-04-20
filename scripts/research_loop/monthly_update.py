"""Monthly research loop — KPI-03 / KPI-04 / SC#5 (Phase 10 Plan 10-06).

이전 월 KPI aggregate 결과와 NotebookLM retrospective 답변을 결합해
``wiki/kpi/monthly_context_YYYY-MM.md`` 를 생성합니다. 다음 월 Producer
입력에 KPI 를 자동 반영하기 위한 학습 회로의 코드 레벨 인프라입니다.

3-tier fallback chain (RESEARCH.md §Plan 6 Open Q4):

    T0 happy path  : aggregate ≥ 1 video AND NotebookLM rc=0
    T1 nlm fail    : aggregate ≥ 1 video AND NotebookLM 실패
                     → 이전 월 monthly_context 재사용 + 재사용 헤더 주입
    T2 no data     : aggregate = 0 videos AND NotebookLM success
                     → empty context 생성 + FAILURES.md F-KPI-NN append
    T3 both fail   : aggregate = 0 videos AND NotebookLM 실패
                     → exit 1 + FAILURES.md F-KPI-NN append + stderr alert
                     (대표님께 수동 점검 pivot)

Pitfall 6 (RESEARCH §Plan 6): NotebookLM source 추가 API 는 미공개이므로
이 스크립트는 .md 파일만 생성하며 실 NotebookLM 업로드는 대표님이 브라우저로
월 1회 수동 수행해야 합니다. 이를 stdout reminder 로 dispatch 합니다.

Usage::

    # 이전 월을 자동 결정 (KST 기준)
    python -m scripts.research_loop.monthly_update

    # 명시적 month + dry-run
    NOTEBOOK_ID=shorts-production-pipeline-bible \
      python -m scripts.research_loop.monthly_update \
          --year-month 2026-04 --dry-run

    # 기존 파일 무시하고 재생성
    python -m scripts.research_loop.monthly_update \
        --year-month 2026-04 --force
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Windows cp949 stdout 가드 — 한국어 NotebookLM 응답 round-trip.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- constants
KST = ZoneInfo("Asia/Seoul")
DEFAULT_NLM_SKILL = Path("C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm")

# Plan 10-03 Rule 1 deviation: frontmatter 의 wiki/shorts/kpi/ 는 stale,
# 실 파일은 wiki/kpi/ 에 존재 (Phase 9 Plan 09-02 생성 위치). Plan 10-03 의 path
# 조정과 일관되게 wiki/kpi/ 를 primary 로 사용합니다.
DEFAULT_WIKI_DIR = Path("wiki/kpi")
DEFAULT_TEMPLATE = DEFAULT_WIKI_DIR / "monthly_context_template.md"
DEFAULT_LATEST_COPY_NAME = "monthly_context_latest.md"
DEFAULT_FAILURES = Path("FAILURES.md")

# Shared helper from Plan 10-03 — composite_score + aggregate_month 재사용.
# (RESEARCH §Plan 6 Open Q2 — shared weights 0.5/0.3/0.2)
from scripts.analytics.monthly_aggregate import aggregate_month, composite_score

__all__ = [
    "KST",
    "DEFAULT_NLM_SKILL",
    "DEFAULT_WIKI_DIR",
    "DEFAULT_TEMPLATE",
    "previous_year_month",
    "top_n_by_composite",
    "render_top_3_table",
    "render_avoidance",
    "query_notebook",
    "render_context",
    "find_previous_context",
    "append_failures_kpi",
    "main",
    "composite_score",  # re-export for import convenience
    "aggregate_month",
]


# ---------------------------------------------------------------- helpers

def previous_year_month(now: datetime) -> str:
    """Return ``YYYY-MM`` for the month before ``now`` (KST-naive arithmetic)."""
    if now.month == 1:
        return f"{now.year - 1}-12"
    return f"{now.year}-{now.month - 1:02d}"


def top_n_by_composite(
    videos: dict[str, dict],
    n: int = 3,
) -> list[tuple[str, dict]]:
    """Return ``n`` videos sorted by composite score descending.

    Missing composite keys default to 0.0 (safe for partial metric dicts).
    """
    return sorted(
        videos.items(),
        key=lambda kv: kv[1].get("composite", 0.0),
        reverse=True,
    )[:n]


def _bottom_n_by_composite(
    videos: dict[str, dict],
    n: int = 3,
) -> list[tuple[str, dict]]:
    """Return ``n`` videos sorted by composite score ascending (worst first)."""
    return sorted(
        videos.items(),
        key=lambda kv: kv[1].get("composite", 0.0),
    )[:n]


def render_top_3_table(top: list[tuple[str, dict]]) -> str:
    """Render markdown table rows for Top-N videos.

    Returns a ``| (no data) | ... |`` single-row fallback when ``top`` is empty,
    preserving the markdown table shape for downstream parsers.
    """
    if not top:
        return (
            "| video_id | 3s_retention | completion | avg_view_s | composite |\n"
            "|----------|--------------|------------|------------|-----------|\n"
            "| _(no data)_ | _ | _ | _ | _ |"
        )
    lines = [
        "| video_id | 3s_retention | completion | avg_view_s | composite |",
        "|----------|--------------|------------|------------|-----------|",
    ]
    for vid, m in top:
        lines.append(
            f"| `{vid}` | {float(m.get('retention_3s', 0) or 0):.3f} "
            f"| {float(m.get('completion_rate', 0) or 0):.3f} "
            f"| {float(m.get('avg_view_sec', 0) or 0):.1f} "
            f"| {float(m.get('composite', 0) or 0):.3f} |"
        )
    return "\n".join(lines)


def render_avoidance(bottom: list[tuple[str, dict]]) -> str:
    """Render the Part 3 avoidance block from bottom-N videos."""
    if not bottom:
        return "_하위 영상 데이터 부족 — 다음 월 aggregate 완료 시 채워집니다._"
    lines = ["아래 영상들의 공통 패턴을 다음 달에 회피합니다:"]
    for vid, m in bottom:
        lines.append(
            f"- `{vid}`: composite={float(m.get('composite', 0) or 0):.3f}, "
            f"retention_3s={float(m.get('retention_3s', 0) or 0):.3f}, "
            f"completion={float(m.get('completion_rate', 0) or 0):.3f}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------- NotebookLM

def query_notebook(
    question: str,
    notebook_id: str,
    nlm_skill: Path = DEFAULT_NLM_SKILL,
    timeout: int = 120,
) -> tuple[str, bool]:
    """Query NotebookLM via shorts_naberal skill subprocess.

    Returns ``(answer, success)``. Graceful-fail on every error path — no
    exception propagates (RESEARCH §Plan 6 Open Q1, 3-tier fallback 전제).

    Args:
        question: Natural-language Korean query routed to NotebookLM.
        notebook_id: Registered notebook id from ``library.json`` (e.g.
            ``shorts-production-pipeline-bible``).
        nlm_skill: Path to shorts_naberal NotebookLM skill dir.
        timeout: Seconds before the subprocess is killed.

    Returns:
        ``(stdout_or_stderr, success_bool)``. On success, ``answer`` is the
        raw stdout of ``ask_question.py`` (NotebookLM's summary text). On any
        failure, ``answer`` carries the diagnostic string for downstream
        fallback headers.
    """
    run_py = nlm_skill / "scripts" / "run.py"
    if not run_py.exists():
        return (f"NotebookLM skill run.py not found at {run_py}", False)
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(run_py),
                "ask_question.py",
                "--question",
                question,
                "--notebook-id",
                notebook_id,
            ],
            cwd=str(nlm_skill),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return (f"NotebookLM query timed out after {timeout}s", False)
    except FileNotFoundError as exc:
        return (f"NotebookLM skill path invalid: {exc}", False)
    except OSError as exc:  # pragma: no cover — defensive, subprocess spawn
        return (f"NotebookLM subprocess OSError: {exc}", False)

    if result.returncode != 0:
        diag = (result.stderr or result.stdout or "").strip()
        return (diag or f"NotebookLM exit {result.returncode}", False)
    return (result.stdout, True)


# ---------------------------------------------------------------- rendering

def render_context(
    template_text: str,
    year_month: str,
    videos: dict[str, dict],
    nlm_answer: str,
    fallback_tier: int,
    notebook_id: str,
    now: datetime,
) -> str:
    """Apply the 8 template placeholders and return the rendered markdown."""
    top = top_n_by_composite(videos, n=3)
    bottom = _bottom_n_by_composite(videos, n=3)
    top_table = render_top_3_table(top)

    clean_answer = (nlm_answer or "").strip()
    if fallback_tier == 0:
        success_patterns = clean_answer or "_(NotebookLM returned empty)_"
    elif fallback_tier == 1:
        success_patterns = (
            "_이전 달 monthly_context 재사용 — NotebookLM query 실패 (3-tier T1 fallback)_\n\n"
            + clean_answer[:1200]
        )
    else:
        success_patterns = (
            "_데이터 부족 — 다음 월 aggregate 완료 시 재생성됩니다._\n\n"
            f"(fallback_tier={fallback_tier})"
        )

    avoidance = render_avoidance(bottom)
    source_ids = ", ".join(f"`{vid}`" for vid, _ in top) if top else "(none)"

    return template_text.format(
        GENERATED_AT=now.isoformat(),
        YEAR_MONTH=year_month,
        TOP_3_TABLE=top_table,
        SUCCESS_PATTERNS=success_patterns,
        AVOIDANCE=avoidance,
        SOURCE_VIDEO_IDS=source_ids,
        NOTEBOOK_ID=notebook_id,
        FALLBACK_TIER=fallback_tier,
    )


# ---------------------------------------------------------------- fallback T1

def find_previous_context(wiki_dir: Path, year_month: str) -> Path | None:
    """Find the immediately preceding ``monthly_context_YYYY-MM.md`` on disk."""
    try:
        y_str, m_str = year_month.split("-", 1)
        y = int(y_str)
        m = int(m_str) - 1
    except ValueError:
        return None
    if m == 0:
        m = 12
        y -= 1
    candidate = wiki_dir / f"monthly_context_{y}-{m:02d}.md"
    return candidate if candidate.exists() else None


# ---------------------------------------------------------------- fallback T2/T3

_FAILURES_KPI_RE = re.compile(r"###\s+F-KPI-(\d{2,})")


def append_failures_kpi(
    failures: Path,
    reason: str,
    year_month: str,
    now: datetime,
) -> str:
    """Append an ``F-KPI-NN`` entry to FAILURES.md.

    Uses direct ``open("a", ...)`` — this bypasses Claude Write hook by design
    (the hook only watches Claude tool invocations, not Python I/O). Entry id
    monotonically increments from the highest existing ``F-KPI-NN`` heading;
    returns ``"(FAILURES.md missing — skipped append)"`` if the file does not
    exist yet (callers treat this as non-fatal).

    Args:
        failures: Path to ``FAILURES.md``.
        reason: Short incident description (Korean OK).
        year_month: ``YYYY-MM`` context for the entry header.
        now: current ``datetime`` (KST); only the date is emitted.

    Returns:
        The assigned ``F-KPI-NN`` id, or a skip-reason string.
    """
    if not failures.exists():
        return "(FAILURES.md missing — skipped append)"

    existing = failures.read_text(encoding="utf-8", errors="replace")
    ids = _FAILURES_KPI_RE.findall(existing)
    next_id = max((int(i) for i in ids), default=0) + 1
    entry_id = f"F-KPI-{next_id:02d}"

    body = [
        "",
        "",
        f"## {entry_id} — Research Loop 실패 ({now.date().isoformat()}, {year_month})",
        "",
        f"**증상**: {reason}",
        "",
        "**조치**:",
        "1. `scripts/analytics/monthly_aggregate.py --year-month <prev>` 직접 실행 + 데이터 유무 확인",
        "2. YouTube Analytics API 인증 상태 확인 (scope 재인증 필요 시 Plan 10-03 Wave 0 참조)",
        "3. NotebookLM browser session 만료 확인 (대표님 수동 로그인 + library 재연결)",
        "4. `.planning/phases/10-sustained-operations/ROLLBACK.md` 학습 회로 오염 시나리오 참조",
        "",
        f"**자동 생성**: scripts.research_loop.monthly_update (fallback_tier 2 or 3, year_month={year_month})",
    ]
    with failures.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(body) + "\n")
    return entry_id


# ---------------------------------------------------------------- CLI

def _build_question(year_month: str) -> str:
    return (
        f"지난 {year_month} 기간 상위 retention 및 completion 영상들의 공통 성공 패턴을 "
        "세 가지로 요약해 주세요 (훅 / 페르소나 / 음성 페이스)."
    )


def _build_reminder(year_month: str, target: Path) -> str:
    return (
        f"[REMINDER to 대표님] {year_month} monthly_context 파일이 생성됐습니다. "
        f"NotebookLM 에 {target.name} 을 수동 업로드하여 다음 월 Producer 의 RAG 에 "
        "반영해 주시기 바랍니다. (Pitfall 6: NotebookLM source add API 미공개로 자동화 불가)"
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts.research_loop.monthly_update",
        description="Monthly research loop — KPI-03/04 (Phase 10 Plan 10-06)",
    )
    parser.add_argument(
        "--year-month",
        default=None,
        help="YYYY-MM (default: previous month in KST)",
    )
    parser.add_argument(
        "--daily-dir",
        type=Path,
        default=Path("data/kpi_daily"),
        help="Directory containing daily CSVs from scripts.analytics.fetch_kpi",
    )
    parser.add_argument(
        "--wiki-dir",
        type=Path,
        default=DEFAULT_WIKI_DIR,
        help="Target directory for monthly_context_*.md",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help="Path to monthly_context_template.md",
    )
    parser.add_argument(
        "--nlm-skill",
        type=Path,
        default=DEFAULT_NLM_SKILL,
        help="Path to shorts_naberal/.claude/skills/notebooklm",
    )
    parser.add_argument(
        "--notebook-id",
        default=os.environ.get("NOTEBOOK_ID"),
        help="Registered notebook id (default: $NOTEBOOK_ID env var)",
    )
    parser.add_argument(
        "--failures",
        type=Path,
        default=DEFAULT_FAILURES,
        help="Path to FAILURES.md for T2/T3 append-on-fail",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute + print JSON summary, do NOT mutate wiki or FAILURES",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even when monthly_context_YYYY-MM.md already exists",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="NotebookLM subprocess timeout in seconds",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Returns exit code (0 OK, 1 fail T3, 2 usage)."""
    args = _parse_args(argv)

    now = datetime.now(KST)
    ym = args.year_month or previous_year_month(now)
    target = args.wiki_dir / f"monthly_context_{ym}.md"
    latest_copy = args.wiki_dir / DEFAULT_LATEST_COPY_NAME

    # Idempotent skip — Plan requirement Test 11.
    if target.exists() and not args.force and not args.dry_run:
        summary = {
            "year_month": ym,
            "skipped": True,
            "target": str(target),
            "reason": "file exists — pass --force to regenerate",
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.notebook_id is None:
        print(
            "[ERROR] --notebook-id or NOTEBOOK_ID env var required "
            "(shorts_naberal library.json entry id — e.g. "
            "'shorts-production-pipeline-bible')",
            file=sys.stderr,
        )
        return 2

    videos = aggregate_month(args.daily_dir, ym)
    question = _build_question(ym)
    nlm_answer, nlm_success = query_notebook(
        question,
        args.notebook_id,
        args.nlm_skill,
        timeout=args.timeout,
    )

    # 3-tier fallback decision — RESEARCH §Plan 6 Open Q4.
    if not videos and not nlm_success:
        fallback_tier = 3
    elif not videos:
        fallback_tier = 2
    elif not nlm_success:
        fallback_tier = 1
    else:
        fallback_tier = 0

    summary: dict = {
        "year_month": ym,
        "videos_count": len(videos),
        "notebooklm_success": nlm_success,
        "fallback_tier": fallback_tier,
        "target": str(target),
    }

    # Tier 3 — both fail. Dry-run previews only (exit 0, no mutation); real
    # runs mutate FAILURES.md and exit 1 (manual pivot signal). This keeps
    # ``--dry-run`` truly side-effect-free so operators can inspect fallout
    # before committing (Plan acceptance criterion line 473: dry-run must
    # exit 0 with ``"fallback_tier"`` key for any tier).
    if fallback_tier == 3:
        if args.dry_run:
            summary["dry_run"] = True
            summary["reminder"] = _build_reminder(ym, target)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            print(
                f"[DRY-RUN] research loop would fail for {ym} (T3) — no files mutated",
                file=sys.stderr,
            )
            return 0
        assigned = append_failures_kpi(
            args.failures,
            "NotebookLM query 실패 AND aggregate 결과 0 videos — 수동 점검 필요",
            ym,
            now,
        )
        summary["failures_entry"] = assigned
        summary["exit"] = 1
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(
            f"[FAIL] research loop failed for {ym} — manual pivot required",
            file=sys.stderr,
        )
        return 1

    # Tier 1 — reuse prior monthly_context as success-pattern body.
    effective_answer = nlm_answer
    if fallback_tier == 1:
        prev = find_previous_context(args.wiki_dir, ym)
        if prev is not None:
            effective_answer = (
                prev.read_text(encoding="utf-8", errors="replace")
                + "\n\n---\n\n(이전 달 재사용 덤프 끝)\n\n"
                + (nlm_answer or "")
            )

    template_text = args.template.read_text(encoding="utf-8", errors="replace")
    rendered = render_context(
        template_text,
        ym,
        videos,
        effective_answer,
        fallback_tier,
        args.notebook_id,
        now,
    )

    if args.dry_run:
        summary["dry_run"] = True
        summary["rendered_preview"] = rendered[:400]
        summary["reminder"] = _build_reminder(ym, target)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    # "latest" copy — Windows 호환성으로 symlink 금지, 단순 복사 유지.
    latest_copy.write_text(rendered, encoding="utf-8")

    # Tier 2 — FAILURES.md append 이후에도 context 파일은 남김 (다음 월 T1 재사용 가능).
    if fallback_tier == 2:
        assigned = append_failures_kpi(
            args.failures,
            f"Aggregate 결과 0 videos (NotebookLM success={nlm_success})",
            ym,
            now,
        )
        summary["failures_entry"] = assigned

    summary["latest_copy"] = str(latest_copy)
    summary["reminder"] = _build_reminder(ym, target)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover — CLI entry
    sys.exit(main())
