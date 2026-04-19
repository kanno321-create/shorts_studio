"""Unit tests for scripts/failures/aggregate_patterns.py (Plan 06-09 FAIL-02).

Covers:
- ENTRY_RE / TRIGGER_RE regex correctness against both FAILURES.md and
  _imported_from_shorts_naberal.md schemas.
- iter_entries: missing file warning, trigger-less entries, fixture parsing.
- normalize_pattern_key: deterministic, case-insensitive, punctuation-stripped,
  Korean-preserving, trigger[:80] truncated.
- aggregate: threshold filtering, empty input handling, example truncation to 3.
- main CLI: default threshold 3, --output file, stdout JSON shape.

D-13 invariant (no SKILL.md.candidate writes) is additionally verified by the
subprocess companion test_aggregate_dry_run.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.failures.aggregate_patterns import (
    ENTRY_RE,
    TRIGGER_RE,
    aggregate,
    iter_entries,
    main,
    normalize_pattern_key,
)


def test_entry_re_matches_schema():
    text = "### FAIL-001: some summary\n- **Tier**: B"
    m = ENTRY_RE.search(text)
    assert m is not None
    assert m.group(1) == "FAIL-001"
    assert m.group(2) == "some summary"


def test_entry_re_matches_multi_digit_id():
    text = "### FAIL-0042: summary here\n"
    m = ENTRY_RE.search(text)
    assert m is not None
    assert m.group(1) == "FAIL-0042"


def test_trigger_re_matches_schema():
    text = "- **Trigger**: some condition"
    m = TRIGGER_RE.search(text)
    assert m is not None
    assert m.group(1) == "some condition"


def test_iter_entries_on_fixture(fixtures_dir: Path):
    p = fixtures_dir / "failures_sample.md"
    entries = list(iter_entries(p))
    assert len(entries) == 2
    assert entries[0]["id"] == "FAIL-001"
    assert "sample" in entries[0]["summary"]
    assert entries[0]["trigger"] == "sample trigger condition"
    assert entries[0]["source"] == "failures_sample.md"
    assert entries[1]["id"] == "FAIL-002"
    assert entries[1]["trigger"] == "different trigger"


def test_iter_entries_missing_file_warns(tmp_path: Path, capsys):
    list(iter_entries(tmp_path / "does_not_exist.md"))
    captured = capsys.readouterr()
    assert "does_not_exist" in captured.err or "WARN" in captured.err


def test_iter_entries_without_trigger(tmp_path: Path):
    p = tmp_path / "no_trigger.md"
    p.write_text("### FAIL-042: summary only\n- **Tier**: A\n", encoding="utf-8")
    entries = list(iter_entries(p))
    assert len(entries) == 1
    assert entries[0]["trigger"] == ""
    assert entries[0]["summary"] == "summary only"


def test_iter_entries_parses_imported_schema(repo_root: Path):
    """The _imported_from_shorts_naberal.md uses slightly different wording
    but the regex anchors on `### FAIL-` + `- **Trigger**:` which are shared.
    """
    imported = repo_root / ".claude" / "failures" / "_imported_from_shorts_naberal.md"
    entries = list(iter_entries(imported))
    # Phase 3 imported file has >= 10 FAIL-N entries
    assert len(entries) >= 10
    for e in entries:
        assert e["id"].startswith("FAIL-")
        assert e["source"] == "_imported_from_shorts_naberal.md"


def test_normalize_pattern_key_deterministic():
    entry = {"summary": "Same summary text", "trigger": "Same trigger"}
    k1 = normalize_pattern_key(entry)
    k2 = normalize_pattern_key(entry)
    assert k1 == k2
    assert len(k1) == 12
    assert all(c in "0123456789abcdef" for c in k1)


def test_normalize_pattern_key_case_insensitive():
    e1 = {"summary": "Summary", "trigger": "Trigger"}
    e2 = {"summary": "SUMMARY", "trigger": "TRIGGER"}
    assert normalize_pattern_key(e1) == normalize_pattern_key(e2)


def test_normalize_pattern_key_strips_punctuation():
    e1 = {"summary": "Hello, world!", "trigger": "trigger..."}
    e2 = {"summary": "hello world", "trigger": "trigger"}
    assert normalize_pattern_key(e1) == normalize_pattern_key(e2)


def test_normalize_pattern_key_collapses_whitespace():
    e1 = {"summary": "a   b   c", "trigger": "x\ty\tz"}
    e2 = {"summary": "a b c", "trigger": "x y z"}
    assert normalize_pattern_key(e1) == normalize_pattern_key(e2)


def test_normalize_pattern_key_preserves_korean():
    e1 = {"summary": "한국어 섬머리", "trigger": "트리거"}
    e2 = {"summary": "한국어 섬머리", "trigger": "트리거"}
    assert normalize_pattern_key(e1) == normalize_pattern_key(e2)
    e3 = {"summary": "다른 섬머리", "trigger": "트리거"}
    assert normalize_pattern_key(e1) != normalize_pattern_key(e3)


def test_normalize_pattern_key_trigger_truncation():
    # trigger[:80] means contents beyond char 80 do not affect key
    long_trigger_a = "x" * 80 + "AAA"
    long_trigger_b = "x" * 80 + "BBB"
    e1 = {"summary": "s", "trigger": long_trigger_a}
    e2 = {"summary": "s", "trigger": long_trigger_b}
    assert normalize_pattern_key(e1) == normalize_pattern_key(e2)


def test_aggregate_threshold_one_yields_all(fixtures_dir: Path):
    report = aggregate([fixtures_dir / "failures_sample.md"], threshold=1)
    assert report["total_entries"] == 2
    assert len(report["candidates"]) == 2
    for c in report["candidates"]:
        assert c["count"] >= 1
        assert c["key"]
        assert len(c["examples"]) <= 3


def test_aggregate_threshold_three_excludes_singletons(fixtures_dir: Path):
    report = aggregate([fixtures_dir / "failures_sample.md"], threshold=3)
    assert report["total_entries"] == 2
    assert report["candidates"] == []


def test_aggregate_empty_input_returns_zero():
    report = aggregate([], threshold=3)
    assert report == {"candidates": [], "total_entries": 0}


def test_aggregate_counts_duplicates(tmp_path: Path):
    p = tmp_path / "dups.md"
    p.write_text(
        "### FAIL-001: identical summary\n- **Trigger**: identical trigger\n\n"
        "### FAIL-002: identical summary\n- **Trigger**: identical trigger\n\n"
        "### FAIL-003: identical summary\n- **Trigger**: identical trigger\n\n"
        "### FAIL-004: different summary\n- **Trigger**: other trigger\n",
        encoding="utf-8",
    )
    report = aggregate([p], threshold=3)
    assert report["total_entries"] == 4
    # Only the identical-summary pattern reaches threshold
    assert len(report["candidates"]) == 1
    assert report["candidates"][0]["count"] == 3
    # examples capped at 3
    assert len(report["candidates"][0]["examples"]) == 3


def test_aggregate_examples_capped_at_three(tmp_path: Path):
    p = tmp_path / "many.md"
    lines = []
    for i in range(6):
        lines.append(f"### FAIL-{i:03d}: same\n- **Trigger**: same\n\n")
    p.write_text("".join(lines), encoding="utf-8")
    report = aggregate([p], threshold=1)
    assert report["total_entries"] == 6
    assert len(report["candidates"]) == 1
    assert report["candidates"][0]["count"] == 6
    assert len(report["candidates"][0]["examples"]) == 3


def test_main_cli_default_threshold_three(fixtures_dir: Path, capsys):
    exit_code = main([
        "--input", str(fixtures_dir / "failures_sample.md"),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert "candidates" in report
    assert "total_entries" in report
    # 2 unique entries, threshold 3 default => 0 candidates
    assert report["total_entries"] == 2
    assert report["candidates"] == []


def test_main_cli_output_file(tmp_path: Path, fixtures_dir: Path):
    out_path = tmp_path / "agg.json"
    exit_code = main([
        "--input", str(fixtures_dir / "failures_sample.md"),
        "--output", str(out_path),
    ])
    assert exit_code == 0
    assert out_path.exists()
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["total_entries"] == 2


def test_main_cli_threshold_override(fixtures_dir: Path, capsys):
    exit_code = main([
        "--input", str(fixtures_dir / "failures_sample.md"),
        "--threshold", "1",
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert len(report["candidates"]) == 2
