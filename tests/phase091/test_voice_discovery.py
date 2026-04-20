"""RED stub for REQ-091-06 — Wave 1 ElevenLabs voice discovery.

Frozen contract:
    discover_korean_default_voice(api_key: str | None = None) -> str
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def test_discover_importable() -> None:
    """REQ-091-06: discover_korean_default_voice is importable."""
    from scripts.orchestrator.voice_discovery import discover_korean_default_voice  # noqa: F401


def test_discover_prefers_korean_language(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-091-06: labels.language == 'ko' voice preferred over others."""
    import scripts.orchestrator.voice_discovery as vd

    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "voices": [
            {"voice_id": "en_voice_1", "labels": {"language": "en"}, "category": "premade"},
            {"voice_id": "ko_voice_1", "labels": {"language": "ko"}, "category": "premade"},
            {"voice_id": "ja_voice_1", "labels": {"language": "ja"}, "category": "premade"},
        ]
    }
    monkeypatch.setattr(vd.httpx, "get", lambda *args, **kwargs: response)

    result = vd.discover_korean_default_voice()
    assert result == "ko_voice_1"


def test_missing_key_raises_korean(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-091-06: missing ElevenLabs API key raises ValueError with Korean message."""
    from scripts.orchestrator.voice_discovery import discover_korean_default_voice

    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ElevenLabs API 키"):
        discover_korean_default_voice()
