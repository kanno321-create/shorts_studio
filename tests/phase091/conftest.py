"""Phase 9.1 shared pytest fixtures.

Exposes 5 fixtures consumed by Wave 1~3 test modules:
    tmp_registry_path      — isolated assets/characters/registry.json path
    fake_agent_md_dir      — synthesised .claude/agents/producers/<name>/AGENT.md
    fixture_png_bytes      — 512-byte valid PNG (1x1 pixel, stdlib struct)
    mock_anthropic_client  — MagicMock shaped like anthropic.Anthropic
    mock_genai_client      — MagicMock shaped like google.genai.Client

Design: fixtures are function-scoped for test isolation. fixture_png_bytes is
session-scoped (immutable) to avoid repeated PNG encoding.
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# UTF-8 safeguard for Windows cp949 per Phase 6/9 precedent.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# tests/phase091/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def tmp_registry_path(tmp_path: Path) -> Path:
    """Return an isolated registry.json path under tmp_path/assets/characters/."""
    d = tmp_path / "assets" / "characters"
    d.mkdir(parents=True, exist_ok=True)
    return d / "registry.json"


@pytest.fixture
def fake_agent_md_dir(tmp_path: Path) -> Path:
    """Synthesise `.claude/agents/producers/fake-producer/AGENT.md` with YAML frontmatter."""
    d = tmp_path / ".claude" / "agents" / "producers" / "fake-producer"
    d.mkdir(parents=True, exist_ok=True)
    (d / "AGENT.md").write_text(
        "---\n"
        "name: fake-producer\n"
        "description: 테스트용 더미 프로듀서 — 대표님 확인 불필요\n"
        "version: 1.0\n"
        "role: producer\n"
        "category: test\n"
        "maxTurns: 3\n"
        "---\n\n"
        "# fake-producer\n\n"
        "Test body — Claude Agent SDK system prompt target.\n",
        encoding="utf-8",
    )
    return d


@pytest.fixture(scope="session")
def fixture_png_bytes() -> bytes:
    """Return a minimal 1x1 opaque red PNG using only stdlib (struct+zlib)."""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(ctype: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + ctype
            + data
            + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        )

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\x00\x00"  # filter byte + RGB red pixel
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Return a MagicMock shaped like `anthropic.Anthropic()` with a canned
    `messages.create` returning a TextBlock-like object whose `.text` is
    `'"verdict": "PASS", "score": 0.9}'` (JSON tail after prefill `{`)."""
    client = MagicMock()
    text_block = MagicMock()
    text_block.text = '"verdict": "PASS", "score": 0.9}'
    response = MagicMock()
    response.content = [text_block]
    client.messages.create.return_value = response
    return client


@pytest.fixture
def mock_genai_client(fixture_png_bytes: bytes) -> MagicMock:
    """Return a MagicMock shaped like `google.genai.Client(api_key=...)`.
    `models.generate_content` returns a response whose candidates[0].content.parts
    has one `inline_data.data` = `fixture_png_bytes`."""
    client = MagicMock()
    part = MagicMock()
    part.inline_data.data = fixture_png_bytes
    part.text = None
    candidate = MagicMock()
    candidate.content.parts = [part]
    response = MagicMock()
    response.candidates = [candidate]
    client.models.generate_content.return_value = response
    return client


__all__ = [
    "tmp_registry_path",
    "fake_agent_md_dir",
    "fixture_png_bytes",
    "mock_anthropic_client",
    "mock_genai_client",
]
