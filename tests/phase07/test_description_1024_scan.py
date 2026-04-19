"""AGENT-09: description yaml field <= 1024 chars across all AGENT.md.

Plan 07-07 Task 7-07-06. AGENT-09 rule: each AGENT.md frontmatter
description field must stay within 1024 characters so ``list_tools``
prompts remain scannable for the supervisor router.

Three angles:
1. Audit report: description_over_1024 == [].
2. Independent filesystem scan: no AGENT.md frontmatter description
   exceeds 1024 chars (catches audit helper regression).
3. Sanity: at least one AGENT.md has a description field (non-empty
   frontmatter).
"""
from __future__ import annotations

import json
import re
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


def test_description_over_1024_is_empty(tmp_path: Path):
    report = _run_audit_json(tmp_path)
    assert report["description_over_1024"] == [], (
        f"AGENT-09 violated: descriptions over 1024 chars: "
        f"{report['description_over_1024']}"
    )


def test_filesystem_description_scan_agrees():
    """Double-entry bookkeeping: independent filesystem scan agrees with audit."""
    if not _AGENTS.exists():
        return
    desc_rx = re.compile(r"^description:\s*(.*)$", re.MULTILINE)
    offenders = []
    for p in _AGENTS.rglob("AGENT.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = desc_rx.search(text)
        if m and len(m.group(1).strip()) > 1024:
            offenders.append(str(p))
    assert offenders == [], (
        f"AGENT-09 violated by filesystem scan: {offenders}"
    )


def test_at_least_one_agent_has_description():
    """Sanity: AGENT.md files exist AND at least one carries a description field."""
    assert _AGENTS.exists()
    desc_rx = re.compile(r"^description:\s*(.*)$", re.MULTILINE)
    with_desc = 0
    for p in _AGENTS.rglob("AGENT.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if desc_rx.search(text):
            with_desc += 1
    assert with_desc >= 1, (
        f"No AGENT.md carries a description field — frontmatter wiped?"
    )


def test_filesystem_and_audit_1024_lists_agree(tmp_path: Path):
    """Audit's description_over_1024 list must equal filesystem scan."""
    if not _AGENTS.exists():
        return
    desc_rx = re.compile(r"^description:\s*(.*)$", re.MULTILINE)
    fs_over = []
    for p in _AGENTS.rglob("AGENT.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = desc_rx.search(text)
        if m and len(m.group(1).strip()) > 1024:
            fs_over.append(str(p).replace("\\", "/"))
    report = _run_audit_json(tmp_path)
    # Lists should agree (both empty on healthy codebase).
    assert sorted(fs_over) == sorted(report["description_over_1024"])
