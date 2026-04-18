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
else:
    from .parse_frontmatter import parse_frontmatter  # noqa: F401
    from .rubric_stdlib_validator import validate_rubric
    from .validate_all_agents import audit_agent, discover_agents


SAMPLE_VALID_RUBRIC = {
    "verdict": "PASS",
    "score": 85,
    "evidence": [],
    "semantic_feedback": "",
}

FORBIDDEN_LEAK_PATTERN = re.compile(r"\b(producer_prompt|producer_system_context)\b")


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

    # Stage 3: RUB-06 GAN leak grep under inspectors/
    inspectors_dir = agents_root / "inspectors"
    if inspectors_dir.exists():
        for md in inspectors_dir.rglob("AGENT.md"):
            try:
                text = md.read_text(encoding="utf-8")
            except OSError as e:
                warnings.append(f"{md}: read failed — {e}")
                continue
            if FORBIDDEN_LEAK_PATTERN.search(text):
                violations.append(
                    f"{md}: forbidden Producer context leak token "
                    f"(producer_prompt|producer_system_context) — RUB-06"
                )

    score = _score_penalty(len(violations), len(warnings))
    return score, violations, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="harness-audit wrapper (Phase 4 Wave 5 entrypoint)")
    parser.add_argument("--agents-root", default=".claude/agents")
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument(
        "--schema",
        default=".claude/agents/_shared/rubric-schema.json",
        help="Path to rubric-schema.json",
    )
    parser.add_argument("--threshold", type=int, default=80)
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

    print(f"HARNESS_AUDIT_SCORE: {score}")
    print(f"  violations: {len(violations)}")
    print(f"  warnings:   {len(warnings)}")

    return 0 if score >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
