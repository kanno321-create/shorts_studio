#!/usr/bin/env python3
"""verify_agent_md_schema.py — AGENT-STD-01 compliance checker.

Scans AGENT.md files for the 5-XML-block schema in fixed order:
  <role> -> <mandatory_reads> -> <output_format> -> <skills> -> <constraints>

Exits 0 if all scanned files comply. Exits 1 if any violation, with
stderr report per file.

Scope:
  --all   Scan .claude/agents/producers/*/AGENT.md
          + .claude/agents/inspectors/*/*/AGENT.md
          EXCLUDE: harvest-importer (Phase 3 deprecated),
                   shorts-supervisor (out of Phase 12 scope).
  <path>  Scan single file.

D-A1-01 / AGENT-STD-01 — Phase 12 Plan 01.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows cp949 stdout/stderr guard (Phase 10 D-22).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

# D-A1-01 fixed-order schema regex — DOTALL accepts multi-line bodies.
SCHEMA_RE = re.compile(
    r"<role>.*?</role>"
    r".*?<mandatory_reads>.*?</mandatory_reads>"
    r".*?<output_format>.*?</output_format>"
    r".*?<skills>.*?</skills>"
    r".*?<constraints>.*?</constraints>",
    re.DOTALL,
)

BLOCK_NAMES = ("role", "mandatory_reads", "output_format", "skills", "constraints")

# Phase 12 scope exclusions (D-A2-01 + CLAUDE.md AF-10 guard).
EXCLUDED_AGENTS = {"harvest-importer", "shorts-supervisor"}

REPO_ROOT = Path(__file__).resolve().parents[2]


def _collect_all_agent_mds() -> list[Path]:
    """Scan producer + inspector AGENT.md files, excluding Phase 12 scope outs."""
    targets: list[Path] = []

    producers_dir = REPO_ROOT / ".claude" / "agents" / "producers"
    if producers_dir.is_dir():
        for agent_dir in sorted(producers_dir.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name in EXCLUDED_AGENTS:
                continue
            agent_md = agent_dir / "AGENT.md"
            if agent_md.exists():
                targets.append(agent_md)

    inspectors_dir = REPO_ROOT / ".claude" / "agents" / "inspectors"
    if inspectors_dir.is_dir():
        for category_dir in sorted(inspectors_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            for agent_dir in sorted(category_dir.iterdir()):
                if not agent_dir.is_dir() or agent_dir.name in EXCLUDED_AGENTS:
                    continue
                agent_md = agent_dir / "AGENT.md"
                if agent_md.exists():
                    targets.append(agent_md)

    return targets


def verify_file(path: Path) -> tuple[bool, list[str]]:
    """Return ``(ok, missing_blocks)``. ``ok=True`` iff 5 blocks present in order."""
    text = path.read_text(encoding="utf-8")
    # Per-block presence.
    missing = [
        name for name in BLOCK_NAMES
        if f"<{name}>" not in text or f"</{name}>" not in text
    ]
    if missing:
        return False, missing
    # Fixed order.
    if not SCHEMA_RE.search(text):
        return False, ["(order violation — blocks exist but not in fixed sequence)"]
    return True, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AGENT-STD-01 compliance checker (5 XML blocks in fixed order).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Scan all producer + inspector AGENT.md files "
             "(excludes harvest-importer + shorts-supervisor)",
    )
    group.add_argument(
        "path",
        type=Path,
        nargs="?",
        help="Single AGENT.md file to scan",
    )
    args = parser.parse_args(argv)

    if args.all:
        targets = _collect_all_agent_mds()
    else:
        if not args.path or not args.path.exists():
            print(f"FAIL: {args.path} does not exist", file=sys.stderr)
            return 1
        targets = [args.path]

    violations: list[tuple[str, list[str]]] = []
    for path in targets:
        ok, missing = verify_file(path)
        if not ok:
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            violations.append((str(rel), missing))

    if violations:
        print(
            f"FAIL: {len(violations)}/{len(targets)} AGENT.md violate 5-block schema",
            file=sys.stderr,
        )
        for rel, missing in violations:
            print(f"  - {rel}: missing/misordered = {missing}", file=sys.stderr)
        return 1

    print(f"OK: {len(targets)}/{len(targets)} AGENT.md comply with 5-block schema")
    return 0


if __name__ == "__main__":
    sys.exit(main())
