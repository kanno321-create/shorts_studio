"""REQ-IMG2-01 — Stage 2 primary GPTImage2Adapter (2026-04-22 확정).

Frozen contract:
    GPTImage2Adapter(api_key, circuit_breaker, output_dir)
    .generate_scene(prompt, output_path, model, quality) -> Path  (NB drop-in compatible)
    .edit_scene(prompt, reference_image, output_path, model, quality) -> Path
    DEFAULT_MODEL   = "gpt-image-2"
    DEFAULT_QUALITY = "medium"
    DEFAULT_SIZE    = "1024x1024"

Decision rationale: ``project_image_stack_gpt_image2`` memory.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_gpt_image2_importable() -> None:
    """REQ-IMG2-01: GPTImage2Adapter is importable from scripts.orchestrator.api.gpt_image2."""
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter  # noqa: F401


def test_default_constants() -> None:
    """REQ-IMG2-01: DEFAULT_MODEL/QUALITY/SIZE class attributes are stable."""
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    assert GPTImage2Adapter.DEFAULT_MODEL == "gpt-image-2"
    assert GPTImage2Adapter.DEFAULT_QUALITY == "medium"
    assert GPTImage2Adapter.DEFAULT_SIZE == "1024x1024"


def test_generate_scene_writes_png(
    mock_openai_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-IMG2-01: generate_scene writes a valid PNG to output_dir (text-to-image)."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    monkeypatch.setattr(
        gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: mock_openai_client)
    )
    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    out = adapter.generate_scene("a detective in noir alley")
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")
    mock_openai_client.images.generate.assert_called_once()


def test_edit_scene_writes_png_with_reference(
    mock_openai_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-IMG2-01: edit_scene reads reference and persists generated PNG."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    ref = tmp_path / "reference.png"
    ref.write_bytes(fixture_png_bytes)

    monkeypatch.setattr(
        gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: mock_openai_client)
    )
    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    out = adapter.edit_scene(
        "the same detective walking through rain", reference_image=ref
    )
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG")
    mock_openai_client.images.edit.assert_called_once()


def test_edit_scene_missing_reference_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-IMG2-01: missing reference image raises FileNotFoundError with Korean message."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    monkeypatch.setattr(gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: MagicMock()))
    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="reference_image") as exc_info:
        adapter.edit_scene("prompt", reference_image=tmp_path / "missing.png")
    assert "대표님" in str(exc_info.value)


def test_missing_key_korean_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-IMG2-01: missing OPENAI_API_KEY raises ValueError with Korean message + 대표님 ref."""
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY") as exc_info:
        GPTImage2Adapter()
    assert "대표님" in str(exc_info.value)


def test_quality_parameter_passed_through(
    mock_openai_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-IMG2-01: quality kwarg ('high'/'medium'/'low') is forwarded to images.generate."""
    import scripts.orchestrator.api.gpt_image2 as gpt_mod
    from scripts.orchestrator.api.gpt_image2 import GPTImage2Adapter

    monkeypatch.setattr(
        gpt_mod, "OpenAI", MagicMock(side_effect=lambda api_key: mock_openai_client)
    )
    adapter = GPTImage2Adapter(api_key="test-key", output_dir=tmp_path)
    adapter.generate_scene("test", quality="high")
    call_kwargs = mock_openai_client.images.generate.call_args.kwargs
    assert call_kwargs["quality"] == "high"
    assert call_kwargs["model"] == "gpt-image-2"
    assert call_kwargs["size"] == "1024x1024"
