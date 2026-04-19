"""Integration tests for aggregate_patterns.py CLI (Plan 06-09 FAIL-02, D-13).

Runs the CLI as a subprocess to lock:
- Real stdin/stdout/stderr contract (UTF-8 Korean round-trip).
- D-13 dry-run invariant: no SKILL.md.candidate file is ever created.
- Argparse error codes (rc=2 on missing --input).
- Against the actual `.claude/failures/_imported_from_shorts_naberal.md` file
  which must remain byte-identical after CLI runs (D-14 side-guarantee).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
CLI = _REPO / "scripts" / "failures" / "aggregate_patterns.py"


def _run_cli(*args: str) -> tuple[int, str, str]:
    p = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        timeout=30,
        encoding="utf-8",
        errors="replace",
        cwd=str(_REPO),
    )
    return p.returncode, p.stdout, p.stderr


def test_cli_runs_against_imported_failures():
    rc, out, err = _run_cli(
        "--input", str(_REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"),
        "--threshold", "3",
    )
    assert rc == 0, f"CLI failed: {err}"
    report = json.loads(out)
    assert "candidates" in report
    assert "total_entries" in report
    assert report["total_entries"] > 0  # imported file has FAIL-N entries


def test_cli_runs_against_both_files():
    rc, out, err = _run_cli(
        "--input", str(_REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"),
        "--input", str(_REPO / ".claude" / "failures" / "FAILURES.md"),
        "--threshold", "3",
    )
    assert rc == 0, err
    report = json.loads(out)
    assert "candidates" in report
    assert report["total_entries"] > 0


def test_cli_high_threshold_empty_candidates():
    rc, out, err = _run_cli(
        "--input", str(_REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"),
        "--threshold", "9999",
    )
    assert rc == 0, err
    report = json.loads(out)
    assert report["candidates"] == []


def test_cli_low_threshold_finds_entries():
    rc, out, err = _run_cli(
        "--input", str(_REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"),
        "--threshold", "1",
    )
    assert rc == 0, err
    report = json.loads(out)
    assert len(report["candidates"]) > 0
    for c in report["candidates"]:
        assert c["count"] >= 1


def test_cli_missing_input_flag_exits_2():
    rc, out, err = _run_cli("--threshold", "3")
    assert rc == 2  # argparse missing required argument
    assert "--input" in err


def test_cli_nonexistent_input_continues_with_warning(tmp_path: Path):
    rc, out, err = _run_cli(
        "--input", str(tmp_path / "no_such_file.md"),
        "--threshold", "3",
    )
    assert rc == 0
    assert "no_such_file" in err or "WARN" in err
    report = json.loads(out)
    assert report["total_entries"] == 0


def test_d13_no_candidate_file_created(tmp_path: Path):
    """D-13: aggregate_patterns in Phase 6 NEVER writes SKILL.md.candidate.

    Even running CLI with threshold=1 (all entries become candidates) must not
    produce a SKILL.md.candidate file anywhere.
    """
    imported_src = _REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"
    local = tmp_path / "imported.md"
    local.write_text(imported_src.read_text(encoding="utf-8"), encoding="utf-8")
    rc, out, err = _run_cli("--input", str(local), "--threshold", "1")
    assert rc == 0, err
    # No candidate file anywhere in tmp_path or near CLI source
    for root in (tmp_path, CLI.parent, _REPO):
        hits = list(root.rglob("SKILL.md.candidate"))
        assert hits == [], f"D-13 VIOLATED at {root}: {hits}"


def test_d14_imported_file_byte_identical_after_run():
    """Running the CLI against _imported_from_shorts_naberal.md must not modify it."""
    imported = _REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"
    before = hashlib.sha256(imported.read_bytes()).hexdigest()
    rc, _, err = _run_cli("--input", str(imported), "--threshold", "1")
    assert rc == 0, err
    after = hashlib.sha256(imported.read_bytes()).hexdigest()
    assert before == after, "D-14 VIOLATED: imported file mutated by CLI"


def test_cli_output_korean_preserved(tmp_path: Path):
    """ensure_ascii=False keeps Korean summary in stdout."""
    seed = tmp_path / "seed.md"
    seed.write_text(
        "### FAIL-999: 한국어 실패 사례 요약\n"
        "- **Trigger**: 한국어 트리거\n",
        encoding="utf-8",
    )
    rc, out, err = _run_cli("--input", str(seed), "--threshold", "1")
    assert rc == 0, err
    assert "한국어" in out
    # JSON is still valid UTF-8
    report = json.loads(out)
    assert report["candidates"][0]["examples"][0]["summary"] == "한국어 실패 사례 요약"


def test_cli_output_file_is_valid_json(tmp_path: Path):
    out_path = tmp_path / "report.json"
    rc, _, err = _run_cli(
        "--input", str(_REPO / ".claude" / "failures" / "_imported_from_shorts_naberal.md"),
        "--threshold", "1",
        "--output", str(out_path),
    )
    assert rc == 0, err
    assert out_path.exists()
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert "candidates" in report
    assert "total_entries" in report
