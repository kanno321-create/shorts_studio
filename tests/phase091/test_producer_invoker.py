"""REQ-091-01: ClaudeAgentProducerInvoker via Claude CLI subprocess.

2026-04-20 세션 #24 architecture fix: ``anthropic`` SDK (usage-based billing)
경로를 제거하고 ``claude --print`` subprocess 로 교체. 대표님 Claude Code
Max 구독 활용 (memory: project_claude_code_max_no_api_key).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_producer_invoker_importable() -> None:
    """REQ-091-01: ClaudeAgentProducerInvoker importable."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker  # noqa: F401


def test_producer_invoker_returns_dict(
    mock_cli_runner: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: invoker call returns parsed dict (cli_runner stdout → json.loads)."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker

    inv = ClaudeAgentProducerInvoker(
        agent_dir_root=fake_agent_md_dir.parent,
        cli_path="/fake/claude",  # bypass shutil.which
        cli_runner=mock_cli_runner,
    )
    result = inv("fake-producer", "TREND", {"keyword": "수달"})
    assert isinstance(result, dict)
    assert result.get("verdict") == "PASS"
    # cli_runner must be called with system_prompt + user_prompt + JSON schema
    mock_cli_runner.assert_called_once()
    kwargs = mock_cli_runner.call_args.kwargs
    assert "system_prompt" in kwargs
    assert "user_prompt" in kwargs
    assert "json_schema" in kwargs
    assert kwargs["json_schema"] == '{"type":"object"}'


def test_producer_invoker_json_schema_enforced(
    mock_cli_runner: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: CLI receives producer --json-schema (structured output)."""
    from scripts.orchestrator.invokers import (
        ClaudeAgentProducerInvoker,
        _PRODUCER_JSON_SCHEMA,
    )

    mock_cli_runner.return_value = '{"k": "v"}'
    inv = ClaudeAgentProducerInvoker(
        agent_dir_root=fake_agent_md_dir.parent,
        cli_path="/fake/claude",
        cli_runner=mock_cli_runner,
    )
    result = inv("fake-producer", "TREND", {"keyword": "수달"})
    assert result == {"k": "v"}
    # schema kwarg equals the module constant
    assert mock_cli_runner.call_args.kwargs["json_schema"] == _PRODUCER_JSON_SCHEMA


def test_producer_invoker_missing_agent_dir_raises(tmp_path: Path) -> None:
    """REQ-091-01: FileNotFoundError with Korean message if AGENT.md missing."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker

    inv = ClaudeAgentProducerInvoker(
        agent_dir_root=tmp_path,
        cli_path="/fake/claude",
        cli_runner=MagicMock(),
    )
    with pytest.raises(FileNotFoundError, match="Agent 디렉토리 없음"):
        inv("nonexistent-producer", "TREND", {})
