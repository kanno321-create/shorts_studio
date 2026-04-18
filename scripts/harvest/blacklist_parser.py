"""HARVEST_BLACKLIST parser.

SINGLE SOURCE OF TRUTH for blacklist count invariant (len == 10).
Downstream callers (Plan 08 audit) MUST NOT re-assert count — they rely
on this module to fail-fast on drift.

Security: `ast.literal_eval` only. `eval()` / `exec()` are PROHIBITED
(CLAUDE.md rule — zero-trust markdown posture, E5 in 03-RESEARCH.md).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

_BLACKLIST_RE = re.compile(r"HARVEST_BLACKLIST\s*=\s*(\[.*?\n\])", re.DOTALL)

EXPECTED_COUNT = 10


def parse_blacklist(scope_md: Path) -> list[dict]:
    """Parse HARVEST_BLACKLIST dict list from 02-HARVEST_SCOPE.md.

    Returns a list of dicts. Each dict has one of 'file' / 'path' /
    'pattern' as selector key plus mandatory 'reason'. Optional 'lines'
    key specifies a range within a file.

    Raises:
        FileNotFoundError: scope_md does not exist.
        ValueError: (a) HARVEST_BLACKLIST literal not found, or
                    (b) parsed length != EXPECTED_COUNT (10).
                    This is the SINGLE SOURCE OF TRUTH contract.
    """
    text = scope_md.read_text(encoding="utf-8")
    match = _BLACKLIST_RE.search(text)
    if not match:
        raise ValueError(
            "HARVEST_BLACKLIST not found in scope md: "
            f"pattern 'HARVEST_BLACKLIST = [...]' not present in {scope_md}"
        )
    literal = match.group(1)
    result = ast.literal_eval(literal)
    if not isinstance(result, list):
        raise ValueError(
            f"HARVEST_BLACKLIST is not a list literal: got {type(result).__name__}"
        )
    if len(result) != EXPECTED_COUNT:
        raise ValueError(
            f"HARVEST_BLACKLIST entry count mismatch: "
            f"expected {EXPECTED_COUNT}, got {len(result)}"
        )
    # Validate each entry has at least one selector key + reason
    for idx, entry in enumerate(result):
        if not isinstance(entry, dict):
            raise ValueError(
                f"HARVEST_BLACKLIST[{idx}] is not a dict: {entry!r}"
            )
        if "reason" not in entry:
            raise ValueError(
                f"HARVEST_BLACKLIST[{idx}] missing 'reason' key: {entry!r}"
            )
        if not any(k in entry for k in ("file", "path", "pattern")):
            raise ValueError(
                f"HARVEST_BLACKLIST[{idx}] missing selector "
                f"(file/path/pattern): {entry!r}"
            )
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python blacklist_parser.py <scope_md_path>", file=sys.stderr)
        sys.exit(2)
    entries = parse_blacklist(Path(sys.argv[1]))
    print(f"[OK] parsed {len(entries)} blacklist entries")
    for entry in entries:
        selector = entry.get("file") or entry.get("path") or entry.get("pattern")
        print(f"  - {selector}: {entry['reason'][:60]}...")
