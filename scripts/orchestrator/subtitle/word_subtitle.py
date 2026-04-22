# Ported from .preserved/harvested/audio_pipeline_raw/word_subtitle.py — Phase 16-03
# Source SHA256 recorded in .preserved/harvested/video_pipeline_raw/harvest_extension_manifest.json
#   (audio pipeline harvest legacy — see Plan 16-03 W1-WORDSUB-PORT).
# Do NOT modify Korean timestamp repair pipeline (_extract_words_from_segments → clamp/merge/fallback) —
# FAIL-SCR-016 / FAIL-EDT-008 defense (feedback_subtitle_semantic_grouping 참조).
# CUDA→CPU fallback 보전 (line ~1341~1348).
# CLAUDE.md 필수 #3: 본 파일은 orchestrator 가 아니므로 500~800 줄 상한 미적용 (subtitle pipeline 전용).
# faster-whisper large-v3 + Korean 고정 — WhisperX 사용 금지 (Phase 16-03 전환 이유).

"""Word/phrase-level SRT subtitle generation from audio using faster-whisper.

Generates short-phrase subtitles (5-8 Korean characters per screen) that
appear and disappear in sync with narration timing.  This produces fast
word-by-word transitions instead of full-sentence blocks.

Pipeline position:
    narration.mp3 -> [word_subtitle.py] -> subtitles.srt (phrase-level)

Core approach:
    1. Transcribe with faster-whisper (word_timestamps=True)
    2. Validate/repair Korean word-level timestamps (known unreliable)
    3. Group consecutive words into short phrases (target 5-8 chars)
    4. Output SRT where each entry is one short phrase

Mitigation for unreliable Korean word timestamps:
    - Clamp word timestamps to segment boundaries
    - Merge words with duration < 100ms into adjacent words
    - Fall back to even distribution when word timestamps are missing

Exit codes:
    0 = success
    1 = input error (missing file, invalid args)
    2 = transcription error (model load or transcribe failure)

Outputs:
    - subtitles.srt at the specified output path
    - JSON result to stdout: {output_path, phrase_count, duration_seconds}
"""
import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp HH:MM:SS,mmm.

    Uses comma separator as required by the SRT specification.

    Args:
        seconds: Time in seconds (float).

    Returns:
        Formatted SRT timestamp string.
    """
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def _extract_words_from_segments(segments: list) -> list[dict]:
    """Extract word-level timestamps from faster-whisper segment objects.

    Handles both faster-whisper Word objects and plain dicts.
    For segments without word-level timestamps, falls back to even
    distribution of text across the segment duration.

    Args:
        segments: List of faster-whisper segment objects.

    Returns:
        Flat list of {"word": str, "start": float, "end": float} dicts.
    """
    all_words = []

    for segment in segments:
        seg_start = segment.start if hasattr(segment, "start") else segment["start"]
        seg_end = segment.end if hasattr(segment, "end") else segment["end"]
        seg_text = (segment.text if hasattr(segment, "text") else segment["text"]).strip()

        words_attr = getattr(segment, "words", None)
        if words_attr is None and isinstance(segment, dict):
            words_attr = segment.get("words", None)

        if words_attr and len(words_attr) > 0:
            # Word-level timestamps available
            for w in words_attr:
                if hasattr(w, "word"):
                    word_text = w.word.strip()
                    word_start = w.start
                    word_end = w.end
                elif isinstance(w, dict):
                    word_text = w["word"].strip()
                    word_start = w["start"]
                    word_end = w["end"]
                else:
                    continue

                if not word_text:
                    continue

                # Clamp to segment boundaries
                word_start = max(word_start, seg_start)
                word_end = min(word_end, seg_end)

                # Ensure end > start
                if word_end <= word_start:
                    word_end = word_start + 0.1

                all_words.append({
                    "word": word_text,
                    "start": word_start,
                    "end": word_end,
                })
        else:
            # Fallback: even distribution across segment duration
            if not seg_text:
                continue
            tokens = seg_text.split()
            if not tokens:
                continue
            seg_duration = seg_end - seg_start
            time_per_token = seg_duration / len(tokens) if len(tokens) > 0 else seg_duration
            for i, token in enumerate(tokens):
                t_start = seg_start + i * time_per_token
                t_end = seg_start + (i + 1) * time_per_token
                all_words.append({
                    "word": token,
                    "start": t_start,
                    "end": t_end,
                })

    return all_words


def _merge_short_duration_words(words: list[dict], min_duration: float = 0.1) -> list[dict]:
    """Merge words with duration < min_duration into adjacent words.

    Short-duration words are merged into the next word. If there is no
    next word, they are merged into the previous word.

    Args:
        words: List of word dicts with "word", "start", "end" keys.
        min_duration: Minimum acceptable duration in seconds (default 0.1).

    Returns:
        New list with short words merged into neighbors.
    """
    if not words:
        return []

    merged = []
    i = 0

    while i < len(words):
        current = dict(words[i])
        duration = current["end"] - current["start"]

        if duration < min_duration and i + 1 < len(words):
            # Merge into next word
            next_word = words[i + 1]
            merged_entry = {
                "word": current["word"] + next_word["word"],
                "start": current["start"],
                "end": next_word["end"],
            }
            # Replace next word in source so the loop picks up the merged version
            words = words[:i + 1] + [merged_entry] + words[i + 2:]
            i += 1
            continue
        elif duration < min_duration and merged:
            # Last word is short -- merge into previous
            merged[-1]["word"] = merged[-1]["word"] + current["word"]
            merged[-1]["end"] = current["end"]
            i += 1
            continue

        merged.append(current)
        i += 1

    return merged


def _merge_split_numbers(words: list[dict]) -> list[dict]:
    """Merge split number tokens like "1" + ",701통" → "1,701통".

    Whisper often splits comma-separated numbers into separate tokens.
    This merges them back: a token that is purely digits followed by a token
    starting with comma+digits should be combined.

    Args:
        words: List of word dicts with "word", "start", "end" keys.

    Returns:
        New list with split numbers merged.
    """
    import re
    if not words:
        return []

    merged = []
    i = 0
    while i < len(words):
        current = dict(words[i])
        # Check if current is pure digits and next starts with comma+digits
        if (i + 1 < len(words)
                and re.match(r'^\d+$', current["word"])
                and re.match(r'^[,\.]\d+', words[i + 1]["word"])):
            next_w = words[i + 1]
            merged.append({
                "word": current["word"] + next_w["word"],
                "start": current["start"],
                "end": next_w["end"],
            })
            i += 2
        else:
            merged.append(current)
            i += 1
    return merged


def _correct_from_script(words: list[dict], script_path: str) -> list[dict]:
    """Correct Whisper transcription by aligning to script.json narration.

    Uses the original script as ground truth to fix ALL Whisper errors:
    - Spacing: "소름돋습니다" → "소름 돋습니다"
    - Number format: "3000m" → script's original form
    - Misrecognition: "G340" → "Z340", "암호물" → "암호문"
    - Missing words: Whisper가 누락한 단어 복원

    세션 53 강화: 50% 길이 가드 제거. 심한 오전사도 반드시 교정.
    교정 후 coverage < 90%이면 WARNING 로그 출력.

    Args:
        words: List of word dicts with "word", "start", "end" keys.
        script_path: Path to script.json.

    Returns:
        Corrected list of word dicts (timing preserved, text fixed).
    """
    import difflib

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            script = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load script for correction: %s", e)
        return words

    # Build script word sequence (all narration concatenated)
    script_text = ""
    for section in script.get("sections", []):
        narration = section.get("narration", "")
        if narration:
            script_text += narration + " "
    script_words = script_text.strip().replace(".", " .").replace(",", " ,").replace("?", " ?").replace("!", " !").split()
    script_clean = [w.strip(".,?!…") for w in script_words if w.strip(".,?!…")]

    # Build whisper word sequence
    whisper_texts = [w["word"].strip(".,?!…") for w in words]

    # Use SequenceMatcher to align Whisper output to script
    matcher = difflib.SequenceMatcher(None, whisper_texts, script_clean, autojunk=False)
    corrections = 0
    skipped_mismatches = []
    corrected = list(words)  # shallow copy
    offset = 0  # track index shift from insert/delete operations

    for op, w_start, w_end, s_start, s_end in matcher.get_opcodes():
        w_start += offset
        w_end += offset

        if op == "replace":
            # Whisper and script differ — ALWAYS use script text, keep Whisper timing
            whisper_chunk = " ".join(whisper_texts[w_start - offset:w_end - offset])
            script_chunk = " ".join(script_clean[s_start:s_end])

            s_count = s_end - s_start
            total_start = corrected[w_start]["start"]
            total_end = corrected[w_end - 1]["end"]
            total_dur = total_end - total_start

            new_words = []
            for j, sw in enumerate(script_clean[s_start:s_end]):
                frac_start = total_start + total_dur * (j / s_count)
                frac_end = total_start + total_dur * ((j + 1) / s_count)
                new_words.append({
                    "word": sw,
                    "start": round(frac_start, 3),
                    "end": round(frac_end, 3),
                })

            old_len = w_end - w_start
            corrected[w_start:w_end] = new_words
            offset += len(new_words) - old_len
            corrections += s_count
            logger.debug("Corrected: '%s' → '%s'", whisper_chunk, script_chunk)

        elif op == "insert":
            # Script has words that Whisper missed — insert with interpolated timing
            script_chunk = " ".join(script_clean[s_start:s_end])
            s_count = s_end - s_start

            # Use surrounding word timing for interpolation
            if w_start > 0 and w_start <= len(corrected):
                ref_end = corrected[w_start - 1]["end"]
                if w_start < len(corrected):
                    ref_next_start = corrected[w_start]["start"]
                    gap = ref_next_start - ref_end
                else:
                    gap = 0.5  # fallback gap
            else:
                ref_end = 0.0
                gap = 0.5

            # Only insert if there's a gap to fill (avoid overlapping)
            if gap > 0.05:
                new_words = []
                for j, sw in enumerate(script_clean[s_start:s_end]):
                    frac_start = ref_end + gap * (j / s_count)
                    frac_end = ref_end + gap * ((j + 1) / s_count)
                    new_words.append({
                        "word": sw,
                        "start": round(frac_start, 3),
                        "end": round(frac_end, 3),
                    })
                corrected[w_start:w_start] = new_words
                offset += len(new_words)
                corrections += s_count
                logger.debug("Inserted missing: '%s' at %.3fs", script_chunk, ref_end)
            else:
                skipped_mismatches.append(f"INSERT(no gap): '{script_chunk}'")

        elif op == "delete":
            # Whisper produced words not in script — remove (likely hallucination)
            whisper_chunk = " ".join(whisper_texts[w_start - offset:w_end - offset])
            old_len = w_end - w_start
            del corrected[w_start:w_end]
            offset -= old_len
            corrections += 1
            logger.debug("Removed hallucination: '%s'", whisper_chunk)

    # Post-correction coverage check
    corrected_text = " ".join(w["word"].strip(".,?!…") for w in corrected)
    script_full = " ".join(script_clean)
    coverage = _calc_word_coverage(corrected_text, script_full)

    if coverage < 0.90:
        logger.warning(
            "LOW COVERAGE after correction: %.1f%% (target ≥ 95%%). "
            "Subtitle may not match narration. Skipped: %s",
            coverage * 100,
            skipped_mismatches[:5] if skipped_mismatches else "none",
        )
    elif coverage < 0.95:
        logger.warning("Coverage %.1f%% — below 95%% target", coverage * 100)

    if corrections > 0:
        logger.info("Script-based correction: %d words corrected, coverage %.1f%%", corrections, coverage * 100)
    else:
        logger.info("Script-based correction: no corrections needed, coverage %.1f%%", coverage * 100)

    return corrected


def _calc_word_coverage(subtitle_text: str, script_text: str) -> float:
    """Calculate word-level coverage of subtitle against script."""
    script_words = set(script_text.lower().split())
    sub_words = set(subtitle_text.lower().split())
    if not script_words:
        return 1.0
    matched = script_words & sub_words
    return len(matched) / len(script_words)


def _recombine_ja_characters(words: list[dict]) -> list[dict]:
    """Whisperの1文字バラバラ出力を文節(bunsetsu)単位に再結合する。

    Whisperは日本語を1〜2文字ずつ出力することが多い:
      ['18', '72', '年', '12', '月、', '大', '西', '洋', 'の', 'ど', '真']
    これを文節単位に再結合する:
      ['1872年', '12月、', '大西洋の', 'ど真ん中で']

    手順:
    1. 全word textを連結してフルテキスト復元
    2. fugashiで文節分割
    3. 文節ごとにタイミングを再割り当て（元のword境界を利用）

    Args:
        words: Whisperの単語リスト (word/start/end).

    Returns:
        文節単位に再結合された単語リスト.
    """
    if not words:
        return []

    # Step 1: 全テキスト復元（元の文字位置→タイミングマッピング作成）
    char_timings: list[dict] = []  # [{char, start, end}, ...]
    for w in words:
        text = w["word"]
        w_start = w["start"]
        w_end = w["end"]
        n = len(text)
        if n == 0:
            continue
        # 各文字に均等タイミング配分
        dur = w_end - w_start
        for ci, ch in enumerate(text):
            char_timings.append({
                "char": ch,
                "start": round(w_start + dur * ci / n, 3),
                "end": round(w_start + dur * (ci + 1) / n, 3),
            })

    if not char_timings:
        return words

    full_text = "".join(ct["char"] for ct in char_timings)

    # Step 2: fugashiで文節分割
    bunsetsu_list = _split_japanese_bunsetsu(full_text)

    if not bunsetsu_list:
        # fugashi失敗 → フォールバック: 4〜6文字ずつ切る
        chunk_size = 5
        bunsetsu_list = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]

    # Step 3: 文節→タイミング再割り当て
    result: list[dict] = []
    char_idx = 0
    for bunsetsu in bunsetsu_list:
        blen = len(bunsetsu)
        if char_idx + blen > len(char_timings):
            blen = len(char_timings) - char_idx
        if blen <= 0:
            continue

        b_start = char_timings[char_idx]["start"]
        b_end = char_timings[char_idx + blen - 1]["end"]
        result.append({
            "word": bunsetsu,
            "start": b_start,
            "end": b_end,
        })
        char_idx += blen

    logger.info("JA recombine: %d chars → %d bunsetsu (from %d whisper tokens)",
                len(char_timings), len(result), len(words))
    return result


def _is_number_or_unit(text: str) -> bool:
    """Check if text is a number, percentage, or unit that should stay together.

    Examples: "44%", "15%", "1000", "100만", "3조", "$500"

    Args:
        text: Word text to check.

    Returns:
        True if the text is a number/unit token.
    """
    import re
    return bool(re.match(r'^[\d,$\.]+[%만억조원달러위개년월일세]?$', text))


def group_words_into_phrases(words: list[dict], max_chars: int = 8) -> list[dict]:
    """Group word-level timestamps into short phrases for subtitle display.

    Produces phrases targeting 5-8 Korean characters per group, suitable
    for fast word-by-word subtitle transitions.

    Grouping rules:
        - Each phrase: target 2-8 characters (can exceed slightly for
          natural word boundaries)
        - Never break in the middle of a word
        - Numbers and key terms stay together ("44%", "15%")
        - Minimum phrase duration: 0.3 seconds
        - Maximum phrase duration: 2.0 seconds

    Args:
        words: List of word dicts: [{"word": str, "start": float, "end": float}].
        max_chars: Maximum characters per phrase (default 8).

    Returns:
        List of phrase dicts: [{"text": str, "start": float, "end": float}].
    """
    if not words:
        return []

    min_phrase_duration = 0.3
    max_phrase_duration = 2.0

    phrases = []
    current_text = ""
    current_start = words[0]["start"]
    current_end = words[0]["end"]

    for i, word in enumerate(words):
        word_text = word["word"]
        word_start = word["start"]
        word_end = word["end"]

        if not current_text:
            # Start a new phrase
            current_text = word_text
            current_start = word_start
            current_end = word_end
            continue

        # Calculate what the phrase would look like if we add this word
        candidate_text = current_text + " " + word_text
        # For character count, ignore spaces (Korean chars are the constraint)
        candidate_chars = len(candidate_text.replace(" ", ""))
        candidate_duration = word_end - current_start

        # Check if the next word is a number/unit that should stay with current
        next_is_number = _is_number_or_unit(word_text)
        current_ends_with_number = _is_number_or_unit(current_text.split()[-1]) if current_text else False

        # Decision: add to current phrase or start new one
        should_break = False

        if candidate_chars > max_chars + 3:
            # Way too long, must break
            should_break = True
        elif candidate_chars > max_chars:
            # Over limit -- break unless it's a number/unit pair
            if next_is_number and current_ends_with_number:
                should_break = False  # Keep number pairs together
            else:
                should_break = True
        elif candidate_duration > max_phrase_duration:
            # Duration too long
            should_break = True

        if should_break:
            # Finalize current phrase
            phrase_duration = current_end - current_start
            if phrase_duration < min_phrase_duration:
                current_end = current_start + min_phrase_duration
            phrases.append({
                "text": current_text,
                "start": current_start,
                "end": current_end,
            })
            # Start new phrase with this word
            current_text = word_text
            current_start = word_start
            current_end = word_end
        else:
            # Add word to current phrase
            current_text = candidate_text
            current_end = word_end

    # Finalize last phrase
    if current_text:
        phrase_duration = current_end - current_start
        if phrase_duration < min_phrase_duration:
            current_end = current_start + min_phrase_duration
        phrases.append({
            "text": current_text,
            "start": current_start,
            "end": current_end,
        })

    # Post-process: ensure no gaps between consecutive phrases cause visual jumps
    # (each phrase end should meet next phrase start)
    for i in range(len(phrases) - 1):
        if phrases[i]["end"] < phrases[i + 1]["start"]:
            # Small gap -- extend current phrase end to next phrase start
            gap = phrases[i + 1]["start"] - phrases[i]["end"]
            if gap < 0.15:
                phrases[i]["end"] = phrases[i + 1]["start"]

    return phrases


def format_ass_timestamp(seconds: float) -> str:
    """Format seconds as ASS timestamp H:MM:SS.cc (centiseconds).

    Args:
        seconds: Time in seconds (float).

    Returns:
        Formatted ASS timestamp string.
    """
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _hex_to_ass_bgr(hex_color: str) -> str:
    """Convert hex color (#RRGGBB) to ASS BGR format (&H00BBGGRR&).

    Args:
        hex_color: Hex color string like "#FFD000".

    Returns:
        ASS BGR color string like "&H0000D0FF&".
    """
    hc = hex_color.lstrip("#")
    if len(hc) == 6:
        return f"&H00{hc[4:6]}{hc[2:4]}{hc[0:2]}&"
    return "&H0000FFFF&"  # fallback yellow


def _clause_boundary_strength(word_text: str) -> int:
    """Detect clause/sentence boundary strength of a Korean word.

    Returns boundary strength:
        2 = strong (sentence endings, connectors) — always split
        1 = soft (particles, short endings) — split if group >= 8 chars
        0 = no boundary

    Args:
        word_text: Word text to check.

    Returns:
        Boundary strength (0, 1, or 2).

    Note:
        The genitive particle ``의`` is intentionally NOT listed as a soft
        boundary. "맨발의 소녀가" is a single noun-phrase unit — splitting
        between "맨발의" and "소녀가" was the exact failure flagged by the
        session 40 feedback ("맨발의/소녀가" banned). The post-pass
        ``_repair_semantic_groups`` provides a second guard, but keeping
        "의" out of soft_endings prevents the bad split from happening
        in the first place.
    """
    import re
    # Punctuation = strong
    if re.search(r'[.?!…]$', word_text):
        return 2

    # Strong boundaries: verb connectors and sentence endings
    strong_endings = (
        '니다', '습니다', '세요', '는데요', '거든요', '잖아요',
        '했다가', '했는데', '됐는데', '인데', '는데',
        '다가', '지만', '으면', '하면', '니까', '으니',
        '면서', '거든', '잖아', '더니',
        '해서', '라서', '돼서', '가지고', '갖고',
        '아슈', '았슈', '디유', '이유', '거여',
        '다', '요', '까', '죠', '고', '서', '며',
    )
    for ending in sorted(strong_endings, key=len, reverse=True):
        if word_text.endswith(ending):
            return 2

    # Soft boundaries: particles (조사) — split if group already long enough.
    # NOTE: "의" (genitive) is intentionally excluded; see docstring.
    soft_endings = (
        '에서', '으로', '부터', '까지', '처럼', '만큼',
        '에', '을', '를', '은', '는', '이', '가', '도', '만',
    )
    for ending in sorted(soft_endings, key=len, reverse=True):
        if word_text.endswith(ending) and len(word_text) >= 2:
            return 1

    return 0


# ---------------------------------------------------------------------------
# Semantic-unit protection for Korean subtitle grouping (FAIL-PROD-010)
# ---------------------------------------------------------------------------
#
# The greedy boundary grouping in `_group_words_for_ass` can still produce
# groups that technically satisfy the 12-char hard cap but break Korean
# modifier/head and dependent-noun relationships:
#
#     "기타큐슈, 형광등이" | "깜빡이는 복도를"          ← 주어-수식어 분리
#     "17살, 팔에 전기화상, 이" | "소녀가 …"            ← 관형사 고립
#     "… 사라진 채였을" | "겁니다."                    ← "~ㄹ 겁니다" 분리
#
# `_repair_semantic_groups` runs as a second pass and moves single boundary
# words across group boundaries (or merges adjacent groups) when they would
# otherwise break one of the following bindings. The pass is conservative:
# it only moves a word when the receiving group can absorb it within an
# elastic cap (14 chars) and never makes a group shorter than 1 char.
#
# Definitions (Korean):
#   - Forward binding: this word semantically attaches to the NEXT word,
#     so it must not be the last word of its group.
#       - 관형사 (determiner):   이/그/저/어떤/무슨/어느/모든/아무/다른/각/본/새/옛/온/순/맨
#       - 수사 (numeral):        한/두/세/네/다섯/여섯/일곱/여덟/아홉/열/스물/서른/마흔/쉰/…
#       - 관형형 어미 (adnominal): -는/-은/-ㄴ/-ㄹ/-던 (as a word ending, length >= 2)
#       - 관형격 조사 (genitive): -의 (as a word ending, length >= 2)
#
#   - Backward binding: this word semantically attaches to the PREVIOUS
#     word, so it must not be the first word of its group.
#       - 의존명사 (dependent noun): 것/수/줄/채/뻔/리/지/등/따위/무렵/당시/터/편/나름
#       - 의존명사 + 보조용언: 것이다/것입니다/것이었다/것을/것이/것은/수 있다/수 없다/
#                             줄 알았다/채였을/채였습니다/채였다/겁니다/거예요/거죠/거야
#       - 단위명사 (counter):      살/명/개/년/월/일/시/분/초/원/엔/달러/미터/킬로/평/만/억/조
#                                 (only when the previous word ends with a digit)

_DETERMINERS = frozenset([
    "이", "그", "저", "어떤", "무슨", "어느",
    "모든", "아무", "다른", "각", "본", "새", "옛", "온", "순", "맨",
])

_NUMERALS = frozenset([
    "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉",
    "열", "열한", "열두", "열셋", "열넷", "열다섯",
    "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔",
    "백", "천", "만",
])

_ADNOMINAL_ENDINGS = ("는", "은", "ㄴ", "ㄹ", "던")

_DEPENDENT_NOUNS = frozenset([
    "것", "수", "줄", "채", "뻔", "리", "지",
    "등", "따위", "무렵", "당시", "터", "편", "나름",
])

# Common dependent-noun + predicate bundles. Prefix match (word startswith).
# NOTE: "채였" (e.g. "채였을") is intentionally excluded because it is a
# bridge word — 관형형 어미 "-ㄹ" + 의존명사 "채" + 과거 "-였-" compound —
# and classifying it as pure backward binding causes an oscillation loop
# with Rule 2c where the word bounces between neighboring groups. The
# resulting split "사라진 | 채였을 겁니다" is acceptable; the repair pass
# only needs to guarantee "채였을 | 겁니다" never happens.
_DEPENDENT_PHRASE_PREFIXES = (
    "것이다", "것입니다", "것이었", "것을", "것이", "것은", "것도", "것만",
    "수 있", "수 없", "수있", "수없",
    "줄 알", "줄 몰",
    "채로", "채입", "채는",
    "겁니다", "겁니까", "거예", "거죠", "거야", "거다",
    "뻔했", "뻔합니",
)

_UNIT_NOUNS = frozenset([
    "살", "명", "개", "년", "월", "일", "시", "분", "초",
    "원", "엔", "달러", "미터", "킬로", "센티", "평", "만", "억", "조",
    "번", "회", "배", "퍼센트", "%",
])


def _is_forward_binding(word_text: str) -> bool:
    """True if this word semantically attaches to the next word.

    Used by the semantic-repair pass to detect when a word should not be
    the last member of its group.
    """
    if not word_text:
        return False
    stripped = word_text.rstrip(".,!?…·")  # strip trailing punctuation

    # 관형사/수사 단독
    if stripped in _DETERMINERS or stripped in _NUMERALS:
        return True

    # 관형격 조사 "의" 로 끝남 (2자 이상, 단독 "의" 제외)
    if len(stripped) >= 2 and stripped.endswith("의"):
        return True

    # 관형형 어미로 끝남 (2자 이상)
    if len(stripped) >= 2 and stripped.endswith(_ADNOMINAL_ENDINGS):
        return True

    return False


def _is_backward_binding(word_text: str, prev_word_text: str | None = None) -> bool:
    """True if this word semantically attaches to the previous word.

    Used by the semantic-repair pass to detect when a word should not be
    the first member of its group.

    Args:
        word_text: Current word.
        prev_word_text: Optional previous word (required for unit-noun
            disambiguation — "살" is only a counter when the prior word
            ends with a digit or is a Korean numeral).
    """
    if not word_text:
        return False
    stripped = word_text.rstrip(".,!?…·")

    # 의존명사 단독
    if stripped in _DEPENDENT_NOUNS:
        return True

    # 의존명사+술어 패턴 (startswith)
    for prefix in _DEPENDENT_PHRASE_PREFIXES:
        if stripped.startswith(prefix):
            return True

    # 단위명사 — 바로 앞 단어가 숫자나 수사일 때만
    if stripped in _UNIT_NOUNS and prev_word_text:
        prev_stripped = prev_word_text.rstrip(".,!?…·")
        if any(ch.isdigit() for ch in prev_stripped):
            return True
        if prev_stripped in _NUMERALS:
            return True
        # Korean native numeral endings are already covered above; also check
        # mixed forms like "열일곱" (열 + 일곱)
        for num in _NUMERALS:
            if prev_stripped.endswith(num):
                return True

    return False


def _group_chars(group: list[dict]) -> int:
    """Sum character count of a group, ignoring spaces in words."""
    return sum(len(w["word"].replace(" ", "")) for w in group)


def _repair_semantic_groups(
    groups: list[list[dict]],
    *,
    hard_max: int = 12,
    elastic_max: int = 14,
) -> list[list[dict]]:
    """Second pass that fixes modifier/head and dependent-noun splits.

    The first-pass greedy grouping can produce hard-max-compliant groups
    that still break Korean semantic units. This pass scans every group
    boundary once and repairs the following patterns by moving boundary
    words (or merging entire adjacent groups) while respecting
    ``elastic_max``:

        1. Last word of groups[i] is forward-binding (e.g. "이", "깜빡이는",
           "맨발의") → move that word to the front of groups[i+1].
        2. First word of groups[i+1] is backward-binding (e.g. "겁니다",
           "것입니다", "살" after a numeral) → move that word to the end
           of groups[i].
        3. If the donor group becomes empty, the next boundary is re-checked.

    Groups that cannot be repaired without exceeding ``elastic_max`` are
    left alone — failing the soft binding is better than producing an
    over-long unreadable group.

    Args:
        groups: Output of the first-pass grouping (``_group_words_for_ass``).
        hard_max: The 12-char cap used during first-pass grouping. Kept
            for documentation; this pass uses ``elastic_max``.
        elastic_max: The upper bound this pass will stretch to when
            merging/moving words. Default 14 — 2 chars of slack above
            ``hard_max`` which a single subtitle line can still render
            comfortably at the 50px base font.

    Returns:
        A new list of groups with semantic repairs applied.
    """
    if not groups or len(groups) < 2:
        return [list(g) for g in groups]

    # Work on a shallow copy of copies so we can mutate.
    repaired: list[list[dict]] = [list(g) for g in groups]

    # Oscillation guard: remember recent (boundary_index, rule) pairs to
    # prevent bouncing — e.g. pushing "채였을" to the right group, then
    # immediately having Rule 2a pull it back, forever. A boundary is
    # allowed at most ``max_repairs_per_boundary`` distinct repairs before
    # the pass moves on.
    repair_log: dict[int, int] = {}  # boundary_i -> repair count
    max_repairs_per_boundary = 2

    i = 0
    max_iterations = len(repaired) * 8  # safety to prevent infinite loops
    iteration = 0
    while i < len(repaired) - 1 and iteration < max_iterations:
        iteration += 1
        left = repaired[i]
        right = repaired[i + 1]

        if not left:
            del repaired[i]
            continue
        if not right:
            del repaired[i + 1]
            continue

        left_last = left[-1]["word"]
        right_first = right[0]["word"]
        right_second = right[1]["word"] if len(right) >= 2 else None

        left_chars = _group_chars(left)
        right_chars = _group_chars(right)
        left_last_chars = len(left_last.replace(" ", ""))
        right_first_chars = len(right_first.replace(" ", ""))

        moved = False

        # Rule 1: last word of left is forward-binding → move it into right.
        if _is_forward_binding(left_last):
            if right_chars + left_last_chars <= elastic_max:
                right.insert(0, left.pop())
                moved = True
            elif left_chars + right_chars <= elastic_max + 1:
                # 1b: total merge fallback — allow one extra char of slack
                # (16 when elastic_max=15) when a forward-binding chain
                # spans two groups that together fit on a single line.
                left.extend(right)
                del repaired[i + 1]
                moved = True
            elif len(right) >= 2:
                # 1c: pull right's first word into left so the modifier
                # (forward-binding word at left's end) is no longer
                # orphaned. The new left_last may itself be forward-
                # binding, in which case the next loop iteration will
                # try again — bounded by max_repairs_per_boundary so we
                # cannot oscillate forever. Used for cases like:
                #   left  = ["그는", "기타큐슈의"]   (8ch)
                #   right = ["좁은", "아파트로", "숨어듭니다."] (12ch)
                # where 1a / 1b both fail because right is too big to
                # absorb "기타큐슈의" but left can absorb "좁은".
                candidate = right[0]
                cand_chars = len(candidate["word"].replace(" ", ""))
                if left_chars + cand_chars <= elastic_max:
                    left.append(right.pop(0))
                    moved = True
            # else leave alone (over elastic cap)

        # Rule 2: first word of right is backward-binding → try to protect
        # the binding with progressively more aggressive repairs:
        #   2a. Move the single backward-binding word into left (if fits)
        #   2b. Total-merge left+right (if within backward_merge_cap)
        #   2c. Push one trailing word from left into right, so left frees
        #       up space for the bound pair to live in right
        elif _is_backward_binding(right_first, prev_word_text=left_last):
            # 2a: simple move into left
            if left_chars + right_first_chars <= elastic_max:
                left.append(right.pop(0))
                moved = True
            else:
                # 2b: total merge — strict elastic_max cap. We do NOT grant
                # an extra slack char here because Rule 2 can also trigger
                # Rule 2c (push trailing word) as a softer fallback; adding
                # slack would produce oversized fused lines like
                # "7명은 영원히 사라진 채였을 겁니다" (16ch) when 2c would
                # have split it cleanly at "사라진 | 채였을 겁니다".
                backward_merge_cap = elastic_max  # 15 when elastic_max=15
                if left_chars + right_chars <= backward_merge_cap:
                    left.extend(right)
                    del repaired[i + 1]
                    moved = True
                # 2c: push the trailing left word into right, if doing so
                # leaves left non-empty and right under elastic_max.
                elif len(left) >= 2:
                    candidate_pushed = left[-1]
                    new_left_chars = left_chars - len(candidate_pushed["word"].replace(" ", ""))
                    new_right_chars = right_chars + len(candidate_pushed["word"].replace(" ", ""))
                    if new_left_chars >= 1 and new_right_chars <= elastic_max:
                        right.insert(0, left.pop())
                        moved = True
                # else: give up — prefer "bad but readable" over over-long line

        # Clean up empty groups after moves
        if not left:
            del repaired[i]
            continue
        if not right:
            del repaired[i + 1]
            continue

        if moved:
            # Re-check this boundary (don't advance) in case another repair
            # is now needed, but stop if this boundary has already been
            # repaired too many times (oscillation guard).
            repair_log[i] = repair_log.get(i, 0) + 1
            if repair_log[i] >= max_repairs_per_boundary:
                i += 1
            continue

        i += 1

    return repaired


def _group_words_for_ass(words: list[dict], max_chars: int = 12) -> list[list[dict]]:
    """Group words into display groups by meaning units (의미 단위).

    Groups words at Korean clause/sentence boundaries for readable subtitles.
    Instead of splitting at arbitrary character counts, splits at natural
    language break points (verb endings, connectors, punctuation).

    Rules:
        - Strong boundary (strength=2): split if group >= 4 chars
        - Soft boundary (strength=1): split if group >= 8 chars
        - Force break above 16 chars at nearest word boundary
        - Groups < 4 chars are merged with adjacent groups

    Args:
        words: List of word dicts with "word", "start", "end".
        max_chars: Soft max chars per group (default 12).

    Returns:
        List of word groups (each group is a list of word dicts).
    """
    if not words:
        return []

    hard_max = 12  # 12자 넘으면 무조건 분리 (1줄 유지)
    soft_split_threshold = 7  # 7자 이상이면 soft boundary에서 분리
    min_chars = 4  # 4자 미만이면 다음과 합침

    groups: list[list[dict]] = []
    current_group: list[dict] = []
    current_chars = 0

    for word in words:
        word_text = word["word"]
        word_chars = len(word_text.replace(" ", ""))

        # PRE-APPEND hard_max check: close the current group BEFORE adding a
        # word that would push it over hard_max. Previous version appended
        # first and then compared — that allowed groups like the session 38
        # v3 cue[26] "오늘의 기록 기타큐슈 연쇄 감금살인" (15 chars) to form.
        if current_group and current_chars + word_chars > hard_max:
            groups.append(current_group)
            current_group = []
            current_chars = 0

        current_group.append(word)
        current_chars += word_chars

        # Soft boundary check (post-append, strength-based). Hard-max is
        # already guaranteed by the pre-append guard above, so we only look
        # at natural clause/sentence boundaries here.
        strength = _clause_boundary_strength(word_text)
        should_split = False
        if strength == 2 and current_chars >= min_chars:
            # Strong boundary — always split
            should_split = True
        elif strength == 1 and current_chars >= soft_split_threshold:
            # Soft boundary — split if enough chars accumulated
            should_split = True

        if should_split:
            groups.append(current_group)
            current_group = []
            current_chars = 0

    # Handle remaining words
    if current_group:
        if groups and current_chars < min_chars:
            groups[-1].extend(current_group)
        else:
            groups.append(current_group)

    # Second pass: semantic-unit protection. Fixes modifier/head and
    # dependent-noun splits that the greedy pass can still produce
    # within hard_max. See _repair_semantic_groups and FAIL-PROD-010.
    # elastic_max=15 gives 3 chars of slack above hard_max=12 so the
    # repair pass can keep modifier/head pairs together in a single
    # readable line; 15 characters at the 50px base font fit on a
    # single 1080px line without wrapping.
    groups = _repair_semantic_groups(groups, hard_max=hard_max, elastic_max=15)

    return groups


def _group_words_for_ass_en(words: list[dict], max_words: int = 7, max_chars: int = 40) -> list[list[dict]]:
    """Group English words into display groups for 2-line subtitles.

    Optimized for 1080px-wide vertical video (shorts) with 2-line display.
    Groups target ~1 sentence or meaning unit, fitting 2 lines.

    Rules:
        - Hard char limit: 40 chars per group (fits 2 lines at font 64)
        - Hard word limit: 7 words per group
        - Strong boundary (., ?, !, ...): always split
        - Comma boundary: split if >= 4 words
        - Never end with dangling article/preposition (the, a, an, of, in, to, etc.)
        - Groups < 2 words merged with adjacent (unless sentence boundary)

    Args:
        words: List of word dicts with "word", "start", "end".
        max_words: Max words per group (default 3).
        max_chars: Max characters per group (default 20).

    Returns:
        List of word groups.
    """
    import re

    if not words:
        return []

    dangling_words = {
        "the", "a", "an", "of", "in", "to", "for", "by", "on", "at",
        "with", "from", "into", "its", "is", "was", "are", "were", "no",
    }

    groups: list[list[dict]] = []
    current_group: list[dict] = []
    current_chars = 0

    def _group_text(grp):
        return " ".join(w["word"].strip() for w in grp)

    def _flush():
        nonlocal current_group, current_chars
        if not current_group:
            return
        # Anti-dangling: if last word is article/preposition, move to next group
        while len(current_group) > 1:
            last = current_group[-1]["word"].strip().lower().rstrip(".,!?")
            if last in dangling_words:
                dangling_word = current_group.pop()
                groups.append(current_group)
                current_group = [dangling_word]
                current_chars = len(dangling_word["word"].strip())
                return
            else:
                break
        groups.append(current_group)
        current_group = []
        current_chars = 0

    for word in words:
        word_text = word["word"].strip()
        word_len = len(word_text)

        # Force break: char limit or word limit BEFORE appending
        if current_group and (current_chars + 1 + word_len > max_chars or len(current_group) >= max_words):
            _flush()

        current_group.append(word)
        current_chars += (1 if current_chars > 0 else 0) + word_len

        # Strong boundary: sentence-ending punctuation
        if re.search(r'[.?!…]$', word_text):
            groups.append(current_group)
            current_group = []
            current_chars = 0
            continue

        # Comma boundary: split if ≥ 4 words
        if word_text.endswith(",") and len(current_group) >= 4:
            groups.append(current_group)
            current_group = []
            current_chars = 0
            continue

    # Remaining words
    if current_group:
        if groups and len(current_group) == 1:
            last_text = current_group[0]["word"].strip()
            # Only merge if combined won't exceed limits
            prev_text = _group_text(groups[-1])
            if len(prev_text) + 1 + len(last_text) <= max_chars + 5:
                groups[-1].extend(current_group)
            else:
                groups.append(current_group)
        else:
            groups.append(current_group)

    return groups


def words_to_remotion_json(
    words: list[dict],
    max_chars: int = 12,
    *,
    language: str = "ko",
) -> list[dict]:
    """Convert word-level timestamps to Remotion word-highlight JSON format.

    Produces the JSON structure consumed by ShortsVideo.tsx:
    [{"startMs": int, "endMs": int, "words": [str], "highlightIndex": int}]

    Each word in a display group gets its own cue where that word is highlighted.
    Group text stays visible for the entire group duration (no flicker).
    Groups are split at meaning boundaries (clause/sentence endings).

    Args:
        words: List of word dicts with "word", "start", "end" keys.
        max_chars: Soft max chars per display group (default 12).
        language: "ko" or "ja" — determines grouping algorithm.

    Returns:
        List of cue dicts for Remotion subtitles prop.
    """
    if language == "ja":
        groups = _group_words_for_ass_ja(words, max_chars=max_chars)
    elif language == "en":
        groups = _group_words_for_ass_en(words, max_words=7, max_chars=40)
    else:
        groups = _group_words_for_ass(words, max_chars=max_chars)
    cues: list[dict] = []

    for g_idx, group in enumerate(groups):
        group_words = [w["word"] for w in group]
        # Group boundary: from first word start to last word end
        group_end_ms = int(group[-1]["end"] * 1000)
        # Extend to next group start to eliminate gap (깜빡임 방지)
        if g_idx + 1 < len(groups):
            next_group_start = int(groups[g_idx + 1][0]["start"] * 1000)
            # If gap < 300ms, extend to next group (seamless transition)
            if next_group_start - group_end_ms < 300:
                group_end_ms = next_group_start

        for i, word in enumerate(group):
            word_start = int(word["start"] * 1000)
            # Each word cue: starts at word start, ends at next word start or group end
            if i + 1 < len(group):
                word_end = int(group[i + 1]["start"] * 1000)
            else:
                word_end = group_end_ms

            cues.append({
                "startMs": word_start,
                "endMs": word_end,
                "words": group_words,
                "highlightIndex": i,
            })

    return cues


def words_to_ass(
    words: list[dict],
    *,
    max_chars: int = 8,
    highlight_color: str = "#FFD000",
    font_name: str = "NanumSquare ExtraBold",
    font_size: int = 50,
    highlight_size: int = 58,
    outline_px: int = 4,
    shadow_px: int = 2,
    margin_v: int = 520,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """Generate ASS subtitle content with word-by-word color highlighting.

    Shows a group of words on screen, with the currently spoken word
    highlighted in a different color (default yellow) and slightly larger.
    Non-active words are white.

    Adapted from youtube-shorts-pipeline's ASS caption system, modified
    for Korean text and DESIGN_SPEC.md specifications.

    Args:
        words: List of word dicts: [{"word": str, "start": float, "end": float}].
        max_chars: Max characters per display group (default 8 for Korean).
        highlight_color: Hex color for active word (default "#FFD000" yellow).
        font_name: ASS font name (default "NanumSquare ExtraBold").
        font_size: Base font size in pixels (default 50).
        highlight_size: Font size for highlighted word (default 58).
        outline_px: Text outline thickness (default 4).
        shadow_px: Shadow offset (default 2).
        margin_v: Vertical margin from bottom in pixels (default 520 = ~73%).
        video_width: Video width (default 1080).
        video_height: Video height (default 1920).

    Returns:
        Complete ASS file content as string.
    """
    ass_highlight = _hex_to_ass_bgr(highlight_color)

    header = f"""[Script Info]
Title: Naberal Shorts Captions
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline_px},{shadow_px},2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    groups = _group_words_for_ass(words, max_chars=max_chars)
    events = []

    for group in groups:
        if not group:
            continue

        for active_idx, active_word in enumerate(group):
            start = format_ass_timestamp(active_word["start"])
            end = format_ass_timestamp(active_word["end"])

            parts = []
            for j, w in enumerate(group):
                if j == active_idx:
                    parts.append(
                        f"{{\\c{ass_highlight}\\b1\\fs{highlight_size}}}"
                        f"{w['word']}"
                        f"{{\\r}}"
                    )
                else:
                    parts.append(w["word"])

            text = " ".join(parts)
            events.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
            )

    return header + "\n".join(events) + "\n"


