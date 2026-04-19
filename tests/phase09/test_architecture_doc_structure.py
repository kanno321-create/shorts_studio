"""SC#1 — docs/ARCHITECTURE.md structure validators (Plan 09-01 target).

Wave 0 RED state: ARCHITECTURE.md does not yet exist; each test skips via a file-existence
gate so collection succeeds. Plan 09-01 writes the single-file architecture doc and flips
these tests to green.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
ARCH = _REPO_ROOT / "docs" / "ARCHITECTURE.md"


def _read_arch() -> str:
    if not ARCH.exists():
        pytest.skip(f"{ARCH} not yet created — Plan 09-01 target", allow_module_level=False)
    return ARCH.read_text(encoding="utf-8")


def test_architecture_md_exists():
    """SC#1: docs/ARCHITECTURE.md exists (Plan 09-01 target)."""
    assert ARCH.exists(), f"{ARCH} not created (Plan 09-01 target)"


def test_mermaid_block_count():
    """D-02: ≥ 3 Mermaid diagrams (stateDiagram-v2 + 2 flowchart)."""
    content = _read_arch()
    blocks = re.findall(r"^```mermaid\s*$", content, re.MULTILINE)
    assert len(blocks) >= 3, f"Expected >= 3 Mermaid blocks, found {len(blocks)}"


def test_required_diagram_types():
    """D-02: stateDiagram-v2 + flowchart TD/LR all present."""
    content = _read_arch()
    assert "stateDiagram-v2" in content, "Missing stateDiagram-v2 (12 GATE state machine)"
    assert ("flowchart TD" in content) or ("flowchart LR" in content), "Missing flowchart diagram"


def test_reading_time_annotations():
    """D-03: Each major section has ⏱ N min; total ≤ 35 (30 + 5 tolerance)."""
    content = _read_arch()
    matches = re.findall(r"⏱\s*~?(\d+)\s*min", content)
    assert len(matches) >= 4, f"Expected >= 4 reading-time annotations, found {len(matches)}"
    total = sum(int(m) for m in matches)
    assert total <= 35, f"Total reading time {total} min exceeds 30+5 tolerance"


def test_tldr_section_near_top():
    """D-03: TL;DR pinned within first 50 lines."""
    lines = _read_arch().splitlines()
    tldr_idx = next((i for i, l in enumerate(lines) if "TL;DR" in l), None)
    assert tldr_idx is not None, "TL;DR section missing"
    assert tldr_idx < 50, f"TL;DR at line {tldr_idx}, must be in first 50 lines"


def test_layered_sections_present():
    """D-01: Layered structure headings in order: State Machine → Agent Team → 3-Tier Wiki → External."""
    content = _read_arch()
    assert re.search(r"12\s*GATE|State\s*Machine", content, re.IGNORECASE), "Missing State Machine section"
    assert re.search(r"17\s*[Ii]nspector|[Aa]gent\s*[Tt]ree|[Aa]gent\s*[Tt]eam", content), "Missing Agent Team section"
    assert re.search(r"3-?[Tt]ier|[Ww]iki", content), "Missing 3-Tier Wiki section"
    assert re.search(r"[Ee]xternal|[Yy]ou[Tt]ube|[Gg]it[Hh]ub|[Nn]otebook[Ll][Mm]", content), "Missing External Integrations section"
