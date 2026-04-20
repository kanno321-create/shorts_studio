"""RED stub for Hook 3종 hygiene — Wave 3 alignment.

Scans Phase 9.1 target files for three forbidden patterns:
    - "skip_gates" literal
    - "TODO(next-session)" literal
    - try/except with a body that is a single `pass` statement (silent swallow)

Wave 4 aggregator re-runs these. RED until all Wave 1~3 landed files exist.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_FILES = [
    _REPO_ROOT / "scripts" / "orchestrator" / "invokers.py",
    _REPO_ROOT / "scripts" / "orchestrator" / "api" / "nanobanana.py",
    _REPO_ROOT / "scripts" / "orchestrator" / "api" / "ken_burns.py",
    _REPO_ROOT / "scripts" / "orchestrator" / "character_registry.py",
    _REPO_ROOT / "scripts" / "orchestrator" / "voice_discovery.py",
    _REPO_ROOT / "scripts" / "smoke" / "phase091_stage2_to_4.py",
]


def test_no_skip_gates_in_new_files() -> None:
    """Hook: 'skip_gates' substring count must be 0 across all Wave 1~3 target files."""
    violations = []
    missing = []
    for f in TARGET_FILES:
        if not f.exists():
            missing.append(f)
            continue
        text = f.read_text(encoding="utf-8")
        if "skip_gates" in text:
            violations.append(str(f))
    assert not missing, (
        f"Wave 1~3 target files missing (RED state expected): {[str(m) for m in missing]}"
    )
    assert not violations, f"skip_gates found in: {violations}"


def test_no_todo_next_session() -> None:
    """Hook: 'TODO(next-session)' literal count must be 0."""
    violations = []
    missing = []
    for f in TARGET_FILES:
        if not f.exists():
            missing.append(f)
            continue
        text = f.read_text(encoding="utf-8")
        if "TODO(next-session)" in text:
            violations.append(str(f))
    assert not missing, (
        f"Wave 1~3 target files missing (RED state expected): {[str(m) for m in missing]}"
    )
    assert not violations, f"TODO(next-session) found in: {violations}"


def test_no_silent_except_pass() -> None:
    """Hook: AST-walk every ExceptHandler; body MUST NOT be a single `Pass` stmt."""
    violations = []
    missing = []
    for f in TARGET_FILES:
        if not f.exists():
            missing.append(f)
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                body = node.body
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    violations.append(f"{f}:{node.lineno}")
    assert not missing, (
        f"Wave 1~3 target files missing (RED state expected): {[str(m) for m in missing]}"
    )
    assert not violations, f"silent except: pass found at: {violations}"