def phrases_to_srt(phrases: list[dict]) -> str:
    """Convert phrase list to SRT format string.

    Each phrase becomes one numbered SRT entry with start/end timestamps.

    Args:
        phrases: List of phrase dicts with "text", "start", "end" keys.

    Returns:
        Complete SRT file content as string.
    """
    srt_lines = []
    for i, phrase in enumerate(phrases, start=1):
        start_ts = format_srt_timestamp(phrase["start"])
        end_ts = format_srt_timestamp(phrase["end"])
        srt_lines.append(str(i))
        srt_lines.append(f"{start_ts} --> {end_ts}")
        srt_lines.append(phrase["text"])
        srt_lines.append("")

    return "\n".join(srt_lines)


def _load_whisper_model(model_size: str):
    """Load faster-whisper model with CUDA-first, CPU fallback.

    Tries GPU (CUDA float16) first, falls back to CPU (int8) on any error.
    This handles CUDA 13 vs CTranslate2 CUDA 12 compatibility issues on Windows.

    Args:
        model_size: Whisper model size (e.g., "large-v3", "medium").

    Returns:
        Loaded WhisperModel instance.
    """
    from faster_whisper import WhisperModel

    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        logger.info("Loaded faster-whisper model '%s' on CUDA", model_size)
        return model
    except Exception as e:
        logger.warning("CUDA failed (%s), falling back to CPU mode", e)

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    logger.info("Loaded faster-whisper model '%s' on CPU", model_size)
    return model


