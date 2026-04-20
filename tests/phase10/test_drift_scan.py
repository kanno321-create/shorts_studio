"""Phase 10 Plan 02 — drift_scan.py + deprecated_patterns.json grade wrapper tests.

Wave 0 smokes (W0-a~W0-d): deprecated_patterns.json 8 entries 의 grade/name
필드 확장, STATE.md phase_lock default, Phase 5/6 regression 무결성을 검증합니다.

본 테스트들은 AUDIT-03/04 requirement 의 구조적 증명을 담당합니다:
  - AUDIT-03: harness drift_scan.py 4 public 함수를 sys.path import 로 재사용
  - AUDIT-04: A급 drift 감지 시 STATE.md frontmatter phase_lock=true + gh issue
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

# tests/phase10/test_drift_scan.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# UTF-8 safeguard for Windows cp949 per Phase 6/9 precedent
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # pragma: no cover - defensive
        pass


# ---------------------------------------------------------------------------
# Wave 0 smokes (Task 1) — pattern/state baseline
# ---------------------------------------------------------------------------


def test_deprecated_patterns_has_grade_and_name():
    """W0-a: 8 entries 모두 grade ∈ {A,B,C} + name (non-empty str) 보유."""
    data = json.loads((_REPO_ROOT / ".claude" / "deprecated_patterns.json").read_text(encoding="utf-8"))
    for entry in data["patterns"]:
        assert entry.get("grade") in {"A", "B", "C"}, entry
        assert isinstance(entry.get("name"), str) and entry["name"], entry


def test_deprecated_patterns_a_grade_exact_four():
    """W0-b: A 등급 entry == 정확히 4 (skip_gates / todo_next / t2v / selenium)."""
    data = json.loads((_REPO_ROOT / ".claude" / "deprecated_patterns.json").read_text(encoding="utf-8"))
    a_names = {e["name"] for e in data["patterns"] if e.get("grade") == "A"}
    assert a_names == {
        "skip_gates_usage",
        "todo_next_session",
        "t2v_code_path",
        "selenium_import",
    }, a_names


def test_deprecated_patterns_regex_and_reason_byte_identical():
    """Phase 5/6 regex 매칭 regression 방지 — 기존 regex + reason 문자열은 byte-identical.

    Plan 02 에서는 grade/name 필드만 추가하며 기존 필드는 수정 금지.
    """
    data = json.loads((_REPO_ROOT / ".claude" / "deprecated_patterns.json").read_text(encoding="utf-8"))
    expected_regexes = [
        "skip_gates\\s*=",
        "TODO\\s*\\(\\s*next-session",
        "(?i)(text_to_video|text2video|(?<![a-z])t2v(?![a-z]))",
        "segments\\s*\\[\\s*\\]",
        "\\bimport\\s+selenium\\b|\\bfrom\\s+selenium\\s+import",
        "try\\s*:[^\\n]*\\n\\s+pass\\s*$",
        "(?i)\\[REMOVED\\]|\\[DELETED\\]|delete this entry",
        "SKILL\\.md",
    ]
    actual = [e["regex"] for e in data["patterns"]]
    assert actual == expected_regexes, actual
    # reason 도 byte-identical 유지
    for e in data["patterns"]:
        assert e.get("reason", "").strip(), e


def test_state_md_frontmatter_phase_lock_false_default():
    """W0-c: STATE.md frontmatter 에 phase_lock: false default 필드 존재."""
    text = (_REPO_ROOT / ".planning" / "STATE.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "STATE.md frontmatter missing"
    fm = m.group(1)
    assert "phase_lock: false" in fm, fm


def test_phase5_6_regression_preserved():
    """W0-d: Phase 5 + Phase 6 회귀 테스트 subprocess GREEN (Plan 02 작업 후 무결성).

    Phase 5 regression 은 Plan 08 의 deprecated_patterns 6->8 expansion 으로 pre-existing
    2 failures 가 있음. 그러나 이것은 Plan 02 범위 밖. Plan 02 는 tests/phase05/test_deprecated_patterns_json.py
    (Phase 5 test baseline) 이 여전히 통과하는지만 확인한다 (grade/name 필드 추가가
    기존 Phase 5 test 를 깨지 않는지 verify).
    """
    target = _REPO_ROOT / "tests" / "phase05" / "test_deprecated_patterns_json.py"
    assert target.exists(), target
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(target),
         "-q", "--tb=short", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=str(_REPO_ROOT),
        encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, (
        "Phase 5 deprecated_patterns regression:\n"
        f"STDOUT:\n{(result.stdout or '')[-2000:]}\n"
        f"STDERR:\n{(result.stderr or '')[-500:]}"
    )


# ---------------------------------------------------------------------------
# Task 2 — drift_scan.py wrapper main scenarios
# ---------------------------------------------------------------------------


@pytest.fixture
def _drift_scan_module():
    """Import scripts.audit.drift_scan as a module (without executing main)."""
    import importlib
    mod = importlib.import_module("scripts.audit.drift_scan")
    # Reload to reset _HARNESS_LOADED module state between tests
    importlib.reload(mod)
    return mod


def test_drift_scan_imports_and_exports_public_api(_drift_scan_module):
    """Test 3: main + set_phase_lock + clear_phase_lock + create_github_issue 공개."""
    mod = _drift_scan_module
    assert hasattr(mod, "main"), "main() entry point missing"
    assert hasattr(mod, "set_phase_lock"), "set_phase_lock helper missing"
    assert hasattr(mod, "clear_phase_lock"), "clear_phase_lock helper missing"
    assert hasattr(mod, "create_github_issue"), "create_github_issue helper missing"
    assert hasattr(mod, "_resolve_harness_imports"), "lazy harness resolver missing"


def test_main_exit_0_when_no_a_grade(_drift_scan_module, tmp_path, monkeypatch):
    """Test 4: scan_studio 빈 dict → exit 0, STATE.md phase_lock 변동 없음."""
    mod = _drift_scan_module

    # Build a tmp studio with .planning/STATE.md + .claude/deprecated_patterns.json
    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    (studio / ".planning" / "STATE.md").write_text(
        "---\n"
        "gsd_state_version: 1.0\n"
        "status: executing\n"
        "phase_lock: false\n"
        "progress:\n"
        "  total_phases: 11\n"
        "---\n\n"
        "# STATE — test\n",
        encoding="utf-8",
    )
    (studio / ".claude" / "deprecated_patterns.json").write_text(
        json.dumps({"patterns": [
            {"regex": "skip_gates\\s*=", "reason": "A", "grade": "A", "name": "skip_gates_usage"},
        ]}),
        encoding="utf-8",
    )

    fake_funcs = {
        "load_patterns": lambda root: [
            {"regex": "skip_gates\\s*=", "reason": "A", "grade": "A", "name": "skip_gates_usage"},
        ],
        "scan_studio": lambda root, pats: {},  # no findings
        "write_conflict_map": lambda root, f, p, out: None,
        "append_history": lambda root, f: None,
    }
    monkeypatch.setattr(mod, "_resolve_harness_imports", lambda hp, skip: fake_funcs)

    rc = mod.main(["--studio-root", str(studio), "--skip-github-issue"])
    assert rc == 0
    state_text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    assert "phase_lock: false" in state_text
    assert "phase_lock: true" not in state_text


def test_main_exit_1_when_a_grade_found(_drift_scan_module, tmp_path, monkeypatch):
    """Test 5: A급 findings → exit 1 + STATE.md phase_lock: true + gh subprocess called."""
    mod = _drift_scan_module

    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    (studio / ".planning" / "STATE.md").write_text(
        "---\n"
        "gsd_state_version: 1.0\n"
        "status: executing\n"
        "phase_lock: false\n"
        "progress:\n"
        "  total_phases: 11\n"
        "---\n\n"
        "# STATE\n",
        encoding="utf-8",
    )

    pats = [
        {"regex": "skip_gates\\s*=", "reason": "A", "grade": "A", "name": "skip_gates_usage"},
        {"regex": "segments\\s*\\[\\s*\\]", "reason": "B", "grade": "B", "name": "segments_deprecated"},
    ]
    fake_funcs = {
        "load_patterns": lambda root: pats,
        "scan_studio": lambda root, p: {
            "skip_gates_usage": [{"file": "x.py", "line": 3, "match": "skip_gates = True"}],
            "segments_deprecated": [{"file": "y.py", "line": 1, "match": "segments[]"}],
        },
        "write_conflict_map": lambda root, f, p, out: None,
        "append_history": lambda root, f: None,
    }
    monkeypatch.setattr(mod, "_resolve_harness_imports", lambda hp, skip: fake_funcs)

    gh_calls: list[dict] = []

    def _fake_run(cmd, **kwargs):
        gh_calls.append({"cmd": cmd, "kwargs": kwargs})
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    rc = mod.main(["--studio-root", str(studio)])
    assert rc == 1, f"expected exit 1 on A-grade findings, got {rc}"
    state_text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    assert "phase_lock: true" in state_text, state_text
    assert "block_reason" in state_text, state_text
    assert "block_since" in state_text, state_text
    # gh subprocess invoked once with correct label + body-file stdin route
    assert len(gh_calls) == 1, gh_calls
    cmd = gh_calls[0]["cmd"]
    assert cmd[0] == "gh" and cmd[1] == "issue" and cmd[2] == "create"
    assert "--label" in cmd
    label_idx = cmd.index("--label")
    assert cmd[label_idx + 1] == "drift,critical,phase-10,auto"


def test_a_grade_count_uses_grade_field(_drift_scan_module, tmp_path, monkeypatch):
    """Test 7: B/C 급 pattern 만 findings 에 있을 때 A급 count == 0 → exit 0."""
    mod = _drift_scan_module

    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    (studio / ".planning" / "STATE.md").write_text(
        "---\n"
        "gsd_state_version: 1.0\n"
        "phase_lock: false\n"
        "---\n\nbody\n",
        encoding="utf-8",
    )

    pats = [
        {"regex": "segments\\s*\\[\\s*\\]", "reason": "B", "grade": "B", "name": "segments_deprecated"},
        {"regex": "SKILL\\.md", "reason": "C", "grade": "C", "name": "skill_md_mention"},
    ]
    fake_funcs = {
        "load_patterns": lambda root: pats,
        "scan_studio": lambda root, p: {
            "segments_deprecated": [{"file": "y.py", "line": 1, "match": "segments[]"}],
            "skill_md_mention": [{"file": "z.md", "line": 2, "match": "SKILL.md"}],
        },
        "write_conflict_map": lambda root, f, p, out: None,
        "append_history": lambda root, f: None,
    }
    monkeypatch.setattr(mod, "_resolve_harness_imports", lambda hp, skip: fake_funcs)

    rc = mod.main(["--studio-root", str(studio), "--skip-github-issue"])
    assert rc == 0
    state_text = (studio / ".planning" / "STATE.md").read_text(encoding="utf-8")
    assert "phase_lock: false" in state_text
    assert "phase_lock: true" not in state_text


def test_cli_dry_run_no_state_md_mutation(_drift_scan_module, tmp_path, monkeypatch):
    """Test 8: --dry-run → STATE.md sha256 before/after 동일."""
    import hashlib

    mod = _drift_scan_module

    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    state_md = studio / ".planning" / "STATE.md"
    state_md.write_text(
        "---\ngsd_state_version: 1.0\nphase_lock: false\n---\n\nbody\n",
        encoding="utf-8",
    )
    before = hashlib.sha256(state_md.read_bytes()).hexdigest()

    pats = [{"regex": "skip_gates\\s*=", "reason": "A", "grade": "A", "name": "skip_gates_usage"}]
    fake_funcs = {
        "load_patterns": lambda root: pats,
        "scan_studio": lambda root, p: {
            "skip_gates_usage": [{"file": "x.py", "line": 1, "match": "skip_gates = True"}],
        },
        "write_conflict_map": lambda root, f, p, out: None,
        "append_history": lambda root, f: None,
    }
    monkeypatch.setattr(mod, "_resolve_harness_imports", lambda hp, skip: fake_funcs)

    rc = mod.main(["--studio-root", str(studio), "--dry-run", "--skip-github-issue"])
    assert rc == 0, "dry-run 은 A-grade 감지하더라도 상태 변경 없이 exit 0"
    after = hashlib.sha256(state_md.read_bytes()).hexdigest()
    assert before == after, "STATE.md mutated during --dry-run"


def test_cli_harness_path_override_missing_falls_back_to_local(
    _drift_scan_module, tmp_path, monkeypatch, capsys,
):
    """Test 9: --harness-path=<nonexistent> → WARN + local-only mode (WARNING #4)."""
    mod = _drift_scan_module

    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    (studio / ".planning" / "STATE.md").write_text(
        "---\ngsd_state_version: 1.0\nphase_lock: false\n---\n\nbody\n",
        encoding="utf-8",
    )
    # Minimal deprecated_patterns.json for _local_load_patterns.
    # NOTE: use a regex that requires control characters so it never matches
    # the json file itself (which contains the regex string literally).
    (studio / ".claude" / "deprecated_patterns.json").write_text(
        json.dumps({"patterns": [
            {"regex": "\\x00zzz_never_matches_\\x00", "reason": "A",
             "grade": "A", "name": "unused"},
        ]}),
        encoding="utf-8",
    )

    nonexistent = tmp_path / "definitely_not_there_harness" / "scripts"
    rc = mod.main([
        "--studio-root", str(studio),
        "--harness-path", str(nonexistent),
        "--skip-github-issue",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    # stderr WARN present
    assert "harness" in captured.err.lower()
    assert "local-only" in captured.err.lower() or "fallback" in captured.err.lower()
    # stdout JSON summary with mode=local-only
    assert '"mode": "local-only"' in captured.out
    assert '"a_grade_count": 0' in captured.out


def test_cli_skip_harness_import_local_only(_drift_scan_module, tmp_path, capsys):
    """Test 10: --skip-harness-import → harness 로드 skip + local-only scan."""
    mod = _drift_scan_module

    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    (studio / ".planning" / "STATE.md").write_text(
        "---\ngsd_state_version: 1.0\nphase_lock: false\n---\n\nbody\n",
        encoding="utf-8",
    )
    (studio / ".claude" / "deprecated_patterns.json").write_text(
        json.dumps({"patterns": []}),
        encoding="utf-8",
    )

    rc = mod.main([
        "--studio-root", str(studio),
        "--skip-harness-import",
        "--skip-github-issue",
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "local-only" in captured.err.lower() or "skip-harness-import" in captured.err.lower()
    assert '"mode": "local-only"' in captured.out


def test_harness_missing_path_falls_back_via_default(
    _drift_scan_module, tmp_path, monkeypatch, capsys,
):
    """Test 11: DEFAULT_HARNESS_SCRIPTS monkeypatch → nonexistent → local-only."""
    mod = _drift_scan_module

    studio = tmp_path / "studio"
    (studio / ".planning").mkdir(parents=True)
    (studio / ".claude").mkdir(parents=True)
    (studio / ".planning" / "STATE.md").write_text(
        "---\ngsd_state_version: 1.0\nphase_lock: false\n---\n\nbody\n",
        encoding="utf-8",
    )
    (studio / ".claude" / "deprecated_patterns.json").write_text(
        json.dumps({"patterns": [
            {"regex": "\\x00never_matches_\\x00", "reason": "A", "grade": "A", "name": "unused"},
        ]}),
        encoding="utf-8",
    )

    nonexistent = tmp_path / "ghost_harness" / "scripts"
    monkeypatch.setattr(mod, "DEFAULT_HARNESS_SCRIPTS", nonexistent)

    rc = mod.main(["--studio-root", str(studio), "--skip-github-issue"])
    captured = capsys.readouterr()
    assert rc == 0
    assert '"mode": "local-only"' in captured.out
