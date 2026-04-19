#!/usr/bin/env python3
"""Taste Gate → FAILURES.md appender (D-12 implementation).

Parses ``wiki/kpi/taste_gate_YYYY-MM.md``, filters rows with score ≤ 3 (D-13),
and appends a ``### [taste_gate] YYYY-MM 리뷰 결과`` block to
``.claude/failures/FAILURES.md``.

Phase 6 Hook compatibility (D-11, check_failures_append_only)
-------------------------------------------------------------
This module uses the read + concatenate + write_text pattern so the prior
FAILURES.md content is preserved as a STRICT PREFIX of the new content.
The pre_tool_use hook accepts this form (prior file bytes == startswith of
new file bytes). ``open(path, "w")`` with fresh content is DENIED because
it would truncate the reservoir.

Design invariants (09-RESEARCH.md Pitfall 2/5/6/7)
--------------------------------------------------
* stdlib-only: argparse, re, sys, datetime, pathlib, zoneinfo.
* Korean error strings raised explicitly via ``TasteGateParseError``
  (no silent try/except: pass fallbacks — Pitfall 6).
* Windows cp949 guard: ``sys.stdout.reconfigure(encoding="utf-8")`` in the
  main guard (Pitfall 7).
* Strict 9-column row regex with named groups (Pitfall 5).

Usage
-----
::

    python scripts/taste_gate/record_feedback.py --month 2026-04
    python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run

Exit codes
----------
* 0 = success (block appended, dry-run printed, or no escalation target)
* 2 = argparse error (bad --month format, missing argument)
* 3 = taste_gate file missing / parse error
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Module-level constants (MUST stay module-level — tests monkeypatch these).
# ---------------------------------------------------------------------------

FAILURES_PATH = Path(".claude/failures/FAILURES.md")
TASTE_GATE_DIR = Path("wiki/kpi")
KST = ZoneInfo("Asia/Seoul")

# Parses 9-column evaluation row:
#   | rank | video_id | "title" | 3sec% | completion% | avg초 | score | comment | tag |
# - rank       : one or more digits
# - video_id   : word chars or hyphens (6-char fake IDs in dry-run fixture)
# - title      : any non-pipe content, optional surrounding double quotes
# - retention/completion/avg : opaque metric cells (not parsed into numbers here)
# - score      : single digit 1-5 OR underscore (未평가 sentinel)
# - comment    : free Korean text (no pipes)
# - tag        : free Korean text (no pipes)
ROW_RE = re.compile(
    r"^\|\s*(?P<rank>\d+)\s*\|\s*(?P<video_id>[\w-]+)\s*\|"
    r"\s*\"?(?P<title>[^\"\|]+?)\"?\s*\|"
    r"\s*(?P<retention>[^\|]*?)\s*\|\s*(?P<completion>[^\|]*?)\s*\|"
    r"\s*(?P<avg>[^\|]*?)\s*\|"
    r"\s*(?P<score>[1-5]|_)\s*\|"
    r"\s*(?P<comment>[^\|]*?)\s*\|"
    r"\s*(?P<tag>[^\|]*?)\s*\|",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TasteGateParseError(Exception):
    """Raised on malformed or missing ``taste_gate_YYYY-MM.md``.

    Korean message via explicit raise — never caught-and-passed per Pitfall 6.
    """


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


def parse_taste_gate(month: str) -> list[dict]:
    """Parse ``TASTE_GATE_DIR / f"taste_gate_{month}.md"`` into evaluated rows.

    Rows with ``score == '_'`` (미평가) are skipped with a stderr warning and
    do not count toward the "평가된 행" total. Rows whose score group captures
    anything outside ``[1-5|_]`` never match the regex so cannot reach this
    function — but if a malformed cell slips through (e.g., 2-digit score),
    ``ROW_RE`` simply does not match that line and the line is ignored, so we
    surface the error as "평가된 행이 없습니다" when the result list is empty.

    Raises
    ------
    TasteGateParseError
        If the file does not exist, or if no evaluated rows could be parsed.
    """
    path = TASTE_GATE_DIR / f"taste_gate_{month}.md"
    if not path.exists():
        raise TasteGateParseError(
            f"파일 없음: {path} — 월별 평가 폼을 먼저 생성하세요"
        )

    text = path.read_text(encoding="utf-8")
    rows: list[dict] = []
    for m in ROW_RE.finditer(text):
        d = m.groupdict()
        if d["score"] == "_":
            print(
                f"WARN: rank {d['rank']} 미평가 (score='_') — 건너뜀",
                file=sys.stderr,
            )
            continue
        # Score group is restricted to '[1-5]' by the regex so int() always
        # succeeds here. We still validate range defensively — if somehow a
        # malformed string arrives (e.g. via a hand-edited regex), raise
        # explicitly rather than swallow.
        score_int = int(d["score"])
        if not 1 <= score_int <= 5:
            raise TasteGateParseError(
                f"rank {d['rank']} 점수 오류: {d['score']} (1-5 범위 밖)"
            )
        d["score"] = score_int
        rows.append(d)

    if not rows:
        raise TasteGateParseError(f"평가된 행이 없습니다: {path}")
    return rows


# ---------------------------------------------------------------------------
# Filter (D-13)
# ---------------------------------------------------------------------------


def filter_escalate(rows: list[dict]) -> list[dict]:
    """D-13: only rows with score ≤ 3 are escalated to FAILURES.md.

    Scores 4 and 5 remain in ``kpi_log.md`` only (noise filter; CONTEXT D-13).
    """
    return [r for r in rows if r["score"] <= 3]


# ---------------------------------------------------------------------------
# FAILURES.md block builder
# ---------------------------------------------------------------------------


def build_failures_block(month: str, escalated: list[dict]) -> str:
    """Render the ``### [taste_gate] YYYY-MM 리뷰 결과`` block.

    Uses ``datetime.now(KST).isoformat()`` so ``freeze_kst_2026_04_01`` fixture
    can monkey-patch ``datetime`` on this module for deterministic snapshots.
    """
    now_kst = datetime.now(KST).isoformat()
    summary_items = ", ".join(
        f"{r['video_id']}({r['score']}점)" for r in escalated
    )
    lines = [
        "",
        f"### [taste_gate] {month} 리뷰 결과",
        "- **Tier**: B",
        f"- **발생 세션**: {now_kst}",
        "- **재발 횟수**: 1",
        "- **Trigger**: 월간 Taste Gate 평가 점수 <= 3",
        f"- **무엇**: 대표님 평가 하위 항목 {len(escalated)}건 — {summary_items}",
        "- **왜**: 채널 정체성 / 품질 기대치 미달 — 다음 월 Producer 입력 조정 필요",
        "- **정답**: 하위 코멘트 패턴을 다음 월 niche-classifier / scripter 프롬프트에 반영",
        "- **검증**: 다음 월 Taste Gate 동일 패턴 재발 여부",
        "- **상태**: observed",
        f"- **관련**: wiki/kpi/taste_gate_{month}.md",
        "",
        "#### 세부 코멘트",
    ]
    for r in escalated:
        lines.append(f"- **{r['video_id']}** ({r['score']}/5): {r['comment']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# FAILURES.md writer (D-11 Hook compat)
# ---------------------------------------------------------------------------


def append_to_failures(block: str) -> None:
    """Append ``block`` to ``FAILURES_PATH`` preserving prior content as prefix.

    Phase 6 ``check_failures_append_only`` accepts Write operations only when
    the new file content starts with the existing content exactly. The
    read + concatenate + ``write_text`` pattern satisfies this contract and
    is more auditable than ``open(path, "a")`` because the full resulting
    byte stream is constructed in memory before the single write call.
    """
    existing = FAILURES_PATH.read_text(encoding="utf-8")
    new_content = existing + "\n" + block + "\n"
    FAILURES_PATH.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    # Pitfall 7: Windows cp949 guard so Korean survives print() calls even when
    # main() is imported (not just when __name__ == "__main__"). Re-configures
    # stdout/stderr to UTF-8 if possible; silent no-op on non-reconfigurable
    # streams (e.g., pytest capture buffers).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Taste Gate → FAILURES.md appender (D-12, Phase 9 KPI-05).",
    )
    parser.add_argument(
        "--month",
        required=True,
        help="평가 대상 월 (YYYY-MM, 예: 2026-04)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="FAILURES.md에 쓰지 않고 생성될 블록만 stdout에 출력",
    )
    args = parser.parse_args(argv)

    # Strict YYYY-MM format — argparse's error() exits with rc=2 automatically.
    if not re.match(r"^\d{4}-\d{2}$", args.month):
        parser.error(
            f"--month 형식 오류: {args.month!r} (YYYY-MM 예: 2026-04)"
        )

    try:
        rows = parse_taste_gate(args.month)
    except TasteGateParseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3

    escalated = filter_escalate(rows)
    block = build_failures_block(args.month, escalated)

    if args.dry_run:
        print(block)
        print(
            f"[dry-run] FAILURES.md 추가 예정 항목: {len(escalated)}건",
            file=sys.stderr,
        )
        return 0

    if not escalated:
        print(
            "승격 대상 없음 (모두 score > 3) — FAILURES.md 변경 없음",
            file=sys.stderr,
        )
        return 0

    append_to_failures(block)
    print(f"FAILURES.md 추가 완료: {len(escalated)}건 ({args.month})")
    return 0


if __name__ == "__main__":
    # Pitfall 7: Windows cp949 guard so Korean survives the print() calls.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
