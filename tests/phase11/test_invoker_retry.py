"""Phase 11 Option D retry-with-JSON-nudge tests (F-D2-EXCEPTION-01 defense-in-depth).

대표님 session #29 directive: after trend-collector 1차 smoke failure produced
한국어 대화체 instead of JSON, invoker must retry with a Korean nudge prompt
up to 3 total attempts before surfacing the failure as a GATE-level RuntimeError.

This test file patches ``_invoke_claude_cli_once`` (the single-attempt worker)
and drives ``_invoke_claude_cli`` (the retry wrapper) through the full branch
matrix:

  Case 1: first attempt returns JSON → no retries
  Case 2: first non-JSON + second JSON → retry_count = 1 (recovered)
  Case 3: first+second non-JSON + third JSON → retry_count = 2 (recovered)
  Case 4: all 3 attempts non-JSON → RuntimeError raised
  Case 5: nudge prompt contains the exact Korean mandate string

The retry wrapper does not expose a ``retry_count`` return channel — it
returns the successful stdout string. Here ``retry_count`` is implied
by how many times ``_invoke_claude_cli_once`` was called (mock call_count).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.orchestrator.invokers import (
    _JSON_NUDGE_PROMPT_KO,
    _MAX_NUDGE_ATTEMPTS,
    _invoke_claude_cli,
)


_VALID_JSON_REPLY = '{"gate":"TREND","keywords":[]}'
_NON_JSON_REPLY = "대표님, 어떤 결정 정보를 필요합니다..."


def _args(user_prompt: str = "input"):
    """Fixed invocation args used by every case."""
    return dict(
        system_prompt="SYS",
        user_prompt=user_prompt,
        json_schema='{"type":"object"}',
        cli_path="/fake/claude",
        timeout_s=30,
    )


def test_retry_case1_first_attempt_json_no_retry():
    """Case 1: 1차 호출이 JSON 반환 → retry 없음 (call_count == 1)."""
    with patch(
        "scripts.orchestrator.invokers._invoke_claude_cli_once",
        return_value=_VALID_JSON_REPLY,
    ) as once:
        out = _invoke_claude_cli(**_args())
        assert out == _VALID_JSON_REPLY
        assert once.call_count == 1, "1차 성공 시 재시도 없어야 함"
        # 1차 호출은 nudge 없는 원본 프롬프트
        first_prompt = once.call_args_list[0].kwargs["user_prompt"]
        assert _JSON_NUDGE_PROMPT_KO not in first_prompt


def test_retry_case2_first_fails_second_succeeds():
    """Case 2: 1차 non-JSON + 2차 JSON → retry_count = 1 (once.call_count == 2)."""
    with patch(
        "scripts.orchestrator.invokers._invoke_claude_cli_once",
        side_effect=[_NON_JSON_REPLY, _VALID_JSON_REPLY],
    ) as once:
        out = _invoke_claude_cli(**_args())
        assert out == _VALID_JSON_REPLY
        assert once.call_count == 2
        # 2차 호출은 nudge 가 프롬프트 앞에 붙어야 함
        second_prompt = once.call_args_list[1].kwargs["user_prompt"]
        assert second_prompt.startswith(_JSON_NUDGE_PROMPT_KO), (
            f"2차 프롬프트에 nudge prefix 누락: head={second_prompt[:80]!r}"
        )


def test_retry_case3_first_second_fail_third_succeeds():
    """Case 3: 1+2차 non-JSON + 3차 JSON → retry_count = 2 (once.call_count == 3)."""
    with patch(
        "scripts.orchestrator.invokers._invoke_claude_cli_once",
        side_effect=[_NON_JSON_REPLY, _NON_JSON_REPLY, _VALID_JSON_REPLY],
    ) as once:
        out = _invoke_claude_cli(**_args())
        assert out == _VALID_JSON_REPLY
        assert once.call_count == 3
        # 2+3차 모두 nudge prefix
        for idx in (1, 2):
            prompt = once.call_args_list[idx].kwargs["user_prompt"]
            assert prompt.startswith(_JSON_NUDGE_PROMPT_KO), (
                f"{idx+1}차 프롬프트에 nudge prefix 누락"
            )


def test_retry_case4_all_three_fail_raises_runtime_error():
    """Case 4: 3회 모두 non-JSON → RuntimeError (cap 소진)."""
    with patch(
        "scripts.orchestrator.invokers._invoke_claude_cli_once",
        side_effect=[_NON_JSON_REPLY, _NON_JSON_REPLY, _NON_JSON_REPLY],
    ) as once:
        with pytest.raises(RuntimeError) as exc:
            _invoke_claude_cli(**_args(), agent_label="trend-collector")
        msg = str(exc.value)
        assert "trend-collector" in msg
        assert "JSON 미준수" in msg
        assert f"{_MAX_NUDGE_ATTEMPTS}회" in msg
        assert "대표님" in msg
        assert once.call_count == _MAX_NUDGE_ATTEMPTS


def test_retry_case5_nudge_prompt_exact_korean():
    """Case 5: nudge 프롬프트 정확한 문구 포함 (Task 3 spec 인용)."""
    # 정확 문구 assertion (문구가 달라지면 이 테스트가 실패)
    assert _JSON_NUDGE_PROMPT_KO == (
        "직전 응답은 JSON이 아니었습니다. JSON 객체만 출력하세요. "
        "설명/질문 금지."
    )
    # End-to-end: 2차 시도 시 이 문구가 nudge prefix 로 삽입되는지 확인
    with patch(
        "scripts.orchestrator.invokers._invoke_claude_cli_once",
        side_effect=[_NON_JSON_REPLY, _VALID_JSON_REPLY],
    ) as once:
        _invoke_claude_cli(**_args(user_prompt="ORIGINAL_INPUT"))
        second_prompt = once.call_args_list[1].kwargs["user_prompt"]
        # nudge 가 ORIGINAL_INPUT 앞에 위치
        assert second_prompt.startswith(_JSON_NUDGE_PROMPT_KO)
        assert "ORIGINAL_INPUT" in second_prompt
        # 구조: "{nudge}\n\n{original}"
        assert f"{_JSON_NUDGE_PROMPT_KO}\n\nORIGINAL_INPUT" == second_prompt
