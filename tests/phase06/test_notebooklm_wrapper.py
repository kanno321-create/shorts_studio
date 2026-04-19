"""Unit tests for scripts.notebooklm.query_notebook wrapper (Phase 6 Plan 03 WIKI-03).

Covers the D-6 argv boundary, D-7 skill-path resolution precedence, UTF-8
encoding guard (Phase 5 STATE #28), FOLLOW_UP_REMINDER marker stripping, and
the error propagation contract (FileNotFoundError + RuntimeError paths).

All subprocess invocations are monkey-patched; no real browser is launched.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.notebooklm.query import (
    DEFAULT_SKILL_PATH,
    FOLLOW_UP_MARKER,
    _resolve_skill_path,
    _strip_follow_up,
    query_notebook,
)


# ---------------------------------------------------------------------------
# D-7 skill-path resolution precedence: kwarg > env var > hardcoded default.
# ---------------------------------------------------------------------------


def test_default_skill_path_matches_install(monkeypatch):
    """With no env var and no kwarg, resolver returns the hardcoded fallback."""
    monkeypatch.delenv("NOTEBOOKLM_SKILL_PATH", raising=False)
    assert _resolve_skill_path(None) == DEFAULT_SKILL_PATH


def test_env_var_overrides_default(monkeypatch, tmp_path: Path):
    """NOTEBOOKLM_SKILL_PATH env var takes precedence over the hardcoded default."""
    monkeypatch.setenv("NOTEBOOKLM_SKILL_PATH", str(tmp_path))
    assert _resolve_skill_path(None) == tmp_path


def test_kwarg_overrides_env(monkeypatch, tmp_path: Path):
    """Explicit ``skill_path`` kwarg wins over both env var and default."""
    monkeypatch.setenv("NOTEBOOKLM_SKILL_PATH", "/ignored/path")
    assert _resolve_skill_path(tmp_path) == tmp_path


def test_default_skill_path_is_the_2026_install():
    """D-7 hardcoded fallback value matches the 2026-04-19 install location."""
    assert str(DEFAULT_SKILL_PATH).replace("\\", "/") == (
        "C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm"
    )


# ---------------------------------------------------------------------------
# FOLLOW_UP_REMINDER marker stripping.
# ---------------------------------------------------------------------------


def test_strip_follow_up_removes_marker():
    """Marker + everything after is removed; trailing whitespace rstripped."""
    answer = "Real answer lines.\n\n" + FOLLOW_UP_MARKER + " more reminder text\nand boilerplate"
    assert _strip_follow_up(answer) == "Real answer lines."


def test_strip_follow_up_no_marker_passthrough():
    """If the marker is absent, the answer is returned unchanged."""
    answer = "A simple answer with no follow-up text."
    assert _strip_follow_up(answer) == answer


def test_strip_follow_up_multiple_markers_only_first_counts():
    """split() keeps everything before the FIRST occurrence of the marker."""
    answer = "body\n" + FOLLOW_UP_MARKER + " first\nmiddle\n" + FOLLOW_UP_MARKER + " second"
    assert _strip_follow_up(answer) == "body"


# ---------------------------------------------------------------------------
# Error propagation contract.
# ---------------------------------------------------------------------------


def test_missing_skill_path_raises(tmp_path: Path):
    """Non-existent skill dir raises FileNotFoundError carrying the offending path."""
    nonexist = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError, match="does_not_exist"):
        query_notebook("Q", "N", skill_path=nonexist)


def test_subprocess_rc_nonzero_raises(monkeypatch, mock_notebooklm_skill_env: Path):
    """rc != 0 from ask_question.py -> RuntimeError with stderr text."""
    fake_path = mock_notebooklm_skill_env

    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="auth expired")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    with pytest.raises(RuntimeError, match="auth expired"):
        query_notebook("Q", "N", skill_path=fake_path)


def test_subprocess_error_includes_notebook_id(monkeypatch, mock_notebooklm_skill_env: Path):
    """Error message must include notebook_id to aid Tier 0->1 fallback diagnosis."""
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, returncode=2, stdout="", stderr="notebook missing")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    with pytest.raises(RuntimeError, match="naberal-shorts-channel-bible"):
        query_notebook("Q", "naberal-shorts-channel-bible", skill_path=mock_notebooklm_skill_env)


# ---------------------------------------------------------------------------
# Success path + argv shape + UTF-8 guard.
# ---------------------------------------------------------------------------


def test_subprocess_success_returns_stripped(monkeypatch, mock_notebooklm_skill_env: Path):
    """rc=0 -> answer body returned with FOLLOW_UP_REMINDER stripped."""
    def fake_run(cmd, **kw):
        payload = "Real answer body.\n" + FOLLOW_UP_MARKER + " boilerplate tail"
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=payload, stderr="")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    result = query_notebook("Q", "N", skill_path=mock_notebooklm_skill_env)
    assert result == "Real answer body."


def test_subprocess_argv_shape(monkeypatch, mock_notebooklm_skill_env: Path):
    """Exact 9-element argv per plan interface contract + UTF-8 encoding."""
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["kw"] = kw
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="answer", stderr="")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    query_notebook(
        "테스트 질문",
        "naberal-shorts-channel-bible",
        timeout_s=300,
        skill_path=mock_notebooklm_skill_env,
    )
    cmd = captured["cmd"]
    # Exact argv shape — 9 elements, positional order per CONTEXT line 84-88.
    assert len(cmd) == 9, f"expected 9-element argv, got {len(cmd)}: {cmd}"
    assert cmd[0] == sys.executable
    assert cmd[1].endswith("run.py")
    assert cmd[2] == "ask_question.py"
    assert cmd[3] == "--question"
    assert cmd[4] == "테스트 질문"
    assert cmd[5] == "--notebook-id"
    assert cmd[6] == "naberal-shorts-channel-bible"
    assert cmd[7] == "--timeout"
    assert cmd[8] == "300"
    # UTF-8 encoding set — Phase 5 STATE #28 cp949 regression guard.
    assert captured["kw"].get("encoding") == "utf-8"


def test_korean_question_single_argv_item(monkeypatch, mock_notebooklm_skill_env: Path):
    """D-6: Korean with spaces stays as single argv item, not shell-split."""
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    q = "한국 시니어 시청자에게 어떤 색 팔레트가 효과적인가"
    query_notebook(q, "naberal-shorts-channel-bible", skill_path=mock_notebooklm_skill_env)
    assert q in captured["cmd"]
    # Ensure the question did not get concatenated with siblings or split by spaces.
    assert captured["cmd"].count(q) == 1


def test_timeout_buffer_30_seconds(monkeypatch, mock_notebooklm_skill_env: Path):
    """Subprocess timeout kwarg = timeout_s + 30 per CONTEXT line 605."""
    captured = {}

    def fake_run(cmd, **kw):
        captured["kw"] = kw
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    query_notebook("Q", "N", timeout_s=120, skill_path=mock_notebooklm_skill_env)
    assert captured["kw"].get("timeout") == 150  # 120 + 30


def test_default_timeout_is_600(monkeypatch, mock_notebooklm_skill_env: Path):
    """query_notebook default timeout_s is 600 seconds (plan contract)."""
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["kw"] = kw
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", fake_run)
    query_notebook("Q", "N", skill_path=mock_notebooklm_skill_env)
    assert captured["cmd"][8] == "600"
    assert captured["kw"].get("timeout") == 630
