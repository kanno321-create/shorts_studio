"""KPI-05 + SC#3 — taste_gate_protocol.md + taste_gate_2026-04.md validators (Plan 09-03 target).

Wave 0 RED state: protocol doc + dry-run file do not yet exist; each test skips via a
file-existence gate so collection succeeds. Plan 09-03 writes both files with D-08/D-09/D-10/D-11
documentation and 6-row 탐정/조수 페르소나 dry-run to flip these green.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = _REPO_ROOT / "wiki" / "kpi" / "taste_gate_protocol.md"
DRYRUN = _REPO_ROOT / "wiki" / "kpi" / "taste_gate_2026-04.md"


def _read(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"{path} not yet created — Plan 09-03 target", allow_module_level=False)
    return path.read_text(encoding="utf-8")


def test_protocol_doc():
    """SC#3: taste_gate_protocol.md documents monthly cadence (D-11 매월 1일 KST 09:00)."""
    content = _read(PROTOCOL)
    assert "매월" in content or "월 1회" in content, "Missing monthly cadence declaration"
    assert "KST" in content and "09:00" in content, "Missing KST 09:00 trigger time"
    assert "상위 3" in content and "하위 3" in content, "Missing top-3/bottom-3 selection method"
    assert "3sec_retention" in content or "3초 retention" in content, "Missing D-08 selection metric"


def test_dry_run_exists():
    """SC#3 + D-10: taste_gate_2026-04.md dry-run file exists with status=dry-run."""
    content = _read(DRYRUN)
    assert "status: dry-run" in content or "status:dry-run" in content, "Missing frontmatter status: dry-run"
    assert "DRY-RUN" in content or "dry-run" in content, "Missing DRY-RUN warning banner (Pitfall 3)"


def test_six_evaluation_rows():
    """KPI-05: 6 rows (3 top + 3 bottom) with score column."""
    content = _read(DRYRUN)
    for vid in ["abc123", "def456", "ghi789", "jkl012", "mno345", "pqr678"]:
        assert vid in content, f"Missing synthetic video_id {vid}"


def test_score_column_1_to_5():
    """KPI-05: 품질 (1-5) column header present."""
    content = _read(DRYRUN)
    assert "품질" in content and ("1-5" in content or "(1-5)" in content), "Missing 품질 (1-5) score column"


def test_comment_column():
    """KPI-05: 한줄 코멘트 column header present."""
    content = _read(DRYRUN)
    assert "한줄 코멘트" in content or "코멘트" in content, "Missing comment column"


def test_persona_titles_not_placeholder():
    """CONTEXT.md §specifics: real 탐정/조수 persona titles, NOT 테스트용 쇼츠 placeholder."""
    content = _read(DRYRUN)
    assert "테스트용 쇼츠" not in content, "Forbidden placeholder 테스트용 쇼츠 present (CONTEXT forbids)"
    assert re.search(r"탐정|조수|범인|갑부|편지", content), "Missing persona-relevant title keyword"
