#!/usr/bin/env python3
"""verify_mandatory_reads_prose.py — AGENT-STD-02 prose quality checker.

Scans AGENT.md <mandatory_reads> blocks for 4 required prose elements:

  1. FAILURES.md reference — literal path ``.claude/failures/FAILURES.md``
  2. channel_bible reference — canonical path
     ``wiki/continuity_bible/channel_identity.md`` (Phase 6 Plan 02 D-10 SSOT;
     Plan 01 SUMMARY deviation #2 rectified the legacy ``wiki/ypp/channel_bible.md``
     drift). No alias tolerated.
  3. At least one SKILL path — regex ``.claude/skills/<name>/SKILL.md``; each
     declared skill is cross-verified against on-disk existence (drift guard).
  4. Korean literal — exact byte sequence ``샘플링 금지`` (대표님 session #29).
     Variants rejected; encoding forced to UTF-8 (Windows cp949 safe).

Elements 1 and 3 use conservative regexes to tolerate paraphrasing across 31
files; elements 2 and 4 are strict literals per Plan 06 HANDOFF.

Exits 0 if every in-scope AGENT.md passes. Exits 1 with per-file violation
report otherwise. Reuses ``_collect_all_agent_mds`` + ``EXCLUDED_AGENTS`` from
``verify_agent_md_schema`` (Plan 01 Task 3) so scope stays consistent with
AGENT-STD-01.

Usage::

    python scripts/validate/verify_mandatory_reads_prose.py --all
    python scripts/validate/verify_mandatory_reads_prose.py \
        --agent .claude/agents/producers/trend-collector/AGENT.md

D-A1-03 soft enforcement surface — hard enforcement (Hook / invoker hint
injection) is Phase 13 conditional per CONTEXT.md §D-A1-03.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows cp949 stdout/stderr guard — identical to Plan 01 verifier.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validate"))

# Reuse Plan 01 scope — DO NOT duplicate.
from verify_agent_md_schema import (  # noqa: E402
    _collect_all_agent_mds,
    EXCLUDED_AGENTS,
)

MANDATORY_READS_BLOCK_RE = re.compile(
    r"<mandatory_reads>(.*?)</mandatory_reads>",
    re.DOTALL,
)

# Conservative patterns for elements that may appear in varied phrasing.
# Strict literals for elements 2 and 4.
REQUIRED_LITERALS: dict[str, str] = {
    "failures_md": r"\.claude/failures/FAILURES\.md",
    "channel_bible": r"wiki/continuity_bible/channel_identity\.md",
    "skill_path": r"\.claude/skills/[a-z-]+/SKILL\.md",
    "sampling_forbidden": r"샘플링 금지",
}

# Sub-regex to enumerate skill references for disk-existence check.
SKILL_REF_RE = re.compile(r"\.claude/skills/([a-z-]+)/SKILL\.md")


def _check_skill_paths_exist(block: str) -> list[str]:
    """Return list of declared skill names whose SKILL.md does NOT exist on disk.

    Intentionally narrow: only verifies file existence. The Plan 04 reciprocity
    verifier (``verify_agent_skill_matrix.py``) owns matrix × AGENT.md cross-
    reference — we do not duplicate that logic here.
    """
    missing: list[str] = []
    seen: set[str] = set()
    for skill_name in SKILL_REF_RE.findall(block):
        if skill_name in seen:
            continue
        seen.add(skill_name)
        skill_md = REPO_ROOT / ".claude" / "skills" / skill_name / "SKILL.md"
        if not skill_md.exists():
            missing.append(skill_name)
    return missing


def verify_file(path: Path) -> tuple[bool, list[str]]:
    """Return ``(ok, missing)``. ``ok=True`` iff all 4 prose elements present
    AND every declared SKILL.md path resolves on disk.

    UTF-8 is enforced explicitly to keep the Korean literal intact on Windows
    where the platform default is cp949.
    """
    text = path.read_text(encoding="utf-8")
    block_match = MANDATORY_READS_BLOCK_RE.search(text)
    if not block_match:
        return False, ["(no <mandatory_reads> block — Plan 02/03 migration 필요)"]
    block = block_match.group(1)

    missing: list[str] = []
    for key, pattern in REQUIRED_LITERALS.items():
        if not re.search(pattern, block):
            missing.append(key)

    # Disk-existence cross-check for declared skill paths (drift guard).
    # Only meaningful when skill_path literal is present; if missing literal,
    # the REQUIRED_LITERALS violation is already logged above.
    if "skill_path" not in missing:
        orphan_skills = _check_skill_paths_exist(block)
        for name in orphan_skills:
            missing.append(f"skill_not_on_disk:{name}")

    return len(missing) == 0, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AGENT-STD-02 mandatory_reads prose quality checker.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Scan all producer + inspector AGENT.md files "
             "(excludes harvest-importer + shorts-supervisor)",
    )
    group.add_argument(
        "--agent",
        type=Path,
        help="Single AGENT.md file to scan",
    )
    args = parser.parse_args(argv)

    if args.all:
        targets = _collect_all_agent_mds()
    else:
        if not args.agent or not args.agent.exists():
            print(f"FAIL: {args.agent} does not exist", file=sys.stderr)
            return 1
        targets = [args.agent]

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
            f"FAIL: {len(violations)}/{len(targets)} AGENT.md missing "
            f"mandatory_reads prose elements",
            file=sys.stderr,
        )
        for rel, missing in violations:
            print(f"  - {rel}: missing = {missing}", file=sys.stderr)
        return 1

    print(
        f"OK: {len(targets)}/{len(targets)} AGENT.md pass AGENT-STD-02 prose "
        f"check (FAILURES.md + channel_identity + skill path (on-disk) + "
        f"'샘플링 금지' literal)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
