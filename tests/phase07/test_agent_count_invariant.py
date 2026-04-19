"""CLAUDE.md + harness_audit: agent_count report matches filesystem discovery.

Plan 07-07 Task 7-07-05. Verifies the D-10 invariant:
- agent_count reported by the audit is the same as an independent
  recursive `rglob("AGENT.md")` scan of .claude/agents/.
- agent_count falls in a sane range (1..100) so a regression that
  silently wipes agents is caught.

Current codebase: 33 AGENT.md files (Producer 14 + Inspector 17 +
Supervisor 1 + harvest-importer 1).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "scripts" / "validate" / "harness_audit.py"
_AGENTS = _REPO / ".claude" / "agents"


def _run_audit_json(tmp_path: Path) -> dict:
    out = tmp_path / "audit.json"
    subprocess.run(
        [sys.executable, str(_AUDIT), "--json-out", str(out)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return json.loads(out.read_text(encoding="utf-8"))


def test_agent_count_is_positive(tmp_path: Path):
    report = _run_audit_json(tmp_path)
    assert report["agent_count"] >= 1


def test_agent_count_matches_filesystem(tmp_path: Path):
    """Double-entry bookkeeping: audit agent_count equals filesystem rglob."""
    assert _AGENTS.exists(), f".claude/agents missing at {_AGENTS}"
    fs_count = sum(1 for _ in _AGENTS.rglob("AGENT.md"))
    report = _run_audit_json(tmp_path)
    assert report["agent_count"] == fs_count, (
        f"harness_audit agent_count={report['agent_count']} != "
        f"filesystem={fs_count}"
    )


def test_agent_count_in_declared_range():
    """CLAUDE.md documents 32 core agents (Producer 14 + Inspector 17 +
    Supervisor 1); harvest-importer brings total to 33. Sanity window
    1..100 catches accidental wipes or runaway duplication.
    """
    assert _AGENTS.exists()
    fs_count = sum(1 for _ in _AGENTS.rglob("AGENT.md"))
    assert 1 <= fs_count <= 100, (
        f"Sanity: agent count {fs_count} outside 1..100"
    )
    # AUDIT-02 minimum declared is 12 (original scaffold); current is 33.
    # Enforce >= 12 so a regression dropping below the baseline trips here.
    assert fs_count >= 12, (
        f"AUDIT-02: agent count {fs_count} below declared minimum 12"
    )
