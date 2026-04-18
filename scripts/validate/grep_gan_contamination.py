"""RUB-06 GAN separation enforcement (Phase 4 Plan 10 Wave 5).

Inspector AGENT.md files must NOT have `producer_prompt` / `producer_system_context`
as *field entries* in the `## Inputs` Markdown table (these would leak Producer
context into the Reviewer pipeline — GAN separation violation).

It IS explicitly OK for these strings to appear in:
  - MUST REMEMBER / documentation as negation ("producer_prompt 읽기 금지")
  - RUB-06 variant notes ("Inputs는 producer_prompt 필드를 절대 포함하지 않는다")
  - Supervisor fan-out rules ("producer_output만 전달, producer_prompt 차단")

Strategy: parse each Inspector AGENT.md, locate the `## Inputs` section,
check only table rows whose first cell matches a forbidden flag pattern.

Exit 0 + prints `GAN_CLEAN: N inspector AGENT.md files verified clean` on success.
Exit 1 + prints violations on stderr on failure.

CLI:
    py -3.11 -m scripts.validate.grep_gan_contamination [--path DIR]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

DEFAULT_INSPECTORS_DIR = pathlib.Path(".claude/agents/inspectors")
FORBIDDEN_FLAGS = ["producer_prompt", "producer_system_context", "producer_system"]


def check_file(md_path: pathlib.Path) -> list[str]:
    """Check a single AGENT.md for forbidden flag names in its ## Inputs table.

    Returns list of violation strings (empty = clean).
    """
    text = md_path.read_text(encoding="utf-8")
    # Find ## Inputs section (between "## Inputs" and the next "## " header or EOF)
    m = re.search(r"^##\s+Inputs\s*\n(.*?)(?=^##\s|\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return []
    inputs_block = m.group(1)

    violations: list[str] = []
    # Only flag rows of the form:  | `producer_prompt` | ... |   or   | producer_prompt | ... |
    # The first cell after leading `|` must *start* with the forbidden token
    # (ignoring leading backtick / whitespace).
    for flag in FORBIDDEN_FLAGS:
        # Match: | optional_backtick + flag + (possibly .subfield or closing backtick) + |
        # Negative: lowercase flag must be the *leading* identifier in the cell.
        pattern = rf"^\s*\|\s*`?-{{0,2}}{re.escape(flag)}(?:\.[a-zA-Z_]\w*)?`?\s*\|"
        if re.search(pattern, inputs_block, re.MULTILINE):
            violations.append(
                f"{md_path}: ## Inputs table contains forbidden flag field '{flag}' (RUB-06)"
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RUB-06 GAN contamination check")
    parser.add_argument(
        "--path",
        default=str(DEFAULT_INSPECTORS_DIR),
        help="Root dir to scan for inspector AGENT.md (default: .claude/agents/inspectors)",
    )
    args = parser.parse_args(argv)

    inspectors_dir = pathlib.Path(args.path)
    if not inspectors_dir.exists():
        print(f"ERROR: path does not exist: {inspectors_dir}", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    md_files = sorted(inspectors_dir.rglob("AGENT.md"))
    for md_path in md_files:
        all_violations.extend(check_file(md_path))

    if all_violations:
        for v in all_violations:
            print(v, file=sys.stderr)
        print(f"GAN_CONTAMINATION: {len(all_violations)} violation(s)", file=sys.stderr)
        return 1

    print(f"GAN_CLEAN: {len(md_files)} inspector AGENT.md files verified clean (RUB-06)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
