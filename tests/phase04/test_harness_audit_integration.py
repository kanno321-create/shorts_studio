"""Phase 4 Plan 10 — VALIDATION row 4-10-01.

harness_audit.py must emit HARNESS_AUDIT_SCORE >= 80 across all 32 non-harvest
agents. This is AUDIT-02 Phase 10 baseline preparation.

harness_audit aggregates:
- validate_all_agents (AGENT-07/08/09)
- rubric_stdlib_validator (RUB-04 schema sanity)
- grep_gan_contamination (RUB-06 GAN separation)
"""
from __future__ import annotations

import re
import subprocess
import sys


def test_harness_audit_score_ge_80() -> None:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.validate.harness_audit",
            "--agents-root",
            ".claude/agents",
            "--exclude",
            "harvest-importer",
        ],
        capture_output=True,
        text=True,
    )
    combined = r.stdout + "\n" + r.stderr
    match = re.search(r"HARNESS_AUDIT_SCORE:\s*(-?\d+)", combined)
    assert match, (
        f"harness_audit did not emit HARNESS_AUDIT_SCORE marker.\n"
        f"stdout={r.stdout}\nstderr={r.stderr}"
    )
    score = int(match.group(1))
    assert score >= 80, (
        f"harness_audit score {score} < 80 (AUDIT-02 threshold).\n"
        f"stderr={r.stderr}"
    )
    assert r.returncode == 0, (
        f"harness_audit exited {r.returncode}. stderr={r.stderr}"
    )
