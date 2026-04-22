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


# --------------------------------------------------------------------------
# _pipeline_fake_env — autouse (Wave 2 addition for Plan 05 pipeline wiring)
#
# ShortsPipeline.__init__ constructs 5 existing adapters (Kling/Runway/
# Typecast/ElevenLabs/Shotstack) + 2 Wave 1 adapters (NanoBanana/KenBurns)
# which each raise ValueError when their env key is absent. Phase 5/7
# conftests set these to "fake" for the same reason; phase091 mirrors that
# pattern so the shared fake_agent_md_dir/mock_anthropic_client tests can
# also construct full pipelines when needed (Plan 05 test_pipeline_wiring.py).
# --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _pipeline_fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set adapter API keys to 'fake' so ShortsPipeline(...) can construct
    without real .env values during unit tests."""
    for var in (
        "KLING_API_KEY",
        "FAL_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",  # 2026-04-22 추가: GPTImage2Adapter Stage 2 primary
    ):
        monkeypatch.setenv(var, "fake")


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
    """DEPRECATED (2026-04-20 세션 #24): kept for back-compat only. invokers.py
    는 이제 Claude CLI subprocess 기반 (memory:
    project_claude_code_max_no_api_key). 신규 테스트는 ``mock_cli_runner``
    사용.

    MagicMock shaped like ``anthropic.Anthropic()`` — 과거 API 직접 호출
    시나리오 테스트용 (현재는 무의미하나 phase05/phase07 레거시 test 가
    참조할 가능성으로 유지)."""
    client = MagicMock()
    text_block = MagicMock()
    text_block.text = '"verdict": "PASS", "score": 0.9}'
    response = MagicMock()
    response.content = [text_block]
    client.messages.create.return_value = response
    return client


@pytest.fixture
def mock_cli_runner() -> MagicMock:
    """Return a MagicMock replacing ``_invoke_claude_cli`` signature.

    Callable with kwargs (system_prompt, user_prompt, json_schema, cli_path,
    timeout_s=...) returning stdout JSON string. Default return: valid
    ``{"verdict": "PASS", "score": 0.9}`` producer-shaped response.

    Supervisor tests override ``.return_value`` to
    ``'{"verdict": "PASS"}'`` (supervisor schema strict).
    """
    runner = MagicMock()
    runner.return_value = '{"verdict": "PASS", "score": 0.9}'
    return runner


@pytest.fixture
def mock_openai_client(fixture_png_bytes: bytes) -> MagicMock:
    """Return a MagicMock shaped like ``openai.OpenAI(api_key=...)``.

    Both ``images.generate`` and ``images.edit`` return a response whose
    ``.data[0].b64_json`` contains base64-encoded ``fixture_png_bytes``.
    Used by tests for ``scripts.orchestrator.api.gpt_image2.GPTImage2Adapter``
    (Stage 2 primary, 2026-04-22). Mirrors ``mock_genai_client`` design.
    """
    import base64

    client = MagicMock()
    image_obj = MagicMock()
    image_obj.b64_json = base64.b64encode(fixture_png_bytes).decode("ascii")
    response = MagicMock()
    response.data = [image_obj]
    client.images.generate.return_value = response
    client.images.edit.return_value = response
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
    "mock_anthropic_client",  # DEPRECATED: see fixture docstring
    "mock_cli_runner",
    "mock_genai_client",
    "mock_openai_client",
]
