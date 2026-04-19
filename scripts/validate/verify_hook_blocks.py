#!/usr/bin/env python3
"""Feed 5 mock tool-use payloads to .claude/hooks/pre_tool_use.py; assert
decision=deny for blacklisted content and decision=allow for the positive
control.

Run: python scripts/validate/verify_hook_blocks.py
Exit 0 if all 4 deny checks + 1 allow check pass; exit 1 on regression.

Covers ORCH-08 (skip_gates), ORCH-09 (TODO next-session), VIDEO-01 (T2V),
AF-8 (selenium), + I2V allow control.

Stdlib-only; indirect through the Hook (no direct JSON load here) so this
validator picks up any future blocklist additions automatically.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# scripts/validate/verify_hook_blocks.py -> parents[2] = studios/shorts/
STUDIO_ROOT = Path(__file__).resolve().parents[2]
HOOK = STUDIO_ROOT / ".claude" / "hooks" / "pre_tool_use.py"


def _hook_check(
    tool_name: str,
    content: str,
    file_path: str = "scripts/orchestrator/shorts_pipeline.py",
) -> dict:
    """Spawn pre_tool_use.py as subprocess with mock payload; return decision dict.

    pre_tool_use.py reads DIFFERENT fields per tool:
        - Write     -> input.content
        - Edit      -> input.new_string
        - MultiEdit -> input.edits[*].new_string
    """
    tool_input: dict = {"file_path": file_path}
    if tool_name == "Write":
        tool_input["content"] = content
    elif tool_name == "Edit":
        tool_input["new_string"] = content
        tool_input["old_string"] = ""  # Edit contract requires old_string too
    elif tool_name == "MultiEdit":
        tool_input["edits"] = [{"old_string": "", "new_string": content}]
    else:
        tool_input["content"] = content
    payload = {"tool_name": tool_name, "input": tool_input}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=5,
        cwd=str(STUDIO_ROOT),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Hook exited {proc.returncode}: stderr={proc.stderr!r}"
        )
    return json.loads(proc.stdout)


CASES = [
    (
        "deny",
        "Write",
        "def run(session_id, skip_gates=True):\n    pass",
        "skip_gates should be blocked (ORCH-08)",
    ),
    (
        "deny",
        "Edit",
        "# TODO(next-session): wire remaining inspectors",
        "TODO(next-session) should be blocked (ORCH-09)",
    ),
    (
        "deny",
        "Write",
        "def text_to_video(prompt: str):\n    return None",
        "T2V should be blocked (VIDEO-01)",
    ),
    (
        "deny",
        "Write",
        "import selenium\nfrom selenium.webdriver import Chrome",
        "selenium should be blocked (AF-8)",
    ),
    (
        "allow",
        "Write",
        "def image_to_video(anchor_frame, prompt: str):\n    pass",
        "I2V should be allowed (positive control)",
    ),
]


def main() -> int:
    if not HOOK.exists():
        print(f"FAIL: Hook not found at {HOOK}", file=sys.stderr)
        return 1
    failures: list[str] = []
    for expected, tool, content, description in CASES:
        try:
            res = _hook_check(tool, content)
        except Exception as e:
            failures.append(f"EXEC ERROR [{description}]: {e}")
            continue
        decision = res.get("decision", "allow")
        if decision != expected:
            failures.append(
                f"REGRESSION [{description}]: expected {expected}, got {decision} "
                f"(reason: {res.get('reason', '?')})"
            )
    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print(f"PASS: all {len(CASES)} hook enforcement checks green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
