"""日本語専用字幕生成モジュール。

韓国語のword_subtitle.pyとは根本的に異なるアプローチ:
- テキスト: script.jsonの原文をそのまま使用（Whisperの誤変換を完全排除）
- タイミング: Whisperのセグメント境界のみ使用
- 表示単位: MeCab文節（ぶんせつ）分割 → 1cueに1フレーズ

Why:
  Whisperは日本語で同音異義語を誤変換する（血痕→結婚, 航海日誌→公開日誌）
  日本語にはスペースがないため、韓国語のword-highlight方式は不適

出力:
  subtitles_remotion.json — [{startMs, endMs, words: [phrase], highlightIndex: 0}]
  各cueのwordsは1要素（フレーズ全体）。ハイライトは常に0。

CLI:
  ja_subtitle.py --audio AUDIO --script SCRIPT --output OUTPUT
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _split_bunsetsu(text: str) -> list[str]:
    """MeCab文節分割。助詞・助動詞は前の自立語に結合。"""
    try:
        import fugashi
    except ImportError:
        logger.warning("fugashi not installed, falling back to 6-char split")
        return [text[i:i + 6] for i in range(0, len(text), 6)] if text else []

    tagger = fugashi.Tagger()
    morphs = tagger(text)

    _JIRITSU = {"名詞", "動詞", "形容詞", "副詞", "接続詞", "感動詞", "連体詞", "接頭辞"}
    bunsetsu_list: list[str] = []
    current = ""

    for morph in morphs:
        pos = morph.feature.pos1 if hasattr(morph.feature, "pos1") else str(morph.feature).split(",")[0]
        surface = morph.surface

        if pos in _JIRITSU and current:
            bunsetsu_list.append(current)
            current = surface
        else:
            current += surface

    if current:
        bunsetsu_list.append(current)

    return bunsetsu_list


def _kanji_to_arabic(text: str) -> str:
    """字幕表示用: 漢数字をアラビア数字に変換。

    TTS用スクリプトは漢数字（千九百七十一年）だが、
    字幕は視聴者が読みやすいアラビア数字（1971年）にする。
    直接マッピング方式 — パーサーより確実。
    """
    # よく出る漢数字を直接置換（長い順に処理）
    _MAP = [
        ('千九百七十一', '1971'), ('千九百八十', '1980'),
        ('二千十六', '2016'), ('二千', '2000'),
        ('二十万', '20万'), ('五千八百', '5800'),
        ('三百七十', '370'), ('三十六', '36'),
        ('五十三', '53'), ('千九百', '1900'),
        ('八百', '800'), ('七百', '700'), ('六百', '600'),
        ('五百', '500'), ('四百', '400'), ('三百', '300'),
        ('二百', '200'), ('百', '100'),
        ('三千', '3000'), ('千', '1000'),
        ('九十', '90'), ('八十', '80'), ('七十', '70'),
        ('六十', '60'), ('五十', '50'), ('四十', '40'),
        ('三十', '30'), ('二十', '20'), ('十一', '11'),
        ('十二', '12'), ('十三', '13'), ('十四', '14'),
        ('十五', '15'), ('十六', '16'), ('十七', '17'),
        ('十八', '18'), ('十九', '19'), ('十', '10'),
        ('九', '9'), ('八', '8'), ('七', '7'),
        ('六', '6'), ('五', '5'), ('四', '4'),
        ('三', '3'), ('二', '2'), ('一', '1'), ('〇', '0'),
    ]
    result = text
    for kanji, arabic in _MAP:
        result = result.replace(kanji, arabic)
    return result


def _group_bunsetsu(bunsetsu_list: list[str], max_chars: int = 12) -> list[str]:
    """文節をフレーズにグルーピング。1フレーズ max_chars文字以内。"""
    phrases: list[str] = []
    current = ""

    for b in bunsetsu_list:
        if current and len(current) + len(b) > max_chars:
            phrases.append(current)
            current = b
        else:
            current += b

    if current:
        phrases.append(current)

    return phrases


def generate_ja_subtitles(
    audio_path: str,
    script_path: str,
    output_path: str,
    model_size: str = "large-v3",
    max_chars: int = 12,
) -> dict:
    """日本語字幕生成のメインエントリポイント。

    1. script.jsonからナレーションテキスト抽出
    2. Whisperでオーディオのセグメントタイミング取得（テキストは使わない）
    3. スクリプトテキストをMeCab文節分割→フレーズグルーピング
    4. Whisperタイミングをフレーズに比例配分
    5. Remotion JSON出力

    Args:
        audio_path: narration.mp3パス
        script_path: script.jsonパス
        output_path: subtitles_remotion.json出力パス
        model_size: Whisperモデルサイズ
        max_chars: フレーズ当たり最大文字数

    Returns:
        {output_path, phrase_count, duration_seconds}
    """
    # 1. スクリプトからテキスト抽出
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    sections = script.get("sections", [])
    narrations = []
    for sec in sections:
        text = sec.get("narration", "").strip()
        if text:
            narrations.append(text)

    if not narrations:
        logger.error("No narration found in script")
        Path(output_path).write_text("[]", encoding="utf-8")
        return {"output_path": output_path, "phrase_count": 0, "duration_seconds": 0.0}

    logger.info("Script: %d sections, %d total chars",
                len(narrations), sum(len(n) for n in narrations))

    # 2. Whisperでタイミング取得
    logger.info("Transcribing '%s' for timing only (model=%s)", audio_path, model_size)
    from faster_whisper import WhisperModel

    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
    except Exception:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info("Using CPU mode")

    try:
        segments_iter, info = model.transcribe(
            audio_path, language="ja", word_timestamps=False,
        )
        whisper_segments = list(segments_iter)
    except RuntimeError:
        logger.warning("CUDA failed, retrying on CPU")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments_iter, info = model.transcribe(
            audio_path, language="ja", word_timestamps=False,
        )
        whisper_segments = list(segments_iter)
    logger.info("Whisper: %d segments, duration=%.1fs", len(whisper_segments), info.duration)

    # 3. スクリプトテキスト → 文節 → フレーズ
    all_phrases: list[str] = []
    section_phrase_counts: list[int] = []

    for narr in narrations:
        bunsetsu = _split_bunsetsu(narr)
        phrases = _group_bunsetsu(bunsetsu, max_chars=max_chars)
        all_phrases.extend(phrases)
        section_phrase_counts.append(len(phrases))

    logger.info("Phrases: %d total from %d sections", len(all_phrases), len(narrations))

    # 4. タイミング割り当て（section_timing.json 使用 — 100%正確）
    #
    # TTS生成時に各セクションの正確な長さを記録済み。
    # section_timing.json: {sections: [{start_ms, end_ms, duration_ms}, ...]}
    # Whisperは不要。タイミングの唯一の真実ソースはTTS自身の記録。

    timing_path = str(Path(audio_path).parent / "section_timing.json")
    section_timings: list[dict] | None = None
    if os.path.exists(timing_path):
        with open(timing_path, "r", encoding="utf-8") as f:
            timing_data = json.load(f)
        section_timings = timing_data.get("sections", [])
        logger.info("Loaded section_timing.json: %d sections", len(section_timings))

    cues: list[dict] = []
    phrase_idx = 0

    if section_timings and len(section_timings) == len(narrations):
        # 正確なタイミング使用
        for sec_idx, phrase_count in enumerate(section_phrase_counts):
            t = section_timings[sec_idx]
            sec_start_ms = t["start_ms"]
            sec_duration_ms = t["duration_ms"]

            sec_phrases = all_phrases[phrase_idx:phrase_idx + phrase_count]
            sec_total_chars = sum(len(p) for p in sec_phrases) or 1

            cursor_ms = sec_start_ms
            for phrase in sec_phrases:
                ratio = len(phrase) / sec_total_chars
                dur_ms = sec_duration_ms * ratio
                cues.append({
                    "startMs": int(cursor_ms),
                    "endMs": int(cursor_ms + dur_ms),
                    "words": [phrase],
                    "highlightIndex": 0,
                })
                cursor_ms += dur_ms

            phrase_idx += phrase_count

        logger.info("Timing from section_timing.json (exact TTS boundaries)")
    else:
        # フォールバック: 全体の長さから文字数比例配分
        logger.warning("section_timing.json missing or mismatched, falling back to proportional")
        total_dur = info.duration if hasattr(info, 'duration') and info.duration else 60.0
        total_chars = sum(len(p) for p in all_phrases) or 1
        cursor = 0.0
        for phrase in all_phrases:
            dur = total_dur * (len(phrase) / total_chars)
            cues.append({"startMs": int(cursor * 1000), "endMs": int((cursor + dur) * 1000), "words": [phrase], "highlightIndex": 0})
            cursor += dur

    # 5. 出力
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(cues, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("JA subtitles written: %s (%d cues)", output_path, len(cues))

    # ASS also
    ass_path = str(Path(output_path).with_suffix(".ass"))
    _write_ass(cues, ass_path)

    duration = (cues[-1]["endMs"] - cues[0]["startMs"]) / 1000 if cues else 0.0

    return {
        "output_path": output_path,
        "ass_path": ass_path,
        "remotion_json_path": output_path,
        "phrase_count": len(cues),
        "duration_seconds": round(duration, 3),
    }


def _write_ass(cues: list[dict], ass_path: str) -> None:
    """簡易ASS出力（フレーズ単位）。"""
    header = """[Script Info]
Title: JA Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,M PLUS Rounded 1c,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for cue in cues:
        start = _ms_to_ass_time(cue["startMs"])
        end = _ms_to_ass_time(cue["endMs"])
        text = cue["words"][0]
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    Path(ass_path).write_text("".join(lines), encoding="utf-8")


def _ms_to_ass_time(ms: int) -> str:
    """ミリ秒→ASS時間形式。"""
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Japanese subtitle generator (script-based)")
    parser.add_argument("--audio", required=True, help="Path to narration.mp3")
    parser.add_argument("--script", required=True, help="Path to script.json")
    parser.add_argument("--output", required=True, help="Path to output subtitles_remotion.json")
    parser.add_argument("--max-chars", type=int, default=12, help="Max chars per phrase (default: 12)")
    parser.add_argument("--model", default="large-v3", help="Whisper model size")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    result = generate_ja_subtitles(
        audio_path=args.audio,
        script_path=args.script,
        output_path=args.output,
        model_size=args.model,
        max_chars=args.max_chars,
    )
    print(json.dumps(result, ensure_ascii=False))
