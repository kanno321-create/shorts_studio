"""SPC-01 현상 재현 — Wave 1 fix 의 before/after 기준선 (mock-only, $0).

대표님 Phase 13 live smoke 에서 드러난 rc=1 "프롬프트가 너무 깁니다"
현상을 실 Claude CLI 호출 없이 mock 으로 고정. Wave 1 에서 invokers.py
가 ``--append-system-prompt-file`` 경로로 전환되면 ``TestCurrentArgvShape``
두 개 테스트는 Wave 1 plan 에서 flip (path-in-argv + body-NOT-in-argv)
되어 계약 방향이 역전됩니다.

References:
    - scripts/orchestrator/invokers.py L121~187 (``_invoke_claude_cli_once``)
    - tests/phase11/test_invoker_stdin.py (mock 사용 precedent)
    - .planning/phases/15-.../15-RESEARCH.md §Phase 13 failure evidence
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.invokers import _invoke_claude_cli_once


# 10KB+ 한국어 body — supervisor AGENT.md 10591 chars 와 동급 drift
# 재현 임계값 (대표님).
KOREAN_10KB = "대표님이 원하시는 최고 품질의 영상 제작 지침서입니다. " * 200


class TestCurrentArgvShape:
    """Wave 1 fix 전 baseline — argv 에 body 직접 전달 상태 고정.

    Wave 1 (Plan 15-02) 이 완료되면 이 class 의 두 테스트는 Wave 1 plan
    에서 flip 되어 ``--append-system-prompt-file`` + 임시 파일 경로
    계약을 검증하게 됩니다.
    """

    def test_current_argv_passes_body_direct(self, mock_popen):
        """현 drift 상태: body 10KB 가 argv 에 직접 있음을 고정."""
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
            # ``--append-system-prompt`` 바로 뒤 slot 에 body 가 직접 전달됨
            idx = argv.index("--append-system-prompt")
            assert argv[idx + 1] == KOREAN_10KB, (
                "현 drift 상태: body 가 argv 에 직접 전달됨 "
                "— Wave 1 에서 수정 예정 (대표님)"
            )

    def test_current_argv_no_file_path_yet(self, mock_popen):
        """Wave 1 fix 전: ``--append-system-prompt-file`` flag 미사용."""
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
            assert "--append-system-prompt-file" not in argv, (
                "Wave 1 fix 완료 후 이 test 는 Wave 1 PLAN 에서 "
                "flip 될 것입니다 (대표님)."
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
