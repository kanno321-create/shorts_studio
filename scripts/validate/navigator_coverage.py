#!/usr/bin/env python3
"""Navigator coverage — CLAUDE.md 네비게이션 매트릭스 완전성 검증.

목적:
    `.claude/agents/**/AGENT.md` 모든 에이전트 + `.claude/skills/*/SKILL.md` 모든
    스킬이 스튜디오 루트 CLAUDE.md 본문에 **최소 1회 이상 언급**되는지 확인.
    구현된 자산이 "찾을 수 없어서" 휴면 상태가 되는 것을 방지.

통합:
    - `.claude/hooks/session_start.py` Step 6b — 경고만 (파이프라인 차단 금지)
    - `scripts/validate/harness_audit.py` — 감사 점수 기여

사용법:
    py -3.11 -m scripts.validate.navigator_coverage              # gap 발견 시 exit 1
    py -3.11 -m scripts.validate.navigator_coverage --warn-only  # 항상 exit 0 (warning)
    py -3.11 -m scripts.validate.navigator_coverage --json-out PATH  # JSON 리포트 작성
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Deprecated / one-time 에이전트는 Navigator 커버리지에서 제외.
# harvest-importer 는 Phase 3 전용으로 Phase 4+ 이후 비활성 (AGENT.md 에도 deprecated 명시).
EXCLUDED_AGENTS = {"harvest-importer"}


def find_studio_root(start: Path) -> Path | None:
    """가장 가까운 `.claude/` + `CLAUDE.md` 둘 다 존재하는 상위 디렉토리 탐색."""
    cur = start.resolve()
    for _ in range(10):
        if (cur / ".claude").is_dir() and (cur / "CLAUDE.md").exists():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


def collect_agent_names(agents_root: Path) -> set[str]:
    """에이전트 이름 = AGENT.md 를 담고 있는 폴더의 basename.

    `_shared/`, `_patterns_reference/` 같은 언더스코어 prefix 폴더는 제외.
    """
    names: set[str] = set()
    if not agents_root.exists():
        return names
    for agent_md in agents_root.rglob("AGENT.md"):
        name = agent_md.parent.name
        if name.startswith("_"):
            continue
        if name in EXCLUDED_AGENTS:
            continue
        names.add(name)
    return names


def collect_skill_names(skills_root: Path) -> set[str]:
    """스킬 이름 = SKILL.md 를 담고 있는 폴더의 basename."""
    names: set[str] = set()
    if not skills_root.exists():
        return names
    for skill_md in skills_root.rglob("SKILL.md"):
        name = skill_md.parent.name
        if name.startswith("_"):
            continue
        names.add(name)
    return names


def find_uncovered(assets: set[str], claude_md_text: str) -> set[str]:
    """CLAUDE.md 본문에 1회도 등장하지 않는 자산 이름 집합."""
    return {name for name in assets if name not in claude_md_text}


def build_report(
    root: Path,
    agents: set[str],
    skills: set[str],
    uncovered_agents: set[str],
    uncovered_skills: set[str],
) -> dict:
    total = len(agents) + len(skills)
    covered = total - len(uncovered_agents) - len(uncovered_skills)
    return {
        "studio_root": str(root),
        "agents_total": len(agents),
        "agents_covered": len(agents) - len(uncovered_agents),
        "agents_uncovered": sorted(uncovered_agents),
        "skills_total": len(skills),
        "skills_covered": len(skills) - len(uncovered_skills),
        "skills_uncovered": sorted(uncovered_skills),
        "total_assets": total,
        "total_covered": covered,
        "coverage_ratio": round(covered / total, 4) if total else 1.0,
        "excluded_agents": sorted(EXCLUDED_AGENTS),
    }


def main(argv: list[str] | None = None) -> int:
    # Windows cp949 기본 인코딩 방어 (harness_audit.py 와 동일 패턴).
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(
        description="Navigator coverage — every agent/skill must appear in CLAUDE.md",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Report gaps but always exit 0 (for non-blocking hooks)",
    )
    parser.add_argument(
        "--studio-root",
        type=Path,
        default=None,
        help="Studio root (auto-detected from cwd if omitted)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write JSON report to this path (in addition to stdout text)",
    )
    args = parser.parse_args(argv)

    root = args.studio_root or find_studio_root(Path.cwd())
    if root is None:
        print("[navigator-coverage] ERROR: studio root not found", file=sys.stderr)
        return 2

    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        print(f"[navigator-coverage] ERROR: {claude_md} missing", file=sys.stderr)
        return 2

    text = claude_md.read_text(encoding="utf-8", errors="ignore")

    agents = collect_agent_names(root / ".claude" / "agents")
    skills = collect_skill_names(root / ".claude" / "skills")

    uncovered_agents = find_uncovered(agents, text)
    uncovered_skills = find_uncovered(skills, text)

    report = build_report(root, agents, skills, uncovered_agents, uncovered_skills)

    print(
        f"[navigator-coverage] agents: {report['agents_covered']}/{report['agents_total']} covered"
    )
    print(
        f"[navigator-coverage] skills: {report['skills_covered']}/{report['skills_total']} covered"
    )
    print(
        f"[navigator-coverage] total:  {report['total_covered']}/{report['total_assets']} "
        f"({report['coverage_ratio']:.1%})"
    )

    if uncovered_agents:
        print(
            f"[navigator-coverage] uncovered agents ({len(uncovered_agents)}):",
            file=sys.stderr,
        )
        for name in sorted(uncovered_agents):
            print(f"  - {name}", file=sys.stderr)

    if uncovered_skills:
        print(
            f"[navigator-coverage] uncovered skills ({len(uncovered_skills)}):",
            file=sys.stderr,
        )
        for name in sorted(uncovered_skills):
            print(f"  - {name}", file=sys.stderr)

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if not uncovered_agents and not uncovered_skills:
        print("[navigator-coverage] OK — all assets covered in CLAUDE.md Navigator")
        return 0

    if args.warn_only:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
