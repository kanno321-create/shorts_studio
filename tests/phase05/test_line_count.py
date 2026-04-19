"""SC 1 line-count contract: ``shorts_pipeline.py`` in [500, 800] + support-module caps.

The 500-800 range for the keystone is non-negotiable (D-1). Support
modules have soft caps derived from Wave 1-4 actuals + headroom, so a
future refactor that accidentally re-introduces a 5166-line drift would
fail loudly here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def test_shorts_pipeline_in_500_800() -> None:
    """SC 1 / ORCH-01 / D-1: shorts_pipeline.py is the 500-800 line keystone."""
    target = REPO / "scripts" / "orchestrator" / "shorts_pipeline.py"
    assert target.exists(), "Plan 07 did not produce shorts_pipeline.py"
    n = _count_lines(target)
    assert 500 <= n <= 800, f"SC 1 VIOLATED: shorts_pipeline.py has {n} lines (expected [500, 800])"


def test_support_modules_under_soft_caps() -> None:
    """Sanity: Wave 1-2 support modules stay under their soft caps.

    Soft caps derived from Wave 1-4 actuals + headroom. A future refactor
    that grows a support module past its cap must be deliberate (bump
    the cap in this test) — silent growth is blocked.
    """
    support = {
        "gates.py": 250,
        "circuit_breaker.py": 260,
        "checkpointer.py": 280,
        "gate_guard.py": 240,
        "voice_first_timeline.py": 360,
        "fallback.py": 200,
    }
    failures: list[str] = []
    for name, max_lines in support.items():
        target = REPO / "scripts" / "orchestrator" / name
        if not target.exists():
            pytest.skip(f"{name} not yet present")
        n = _count_lines(target)
        if n > max_lines:
            failures.append(f"{name}: {n} lines (soft cap {max_lines})")
    assert not failures, "Support module cap breach:\n" + "\n".join(failures)


def test_api_adapters_under_soft_caps() -> None:
    """Sanity: API adapter modules stay within budget."""
    api = REPO / "scripts" / "orchestrator" / "api"
    if not api.exists():
        pytest.skip("scripts/orchestrator/api/ not present")
    caps = {
        "models.py": 180,
        "kling_i2v.py": 260,
        "runway_i2v.py": 240,
        "typecast.py": 400,
        "elevenlabs.py": 340,
        "shotstack.py": 400,
    }
    failures: list[str] = []
    for name, max_lines in caps.items():
        target = api / name
        if not target.exists():
            continue
        n = _count_lines(target)
        if n > max_lines:
            failures.append(f"{name}: {n} lines (soft cap {max_lines})")
    assert not failures, "API adapter cap breach:\n" + "\n".join(failures)


def test_api_models_has_substance() -> None:
    """Lower bound: models.py pydantic contracts should not be empty."""
    target = REPO / "scripts" / "orchestrator" / "api" / "models.py"
    if not target.exists():
        pytest.skip("models.py not present")
    n = _count_lines(target)
    assert n >= 40, f"models.py suspiciously short ({n} lines) — pydantic contracts missing?"


def test_hc_checks_under_rewrite_budget() -> None:
    """hc_checks.py is a rewrite of 1129-line baseline; cap at 1200 for headroom."""
    target = REPO / "scripts" / "hc_checks" / "hc_checks.py"
    if not target.exists():
        pytest.skip("hc_checks.py not yet rewritten")
    n = _count_lines(target)
    assert n <= 1200, f"hc_checks.py has {n} lines (baseline 1129; cap 1200)"


def test_line_count_verifier_cli_accepts_pipeline() -> None:
    """Plan 01's verify_line_count.py CLI still validates the keystone."""
    target = REPO / "scripts" / "orchestrator" / "shorts_pipeline.py"
    verifier = REPO / "scripts" / "validate" / "verify_line_count.py"
    if not verifier.exists():
        pytest.skip("verify_line_count.py missing — Plan 01 incomplete")
    result = subprocess.run(
        [sys.executable, str(verifier), str(target), "500", "800"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    assert result.returncode == 0, (
        f"verify_line_count.py CLI failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
