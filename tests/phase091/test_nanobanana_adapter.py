"""RED stub for REQ-091-02 — Wave 1 NanoBananaAdapter target.

Frozen contract:
    NanoBananaAdapter(api_key, circuit_breaker, output_dir)
    .generate_scene(prompt, output_path, model) -> Path
    DEFAULT_MODEL = "nano-banana-pro-preview"
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_nanobanana_importable() -> None:
    """REQ-091-02: NanoBananaAdapter is importable from scripts.orchestrator.api.nanobanana."""
    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter  # noqa: F401


def test_generate_scene_writes_png(
    mock_genai_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-091-02: generate_scene writes a valid PNG to output_dir."""
    import scripts.orchestrator.api.nanobanana as nb_mod
    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter

    monkeypatch.setattr(nb_mod, "genai", MagicMock(Client=lambda api_key: mock_genai_client))
    adapter = NanoBananaAdapter(api_key="test-key", output_dir=tmp_path)
    out = adapter.generate_scene("hello")
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")


def test_missing_key_korean_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-091-02: missing GOOGLE_API_KEY raises ValueError with Korean message + 대표님 ref."""
    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY") as exc_info:
        NanoBananaAdapter()
    assert "대표님" in str(exc_info.value)


def test_default_model_constant() -> None:
    """REQ-091-02: DEFAULT_MODEL class attribute is 'nano-banana-pro-preview'."""
    from scripts.orchestrator.api.nanobanana import NanoBananaAdapter

    assert NanoBananaAdapter.DEFAULT_MODEL == "nano-banana-pro-preview"
