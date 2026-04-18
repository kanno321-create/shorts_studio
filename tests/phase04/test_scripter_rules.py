"""Phase 4 Wave 3 — scripter producer content rules tests (Plan 04-08 Task 3).

Enforces plan 04-08 specialized scripter requirements:
    - 8 required keywords (CONTENT-01 + CONTENT-02)
    - 7+ MUST REMEMBER bullets
    - Inputs include --prior-vqqa and --channel-bible

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

SCRIPTER_PATH = _REPO_ROOT / ".claude/agents/producers/scripter/AGENT.md"

REQUIRED_KEYWORDS = [
    "3초 hook",  # CONTENT-01
    "질문형",  # CONTENT-01
    "숫자",  # CONTENT-01
    "고유명사",  # CONTENT-01
    "탐정",  # CONTENT-02
    "하오체",  # CONTENT-02
    "조수",  # CONTENT-02
    "해요체",  # CONTENT-02
]


@pytest.fixture(scope="module")
def scripter_agent():
    """Load scripter AGENT.md once for all tests."""
    assert SCRIPTER_PATH.exists(), f"scripter AGENT.md not found at {SCRIPTER_PATH}"
    meta, body = parse_frontmatter(SCRIPTER_PATH)
    return meta, body


def test_scripter_frontmatter_is_producer_core_maxturns_3(scripter_agent):
    meta, _body = scripter_agent
    assert meta.get("role") == "producer", f"role={meta.get('role')!r}, expected 'producer'"
    assert meta.get("category") == "core", f"category={meta.get('category')!r}, expected 'core'"
    assert int(meta.get("maxTurns", "0")) == 3, (
        f"maxTurns={meta.get('maxTurns')!r}, expected 3 (RUB-05)"
    )


def test_scripter_body_contains_all_8_required_keywords(scripter_agent):
    """CONTENT-01 + CONTENT-02 — scripter prompt must contain all 8 hook/duo-dialogue keywords."""
    _meta, body = scripter_agent
    missing = [kw for kw in REQUIRED_KEYWORDS if kw not in body]
    assert not missing, (
        f"scripter body missing keywords: {missing} (CONTENT-01 + CONTENT-02)"
    )


def test_scripter_must_remember_has_7_plus_bullets(scripter_agent):
    """scripter MUST REMEMBER should have 7+ numbered bullets (plan spec)."""
    _meta, body = scripter_agent
    mr_match = re.search(r"## MUST REMEMBER.*?\Z", body, re.DOTALL)
    assert mr_match, "scripter: no MUST REMEMBER section (AGENT-09)"
    mr = mr_match.group(0)
    # Count numbered bullets "1. ", "2. ", ... at line starts
    bullet_lines = re.findall(r"^\s*(\d+)\.\s+", mr, re.MULTILINE)
    unique_bullets = sorted(set(int(n) for n in bullet_lines))
    assert len(unique_bullets) >= 7, (
        f"scripter MUST REMEMBER has {len(unique_bullets)} unique bullets, expected 7+ "
        f"(bullets: {unique_bullets})"
    )


def test_scripter_inputs_include_prior_vqqa_and_channel_bible(scripter_agent):
    """scripter Inputs section must reference both --prior-vqqa and --channel-bible."""
    _meta, body = scripter_agent
    # Extract Inputs section (until next top-level header)
    inputs_match = re.search(r"## Inputs.*?(?=\n## )", body, re.DOTALL)
    assert inputs_match, "scripter: no Inputs section"
    inputs = inputs_match.group(0)

    # --prior-vqqa required (RUB-03)
    assert "--prior-vqqa" in inputs or "prior_vqqa" in inputs, (
        "scripter Inputs missing --prior-vqqa / prior_vqqa (RUB-03 feedback loop)"
    )
    # --channel-bible required (CONTENT-03)
    assert "--channel-bible" in inputs or "channel_bible" in inputs, (
        "scripter Inputs missing --channel-bible / channel_bible (CONTENT-03)"
    )


def test_scripter_must_remember_contains_inspector_prompt_forbidden(scripter_agent):
    """RUB-06 GAN mirror — scripter MUST REMEMBER has 'inspector_prompt 읽기 금지'."""
    _meta, body = scripter_agent
    mr_match = re.search(r"## MUST REMEMBER.*?\Z", body, re.DOTALL)
    assert mr_match, "scripter: no MUST REMEMBER section"
    mr = mr_match.group(0)
    assert "inspector_prompt" in mr, (
        "scripter MUST REMEMBER missing 'inspector_prompt' reference "
        "(RUB-06 GAN separation mirror)"
    )


def test_scripter_references_59s_and_citation(scripter_agent):
    """CONTENT-04 + CONTENT-05 — scripter body references citation + 59s duration cap."""
    _meta, body = scripter_agent
    assert "citation" in body.lower(), "scripter: missing 'citation' (CONTENT-04)"
    assert "59" in body, "scripter: missing '59' (CONTENT-05 59s duration cap)"
