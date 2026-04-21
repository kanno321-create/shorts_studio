"""PIPELINE-01 stdin-piped Claude CLI invocation tests (6 cases).

D-01/D-02/D-04 LOCKED decisions:
- user_prompt MUST flow through stdin (not argv positional)
- argv canonical form (Phase 15 SPC-01 fix, 2026-04-21):
  [cli_path, --print, --append-system-prompt-file, <tempfile_path>,
   --json-schema, schema] — body 는 argv 에 없고 UTF-8 tempfile 경유.
- Korean-first RuntimeError messages preserved verbatim (대표님 호칭)
- cli_runner test seam unchanged — these tests patch subprocess.Popen
  at module level (scripts.orchestrator.invokers.subprocess.Popen).

Regression protection: tests/phase04/+ use the `cli_runner` injection seam
(bypass subprocess entirely); those 244 tests are unaffected by this rewrite.

Phase 11 Option D note (2026-04-21, F-D2-EXCEPTION-01 defense-in-depth):
the production entry point ``_invoke_claude_cli`` was promoted to a
retry-with-JSON-nudge wrapper (up to 3 attempts). The single-attempt
logic moved to ``_invoke_claude_cli_once``; these PIPELINE-01 regression
tests target ``_invoke_claude_cli_once`` directly so the stdin/argv/
timeout/rc/stdout contract remains asserted without the retry layer
intercepting side_effects. Retry behavior is tested separately in
``test_invoker_retry.py``.

Phase 15 SPC-01 update (2026-04-21, Plan 15-02):
``_invoke_claude_cli_once`` now writes system_prompt to a UTF-8 tempfile
and passes ``--append-system-prompt-file <path>`` (not the body directly)
to avoid rc=1 "프롬프트가 너무 깁니다" from 10KB+ Korean bodies.
test_invoker_argv_contains_expected_flags was updated to assert the new
post-fix argv shape. tempfile cleanup contract is pinned by
tests/adapters/test_invokers_encoding_contract.py (SPC-05, 10 tests).
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator.invokers import (
    _invoke_claude_cli_once as _invoke_claude_cli,
)


def _make_popen_mock(
    stdout: str = '{"ok": true}',
    stderr: str = "",
    returncode: int = 0,
) -> MagicMock:
    """Build a MagicMock Popen-return that emulates communicate() contract."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc


def test_invoker_uses_stdin_piping():
    """Popen invoked with stdin=PIPE; user_prompt passed via communicate(input=...)."""
    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        popen_cls.return_value = _make_popen_mock()
        _invoke_claude_cli(
            system_prompt="SYS",
            user_prompt="USER_PROMPT_MARKER",
            json_schema='{"type":"object"}',
            cli_path="/fake/claude",
            timeout_s=30,
        )
        call = popen_cls.call_args
        # argv is first positional arg
        argv = call.args[0]
        assert "USER_PROMPT_MARKER" not in argv, "user_prompt MUST NOT be in argv"
        assert call.kwargs["stdin"] is subprocess.PIPE
        assert call.kwargs["stdout"] is subprocess.PIPE
        assert call.kwargs["stderr"] is subprocess.PIPE
        proc = popen_cls.return_value
        proc.communicate.assert_called_once_with(
            input="USER_PROMPT_MARKER", timeout=30
        )


