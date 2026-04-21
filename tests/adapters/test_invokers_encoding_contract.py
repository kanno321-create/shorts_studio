"""SPC-05 — invokers.py tempfile + --append-system-prompt-file contract.

Phase 14 ``adapter_contract`` marker 승계. 10 tests, mock-only, $0.

대표님 Phase 13 live smoke 2026-04-22 시도에서 드러난 SPC-01 encoding 실패
(10591 chars Korean body → argv 직접 전달 → rc=1 "프롬프트가 너무 깁니다") 의
Wave 1 fix 를 고정합니다. invokers.py ``_invoke_claude_cli_once`` 가 반드시
tempfile 에 UTF-8 로 system_prompt 를 기록한 뒤 path 만 argv 에 넘기도록
강제하고, 명시적 cleanup + OSError warn-continue 패턴 (CLAUDE.md 금기 #3) 을
계약합니다. Phase 11 stdin invariant (user_prompt stdin 경유) 는 그대로
보존됨을 최종 test 로 재확인합니다.

Fixture 재사용 방침: 본 파일은 tests/adapters/conftest.py 의 ``repo_root``
PYTHONPATH 보강을 공유하며, Wave 0 tests/phase15/conftest.py 의 KOREAN_FILLER
payload 와 동일 크기 (10KB+) 를 in-file 상수로 재구성합니다 (fixture cross-
package 의존을 피해 pytest collection 규약을 준수합니다).

References:
    - .planning/phases/15-.../15-RESEARCH.md §SPC-05 contract test cases
    - .planning/phases/15-.../15-02-PLAN.md
    - scripts/orchestrator/invokers.py L121~187 (``_invoke_claude_cli_once``)
    - tests/phase11/test_invoker_stdin.py (_make_popen_mock 패턴)
    - tests/adapters/test_veo_i2v_contract.py (adapter_contract marker 선례)
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator.invokers import _invoke_claude_cli_once


pytestmark = pytest.mark.adapter_contract


# 10KB+ 한국어 body — Phase 13 supervisor AGENT.md 10591 chars 와 동급 drift
# 재현 임계값 (대표님). 51 chars × 200 반복 ≈ 10200 chars.
KOREAN_10KB = "대표님이 원하시는 최고 품질의 영상 제작 지침서입니다. " * 200

# 10KB ASCII body — 한국어 cp949 인코딩 가설을 통제 검증하기 위한 대조군.
ASCII_10KB = "You are a careful script writer. " * 320


def _make_popen_mock(
    stdout: str = '{"ok":true}',
    stderr: str = "",
    returncode: int = 0,
) -> MagicMock:
    """Phase 11 선례와 동일한 MagicMock Popen factory (mock-only, $0)."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc


