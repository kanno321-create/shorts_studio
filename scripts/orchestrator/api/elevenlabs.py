"""ElevenLabs TTS fallback adapter with word-level timestamps (D-10).

Phase 5 rewrite of the ElevenLabs path harvested in
``.preserved/harvested/api_wrappers_raw/elevenlabs_alignment.py``. The
critical preservation target per RESEARCH §8 line 787 is
:func:`_chars_to_words` — it maps character-level timestamps (what the
ElevenLabs ``convert_with_timestamps`` endpoint returns) to the
word-level timing format that :class:`VoiceFirstTimeline` and the
subtitle generator consume.

Two public generation methods:

* :meth:`generate` — simple synthesis returning one AudioSegment per
  scene, no word timings. Used when ElevenLabs is the fallback and the
  pipeline only needs playback.
* :meth:`generate_with_timestamps` — synthesis + word-level alignment.
  Each AudioSegment still carries ``(start, end, duration, path)`` as
  usual; word timings attach to the returned list via a parallel
  ``words`` attribute not modelled on the dataclass (kept on the
  returned tuple form to avoid mutating the dataclass contract).

API key resolution: ``api_key`` -> ``$ELEVENLABS_API_KEY`` ->
``$ELEVEN_API_KEY``. ``ValueError`` if none resolves.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..voice_first_timeline import AudioSegment

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker


DEFAULT_OUTPUT_DIR = Path("outputs/elevenlabs")
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_LANGUAGE_CODE = "ko"
DEFAULT_SILENCE_GAP_S = 0.3
DEFAULT_VOICE_ID_ENV = "ELEVENLABS_DEFAULT_VOICE_ID"

# Pitfall 6 (RESEARCH §5): module-level cache for API discovery result so
# repeated ElevenLabsAdapter construction within the same process does not
# re-query GET /v1/voices (cost + rate-limit hygiene).
_KOREAN_FALLBACK_VOICE_ID: str | None = None


# ---------------------------------------------------------------------------
# _chars_to_words — preserved verbatim from harvested elevenlabs_alignment.py
# (lines 36-72, per RESEARCH §8 line 787).
# ---------------------------------------------------------------------------


def _chars_to_words(
    characters: list[str],
    start_times: list[float],
    end_times: list[float],
) -> list[dict]:
    """Convert character-level alignment to word-level alignment.

    Splits on whitespace characters to group into words. Returns a list of
    ``{"word": str, "start": float, "end": float}`` dicts. Whitespace acts
    as a word boundary; leading whitespace skips until a non-blank char.
    Trailing word is emitted with the last character's end time.
    """

    words: list[dict] = []
    current_word = ""
    word_start: float | None = None

    for i, char in enumerate(characters):
        if char.strip() == "":
            if current_word:
                words.append(
                    {
                        "word": current_word,
                        "start": word_start,
                        "end": end_times[i - 1] if i > 0 else start_times[i],
                    }
                )
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = start_times[i]
            current_word += char

    if current_word and word_start is not None:
        words.append(
            {
                "word": current_word,
                "start": word_start,
                "end": end_times[-1] if end_times else word_start + 0.1,
            }
        )
    return words


class ElevenLabsAdapter:
    """ElevenLabs Multilingual v2 TTS (fallback for Typecast per D-10).

    ``words_by_scene`` holds the word-level alignment from the most recent
    call to :meth:`generate_with_timestamps`, keyed by ``scene_id``. Plan
    07 uses this to build subtitle tracks without re-querying the API.
    """

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
        default_voice_id: str | None = None,
    ) -> None:
        resolved = (
            api_key
            or os.environ.get("ELEVENLABS_API_KEY")
            or os.environ.get("ELEVEN_API_KEY")
        )
        if not resolved:
            raise ValueError(
                "ElevenLabsAdapter: no API key supplied and neither ELEVENLABS_API_KEY"
                " nor ELEVEN_API_KEY is set in the environment."
            )
        self._api_key = resolved
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.words_by_scene: dict[int, list[dict]] = {}

        # D-13 default voice_id resolution (3-tier, lazy):
        #   (a) explicit constructor kwarg
        #   (b) env var ELEVENLABS_DEFAULT_VOICE_ID
        #   (c) discover_korean_default_voice() via GET /v1/voices
        # Constructor captures (a) + env snapshot (b) so tests can assert the
        # end state. Tier (c) is deferred to _resolve_default_voice_id() so
        # network I/O happens only when actually synthesising audio.
        self._default_voice_id = default_voice_id or os.environ.get(
            DEFAULT_VOICE_ID_ENV
        )

    # ------------------------------------------------------------------
    # Default-voice resolution (D-13)
    # ------------------------------------------------------------------

    def _resolve_default_voice_id(self) -> str:
        """3-tier resolution: constructor/env snapshot → module cache → API.

        Uses a module-level cache (:data:`_KOREAN_FALLBACK_VOICE_ID`) so
        multiple adapter instances in the same process share one GET
        /v1/voices round-trip (Pitfall 6).
        """

        global _KOREAN_FALLBACK_VOICE_ID
        if self._default_voice_id:
            return self._default_voice_id
        if _KOREAN_FALLBACK_VOICE_ID:
            return _KOREAN_FALLBACK_VOICE_ID
        from ..voice_discovery import discover_korean_default_voice
        _KOREAN_FALLBACK_VOICE_ID = discover_korean_default_voice(self._api_key)
        return _KOREAN_FALLBACK_VOICE_ID

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, scenes: list[dict]) -> list[AudioSegment]:
        """Synthesise one :class:`AudioSegment` per scene without word timings.

        Mirror of :meth:`TypecastAdapter.generate` so Plan 07 can swap the
        two adapters without reshaping the return value.
        """

        self.output_dir.mkdir(parents=True, exist_ok=True)

        segments: list[AudioSegment] = []
        running_offset = 0.0
        for scene in scenes:
            scene_id = int(scene["scene_id"])
            text = scene["text"]
            if not text:
                raise ValueError(f"ElevenLabsAdapter.generate: empty text for scene {scene_id}")
            voice_id = scene.get("voice_id") or self._resolve_default_voice_id()
            output_path = self.output_dir / f"scene_{scene_id:03d}.mp3"

            audio_bytes = self._invoke_tts(
                text=text,
                voice_id=voice_id,
                language_code=scene.get("language_code", DEFAULT_LANGUAGE_CODE),
                model_id=scene.get("model_id", DEFAULT_MODEL_ID),
            )
            output_path.write_bytes(audio_bytes)

            duration = self._get_audio_duration(output_path)
            seg = AudioSegment(
                index=scene_id,
                start=running_offset,
                end=running_offset + duration,
                duration=duration,
                path=output_path,
            )
            segments.append(seg)
            running_offset = seg.end + DEFAULT_SILENCE_GAP_S

        segments.sort(key=lambda s: s.index)
        return segments

    def generate_with_timestamps(self, scenes: list[dict]) -> list[AudioSegment]:
        """Synthesise scenes AND populate :attr:`words_by_scene` with word timings.

        Uses ElevenLabs' ``convert_with_timestamps`` endpoint (via the
        SDK's :meth:`text_to_speech.convert_with_timestamps`). The SDK
        returns character-level alignment; :func:`_chars_to_words` folds
        it into the word-level dicts the subtitle generator expects.
        """

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.words_by_scene = {}

        segments: list[AudioSegment] = []
        running_offset = 0.0
        for scene in scenes:
            scene_id = int(scene["scene_id"])
            text = scene["text"]
            if not text:
                raise ValueError(
                    f"ElevenLabsAdapter.generate_with_timestamps: empty text for scene {scene_id}"
                )
            voice_id = scene.get("voice_id") or self._resolve_default_voice_id()
            output_path = self.output_dir / f"scene_{scene_id:03d}.mp3"

            audio_bytes, alignment = self._invoke_tts_with_timestamps(
                text=text,
                voice_id=voice_id,
                language_code=scene.get("language_code", DEFAULT_LANGUAGE_CODE),
                model_id=scene.get("model_id", DEFAULT_MODEL_ID),
            )
            output_path.write_bytes(audio_bytes)

            chars = list(alignment.get("characters", []))
            start_times = list(alignment.get("character_start_times_seconds", []))
            end_times = list(alignment.get("character_end_times_seconds", []))
            words = _chars_to_words(chars, start_times, end_times)
            self.words_by_scene[scene_id] = words

            duration = self._get_audio_duration(output_path)
            seg = AudioSegment(
                index=scene_id,
                start=running_offset,
                end=running_offset + duration,
                duration=duration,
                path=output_path,
            )
            segments.append(seg)
            running_offset = seg.end + DEFAULT_SILENCE_GAP_S

        segments.sort(key=lambda s: s.index)
        return segments

    # ------------------------------------------------------------------
    # SDK seams — test-mockable
    # ------------------------------------------------------------------

    def _invoke_tts(
        self,
        *,
        text: str,
        voice_id: str,
        language_code: str,
        model_id: str,
    ) -> bytes:
        """Simple bytes-out TTS call. Mocked in tests."""

        from elevenlabs.client import ElevenLabs  # lazy

        client = ElevenLabs(api_key=self._api_key)
        stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            language_code=language_code,
        )
        # SDK returns an iterator of chunks. Join into a single bytes buffer.
        return b"".join(chunk for chunk in stream)

    def _invoke_tts_with_timestamps(
        self,
        *,
        text: str,
        voice_id: str,
        language_code: str,
        model_id: str,
    ) -> tuple[bytes, dict[str, Any]]:
        """TTS + character-level alignment call. Mocked in tests."""

        from elevenlabs.client import ElevenLabs  # lazy

        client = ElevenLabs(api_key=self._api_key)
        response = client.text_to_speech.convert_with_timestamps(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            language_code=language_code,
        )
        audio_bytes = base64.b64decode(response.audio_base64)
        alignment_obj = response.alignment
        alignment = {
            "characters": list(getattr(alignment_obj, "characters", []) or []),
            "character_start_times_seconds": list(
                getattr(alignment_obj, "character_start_times_seconds", []) or []
            ),
            "character_end_times_seconds": list(
                getattr(alignment_obj, "character_end_times_seconds", []) or []
            ),
        }
        return audio_bytes, alignment

    # ------------------------------------------------------------------
    # Duration helper (parallel to TypecastAdapter._get_audio_duration).
    # ------------------------------------------------------------------

    def _get_audio_duration(self, path: Path) -> float:
        try:
            from pydub import AudioSegment as PydubAudio
        except ImportError:
            import json
            import subprocess

            out = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(json.loads(out.stdout)["format"]["duration"])

        audio = PydubAudio.from_mp3(str(path))
        return len(audio) / 1000.0


__all__ = ["ElevenLabsAdapter", "_chars_to_words"]
