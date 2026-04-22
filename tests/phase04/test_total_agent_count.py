"""Phase 4 Plan 10 — VALIDATION 32-agent invariant + SC1 reconciliation flag.

Total agent count (excluding harvest-importer, which is Phase 3 deprecated):
  - Inspector 17 (6 categories: structural 3 + content 3 + style 3 + compliance 3 + technical 3 + media 2)
  - Producer 15 (Core 6 + 3단 분리 3 + Support 6 — subtitle-producer 추가 Phase 16-03)
  - Supervisor 1 (shorts-supervisor)
  Total = 33 (Phase 16-03 amend per CONTEXT.md + CLAUDE.md forbid-9)

This is the canonical count per REQUIREMENTS.md AGENT-01~05 and RESEARCH.md Open Q1.
ROADMAP.md Phase 4 SC1 "12~20 사이" is the Phase 2 initial estimate and is reconciled
to 33 (Phase 16-03 amend: subtitle-producer 신규, 32→33).
"""
from __future__ import annotations

import pathlib


AGENTS_DIR = pathlib.Path(".claude/agents")


def test_32_agents_total_excluding_harvest() -> None:
    """Phase 16-03 amend: 32 → 33 (subtitle-producer 신규)."""
    all_agents = [
        p for p in AGENTS_DIR.rglob("AGENT.md") if "harvest-importer" not in str(p)
    ]
    assert len(all_agents) == 33, (
        f"Expected 33 agents (17 inspector + 15 producer + 1 supervisor, "
        f"excluding harvest-importer; Phase 16-03 amend: subtitle-producer 신규), "
        f"got {len(all_agents)}.\n"
        f"Agents: {sorted(str(p) for p in all_agents)}"
    )


def test_inspector_count_17() -> None:
    inspectors = list((AGENTS_DIR / "inspectors").rglob("AGENT.md"))
    assert len(inspectors) == 17, (
        f"Expected 17 inspectors across 6 categories "
        f"(structural 3 + content 3 + style 3 + compliance 3 + technical 3 + media 2), "
        f"got {len(inspectors)}"
    )


def test_producer_count_14() -> None:
    """Phase 16-03 amend: Producer 14 → 15 (subtitle-producer 신규)."""
    producers = list((AGENTS_DIR / "producers").rglob("AGENT.md"))
    assert len(producers) == 15, (
        f"Expected 15 producers (Core 6 + 3단 분리 3 + Support 6: "
        f"trend-collector, niche-classifier, researcher, director, scene-planner, "
        f"shot-planner, scripter, script-polisher, metadata-seo, voice-producer, "
        f"asset-sourcer, assembler, thumbnail-designer, publisher, subtitle-producer), "
        f"got {len(producers)}"
    )


def test_supervisor_count_1() -> None:
    supervisors = list((AGENTS_DIR / "supervisor").rglob("AGENT.md"))
    assert len(supervisors) == 1, (
        f"Expected 1 supervisor (shorts-supervisor), got {len(supervisors)}"
    )


def test_inspector_category_breakdown() -> None:
    """Verify 6-category breakdown matches RESEARCH.md Appendix C."""
    insp = AGENTS_DIR / "inspectors"
    assert len(list((insp / "structural").rglob("AGENT.md"))) == 3, "structural must be 3"
    assert len(list((insp / "content").rglob("AGENT.md"))) == 3, "content must be 3"
    assert len(list((insp / "style").rglob("AGENT.md"))) == 3, "style must be 3"
    assert len(list((insp / "compliance").rglob("AGENT.md"))) == 3, "compliance must be 3"
    assert len(list((insp / "technical").rglob("AGENT.md"))) == 3, "technical must be 3"
    assert len(list((insp / "media").rglob("AGENT.md"))) == 2, "media must be 2"
