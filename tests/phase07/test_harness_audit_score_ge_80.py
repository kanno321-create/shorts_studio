"""SC5 primary gate: harness_audit score must be >= 80.

Plan 07-07 Task 7-07-02. ROADMAP SC5 contract: the audit score must stay
at or above 80 for Phase 7 to ship. Current baseline = 90.

Three angles verified:
1. CLI `--threshold 80` exits 0 (integration — score >= threshold).
2. JSON `--json-out` report["score"] >= 80 (data contract).
3. Legacy text line "HARNESS_AUDIT_SCORE: N" still parseable and >= 80
   (Pitfall 8: backward-compat line must remain for Phase 4/10 pipelines).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_AUDIT = _REPO / "scripts" / "validate" / "harness_audit.py"


def test_default_threshold_80_pass():
    """CLI exits 0 iff score >= threshold (default 80)."""
    result = subprocess.run(
        [sys.executable, str(_AUDIT), "--threshold", "80"],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, (
        f"harness_audit exit {result.returncode} (score < 80)\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_json_score_exceeds_80(tmp_path: Path):
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
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["score"] >= 80, (
        f"SC5 violated: score {report['score']} < 80"
    )


def test_text_output_reports_score_line():
    """Legacy HARNESS_AUDIT_SCORE: N line present and >= 80 (Pitfall 8)."""
    result = subprocess.run(
        [sys.executable, str(_AUDIT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert "HARNESS_AUDIT_SCORE:" in result.stdout
    score_found = False
    for line in result.stdout.splitlines():
        if line.startswith("HARNESS_AUDIT_SCORE:"):
            parts = line.split(":")
            score = int(parts[1].strip())
            assert score >= 80, (
                f"Legacy HARNESS_AUDIT_SCORE={score} < 80 (SC5 violated)"
            )
            score_found = True
            break
    assert score_found, "HARNESS_AUDIT_SCORE line missing from stdout"
