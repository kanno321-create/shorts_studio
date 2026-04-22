"""Multi-speaker dialogue audio generation via ElevenLabs Text to Dialogue API.

Produces multi-speaker audio for politics channel debate/argument content.
Per D-03: max 2-3 voices (anchor + panelist structure).

Uses ElevenLabs Text to Dialogue API with Eleven v3 model.

IMPORTANT: This module defines TTSProviderError inline rather than importing from
tts_generate.py. The scripts/audio-pipeline/ directory uses hyphens and is NOT a
Python package (no __init__.py). The existing convention is sys.path manipulation,
not package imports. The inline class signature matches tts_generate.TTSProviderError
for consistency.
"""
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Maximum speakers per dialogue per D-03 (anchor + panelist_a + panelist_b)
MAX_SPEAKERS = 3

# Env var names for voice ID overrides
_ENV_VOICE_MAP = {
    "anchor": "ELEVENLABS_ANCHOR_VOICE_ID",
    "panelist_a": "ELEVENLABS_PANELIST_A_VOICE_ID",
    "panelist_b": "ELEVENLABS_PANELIST_B_VOICE_ID",
}


class TTSProviderError(Exception):
    """Raised when a TTS provider returns an error. Mirrors tts_generate.TTSProviderError."""

    def __init__(self, provider: str, status_code: int = None, message: str = ""):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}" + (f" (HTTP {status_code})" if status_code else ""))


@dataclass
class DialogueResult:
    """Result of a dialogue generation operation.

    Attributes:
        output_path: Path to the generated dialogue audio file.
        speaker_count: Number of unique speakers in the dialogue.
        status: One of "success" or "error".
        error_message: Error details if status is "error".
    """
    output_path: str
    speaker_count: int
    status: str
    error_message: str = ""


def load_dialogue_voices(presets_path: str = None) -> dict:
    """Load dialogue voice presets from voice-presets.json.

    Args:
        presets_path: Path to voice-presets.json. Defaults to config/voice-presets.json
            relative to project root.

    Returns:
        Dict with dialogue_voices section containing anchor, panelist_a, panelist_b entries.
    """
    if presets_path is None:
        presets_path = str(
            Path(__file__).resolve().parent.parent.parent / "config" / "voice-presets.json"
        )

    with open(presets_path, "r", encoding="utf-8") as f:
        presets = json.load(f)

    return presets.get("dialogue_voices", {})


def _get_voice_id(speaker: str, dialogue_voices: dict) -> str:
    """Resolve voice_id for a speaker, checking env var overrides first.

    Args:
        speaker: Speaker name (anchor, panelist_a, panelist_b).
        dialogue_voices: Loaded dialogue_voices config section.

    Returns:
        Voice ID string (from env var override or config).
    """
    # Check env var override first
    env_var = _ENV_VOICE_MAP.get(speaker)
    if env_var:
        env_value = os.environ.get(env_var)
        if env_value:
            logger.info("Using env var override for %s: %s=%s", speaker, env_var, env_value)
            return env_value

    # Fall back to voice-presets.json config
    voice_config = dialogue_voices.get(speaker, {})
    voice_id = voice_config.get("voice_id", "")
    if not voice_id:
        logger.warning("No voice_id found for speaker '%s' in dialogue_voices config", speaker)
    return voice_id


def generate_dialogue(
    script_sections: list[dict],
    output_path: str,
    language_code: str = "ko",
    client=None,
) -> DialogueResult:
    """Generate multi-speaker dialogue audio via ElevenLabs Text to Dialogue API.

    Args:
        script_sections: List of dicts with "speaker" and "text" keys.
            Speaker values should be "anchor", "panelist_a", or "panelist_b".
        output_path: Path to write the output MP3 file.
        language_code: Language code for the dialogue (default: "ko" for Korean).
        client: Optional pre-configured ElevenLabs client (for testing).

    Returns:
        DialogueResult with status "success" on success.

    Raises:
        ValueError: If script_sections is invalid or exceeds MAX_SPEAKERS.
        TTSProviderError: If ElevenLabs API returns an error.
    """
    # Validate script_sections
    if not script_sections:
        raise ValueError("script_sections cannot be empty")

    for i, section in enumerate(script_sections):
        if "speaker" not in section:
            raise ValueError(f"Section {i} missing required 'speaker' key")
        if "text" not in section:
            raise ValueError(f"Section {i} missing required 'text' key")

    # Validate unique speakers <= MAX_SPEAKERS
    unique_speakers = set(section["speaker"] for section in script_sections)
    if len(unique_speakers) > MAX_SPEAKERS:
        raise ValueError(
            f"Too many speakers ({len(unique_speakers)}): {unique_speakers}. "
            f"Maximum is {MAX_SPEAKERS} per D-03."
        )

    # Create client if not provided
    if client is None:
        from elevenlabs.client import ElevenLabs
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise TTSProviderError("elevenlabs_dialogue", message="ELEVENLABS_API_KEY not set")
        client = ElevenLabs(api_key=api_key)

    # Load dialogue voice presets
    dialogue_voices = load_dialogue_voices()

    # Build inputs list with voice_id mappings
    inputs = []
    for section in script_sections:
        speaker = section["speaker"]
        voice_id = _get_voice_id(speaker, dialogue_voices)
        inputs.append({
            "text": section["text"],
            "voice_id": voice_id,
        })

    # Call Text to Dialogue API
    try:
        audio_iterator = client.text_to_dialogue.convert(
            inputs=inputs,
            model_id="eleven_v3",
            language_code=language_code,
            output_format="mp3_44100_128",
        )

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write audio chunks to file
        with open(output_path, "wb") as f:
            for chunk in audio_iterator:
                if isinstance(chunk, bytes):
                    f.write(chunk)

        logger.info(
            "Dialogue audio generated: %s (%d speakers)",
            output_path, len(unique_speakers),
        )

        return DialogueResult(
            output_path=output_path,
            speaker_count=len(unique_speakers),
            status="success",
        )

    except TTSProviderError:
        raise
    except Exception as e:
        raise TTSProviderError(
            "elevenlabs_dialogue",
            message=f"Text to Dialogue API error: {e}",
        )
