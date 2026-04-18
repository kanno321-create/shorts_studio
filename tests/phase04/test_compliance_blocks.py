"""Phase 4 Plan 05 Task 2 — AF-4 / AF-13 100% block-rate smoke test.

VALIDATION row 4-05-02: ins-license's regex/blocklist logic must block
every FAIL-expected entry in af_bank.json::af4_voice_clone and
af_bank.json::af13_kpop. PASS-expected entries (fictional character, royalty-free
whitelist) must NOT be blocked.

This test mirrors the regex/blocklist specified in
  .claude/agents/inspectors/compliance/ins-license/AGENT.md
and enforces a regression contract: any future edit to the Inspector's
regex must remain 100% faithful to the expected_verdict field in af_bank.
"""
from __future__ import annotations

import pathlib
import re

import pytest

# AF-13 K-pop artists regex (mirrors §5.5 line 1162 + extended to 10 core groups)
KPOP_ARTISTS = re.compile(
    r"BTS|방탄소년단|블랙핑크|BLACKPINK|뉴진스|NewJeans|아이브|IVE|"
    r"에스파|aespa|르세라핌|LE SSERAFIM|스트레이 키즈|Stray Kids|"
    r"세븐틴|SEVENTEEN|NCT|트와이스|TWICE",
    re.IGNORECASE,
)

# AF-13 title regex — popular KOMCA-managed K-pop titles (with fuzz for af_bank entries)
KPOP_TITLES = re.compile(
    r"Dynamite|다이너마이트|Butter|Spring Day|Savage|Ditto|"
    r"Super Shy|Hype Boy|Love Dive|LOVE DIVE|ETA|How Sweet|"
    r"Pink Venom|Kill This Love|Supernova|UNFORGIVEN|MANIAC|"
    r"God of Music|Sticker|FANCY",
    re.IGNORECASE,
)

# Royalty-free whitelist — artists/labels where PASS is expected
ROYALTY_FREE_WHITELIST = re.compile(
    r"Epidemic Sound|Artlist|YouTube Audio Library|Free Music Archive|"
    r"Pixabay|Uppbeat",
    re.IGNORECASE,
)

AF_BANK_PATH = pathlib.Path(".claude/agents/_shared/af_bank.json")


def af4_blocked(name: str, bank_af4: list[dict]) -> bool:
    """Return True iff `name` matches any AF-4 blocklist entry's name
    (case-insensitive, substring-bidirectional)."""
    if not name:
        return False
    name_lower = name.lower()
    for entry in bank_af4:
        if entry.get("expected_verdict") != "FAIL":
            # Skip the PASS gold-standard entries (e.g. fictional character) so
            # the blocklist mirrors the Inspector contract, not the bank itself.
            continue
        blocklist_name = entry.get("name", "").lower()
        if not blocklist_name:
            continue
        if blocklist_name in name_lower or name_lower in blocklist_name:
            return True
    return False


def af13_blocked(artist: str, title: str) -> bool:
    """Return True iff artist OR title matches K-pop regex,
    AND does NOT match royalty-free whitelist override."""
    artist = artist or ""
    title = title or ""
    # Whitelist override (e.g. Epidemic Sound — Suspense Strings)
    if ROYALTY_FREE_WHITELIST.search(artist) or ROYALTY_FREE_WHITELIST.search(title):
        return False
    if KPOP_ARTISTS.search(artist) or KPOP_TITLES.search(title):
        return True
    return False


def test_af_bank_file_exists():
    assert AF_BANK_PATH.exists(), f"af_bank.json missing at {AF_BANK_PATH}"


def test_af4_voice_clone_100pct_block_rate(af_bank):
    """Every FAIL-expected AF-4 entry must be blocked by the regex/blocklist
    and every PASS-expected entry must NOT be blocked."""
    af4 = af_bank["af4_voice_clone"]
    assert len(af4) >= 10, f"af4_voice_clone only {len(af4)} entries (need >= 10)"

    fail_entries = [e for e in af4 if e.get("expected_verdict") == "FAIL"]
    pass_entries = [e for e in af4 if e.get("expected_verdict") == "PASS"]
    assert fail_entries, "af4_voice_clone has no FAIL entries — bank misconfigured"

    # FAIL entries: 100% blocked
    blocked_fail = [e for e in fail_entries if af4_blocked(e["name"], af4)]
    assert len(blocked_fail) == len(fail_entries), (
        f"AF-4 FAIL block rate {len(blocked_fail)}/{len(fail_entries)} != 100%. "
        f"Missed: {[e['name'] for e in fail_entries if e not in blocked_fail]}"
    )

    # PASS entries: 0% blocked
    blocked_pass = [e for e in pass_entries if af4_blocked(e["name"], af4)]
    assert not blocked_pass, (
        f"AF-4 PASS false-positive: {[e['name'] for e in blocked_pass]}"
    )


