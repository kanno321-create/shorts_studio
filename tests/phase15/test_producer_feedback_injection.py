"""UFL-01 Producer invoker prior_user_feedback injection.

ClaudeAgentProducerInvoker.__init__ 실제 signature:
    (agent_dir_root, circuit_breaker=None, cli_path=None, cli_runner=None)

__call__ 는 agent_dir.exists() 체크 → tmp_path 하위 stub AGENT.md 사전 생성 필요.
cli_runner signature (system_prompt, user_prompt, json_schema, cli_path).

대표님 재작업 피드백이 producer 의 user_payload JSON 에 포함되어 scripter /
script-polisher 등 하류 producer 에 전달되는지 검증합니다.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker


def _make_scripter_stub(tmp_path: Path) -> Path:
    """agent_dir.exists() 통과용 stub scripter/AGENT.md 생성.

    대표님 Phase 15 test — ClaudeAgentProducerInvoker 가 ``agent_dir_root /
    agent_name`` 을 확인하므로 tmp_path/scripter/AGENT.md 를 사전 배치.
    """
    scripter_dir = tmp_path / "scripter"
    scripter_dir.mkdir(parents=True, exist_ok=True)
    (scripter_dir / "AGENT.md").write_text(
        "stub body — 대표님 Phase 15 UFL-01 feedback injection test",
        encoding="utf-8",
    )
    return tmp_path


class TestFeedbackInjection:
    """UFL-01 producer invoker prior_user_feedback 주입 계약 (대표님)."""

    def test_feedback_injected_into_user_payload(self, tmp_path: Path):
        """inputs['prior_user_feedback'] 이 user_prompt JSON 에 주입되어야 함."""
        agent_root = _make_scripter_stub(tmp_path)
        captured: dict = {}

        def fake_cli_runner(system_prompt, user_prompt, json_schema, cli_path):
            captured["user_prompt"] = user_prompt
            return '{"gate": "SCRIPT", "verdict": "PASS", "script": "..."}'

        invoker = ClaudeAgentProducerInvoker(
            agent_dir_root=agent_root,
            cli_runner=fake_cli_runner,
        )
        result = invoker(
            "scripter",
            "SCRIPT",
            {
                "topic": "test",
                "prior_user_feedback": "hook 이 약합니다 (대표님)",
            },
        )
        payload = json.loads(captured["user_prompt"])
        assert "prior_user_feedback" in captured["user_prompt"], (
            "대표님 feedback 이 user_prompt 에 포함되지 않았습니다"
        )
        assert "hook 이 약합니다 (대표님)" in captured["user_prompt"]
        assert payload.get("prior_user_feedback") == "hook 이 약합니다 (대표님)"
        assert result["verdict"] == "PASS"

    def test_feedback_absent_when_not_provided(self, tmp_path: Path):
        """inputs 에 prior_user_feedback 키가 없으면 user_prompt 에도 부재."""
        agent_root = _make_scripter_stub(tmp_path)
        captured: dict = {}

        def fake_cli_runner(system_prompt, user_prompt, json_schema, cli_path):
            captured["user_prompt"] = user_prompt
            return '{"gate": "SCRIPT", "verdict": "PASS"}'

        invoker = ClaudeAgentProducerInvoker(
            agent_dir_root=agent_root,
            cli_runner=fake_cli_runner,
        )
        invoker("scripter", "SCRIPT", {"topic": "test"})
        payload = json.loads(captured["user_prompt"])
        assert "prior_user_feedback" not in payload, (
            "대표님 feedback 미지정 시 user_payload 에 key 가 없어야 합니다"
        )

    def test_feedback_none_treated_as_absent(self, tmp_path: Path):
        """inputs['prior_user_feedback'] 이 None 이면 skip (빈 값 주입 금지)."""
        agent_root = _make_scripter_stub(tmp_path)
        captured: dict = {}

        def fake_cli_runner(system_prompt, user_prompt, json_schema, cli_path):
            captured["user_prompt"] = user_prompt
            return '{"ok": true}'

        invoker = ClaudeAgentProducerInvoker(
            agent_dir_root=agent_root,
            cli_runner=fake_cli_runner,
        )
        invoker(
            "scripter",
            "SCRIPT",
            {"topic": "t", "prior_user_feedback": None},
        )
        payload = json.loads(captured["user_prompt"])
        assert "prior_user_feedback" not in payload, (
            "대표님, None 은 feedback 미지정과 동일하게 처리되어야 합니다"
        )