def _split_japanese_bunsetsu(text: str) -> list[str]:
    """일본어 텍스트를 문절(文節) 단위로 분리한다.

    MeCab 형태소 분석 후 조사/조동사를 이전 자립어에 붙여
    자연스러운 자막 표시 단위를 만든다.

    예: "現場に到着した" → ["現場に", "到着した"]

    Args:
        text: 일본어 텍스트.

    Returns:
        문절 단위 문자열 리스트.
    """
    try:
        import fugashi
    except ImportError:
        logger.warning("fugashi not installed, falling back to character split")
        # 폴백: 6자씩 단순 분리
        return [text[i:i + 6] for i in range(0, len(text), 6)] if text else []

    tagger = fugashi.Tagger()
    words = tagger(text)

    # 자립어(名詞/動詞/形容詞/副詞) 시작 시 새 문절, 부속어(助詞/助動詞)는 이전에 붙임
    _JIRITSU = {"名詞", "動詞", "形容詞", "副詞", "接続詞", "感動詞", "連体詞", "接頭辞"}
    bunsetsu_list: list[str] = []
    current = ""

    for word in words:
        pos = word.feature.pos1 if hasattr(word.feature, "pos1") else str(word.feature).split(",")[0]
        surface = word.surface

        if pos in _JIRITSU and current:
            bunsetsu_list.append(current)
            current = surface
        else:
            current += surface

    if current:
        bunsetsu_list.append(current)

    return bunsetsu_list