def test_invoker_argv_contains_expected_flags():
    """argv matches Phase 15 SPC-01 post-fix canonical form (tempfile path, not body).

    대표님 Plan 15-02 (2026-04-21) 로 ``--append-system-prompt`` + body
    argv 가 ``--append-system-prompt-file`` + UTF-8 tempfile path 로
    교체되었습니다. body 는 argv 어느 슬롯에도 존재하지 않고, path 는 ``.md``
    확장자 + 시스템 tempdir 의 짧은 경로로 flag 바로 뒤에 위치합니다.
    Tempfile cleanup 은 finally 블록에서 검증
    (tests/adapters/test_invokers_encoding_contract.py).
    """
    from pathlib import Path as _Path

    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        popen_cls.return_value = _make_popen_mock()
        _invoke_claude_cli(
            system_prompt="SYS_BODY",
            user_prompt="u",
            json_schema='{"type":"object"}',
            cli_path="/fake/claude",
        )
        argv = popen_cls.call_args.args[0]

        # Skeleton — body 대신 --append-system-prompt-file + <path>.
        assert argv[0] == "/fake/claude"
        assert argv[1] == "--print"
        assert argv[2] == "--append-system-prompt-file"
        path_arg = argv[3]
        # path 는 실제 tempfile — body (argv 직접 전달) 가 아님.
        assert path_arg != "SYS_BODY", "body 가 여전히 argv 직접 전달 (대표님)"
        assert _Path(path_arg).suffix == ".md"
        # 파일은 이미 cleanup 됐으므로 exists() False — 정상 (finally).
        assert argv[4] == "--json-schema"
        assert argv[5] == '{"type":"object"}'
        assert len(argv) == 6

        # 구 flag + body 직접 전달 drift 재발 방지 guard.
        assert "--append-system-prompt" not in argv, (
            "구 D-02 flag (body-direct) 잔류 — SPC-01 fix regression (대표님)"
        )
        assert "SYS_BODY" not in argv


def test_invoker_timeout_raises_korean_runtime_error():
    """TimeoutExpired → RuntimeError with Korean diagnostic + 대표님 + proc.kill()+drain."""
    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        proc = MagicMock()
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="claude", timeout=30),
            ("", ""),  # drain call after kill
        ]
        popen_cls.return_value = proc
        with pytest.raises(RuntimeError) as exc:
            _invoke_claude_cli(
                system_prompt="s", user_prompt="u", json_schema="{}",
                cli_path="/fake/claude", timeout_s=30,
            )
        msg = str(exc.value)
        assert "타임아웃" in msg
        assert "대표님" in msg
        assert "30s" in msg
        proc.kill.assert_called_once()
        # communicate called twice: initial + drain
        assert proc.communicate.call_count == 2


def test_invoker_rc_nonzero_raises_korean_error():
    """returncode!=0 → RuntimeError with rc + 대표님 + stderr tail (last 500)."""
    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        popen_cls.return_value = _make_popen_mock(
            stdout="", stderr="boom detail", returncode=2,
        )
        with pytest.raises(RuntimeError) as exc:
            _invoke_claude_cli(
                system_prompt="s", user_prompt="u", json_schema="{}",
                cli_path="/fake/claude",
            )
        msg = str(exc.value)
        assert "rc=2" in msg
        assert "대표님" in msg
        assert "boom detail" in msg


def test_invoker_empty_stdout_raises_korean_error():
    """rc=0 but stdout empty → RuntimeError with stdout diagnostic + 대표님."""
    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        popen_cls.return_value = _make_popen_mock(
            stdout="", stderr="", returncode=0,
        )
        with pytest.raises(RuntimeError) as exc:
            _invoke_claude_cli(
                system_prompt="s", user_prompt="u", json_schema="{}",
                cli_path="/fake/claude",
            )
        msg = str(exc.value)
        assert "stdout 비어있음" in msg
        assert "대표님" in msg


def test_invoker_korean_prompt_round_trip():
    """Korean chars in user_prompt passed through; Popen kwargs include utf-8 encoding."""
    korean_prompt = "나베랄 감마 테스트 {대표님} — 한국어 왕복"
    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        popen_cls.return_value = _make_popen_mock(stdout='{"reply":"ok"}')
        out = _invoke_claude_cli(
            system_prompt="시스템", user_prompt=korean_prompt, json_schema="{}",
            cli_path="/fake/claude",
        )
        assert out == '{"reply":"ok"}'
        kwargs = popen_cls.call_args.kwargs
        assert kwargs.get("text") is True
        assert kwargs.get("encoding") == "utf-8"
        assert kwargs.get("errors") == "replace"
        popen_cls.return_value.communicate.assert_called_once()
        assert (
            popen_cls.return_value.communicate.call_args.kwargs["input"]
            == korean_prompt
        )
