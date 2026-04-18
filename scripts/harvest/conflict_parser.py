"""CONFLICT_MAP.md parser.

Parses 39 drift entries (A:13, B:16, C:10) via heading regex.
On count mismatch raises CONFLICT_MAP_COUNT_MISMATCH — fail-loudly
contract per 03-RESEARCH.md §E10.
"""
from __future__ import annotations

import re
from pathlib import Path

_ENTRY_RE = re.compile(r"^### ([ABC])-(\d+)\.\s+(.*)$", re.MULTILINE)

EXPECTED_A = 13
EXPECTED_B = 16
EXPECTED_C = 10


class CONFLICT_MAP_COUNT_MISMATCH(Exception):
    """Raised when parsed entry counts deviate from (13, 16, 10)."""


def parse_conflict_map(path: Path) -> list[dict]:
    """Parse CONFLICT_MAP.md into structured entry list.

    Returns:
        list of {"class": "A"|"B"|"C", "num": int, "summary": str, "id": "X-N"}

    Raises:
        FileNotFoundError: path does not exist.
        CONFLICT_MAP_COUNT_MISMATCH: counts not equal to (13, 16, 10).
    """
    text = path.read_text(encoding="utf-8")
    entries: list[dict] = []
    for match in _ENTRY_RE.finditer(text):
        entries.append(
            {
                "class": match.group(1),
                "num": int(match.group(2)),
                "summary": match.group(3).strip(),
                "id": f"{match.group(1)}-{match.group(2)}",
            }
        )

    count_a = sum(1 for e in entries if e["class"] == "A")
    count_b = sum(1 for e in entries if e["class"] == "B")
    count_c = sum(1 for e in entries if e["class"] == "C")

    if not (count_a == EXPECTED_A and count_b == EXPECTED_B and count_c == EXPECTED_C):
        raise CONFLICT_MAP_COUNT_MISMATCH(
            f"expected {EXPECTED_A}/{EXPECTED_B}/{EXPECTED_C}, "
            f"got {count_a}/{count_b}/{count_c}"
        )

    assert len([e for e in entries if e["class"] == "A"]) == 13
    assert len([e for e in entries if e["class"] == "B"]) == 16
    assert len([e for e in entries if e["class"] == "C"]) == 10

    return entries


def extract_entry_body(path: Path, entry_id: str) -> str:
    """Extract full body text of a single entry (between its heading and next)."""
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^### {re.escape(entry_id)}\.\s+.*?(?=^### [ABC]-\d+\.\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(0)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python conflict_parser.py <conflict_map_path>", file=sys.stderr)
        sys.exit(2)
    items = parse_conflict_map(Path(sys.argv[1]))
    a = sum(1 for e in items if e["class"] == "A")
    b = sum(1 for e in items if e["class"] == "B")
    c = sum(1 for e in items if e["class"] == "C")
    print(f"[OK] parsed {len(items)} entries (A={a}, B={b}, C={c})")
