"""Shape regression for korean_speech_samples.json — SUBT-02 + CONTENT-02 (Phase 4 Wave 0)."""
from __future__ import annotations


def test_positive_10_all_pass(korean_samples):
    pos = korean_samples["positive"]
    assert len(pos) >= 10, f"positive count {len(pos)} < 10"
    for entry in pos:
        assert entry.get("expected_verdict") == "PASS", f"bad positive: {entry}"


def test_negative_10_all_fail(korean_samples):
    neg = korean_samples["negative"]
    assert len(neg) >= 10, f"negative count {len(neg)} < 10"
    for entry in neg:
        assert entry.get("expected_verdict") == "FAIL", f"bad negative: {entry}"


def test_negative_has_reason(korean_samples):
    for entry in korean_samples["negative"]:
        reason = entry.get("reason", "")
        assert isinstance(reason, str) and len(reason) > 0, (
            f"negative entry missing/empty reason: {entry}"
        )


def test_positive_has_speaker_and_register(korean_samples):
    for entry in korean_samples["positive"]:
        assert entry.get("speaker") in ("detective", "assistant"), f"bad speaker: {entry}"
        assert entry.get("register") in ("하오체", "해요체"), f"bad register: {entry}"
