"""Phase 10 Plan 02 — AUDIT-04 phase_lock helpers + gh issue subprocess tests.

set_phase_lock / clear_phase_lock 의 idempotent 동작 검증과 create_github_issue 의
subprocess argv 계약을 보장합니다. End-to-end 로는 main() 이 A급 drift 발견 시
STATE.md frontmatter 에 phase_lock: true 를 삽입하고 gh subprocess 를 호출하는지 확인.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# tests/phase10/test_phase_lock.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # pragma: no cover - defensive
        pass


KST = ZoneInfo("Asia/Seoul")


@pytest.fixture
def drift_scan_mod():
    import importlib
    mod = importlib.import_module("scripts.audit.drift_scan")
    importlib.reload(mod)
    return mod


def _build_state_md(tmp_path: Path, phase_lock_line: str = "phase_lock: false") -> Path:
    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    state_md = studio / ".planning" / "STATE.md"
    state_md.write_text(
        "---\n"
        "gsd_state_version: 1.0\n"
        "milestone: v1.0.1\n"
        'last_updated: "2026-04-20T12:00:00.000Z"\n'
        f"{phase_lock_line}\n"
        "progress:\n"
        "  total_phases: 11\n"
        "  completed_phases: 9\n"
        "---\n\n"
        "# STATE — test\n"
        "body content here.\n",
        encoding="utf-8",
    )
    return studio


# ---------------------------------------------------------------------------
# set/clear_phase_lock idempotency
# ---------------------------------------------------------------------------


def test_set_phase_lock_inserts_three_fields(drift_scan_mod, tmp_path):
    """set_phase_lock() 호출 시 phase_lock/block_reason/block_since 3 필드 삽입."""
    mod = drift_scan_mod
    studio = _build_state_md(tmp_path)
    now = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)

    mod.set_phase_lock(studio, "A급 drift 2건 — 2026-04-27 drift_scan", now)

    text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "frontmatter missing after set_phase_lock"
    fm = m.group(1)
    assert re.search(r"^phase_lock:\s*true", fm, re.MULTILINE), fm
    assert re.search(r"^block_reason:", fm, re.MULTILINE), fm
    assert re.search(r"^block_since:", fm, re.MULTILINE), fm
    # block_since contains ISO timestamp
    assert "2026-04-27T09:00:00" in fm


def test_set_phase_lock_replaces_existing_value_no_duplication(drift_scan_mod, tmp_path):
    """phase_lock: false → set_phase_lock() → phase_lock: true 1 occurrence only."""
    mod = drift_scan_mod
    studio = _build_state_md(tmp_path, phase_lock_line="phase_lock: false")
    now = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)

    mod.set_phase_lock(studio, "test reason", now)

    text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = m.group(1)
    phase_lock_lines = [l for l in fm.split("\n") if re.match(r"^phase_lock\s*:", l)]
    assert len(phase_lock_lines) == 1, f"duplicated phase_lock lines: {phase_lock_lines}"
    assert phase_lock_lines[0].strip() == "phase_lock: true"


def test_set_phase_lock_idempotent_double_call(drift_scan_mod, tmp_path):
    """set_phase_lock 두 번 호출 시 중복 없이 재수정."""
    mod = drift_scan_mod
    studio = _build_state_md(tmp_path)
    now1 = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)
    now2 = datetime(2026, 4, 28, 9, 0, 0, tzinfo=KST)

    mod.set_phase_lock(studio, "reason 1", now1)
    mod.set_phase_lock(studio, "reason 2", now2)

    text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = m.group(1)
    pl_lines = [l for l in fm.split("\n") if re.match(r"^phase_lock\s*:", l)]
    br_lines = [l for l in fm.split("\n") if re.match(r"^block_reason\s*:", l)]
    bs_lines = [l for l in fm.split("\n") if re.match(r"^block_since\s*:", l)]
    assert len(pl_lines) == 1
    assert len(br_lines) == 1
    assert len(bs_lines) == 1
    assert "reason 2" in br_lines[0]
    assert "2026-04-28T09:00:00" in bs_lines[0]


def test_clear_phase_lock_removes_block_fields(drift_scan_mod, tmp_path):
    """set 후 clear → phase_lock: false + block_reason/block_since 라인 제거."""
    mod = drift_scan_mod
    studio = _build_state_md(tmp_path)
    now = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)

    mod.set_phase_lock(studio, "some reason", now)
    mod.clear_phase_lock(studio)

    text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = m.group(1)
    assert re.search(r"^phase_lock:\s*false", fm, re.MULTILINE)
    assert not re.search(r"^block_reason\s*:", fm, re.MULTILINE)
    assert not re.search(r"^block_since\s*:", fm, re.MULTILINE)


# ---------------------------------------------------------------------------
# create_github_issue subprocess contract
# ---------------------------------------------------------------------------


def test_create_github_issue_subprocess_argv(drift_scan_mod, monkeypatch):
    """gh subprocess 가 정확한 argv 로 호출되는지 (title/body-file/label)."""
    mod = drift_scan_mod
    captured: list[dict] = []

    def _fake_run(cmd, **kwargs):
        captured.append({"cmd": cmd, "kwargs": kwargs})
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    now = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)
    mod.create_github_issue(
        {"skip_gates_usage": 2, "t2v_code_path": 1},
        "A급 drift 3건 — 2026-04-27",
        now,
    )

    assert len(captured) == 1
    cmd = captured[0]["cmd"]
    assert cmd[0] == "gh"
    assert cmd[1] == "issue"
    assert cmd[2] == "create"
    assert "--title" in cmd
    assert "--body-file" in cmd
    assert cmd[cmd.index("--body-file") + 1] == "-"
    assert "--label" in cmd
    label_val = cmd[cmd.index("--label") + 1]
    assert label_val == "drift,critical,phase-10,auto"
    # title contains count
    title = cmd[cmd.index("--title") + 1]
    assert "3건" in title
    assert "AUDIT-04" in title
    # body passed via stdin input
    assert "input" in captured[0]["kwargs"]


def test_create_github_issue_body_includes_pattern_counts(drift_scan_mod, monkeypatch):
    """body stdin 에 A급 pattern 이름 + 개수 포함."""
    mod = drift_scan_mod
    captured: list[dict] = []

    def _fake_run(cmd, **kwargs):
        captured.append({"cmd": cmd, "kwargs": kwargs})
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    now = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)
    mod.create_github_issue(
        {"skip_gates_usage": 5, "selenium_import": 2},
        "A급 drift 7건",
        now,
    )

    body = captured[0]["kwargs"]["input"]
    assert "skip_gates_usage" in body
    assert "5건" in body
    assert "selenium_import" in body
    assert "2건" in body
    assert "Phase lock" in body or "phase_lock" in body
    assert "복구 경로" in body or "Recovery" in body


# ---------------------------------------------------------------------------
# End-to-end main() A-grade trigger
# ---------------------------------------------------------------------------


def test_main_exit_1_triggers_phase_lock_and_gh_issue(drift_scan_mod, tmp_path, monkeypatch):
    """main() A급 발견 → exit 1 + STATE.md phase_lock true + gh subprocess called."""
    mod = drift_scan_mod
    studio = _build_state_md(tmp_path)

    pats = [
        {"regex": "skip_gates\\s*=", "reason": "A", "grade": "A", "name": "skip_gates_usage"},
    ]
    fake_funcs = {
        "load_patterns": lambda root: pats,
        "scan_studio": lambda root, p: {
            "skip_gates_usage": [
                {"file": "orchestrator.py", "line": 42, "match": "skip_gates=True"},
            ],
        },
        "write_conflict_map": lambda root, f, p, out: None,
        "append_history": lambda root, f: None,
    }
    monkeypatch.setattr(mod, "_resolve_harness_imports", lambda hp, skip: fake_funcs)

    gh_calls: list[list[str]] = []

    def _fake_run(cmd, **kwargs):
        gh_calls.append(list(cmd))
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    rc = mod.main(["--studio-root", str(studio)])
    assert rc == 1

    text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m
    fm = m.group(1)
    assert re.search(r"^phase_lock:\s*true", fm, re.MULTILINE), fm
    assert len(gh_calls) == 1
    assert gh_calls[0][:3] == ["gh", "issue", "create"]


def test_main_clear_lock_subcommand(drift_scan_mod, tmp_path):
    """--clear-lock → phase_lock: false + JSON stdout."""
    mod = drift_scan_mod
    studio = _build_state_md(tmp_path)
    now = datetime(2026, 4, 27, 9, 0, 0, tzinfo=KST)
    mod.set_phase_lock(studio, "test", now)

    rc = mod.main(["--studio-root", str(studio), "--clear-lock"])
    assert rc == 0

    text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = m.group(1)
    assert re.search(r"^phase_lock:\s*false", fm, re.MULTILINE)
    assert not re.search(r"^block_reason\s*:", fm, re.MULTILINE)
