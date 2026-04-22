"""ElevenLabs Forced Alignment & TTS-with-Timestamps utility.

STT 없이 대본 텍스트로부터 100% 정확한 단어별 타이밍을 생성한다.

두 가지 모드:
1. TTS + Timestamps 동시 생성 (ElevenLabs TTS 사용 시)
   - 음성 + alignment JSON 동시 리턴
2. Forced Alignment (Typecast 등 외부 TTS 사용 시)
   - 이미 생성된 음성 + 대본 텍스트 → 단어별 타이밍 리턴

출력: word_subtitle.py가 소비할 수 있는 단어 리스트 JSON
[{"word": "탐정이", "start": 0.123, "end": 0.456}, ...]
"""
import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env", override=True)


def _get_api_key() -> str:
    """Get ElevenLabs API key from env."""
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_API_KEY")
    if not key:
        raise ValueError("ELEVENLABS_API_KEY or ELEVEN_API_KEY not set in .env")
    return key


def _chars_to_words(characters: list[str],
                    start_times: list[float],
                    end_times: list[float]) -> list[dict]:
    """Convert character-level alignment to word-level alignment.

    Splits on whitespace characters to group into words.
    Returns list of {"word": str, "start": float, "end": float}.
    """
    words = []
    current_word = ""
    word_start = None

    for i, char in enumerate(characters):
        if char.strip() == "":
            # Whitespace = word boundary
            if current_word:
                words.append({
                    "word": current_word,
                    "start": word_start,
                    "end": end_times[i - 1] if i > 0 else start_times[i],
                })
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = start_times[i]
            current_word += char

    # Last word
    if current_word and word_start is not None:
        words.append({
            "word": current_word,
            "start": word_start,
            "end": end_times[-1] if end_times else word_start + 0.1,
        })

    return words


def tts_with_timestamps(text: str,
                        voice_id: str,
                        output_audio_path: str,
                        model_id: str = "eleven_multilingual_v2",
                        language_code: str = "ko",
                        voice_settings: dict = None) -> list[dict]:
    """Generate TTS audio AND word-level timestamps in one API call.

    Args:
        text: 대본 텍스트
        voice_id: ElevenLabs voice ID
        output_audio_path: MP3 저장 경로
        model_id: ElevenLabs model
        language_code: ISO 639-1 (ko, en, ja)
        voice_settings: Optional stability/similarity settings

    Returns:
        Word-level alignment list: [{"word": str, "start": float, "end": float}, ...]
    """
    from elevenlabs.client import ElevenLabs

    api_key = _get_api_key()
    client = ElevenLabs(api_key=api_key)

    kwargs = {
        "voice_id": voice_id,
        "text": text,
        "model_id": model_id,
        "language_code": language_code,
    }
    if voice_settings:
        kwargs["voice_settings"] = voice_settings

    response = client.text_to_speech.convert_with_timestamps(**kwargs)

    # Save audio
    audio_bytes = base64.b64decode(response.audio_base64)
    Path(output_audio_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_audio_path, "wb") as f:
        f.write(audio_bytes)

    # Convert character alignment to word alignment
    alignment = response.alignment
    words = _chars_to_words(
        alignment.characters,
        alignment.character_start_times_seconds,
        alignment.character_end_times_seconds,
    )

    return words


def forced_alignment(audio_path: str,
                     text: str,
                     language_code: str = "ko") -> list[dict]:
    """Align existing audio with text using ElevenLabs Forced Alignment.

    Typecast 등 외부 TTS로 생성한 음성에 대본 텍스트를 정렬한다.
    STT 없이 100% 정확한 단어 타이밍 생성.

    Args:
        audio_path: 음성 파일 경로 (mp3/wav)
        text: 대본 텍스트 (음성과 일치해야 함)
        language_code: ISO 639-1

    Returns:
        Word-level alignment list: [{"word": str, "start": float, "end": float}, ...]
    """
    import httpx

    api_key = _get_api_key()

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # ElevenLabs Forced Alignment API
    response = httpx.post(
        "https://api.elevenlabs.io/v1/forced-alignment",
        headers={"xi-api-key": api_key},
        files={"audio": (Path(audio_path).name, audio_data)},
        data={
            "text": text,
            "language_code": language_code,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    # Parse alignment response
    alignment = data.get("alignment", {})
    words = _chars_to_words(
        alignment.get("characters", []),
        alignment.get("character_start_times_seconds", []),
        alignment.get("character_end_times_seconds", []),
    )

    return words


def save_alignment_json(words: list[dict], output_path: str):
    """Save word alignment to JSON file for word_subtitle.py consumption."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(words)} words to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="ElevenLabs Forced Alignment — STT 없이 100% 정확한 자막 타이밍"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Mode 1: TTS + timestamps
    tts_parser = subparsers.add_parser("tts", help="TTS 생성 + 타임스탬프 동시")
    tts_parser.add_argument("--text", required=True, help="대본 텍스트 또는 파일 경로")
    tts_parser.add_argument("--voice-id", required=True, help="ElevenLabs voice ID")
    tts_parser.add_argument("--output-audio", required=True, help="음성 출력 경로")
    tts_parser.add_argument("--output-alignment", required=True, help="alignment JSON 출력 경로")
    tts_parser.add_argument("--model", default="eleven_multilingual_v2")
    tts_parser.add_argument("--language", default="ko", choices=["ko", "en", "ja"])

    # Mode 2: Forced alignment (외부 TTS 음성)
    fa_parser = subparsers.add_parser("align", help="기존 음성에 대본 정렬")
    fa_parser.add_argument("--audio", required=True, help="음성 파일 경로")
    fa_parser.add_argument("--text", required=True, help="대본 텍스트 또는 파일 경로")
    fa_parser.add_argument("--output", required=True, help="alignment JSON 출력 경로")
    fa_parser.add_argument("--language", default="ko", choices=["ko", "en", "ja"])

    args = parser.parse_args()

    def _resolve_text(text_arg: str) -> str:
        """텍스트 인자가 파일 경로면 파일 내용 읽기."""
        if Path(text_arg).exists():
            return Path(text_arg).read_text(encoding="utf-8")
        return text_arg

    if args.mode == "tts":
        text = _resolve_text(args.text)
        words = tts_with_timestamps(
            text=text,
            voice_id=args.voice_id,
            output_audio_path=args.output_audio,
            model_id=args.model,
            language_code=args.language,
        )
        save_alignment_json(words, args.output_alignment)
        print(json.dumps({
            "mode": "tts_with_timestamps",
            "audio_path": args.output_audio,
            "alignment_path": args.output_alignment,
            "word_count": len(words),
        }, ensure_ascii=False))

    elif args.mode == "align":
        text = _resolve_text(args.text)
        words = forced_alignment(
            audio_path=args.audio,
            text=text,
            language_code=args.language,
        )
        save_alignment_json(words, args.output)
        print(json.dumps({
            "mode": "forced_alignment",
            "alignment_path": args.output,
            "word_count": len(words),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
