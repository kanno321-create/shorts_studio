"""Phase 4 Plan 04-07 Task 2 — AF-5 real-face block-rate smoke test.

Simulates ins-mosaic's regex-based blocklist logic against
`.claude/agents/_shared/af_bank.json["af5_real_face"]` and asserts that:

- Every AF-5 entry with expected_verdict=FAIL is blocked (domain OR keyword hit).
- Every AF-5 entry with expected_verdict=PASS is NOT blocked.
- Block rate on FAIL entries == 100%.

This is the regression baseline for the COMPLY-05 hard gate.
"""
from __future__ import annotations

import re

import pytest

# Mirror ins-mosaic domain + keyword regex (kept in sync with AGENT.md blocklist)
KOREAN_PRESS_DOMAINS = re.compile(
    r"(chosun\.com|joongang\.co\.kr|donga\.com|hani\.co\.kr|"
    r"mbc\.co\.kr|imbc\.com|kbs\.co\.kr|sbs\.co\.kr|jtbc\.co\.kr|"
    r"news\.naver\.com|news\.daum\.net|yna\.co\.kr|news1\.kr|news\.joins\.com)",
    re.IGNORECASE,
)
REAL_FACE_KEYWORDS = re.compile(
    r"(news|victim|press-photo|press_photo|실존|피해자|real_person|accident)",
    re.IGNORECASE,
)


def af5_blocked(entry: dict) -> bool:
    """Return True if ins-mosaic regex simulator would block this entry."""
    url = entry.get("url_pattern", "")
    caption = entry.get("caption", "")
    full_text = f"{url} {caption}"
    if KOREAN_PRESS_DOMAINS.search(full_text):
        return True
    if REAL_FACE_KEYWORDS.search(full_text):
        return True
    return False


@pytest.fixture(scope="module")
def af5_entries(af_bank):
    assert "af5_real_face" in af_bank, "af_bank.json missing af5_real_face key"
    entries = af_bank["af5_real_face"]
    assert len(entries) >= 10, (
        f"af5_real_face must have ≥10 entries (COMPLY-05 baseline), got {len(entries)}"
    )
    return entries


def test_af5_fail_entries_100pct_blocked(af5_entries):
    """Every expected_verdict=FAIL entry must be blocked by the regex simulator."""
    fail_entries = [e for e in af5_entries if e.get("expected_verdict") == "FAIL"]
    assert len(fail_entries) >= 10, (
        f"AF-5 must include ≥10 FAIL samples, got {len(fail_entries)}"
    )
    blocked = [e for e in fail_entries if af5_blocked(e)]
    missed = [e["id"] for e in fail_entries if not af5_blocked(e)]
    assert len(blocked) == len(fail_entries), (
        f"AF-5 block rate {len(blocked)}/{len(fail_entries)} != 100% — missed: {missed}"
    )


def test_af5_pass_entries_not_blocked(af5_entries):
    """AI-generated whitelist entries (expected_verdict=PASS) must NOT be blocked."""
    pass_entries = [e for e in af5_entries if e.get("expected_verdict") == "PASS"]
    assert len(pass_entries) >= 1, "AF-5 must include ≥1 PASS sample (AI-generated whitelist)"
    wrongly_blocked = [e["id"] for e in pass_entries if af5_blocked(e)]
    assert not wrongly_blocked, (
        f"AF-5 PASS entries wrongly blocked (false-positive): {wrongly_blocked}"
    )


def test_af5_overall_block_rate_invariant(af5_entries):
    """Aggregate invariant: blocked == #FAIL, not_blocked == #PASS."""
    expected_blocked = sum(1 for e in af5_entries if e.get("expected_verdict") == "FAIL")
    actual_blocked = sum(1 for e in af5_entries if af5_blocked(e))
    assert actual_blocked == expected_blocked, (
        f"AF-5 block-rate invariant violated: "
        f"expected blocked={expected_blocked}, actual={actual_blocked}"
    )
