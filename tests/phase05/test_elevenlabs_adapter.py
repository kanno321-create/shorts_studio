"""Mock tests for :class:`ElevenLabsAdapter` and the preserved
:func:`_chars_to_words` word-alignment helper.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.orchestrator.api.elevenlabs import ElevenLabsAdapter, _chars_to_words
from scripts.orchestrator.voice_first_timeline import AudioSegment


# ---------------------------------------------------------------------------
# _chars_to_words — preserved verbatim from harvested elevenlabs_alignment.py
# ---------------------------------------------------------------------------


def test_chars_to_words_basic_english():
    chars = list("hi there")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    ends = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    words = _chars_to_words(chars, starts, ends)
    assert len(words) == 2
    assert words[0]["word"] == "hi"
    assert words[1]["word"] == "there"
    assert words[0]["start"] == 0.0
    assert words[1]["start"] == 0.3


def test_chars_to_words_korean():
    chars = list("탐정님 안녕")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    ends = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    words = _chars_to_words(chars, starts, ends)
    assert len(words) == 2
    assert words[0]["word"] == "탐정님"
    assert words[1]["word"] == "안녕"


def test_chars_to_words_empty_input():
    assert _chars_to_words([], [], []) == []


def test_chars_to_words_single_word_no_whitespace():
    chars = list("hello")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4]
    ends = [0.1, 0.2, 0.3, 0.4, 0.5]
    words = _chars_to_words(chars, starts, ends)
    assert len(words) == 1
    assert words[0]["word"] == "hello"
    assert words[0]["start"] == 0.0
    assert words[0]["end"] == 0.5


def test_chars_to_words_multiple_spaces_skipped():
    chars = list("a  b")  # double space
    starts = [0.0, 0.1, 0.2, 0.3]
    ends = [0.1, 0.2, 0.3, 0.4]
    words = _chars_to_words(chars, starts, ends)
    assert [w["word"] for w in words] == ["a", "b"]


# ---------------------------------------------------------------------------
# API-key resolution
# ---------------------------------------------------------------------------


def test_elevenlabs_init_requires_key(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ElevenLabsAdapter(api_key=None)


def test_elevenlabs_init_with_explicit_key():
    assert ElevenLabsAdapter(api_key="fake") is not None


def test_elevenlabs_init_with_primary_env(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "env-primary")
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    a = ElevenLabsAdapter(api_key=None)
    assert a is not None


def test_elevenlabs_init_with_alias_env(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("ELEVEN_API_KEY", "env-alias")
    a = ElevenLabsAdapter(api_key=None)
    assert a is not None


# ---------------------------------------------------------------------------
# generate() and generate_with_timestamps() — mocked SDK seams
# ---------------------------------------------------------------------------


def test_generate_returns_audio_segment_list(tmp_path):
    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)

    with patch.object(
        ElevenLabsAdapter, "_invoke_tts", return_value=b"fake mp3"
    ), patch.object(ElevenLabsAdapter, "_get_audio_duration", return_value=3.0):
        scenes = [
            {"scene_id": 0, "text": "안녕하세요"},
            {"scene_id": 1, "text": "반갑습니다"},
        ]
        result = adapter.generate(scenes)

    assert len(result) == 2
    assert all(isinstance(s, AudioSegment) for s in result)
    assert result[0].duration == 3.0
    assert result[1].start == pytest.approx(3.3)  # 3.0 + 0.3 silence gap


def test_generate_rejects_empty_text(tmp_path):
    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)
    with pytest.raises(ValueError):
        adapter.generate([{"scene_id": 0, "text": ""}])


def test_generate_with_timestamps_populates_words_by_scene(tmp_path):
    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)

    fake_alignment = {
        "characters": list("hi there"),
        "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    }

    with patch.object(
        ElevenLabsAdapter,
        "_invoke_tts_with_timestamps",
        return_value=(b"fake mp3", fake_alignment),
    ), patch.object(ElevenLabsAdapter, "_get_audio_duration", return_value=0.8):
        result = adapter.generate_with_timestamps(
            [{"scene_id": 5, "text": "hi there"}]
        )

    assert len(result) == 1
    assert result[0].index == 5
    assert 5 in adapter.words_by_scene
    assert [w["word"] for w in adapter.words_by_scene[5]] == ["hi", "there"]


def test_generate_with_timestamps_empty_alignment_fallback(tmp_path):
    """SDK returned empty alignment: words_by_scene should hold an empty list."""

    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)

    with patch.object(
        ElevenLabsAdapter,
        "_invoke_tts_with_timestamps",
        return_value=(b"fake", {
            "characters": [],
            "character_start_times_seconds": [],
            "character_end_times_seconds": [],
        }),
    ), patch.object(ElevenLabsAdapter, "_get_audio_duration", return_value=1.0):
        result = adapter.generate_with_timestamps(
            [{"scene_id": 0, "text": "x"}]
        )

    assert len(result) == 1
    assert adapter.words_by_scene[0] == []
