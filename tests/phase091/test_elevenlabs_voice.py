"""RED stub for REQ-091-06 — Wave 1 ElevenLabsAdapter default voice refactor.

Wave 1 Plan 04 must:
- Add `default_voice_id` constructor parameter
- Replace `scene.get("voice_id", "detective_hao")` with discovery chain
- env var ELEVENLABS_DEFAULT_VOICE_ID as second fallback
"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_default_voice_id_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-091-06: ELEVENLABS_DEFAULT_VOICE_ID env var propagates to adapter default."""
    from scripts.orchestrator.api.elevenlabs import ElevenLabsAdapter

    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_DEFAULT_VOICE_ID", "env_voice")

    adapter = ElevenLabsAdapter(api_key="test-key")
    # Contract: adapter exposes ._default_voice_id (set via chain in Wave 1 Plan 04).
    assert getattr(adapter, "_default_voice_id", None) == "env_voice"


def test_detective_hao_no_longer_hardcoded() -> None:
    """REQ-091-06: string literal '"detective_hao"' must not appear as runtime default.

    Allows detective_hao inside comments/docstrings but forbids the pattern
    `scene.get("voice_id", "detective_hao")` which was the buggy default.
    """
    adapter_src = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "orchestrator"
        / "api"
        / "elevenlabs.py"
    )
    # Wave 0 state: file may or may not be Wave-1-patched — if current file still uses the
    # hardcoded fallback, this test asserts and stays RED until Wave 1 Plan 04 lands.
    if not adapter_src.exists():
        pytest.fail(f"{adapter_src} missing — cannot validate voice default")
    text = adapter_src.read_text(encoding="utf-8")
    assert 'scene.get("voice_id", "detective_hao")' not in text, (
        "detective_hao hardcoded default remains — Wave 1 Plan 04 pending"
    )
