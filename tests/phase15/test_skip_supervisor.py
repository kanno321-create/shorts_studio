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

from scripts.orchestrator.gate_guard import Verdict
from scripts.orchestrator.gates import GateName
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
    """`_AutoPassSupervisorInvoker` 계약 검증 — gate_guard.Verdict (dataclass) 반환 호환."""

    def test_returns_verdict_dataclass_with_pass_for_any_gate(self):
        """모든 GateName 입력에 대해 gate_guard.Verdict(result='PASS') 반환.

        GateGuard.dispatch 가 asdict(verdict) 를 호출하므로 dataclass 이어야 함.
        """
        from dataclasses import asdict
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
            assert isinstance(result, Verdict), (
                f"gate={gate.name} 반환값이 gate_guard.Verdict 가 아님"
            )
            assert result.result == "PASS", (
                f"gate={gate.name} 에서 result!=PASS: {result.result}"
            )
            assert result.score == 100
            # asdict() 가 예외 없이 실행되어야 GateGuard.dispatch 와 호환
            d = asdict(result)
            assert d["result"] == "PASS"

    def test_accepts_bare_string_gate(self):
        """bare string gate 도 허용 (ClaudeAgentSupervisorInvoker 와 동일 duck-typing)."""
        invoker = _AutoPassSupervisorInvoker()
        result = invoker("SCRIPT", {"verdict": "PASS"})
        assert isinstance(result, Verdict)
        assert result.result == "PASS"

    def test_tracks_call_count(self):
        """호출 횟수 추적 — evidence 감사 trail 용."""
        invoker = _AutoPassSupervisorInvoker()
        assert invoker._calls == 0
        invoker(GateName.TREND, {})
        invoker(GateName.NICHE, {})
        invoker(GateName.RESEARCH_NLM, {})
        assert invoker._calls == 3

    def test_evidence_and_semantic_feedback_fields_present(self):
        """rubric-schema 필수 필드 (evidence, semantic_feedback) 존재 확인."""
        invoker = _AutoPassSupervisorInvoker()
        result = invoker(GateName.SCRIPT, {})
        assert result.evidence == []
        assert "auto-PASS" in result.semantic_feedback
        assert result.inspector_name == "auto-pass-supervisor-bypass"
