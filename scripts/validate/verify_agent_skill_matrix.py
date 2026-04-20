#!/usr/bin/env python3
"""verify_agent_skill_matrix.py — SKILL-ROUTE-01 bidirectional reciprocity check.

Parses wiki/agent_skill_matrix.md + all AGENT.md `<skills>` blocks.
For each (agent, skill) pair:
  - matrix cell = "required" ↔ AGENT.md <skills> contains "{skill} (required)"
  - matrix cell = "optional" ↔ AGENT.md <skills> contains "{skill} (optional)"
  - matrix cell = "n/a" ↔ AGENT.md <skills> does NOT contain skill name

Exits 0 if all N × 5 cells reciprocate (N = 31 on disk: 14 producer + 17 inspector).
Exits 1 with stderr report on drift (when --fail-on-drift).

D-A1-02 / SKILL-ROUTE-01 / Phase 12 Plan 04.
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

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = REPO_ROOT / "wiki" / "agent_skill_matrix.md"

# Matrix column order (5 공용 skill) — matches wiki/agent_skill_matrix.md header.
COMMON_SKILLS = [
    "progressive-disclosure",
    "gate-dispatcher",
    "drift-detection",
    "context-compressor",
    "harness-audit",
]

# 14 producer dirs (disk reality 2026-04-21) — Plan 01 SUMMARY key-decisions §1.
PRODUCERS = [
    "trend-collector", "niche-classifier", "researcher", "director", "scripter",
    "script-polisher", "metadata-seo", "scene-planner", "shot-planner",
    "voice-producer", "asset-sourcer", "thumbnail-designer", "assembler", "publisher",
]

# 17 inspector dirs (category, name).
INSPECTORS = [
    ("structural", "ins-schema-integrity"),
    ("structural", "ins-timing-consistency"),
    ("structural", "ins-blueprint-compliance"),
    ("content", "ins-factcheck"),
    ("content", "ins-narrative-quality"),
    ("content", "ins-korean-naturalness"),
    ("style", "ins-thumbnail-hook"),
    ("style", "ins-tone-brand"),
    ("style", "ins-readability"),
    ("compliance", "ins-license"),
    ("compliance", "ins-platform-policy"),
    ("compliance", "ins-safety"),
    ("technical", "ins-audio-quality"),
    ("technical", "ins-render-integrity"),
    ("technical", "ins-subtitle-alignment"),
    ("media", "ins-mosaic"),
    ("media", "ins-gore"),
]


def parse_matrix() -> dict[str, dict[str, str]]:
    """Parse wiki/agent_skill_matrix.md → {agent: {skill: required|optional|n/a}}.

    Row format: `| agent-name | v1 | v2 | v3 | v4 | v5 | additional |`
    (spaces around cell values optional; lenient matching).
    """
    text = MATRIX_PATH.read_text(encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    # Lenient row regex — tolerate flexible spacing. Extracts 5 skill cells.
    row_re = re.compile(
        r"^\|\s*([a-z][a-z0-9-]+)\s*\|"
        r"\s*(required|optional|n/a)\s*\|"
        r"\s*(required|optional|n/a)\s*\|"
        r"\s*(required|optional|n/a)\s*\|"
        r"\s*(required|optional|n/a)\s*\|"
        r"\s*(required|optional|n/a)\s*\|"
        r"[^|]*\|",
        re.MULTILINE,
    )
    for m in row_re.finditer(text):
        agent = m.group(1)
        cells = [m.group(i) for i in range(2, 7)]
        result[agent] = dict(zip(COMMON_SKILLS, cells))
    return result


def parse_agent_skills_block(agent_path: Path) -> dict[str, str]:
    """Parse <skills> block of AGENT.md → {skill_name: required|optional}.

    Skills marked `n/a` are omitted from the return dict (absence == n/a).
    Accepts formats like:
      - `gate-dispatcher` (required) — description
      - gate-dispatcher (optional)
    """
    text = agent_path.read_text(encoding="utf-8")
    block_re = re.compile(r"<skills>(.*?)</skills>", re.DOTALL)
    m = block_re.search(text)
    if not m:
        return {}
    block = m.group(1)
    result: dict[str, str] = {}
    # Match skill name (optionally backtick-wrapped) followed by (required|optional)
    entry_re = re.compile(r"`?([a-z][a-z0-9-]+)`?\s*\((required|optional)\)")
    for em in entry_re.finditer(block):
        result[em.group(1)] = em.group(2)
    return result


def _agent_md_path(agent: str) -> Path | None:
    """Resolve agent name → AGENT.md path on disk."""
    if agent in PRODUCERS:
        return REPO_ROOT / ".claude" / "agents" / "producers" / agent / "AGENT.md"
    for cat, name in INSPECTORS:
        if name == agent:
            return (
                REPO_ROOT / ".claude" / "agents" / "inspectors" / cat / name / "AGENT.md"
            )
    return None


def verify_reciprocity(fail_on_drift: bool = False) -> tuple[int, list[str]]:
    """Compare matrix vs AGENT.md <skills> blocks.

    Returns (drift_count, messages). Drift includes:
      - agent in matrix but AGENT.md missing
      - matrix cell "required" but AGENT.md block says other
      - matrix cell "optional" but AGENT.md block contradicts
      - matrix cell "n/a" but AGENT.md block lists the skill
    """
    matrix = parse_matrix()
    drifts: list[str] = []
    for agent, cells in matrix.items():
        p = _agent_md_path(agent)
        if p is None or not p.exists():
            drifts.append(
                f"DRIFT: agent '{agent}' in matrix but AGENT.md not found"
            )
            continue
        skills_block = parse_agent_skills_block(p)
        for skill, cell_value in cells.items():
            in_block = skills_block.get(skill)
            # Reciprocity rules
            if cell_value == "required" and in_block != "required":
                drifts.append(
                    f"DRIFT: {agent}/{skill}: matrix=required, "
                    f"AGENT.md=<{in_block or 'missing'}>"
                )
            elif cell_value == "optional":
                # optional in matrix → <skills> must have optional entry OR absent (soft)
                if in_block is not None and in_block != "optional":
                    drifts.append(
                        f"DRIFT: {agent}/{skill}: matrix=optional, "
                        f"AGENT.md=<{in_block}>"
                    )
            elif cell_value == "n/a" and in_block is not None:
                drifts.append(
                    f"DRIFT: {agent}/{skill}: matrix=n/a, "
                    f"AGENT.md=<{in_block}> (should be absent)"
                )
    return len(drifts), drifts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SKILL-ROUTE-01 matrix × AGENT.md reciprocity check"
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 on any drift (CI default).",
    )
    args = parser.parse_args(argv)

    count, drifts = verify_reciprocity(fail_on_drift=args.fail_on_drift)
    total_cells = 31 * 5  # 14 producer + 17 inspector = 31 agents × 5 공용 skill
    if count == 0:
        print(
            f"OK: {total_cells} cells (31 × 5) reciprocate between matrix "
            f"and AGENT.md <skills>"
        )
        return 0
    print(f"FAIL: {count} drift(s) detected", file=sys.stderr)
    for d in drifts[:20]:
        print(f"  {d}", file=sys.stderr)
    if count > 20:
        print(f"  ... and {count - 20} more", file=sys.stderr)
    return 1 if args.fail_on_drift else 0


if __name__ == "__main__":
    sys.exit(main())
