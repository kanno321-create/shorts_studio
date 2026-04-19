"""harness-audit wrapper — Phase 4 Wave 5 entrypoint.

Combines:
- validate_all_agents (AGENT-07/08/09 line/desc/MUST REMEMBER)
- rubric_stdlib_validator (RUB-04 schema sanity on a canonical sample)
- RUB-06 grep: `producer_prompt` / `producer_system_context` must not appear under
  .claude/agents/inspectors/ (GAN separation).

Scoring: base 100, -10 per file violation, -5 per warning.
Prints `HARNESS_AUDIT_SCORE: N` and exits 0 if N >= 80 else 1.

CLI:
    py -3.11 -m scripts.validate.harness_audit [--agents-root DIR] [--exclude NAME] [--threshold 80]

Phase 10 Wave 5 calls this exact script as the single audit entry-point.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: F401
    from scripts.validate.rubric_stdlib_validator import validate_rubric
    from scripts.validate.validate_all_agents import (
        audit_agent,
        discover_agents,
    )
    from scripts.validate.grep_gan_contamination import check_file as gan_check_file
else:
    from .parse_frontmatter import parse_frontmatter  # noqa: F401
    from .rubric_stdlib_validator import validate_rubric
    from .validate_all_agents import audit_agent, discover_agents
    from .grep_gan_contamination import check_file as gan_check_file


SAMPLE_VALID_RUBRIC = {
    "verdict": "PASS",
    "score": 85,
    "evidence": [],
    "semantic_feedback": "",
}


# ---------------------------------------------------------------------------
# D-11 JSON extension (Phase 7 Wave 0) — additive, backward-compatible
# ---------------------------------------------------------------------------

_SCAN_ROOTS = [
    pathlib.Path("scripts"),
    pathlib.Path(".claude/agents"),
    pathlib.Path("tests"),
    pathlib.Path("wiki"),
]
_SKILL_ROOT = pathlib.Path(".claude/skills")
_DEPRECATED_PATTERNS_JSON = pathlib.Path(".claude/deprecated_patterns.json")


def _scan_deprecated_patterns(
    patterns_json: pathlib.Path = _DEPRECATED_PATTERNS_JSON,
) -> dict[str, int]:
    """Scan 4 roots for each deprecated_patterns.json regex; return {name: count}.

    Keys are stable short names derived from the regex ``reason`` field or the
    first segment before ':'. Excludes the audit script itself and the
    patterns JSON from self-referential scans.
    """
    if not patterns_json.exists():
        return {}
    try:
        raw = json.loads(patterns_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    patterns = raw.get("patterns", raw) if isinstance(raw, dict) else raw
    # Build skip-set: scanner must NOT match its own regex definitions.
    this_file = pathlib.Path(__file__).resolve()
    skip_paths = {this_file, patterns_json.resolve()}
    counts: dict[str, int] = {}
    for entry in patterns:
        regex_str = entry.get("regex") or entry.get("pattern") or ""
        if not regex_str:
            continue
        reason = entry.get("reason", "")
        # Stable short name: text before ':' in reason, else first 24 chars of regex.
        key = entry.get("name") or reason.split(":")[0].strip() or regex_str[:24]
        try:
            rx = re.compile(regex_str)
        except re.error:
            counts[key] = 0
            continue
        n = 0
        for root in _SCAN_ROOTS:
            if not root.exists():
                continue
            for p in root.rglob("*"):
                if not p.is_file() or p.suffix not in {".py", ".md", ".json"}:
                    continue
                try:
                    if p.resolve() in skip_paths:
                        continue
                except OSError:
                    pass
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                n += len(rx.findall(text))
        counts[key] = n
    return counts


def _count_agents(agents_root: pathlib.Path) -> int:
    """Count AGENT.md files under agents_root (includes harvest-importer etc.)."""
    if not agents_root.exists():
        return 0
    return sum(1 for _ in agents_root.rglob("AGENT.md"))


def _skills_over_500_lines(skills_root: pathlib.Path = _SKILL_ROOT) -> list[str]:
    """Return relative POSIX paths of SKILL.md files exceeding 500 lines."""
    out: list[str] = []
    if not skills_root.exists():
        return out
    for p in skills_root.rglob("SKILL.md"):
        try:
            with p.open(encoding="utf-8") as f:
                line_count = sum(1 for _ in f)
        except OSError:
            continue
        if line_count > 500:
            out.append(str(p).replace("\\", "/"))
    return out


def _descriptions_over_1024(agents_root: pathlib.Path) -> list[str]:
    """Return relative POSIX paths of AGENT.md with frontmatter description > 1024 chars."""
    out: list[str] = []
    if not agents_root.exists():
        return out
    desc_rx = re.compile(r"^description:\s*(.*)$", re.MULTILINE)
    for p in agents_root.rglob("AGENT.md"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = desc_rx.search(text)
        if m and len(m.group(1).strip()) > 1024:
            out.append(str(p).replace("\\", "/"))
    return out


def _a_rank_drift_count(violations: list[str]) -> int:
    """A-rank drift contribution from validator violations (non-deprecated-regex)."""
    return sum(1 for v in violations if "A급" in v or "A-rank" in v or "drift" in v.lower())


def _build_d11_report(
    score: int,
    violations: list[str],
    agents_root: pathlib.Path,
) -> dict:
    """D-11 6-key schema (+ phase + timestamp metadata)."""
    deprecated = _scan_deprecated_patterns()
    a_rank_from_deprecated = sum(deprecated.values())
    return {
        "score": int(score),
        "a_rank_drift_count": _a_rank_drift_count(violations) + a_rank_from_deprecated,
        "skill_over_500_lines": _skills_over_500_lines(),
        "agent_count": _count_agents(agents_root),
        "description_over_1024": _descriptions_over_1024(agents_root),
        "deprecated_pattern_matches": deprecated,
        "phase": 7,
        "timestamp": _dt.datetime.now(_dt.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }


def _score_penalty(n_violations: int, n_warnings: int) -> int:
    return 100 - (n_violations * 10) - (n_warnings * 5)


def run_audit(agents_root: pathlib.Path, exclude: set[str], schema_path: pathlib.Path) -> tuple[int, list[str], list[str]]:
    """Return (score, violations, warnings)."""
    violations: list[str] = []
    warnings: list[str] = []

    # Stage 1: AGENT-07/08/09
    agents = discover_agents(agents_root, exclude)
    if not agents:
        warnings.append(f"no AGENT.md found under {agents_root} (expected during early Wave 0)")
    for md in agents:
        violations.extend(audit_agent(md))

    # Stage 2: RUB-04 schema sanity — canonical valid rubric must validate clean
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        violations.append(f"{schema_path}: failed to load schema — {e}")
        return _score_penalty(len(violations), len(warnings)), violations, warnings

    errs = validate_rubric(SAMPLE_VALID_RUBRIC, schema)
    if errs:
        violations.append(f"rubric schema sanity failed on canonical sample: {errs}")

    # Stage 3: RUB-06 GAN leak check under inspectors/ — parses ## Inputs table only
    # (negation references in MUST REMEMBER / docs are allowed — see grep_gan_contamination.py)
    inspectors_dir = agents_root / "inspectors"
    if inspectors_dir.exists():
        for md in inspectors_dir.rglob("AGENT.md"):
            try:
                violations.extend(gan_check_file(md))
            except OSError as e:
                warnings.append(f"{md}: read failed — {e}")

    score = _score_penalty(len(violations), len(warnings))
    return score, violations, warnings


def main(argv: list[str] | None = None) -> int:
    # Phase 7 D-22: UTF-8 stdout guard for Windows cp949 default encoding.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(description="harness-audit wrapper (Phase 4 Wave 5 entrypoint)")
    parser.add_argument("--agents-root", default=".claude/agents")
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument(
        "--schema",
        default=".claude/agents/_shared/rubric-schema.json",
        help="Path to rubric-schema.json",
    )
    parser.add_argument("--threshold", type=int, default=80)
    parser.add_argument(
        "--json-out",
        type=pathlib.Path,
        default=None,
        help=(
            "If set, write D-11 6-key JSON report to this path. "
            "Legacy text output (HARNESS_AUDIT_SCORE: N) is always preserved "
            "on stdout regardless of this flag (Phase 7 Pitfall 8)."
        ),
    )
    args = parser.parse_args(argv)

    score, violations, warnings = run_audit(
        pathlib.Path(args.agents_root),
        set(args.exclude),
        pathlib.Path(args.schema),
    )

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for v in violations:
        print(f"VIOL: {v}", file=sys.stderr)

    # Legacy text output — MUST be preserved (Phase 4 Wave 5 acceptance grep-parses this).
    print(f"HARNESS_AUDIT_SCORE: {score}")
    print(f"  violations: {len(violations)}")
    print(f"  warnings:   {len(warnings)}")

    # Phase 7 D-11 additive JSON emission.
    if args.json_out is not None:
        report = _build_d11_report(
            score, violations, pathlib.Path(args.agents_root)
        )
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if score >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
