"""RED stub for REQ-091-01 — Wave 2 ClaudeAgentSupervisorInvoker target.

Frozen contract: `__call__(gate: GateName, output: dict) -> Verdict`.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_supervisor_invoker_importable() -> None:
    """REQ-091-01: ClaudeAgentSupervisorInvoker is importable."""
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker  # noqa: F401


def test_supervisor_invoker_returns_verdict(
    mock_anthropic_client: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: supervisor returns Verdict.FAIL when mock emits FAIL tail."""
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker
    from scripts.orchestrator.state import Verdict

    text_block = MagicMock()
    text_block.text = '"verdict": "FAIL", "reason": "drift"}'
    response = MagicMock()
    response.content = [text_block]
    mock_anthropic_client.messages.create.return_value = response

    inv = ClaudeAgentSupervisorInvoker(
        agent_dir=fake_agent_md_dir,
        client=mock_anthropic_client,
    )
    result = inv("TREND", {"output_dummy": True})
    assert result is Verdict.FAIL


def test_supervisor_invoker_unknown_verdict_raises(
    mock_anthropic_client: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: unknown verdict string raises RuntimeError('파싱 실패')."""
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker

    text_block = MagicMock()
    text_block.text = '"verdict": "UNKNOWN"}'
    response = MagicMock()
    response.content = [text_block]
    mock_anthropic_client.messages.create.return_value = response

    inv = ClaudeAgentSupervisorInvoker(
        agent_dir=fake_agent_md_dir,
        client=mock_anthropic_client,
    )
    with pytest.raises(RuntimeError, match="파싱 실패"):
        inv("TREND", {"output_dummy": True})
