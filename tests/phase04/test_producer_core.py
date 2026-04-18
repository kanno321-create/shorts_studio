"""Phase 4 Wave 3 — Producer Core 6 structural compliance tests (Plan 04-08).

Enforces plan 04-08 Task 1 contract for the 6 Producer Core AGENT.md files:
    - trend-collector
    - niche-classifier
    - researcher
    - scripter
    - script-polisher
    - metadata-seo

All tests must PASS (no skip, no xfail).
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402

PRODUCERS_DIR = _REPO_ROOT / ".claude/agents/producers"
EXPECTED_CORE = {
    "trend-collector",
    "niche-classifier",
    "researcher",
    "scripter",
    "script-polisher",
    "metadata-seo",
}


@pytest.fixture(scope="module")
def core_agents():
    """Return list of (path, meta, body) tuples for every Producer Core AGENT.md (category=core)."""
    files = sorted(PRODUCERS_DIR.rglob("AGENT.md"))
    loaded = []
    for f in files:
        meta, body = parse_frontmatter(f)
        if meta.get("category") == "core":
            loaded.append((f, meta, body))
    return loaded


def test_exactly_6_producer_core_agents(core_agents):
    assert (
        len(core_agents) == 6
    ), f"Expected 6 Producer Core agents (category=core), found {len(core_agents)}"
    names = {meta["name"] for _, meta, _ in core_agents}
    assert names == EXPECTED_CORE, f"Expected {EXPECTED_CORE}, got {names}"


def test_frontmatter_role_producer_category_core_maxturns_3(core_agents):
    for path, meta, _body in core_agents:
        assert meta.get("role") == "producer", (
            f"{path.parent.name}: role={meta.get('role')!r}, expected 'producer'"
        )
        assert meta.get("category") == "core", (
            f"{path.parent.name}: category={meta.get('category')!r}, expected 'core'"
        )
        max_turns = int(meta.get("maxTurns", "0"))
        assert max_turns == 3, (
            f"{path.parent.name}: maxTurns={max_turns}, expected 3 (RUB-05)"
        )


def test_all_have_prior_vqqa_in_inputs(core_agents):
    """RUB-03 — all producers accept prior_vqqa feedback for retry loop."""
    for path, meta, body in core_agents:
        # Check Inputs section for prior_vqqa reference (table row or --prior-vqqa flag)
        has_prior_vqqa = (
            ("prior_vqqa" in body) or ("--prior-vqqa" in body)
        )
        assert has_prior_vqqa, (
            f"{path.parent.name}: missing prior_vqqa/--prior-vqqa reference "
            f"in body (RUB-03 feedback loop)"
        )


def test_niche_classifier_references_theme_bible_raw(core_agents):
    """CONTENT-03 — niche-classifier body references .preserved/harvested/theme_bible_raw/."""
    target = None
    for path, meta, body in core_agents:
        if meta["name"] == "niche-classifier":
            target = (path, body)
            break
    assert target is not None, "niche-classifier AGENT.md not found"
    path, body = target
    assert "theme_bible_raw" in body, (
        f"{path.parent.name}: missing 'theme_bible_raw' reference (CONTENT-03)"
    )


def test_researcher_contains_citation_and_source_grounded(core_agents):
    """CONTENT-04 — researcher body contains 'citation' + ('source-grounded' OR 'NotebookLM')."""
    target = None
    for path, meta, body in core_agents:
        if meta["name"] == "researcher":
            target = (path, body)
            break
    assert target is not None, "researcher AGENT.md not found"
    path, body = target
    assert "citation" in body.lower(), (
        f"{path.parent.name}: missing 'citation' keyword (CONTENT-04)"
    )
    assert ("source-grounded" in body.lower()) or ("NotebookLM" in body) or (
        "notebooklm" in body.lower()
    ), (
        f"{path.parent.name}: neither 'source-grounded' nor 'NotebookLM' present "
        f"(CONTENT-04)"
    )


def test_metadata_seo_contains_korean_and_roman(core_agents):
    """CONTENT-07 — metadata-seo body contains '한국어' AND ('roman' OR '로마자')."""
    target = None
    for path, meta, body in core_agents:
        if meta["name"] == "metadata-seo":
            target = (path, body)
            break
    assert target is not None, "metadata-seo AGENT.md not found"
    path, body = target
    assert "한국어" in body, (
        f"{path.parent.name}: missing '한국어' keyword (CONTENT-07)"
    )
    assert ("roman" in body.lower()) or ("로마자" in body), (
        f"{path.parent.name}: neither 'roman' nor '로마자' present (CONTENT-07)"
    )


def test_all_core_have_must_remember_with_inspector_prompt_forbidden(core_agents):
    """RUB-06 GAN mirror — all Producer Core have MUST REMEMBER with 'inspector_prompt 읽기 금지'."""
    for path, meta, body in core_agents:
        mr_match = re.search(r"## MUST REMEMBER.*?\Z", body, re.DOTALL)
        assert mr_match, f"{path.parent.name}: no MUST REMEMBER section (AGENT-09)"
        mr = mr_match.group(0)
        assert "inspector_prompt" in mr, (
            f"{path.parent.name}: MUST REMEMBER missing 'inspector_prompt' reference "
            f"(RUB-06 GAN separation mirror)"
        )
