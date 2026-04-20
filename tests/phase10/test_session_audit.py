"""Phase 10 Plan 5 — session_audit_rollup tests (AUDIT-01 / SC#3).

11 tests covering:
    1. logs/.gitkeep exists + logs/*.jsonl gitignored (.gitignore rule)
    2. subprocess call to scripts.validate.harness_audit (mock returncode + json file)
    3. Append single record to jsonl on default invocation
    4. Empty jsonl rolling avg = 100.0 (신규 스튜디오) + exit 0
    5. rolling avg < 80 triggers FAILURES.md append + exit 1
    6. rolling avg at exactly 80 (boundary) passes + exit 0
    7. Records older than 30 days excluded from rolling window
    8. --dry-run does not mutate jsonl (no new record)
    9. --threshold override (e.g. 70) customises pass/fail decision
    10. cp949-safe Korean reason body in FAILURES.md append (UTF-8 reconfigure)
    11. harness_audit subprocess returncode != 0 → explicit raise (no silent fallback)

Runtime contract (session_audit_rollup module):
    - `run_harness_audit(studio_root: Path) -> dict`
    - `append_session_record(jsonl: Path, audit_json: dict, now: datetime) -> dict`
    - `rolling_avg(jsonl: Path, days: int, now: datetime | None) -> tuple[float, int]`
    - `append_failures(failures: Path, avg: float, sample_count: int, threshold: int, now: datetime) -> str`
    - `main(argv: list[str] | None) -> int` with `--dry-run`, `--skip-audit`, `--threshold`,
      `--jsonl PATH`, `--failures PATH`, `--window-days N`.

Design:
    - No reliance on conftest.freeze_kst_now (tests pass explicit `now=` where timing matters).
    - `subprocess.run` monkeypatched via `side_effect` that writes a fake audit JSON to the
      `--json-out` tmp path before returning a MockCompletedProcess (returncode=0).
    - FAILURES.md seeded inside tmp_path per test to avoid polluting real repo.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

_KST = ZoneInfo("Asia/Seoul")
_FIXED_NOW = datetime(2026, 5, 1, 9, 0, 0, tzinfo=_KST)


# ---------------------------------------------------------------------------
# Subprocess fake — writes a fake audit JSON at the --json-out path.
# ---------------------------------------------------------------------------


def _make_fake_subprocess(score: int = 90, *, returncode: int = 0):
    """Return a side_effect callable that mocks scripts.validate.harness_audit.

    When the fake subprocess is invoked, it looks for `--json-out` in the cmd
    and writes a minimal audit JSON (with the given score) to that path, then
    returns a MockCompletedProcess with the specified returncode.
    """
    def _side_effect(cmd, *args, **kwargs):
        # Locate --json-out PATH in the cmd list
        out_path: Path | None = None
        for i, tok in enumerate(cmd):
            if tok == "--json-out" and i + 1 < len(cmd):
                out_path = Path(cmd[i + 1])
                break
        if out_path is not None:
            payload = {
                "score": score,
                "a_rank_drift_count": 0,
                "phase": 7,
                "timestamp": "2026-05-01T00:00:00Z",
            }
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )

        class _Result:
            pass

        r = _Result()
        # Populate required attributes accessed by production code
        r.returncode = returncode
        r.stdout = f"HARNESS_AUDIT_SCORE: {score}\n"
        r.stderr = ""
        return r

    return _side_effect


def _seed_failures_md(path: Path) -> None:
    path.write_text(
        "# FAILURES.md — test seed\n\n"
        "> append-only (test fixture)\n\n"
        "---\n\n"
        "## F-CTX-01 — seed entry (2026-04-20)\n\n"
        "test fixture placeholder — strict prefix preserved.\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Test 1: logs/.gitkeep exists + logs/*.jsonl gitignored
# ---------------------------------------------------------------------------


def test_logs_gitkeep_exists_logs_jsonl_ignored(repo_root: Path) -> None:
    """logs/.gitkeep must exist (Plan 5 placeholder); .gitignore must ignore logs/*.jsonl."""
    gk = repo_root / "logs" / ".gitkeep"
    assert gk.exists(), f"{gk} must exist as Plan 5 logs/ placeholder"
    gi = (repo_root / ".gitignore").read_text(encoding="utf-8")
    # Accept either `logs/*.jsonl` or a broader `logs/` pattern with gitkeep exception
    assert (
        "logs/*.jsonl" in gi
        or "logs/session_audit" in gi
        or ("logs/*" in gi and "!logs/.gitkeep" in gi)
    ), ".gitignore must register logs/*.jsonl or equivalent"


# ---------------------------------------------------------------------------
# Test 2: subprocess call to scripts.validate.harness_audit
# ---------------------------------------------------------------------------


def test_subprocess_call_to_harness_audit(tmp_path: Path, monkeypatch) -> None:
    """run_harness_audit must invoke scripts.validate.harness_audit via subprocess."""
    from scripts.audit import session_audit_rollup as sar

    captured: list[list[str]] = []

    def _spy(cmd, *args, **kwargs):
        captured.append(list(cmd))
        return _make_fake_subprocess(score=88)(cmd, *args, **kwargs)

    monkeypatch.setattr(sar.subprocess, "run", _spy)

    result = sar.run_harness_audit(tmp_path)

    assert captured, "subprocess.run must be invoked"
    flat = " ".join(captured[0])
    assert "scripts.validate.harness_audit" in flat, (
        f"expected 'scripts.validate.harness_audit' in cmd, got: {flat}"
    )
    assert "--json-out" in captured[0]
    assert isinstance(result, dict)
    assert result.get("score") == 88


# ---------------------------------------------------------------------------
# Test 3: Append a record to jsonl on default invocation
# ---------------------------------------------------------------------------


def test_append_to_jsonl(tmp_path: Path) -> None:
    """append_session_record writes exactly one JSON line with required fields."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    audit_json = {"score": 85}
    record = sar.append_session_record(jsonl, audit_json, _FIXED_NOW)

    assert jsonl.exists(), "jsonl file must be created"
    lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1, f"expected 1 line, got {len(lines)}"
    parsed = json.loads(lines[0])
    assert parsed["score"] == 85
    assert "timestamp" in parsed
    assert "violations_count" in parsed
    assert "warnings_count" in parsed
    assert record["score"] == 85


# ---------------------------------------------------------------------------
# Test 4: Empty jsonl → rolling avg 100.0, exit 0
# ---------------------------------------------------------------------------


def test_rolling_avg_empty_returns_100(tmp_path: Path) -> None:
    """Empty (non-existent or empty) jsonl must return (100.0, 0)."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    # Not created yet
    avg, count = sar.rolling_avg(jsonl, days=30, now=_FIXED_NOW)
    assert avg == 100.0
    assert count == 0

    # Empty file
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text("", encoding="utf-8")
    avg2, count2 = sar.rolling_avg(jsonl, days=30, now=_FIXED_NOW)
    assert avg2 == 100.0
    assert count2 == 0


# ---------------------------------------------------------------------------
# Test 5: rolling avg < 80 → FAILURES.md append + exit 1
# ---------------------------------------------------------------------------


def test_rolling_avg_below_80_triggers_failures_append(tmp_path: Path, monkeypatch) -> None:
    """Three records [70, 75, 70] → avg ≈ 71.67 → F-AUDIT-XX appended + exit 1."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    # Three recent records (within 30 days)
    for i, s in enumerate([70, 75, 70]):
        ts = (_FIXED_NOW - timedelta(days=i + 1)).isoformat()
        line = json.dumps({
            "timestamp": ts,
            "score": s,
            "violations_count": 0,
            "warnings_count": 0,
        }, ensure_ascii=False)
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    failures = tmp_path / "FAILURES.md"
    _seed_failures_md(failures)
    pre_bytes = failures.read_bytes()

    # Run with --skip-audit (no subprocess) so the test only exercises rolling logic
    exit_code = sar.main([
        "--jsonl", str(jsonl),
        "--failures", str(failures),
        "--skip-audit",
    ])

    assert exit_code == 1, "exit 1 expected on rolling avg < threshold"
    post_bytes = failures.read_bytes()
    # Strict-prefix preservation (append-only invariant)
    assert post_bytes[: len(pre_bytes)] == pre_bytes, "FAILURES.md prefix must be preserved"
    appended = post_bytes[len(pre_bytes):].decode("utf-8")
    assert "F-AUDIT" in appended, "F-AUDIT-NN entry must be appended"
    assert "71" in appended, "computed avg ≈ 71.67 must appear in appended body"


# ---------------------------------------------------------------------------
# Test 6: rolling avg at exactly 80 → exit 0 (boundary)
# ---------------------------------------------------------------------------


def test_rolling_avg_at_80_passes(tmp_path: Path) -> None:
    """Three records [80, 80, 80] → avg 80.0 → exit 0 (≥ threshold)."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    for i in range(3):
        ts = (_FIXED_NOW - timedelta(days=i + 1)).isoformat()
        line = json.dumps({
            "timestamp": ts,
            "score": 80,
            "violations_count": 0,
            "warnings_count": 0,
        }, ensure_ascii=False)
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    failures = tmp_path / "FAILURES.md"
    _seed_failures_md(failures)
    pre_bytes = failures.read_bytes()

    exit_code = sar.main([
        "--jsonl", str(jsonl),
        "--failures", str(failures),
        "--skip-audit",
    ])

    assert exit_code == 0, "avg == threshold must pass (≥, not >)"
    assert failures.read_bytes() == pre_bytes, "FAILURES.md must not mutate when passing"


# ---------------------------------------------------------------------------
# Test 7: Records older than 30 days excluded
# ---------------------------------------------------------------------------


def test_records_older_than_30_days_excluded(tmp_path: Path) -> None:
    """60-day-old record (score 50) must not pull the rolling avg below 90."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)

    # 60 days old — should be excluded
    old_ts = (_FIXED_NOW - timedelta(days=60)).isoformat()
    # 1 day old — should be included
    new_ts = (_FIXED_NOW - timedelta(days=1)).isoformat()

    for ts, s in [(old_ts, 50), (new_ts, 90)]:
        line = json.dumps({
            "timestamp": ts, "score": s,
            "violations_count": 0, "warnings_count": 0,
        }, ensure_ascii=False)
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    avg, count = sar.rolling_avg(jsonl, days=30, now=_FIXED_NOW)
    assert count == 1, f"only the recent record should be counted, got {count}"
    assert avg == 90.0, f"avg over recent window only = 90, got {avg}"


# ---------------------------------------------------------------------------
# Test 8: --dry-run does not mutate jsonl
# ---------------------------------------------------------------------------


def test_cli_dry_run_no_jsonl_mutation(tmp_path: Path, monkeypatch) -> None:
    """--dry-run must NOT append a record to jsonl."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text("", encoding="utf-8")
    pre_bytes = jsonl.read_bytes()

    failures = tmp_path / "FAILURES.md"
    _seed_failures_md(failures)

    monkeypatch.setattr(sar.subprocess, "run", _make_fake_subprocess(score=95))

    exit_code = sar.main([
        "--jsonl", str(jsonl),
        "--failures", str(failures),
        "--dry-run",
    ])

    assert exit_code == 0
    assert jsonl.read_bytes() == pre_bytes, "--dry-run must leave jsonl untouched"


# ---------------------------------------------------------------------------
# Test 9: --threshold override
# ---------------------------------------------------------------------------


def test_cli_score_threshold_override(tmp_path: Path) -> None:
    """--threshold 70 accepts avg 75, whereas default 80 would fail."""
    from scripts.audit import session_audit_rollup as sar

    jsonl = tmp_path / "logs" / "session_audit.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate([70, 75, 80]):  # avg = 75
        ts = (_FIXED_NOW - timedelta(days=i + 1)).isoformat()
        line = json.dumps({
            "timestamp": ts, "score": s,
            "violations_count": 0, "warnings_count": 0,
        }, ensure_ascii=False)
        with jsonl.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    failures = tmp_path / "FAILURES.md"
    _seed_failures_md(failures)

    exit_code = sar.main([
        "--jsonl", str(jsonl),
        "--failures", str(failures),
        "--threshold", "70",
        "--skip-audit",
    ])
    assert exit_code == 0, "avg 75 ≥ threshold 70 must pass"


# ---------------------------------------------------------------------------
# Test 10: cp949-safe Korean reason body (UTF-8 reconfigure)
# ---------------------------------------------------------------------------


def test_cp949_safe_korean_reason(tmp_path: Path) -> None:
    """append_failures body must contain Korean characters without UnicodeError."""
    from scripts.audit import session_audit_rollup as sar

    failures = tmp_path / "FAILURES.md"
    _seed_failures_md(failures)

    entry_id = sar.append_failures(failures, avg=71.5, sample_count=3,
                                   threshold=80, now=_FIXED_NOW)

    body = failures.read_text(encoding="utf-8")
    assert entry_id.startswith("F-AUDIT-")
    # Korean must round-trip
    assert "미달" in body or "임계" in body, "Korean diagnostic text must survive round-trip"
    assert entry_id in body


# ---------------------------------------------------------------------------
# Test 11: subprocess returncode != 0 → explicit raise
# ---------------------------------------------------------------------------


def test_harness_audit_subprocess_failure_explicit_raise(
    tmp_path: Path, monkeypatch
) -> None:
    """Project rule: no silent fallback — non-zero returncode must raise."""
    from scripts.audit import session_audit_rollup as sar

    # threshold=0 in run_harness_audit means exit should be 0 regardless of score,
    # but we force returncode=2 to simulate a real subprocess failure.
    monkeypatch.setattr(
        sar.subprocess, "run",
        _make_fake_subprocess(score=80, returncode=2),
    )

    with pytest.raises(RuntimeError, match=r"harness_audit subprocess failed"):
        sar.run_harness_audit(tmp_path)
