"""AGENT-STD-02 — <mandatory_reads> 블록 prose 품질 검증.

Plan 06 populate: Plan 01 red stubs (skip-decorated) → real assertions
covering all 31 in-scope AGENT.md (14 producer + 17 inspector; disk reality
per Plan 01 SUMMARY deviation #1 and Plan 03 reconciliation).

Checks per file:
  1. FAILURES.md reference present in <mandatory_reads>
  2. canonical channel_identity.md path present
  3. At least one .claude/skills/<name>/SKILL.md reference AND that SKILL.md
     exists on disk
  4. Korean literal '샘플링 금지' present (UTF-8, strict literal)

Also exercises four bad-fixture negative tests so the validator's detection
path is regression-locked, and a smoke test proving UTF-8 encoding round-trips
the Korean bytes (Windows cp949 safety).

D-A1-03 soft enforcement / AGENT-STD-02 close-out.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validate"))

from verify_agent_md_schema import _collect_all_agent_mds  # noqa: E402
from verify_mandatory_reads_prose import (  # noqa: E402
    verify_file,
    REQUIRED_LITERALS,
    MANDATORY_READS_BLOCK_RE,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"
KOREAN_LITERAL = "샘플링 금지"


# ---------------------------------------------------------------------------
# Disk-truth collection — used by all parametrized tests.
# ---------------------------------------------------------------------------

ALL_AGENT_MDS = _collect_all_agent_mds()
AGENT_IDS = [p.relative_to(REPO_ROOT).as_posix() for p in ALL_AGENT_MDS]


# ---------------------------------------------------------------------------
# Shape guards — reject regressions in the validator contract itself.
# ---------------------------------------------------------------------------

def test_required_literals_count_is_4():
    """AGENT-STD-02 contract: exactly 4 prose elements."""
    assert len(REQUIRED_LITERALS) == 4, (
        f"REQUIRED_LITERALS count = {len(REQUIRED_LITERALS)}, expected 4"
    )
    assert set(REQUIRED_LITERALS.keys()) == {
        "failures_md",
        "channel_bible",
        "skill_path",
        "sampling_forbidden",
    }


def test_scope_is_31_agents():
    """14 producer + 17 inspector = 31 AGENT.md in scope (disk reality,
    Plan 01 SUMMARY deviation #1 and Plan 03 reconciliation)."""
    assert len(ALL_AGENT_MDS) == 31, (
        f"expected 31 in-scope AGENT.md, got {len(ALL_AGENT_MDS)}"
    )


# ---------------------------------------------------------------------------
# Global assertions — 31 agents collectively.
# ---------------------------------------------------------------------------

def test_sampling_forbidden_literal():
    """Every in-scope AGENT.md contains the literal '샘플링 금지' (element 4)."""
    missing: list[str] = []
    for p in ALL_AGENT_MDS:
        text = p.read_text(encoding="utf-8")
        if KOREAN_LITERAL not in text:
            missing.append(str(p.relative_to(REPO_ROOT)))
    assert not missing, (
        f"{len(missing)}/31 AGENT.md missing '{KOREAN_LITERAL}' literal: "
        f"{missing[:5]}"
    )


def test_three_mandatory_items_present():
    """Every <mandatory_reads> block contains FAILURES.md + channel_bible +
    skill path references (elements 1, 2, 3)."""
    violations: list[tuple[str, list[str]]] = []
    for p in ALL_AGENT_MDS:
        text = p.read_text(encoding="utf-8")
        m = MANDATORY_READS_BLOCK_RE.search(text)
        assert m, f"{p.relative_to(REPO_ROOT)} has no <mandatory_reads> block"
        block = m.group(1)
        missing_items: list[str] = []
        if ".claude/failures/FAILURES.md" not in block:
            missing_items.append("FAILURES.md")
        if "wiki/continuity_bible/channel_identity.md" not in block:
            missing_items.append("channel_identity.md")
        if ".claude/skills/" not in block or "SKILL.md" not in block:
            missing_items.append("skill_path")
        if missing_items:
            violations.append(
                (str(p.relative_to(REPO_ROOT)), missing_items)
            )
    assert not violations, (
        f"{len(violations)}/31 violate 3-item prose contract: {violations[:3]}"
    )


# ---------------------------------------------------------------------------
# Per-agent parametrized — each in-scope AGENT.md individually verified.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "agent_path",
    ALL_AGENT_MDS,
    ids=AGENT_IDS,
)
def test_each_agent_passes_prose_check(agent_path: Path):
    """verify_file returns ok=True for every in-scope AGENT.md.

    Bundles all 4 prose checks + on-disk skill existence into one canonical
    acceptance predicate per file. No skips permitted."""
    ok, missing = verify_file(agent_path)
    rel = agent_path.relative_to(REPO_ROOT)
    assert ok, f"{rel} violates AGENT-STD-02: missing = {missing}"


