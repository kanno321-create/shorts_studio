"""Integration tests for scripts.notebooklm.query_notebook (Phase 6 Plan 03 WIKI-03).

Exercises the real ``subprocess.run`` code path end-to-end against a fake
skill tree. The fake skill's ``run.py`` is a stdlib-only script that emits a
canned payload and exits with the configured returncode — no Playwright, no
browser, no network. Verifies the wrapper survives a real process fork with
Korean payloads (cp949 regression guard), argv passthrough, and stderr
propagation on non-zero exit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.notebooklm.query import FOLLOW_UP_MARKER, query_notebook


def _make_fake_skill(tmp_path: Path, stdout_payload: str, returncode: int = 0) -> Path:
    """Build a minimal fake skill tree with a run.py that prints the payload.

    Layout mirrors the real external skill:
        skill/
          scripts/run.py   <- prints payload, exits returncode
          data/            <- placeholder for library.json etc.
    """
    skill = tmp_path / "skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "data").mkdir()
    run_py = skill / "scripts" / "run.py"
    # Force the child's stdout to UTF-8 — mirrors what the real ask_question.py
    # would need on Windows cp949 default console. Without this, writing
    # Korean / em-dash to stdout raises UnicodeEncodeError inside the child.
    run_py.write_text(
        "import sys\n"
        "sys.stdout.reconfigure(encoding='utf-8')\n"
        f"sys.stdout.write({stdout_payload!r})\n"
        f"sys.exit({returncode})\n",
        encoding="utf-8",
    )
    return skill


def test_real_subprocess_success_round_trip(tmp_path: Path):
    """Real subprocess.run call to a fake run.py; assert stripped stdout returned."""
    payload = "실제 답변입니다.\n\n" + FOLLOW_UP_MARKER + " to know?"
    skill = _make_fake_skill(tmp_path, payload, returncode=0)
    result = query_notebook("테스트", "N", skill_path=skill)
    assert "실제 답변입니다" in result
    assert "EXTREMELY IMPORTANT" not in result


def test_real_subprocess_error_propagates(tmp_path: Path):
    """rc=1 from fake run.py => RuntimeError with stderr surfaced to caller."""
    skill = tmp_path / "skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text(
        "import sys\nsys.stderr.write('not authenticated')\nsys.exit(1)\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="not authenticated"):
        query_notebook("Q", "N", skill_path=skill)


def test_real_subprocess_utf8_korean(tmp_path: Path):
    """Korean output survives subprocess round trip (cp949 regression, STATE #28)."""
    payload = "한국어 답변 with em-dash — and special chars"
    skill = _make_fake_skill(tmp_path, payload)
    result = query_notebook("테스트", "N", skill_path=skill)
    assert "한국어 답변" in result
    assert "em-dash —" in result


def test_timeout_argument_passed(tmp_path: Path, monkeypatch):
    """timeout_s flows into --timeout argv position (real invocation path)."""
    skill = _make_fake_skill(tmp_path, "ok")
    captured = {}
    real_run = subprocess.run

    def spy_run(cmd, **kw):
        captured["cmd"] = cmd
        return real_run(cmd, **kw)

    monkeypatch.setattr("scripts.notebooklm.query.subprocess.run", spy_run)
    query_notebook("Q", "N", timeout_s=42, skill_path=skill)
    assert "--timeout" in captured["cmd"]
    idx = captured["cmd"].index("--timeout")
    assert captured["cmd"][idx + 1] == "42"


def test_notebook_id_passed_verbatim(tmp_path: Path):
    """Complex notebook_id (dashes) reaches the fake run.py unchanged."""
    skill = tmp_path / "skill"
    (skill / "scripts").mkdir(parents=True)
    # run.py echoes back the --notebook-id value so we can assert passthrough.
    (skill / "scripts" / "run.py").write_text(
        "import sys\n"
        "args = sys.argv\n"
        "idx = args.index('--notebook-id')\n"
        "sys.stdout.write('NBID=' + args[idx+1])\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    out = query_notebook("Q", "naberal-shorts-channel-bible", skill_path=skill)
    assert out == "NBID=naberal-shorts-channel-bible"


def test_missing_skill_raises_filenotfound(tmp_path: Path):
    """Skill directory does not exist -> FileNotFoundError (D-7 skill absent)."""
    # No mkdir — path does not exist.
    absent = tmp_path / "never_created"
    with pytest.raises(FileNotFoundError):
        query_notebook("Q", "N", skill_path=absent)
