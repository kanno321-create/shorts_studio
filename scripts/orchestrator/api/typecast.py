"""Typecast Korean TTS adapter (AUDIO-01 primary per D-10).

Phase 5 rewrite of the Typecast path harvested in
``.preserved/harvested/api_wrappers_raw/tts_generate.py`` (1413 lines). The
Fish Audio / VOICEVOX / EdgeTTS tiers are intentionally dropped (AUDIO-01
locks the stack to Typecast primary + ElevenLabs fallback), but the
critical preservation targets are retained verbatim per RESEARCH §8 line
786:

* ``chunk_text_for_typecast`` — sentence-boundary chunking so long
  narrations still fit Typecast's per-call length budget.
* ``_inject_punctuation_breaks`` — SSML ``<break/>`` injection that
  compensates for voices which under-pause at ``.?!`` and ``,``.
* ``_get_audio_duration`` — pydub-based MP3 duration lookup.

The adapter returns ``list[AudioSegment]`` (from
:mod:`scripts.orchestrator.voice_first_timeline`) with monotonic
``start`` / ``end`` offsets so :class:`VoiceFirstTimeline.align` can
consume the output directly (D-10 voice-first contract).

API key resolution: constructor ``api_key`` -> ``$TYPECAST_API_KEY``.
Raises ``ValueError`` if missing.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..voice_first_timeline import AudioSegment
from .models import TypecastRequest

if TYPE_CHECKING:
    from ..circuit_breaker import CircuitBreaker


DEFAULT_OUTPUT_DIR = Path("outputs/typecast")
DEFAULT_SILENCE_GAP_S = 0.3
DEFAULT_CHUNK_MAX_CHARS = 2000


class TypecastAdapter:
    """Primary Korean TTS provider.

    Parameters mirror the other Phase 5 adapters. ``circuit_breaker`` is
    optional — Plan 07 wraps the adapter call through the breaker to
    route to :class:`ElevenLabsAdapter` when Typecast is unhealthy.
    """

    def __init__(
        self,
        api_key: str | None = None,
        circuit_breaker: "CircuitBreaker | None" = None,
        output_dir: Path | None = None,
    ) -> None:
        resolved = api_key or os.environ.get("TYPECAST_API_KEY")
        if not resolved:
            raise ValueError(
                "TypecastAdapter: no API key supplied and TYPECAST_API_KEY is not"
                " set in the environment."
            )
        self._api_key = resolved
        self.circuit_breaker = circuit_breaker
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, scenes: list[dict]) -> list[AudioSegment]:
        """Synthesise one :class:`AudioSegment` per input scene.

        Parameters
        ----------
        scenes:
            List of dicts shaped like
            ``{"scene_id": int, "text": str, "emotion_style": str | None,
            "voice_id": str | None}``. Each entry is validated through
            :class:`TypecastRequest` before it reaches the SDK.

        Returns
        -------
        list[AudioSegment]
            Ordered by ``scene_id``. ``start`` offsets accumulate
            (segment ``i+1`` starts at ``segment_i.end + silence_gap``)
            so the return value feeds straight into
            :meth:`VoiceFirstTimeline.align`.
        """

        self.output_dir.mkdir(parents=True, exist_ok=True)

        segments: list[AudioSegment] = []
        running_offset = 0.0
        for scene in scenes:
            req = TypecastRequest(
                scene_id=scene["scene_id"],
                text=scene["text"],
                emotion_style=scene.get("emotion_style", "neutral"),
                voice_id=scene.get("voice_id", "detective_hao"),
                model=scene.get("model", "ssfm-v30"),
            )

            # Pre-process: inject SSML pauses so short voices (Morgan etc.)
            # don't glue sentences together on commas/terminals.
            prepared_text = self._inject_punctuation_breaks(req.text)
            chunks = self._chunk_text_for_typecast(prepared_text, DEFAULT_CHUNK_MAX_CHARS)
            output_path = self.output_dir / f"scene_{req.scene_id:03d}.mp3"

            self._invoke_typecast_api(
                text_chunks=chunks,
                voice_id=req.voice_id,
                emotion_style=req.emotion_style,
                scene_id=req.scene_id,
                output_path=output_path,
                model=req.model,
            )

            duration = self._get_audio_duration(output_path)
            seg = AudioSegment(
                index=req.scene_id,
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
    # Text-shaping helpers (preserved from harvested tts_generate.py)
    # ------------------------------------------------------------------

    def _chunk_text_for_typecast(
        self,
        text: str,
        max_chars: int = DEFAULT_CHUNK_MAX_CHARS,
    ) -> list[str]:
        """Split ``text`` at sentence boundaries into chunks <= ``max_chars``.

        Mirrors ``chunk_text_for_typecast`` from the harvested reference.
        Korean and Latin sentence terminators (``.?!``) are honoured; if
        the regex yields nothing the fallback path splits on newlines, then
        forces a hard split at spaces inside any single oversize sentence.
        """

        if len(text) <= max_chars:
            return [text] if text else []

        sentences = re.findall(r"[^.!?]*[.!?]+\s*|[^.!?]+$", text)
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            sentences = [s for s in text.split("\n") if s.strip()]
        if not sentences:
            sentences = [text]

        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) > max_chars:
                chunks.append(current.strip())
                current = ""

            if len(sentence) > max_chars:
                if current:
                    chunks.append(current.strip())
                    current = ""
                remainder = sentence
                while len(remainder) > max_chars:
                    split_at = remainder.rfind(" ", 0, max_chars)
                    if split_at == -1:
                        split_at = remainder.rfind("\n", 0, max_chars)
                    if split_at == -1:
                        split_at = max_chars
                    chunks.append(remainder[:split_at].strip())
                    remainder = remainder[split_at:].strip()
                if remainder:
                    current = remainder
            else:
                current += sentence

        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if c.strip()]

    def _inject_punctuation_breaks(
        self,
        text: str,
        mark_pause: float = 0.35,
        comma_pause: float = 0.2,
    ) -> str:
        """Inject ``<break time="Xs"/>`` after terminals / commas.

        Idempotent: once a ``<break/>`` tag follows a punctuation mark, the
        trailing-whitespace precondition is no longer met, so a second pass
        cannot re-inject. Preserved verbatim from harvested
        ``tts_generate._inject_punctuation_breaks``.
        """

        text = re.sub(
            r"([.!?。！？])(\s+)",
            lambda m: f'{m.group(1)}<break time="{mark_pause}s"/>{m.group(2)}',
            text,
        )
        text = re.sub(
            r"([,，、])(\s+)",
            lambda m: f'{m.group(1)}<break time="{comma_pause}s"/>{m.group(2)}',
            text,
        )
        return text

    # ------------------------------------------------------------------
    # Audio-duration helper (preserved)
    # ------------------------------------------------------------------

    def _get_audio_duration(self, path: Path) -> float:
        """Return ``path``'s duration in seconds using pydub.

        pydub is imported lazily so the adapter module stays importable
        on machines without ffmpeg present (pydub imports it at class load).
        """

        try:
            from pydub import AudioSegment as PydubAudio
        except ImportError:
            # Fallback: use ffprobe via subprocess. Both paths give the
            # same number; pydub is preferred for parity with the harvested
            # reference.
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

    # ------------------------------------------------------------------
    # SDK seam — mockable by tests
    # ------------------------------------------------------------------

    def _invoke_typecast_api(
        self,
        *,
        text_chunks: list[str],
        voice_id: str,
        emotion_style: str,
        scene_id: int,
        output_path: Path,
        model: str = "ssfm-v30",
    ) -> Path:
        """Call the Typecast SDK once per chunk and concatenate the results.

        The ``typecast`` Python SDK is imported lazily so tests can mock
        this seam without the SDK installed. Returns ``output_path``.

        Session #31 fix: Typecast SDK pydantic v2 upgrade requires ``model``
        field on TTSRequest. Default ``ssfm-v30`` (2026Q2 한국어 주 모델).
        """

        from typecast import Typecast  # lazy
        from typecast.models import Output, TTSRequest  # lazy

        client = Typecast(api_key=self._api_key)

        audio_paths: list[Path] = []
        for idx, chunk in enumerate(text_chunks):
            tmp_path = self.output_dir / f"scene_{scene_id:03d}_chunk_{idx:02d}.mp3"
            request: Any = TTSRequest(
                voice_id=voice_id,
                text=chunk,
                model=model,
                emotion=emotion_style,
                output=Output(audio_format="mp3"),
            )
            # Session #31 — Typecast SDK API: client.text_to_speech(request=)
            # returns TTSResponse(audio_data, duration, format). Old .generate()
            # + .audio path deprecated.
            response = client.text_to_speech(request=request)
            tmp_path.write_bytes(response.audio_data)
            audio_paths.append(tmp_path)

        if len(audio_paths) == 1:
            audio_paths[0].replace(output_path)
            return output_path
        return self._concat_with_silence(audio_paths, output_path, DEFAULT_SILENCE_GAP_S)

    def _concat_with_silence(
        self,
        chunk_files: list[Path],
        output_path: Path,
        gap_seconds: float = DEFAULT_SILENCE_GAP_S,
    ) -> Path:
        """Concatenate chunk MP3s with ``gap_seconds`` of silence between each.

        Uses FFmpeg's concat demuxer (matches the harvested
        ``concat_with_silence`` helper). Tests mock this method since it
        shells out.
        """

        import subprocess

        output_dir = output_path.parent
        silence_path = output_dir / "_silence_gap.mp3"
        concat_list_path = output_dir / "_concat_list.txt"

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                str(gap_seconds),
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(silence_path),
            ],
            check=True,
            capture_output=True,
        )

        with concat_list_path.open("w", encoding="utf-8") as f:
            for i, chunk_file in enumerate(chunk_files):
                safe = chunk_file.resolve().as_posix()
                f.write(f"file '{safe}'\n")
                if i < len(chunk_files) - 1:
                    f.write(f"file '{silence_path.resolve().as_posix()}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                "-c",
                "copy",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )

        for tmp in (silence_path, concat_list_path):
            if tmp.exists():
                tmp.unlink()
        return output_path


__all__ = ["TypecastAdapter"]