class TestArgvShape:
    """SPC-01 fix 확증 — argv 에는 body 가 아니라 file path 만 존재."""

    def test_system_prompt_file_argv_shape(self):
        """``--append-system-prompt-file`` flag + short path argv 강제."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            popen_cls.return_value = _make_popen_mock()
            _invoke_claude_cli_once(
                system_prompt=KOREAN_10KB,
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
            argv = popen_cls.call_args.args[0]
            assert "--append-system-prompt-file" in argv, (
                "SPC-01 fix 미적용 — body 가 여전히 argv 직접 전달 (대표님)"
            )
            idx = argv.index("--append-system-prompt-file")
            path_arg = argv[idx + 1]
            # Path 여야 하고, body 내용 자체가 argv 에 없어야 함.
            assert len(path_arg) < 500, (
                "argv 뒤 slot 이 path 가 아니라 body 로 보임 (대표님)"
            )
            assert KOREAN_10KB[:1000] not in " ".join(argv), (
                "body 앞부분 1000자가 argv 에 여전히 노출 — fix 실패 (대표님)"
            )

    def test_system_prompt_file_content_matches(self):
        """argv 의 path 를 열면 원본 system_prompt 와 byte-wise 일치."""
        captured: dict = {}

        def _capture_popen(cmd, **kw):
            captured["cmd"] = cmd
            idx = cmd.index("--append-system-prompt-file")
            captured["content"] = Path(cmd[idx + 1]).read_text(
                encoding="utf-8"
            )
            return _make_popen_mock()

        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            _invoke_claude_cli_once(
                system_prompt=KOREAN_10KB,
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
        assert captured["content"] == KOREAN_10KB, (
            "tempfile 내용이 원본과 불일치 — encoding 손실 의심 (대표님)"
        )


class TestLargeBodyHandling:
    """10KB+ body 가 argv 경로를 거치지 않음을 입력 규모별 확증."""

    def test_10kb_body_korean_chars_success(self):
        """한국어 10KB body + mock rc=0 → 예외 없이 return."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            popen_cls.return_value = _make_popen_mock()
            result = _invoke_claude_cli_once(
                system_prompt=KOREAN_10KB,
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
            assert result, "10KB 한국어 body 호출이 빈 결과 반환 (대표님)"

    def test_10kb_body_ascii_success(self):
        """ASCII 10KB body 도 동일 경로 — encoding 특수성 없는 대조군."""
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls:
            popen_cls.return_value = _make_popen_mock()
            result = _invoke_claude_cli_once(
                system_prompt=ASCII_10KB,
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
            assert result


class TestCleanup:
    """명시적 finally cleanup — 정상 / timeout / rc=1 세 경로 모두 삭제."""

    def test_temp_file_cleanup_on_success(self):
        paths_seen: list[str] = []

        def _capture_popen(cmd, **kw):
            idx = cmd.index("--append-system-prompt-file")
            paths_seen.append(cmd[idx + 1])
            return _make_popen_mock()

        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            _invoke_claude_cli_once(
                system_prompt="x",
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
        assert paths_seen, "argv 에서 path 미발견 (대표님)"
        assert not Path(paths_seen[0]).exists(), (
            "정상 완료 후 tempfile cleanup 누락 (대표님 SPC-01 fix 필요)"
        )

    def test_temp_file_cleanup_on_timeout(self):
        paths_seen: list[str] = []

        def _capture_popen(cmd, **kw):
            idx = cmd.index("--append-system-prompt-file")
            paths_seen.append(cmd[idx + 1])
            proc = MagicMock()
            # invokers.py 는 TimeoutExpired 시 proc.kill() 후 reap 으로
            # proc.communicate() 를 한 번 더 호출합니다. 첫 호출은
            # TimeoutExpired, 두 번째는 정상 반환하도록 side_effect 를
            # 순차 지정 (Phase 11 선례와 동일, 대표님).
            proc.communicate.side_effect = [
                subprocess.TimeoutExpired(cmd=cmd[0], timeout=30),
                ("", ""),
            ]
            return proc

        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            with pytest.raises(RuntimeError, match="타임아웃"):
                _invoke_claude_cli_once(
                    system_prompt="x",
                    user_prompt="u",
                    json_schema="{}",
                    cli_path="/fake/claude",
                )
        assert paths_seen
        assert not Path(paths_seen[0]).exists(), (
            "timeout 경로에서 cleanup 누락 — finally 블록 누락 의심 (대표님)"
        )

    def test_temp_file_cleanup_on_rc1(self):
        paths_seen: list[str] = []

        def _capture_popen(cmd, **kw):
            idx = cmd.index("--append-system-prompt-file")
            paths_seen.append(cmd[idx + 1])
            return _make_popen_mock(
                returncode=1, stderr="프롬프트가 너무 깁니다."
            )

        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            with pytest.raises(RuntimeError, match="rc=1"):
                _invoke_claude_cli_once(
                    system_prompt="x",
                    user_prompt="u",
                    json_schema="{}",
                    cli_path="/fake/claude",
                )
        assert paths_seen
        assert not Path(paths_seen[0]).exists(), (
            "rc=1 경로에서 cleanup 누락 (대표님)"
        )


class TestEncoding:
    """tempfile 의 on-disk byte 직렬화 — UTF-8 강제 + BOM 금지."""

    def test_temp_file_utf8_encoding(self):
        captured: dict = {}

        def _capture_popen(cmd, **kw):
            idx = cmd.index("--append-system-prompt-file")
            path = Path(cmd[idx + 1])
            captured["bytes"] = path.read_bytes()
            return _make_popen_mock()

        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen",
            side_effect=_capture_popen,
        ):
            _invoke_claude_cli_once(
                system_prompt=KOREAN_10KB,
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
        assert not captured["bytes"].startswith(b"\xef\xbb\xbf"), (
            "UTF-8 BOM 검출 — Claude CLI 파싱 실패 위험 (대표님)"
        )
        # 한국어 문자가 cp949 아닌 UTF-8 로 직렬화되었는지 확인.
        assert "대표님".encode("utf-8") in captured["bytes"], (
            "한국어 바이트가 UTF-8 인코딩 부재 — cp949 fallback 의심 (대표님)"
        )


class TestCleanupErrorHandling:
    """os.unlink OSError — 명시적 logger.warning + no raise (금기 #3)."""

    def test_unlink_oserror_logged_not_raised(self, caplog):
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen"
        ) as popen_cls, patch(
            "scripts.orchestrator.invokers.os.unlink",
            side_effect=OSError("Access denied"),
        ):
            popen_cls.return_value = _make_popen_mock()
            caplog.set_level(logging.WARNING)
            # OSError 는 삼키지 말고 명시적 warn → 정상 return (대표님 금기 #3).
            result = _invoke_claude_cli_once(
                system_prompt="x",
                user_prompt="u",
                json_schema="{}",
                cli_path="/fake/claude",
            )
            assert result, "unlink 실패가 return 경로를 막음 (대표님)"
            assert any(
                "삭제 실패" in record.message for record in caplog.records
            ), (
                "unlink OSError 가 logger.warning 으로 기록되지 않음 (대표님)"
            )


class TestPhase11Invariant:
    """Phase 11 stdin invariant — user_prompt 는 argv 아니라 communicate(input=)."""

    def test_stdin_unchanged_user_prompt(self):
        mock_proc = _make_popen_mock()
        with patch(
            "scripts.orchestrator.invokers.subprocess.Popen",
            return_value=mock_proc,
        ) as popen_cls:
            _invoke_claude_cli_once(
                system_prompt="s",
                user_prompt="내_payload_JSON",
                json_schema="{}",
                cli_path="/fake/claude",
            )
            mock_proc.communicate.assert_called_once()
            kwargs = mock_proc.communicate.call_args.kwargs
            assert kwargs.get("input") == "내_payload_JSON", (
                "Phase 11 stdin invariant 파괴 — user_prompt stdin 경유 아님 (대표님)"
            )
            argv = popen_cls.call_args.args[0]
            assert "내_payload_JSON" not in argv, (
                "user_prompt 가 argv 에 노출됨 — Phase 11 D-01 재발 (대표님)"
            )
