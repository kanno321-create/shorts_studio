#!/usr/bin/env python3
"""Usage: python verify_line_count.py <file> <min> <max>

Exit 0 if min <= wc -l <= max; exit 1 otherwise.
Used by Phase 5 Plan 10 SC 1 acceptance (shorts_pipeline.py 500~800).
Stdlib-only; no 3rd-party imports.
"""
from __future__ import annotations

import sys
from pathlib import Path


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: verify_line_count.py <file> <min> <max>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    try:
        lo = int(sys.argv[2])
        hi = int(sys.argv[3])
    except ValueError as e:
        print(f"FAIL: min/max must be integers ({e})", file=sys.stderr)
        return 2
    if not target.exists():
        print(f"FAIL: {target} does not exist", file=sys.stderr)
        return 1
    n = count_lines(target)
    if lo <= n <= hi:
        print(f"PASS: {target} has {n} lines (range [{lo}, {hi}])")
        return 0
    print(
        f"FAIL: {target} has {n} lines (expected [{lo}, {hi}])",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