def _clause_boundary_strength_ja(word_text: str) -> int:
    """일본어 문절의 절/문장 경계 강도를 판별한다.

    Returns:
        2 = strong (문장 종결, 구두점)
        1 = soft (접속조사, 연용)
        0 = no boundary
    """
    import re
    if re.search(r'[。？！…]$', word_text):
        return 2
    strong_endings = ("た", "だ", "ない", "ます", "です", "である", "のだ", "ている")
    for ending in sorted(strong_endings, key=len, reverse=True):
        if word_text.endswith(ending):
            return 2
    soft_endings = ("が", "けど", "ので", "から", "ため", "として", "について")
    for ending in sorted(soft_endings, key=len, reverse=True):
        if word_text.endswith(ending):
            return 1
    return 0


def _group_words_for_ass_ja(words: list[dict], max_chars: int = 15) -> list[list[dict]]:
    """일본어 단어를 의미 단위로 그룹핑한다.

    Args:
        words: 단어 리스트 (word/start/end).
        max_chars: 그룹당 최대 글자수 (기본 15, 한자 압축률 높음).

    Returns:
        그룹별 단어 리스트.
    """
    if not words:
        return []

    hard_max = 15
    soft_split = 10
    min_chars = 3

    groups: list[list[dict]] = []
    current_group: list[dict] = []
    current_chars = 0

    for word in words:
        word_text = word["word"]
        word_chars = len(word_text.replace(" ", ""))

        # PRE-APPEND hard_max check (mirrors Korean grouping fix). Close the
        # current group before adding a word that would overflow hard_max.
        if current_group and current_chars + word_chars > hard_max:
            groups.append(current_group)
            current_group = []
            current_chars = 0

        current_group.append(word)
        current_chars += word_chars

        strength = _clause_boundary_strength_ja(word_text)
        should_split = False
        if strength == 2 and current_chars >= min_chars:
            should_split = True
        elif strength == 1 and current_chars >= soft_split:
            should_split = True

        if should_split:
            groups.append(current_group)
            current_group = []
            current_chars = 0

    if current_group:
        if groups and current_chars < min_chars:
            groups[-1].extend(current_group)
        else:
            groups.append(current_group)

    return groups


