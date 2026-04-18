"""Phase 4 Wave 4 — Supervisor AGENT-05 재귀 방지 회귀 (plan 04-09).

Enforces shorts-supervisor AGENT.md contract:
    - Exactly 1 supervisor AGENT.md under .claude/agents/supervisor/
    - role=supervisor, category=supervisor, maxTurns=3
    - body contains '_delegation_depth' + '>= 1' + 'raise' (AGENT-05 guard)
    - body lists all 17 inspector names (전수 fan-out)
    - body contains 'fan-out' or 'fan_out'
    - MUST REMEMBER header in final 40%

All tests must PASS.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.validate.parse_frontmatter import parse_frontmatter  # noqa: E402

SUPERVISOR_PATH = (
    _REPO_ROOT / ".claude/agents/supervisor/shorts-supervisor/AGENT.md"
)
SUPERVISOR_DIR = _REPO_ROOT / ".claude/agents/supervisor"

EXPECTED_17_INSPECTORS = [
    # structural 3
    "ins-blueprint-compliance",
    "ins-timing-consistency",
    "ins-schema-integrity",
    # content 3
    "ins-factcheck",
    "ins-narrative-quality",
    "ins-korean-naturalness",
    # style 3
    "ins-tone-brand",
    "ins-readability",
    "ins-thumbnail-hook",
    # compliance 3
    "ins-license",
    "ins-platform-policy",
    "ins-safety",
    # technical 3
    "ins-audio-quality",
    "ins-render-integrity",
    "ins-subtitle-alignment",
    # media 2
    "ins-mosaic",
    "ins-gore",
]


@pytest.fixture(scope="module")
def supervisor():
    meta, body = parse_frontmatter(SUPERVISOR_PATH)
    return meta, body


# -----------------------------------------------------------------------------
# Test 1 — exactly 1 supervisor AGENT.md exists at expected path
# -----------------------------------------------------------------------------
def test_exactly_1_supervisor_exists():
    all_sup = list(SUPERVISOR_DIR.rglob("AGENT.md"))
    assert len(all_sup) == 1, (
        f"Expected exactly 1 supervisor AGENT.md, found {len(all_sup)}"
    )
    assert all_sup[0] == SUPERVISOR_PATH, (
        f"Supervisor path mismatch: got {all_sup[0]}, expected {SUPERVISOR_PATH}"
    )


# -----------------------------------------------------------------------------
# Test 2 — frontmatter role/category/maxTurns
# -----------------------------------------------------------------------------
def test_supervisor_frontmatter(supervisor):
    meta, _ = supervisor
    assert meta.get("role") == "supervisor", (
        f"role={meta.get('role')!r}, expected 'supervisor'"
    )
    assert meta.get("category") == "supervisor", (
        f"category={meta.get('category')!r}, expected 'supervisor'"
    )
    max_turns = int(meta.get("maxTurns", "0"))
    assert max_turns == 3, (
        f"maxTurns={max_turns}, expected 3 (RUB-05 Supervisor standard)"
    )
    assert meta.get("name") == "shorts-supervisor", (
        f"name={meta.get('name')!r}, expected 'shorts-supervisor'"
    )


# -----------------------------------------------------------------------------
# Test 3 — AGENT-05 재귀 방지 guard (_delegation_depth + >= 1 + raise)
# -----------------------------------------------------------------------------
def test_delegation_depth_guard(supervisor):
    _meta, body = supervisor
    assert "_delegation_depth" in body, (
        "Supervisor missing '_delegation_depth' field (AGENT-05 guard)"
    )
    assert ">= 1" in body, (
        "Supervisor missing '>= 1' threshold (AGENT-05 guard)"
    )
    assert "raise" in body.lower(), (
        "Supervisor missing 'raise' for DelegationDepthExceeded (AGENT-05)"
    )


# -----------------------------------------------------------------------------
# Test 4 — all 17 inspector names listed in body
# -----------------------------------------------------------------------------
def test_17_inspector_names_present(supervisor):
    _meta, body = supervisor
    missing = [i for i in EXPECTED_17_INSPECTORS if i not in body]
    assert not missing, (
        f"Supervisor missing inspector names: {missing}"
    )


# -----------------------------------------------------------------------------
# Test 5 — fan-out terminology present
# -----------------------------------------------------------------------------
def test_fanout_mention(supervisor):
    _meta, body = supervisor
    assert ("fan-out" in body) or ("fan_out" in body), (
        "Supervisor missing 'fan-out' or 'fan_out' terminology"
    )


# -----------------------------------------------------------------------------
# Test 6 — MUST REMEMBER header in final 40% of body (AGENT-09)
# -----------------------------------------------------------------------------
def test_must_remember_final_40_percent(supervisor):
    _meta, body = supervisor
    lines = body.splitlines()
    total = len(lines)
    assert total > 0, "Supervisor body empty"
    found_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("## MUST REMEMBER"):
            found_idx = i
            break
    assert found_idx >= 0, "Supervisor missing '## MUST REMEMBER' header"
    ratio_from_end = (total - found_idx) / total
    assert ratio_from_end <= 0.4, (
        f"MUST REMEMBER ratio_from_end={ratio_from_end:.3f}, "
        f"expected ≤ 0.4 (AGENT-09)"
    )


# -----------------------------------------------------------------------------
# Test 7 — supervisor-rubric-schema.json referenced
# -----------------------------------------------------------------------------
def test_supervisor_rubric_schema_reference(supervisor):
    _meta, body = supervisor
    assert "supervisor-rubric-schema.json" in body, (
        "Supervisor missing supervisor-rubric-schema.json reference"
    )


# -----------------------------------------------------------------------------
# Test 8 — aggregated_vqqa 원문 concat 규칙 명시 (요약 금지)
# -----------------------------------------------------------------------------
def test_aggregated_vqqa_concat_no_summary(supervisor):
    _meta, body = supervisor
    # body must mention concat/원문 + 요약 금지
    assert "aggregated_vqqa" in body, (
        "Supervisor missing 'aggregated_vqqa' in body"
    )
    # either explicit "요약 금지" or "concat" terminology
    assert ("요약 금지" in body) or ("concat" in body.lower()), (
        "Supervisor missing aggregated_vqqa concat / 요약 금지 rule (RUB-03)"
    )
