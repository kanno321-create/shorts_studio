"""Wave 6 — subprocess wrapper asserts phase08_acceptance.py ships all 6 SC green.

Mirrors tests/phase07/test_phase07_acceptance.py (Phase 7 Plan 07-08 canonical).
Subprocess-invokes the Phase 8 acceptance aggregator and asserts:

- Script file exists on disk at the canonical scripts/validate path
- Subprocess exit code is 0 (every SC group PASS)
- STDOUT contains the literal `SC<N>: PASS` labels for SC1..SC6
- STDOUT contains the final `Phase 8 acceptance: ALL_PASS` marker
- _SC_MAP source code mentions SC1..SC6 exactly (no SC7 leak)
- UTF-8 subprocess encoding guards are present (Pitfall 3 cp949 defence)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_ACCEPT = _REPO / "scripts" / "validate" / "phase08_acceptance.py"


def test_acceptance_script_exists() -> None:
    """phase08_acceptance.py file must exist at the canonical path."""
    assert _ACCEPT.exists(), f"phase08_acceptance.py missing: {_ACCEPT}"


def test_acceptance_script_valid_python() -> None:
    """The aggregator must compile without syntax errors."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(_ACCEPT)],
        capture_output=True,
        text=True,
        timeout=30,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_acceptance_script_exits_zero_when_all_sc_pass() -> None:
    """All 6 SCs must PASS -> exit 0."""
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    if result.returncode != 0:
        print("=== STDOUT ===")
        print(result.stdout)
        print("=== STDERR ===")
        print(result.stderr[-2000:] if result.stderr else "")
    assert result.returncode == 0, (
        f"phase08_acceptance.py FAILED (exit {result.returncode})\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_acceptance_stdout_reports_all_six_sc_pass() -> None:
    """STDOUT must contain every `SC<N>: PASS` label for SC1..SC6."""
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    for sc in ("SC1", "SC2", "SC3", "SC4", "SC5", "SC6"):
        assert f"{sc}: PASS" in result.stdout, (
            f"{sc} not PASS in phase08_acceptance output:\n{result.stdout}"
        )


def test_acceptance_stdout_final_all_pass_marker() -> None:
    """Final `Phase 8 acceptance: ALL_PASS` marker must appear."""
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    assert "Phase 8 acceptance: ALL_PASS" in result.stdout, (
        f"ALL_PASS marker missing from output:\n{result.stdout}"
    )


def test_acceptance_has_six_sc_entries_in_map() -> None:
    """_SC_MAP must have exactly SC1..SC6 keys — no SC7 drift."""
    source = _ACCEPT.read_text(encoding="utf-8")
    for sc in ("SC1", "SC2", "SC3", "SC4", "SC5", "SC6"):
        assert f'"{sc}"' in source, f"SC entry {sc} missing from _SC_MAP"
    # Guard against SC count drift: no SC7 (Phase 8 ships exactly 6 SCs).
    assert '"SC7"' not in source, "SC7 drift detected — Phase 8 has exactly 6 SCs"


def test_acceptance_utf8_encoding_in_subprocess_call() -> None:
    """Pitfall 3 / Phase 6 STATE #28 — UTF-8 cp949 guards must be present."""
    source = _ACCEPT.read_text(encoding="utf-8")
    assert 'encoding="utf-8"' in source, (
        "encoding='utf-8' missing — Windows cp949 subprocess call will crash"
    )
    assert 'errors="replace"' in source, (
        "errors='replace' missing — decode crash on unexpected bytes"
    )


def test_acceptance_reports_six_sc_labels_even_on_failure_branch() -> None:
    """The aggregator prints SC<N>: ... line for every SC unconditionally.

    Even a hypothetical FAIL branch prints the label. Count labels by
    matching the per-SC line prefix regex.
    """
    result = subprocess.run(
        [sys.executable, str(_ACCEPT)],
        cwd=str(_REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    lines = result.stdout.splitlines()
    sc_label_lines = [ln for ln in lines if ln.startswith(("SC1:", "SC2:", "SC3:", "SC4:", "SC5:", "SC6:"))]
    assert len(sc_label_lines) == 6, (
        f"Expected exactly 6 SC label lines; got {len(sc_label_lines)}:\n{result.stdout}"
    )
