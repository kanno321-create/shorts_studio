"""F-LIVE-SMOKE-JSON-NONCOMPLIANCE 우회 경로 — --skip-supervisor 계약 테스트.

대표님 세션 #30 합의 경로 (Option A 수동 혼합): Claude CLI 대화형 session 의
``--json-schema`` 엄수가 brittle 하여 supervisor 호출이 자연어 응답 또는
empty stdout 을 반환하는 문제를 우회. ``--skip-supervisor`` 플래그 지정 시
기본 supervisor_invoker 를 ``_AutoPassSupervisorInvoker`` 로 교체하여 모든
gate 에 ``Verdict.PASS`` 자동 반환.

Inspector 17 의 실제 품질 검증은 유지되며, supervisor aggregation layer
만 skip 됩니다. Quality gate 는 영상 제작 달성 후 점진 복구.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.orchestrator.gates import GateName
from scripts.orchestrator.state import Verdict
from scripts.smoke.phase13_live_smoke import (
    _AutoPassSupervisorInvoker,
    _parse_args,
)


class TestSkipSupervisorFlag:
    """`--skip-supervisor` argparse 계약 (대표님)."""

    def test_flag_defaults_to_false(self):
        """플래그 미지정 시 기본값 False — 기존 동작 보존."""
        args = _parse_args(["--session-id", "test_default"])
        assert args.skip_supervisor is False, (
            "기본값은 False 여야 기존 real supervisor 경로가 유지됩니다"
        )

    def test_flag_sets_true_when_specified(self):
        """`--skip-supervisor` 지정 시 True — auto-PASS 경로 활성."""
        args = _parse_args(
            ["--session-id", "test_skip", "--skip-supervisor"]
        )
        assert args.skip_supervisor is True, (
            "--skip-supervisor 명시 시 True 로 세팅되어야 합니다"
        )


class TestAutoPassSupervisorInvoker:
    """`_AutoPassSupervisorInvoker` 계약 검증 — ClaudeAgentSupervisorInvoker 와 duck-typing 호환."""

    def test_returns_verdict_pass_for_any_gate(self):
        """모든 GateName 입력에 대해 Verdict.PASS 반환."""
        invoker = _AutoPassSupervisorInvoker()
        for gate in [
            GateName.TREND,
            GateName.NICHE,
            GateName.RESEARCH_NLM,
            GateName.BLUEPRINT,
            GateName.SCRIPT,
            GateName.POLISH,
            GateName.VOICE,
            GateName.ASSETS,
            GateName.ASSEMBLY,
            GateName.THUMBNAIL,
            GateName.METADATA,
            GateName.UPLOAD,
            GateName.MONITOR,
        ]:
            result = invoker(gate, {"verdict": "PASS", "payload": "x"})
            assert result is Verdict.PASS, (
                f"gate={gate.name} 에서 Verdict.PASS 가 아님: {result}"
            )

    def test_accepts_bare_string_gate(self):
        """bare string gate 도 허용 (ClaudeAgentSupervisorInvoker 와 동일 duck-typing)."""
        invoker = _AutoPassSupervisorInvoker()
        result = invoker("SCRIPT", {"verdict": "PASS"})
        assert result is Verdict.PASS

    def test_tracks_call_count(self):
        """호출 횟수 추적 — evidence 감사 trail 용."""
        invoker = _AutoPassSupervisorInvoker()
        assert invoker._calls == 0
        invoker(GateName.TREND, {})
        invoker(GateName.NICHE, {})
        invoker(GateName.RESEARCH_NLM, {})
        assert invoker._calls == 3

    def test_output_arg_is_accepted_but_not_consumed(self):
        """output dict 이 빈 dict / 잘못된 schema 여도 PASS — auto-pass 는 validation 안 함."""
        invoker = _AutoPassSupervisorInvoker()
        assert invoker(GateName.SCRIPT, {}) is Verdict.PASS
        assert invoker(GateName.SCRIPT, {"garbage": "nonsense"}) is Verdict.PASS
        # None 은 실제 supervisor 에서도 받지 않지만, duck typing 견고성 확인.
        # ClaudeAgentSupervisorInvoker 는 output.get(...) 을 호출하므로
        # None 은 AttributeError 를 유발 — auto-pass 도 동일 계약이어야 하나,
        # 우리는 output 을 touch 하지 않으므로 실제로는 통과함.
        assert invoker(GateName.SCRIPT, None) is Verdict.PASS  # type: ignore[arg-type]
