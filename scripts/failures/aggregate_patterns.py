#!/usr/bin/env python3
"""FAILURES aggregation dry-run CLI (D-13, FAIL-02).

Reads one or more FAILURES-schema markdown files, normalizes pattern keys
via sha256, counts recurrences, emits JSON candidates with count >= threshold.

Phase 6 is DRY-RUN ONLY. No SKILL.md.candidate file is ever created by this
script -- that promotion is Phase 10 per ROADMAP. The --dry-run flag exists
for future compatibility but defaults to True and cannot be disabled within
Phase 6 (per D-13; BooleanOptionalAction intentionally NOT used).

Usage:
    python scripts/failures/aggregate_patterns.py \\
        --input .claude/failures/_imported_from_shorts_naberal.md \\
        --input .claude/failures/FAILURES.md \\
        --threshold 3 \\
        [--output out.json]

Exit codes:
    0 = success (JSON emitted)
    2 = argparse error (missing required args, bad types)

Design invariants (see 06-CONTEXT.md D-13 / 06-RESEARCH.md Area 8):
    - Stdlib-only (argparse, hashlib, json, re, collections.Counter, pathlib).
    - UTF-8 throughout; ensure_ascii=False in json.dumps so Korean summaries
      survive round-trip.
    - 48-bit pattern key (sha256[:12]) -- collision safe up to ~16M entries.
    - Missing inputs log a warning to stderr but do NOT abort (returns 0).
    - NO SKILL.md.candidate file is ever created; Phase 10 owns promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator

ENTRY_RE = re.compile(r"^### (FAIL-[\w]+):\s*(.+?)$", re.MULTILINE)
TRIGGER_RE = re.compile(r"^-\s*\*\*Trigger\*\*:\s*(.+?)$", re.MULTILINE)


def iter_entries(md_path: Path) -> Iterator[dict]:
    """Yield dicts {id, summary, trigger, source} for every FAIL-NNN section.

    Tolerates entries without a Trigger field (trigger defaults to '').
    Missing files emit a warning to stderr and yield nothing (do not raise).
    """
    if not md_path.exists():
        print(f"WARN: input does not exist: {md_path}", file=sys.stderr)
        return
    text = md_path.read_text(encoding="utf-8", errors="replace")
    # Split on each ### FAIL- header so one entry's text does not leak Trigger
    # fields into the next entry's lookup scope.
    sections = re.split(r"(?=^### FAIL-)", text, flags=re.MULTILINE)
    for sec in sections:
        m = ENTRY_RE.search(sec)
        if not m:
            continue
        fail_id = m.group(1)
        summary = m.group(2).strip()
        trig_match = TRIGGER_RE.search(sec)
        trigger = trig_match.group(1).strip() if trig_match else ""
        yield {
            "id": fail_id,
            "summary": summary,
            "trigger": trigger,
            "source": md_path.name,
        }


def normalize_pattern_key(entry: dict) -> str:
    """Stable 12-hex-char key: sha256(summary + '||' + trigger[:80]).

    Lowercase, strip non-word/space/Korean runs, collapse whitespace.
    48-bit prefix -> collision safe up to ~16M entries (RESEARCH Area 8 line 1032).
    """
    summary = entry.get("summary", "").lower().strip()
    trigger = entry.get("trigger", "")[:80].lower().strip()
    base = f"{summary}||{trigger}"
    # Strip punctuation, keep words + whitespace + Korean syllables
    base = re.sub(r"[^\w\s가-힣]", "", base)
    base = re.sub(r"\s+", " ", base).strip()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]


def aggregate(inputs: list[Path], threshold: int) -> dict:
    """Aggregate FAILURES entries into {candidates, total_entries}.

    candidates is filtered by count >= threshold and examples capped at 3.
    """
    counter: Counter[str] = Counter()
    key_examples: dict[str, list[dict]] = {}

    for f in inputs:
        for entry in iter_entries(f):
            key = normalize_pattern_key(entry)
            counter[key] += 1
            key_examples.setdefault(key, []).append(entry)

    candidates = [
        {"key": k, "count": c, "examples": key_examples[k][:3]}
        for k, c in counter.most_common()
        if c >= threshold
    ]
    return {
        "candidates": candidates,
        "total_entries": sum(counter.values()),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="FAILURES aggregation dry-run (D-13, Phase 6 only).",
    )
    p.add_argument(
        "--input",
        action="append",
        type=Path,
        required=True,
        help="Path to a FAILURES-schema markdown file (repeatable).",
    )
    p.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Minimum occurrence count for candidate (default 3).",
    )
    # Intentionally NOT BooleanOptionalAction: Phase 6 cannot disable dry-run.
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry-run only (Phase 6 default; cannot be disabled in Phase 6).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path; if omitted, emit to stdout.",
    )

    args = p.parse_args(argv)

    report = aggregate(args.input, args.threshold)
    text = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        # Force UTF-8 on Windows stdout so Korean survives the print() call.
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