def generate_word_subtitles(
    audio_path: str,
    output_path: str,
    model_size: str = "large-v3",
    max_chars_per_line: int = 8,
    *,
    initial_prompt: str | None = None,
    language: str = "ko",
    script_path: str | None = None,
) -> dict:
    """Generate word/phrase-level SRT subtitles from audio.

    Main entry point.  Transcribes audio with word-level timestamps,
    groups words into short phrases, and writes SRT.

    Args:
        audio_path: Path to narration.mp3.
        output_path: Path to write output SRT file.
        model_size: faster-whisper model size (default "large-v3").
        max_chars_per_line: Max characters per subtitle line (default 8 for ko, 15 for ja).
        initial_prompt: Optional text hint for Whisper to improve recognition.
        language: Language code ("ko", "ja", or "en"). Japanese uses fugashi, English uses word-count grouping.

    Returns:
        Dict with keys: output_path, phrase_count, duration_seconds.

    Raises:
        FileNotFoundError: If audio_path does not exist.
        RuntimeError: If transcription fails.
    """
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info("Transcribing '%s' with model '%s' (word_timestamps=True, language=%s)", audio_path, model_size, language)
    if initial_prompt:
        logger.info("Using initial_prompt hint (%d chars): %s...", len(initial_prompt), initial_prompt[:80])

    # Transcribe kwargs — initial_prompt guides Whisper on expected vocabulary
    transcribe_kwargs: dict = {
        "language": language,
        "word_timestamps": True,
    }
    if initial_prompt:
        transcribe_kwargs["initial_prompt"] = initial_prompt

    # Load model and transcribe (CUDA → CPU fallback on runtime errors)
    model = _load_whisper_model(model_size)
    try:
        segments, info = model.transcribe(
            str(audio_file),
            **transcribe_kwargs,
        )
        segments_list = list(segments)
    except Exception as cuda_err:
        logger.warning("CUDA transcribe failed (%s), retrying on CPU", cuda_err)
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info("Reloaded model '%s' on CPU for retry", model_size)
        segments, info = model.transcribe(
            str(audio_file),
            **transcribe_kwargs,
        )
        segments_list = list(segments)

    if not segments_list:
        logger.warning("No segments returned from transcription")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text("", encoding="utf-8")
        return {
            "output_path": output_path,
            "phrase_count": 0,
            "duration_seconds": 0.0,
        }

    # Extract word-level timestamps from segments
    raw_words = _extract_words_from_segments(segments_list)
    logger.info("Extracted %d raw words from %d segments", len(raw_words), len(segments_list))

    # Merge words with very short duration (< 100ms)
    validated_words = _merge_short_duration_words(raw_words, min_duration=0.1)

    # Merge split numbers: "1" + ",701통" → "1,701통" (FAIL-PROD-020)
    validated_words = _merge_split_numbers(validated_words)
    logger.info("After merge: %d validated words", len(validated_words))

    # Japanese: re-combine single-character Whisper tokens into bunsetsu (文節)
    if language == "ja":
        validated_words = _recombine_ja_characters(validated_words)
        logger.info("After JA recombine: %d words", len(validated_words))

    # Script-based correction: align Whisper output to script.json narration
    # Fixes: 소름돋습니다→소름 돋습니다, 나스카라인→나스카 라인, 3000m→3천 미터
    if script_path:
        validated_words = _correct_from_script(validated_words, script_path)
        logger.info("After script correction: %d words", len(validated_words))

    # Group into phrases (의미 단위 그룹핑)
    if language == "ja":
        effective_max = max(max_chars_per_line, 15)
    elif language == "en":
        effective_max = max(max_chars_per_line, 30)
    else:
        effective_max = max(max_chars_per_line, 12)
    phrases = group_words_into_phrases(validated_words, max_chars=effective_max)
    logger.info("Grouped into %d phrases (max_chars=%d)", len(phrases), max_chars_per_line)

    # Convert to SRT
    srt_content = phrases_to_srt(phrases)

    # Write SRT output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(srt_content, encoding="utf-8")

    # Generate ASS with word-level highlight (alongside SRT)
    ass_output_path = str(Path(output_path).with_suffix(".ass"))
    ass_content = words_to_ass(validated_words, max_chars=max_chars_per_line)
    Path(ass_output_path).write_text(ass_content, encoding="utf-8")
    logger.info("ASS word-highlight subtitles written: %s", ass_output_path)

    # Generate Remotion word-highlight JSON (alongside SRT/ASS)
    remotion_json_path = str(Path(output_path).with_name("subtitles_remotion.json"))
    remotion_max = 15 if language == "ja" else (30 if language == "en" else max_chars_per_line)
    remotion_cues = words_to_remotion_json(validated_words, max_chars=remotion_max, language=language)
    Path(remotion_json_path).write_text(
        json.dumps(remotion_cues, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("Remotion word-highlight JSON written: %s (%d cues)", remotion_json_path, len(remotion_cues))

    # Calculate total duration
    duration = 0.0
    if phrases:
        duration = phrases[-1]["end"] - phrases[0]["start"]
    elif hasattr(info, "duration") and info.duration:
        duration = info.duration

    result = {
        "output_path": output_path,
        "ass_path": ass_output_path,
        "remotion_json_path": remotion_json_path,
        "phrase_count": len(phrases),
        "duration_seconds": round(duration, 3),
    }

    logger.info("Word subtitles generated: %s", json.dumps(result, ensure_ascii=False))
    return result


def main():
    """CLI entry point for word_subtitle.py."""
    parser = argparse.ArgumentParser(
        description="Generate word/phrase-level SRT subtitles from narration audio"
    )
    parser.add_argument(
        "--audio", required=True,
        help="Path to narration.mp3 audio file",
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to write output subtitles.srt",
    )
    parser.add_argument(
        "--max-chars", type=int, default=8,
        help="Max Korean characters per subtitle line (default: 8)",
    )
    parser.add_argument(
        "--model", default="large-v3",
        help="faster-whisper model size (default: large-v3)",
    )
    parser.add_argument(
        "--script",
        help="Path to script.json for Whisper correction (fixes spacing/numbers)",
    )
    parser.add_argument(
        "--language", default="ko",
        choices=["ko", "ja", "en"],
        help="Language code for Whisper transcription and grouping (default: ko)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Validate input
    if not Path(args.audio).exists():
        print(
            json.dumps({"error": f"Input audio file not found: {args.audio}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    # Generate
    try:
        result = generate_word_subtitles(
            audio_path=args.audio,
            output_path=args.output,
            model_size=args.model,
            max_chars_per_line=args.max_chars,
            script_path=args.script,
            language=args.language,
        )
    except Exception as e:
        print(
            json.dumps({"error": f"Subtitle generation failed: {e}"}),
            file=sys.stderr,
        )
        sys.exit(2)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
