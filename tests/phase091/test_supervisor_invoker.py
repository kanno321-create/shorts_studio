"""REQ-091-01: ClaudeAgentSupervisorInvoker via Claude CLI subprocess.

2026-04-20 세션 #24 architecture fix: Claude CLI `--json-schema` 로 Verdict
enum 강제 출력 (memory: project_claude_code_max_no_api_key).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_supervisor_invoker_importable() -> None:
    """REQ-091-01: ClaudeAgentSupervisorInvoker is importable."""
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker  # noqa: F401


def test_supervisor_invoker_returns_verdict(
    mock_cli_runner: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: supervisor returns Verdict.FAIL when CLI emits FAIL."""
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker
    from scripts.orchestrator.state import Verdict

    mock_cli_runner.return_value = '{"verdict": "FAIL", "reason": "drift"}'

    inv = ClaudeAgentSupervisorInvoker(
        agent_dir=fake_agent_md_dir,
        cli_path="/fake/claude",
        cli_runner=mock_cli_runner,
    )
    result = inv("TREND", {"output_dummy": True})
    assert result is Verdict.FAIL


def test_supervisor_invoker_json_schema_enforced(
    mock_cli_runner: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: supervisor CLI receives strict verdict enum schema."""
    from scripts.orchestrator.invokers import (
        ClaudeAgentSupervisorInvoker,
        _SUPERVISOR_JSON_SCHEMA,
    )
    from scripts.orchestrator.state import Verdict

    mock_cli_runner.return_value = '{"verdict": "PASS"}'
    inv = ClaudeAgentSupervisorInvoker(
        agent_dir=fake_agent_md_dir,
        cli_path="/fake/claude",
        cli_runner=mock_cli_runner,
    )
    result = inv("TREND", {"output_dummy": True})
    assert result is Verdict.PASS
    assert mock_cli_runner.call_args.kwargs["json_schema"] == _SUPERVISOR_JSON_SCHEMA


def test_supervisor_invoker_unknown_verdict_raises(
    mock_cli_runner: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: unknown verdict string raises RuntimeError('파싱 실패')."""
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker

    mock_cli_runner.return_value = '{"verdict": "UNKNOWN"}'
    inv = ClaudeAgentSupervisorInvoker(
        agent_dir=fake_agent_md_dir,
        cli_path="/fake/claude",
        cli_runner=mock_cli_runner,
    )
    with pytest.raises(RuntimeError, match="파싱 실패"):
        inv("TREND", {"output_dummy": True})
