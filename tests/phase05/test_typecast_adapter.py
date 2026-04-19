"""Mock tests for :class:`TypecastAdapter`.

Covers:

* API-key resolution (explicit, env, missing => ValueError).
* Text-shaping helpers preserved from harvested tts_generate.py:
  ``_chunk_text_for_typecast`` and ``_inject_punctuation_breaks``.
* ``generate()`` composes :class:`AudioSegment` output with monotonic
  offsets, one segment per scene.
* Harvested fallback paths (Fish Audio / VOICEVOX / EdgeTTS) are NOT
  present in the rewritten module (RESEARCH §8 line 786).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.orchestrator.api.typecast import TypecastAdapter
from scripts.orchestrator.voice_first_timeline import AudioSegment


# ---------------------------------------------------------------------------
# API-key resolution
# ---------------------------------------------------------------------------


def test_typecast_init_requires_api_key(monkeypatch):
    monkeypatch.delenv("TYPECAST_API_KEY", raising=False)
    with pytest.raises(ValueError):
        TypecastAdapter(api_key=None)


def test_typecast_init_accepts_explicit_key():
    a = TypecastAdapter(api_key="fake")
    assert a is not None


def test_typecast_init_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("TYPECAST_API_KEY", "env-key")
    a = TypecastAdapter(api_key=None)
    assert a is not None


# ---------------------------------------------------------------------------
# Text-shaping helpers
# ---------------------------------------------------------------------------


def test_chunk_text_short_returns_single_chunk():
    a = TypecastAdapter(api_key="fake")
    chunks = a._chunk_text_for_typecast("짧은 문장.", max_chars=100)
    assert chunks == ["짧은 문장."]


def test_chunk_text_respects_max_chars():
    """Long input is split and no chunk exceeds max_chars."""

    a = TypecastAdapter(api_key="fake")
    # Build a long text with sentence boundaries so the regex splitter
    # has somewhere to cut.
    long_text = "안녕하세요. " * 50  # ~350 chars
    chunks = a._chunk_text_for_typecast(long_text, max_chars=100)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 100


def test_chunk_text_preserves_content():
    """Joining the chunks recovers the input (modulo whitespace trimming)."""

    a = TypecastAdapter(api_key="fake")
    text = "첫번째. 두번째. 세번째. 네번째."
    chunks = a._chunk_text_for_typecast(text, max_chars=20)
    rejoined = "".join(chunks).replace(" ", "")
    assert rejoined.replace(".", "") == text.replace(" ", "").replace(".", "")


def test_inject_punctuation_breaks_adds_ssml_after_terminal():
    a = TypecastAdapter(api_key="fake")
    result = a._inject_punctuation_breaks("문장 하나. 문장 둘.")
    assert "<break" in result
    assert 'time="0.35s"' in result


def test_inject_punctuation_breaks_adds_ssml_after_comma():
    a = TypecastAdapter(api_key="fake")
    result = a._inject_punctuation_breaks("앞 절, 뒤 절입니다")
    assert "<break" in result
    assert 'time="0.2s"' in result


def test_inject_punctuation_breaks_is_idempotent():
    a = TypecastAdapter(api_key="fake")
    once = a._inject_punctuation_breaks("안녕. 반갑습니다.")
    twice = a._inject_punctuation_breaks(once)
    # Second pass should not double-inject because the punctuation is
    # followed by the <break/> tag directly (no whitespace).
    assert once == twice


def test_inject_punctuation_breaks_does_not_break_decimals():
    """Decimal '3.14' has no space after the dot, so no injection."""

    a = TypecastAdapter(api_key="fake")
    result = a._inject_punctuation_breaks("파이는 3.14입니다.")
    # The decimal dot should be untouched; only the final sentence-end
    # is followed by whitespace OR end-of-string — final is end-of-string
    # so no whitespace => no injection there either.
    assert "3.14" in result
    # No break injected next to "3.14" specifically.
    assert "3.14<break" not in result


# ---------------------------------------------------------------------------
# AUDIO-01 removed tiers must be physically absent
# ---------------------------------------------------------------------------
#
# The harvested tts_generate.py exposed a 4-tier fallback (Typecast ->
# Fish Audio -> ElevenLabs -> EdgeTTS) plus a VOICEVOX path for Japanese.
# RESEARCH §8 line 786 drops everything except Typecast and ElevenLabs.
# These tests verify the removed tiers have no IMPORT / CALL presence —
# mere mentions in the module docstring (historical explanation) are
# allowed and expected.


def _non_docstring_source(module) -> str:
    """Return the module source with its leading module docstring stripped.

    Implementation detail: the harvest-drop tests assert the removed
    providers have no IMPORT or CALL site in the module. The module's
    own docstring naturally mentions the dropped providers by name as
    historical context; that is not a drift signal.
    """

    import ast
    import textwrap
    from pathlib import Path as _Path

    source = _Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        # Strip module docstring, keep everything after the closing quote.
        end_line = tree.body[0].end_lineno or 0
        remaining = "\n".join(source.splitlines()[end_line:])
        return textwrap.dedent(remaining)
    return source


def test_no_fish_audio_import_in_typecast_module():
    """RESEARCH §8 line 786: Fish Audio tier was dropped."""

    import scripts.orchestrator.api.typecast as mod

    body = _non_docstring_source(mod).lower()
    assert "fish_audio" not in body
    assert "fish-audio" not in body


def test_no_voicevox_import_in_typecast_module():
    import scripts.orchestrator.api.typecast as mod

    body = _non_docstring_source(mod).lower()
    assert "voicevox" not in body


def test_no_edgetts_import_in_typecast_module():
    import scripts.orchestrator.api.typecast as mod

    body = _non_docstring_source(mod).lower()
    assert "edge_tts" not in body
    assert "edgetts" not in body


# ---------------------------------------------------------------------------
# generate() — mocked SDK seam
# ---------------------------------------------------------------------------


def test_generate_returns_audio_segment_list(tmp_path):
    adapter = TypecastAdapter(api_key="fake", output_dir=tmp_path)

    def _fake_invoke(*, text_chunks, voice_id, emotion_style, scene_id, output_path):
        output_path.write_bytes(b"fake mp3 bytes")
        return output_path

    with patch.object(
        TypecastAdapter, "_invoke_typecast_api", side_effect=_fake_invoke
    ), patch.object(TypecastAdapter, "_get_audio_duration", return_value=5.0):
        scenes = [
            {"scene_id": 0, "text": "안녕하세요"},
            {"scene_id": 1, "text": "반갑습니다"},
            {"scene_id": 2, "text": "잘 부탁드립니다"},
        ]
        result = adapter.generate(scenes)

    assert len(result) == 3
    assert all(isinstance(s, AudioSegment) for s in result)
    assert result[0].index == 0
    assert result[0].start == 0.0
    assert result[0].end == 5.0
    # Offsets accumulate: scene 1 starts after scene 0 (5s) + silence gap (0.3s)
    assert result[1].start == pytest.approx(5.3)


def test_generate_rejects_invalid_scene_id(tmp_path):
    """TypecastRequest validation: negative scene_id is rejected."""

    adapter = TypecastAdapter(api_key="fake", output_dir=tmp_path)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        adapter.generate([{"scene_id": -1, "text": "x"}])


def test_generate_output_paths_use_zero_padded_scene_id(tmp_path):
    adapter = TypecastAdapter(api_key="fake", output_dir=tmp_path)

    captured: list[Path] = []

    def _fake_invoke(*, text_chunks, voice_id, emotion_style, scene_id, output_path):
        captured.append(output_path)
        output_path.write_bytes(b"fake")
        return output_path

    with patch.object(
        TypecastAdapter, "_invoke_typecast_api", side_effect=_fake_invoke
    ), patch.object(TypecastAdapter, "_get_audio_duration", return_value=1.0):
        adapter.generate([{"scene_id": 7, "text": "x"}])

    assert captured[0].name == "scene_007.mp3"
