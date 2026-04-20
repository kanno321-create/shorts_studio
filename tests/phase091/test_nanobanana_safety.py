"""RED stub for REQ-091-02 — Wave 1 Nano Banana safety fallback.

Wave 1 Plan 01 must implement retry-on-SAFETY/BLOCK pattern (shorts_naberal
_nanobanana_from_script_v3.py line-by-line reference).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_safety_fallback_on_block_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-091-02: first call raises SAFETY, second softer call succeeds."""
    import scripts.orchestrator.api.nanobanana as nb_mod
    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter

    part_ok = MagicMock()
    part_ok.inline_data.data = fixture_png_bytes
    part_ok.text = None
    candidate_ok = MagicMock()
    candidate_ok.content.parts = [part_ok]
    response_ok = MagicMock()
    response_ok.candidates = [candidate_ok]

    client = MagicMock()
    client.models.generate_content.side_effect = [
        Exception("SAFETY filter triggered"),
        response_ok,
    ]
    monkeypatch.setattr(nb_mod, "genai", MagicMock(Client=lambda api_key: client))

    adapter = NanoBananaAdapter(api_key="test-key", output_dir=tmp_path)
    out = adapter.generate_scene("risky prompt")
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")
    assert client.models.generate_content.call_count == 2


def test_non_safety_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """REQ-091-02: non-safety errors (e.g., network timeout) are re-raised, NOT swallowed."""
    import scripts.orchestrator.api.nanobanana as nb_mod
    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter

    client = MagicMock()
    client.models.generate_content.side_effect = Exception("network timeout")
    monkeypatch.setattr(nb_mod, "genai", MagicMock(Client=lambda api_key: client))

    adapter = NanoBananaAdapter(api_key="test-key", output_dir=tmp_path)
    with pytest.raises(Exception, match="network timeout"):
        adapter.generate_scene("normal prompt")