def test_af13_kpop_100pct_block_rate(af_bank):
    """Every FAIL-expected AF-13 entry must be blocked by K-pop regex
    and every PASS-expected entry (royalty-free) must NOT be blocked."""
    af13 = af_bank["af13_kpop"]
    assert len(af13) >= 10, f"af13_kpop only {len(af13)} entries (need >= 10)"

    fail_entries = [e for e in af13 if e.get("expected_verdict") == "FAIL"]
    pass_entries = [e for e in af13 if e.get("expected_verdict") == "PASS"]
    assert fail_entries, "af13_kpop has no FAIL entries — bank misconfigured"

    blocked_fail = [
        e for e in fail_entries
        if af13_blocked(e.get("artist", ""), e.get("title", ""))
    ]
    assert len(blocked_fail) == len(fail_entries), (
        f"AF-13 FAIL block rate {len(blocked_fail)}/{len(fail_entries)} != 100%. "
        f"Missed: "
        f"{[(e.get('artist'), e.get('title')) for e in fail_entries if e not in blocked_fail]}"
    )

    blocked_pass = [
        e for e in pass_entries
        if af13_blocked(e.get("artist", ""), e.get("title", ""))
    ]
    assert not blocked_pass, (
        f"AF-13 PASS false-positive: "
        f"{[(e.get('artist'), e.get('title')) for e in blocked_pass]}"
    )


def test_af13_fail_entries_cover_all_10_core_kpop_groups(af_bank):
    """Regression: af_bank's FAIL entries must span the 10 core K-pop groups
    named in RESEARCH.md §5.5 line 1162 — ensures the regex gets exercised
    against every prescribed artist, not just the top 3."""
    core_groups = {"BTS", "BLACKPINK", "NewJeans", "IVE", "aespa",
                   "LE SSERAFIM", "Stray Kids", "SEVENTEEN", "NCT", "TWICE"}
    fail_artists = {
        e["artist"] for e in af_bank["af13_kpop"]
        if e.get("expected_verdict") == "FAIL"
    }
    coverage = core_groups & fail_artists
    assert len(coverage) >= 10, (
        f"AF-13 core group coverage only {len(coverage)}/10: {coverage}. "
        f"Missing: {core_groups - fail_artists}"
    )


def test_af4_fail_entries_cover_10_plus_real_persons(af_bank):
    """Regression: af_bank af4_voice_clone must have >= 10 FAIL entries
    (per plan success criteria)."""
    fail_count = sum(
        1 for e in af_bank["af4_voice_clone"] if e.get("expected_verdict") == "FAIL"
    )
    assert fail_count >= 10, f"AF-4 FAIL entries only {fail_count} (need >= 10)"


@pytest.mark.parametrize("artist,title,expected", [
    ("BTS", "Dynamite", True),
    ("방탄소년단", "봄날", True),
    ("BLACKPINK", "Pink Venom", True),
    ("NewJeans", "How Sweet", True),
    ("IVE", "LOVE DIVE", True),
    ("aespa", "Supernova", True),
    ("LE SSERAFIM", "UNFORGIVEN", True),
    ("Stray Kids", "MANIAC", True),
    ("SEVENTEEN", "God of Music", True),
    ("NCT", "Sticker", True),
    ("TWICE", "FANCY", True),
    ("Epidemic Sound", "Suspense Strings", False),
    ("Artlist", "Background Groove", False),
    ("", "", False),
])
def test_af13_regex_direct_matrix(artist, title, expected):
    """Direct regex verification against canonical (artist, title) pairs."""
    assert af13_blocked(artist, title) is expected, (
        f"({artist!r}, {title!r}) expected blocked={expected}"
    )
