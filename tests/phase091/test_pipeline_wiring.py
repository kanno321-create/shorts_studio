"""RED stub for REQ-091-01 — Wave 2 shorts_pipeline integration.

After Wave 2, `_default_producer_invoker` no longer raises NotImplementedError;
it is replaced by a live `ClaudeAgentProducerInvoker`. Constructor also gains
`nanobanana_adapter` and `ken_burns_adapter` parameter slots.
"""
from __future__ import annotations

import inspect
from pathlib import Path


def test_default_producer_invoker_no_longer_notimplementederror(tmp_path: Path) -> None:
    """REQ-091-01: ShortsPipeline.producer_invoker is a ClaudeAgentProducerInvoker callable."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline

    pipeline = ShortsPipeline(
        session_id="test-091",
        state_root=tmp_path,
    )
    assert pipeline.producer_invoker is not None
    assert callable(pipeline.producer_invoker)
    assert pipeline.producer_invoker.__class__.__name__ == "ClaudeAgentProducerInvoker"


def test_new_adapter_slots_exist() -> None:
    """REQ-091-01: ShortsPipeline.__init__ exposes nanobanana_adapter + ken_burns_adapter params."""
    from scripts.orchestrator.shorts_pipeline import ShortsPipeline

    sig = inspect.signature(ShortsPipeline.__init__)
    params = set(sig.parameters.keys())
    assert "nanobanana_adapter" in params, f"missing nanobanana_adapter; got {sorted(params)}"
    assert "ken_burns_adapter" in params, f"missing ken_burns_adapter; got {sorted(params)}"
