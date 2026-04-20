"""RED stub for REQ-091-01 — Wave 2 ClaudeAgentProducerInvoker target.

Wave 2 Plan 05 must GREEN these by providing
`scripts.orchestrator.invokers.ClaudeAgentProducerInvoker` per the frozen contract
in 09.1-00-foundation-PLAN.md <interfaces>.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_producer_invoker_importable() -> None:
    """REQ-091-01: ClaudeAgentProducerInvoker is importable from scripts.orchestrator.invokers."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker  # noqa: F401


def test_producer_invoker_returns_dict(
    mock_anthropic_client: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: invoker call returns a parsed dict with verdict=PASS (mock prefill tail)."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker

    inv = ClaudeAgentProducerInvoker(
        agent_dir_root=fake_agent_md_dir.parent,
        client=mock_anthropic_client,
    )
    result = inv("fake-producer", "TREND", {"keyword": "수달"})
    assert isinstance(result, dict)
    assert result.get("verdict") == "PASS"


def test_producer_invoker_json_prefill_restoration(
    mock_anthropic_client: MagicMock, fake_agent_md_dir: Path
) -> None:
    """REQ-091-01: prefill `{` reassembled before json.loads. Mock returns tail '"k":"v"}'."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker

    text_block = MagicMock()
    text_block.text = '"k": "v"}'
    response = MagicMock()
    response.content = [text_block]
    mock_anthropic_client.messages.create.return_value = response

    inv = ClaudeAgentProducerInvoker(
        agent_dir_root=fake_agent_md_dir.parent,
        client=mock_anthropic_client,
    )
    result = inv("fake-producer", "TREND", {"keyword": "수달"})
    assert result == {"k": "v"}


def test_producer_invoker_missing_agent_dir_raises(tmp_path: Path) -> None:
    """REQ-091-01: FileNotFoundError with Korean message if AGENT.md missing."""
    from scripts.orchestrator.invokers import ClaudeAgentProducerInvoker

    inv = ClaudeAgentProducerInvoker(agent_dir_root=tmp_path, client=MagicMock())
    with pytest.raises(FileNotFoundError, match="Agent 디렉토리 없음"):
        inv("nonexistent-producer", "TREND", {})
