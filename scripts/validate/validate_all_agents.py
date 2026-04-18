"""AGENT-07/08/09 enforcer — walks .claude/agents/ for AGENT.md files.

Checks (all stdlib only):
- AGENT-07: AGENT.md ≤ 500 lines.
- AGENT-08: description ≤ 1024 chars + ≥ 3 trigger-keyword-ish tokens.
- AGENT-09: "## MUST REMEMBER" header appears in the final 40% of the body (ratio_from_end ≤ 0.4).

CLI:
    py -3.11 -m scripts.validate.validate_all_agents [--path DIR] [--exclude NAME] [--strict]

Exit 0 on no violations, 1 otherwise.
Prints `OK: N agents validated` on success, per-violation lines on failure.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

# Support both `-m scripts.validate.validate_all_agents` and direct execution
if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from scripts.validate.parse_frontmatter import parse_frontmatter
else:
    from .parse_frontmatter import parse_frontmatter


LINE_LIMIT = 500
DESC_LIMIT = 1024
MUST_REMEMBER_HEADER = "## MUST REMEMBER"
MIN_TRIGGER_TOKENS = 3
MUST_REMEMBER_MAX_RATIO_FROM_END = 0.4  # MUST REMEMBER 헤더가 파일 하위 40% 이내에 있어야 함


def check_line_count(md_path: pathlib.Path, limit: int = LINE_LIMIT) -> tuple[int, bool]:
    """Return (total_lines, ok)."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    return len(lines), len(lines) <= limit


def check_description_chars(meta: dict, limit: int = DESC_LIMIT) -> tuple[int, bool]:
    """Return (char_count, ok)."""
    desc = meta.get("description", "")
    return len(desc), len(desc) <= limit


def check_description_triggers(meta: dict, min_tokens: int = MIN_TRIGGER_TOKENS) -> tuple[int, bool]:
    """Description 내 comma-separated 트리거 키워드 개수 추정 (AGENT-08).

    Heuristic: 쉼표 분리 토큰 또는 공백 분리 한글/영문 명사구 5자 이상 단어를 후보로 카운트.
    """
    desc = meta.get("description", "")
    # Use comma-separated tokens first
    candidates = [t.strip() for t in desc.split(",") if len(t.strip()) >= 2]
    if len(candidates) >= min_tokens:
        return len(candidates), True
    # Fallback: count 5+ char tokens separated by whitespace
    tokens = [t for t in desc.split() if len(t) >= 5]
    return len(tokens), len(tokens) >= min_tokens


def check_must_remember_position(body: str) -> tuple[int, float, int]:
    """Return (header_line_idx, ratio_from_end, total_lines).

    header_line_idx == -1 means header not found.
    ratio_from_end == (total - idx) / total — smaller = closer to end.
    AGENT-09: ratio_from_end should be ≤ 0.4 (MUST REMEMBER in final 40% of body).
    """
    lines = body.splitlines()
    total = len(lines)
    if total == 0:
        return -1, 0.0, 0
    for i, line in enumerate(lines):
        if line.strip().startswith(MUST_REMEMBER_HEADER):
            ratio = (total - i) / total
            return i, ratio, total
    return -1, 0.0, total


def audit_agent(md_path: pathlib.Path, strict: bool = False) -> list[str]:
    """Audit a single AGENT.md. Returns list of violation strings (empty = OK)."""
    violations: list[str] = []
    try:
        meta, body = parse_frontmatter(md_path)
    except ValueError as e:
        return [f"{md_path}: frontmatter parse failed — {e}"]

    total_lines, line_ok = check_line_count(md_path)
    if not line_ok:
        violations.append(f"{md_path}: {total_lines} lines > {LINE_LIMIT} (AGENT-07)")

    desc_len, desc_ok = check_description_chars(meta)
    if not desc_ok:
        violations.append(f"{md_path}: description {desc_len} chars > {DESC_LIMIT} (AGENT-08)")

    trigger_count, trigger_ok = check_description_triggers(meta)
    if not trigger_ok:
        violations.append(
            f"{md_path}: description only {trigger_count} trigger tokens "
            f"(need >= {MIN_TRIGGER_TOKENS}, AGENT-08)"
        )

    mr_idx, mr_ratio, body_total = check_must_remember_position(body)
    if mr_idx == -1:
        violations.append(f"{md_path}: '## MUST REMEMBER' section missing (AGENT-09)")
    elif mr_ratio > MUST_REMEMBER_MAX_RATIO_FROM_END:
        violations.append(
            f"{md_path}: MUST REMEMBER at line {mr_idx}/{body_total} "
            f"(ratio_from_end={mr_ratio:.2f} > {MUST_REMEMBER_MAX_RATIO_FROM_END}, AGENT-09)"
        )
    return violations


def discover_agents(root: pathlib.Path, exclude: set[str]) -> list[pathlib.Path]:
    """Walk `root` for AGENT.md files, skipping any whose parent dir name is in `exclude`.

    Also skips any AGENT.md whose ancestor path matches `_shared` / `_patterns_reference`
    (those are templates, not real agents).
    """
    results: list[pathlib.Path] = []
    for md in sorted(root.rglob("AGENT.md")):
        parts = set(p.name for p in md.parents)
        if parts & {"_shared", "_patterns_reference"}:
            continue
        parent_name = md.parent.name
        if parent_name in exclude:
            continue
        results.append(md)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AGENT-07/08/09 validator")
    parser.add_argument("--path", default=".claude/agents", help="Root dir to scan for AGENT.md")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Agent dir name to exclude (repeatable). e.g. --exclude harvest-importer",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="(reserved) treat warnings as errors. Currently all checks are errors.",
    )
    args = parser.parse_args(argv)

    root = pathlib.Path(args.path)
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 1

    agents = discover_agents(root, set(args.exclude))

    all_violations: list[str] = []
    for md in agents:
        all_violations.extend(audit_agent(md, strict=args.strict))

    if all_violations:
        for v in all_violations:
            print(v, file=sys.stderr)
        print(f"FAIL: {len(all_violations)} violation(s) across {len(agents)} agent(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(agents)} agent(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
