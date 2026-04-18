"""Phase 4 Plan 10 — VALIDATION row 4-10-02.

RUB-06 GAN separation: inspector AGENT.md `## Inputs` tables must not contain
`producer_prompt` / `producer_system_context` / `producer_system` as field names.

Uses scripts.validate.grep_gan_contamination (smart, table-aware check).
Raw-grep in inspector docs (negation references) is allowed and must not trip this test.
"""
from __future__ import annotations

import subprocess
import sys


def test_grep_gan_contamination_exit_0() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "scripts.validate.grep_gan_contamination"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (
        f"GAN contamination detected (RUB-06 violation).\n"
        f"stdout: {r.stdout}\nstderr: {r.stderr}"
    )
    assert "GAN_CLEAN" in r.stdout, f"Expected GAN_CLEAN marker in stdout, got: {r.stdout}"
