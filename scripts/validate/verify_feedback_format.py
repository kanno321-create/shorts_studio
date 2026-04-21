#!/usr/bin/env python3
"""verify_feedback_format.py — UFL-04 feedback_video_quality.md validator.

Phase 15 Plan 05 Task 02. `.claude/memory/feedback_video_quality.md` 의 각
Markdown H2 entry 가 4 필수 필드 (session_id, niche, rating, feedback) 를
포함하며 rating 이 `[1-5]/5` 형식임을 검증.

Usage::

    py -3.11 scripts/validate/verify_feedback_format.py
    py -3.11 scripts/validate/verify_feedback_format.py --path <custom.md>

Exit codes:
    0 — 모든 entry 통과 (entry 0 개일 때도 정상).
    1 — 위반 entry 존재 또는 파일 부재.

CLAUDE.md 준수: 필수 #7 대표님 존댓말, 금기 #3 silent except 금지.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows cp949 stdout/stderr 대비 (Phase 10 D-22 pattern).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover — reconfigure 미지원 환경 명시적 체념
    pass

DEFAULT_PATH = Path(".claude/memory/feedback_video_quality.md")

# H2 엄격 pattern: `## YYYY-MM-DD VIDEO_ID`
H2_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} \S+\s*$")

# Bullet field pattern: `- field: value`
FIELD_RE = re.compile(r"^-\s*(\w+)\s*:\s*(.+)$")

# Rating 1~5/5 엄격 format.
RATING_RE = re.compile(r"^[1-5]/5$")

REQUIRED_FIELDS = {"session_id", "niche", "rating", "feedback"}


def parse_entries(text: str) -> list[dict]:
    """Markdown 텍스트를 H2 entry list 로 파싱.

    Returns:
        entry dict list — 각 ``{"_line": int, "_header": str, "_fields": dict}``.
        H2 regex 미일치 라인은 entry 로 잡히지 않음 (malformed 는 silently skip,
        상위에서 "0 entry" 로 reporting).
    """
    entries: list[dict] = []
    current: dict | None = None
    for i, line in enumerate(text.splitlines(), start=1):
        if H2_RE.match(line):
            if current:
                entries.append(current)
            current = {"_line": i, "_header": line, "_fields": {}}
        elif current is not None:
            m = FIELD_RE.match(line)
            if m:
                current["_fields"][m.group(1)] = m.group(2).strip()
    if current:
        entries.append(current)
    return entries


def validate_entry(entry: dict) -> list[str]:
    """단일 entry 의 필수 필드 + rating format 검증.

    Returns:
        error 메시지 리스트. 빈 리스트 = 통과.
    """
    errors: list[str] = []
    fields = entry["_fields"]
    missing = REQUIRED_FIELDS - set(fields.keys())
    for m in sorted(missing):
        errors.append(
            f"line {entry['_line']}: 누락 field '{m}' (대표님)"
        )
    rating = fields.get("rating", "")
    if rating and not RATING_RE.match(rating):
        errors.append(
            f"line {entry['_line']}: rating format 위반 '{rating}' "
            f"— 1/5~5/5 요구 (대표님)"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="UFL-04 feedback_video_quality.md format validator",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_PATH,
        help="검증 대상 Markdown 파일 (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"[feedback-fmt] 파일 없음 (대표님): {args.path}")
        return 1

    text = args.path.read_text(encoding="utf-8")
    entries = parse_entries(text)

    all_errors: list[str] = []
    for e in entries:
        all_errors.extend(validate_entry(e))

    if all_errors:
        print(f"[feedback-fmt] 위반 {len(all_errors)} 건 (대표님):")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"[feedback-fmt] 전체 {len(entries)} entry 검증 완료 (대표님).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
