"""SPC-01 현상 재현 — Wave 1 fix 후 post-fix 계약 고정 (mock-only, $0).

대표님 Phase 13 live smoke 에서 드러난 rc=1 "프롬프트가 너무 깁니다"
현상을 실 Claude CLI 호출 없이 mock 으로 고정했고, Wave 1 (Plan 15-02)
에서 invokers.py 가 ``--append-system-prompt-file`` 경로로 전환되어
``TestCurrentArgvShape`` 두 개 테스트는 2026-04-21 post-fix assertions
로 flipped 되었습니다 (body-NOT-in-argv + file-path-present).

TestRc1Reproduction 은 contract 불변 — fix 후에도 rc=1 응답이 오면
RuntimeError("rc=1") 로 Korean-first 반환해야 함을 유지합니다.

References:
    - scripts/orchestrator/invokers.py L121~200 (``_invoke_claude_cli_once``)
    - tests/phase11/test_invoker_stdin.py (mock 사용 precedent)
    - tests/adapters/test_invokers_encoding_contract.py (SPC-05 10 tests)
    - .planning/phases/15-.../15-02-SUMMARY.md (fix anchor)
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.invokers import _invoke_claude_cli_once


# 10KB+ 한국어 body — supervisor AGENT.md 10591 chars 와 동급 drift
# 재현 임계값 (대표님).
KOREAN_10KB = "대표님이 원하시는 최고 품질의 영상 제작 지침서입니다. " * 200


class TestCurrentArgvShape:
    """Wave 1 post-fix baseline — argv 에 body 대신 tempfile path 만 존재.

    2026-04-21 Plan 15-02 에서 invokers.py 가 ``--append-system-prompt-file``
    + UTF-8 tempfile 경로로 전환됨에 따라 두 테스트 모두 post-fix assertion
    으로 flipped 되었습니다. body 10KB 가 argv 에 직접 노출되지 않아야 하고,
    ``--append-system-prompt-file`` flag 는 반드시 존재해야 합니다.
    """

    def test_fix_applied_argv_path_not_body(self, mock_popen):
        """post-fix: body 10KB 가 argv 에 직접 노출되지 않음."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            popen_cls.return_value = mock_popen()
            _invoke_claude_cli_once(
                system_prompt=KOREAN_10KB,
                user_prompt="u",
                json_schema='{"type":"object"}',
                cli_path="/fake/claude",
            )
            argv = popen_cls.call_args.args[0]
            # body 가 argv 어느 slot 에도 직접 존재하지 않아야 함
            assert KOREAN_10KB not in argv, (
                "SPC-01 fix 파괴 — body 가 argv 에 직접 전달됨 (대표님)"
            )
            # 대신 --append-system-prompt-file + 짧은 path 가 존재해야 함
            assert "--append-system-prompt-file" in argv, (
                "fix flag 누락 (대표님) — tempfile 경로 미사용"
            )
            idx = argv.index("--append-system-prompt-file")
            path_arg = argv[idx + 1]
            assert len(path_arg) < 500, (
                "argv path slot 이 짧은 path 가 아님 (대표님)"
            )

    def test_append_system_prompt_file_present(self, mock_popen):
        """post-fix: ``--append-system-prompt-file`` flag 가 cmd 에 반드시 존재."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            popen_cls.return_value = mock_popen()
            _invoke_claude_cli_once(
                system_prompt=KOREAN_10KB,
                user_prompt="u",
                json_schema='{}',
                cli_path="/fake/claude",
            )
            argv = popen_cls.call_args.args[0]
            assert "--append-system-prompt-file" in argv, (
                "fix regression — flag 부재 (대표님)"
            )
            # 기존 argv-body flag 는 완전히 제거되었는지 확인 (drift guard).
            assert "--append-system-prompt" not in [
                a for a in argv if a == "--append-system-prompt"
            ], (
                "구 flag ``--append-system-prompt`` (body-direct) 잔류 (대표님)"
            )


class TestRc1Reproduction:
    """Phase 13 evidence 와 동일한 rc=1 error path 를 mock 으로 재현."""

    def test_10kb_body_triggers_rc1_via_mock(self, mock_popen):
        """mock rc=1 + Korean stderr → RuntimeError("rc=1") 확인."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            popen_cls.return_value = mock_popen(
                returncode=1, stderr="프롬프트가 너무 깁니다."
            )
            with pytest.raises(RuntimeError, match=r"rc=1"):
                _invoke_claude_cli_once(
                    system_prompt=KOREAN_10KB,
                    user_prompt="u",
                    json_schema='{}',
                    cli_path="/fake/claude",
                )


class TestPhase11Invariant:
    """Phase 11 D-01/D-02 invariant — user_prompt 는 stdin 경유 보존."""

    def test_phase11_stdin_invariant_preserved(self, mock_popen):
        """user_prompt 는 communicate(input=) 로만 전달 — argv 에 없음."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            mock_proc = mock_popen()
            popen_cls.return_value = mock_proc
            _invoke_claude_cli_once(
                system_prompt="short",
                user_prompt="내_대본_내용",
                json_schema='{}',
                cli_path="/fake/claude",
            )
            # stdin 경유 확인
            mock_proc.communicate.assert_called_once()
            kwargs = mock_proc.communicate.call_args.kwargs
            assert kwargs.get("input") == "내_대본_내용"
            # argv 에는 user_prompt 없음
            argv = popen_cls.call_args.args[0]
            assert "내_대본_내용" not in argv
