"""Phase 12 공통 fixture — tmp FAILURES.md, MockClaudeCLI, synthetic producer_output."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Windows cp949 stdout guard — Korean text round-trip safety (Phase 11 precedent).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Phase 11 precedent: sys.path prelude for `tests.phase12.mocks` resolution.
sys.path.insert(0, str(Path(__file__).parent))

# tests/phase12/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

REPO_ROOT = _REPO_ROOT


@pytest.fixture
def tmp_failures_file(tmp_path: Path) -> Path:
    """tmp FAILURES.md — 31-line head (schema + notice) + configurable body.

    Gives Plan 05 rotation tests a writable FAILURES.md fixture without
    touching the real `.claude/failures/FAILURES.md` (D-11 append-only
    enforcement + D-14 sha256 lock on _imported_from_shorts_naberal.md).
    """
    head = (
        "# FAILURES.md — Append-Only Reservoir\n\n"
        "> **D-11:** Append-only.\n\n"
        "## Entry Schema\n\n```\n### FAIL-NNN\n```\n\n"
        "## Entries\n\n"
    )
    # Pad to 31 lines so tests control the tail portion.
    lines = head.splitlines()
    while len(lines) < 31:
        lines.append("")
    p = tmp_path / "FAILURES.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


@pytest.fixture
def synthetic_producer_output_small() -> dict:
    """5 decisions × 2 error_codes — under Plan 07 compression budget (2000 chars)."""
    return {
        "gate": "SCRIPT",
        "verdict": "RETRY",
        "decisions": [
            {
                "rule": f"rule_{i}",
                "severity": "medium",
                "score": 60 + i,
                "evidence": f"decision {i} evidence",
            }
            for i in range(5)
        ],
        "error_codes": ["ERR_A", "ERR_B"],
        "semantic_feedback": "5 decisions seed",
    }