# ---------------------------------------------------------------------------
# Encoding smoke test — Windows cp949 safety.
# ---------------------------------------------------------------------------

def test_utf8_encoding_round_trip_korean_literal():
    """Reading a known-good AGENT.md with encoding='utf-8' preserves the
    Korean literal byte-for-byte. Guards against Windows cp949 default
    corrupting the match (validator uses open(..., encoding='utf-8'))."""
    canonical = (
        REPO_ROOT
        / ".claude"
        / "agents"
        / "producers"
        / "trend-collector"
        / "AGENT.md"
    )
    assert canonical.exists(), "canonical exemplar missing"
    text = canonical.read_text(encoding="utf-8")
    assert KOREAN_LITERAL in text, (
        "UTF-8 round-trip failed — Korean literal bytes corrupted"
    )


# ---------------------------------------------------------------------------
# Negative fixtures — prove the validator REJECTS each element's absence.
# Without these, a broken validator (e.g. missing a literal check) could
# still pass the 31-agent positive suite.
# ---------------------------------------------------------------------------

def test_bad_fixture_missing_sampling_literal_rejected():
    """Fixture omits '샘플링 금지' literal → verify_file must fail with
    'sampling_forbidden' in the missing list."""
    path = FIXTURES_DIR / "bad_agent_missing_sampling_literal.md"
    assert path.exists(), "negative fixture missing"
    ok, missing = verify_file(path)
    assert not ok
    assert "sampling_forbidden" in missing


def test_bad_fixture_missing_channel_bible_rejected():
    """Fixture uses legacy `wiki/ypp/channel_bible.md` path instead of the
    canonical `wiki/continuity_bible/channel_identity.md` →
    verify_file must fail with 'channel_bible' in the missing list."""
    path = FIXTURES_DIR / "bad_agent_missing_channel_bible.md"
    assert path.exists(), "negative fixture missing"
    ok, missing = verify_file(path)
    assert not ok
    assert "channel_bible" in missing


def test_bad_fixture_missing_block_rejected():
    """Fixture has no <mandatory_reads> block → verify_file fails with the
    'no block' sentinel message."""
    path = FIXTURES_DIR / "bad_agent_missing_block.md"
    assert path.exists(), "negative fixture missing"
    ok, missing = verify_file(path)
    assert not ok
    assert len(missing) == 1
    assert "no <mandatory_reads> block" in missing[0]


def test_bad_fixture_orphan_skill_rejected():
    """Fixture declares a SKILL.md path that does not exist on disk →
    verify_file fails with 'skill_not_on_disk:<name>' in missing list
    (drift guard between AGENT.md and .claude/skills/)."""
    path = FIXTURES_DIR / "bad_agent_orphan_skill.md"
    assert path.exists(), "negative fixture missing"
    ok, missing = verify_file(path)
    assert not ok
    # Orphan skill should surface even though the skill_path regex itself matched.
    assert any(
        m.startswith("skill_not_on_disk:") for m in missing
    ), f"expected skill_not_on_disk sentinel in {missing}"


# ---------------------------------------------------------------------------
# Validator CLI integration — ensure --all exits 0 at current disk state.
# ---------------------------------------------------------------------------

def test_validator_cli_all_exits_zero():
    """`verify_mandatory_reads_prose.main(['--all'])` returns 0 — regression
    guard covering the CLI entrypoint (not just verify_file)."""
    from verify_mandatory_reads_prose import main as prose_main

    exit_code = prose_main(["--all"])
    assert exit_code == 0, "CLI --all should pass at current Plan 06 disk state"
