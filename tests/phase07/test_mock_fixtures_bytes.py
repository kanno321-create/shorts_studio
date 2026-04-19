"""D-2 + Don't Hand-Roll: fixtures are zero-byte placeholders, not real MP4/WAV content.

Per 07-01-PLAN.md task 7-01-01 acceptance and 07-RESEARCH.md §Don't Hand-Roll:
MagicMock adapters never invoke ``.read_bytes()`` on the returned placeholder paths,
so keeping these files at 0 bytes is both deterministic and the minimum disk
footprint — and avoids the pitfalls of hand-rolling MP4/WAV atom/header bytes.
"""
from __future__ import annotations

from pathlib import Path

import pytest


_FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "name",
    [
        "mock_kling.mp4",
        "mock_runway.mp4",
        "mock_typecast.wav",
        "mock_elevenlabs.wav",
        "mock_shotstack.mp4",
        "still_image.jpg",
    ],
)
def test_fixture_is_zero_byte_placeholder(name: str):
    """Per RESEARCH Don't Hand-Roll: MagicMock adapters never read_bytes().

    Zero-byte is deterministic + minimal disk footprint + no MP4/WAV header complexity.
    """
    p = _FIXTURES / name
    assert p.exists()
    assert p.stat().st_size == 0, (
        f"{name} is {p.stat().st_size} bytes; Phase 7 expects 0-byte placeholders "
        f"(Don't Hand-Roll row; Phase 5 precedent)"
    )
