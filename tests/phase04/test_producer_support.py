"""Phase 4 Wave 4 — Producer Support 5 compliance tests (plan 04-09).

Enforces contract for the 5 Producer Support AGENT.md files:
    - voice-producer      (AUDIO-01, AUDIO-03, AF-4 2차 방어)
    - asset-sourcer       (AUDIO-02 하이브리드 오디오, AUDIO-04 whitelist)
    - assembler           (Remotion composition spec, Phase 5 경계)
    - thumbnail-designer  (14자 text overlay, AF-5 2차 방어)
    - publisher           (YouTube Data API v3, AI disclosure, Selenium 금지)

All tests must PASS (no skip, no xfail).
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402

PRODUCERS_DIR = _REPO_ROOT / ".claude/agents/producers"

EXPECTED_SUPPORT_NAMES = {
    "voice-producer",
    "asset-sourcer",
    "assembler",
    "thumbnail-designer",
    "publisher",
}


def _load(name: str):
    path = PRODUCERS_DIR / name / "AGENT.md"
    meta, body = parse_frontmatter(path)
    return path, meta, body


@pytest.fixture(scope="module")
def support_agents():
    return {name: _load(name) for name in EXPECTED_SUPPORT_NAMES}


# -----------------------------------------------------------------------------
# Test 1 — all 5 Producer Support AGENT.md exist
# -----------------------------------------------------------------------------
def test_all_5_support_producers_exist(support_agents):
    for name in EXPECTED_SUPPORT_NAMES:
        path = PRODUCERS_DIR / name / "AGENT.md"
        assert path.exists(), f"Missing Producer Support AGENT.md: {name}"


# -----------------------------------------------------------------------------
# Test 2 — frontmatter role=producer, category=support, maxTurns=3
# -----------------------------------------------------------------------------
def test_frontmatter_role_category_maxturns(support_agents):
    for name, (path, meta, _body) in support_agents.items():
        assert meta.get("role") == "producer", (
            f"{name}: role={meta.get('role')!r}, expected 'producer'"
        )
        assert meta.get("category") == "support", (
            f"{name}: category={meta.get('category')!r}, expected 'support'"
        )
        max_turns = int(meta.get("maxTurns", "0"))
        assert max_turns == 3, (
            f"{name}: maxTurns={max_turns}, expected 3 (RUB-05 standard)"
        )


# -----------------------------------------------------------------------------
# Test 3 — voice-producer AUDIO-01 + AUDIO-03 + AF-4 2차 방어
# -----------------------------------------------------------------------------
def test_voice_producer_audio_01_03_af4(support_agents):
    _path, _meta, body = support_agents["voice-producer"]

    # AUDIO-01: Typecast primary + ElevenLabs fallback
    assert "Typecast" in body, "voice-producer missing 'Typecast' (AUDIO-01)"
    assert "ElevenLabs" in body, "voice-producer missing 'ElevenLabs' (AUDIO-01 fallback)"

    # AUDIO-03: 7 emotion enum
    emotions = ["neutral", "tense", "sad", "happy", "urgent", "mysterious", "empathetic"]
    body_lower = body.lower()
    missing = [e for e in emotions if e not in body_lower]
    assert not missing, f"voice-producer missing emotions (AUDIO-03): {missing}"

    # AF-4 2차 방어
    assert "AF-4" in body, "voice-producer missing 'AF-4' (AF-4 2차 방어)"


# -----------------------------------------------------------------------------
# Test 4 — asset-sourcer AUDIO-02 하이브리드 + AUDIO-04 whitelist
# -----------------------------------------------------------------------------
def test_asset_sourcer_audio_02_04_whitelist(support_agents):
    _path, _meta, body = support_agents["asset-sourcer"]

    # AUDIO-04 whitelist 4 domains
    whitelist = ["Epidemic Sound", "Artlist", "YouTube Audio Library", "Free Music Archive"]
    missing = [w for w in whitelist if w not in body]
    assert not missing, f"asset-sourcer whitelist missing (AUDIO-04): {missing}"

    # AUDIO-02 하이브리드: 3-5s crossfade
    assert "crossfade" in body.lower(), "asset-sourcer missing 'crossfade' (AUDIO-02)"
    assert "3" in body and "5" in body, "asset-sourcer missing '3'/'5' duration range (AUDIO-02)"


# -----------------------------------------------------------------------------
# Test 5 — publisher YouTube Data API v3 + AI disclosure + Selenium 금지
# -----------------------------------------------------------------------------
def test_publisher_youtube_api_disclosure_selenium_block(support_agents):
    _path, _meta, body = support_agents["publisher"]

    assert "YouTube Data API v3" in body, (
        "publisher missing 'YouTube Data API v3' (PUB-01)"
    )
    assert "AI disclosure" in body, "publisher missing 'AI disclosure' (PUB-02)"
    assert "Selenium" in body, "publisher missing 'Selenium' (AF-8 금지 명시)"
    # 48시간 publish lock + KST peak 윈도우
    assert "48" in body, "publisher missing '48' (PUB-03 lock)"
    assert ("평일 20-23" in body or "peak" in body.lower() or "20:00-23:00" in body), (
        "publisher missing peak KST 윈도우 (PUB-04)"
    )


# -----------------------------------------------------------------------------
# Test 6 — thumbnail-designer AF-5 2차 방어 + 실존 인물명 caption 차단
# -----------------------------------------------------------------------------
def test_thumbnail_designer_af5_real_person_block(support_agents):
    _path, _meta, body = support_agents["thumbnail-designer"]

    assert "AF-5" in body, "thumbnail-designer missing 'AF-5' 2차 방어"
    # 실존 인물명 caption 금지 (AF-4 bank 참조)
    assert "real_person" in body.lower() or "실존 인물" in body, (
        "thumbnail-designer missing 실존 인물명 caption 금지 지시"
    )
    # af_bank.json 연계
    assert "af_bank" in body.lower(), "thumbnail-designer missing af_bank.json reference"


# -----------------------------------------------------------------------------
# Test 7 — assembler Phase 4/5 경계 명시 (Remotion CLI는 Phase 5)
# -----------------------------------------------------------------------------
def test_assembler_phase4_5_boundary(support_agents):
    _path, _meta, body = support_agents["assembler"]

    assert "Remotion" in body, "assembler missing 'Remotion' (composition spec)"
    # Phase 4는 스펙만. 실 CLI 호출은 Phase 5 (MUST REMEMBER rule 5)
    assert "Phase 5" in body, "assembler missing 'Phase 5' 경계 명시"
    assert ("composition" in body.lower()), "assembler missing 'composition' terminology"


# -----------------------------------------------------------------------------
# Test 8 — all 5 have MUST REMEMBER in final 40% of body (AGENT-09)
# -----------------------------------------------------------------------------
def test_must_remember_in_final_40_percent(support_agents):
    for name, (path, _meta, body) in support_agents.items():
        lines = body.splitlines()
        total = len(lines)
        assert total > 0, f"{name}: empty body"
        found_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("## MUST REMEMBER"):
                found_idx = i
                break
        assert found_idx >= 0, f"{name}: '## MUST REMEMBER' header not found"
        ratio_from_end = (total - found_idx) / total
        assert ratio_from_end <= 0.4, (
            f"{name}: MUST REMEMBER ratio_from_end={ratio_from_end:.3f}, "
            f"expected ≤ 0.4 (AGENT-09)"
        )
