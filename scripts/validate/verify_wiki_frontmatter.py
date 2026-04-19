#!/usr/bin/env python3
"""Usage: python verify_wiki_frontmatter.py [--root wiki] [--allow-scaffold]

Walk <root>/**/*.md and validate each against D-17 schema. Exit 0 on clean
sweep; exit 1 on any violation.

`--allow-scaffold` tolerates status=scaffold placeholders (legacy Phase 2
MOC.md files) even when they lack all 5 required fields. README.md and
files without a frontmatter block at all are skipped.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# scripts/validate/verify_wiki_frontmatter.py -> parents[2] = studios/shorts/
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.wiki.frontmatter import parse_frontmatter, validate_node  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="wiki", type=Path)
    p.add_argument(
        "--allow-scaffold",
        action="store_true",
        help="Allow status=scaffold (Phase 2 MOC placeholders).",
    )
    args = p.parse_args()

    root = (_REPO / args.root) if not args.root.is_absolute() else args.root
    if not root.exists():
        print(f"FAIL: wiki root does not exist: {root}", file=sys.stderr)
        return 1

    violations: list[str] = []
    checked = 0
    for md in root.rglob("*.md"):
        # README.md files are navigation indexes, not wiki nodes.
        if md.name == "README.md":
            continue
        checked += 1
        try:
            validate_node(md)
        except ValueError as e:
            # Scaffold tolerance: if the file's actual status is scaffold
            # and --allow-scaffold is set, do NOT count as a violation even
            # if other fields are missing. Scaffold placeholders are legacy
            # Phase 2 artefacts superseded by Plan 02's real node authoring.
            if args.allow_scaffold:
                try:
                    fm = parse_frontmatter(md)
                    if fm.get("status") == "scaffold":
                        continue
                except ValueError:
                    pass
            violations.append(str(e))

    if violations:
        print(
            f"FAIL: {len(violations)}/{checked} wiki nodes invalid:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print(f"PASS: {checked} wiki nodes valid D-17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
