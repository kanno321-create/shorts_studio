"""D-12 + progressive-disclosure: no SKILL.md exceeds 500 lines.

Plan 07-07 Task 7-07-03. Two levels of assertion:
1. Audit report: `skill_over_500_lines == []`.
2. Independent filesystem scan agrees with the audit (double-entry
   bookkeeping — catches the audit helper silently regressing).

Also sanity-checks inheritance of the 5 canonical shared skills
(harness-audit, drift-detection, progressive-disclosure,
gate-dispatcher, context-compressor) per 07-CONTEXT §canonical_refs.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "scripts" / "validate" / "harness_audit.py"
_SKILLS = _REPO / ".claude" / "skills"


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


def test_skill_over_500_lines_is_empty(tmp_path: Path):
    report = _run_audit_json(tmp_path)
    assert report["skill_over_500_lines"] == [], (
        f"D-12 violated: SKILL.md files over 500 lines: "
        f"{report['skill_over_500_lines']}"
    )


def test_filesystem_scan_confirms_no_skill_over_500():
    """Independent filesystem scan must agree with harness_audit report."""
    if not _SKILLS.exists():
        return
    offenders = []
    for p in _SKILLS.rglob("SKILL.md"):
        with p.open(encoding="utf-8") as f:
            n = sum(1 for _ in f)
        if n > 500:
            offenders.append((str(p), n))
    assert offenders == [], (
        f"D-12 violated by filesystem scan: {offenders}"
    )


def test_inherited_harness_skills_present():
    """Sanity: 5 canonical shared skills inherited from harness/ exist."""
    inherited = {
        "harness-audit",
        "drift-detection",
        "progressive-disclosure",
        "gate-dispatcher",
        "context-compressor",
    }
    if not _SKILLS.exists():
        return
    present_dirs = {p.name for p in _SKILLS.iterdir() if p.is_dir()}
    missing = inherited - present_dirs
    # Allow partial — but at minimum progressive-disclosure must be present.
    assert "progressive-disclosure" in present_dirs, (
        f"canonical skill progressive-disclosure missing from {_SKILLS}. "
        f"Present: {sorted(present_dirs)}"
    )
    # And all 5 should exist per CONTEXT §canonical_refs.
    assert not missing, (
        f"Expected inherited harness skills missing: {missing}. "
        f"Present: {sorted(present_dirs)}"
    )


def test_filesystem_and_audit_report_agree(tmp_path: Path):
    """Both scans should produce the same SKILL.md-over-500 list."""
    report = _run_audit_json(tmp_path)
    fs_over_500 = []
    if _SKILLS.exists():
        for p in _SKILLS.rglob("SKILL.md"):
            with p.open(encoding="utf-8") as f:
                n = sum(1 for _ in f)
            if n > 500:
                fs_over_500.append(str(p).replace("\\", "/"))
    # Both should be empty on current codebase.
    assert fs_over_500 == []
    assert report["skill_over_500_lines"] == []
    # Cross-check lengths match even if both are 0.
    assert len(fs_over_500) == len(report["skill_over_500_lines"])
