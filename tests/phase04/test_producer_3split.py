"""Phase 4 Wave 3 — Producer 3단 분리 compliance tests (Plan 04-08 Task 2).

Enforces plan 04-08 Task 2 contract for the 3 Producer split3 AGENT.md files:
    - director (FilmAgent Level 1)
    - scene-planner (FilmAgent Level 2)
    - shot-planner (FilmAgent Level 3)

NotebookLM T6 = FilmAgent hierarchy (Director → Scene Planner → Shot Planner).
NotebookLM T2 = 1 Move Rule per scene.
NotebookLM T1 = I2V only, T2V forbidden.

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
EXPECTED_SPLIT3 = {"director", "scene-planner", "shot-planner"}


@pytest.fixture(scope="module")
def split3_agents():
    """Return list of (path, meta, body) tuples for Producer split3 AGENT.md files."""
    files = sorted(PRODUCERS_DIR.rglob("AGENT.md"))
    loaded = []
    for f in files:
        meta, body = parse_frontmatter(f)
        if meta.get("category") == "split3":
            loaded.append((f, meta, body))
    return loaded


def test_exactly_3_split3_producers(split3_agents):
    assert (
        len(split3_agents) == 3
    ), f"Expected 3 Producer split3 agents, found {len(split3_agents)}"
    names = {meta["name"] for _, meta, _ in split3_agents}
    assert names == EXPECTED_SPLIT3, f"Expected {EXPECTED_SPLIT3}, got {names}"


def test_frontmatter_role_producer_category_split3_maxturns_3(split3_agents):
    for path, meta, _body in split3_agents:
        assert meta.get("role") == "producer", (
            f"{path.parent.name}: role={meta.get('role')!r}, expected 'producer'"
        )
        assert meta.get("category") == "split3", (
            f"{path.parent.name}: category={meta.get('category')!r}, expected 'split3'"
        )
        max_turns = int(meta.get("maxTurns", "0"))
        assert max_turns == 3, (
            f"{path.parent.name}: maxTurns={max_turns}, expected 3 (RUB-05)"
        )


def test_all_split3_have_prior_vqqa_in_inputs(split3_agents):
    """RUB-03 — all split3 producers accept prior_vqqa feedback for retry loop."""
    for path, meta, body in split3_agents:
        has_prior_vqqa = (
            ("prior_vqqa" in body) or ("--prior-vqqa" in body)
        )
        assert has_prior_vqqa, (
            f"{path.parent.name}: missing prior_vqqa/--prior-vqqa reference "
            f"in body (RUB-03 feedback loop)"
        )


def test_scene_planner_contains_1_move_rule(split3_agents):
    """NotebookLM T2 — scene-planner body contains '1 Move Rule'."""
    target = None
    for path, meta, body in split3_agents:
        if meta["name"] == "scene-planner":
            target = (path, body)
            break
    assert target is not None, "scene-planner AGENT.md not found"
    path, body = target
    assert "1 Move Rule" in body, (
        f"{path.parent.name}: missing '1 Move Rule' (NotebookLM T2)"
    )


def test_shot_planner_contains_i2v_anchor_t2v_forbidden(split3_agents):
    """NotebookLM T1 — shot-planner body contains 'I2V', 'anchor frame', 'T2V 금지'."""
    target = None
    for path, meta, body in split3_agents:
        if meta["name"] == "shot-planner":
            target = (path, body)
            break
    assert target is not None, "shot-planner AGENT.md not found"
    path, body = target
    assert "I2V" in body, f"{path.parent.name}: missing 'I2V' (NotebookLM T1)"
    assert "anchor frame" in body, (
        f"{path.parent.name}: missing 'anchor frame' (NotebookLM T1)"
    )
    assert "T2V 금지" in body, (
        f"{path.parent.name}: missing 'T2V 금지' (NotebookLM T1)"
    )


def test_all_split3_have_must_remember_with_inspector_prompt_forbidden(split3_agents):
    """RUB-06 GAN mirror — all Producer split3 have MUST REMEMBER with 'inspector_prompt 읽기 금지'."""
    for path, meta, body in split3_agents:
        mr_match = re.search(r"## MUST REMEMBER.*?\Z", body, re.DOTALL)
        assert mr_match, f"{path.parent.name}: no MUST REMEMBER section (AGENT-09)"
        mr = mr_match.group(0)
        assert "inspector_prompt" in mr, (
            f"{path.parent.name}: MUST REMEMBER missing 'inspector_prompt' reference "
            f"(RUB-06 GAN separation mirror)"
        )


def test_director_mentions_blueprint(split3_agents):
    """director body should reference Blueprint (Level 1 output)."""
    target = None
    for path, meta, body in split3_agents:
        if meta["name"] == "director":
            target = (path, body)
            break
    assert target is not None, "director AGENT.md not found"
    path, body = target
    assert "Blueprint" in body, (
        f"{path.parent.name}: missing 'Blueprint' — director Level 1 output"
    )
