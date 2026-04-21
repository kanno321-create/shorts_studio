#!/usr/bin/env python3
"""verify_agent_md_size.py — SPC-03 AGENT.md body char ceiling enforcement.

Phase 12 AGENT-STD-01 5-block invariant 보완. Drift 방지용 soft ceiling.
기본 ``CHAR_LIMIT = 18000`` (Phase 15 Wave 0 empirical: producer max = scripter
17426 chars + 3% 여유) — 현 시점 0 breaking change, 장기 drift 방지 전용.

Scope:
    ``{agents-root}/producers/*/AGENT.md`` + ``{agents-root}/supervisor/*/AGENT.md``
    — inspector 17 은 Phase 12 AGENT-STD-01 5 XML block schema 로 이미 강제되어
    body bloat 가 구조적으로 제한. producer/supervisor 만 size audit 대상.

Usage::

    py -3.11 scripts/validate/verify_agent_md_size.py --ceiling 18000
    py -3.11 scripts/validate/verify_agent_md_size.py --agents-root /tmp/fake \
        --ceiling 5000

Exit codes:
    0 — 전체 AGENT.md body stripped chars ≤ ceiling
    1 — 1건 이상 violator (stdout 에 table 출력)

대표님을 위한 drift guard CLI — Plan 15-03 Task 3 populate (SPC-02/03 closure).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Phase 15 Wave 0 empirical baseline (tests/phase15 evidence/):
#   producers/* max = scripter 17426 chars
#   supervisor/shorts-supervisor post-compression = 5712 chars
# Ceiling = 18000 (max + 3% 여유) — 0 breaking change, drift-only guard.
CHAR_LIMIT = 18000

# Windows cp949 stdout guard — Phase 10 D-22 pattern.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass


def strip_frontmatter(text: str) -> str:
    """Return body after YAML frontmatter (``---`` delimited) — identical to
    ``verify_agent_md_schema._body_after_frontmatter`` semantics.
    """
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def scan_agents(root: Path) -> dict[str, int]:
    """Glob producers/*/AGENT.md + supervisor/*/AGENT.md; return {rel_path: body_chars}."""
    results: dict[str, int] = {}
    for pattern in ("producers/*/AGENT.md", "supervisor/*/AGENT.md"):
        for agent_md in sorted(root.glob(pattern)):
            text = agent_md.read_text(encoding="utf-8")
            body = strip_frontmatter(text).strip()
            key = str(agent_md.relative_to(root)).replace("\\", "/")
            results[key] = len(body)
    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint — returns exit code (0 = pass, 1 = violator)."""
    parser = argparse.ArgumentParser(
        description="SPC-03 — AGENT.md body char ceiling (Phase 15 drift guard).",
    )
    parser.add_argument(
        "--ceiling",
        type=int,
        default=CHAR_LIMIT,
        help=f"Max body chars (default {CHAR_LIMIT}).",
    )
    parser.add_argument(
        "--agents-root",
        type=Path,
        default=Path(".claude/agents"),
        help="Agents root directory (default '.claude/agents').",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional — write scan result + violator list as JSON.",
    )
    args = parser.parse_args(argv)

    sizes = scan_agents(args.agents_root)
    violators = {k: v for k, v in sizes.items() if v > args.ceiling}

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "ceiling": args.ceiling,
                    "sizes": sizes,
                    "violators": violators,
                    "count": len(sizes),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    if violators:
        print(
            f"[SPC-03] CHAR_LIMIT={args.ceiling} 초과 agent {len(violators)}/"
            f"{len(sizes)} (대표님):"
        )
        for name, size in sorted(violators.items(), key=lambda kv: -kv[1]):
            excess = size - args.ceiling
            print(f"  - {name}: {size} chars (+{excess})")
        return 1

    print(
        f"[SPC-03] 전체 {len(sizes)} AGENT.md 모두 {args.ceiling} chars 이하 "
        f"(대표님)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
