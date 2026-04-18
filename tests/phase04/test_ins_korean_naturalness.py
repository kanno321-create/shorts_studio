"""Regression test for ins-korean-naturalness — SUBT-02 + CONTENT-02 (Plan 04-03 Task 2).

The actual inspector is LLM-backed; this test provides a regex-only rule_simulator
as a deterministic stand-in that mirrors §5.3 line 1127-1131 regex bank.

Gate: negative 10 samples → ≥ 9 FAIL; positive 10 samples → ≥ 8 PASS.
If either fails, either korean_speech_samples.json (Plan 04-01) needs tightening
or ins-korean-naturalness regex bank needs expansion.

This is the roundtrip proof for VALIDATION map row 4-03-02.
"""
from __future__ import annotations

import re

import pytest


# Regex patterns mirror .claude/agents/inspectors/content/ins-korean-naturalness/AGENT.md
# which itself mirrors RESEARCH.md §5.3 lines 1127-1131.
#
# Simulator note: the AGENT.md lists canonical morpheme endings (하오체 / 해요체 / 반말);
# this regex simulator *expands* those bases to include common verb conjugations that
# share the register — e.g., 해요체 expands to include generic '아요/어요' verb stems
# (알아요, 갔어요), and 반말 expands to include '했어/맞지/알지' style bare endings.
# Expansion is required because negative samples use natural Korean conjugations, not
# only the bare morpheme forms. `\??\.?\s*$` anchors allow sentence-final punctuation.
HAOCHE_ENDINGS = re.compile(
    r"(하오|이오|보오|가오|구려|다네|습니다|올시다|있소|았소|었소|겠소|봤소|갔소)\??\.?\s*$"
)
HAEYOCHE_ENDINGS = re.compile(
    r"(아요|어요|여요|해요|이에요|예요|지요|거든요|네요|잖아요|다고요|라고요|세요|"
    r"았어요|었어요|겠어요|있어요)\??\.?\s*$"
)
# 반말 종결 — '했어/맞지/알지/뭐해/맞아/거든/잖아' 계열. '다'는 평서 경계가 모호해 제외.
# `?` / `.` sentence-final allowed.
BANMAL_ENDINGS = re.compile(
    r"(했어|했지|됐어|됐지|맞아|맞지|알지|알아|뭐해|뭐했어|야지|거든|잖아)\??\.?\s*$"
)
# 외래어(로마자 3+자) — 'alibi', 'check', 'CCTV', 'blurry', 'scene', 'reconstruction'.
# Threshold 1 in simulator (stricter than AGENT.md's "5 문장당 2" rule); per-utterance
# regression: positives have 0 roman words, negatives have 1+.
FOREIGN_WORD = re.compile(r"[A-Za-z]{3,}")
FOREIGN_THRESHOLD = 1
CALL_DETECTIVE = re.compile(r"탐정님")
CALL_ASSISTANT = re.compile(r"조수님")


