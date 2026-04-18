"""Phase 4 Wave 1c — Style Inspector compliance tests.

Asserts that .claude/agents/inspectors/style/*/AGENT.md satisfies:
- Exactly 3 AGENT.md files under style/
- Frontmatter: role=inspector, category=style
- maxTurns: ins-tone-brand=5 (RUB-05 exception); ins-readability=3; ins-thumbnail-hook=3
- LogicQA block with main_q + exactly 5 sub_qs (q1..q5)
- MUST REMEMBER at END (ratio_from_end ≤ 0.4, AGENT-09) containing 창작 금지 (RUB-02) + producer_prompt (RUB-06)
- Inputs table must NOT expose producer_prompt / producer_system_context (RUB-06 GAN separation)
- ins-tone-brand body references '.preserved/harvested/theme_bible_raw/' (CONTENT-03, 10 필드 대조)
- ins-readability body contains '24', '32', '1', '4', 'Pretendard' and '중앙' (CONTENT-06)
- ins-thumbnail-hook body contains '4.5' (WCAG AA) and hook pattern terms
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
from scripts.validate.validate_all_agents import (  # noqa: E402
    MUST_REMEMBER_HEADER,
    MUST_REMEMBER_MAX_RATIO_FROM_END,
    check_must_remember_position,
)

STYLE_DIR = _REPO_ROOT / ".claude/agents/inspectors/style"

EXPECTED_MAX_TURNS = {
    "ins-tone-brand": 5,       # RUB-05 exception
    "ins-readability": 3,
    "ins-thumbnail-hook": 3,
}


@pytest.fixture(scope="module")
def style_agents():
    """Return list of (path, meta_dict, body_str) tuples for every style Inspector AGENT.md."""
    files = sorted(STYLE_DIR.rglob("AGENT.md"))
    result = []
    for f in files:
        meta, body = parse_frontmatter(f)
        result.append((f, meta, body))
    return result


def test_exactly_3_style_inspectors(style_agents):
    assert len(style_agents) == 3, (
        f"Expected exactly 3 style inspectors, got {len(style_agents)}: "
        f"{[str(p.relative_to(_REPO_ROOT)) for p, _, _ in style_agents]}"
    )


def test_all_names_present(style_agents):
    names = {meta["name"] for _, meta, _ in style_agents}
    assert names == set(EXPECTED_MAX_TURNS.keys()), (
        f"Expected {set(EXPECTED_MAX_TURNS.keys())}, got {names}"
    )


def test_frontmatter_role_category(style_agents):
    for path, meta, _ in style_agents:
        assert meta.get("role") == "inspector", f"{path}: role != inspector"
        assert meta.get("category") == "style", f"{path}: category != style"


def test_maxturns_per_agent(style_agents):
    for path, meta, _ in style_agents:
        name = meta["name"]
        expected = EXPECTED_MAX_TURNS[name]
        actual = int(meta["maxTurns"])
        assert actual == expected, (
            f"{path}: {name} expected maxTurns={expected}, got {actual}"
        )


def test_logicqa_block_present(style_agents):
    for path, _, body in style_agents:
        assert "<main_q>" in body, f"{path}: missing <main_q>"
        assert "</main_q>" in body, f"{path}: missing closing </main_q>"
        assert "<sub_qs>" in body, f"{path}: missing <sub_qs>"
        assert "</sub_qs>" in body, f"{path}: missing closing </sub_qs>"


def test_logicqa_exactly_5_sub_qs(style_agents):
    for path, _, body in style_agents:
        # Match the sub_qs block content
        m = re.search(r"<sub_qs>(.*?)</sub_qs>", body, re.DOTALL)
        assert m, f"{path}: <sub_qs> block not found"
        block = m.group(1)
        for q_id in ["q1", "q2", "q3", "q4", "q5"]:
            # Each q# appears on its own line with a colon
            assert re.search(rf"\b{q_id}\s*:", block), (
                f"{path}: missing {q_id} inside <sub_qs>"
            )
        # Also: no q6/q7 inside the block (exactly 5)
        assert not re.search(r"\bq6\s*:", block), f"{path}: unexpected q6 in <sub_qs>"


def test_must_remember_at_end(style_agents):
    """AGENT-09: MUST REMEMBER header must appear in final 40% of body."""
    for path, _, body in style_agents:
        idx, ratio, total = check_must_remember_position(body)
        assert idx != -1, (
            f"{path}: '{MUST_REMEMBER_HEADER}' header missing (AGENT-09)"
        )
        assert ratio <= MUST_REMEMBER_MAX_RATIO_FROM_END, (
            f"{path}: MUST REMEMBER at line {idx}/{total} "
            f"(ratio_from_end={ratio:.2f} > {MUST_REMEMBER_MAX_RATIO_FROM_END})"
        )


def test_must_remember_contains_rub_02_and_rub_06(style_agents):
    for path, _, body in style_agents:
        mr_match = re.search(
            r"## MUST REMEMBER.*?(?=\n##\s|\Z)", body, re.DOTALL
        )
        assert mr_match, f"{path}: no MUST REMEMBER section captured"
        mr = mr_match.group(0)
        assert "창작 금지" in mr, (
            f"{path}: MUST REMEMBER missing '창작 금지' (RUB-02)"
        )
        assert "producer_prompt" in mr, (
            f"{path}: MUST REMEMBER missing 'producer_prompt' reference (RUB-06)"
        )


def test_inputs_table_no_producer_prompt_leak(style_agents):
    """RUB-06: Inputs table must not list producer_prompt or producer_system_context as fields."""
    for path, _, body in style_agents:
        inputs_match = re.search(
            r"## Inputs(.*?)(?=\n##\s)", body, re.DOTALL
        )
        assert inputs_match, f"{path}: no ## Inputs section"
        inputs = inputs_match.group(1)
        # No table row with producer_prompt or producer_system_context as a Field
        assert not re.search(r"\|\s*`?producer_prompt`?\s*\|", inputs), (
            f"{path}: Inputs table leaks producer_prompt (RUB-06 위반)"
        )
        assert not re.search(r"\|\s*`?producer_system_context`?\s*\|", inputs), (
            f"{path}: Inputs table leaks producer_system_context (RUB-06 위반)"
        )


def test_ins_tone_brand_references_theme_bible_raw(style_agents):
    """ins-tone-brand body must reference .preserved/harvested/theme_bible_raw/ (CONTENT-03, 10 필드)."""
    for path, meta, body in style_agents:
        if meta["name"] == "ins-tone-brand":
            assert "theme_bible_raw" in body, (
                f"{path}: missing 'theme_bible_raw' reference (CONTENT-03, 10줄 바이블)"
            )
            # Also check maxTurns=5 explicitly (RUB-05 exception) appears in frontmatter
            assert int(meta["maxTurns"]) == 5
            return
    pytest.fail("ins-tone-brand not found in style inspectors")


def test_ins_readability_content_06_spec(style_agents):
    """ins-readability body must hardcode CONTENT-06 spec: 24~32pt, 1~4 단어/라인, Pretendard, 중앙."""
    for path, meta, body in style_agents:
        if meta["name"] == "ins-readability":
            assert "24" in body, f"{path}: missing '24' (CONTENT-06 min font)"
            assert "32" in body, f"{path}: missing '32' (CONTENT-06 max font)"
            # '1' and '4' must appear for 1~4 단어/라인 (trivially true but enforce anyway)
            assert "1" in body and "4" in body, (
                f"{path}: missing '1' or '4' (CONTENT-06 words/line range)"
            )
            assert "Pretendard" in body or "Noto Sans KR" in body, (
                f"{path}: missing Pretendard or Noto Sans KR (CONTENT-06 font family)"
            )
            assert "중앙" in body, (
                f"{path}: missing '중앙' (CONTENT-06 center alignment)"
            )
            return
    pytest.fail("ins-readability not found in style inspectors")


def test_ins_thumbnail_hook_wcag_and_hook_patterns(style_agents):
    """ins-thumbnail-hook body must reference WCAG 4.5 contrast + hook pattern terms."""
    for path, meta, body in style_agents:
        if meta["name"] == "ins-thumbnail-hook":
            # WCAG AA contrast 4.5 must appear
            assert "4.5" in body, f"{path}: missing '4.5' (WCAG AA contrast ratio)"
            # At least 2 of 3 hook pattern terms (질문형 / 숫자 / 고유명사) must appear
            hook_terms = ["질문", "숫자", "고유명사"]
            matched = [t for t in hook_terms if t in body]
            assert len(matched) >= 2, (
                f"{path}: expected ≥2 of {hook_terms}, got {matched}"
            )
            assert int(meta["maxTurns"]) == 3
            return
    pytest.fail("ins-thumbnail-hook not found in style inspectors")


def test_all_reference_rubric_schema(style_agents):
    for path, _, body in style_agents:
        assert "rubric-schema.json" in body, (
            f"{path}: missing rubric-schema.json reference (RUB-04)"
        )
