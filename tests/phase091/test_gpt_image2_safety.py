"""REQ-IMG2-01 — GPTImage2Adapter safety fallback (mirror of NB pattern).

Two-call SAFETY pattern: first call raises with SAFETY/BLOCK/PROHIBITED/
CONTENT_POLICY in message → adapter softens prompt → second call succeeds.
Non-safety errors propagate unchanged (no silent-except — CLAUDE.md 금기 #3).
"""
from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _make_response(fixture_png_bytes: bytes) -> MagicMock:
    image_obj = MagicMock()
    image_obj.b64_json = base64.b64encode(fixture_png_bytes).decode("ascii")
    response = MagicMock()
    response.data = [image_obj]
    return response


def test_safety_fallback_on_block_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-IMG2-01: first call raises SAFETY, softened second call succeeds."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    response_ok = _make_response(fixture_png_bytes)
    client = MagicMock()
    client.images.generate.side_effect = [
        Exception("CONTENT_POLICY violation: blood detected"),
        response_ok,
    ]
    monkeypatch.setattr(gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: client))

    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    out = adapter.generate_scene("scene with blood")
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")
    assert client.images.generate.call_count == 2

    # second call must use softened prompt prefix
    second_prompt = client.images.generate.call_args_list[1].kwargs["prompt"]
    assert "Family-friendly" in second_prompt or "SFW" in second_prompt


def test_non_safety_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """REQ-IMG2-01: non-safety errors (e.g., network timeout) re-raise, NOT swallowed."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    client = MagicMock()
    client.images.generate.side_effect = Exception("network timeout")
    monkeypatch.setattr(gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: client))

    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    with pytest.raises(Exception, match="network timeout"):
        adapter.generate_scene("normal prompt")


def test_edit_safety_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-IMG2-01: edit_scene also retries on SAFETY with softened prompt."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    ref = tmp_path / "reference.png"
    ref.write_bytes(fixture_png_bytes)

    response_ok = _make_response(fixture_png_bytes)
    client = MagicMock()
    client.images.edit.side_effect = [
        Exception("SAFETY filter: violence"),
        response_ok,
    ]
    monkeypatch.setattr(gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: client))

    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    out = adapter.edit_scene("violent action scene", reference_image=ref)
    assert out.exists()
    assert client.images.edit.call_count == 2