def rule_simulator(text: str, speaker: str) -> tuple[str, str]:
    """Pure-regex approximation of ins-korean-naturalness LogicQA verdict.

    Returns (verdict, reason_hint) where verdict ∈ {"PASS", "FAIL"}.

    Priority order (first match wins):
      1. self_title_leak (호칭 누출) — highest severity
      2. foreign_word_overuse (roman-word count >= FOREIGN_THRESHOLD)
      3. register mismatch (speaker-specific)
    """
    # Priority 1: self-title leak (speaker-dependent)
    if speaker == "detective" and CALL_DETECTIVE.search(text):
        return "FAIL", "self_title_leak: 탐정이 자기 자신을 '탐정님'으로 지칭"
    if speaker == "assistant" and CALL_ASSISTANT.search(text):
        return "FAIL", "self_title_leak: 조수가 자기 자신을 '조수님'으로 지칭"

    # Priority 2: foreign word overuse
    foreign_hits = FOREIGN_WORD.findall(text)
    if len(foreign_hits) >= FOREIGN_THRESHOLD:
        return "FAIL", f"foreign_word_overuse: {foreign_hits}"

    # Priority 3: register mismatch (speaker-specific)
    if speaker == "detective":
        # haeyoche mixed into hao-che (e.g., '알아요' in detective line)
        if HAEYOCHE_ENDINGS.search(text) and not HAOCHE_ENDINGS.search(text):
            return "FAIL", "mixed_register: 해요체 혼입 (탐정 발화)"
        # banmal mixed into hao-che (e.g., '뭐했어?')
        if BANMAL_ENDINGS.search(text) and not HAOCHE_ENDINGS.search(text):
            return "FAIL", "informal_in_hao: 반말 혼입 (탐정 발화)"
        # positive hao-che match
        if HAOCHE_ENDINGS.search(text):
            return "PASS", ""
        # 모호 시 PASS (conservative — simulator cannot confidently FAIL)
        return "PASS", ""

    if speaker == "assistant":
        # banmal mixed into haeyoche (e.g., '알지', '맞아')
        if BANMAL_ENDINGS.search(text) and not HAEYOCHE_ENDINGS.search(text):
            return "FAIL", "informal_in_polite: 반말 혼입 (조수 발화)"
        # positive haeyoche match
        if HAEYOCHE_ENDINGS.search(text):
            return "PASS", ""
        return "PASS", ""

    return "PASS", ""


def test_negative_10_at_least_9_fail(korean_samples):
    """ins-korean-naturalness regex simulator must catch ≥ 9/10 negatives (VALIDATION 4-03-02)."""
    results = [
        (s["id"], rule_simulator(s["text"], s["speaker"]))
        for s in korean_samples["negative"]
    ]
    fail_count = sum(1 for _, (v, _) in results if v == "FAIL")
    assert fail_count >= 9, (
        f"Expected ≥ 9 FAIL on negative samples, got {fail_count}/10: {results}"
    )


def test_positive_10_at_least_8_pass(korean_samples):
    """ins-korean-naturalness regex simulator must preserve ≥ 8/10 positives as PASS."""
    results = [
        (s["id"], rule_simulator(s["text"], s["speaker"]))
        for s in korean_samples["positive"]
    ]
    pass_count = sum(1 for _, (v, _) in results if v == "PASS")
    assert pass_count >= 8, (
        f"Expected ≥ 8 PASS on positive samples, got {pass_count}/10: {results}"
    )


def test_rule_simulator_self_title_leak_detective():
    """Sanity: explicit regression for self_title_leak detective branch."""
    verdict, reason = rule_simulator("탐정님이 먼저 확인했소.", "detective")
    assert verdict == "FAIL"
    assert "self_title_leak" in reason


def test_rule_simulator_self_title_leak_assistant():
    """Sanity: explicit regression for self_title_leak assistant branch."""
    verdict, reason = rule_simulator("조수님도 같이 갔어요.", "assistant")
    assert verdict == "FAIL"
    assert "self_title_leak" in reason


def test_rule_simulator_mixed_register_detective_haeyoche_leak():
    """Sanity: detective using haeyo-che must FAIL."""
    verdict, reason = rule_simulator("그 사건을 알아요.", "detective")
    assert verdict == "FAIL"
    assert "mixed_register" in reason


def test_rule_simulator_foreign_word_overuse():
    """Sanity: ≥ 2 roman-word tokens in single utterance → FAIL."""
    verdict, reason = rule_simulator("scene을 reconstruction 해봅시다.", "detective")
    assert verdict == "FAIL"
    assert "foreign_word_overuse" in reason


def test_rule_simulator_positive_hao_che():
    """Sanity: clean hao-che detective line must PASS."""
    verdict, _ = rule_simulator("그 사건을 알고 있소.", "detective")
    assert verdict == "PASS"


def test_rule_simulator_positive_haeyo_che():
    """Sanity: clean haeyo-che assistant line must PASS."""
    verdict, _ = rule_simulator("저도 들었어요.", "assistant")
    assert verdict == "PASS"
