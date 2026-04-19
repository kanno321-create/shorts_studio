---
plan: 09-00
phase: 9
wave: 0
depends_on: []
files_modified:
  - tests/phase09/__init__.py
  - tests/phase09/conftest.py
  - tests/phase09/test_architecture_doc_structure.py
  - tests/phase09/test_kpi_log_schema.py
  - tests/phase09/test_taste_gate_form_schema.py
  - tests/phase09/test_record_feedback.py
  - tests/phase09/test_score_threshold_filter.py
  - tests/phase09/test_failures_append_only.py
  - tests/phase09/test_e2e_synthetic_dry_run.py
  - tests/phase09/phase09_acceptance.py
  - scripts/taste_gate/__init__.py
  - docs/.gitkeep
files_read_first:
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md
  - .planning/phases/08-remote-publishing-production-metadata/08-01-PLAN.md
  - tests/phase08/conftest.py
  - tests/phase08/phase08_acceptance.py
  - scripts/failures/aggregate_patterns.py
autonomous: true
requirements: [KPI-05, KPI-06]
tasks_addressed: [9-00-01, 9-00-02, 9-00-03]
success_criteria: [SC_FOUNDATION_WAVE_0]
estimated_commits: 3
parallel_boundary: sequential (unblocks Wave 1 + Wave 2 + Wave 3)

must_haves:
  truths:
    - "tests/phase09/__init__.py exists as empty package marker"
    - "tests/phase09/conftest.py defines 3 fixtures: synthetic_taste_gate_april, tmp_failures_md, freeze_kst_2026_04_01"
    - "7 RED test files exist as importable stubs (failing until implementation plans ship)"
    - "tests/phase09/phase09_acceptance.py skeleton present with SC 1-4 aggregator returning 1 (RED until Plan 09-05 flips to 0)"
    - "scripts/taste_gate/__init__.py exists as 7-line namespace marker mirroring scripts/failures/__init__.py"
    - "docs/ directory exists (empty or with .gitkeep) ready for ARCHITECTURE.md"
    - "pytest tests/phase09/ --collect-only exits 0 (all tests collectible even if failing)"
    - "pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q exits 0 (regression baseline preserved)"
  artifacts:
    - path: "tests/phase09/conftest.py"
      provides: "3 Phase 9 shared fixtures (independent from phase05/06/07/08 conftests per D-13 Phase 7 precedent)"
      min_lines: 80
    - path: "tests/phase09/phase09_acceptance.py"
      provides: "SC 1-4 aggregator skeleton (mirrors tests/phase08/phase08_acceptance.py shape); returns 1 at Wave 0, flipped to 0 by Plan 09-05"
      min_lines: 60
    - path: "scripts/taste_gate/__init__.py"
      provides: "Empty namespace marker, 7-line pattern mirrored from scripts/failures/__init__.py"
    - path: "tests/phase09/test_e2e_synthetic_dry_run.py"
      provides: "RED stub for SC#4 end-to-end test — imports record_feedback will fail (ModuleNotFoundError expected) until Plan 09-04"
  key_links:
    - from: "tests/phase09/conftest.py"
      to: "tests/phase08/conftest.py"
      via: "D-13 independent conftest pattern + cp949 sys.stdout.reconfigure guard + _REPO_ROOT resolve"
      pattern: "sys.stdout.reconfigure|_REPO_ROOT"
    - from: "scripts/taste_gate/__init__.py"
      to: "scripts/failures/__init__.py"
      via: "Namespace package marker pattern (7-line mirror)"
      pattern: "scripts/failures/__init__.py"
    - from: "tests/phase09/phase09_acceptance.py"
      to: "tests/phase08/phase08_acceptance.py"
      via: "SC aggregator shape (argparse + SC 1-N bool checks + sys.exit)"
      pattern: "sys.exit|all\\("
---

<objective>
Wave 0 FOUNDATION — Create tests/phase09/ package skeleton with 3 shared fixtures (D-13 independent-conftest per Phase 7 precedent), seed 7 RED test stubs covering SC#1-4 + KPI-05/06 acceptance surface, build scripts/taste_gate/ namespace as 7-line mirror of scripts/failures/, and prepare docs/ directory for ARCHITECTURE.md.

Purpose: Wave 0 infrastructure unblocks Waves 1-3. Plans 09-01/02/03 (Wave 1 parallel) need test_architecture_doc_structure.py / test_kpi_log_schema.py / test_taste_gate_form_schema.py collectible so they can RED→GREEN against them. Plan 09-04 needs scripts/taste_gate/ namespace plus test_record_feedback.py / test_score_threshold_filter.py / test_failures_append_only.py collectible. Plan 09-05 needs test_e2e_synthetic_dry_run.py + phase09_acceptance.py skeleton to flip at phase gate.

Output: 1 package marker + 1 conftest + 7 RED test files + 1 acceptance aggregator skeleton + 1 namespace marker + 1 docs/ placeholder = 12 files, zero production logic.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md
@tests/phase08/conftest.py
@tests/phase08/phase08_acceptance.py
@scripts/failures/aggregate_patterns.py

<interfaces>
## conftest.py fixtures (D-13 independent from phase05/06/07/08 conftests)

```python
@pytest.fixture
def synthetic_taste_gate_april(tmp_path: Path) -> Path:
    """D-10 synthetic sample 6 based on shorts_naberal 탐정/조수 페르소나.
    Writes tmp_path/wiki/kpi/taste_gate_2026-04.md with status=dry-run + 6 evaluated rows.
    Video IDs are obviously-fake 6-char (abc123, def456 ...) per Research Pitfall 3.
    """

@pytest.fixture
def tmp_failures_md(tmp_path: Path, monkeypatch) -> Path:
    """Redirects FAILURES_PATH to tmp_path/FAILURES.md seeded with existing Phase 6 prefix
    (so append-only Hook contract is testable in isolation). Must preserve prior content."""

@pytest.fixture
def freeze_kst_2026_04_01(monkeypatch):
    """Freezes datetime.now(KST) to 2026-04-01T09:00:00+09:00 for deterministic
    build_failures_block timestamps in E2E tests."""
```

## phase09_acceptance.py skeleton (mirror of tests/phase08/phase08_acceptance.py)

```python
#!/usr/bin/env python3
"""Phase 9 acceptance aggregator — SC 1-4 rolled into single exit code.

Wave 0 state: ALL SC return False → exit 1 (RED by design).
Plan 09-05 flips each SC aggregator to concrete checks → exit 0 on green.
"""
from __future__ import annotations
import sys

def sc1_architecture_doc() -> bool:
    """SC#1 ARCHITECTURE.md + 3 Mermaid blocks + reading time + TL;DR near top."""
    return False  # Wave 0: stub returns False

def sc2_kpi_log_hybrid() -> bool:
    """SC#2 kpi_log.md Hybrid format (Part A Target Declaration + Part B Monthly Tracking)."""
    return False

def sc3_taste_gate_protocol_and_dryrun() -> bool:
    """SC#3 taste_gate_protocol.md + taste_gate_2026-04.md dry-run exists."""
    return False

def sc4_e2e_synthetic_dryrun() -> bool:
    """SC#4 synthetic dry-run → record_feedback.py → FAILURES.md has new [taste_gate] 2026-04 entry."""
    return False

def main() -> int:
    results = {
        "SC#1": sc1_architecture_doc(),
        "SC#2": sc2_kpi_log_hybrid(),
        "SC#3": sc3_taste_gate_protocol_and_dryrun(),
        "SC#4": sc4_e2e_synthetic_dryrun(),
    }
    for k, v in results.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
```

## scripts/taste_gate/__init__.py (7-line mirror of scripts/failures/__init__.py)

```python
"""Taste Gate feedback pipeline — D-12 appender to .claude/failures/FAILURES.md.

Phase 9 ships record_feedback.py; Phase 10 may add taste_gate/selector.py for
auto selection of top-3/bottom-3 by 3-sec retention (currently manual).
"""
```
</interfaces>
</context>

<tasks>

<task id="9-00-01">
  <action>
Create `tests/phase09/__init__.py` as a single-blank-line package marker (D-13 Phase 7 precedent — independent Phase 9 test package).

Create `scripts/taste_gate/__init__.py` as 7-line namespace marker. Exact content:

```python
"""Taste Gate feedback pipeline — D-12 appender to .claude/failures/FAILURES.md.

Phase 9 ships record_feedback.py; Phase 10 may add taste_gate/selector.py for
auto selection of top-3/bottom-3 by 3-sec retention (currently manual).

Mirrors scripts/failures/__init__.py namespace discipline (stdlib-only downstream).
"""
```

Create `docs/.gitkeep` as empty file (so docs/ directory is git-tracked; Plan 09-01 writes ARCHITECTURE.md into it). Use empty string content.

Create `tests/phase09/conftest.py` (~110 lines) with the 3 fixtures specified in the `<interfaces>` block. The file MUST start with:

```python
"""Phase 9 documentation + KPI + Taste Gate shared fixtures.

D-13 independence from phase05/06/07/08 conftests per Phase 7 precedent.
Per 09-CONTEXT.md D-10 (synthetic sample 6) + D-12 (FAILURES append-only) + D-14 (synthetic E2E).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# UTF-8 safeguard for Windows cp949 per Phase 6 Plan 06-09 STATE #28 + Research Pitfall 7
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[2]
KST = ZoneInfo("Asia/Seoul")
```

Then define the 3 fixtures. The `synthetic_taste_gate_april` fixture body MUST write the EXACT synthetic sample from 09-RESEARCH.md §Code Examples Example 2 (6 rows with 탐정/조수 페르소나 titles — NO placeholder like "테스트용 쇼츠 #1" per CONTEXT.md §specifics). Use obviously-fake 6-char video_ids per Research Pitfall 3:

```
상위 3:
  1 | abc123 | "탐정이 조수에게 묻다: 23살 범인의 진짜 동기?" | 68% | 42% | 27초 | 5 | 완성도 우수 | 재생산
  2 | def456 | "100억 갑부가 딱 한 번 울었던 순간"            | 64% | 41% | 26초 | 4 | 훌륭함    | 유지
  3 | ghi789 | "3번째 편지의 의미를 아시나요?"                | 61% | 40% | 25초 | 4 | 좋음      | 유지
하위 3:
  4 | jkl012 | "조수가 놓친 단서"                             | 48% | 28% | 19초 | 3 | hook 약함 | 재제작
  5 | mno345 | "5번 방문한 이유"                              | 45% | 25% | 17초 | 2 | 지루함    | 폐기
  6 | pqr678 | "범인의 마지막 말"                             | 42% | 24% | 16초 | 1 | 결말 처참 | 폐기
```

The `tmp_failures_md` fixture MUST write a seed FAILURES.md at tmp_path with minimum Phase 6 schema (frontmatter + `## Failures` heading + 1 existing entry placeholder) and `monkeypatch.setattr("scripts.taste_gate.record_feedback.FAILURES_PATH", tmp_path / "FAILURES.md")` — NOTE: the monkeypatch must be a no-op if scripts.taste_gate.record_feedback not yet importable (Wave 0 RED state). Use `pytest.importorskip("scripts.taste_gate.record_feedback", reason="Plan 09-04 not yet shipped")` guard pattern.

The `freeze_kst_2026_04_01` fixture freezes to `datetime(2026, 4, 1, 9, 0, 0, tzinfo=KST)` via a class that shadows `datetime.now`.
  </action>
  <read_first>
    - tests/phase08/conftest.py (D-13 independent conftest pattern + cp949 guard + _REPO_ROOT)
    - tests/phase08/phase08_acceptance.py (SC aggregator shape)
    - scripts/failures/__init__.py (namespace marker 7-line pattern)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md (D-10 synthetic sample + D-13 score filter)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Code Examples Example 2 (fixture body)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Pitfall 3 (fake 6-char video_ids) + §Pitfall 7 (cp949)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md §Wave 0 Requirements
  </read_first>
  <acceptance_criteria>
    - `test -f tests/phase09/__init__.py` exits 0
    - `test -f scripts/taste_gate/__init__.py` exits 0
    - `test -f docs/.gitkeep` exits 0
    - `wc -l < scripts/taste_gate/__init__.py` outputs between 5 and 10
    - `grep -c "def synthetic_taste_gate_april\|def tmp_failures_md\|def freeze_kst_2026_04_01" tests/phase09/conftest.py` outputs `3`
    - `grep -c "sys.stdout.reconfigure" tests/phase09/conftest.py` outputs `>= 1`
    - `grep -c "탐정이 조수에게 묻다" tests/phase09/conftest.py` outputs `>= 1` (synthetic Korean title present, no placeholder)
    - `grep -c "테스트용 쇼츠" tests/phase09/conftest.py` outputs `0` (CONTEXT.md forbids placeholder)
    - `grep -c "abc123\|def456\|ghi789\|jkl012\|mno345\|pqr678" tests/phase09/conftest.py` outputs `>= 6` (all 6 fake IDs present)
    - `python -c "import ast; ast.parse(open('tests/phase09/conftest.py', encoding='utf-8').read())"` exits 0
    - `python -m pytest tests/phase09/ --collect-only -q` exits 0 (Wave 0 collects even if body is stubs)
  </acceptance_criteria>
  <automated>python -m pytest tests/phase09/ --collect-only -q --no-cov</automated>
  <task_type>impl</task_type>
</task>

<task id="9-00-02">
  <action>
Create 7 RED test stub files under `tests/phase09/`. Each MUST be collectible by pytest (`--collect-only` succeeds) but tests within MAY fail with `FileNotFoundError` or `AssertionError` until downstream plans ship the implementation.

**File 1: `tests/phase09/test_architecture_doc_structure.py`** (~70 lines) — mirrors 09-RESEARCH.md §Code Examples Example 3 exactly. Required tests:

```python
"""SC#1 — docs/ARCHITECTURE.md structure validators (Plan 09-01 target)."""
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
    # Soft order check: all 4 section markers present
    assert re.search(r"12\s*GATE|State\s*Machine", content, re.IGNORECASE), "Missing State Machine section"
    assert re.search(r"17\s*[Ii]nspector|[Aa]gent\s*[Tt]ree|[Aa]gent\s*[Tt]eam", content), "Missing Agent Team section"
    assert re.search(r"3-?[Tt]ier|[Ww]iki", content), "Missing 3-Tier Wiki section"
    assert re.search(r"[Ee]xternal|[Yy]ou[Tt]ube|[Gg]it[Hh]ub|[Nn]otebook[Ll][Mm]", content), "Missing External Integrations section"
```

**File 2: `tests/phase09/test_kpi_log_schema.py`** (~60 lines) — KPI-06 + SC#2:

```python
"""KPI-06 + SC#2 — wiki/kpi/kpi_log.md Hybrid format validators (Plan 09-02 target)."""
from __future__ import annotations

from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
KPI_LOG = _REPO_ROOT / "wiki" / "kpi" / "kpi_log.md"


def _read_kpi_log() -> str:
    if not KPI_LOG.exists():
        pytest.skip(f"{KPI_LOG} not yet created — Plan 09-02 target", allow_module_level=False)
    return KPI_LOG.read_text(encoding="utf-8")


def test_kpi_log_exists():
    assert KPI_LOG.exists(), f"{KPI_LOG} not created (Plan 09-02 target)"


def test_target_declaration():
    """KPI-06: 3 KPI targets (3sec retention > 60% / completion > 40% / avg watch > 25sec) explicit."""
    content = _read_kpi_log()
    # 3 targets literal presence
    assert "60%" in content and "3초 retention" in content or "3sec_retention" in content, "Missing 3-sec retention > 60% target"
    assert "40%" in content and ("완주율" in content or "completion" in content.lower()), "Missing completion rate > 40% target"
    assert "25" in content and ("평균 시청" in content or "avg" in content.lower()), "Missing avg watch > 25초 target"


def test_api_contract_present():
    """D-07: YouTube Analytics v2 endpoint + OAuth scope + metric names declared."""
    content = _read_kpi_log()
    assert "youtubeanalytics.googleapis.com/v2/reports" in content, "Missing YouTube Analytics v2 endpoint"
    assert "yt-analytics.readonly" in content, "Missing OAuth scope yt-analytics.readonly"
    assert "audienceWatchRatio" in content, "Missing metric audienceWatchRatio"
    assert "averageViewDuration" in content, "Missing metric averageViewDuration"


def test_hybrid_structure():
    """D-06: Hybrid format — Part A Target Declaration + Part B Monthly Tracking both present."""
    content = _read_kpi_log()
    assert "Part A" in content and "Target Declaration" in content, "Missing Part A Target Declaration section"
    assert "Part B" in content and ("Monthly Tracking" in content or "월별" in content), "Missing Part B Monthly Tracking section"
    # Part B monthly tracking table columns
    for col in ["video_id", "title", "3sec_retention", "completion_rate", "avg_view_sec", "taste_gate_rank"]:
        assert col in content, f"Missing Part B column: {col}"


def test_failure_thresholds_declared():
    """D-06: "실패 정의" section with re-creation trigger thresholds."""
    content = _read_kpi_log()
    assert "실패" in content or "재제작" in content, "Missing failure/re-creation trigger definition"
    assert "50%" in content, "Missing 3sec retention < 50% re-creation threshold"
```

**File 3: `tests/phase09/test_taste_gate_form_schema.py`** (~70 lines) — KPI-05 + SC#3:

```python
"""KPI-05 + SC#3 — taste_gate_protocol.md + taste_gate_2026-04.md validators (Plan 09-03 target)."""
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
    # 6 fake 6-char video_ids per Pitfall 3
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
    # At least one persona-relevant keyword
    assert re.search(r"탐정|조수|범인|갑부|편지", content), "Missing persona-relevant title keyword"
```

**File 4: `tests/phase09/test_record_feedback.py`** (~60 lines) — KPI-05 parser stub:

```python
"""KPI-05 parser — scripts/taste_gate/record_feedback.py (Plan 09-04 target).

Wave 0 state: skip if module not importable. Plan 09-04 makes tests runnable.
"""
from __future__ import annotations

import pytest

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py",
)


def test_parse_six_rows(synthetic_taste_gate_april, monkeypatch):
    """KPI-05: parse_taste_gate returns 6 evaluated rows from fixture."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    rows = record_feedback.parse_taste_gate("2026-04")
    assert len(rows) == 6, f"Expected 6 rows, got {len(rows)}"


def test_parse_extracts_required_fields(synthetic_taste_gate_april, monkeypatch):
    """KPI-05: each row has video_id, title, score, comment extracted."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    rows = record_feedback.parse_taste_gate("2026-04")
    row0 = rows[0]
    assert row0["video_id"] == "abc123"
    assert isinstance(row0["score"], int)
    assert 1 <= row0["score"] <= 5
    assert "comment" in row0
    assert "title" in row0


def test_parse_raises_on_missing_file(tmp_path, monkeypatch):
    """Pitfall 5: explicit Korean error on missing file (not silent)."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", tmp_path)
    with pytest.raises(record_feedback.TasteGateParseError) as exc:
        record_feedback.parse_taste_gate("2026-04")
    assert "파일 없음" in str(exc.value)


def test_parse_raises_on_malformed_score(tmp_path, monkeypatch):
    """Pitfall 5: score outside 1-5 → explicit Korean raise."""
    bad = tmp_path / "taste_gate_2026-04.md"
    bad.write_text(
        "| 1 | abc123 | \"t\" | 68% | 42% | 27초 | 9 | c | tag |\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", tmp_path)
    # Malformed score 9 must not silently pass — either raise or skip with warning
    rows = record_feedback.parse_taste_gate("2026-04")
    # If skipped (underscore pattern), rows should be empty → raises "평가된 행이 없습니다"
    # Implementation in Plan 09-04 resolves this path.
```

**File 5: `tests/phase09/test_score_threshold_filter.py`** (~50 lines) — D-13 filter:

```python
"""D-13: only score <= 3 escalates to FAILURES.md (Plan 09-04 target)."""
from __future__ import annotations

import pytest

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py",
)


def test_filter_includes_score_1():
    rows = [{"video_id": "a", "score": 1, "title": "t", "comment": "c"}]
    assert record_feedback.filter_escalate(rows) == rows


def test_filter_includes_score_2():
    rows = [{"video_id": "a", "score": 2, "title": "t", "comment": "c"}]
    assert len(record_feedback.filter_escalate(rows)) == 1


def test_filter_includes_score_3_boundary():
    """D-13 boundary: score == 3 escalates (<=)."""
    rows = [{"video_id": "a", "score": 3, "title": "t", "comment": "c"}]
    assert len(record_feedback.filter_escalate(rows)) == 1


def test_filter_excludes_score_4():
    rows = [{"video_id": "a", "score": 4, "title": "t", "comment": "c"}]
    assert record_feedback.filter_escalate(rows) == []


def test_filter_excludes_score_5():
    rows = [{"video_id": "a", "score": 5, "title": "t", "comment": "c"}]
    assert record_feedback.filter_escalate(rows) == []


def test_filter_mixed_six_rows(synthetic_taste_gate_april, monkeypatch):
    """D-13: synthetic sample has scores [5,4,4,3,2,1] → 3 escalated (3,2,1)."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    rows = record_feedback.parse_taste_gate("2026-04")
    escalated = record_feedback.filter_escalate(rows)
    assert len(escalated) == 3, f"D-13 expected 3 escalations (scores 1/2/3), got {len(escalated)}"
    assert all(r["score"] <= 3 for r in escalated)
```

**File 6: `tests/phase09/test_failures_append_only.py`** (~60 lines) — D-12 Hook compat:

```python
"""D-12: record_feedback.py write must be Phase 6 Hook check_failures_append_only compatible (Plan 09-04 target).

Pitfall 2: open('a') direct is Hook-safe but "read+append+write full" preserves prior content as
prefix (Hook accepts either form). Verify via AST scan + write-preserve assertion.
"""
from __future__ import annotations

import ast
from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = _REPO_ROOT / "scripts" / "taste_gate" / "record_feedback.py"

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py",
)


def test_source_file_exists():
    assert SRC.exists(), f"{SRC} not yet created (Plan 09-04 target)"


def test_no_open_w_for_failures():
    """D-12 Pitfall 2: no `open(FAILURES_PATH, 'w')` — either 'a' mode or read+append+write pattern."""
    src_text = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
                assert mode != "w", (
                    "Pitfall 2: open(path, 'w') truncates FAILURES.md — must use 'a' or read+append+write"
                )


def test_append_preserves_prior_content(tmp_failures_md, freeze_kst_2026_04_01, monkeypatch):
    """D-12: append operation preserves existing FAILURES.md content as prefix."""
    prior = tmp_failures_md.read_text(encoding="utf-8")
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)
    block = record_feedback.build_failures_block("2026-04", [
        {"video_id": "jkl012", "score": 3, "title": "t", "comment": "c"}
    ])
    record_feedback.append_to_failures(block)
    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after.startswith(prior), "D-12 violated: prior content not preserved as prefix"
    assert "[taste_gate] 2026-04" in after, "New taste_gate block not appended"


def test_no_skip_gates_string():
    """Hook 3종 차단: scripts/taste_gate/record_feedback.py MUST NOT contain skip_gates string."""
    src_text = SRC.read_text(encoding="utf-8")
    assert "skip_gates" not in src_text, "skip_gates physically banned (pre_tool_use Hook)"


def test_no_todo_next_session():
    """Hook 3종 차단: no TODO(next-session) patterns."""
    src_text = SRC.read_text(encoding="utf-8")
    assert "TODO(next-session)" not in src_text, "TODO(next-session) physically banned (pre_tool_use Hook)"


def test_no_try_except_silent_fallback():
    """Hook 3종 차단: no bare try/except: pass patterns."""
    src_text = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for h in node.handlers:
                # Silent fallback = pass-only body + no raise
                if len(h.body) == 1 and isinstance(h.body[0], ast.Pass):
                    pytest.fail("try/except: pass silent fallback banned (Pitfall 6)")
```

**File 7: `tests/phase09/test_e2e_synthetic_dry_run.py`** (~50 lines) — SC#4 E2E stub:

```python
"""SC#4 — end-to-end synthetic dry-run (Plan 09-05 target).

Wave 0 state: skip if Plan 09-04 record_feedback.py not yet shipped.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

record_feedback = pytest.importorskip(
    "scripts.taste_gate.record_feedback",
    reason="Plan 09-04 ships record_feedback.py; Plan 09-05 activates E2E",
)


def test_e2e_parse_filter_append(synthetic_taste_gate_april, tmp_failures_md, freeze_kst_2026_04_01, monkeypatch):
    """SC#4: synthetic dry-run → record_feedback.py → FAILURES.md has new [taste_gate] 2026-04 entry."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)

    prior = tmp_failures_md.read_text(encoding="utf-8")
    rc = record_feedback.main(["--month", "2026-04"])
    assert rc == 0, f"record_feedback.main returned {rc}, expected 0"

    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after.startswith(prior), "D-12: prior FAILURES content must be preserved as prefix"
    assert "### [taste_gate] 2026-04" in after, "New [taste_gate] 2026-04 section not found"


def test_e2e_dry_run_no_write(synthetic_taste_gate_april, tmp_failures_md, monkeypatch):
    """SC#4: --dry-run prints block but does NOT write FAILURES.md."""
    monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)
    monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)
    prior = tmp_failures_md.read_text(encoding="utf-8")
    rc = record_feedback.main(["--month", "2026-04", "--dry-run"])
    assert rc == 0
    after = tmp_failures_md.read_text(encoding="utf-8")
    assert after == prior, "--dry-run must NOT modify FAILURES.md"
```

All 7 files MUST end with trailing newline. All imports MUST use absolute `from scripts.taste_gate...` (not relative).
  </action>
  <read_first>
    - tests/phase08/test_scaffold.py (Wave 0 smoke test shape)
    - tests/phase08/phase08_acceptance.py (aggregator skeleton)
    - scripts/failures/aggregate_patterns.py (CLI + parse + error handling patterns)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Code Examples Example 3 (test patterns verbatim)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Validation Architecture §Phase Requirements → Test Map
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md §Wave 0 Requirements + §Per-Task Verification Map
  </read_first>
  <acceptance_criteria>
    - `test -f tests/phase09/test_architecture_doc_structure.py` exits 0
    - `test -f tests/phase09/test_kpi_log_schema.py` exits 0
    - `test -f tests/phase09/test_taste_gate_form_schema.py` exits 0
    - `test -f tests/phase09/test_record_feedback.py` exits 0
    - `test -f tests/phase09/test_score_threshold_filter.py` exits 0
    - `test -f tests/phase09/test_failures_append_only.py` exits 0
    - `test -f tests/phase09/test_e2e_synthetic_dry_run.py` exits 0
    - `grep -c "def test_" tests/phase09/test_architecture_doc_structure.py` outputs `>= 5`
    - `grep -c "def test_" tests/phase09/test_kpi_log_schema.py` outputs `>= 4`
    - `grep -c "def test_" tests/phase09/test_taste_gate_form_schema.py` outputs `>= 5`
    - `grep -c "def test_" tests/phase09/test_record_feedback.py` outputs `>= 3`
    - `grep -c "def test_" tests/phase09/test_score_threshold_filter.py` outputs `>= 5`
    - `grep -c "def test_" tests/phase09/test_failures_append_only.py` outputs `>= 5`
    - `grep -c "def test_" tests/phase09/test_e2e_synthetic_dry_run.py` outputs `>= 2`
    - `grep -rn "pytest.importorskip" tests/phase09/ | wc -l` outputs `>= 4` (Plan 09-04 downstream guarded)
    - `python -m pytest tests/phase09/ --collect-only -q --no-cov` exits 0 (all 7 files collectible)
    - `python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('tests/phase09').glob('test_*.py')]"` exits 0 (all files parse-valid)
  </acceptance_criteria>
  <automated>python -m pytest tests/phase09/ --collect-only -q --no-cov</automated>
  <task_type>impl</task_type>
</task>

<task id="9-00-03">
  <action>
Create `tests/phase09/phase09_acceptance.py` (~80 lines) exactly as the skeleton shown in the `<interfaces>` block. The 4 SC aggregator functions (`sc1_architecture_doc`, `sc2_kpi_log_hybrid`, `sc3_taste_gate_protocol_and_dryrun`, `sc4_e2e_synthetic_dryrun`) MUST return `False` at Wave 0 so the aggregator exits 1 (RED by design — Plan 09-05 flips each to concrete checks and makes it exit 0).

File header MUST include:

```python
#!/usr/bin/env python3
"""Phase 9 acceptance aggregator — SC 1-4 rolled into single exit code.

Mirror of tests/phase08/phase08_acceptance.py pattern.

Wave 0 state: ALL SC return False → exit 1 (RED by design).
Plan 09-05 flips each aggregator to concrete checks → exit 0 on green.

Usage:
    python tests/phase09/phase09_acceptance.py

Exit codes:
    0 = all SC green (phase gate open)
    1 = any SC red (phase gate closed)
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
```

After the 4 stub aggregator functions defined to return `False`, add the `main()` dispatcher exactly as shown in `<interfaces>`.

Run full regression sweep to confirm Phase 4-8 baseline preserved:

```
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 -q --no-cov --co
```

MUST exit 0 (all collections still pass; Wave 0 adds no prod code so nothing should break).

Then run Phase 9 collection check:

```
python -m pytest tests/phase09/ --collect-only -q --no-cov
```

MUST exit 0. Individual tests may fail on actual run (expected — downstream plans not shipped yet), but collection MUST succeed.

Final: run `python tests/phase09/phase09_acceptance.py` → MUST exit 1 (Wave 0 RED baseline).
  </action>
  <read_first>
    - tests/phase08/phase08_acceptance.py (aggregator shape + sys.exit logic + cp949 guard)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Validation Architecture §SC → Test Map
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md §Wave 0 Requirements line "phase09_acceptance.py SC 1-4 aggregator"
  </read_first>
  <acceptance_criteria>
    - `test -f tests/phase09/phase09_acceptance.py` exits 0
    - `grep -c "def sc1_architecture_doc\|def sc2_kpi_log_hybrid\|def sc3_taste_gate_protocol_and_dryrun\|def sc4_e2e_synthetic_dryrun" tests/phase09/phase09_acceptance.py` outputs `4`
    - `grep -c "sys.stdout.reconfigure" tests/phase09/phase09_acceptance.py` outputs `>= 1`
    - `python -c "import ast; ast.parse(open('tests/phase09/phase09_acceptance.py', encoding='utf-8').read())"` exits 0
    - `python tests/phase09/phase09_acceptance.py; test $? -eq 1` exits 0 (Wave 0 RED baseline = aggregator exit 1)
    - `python -m pytest tests/phase09/ --collect-only -q --no-cov` exits 0
    - `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov` exits 0 (regression baseline preserved)
  </acceptance_criteria>
  <automated>python tests/phase09/phase09_acceptance.py; test $? -eq 1</automated>
  <task_type>impl</task_type>
</task>

</tasks>

<verification>
1. tests/phase09/__init__.py + scripts/taste_gate/__init__.py + docs/.gitkeep exist on disk.
2. tests/phase09/conftest.py defines 3 fixtures with 탐정/조수 persona content (no placeholder).
3. 7 RED test stubs collectible by pytest (`--collect-only` exits 0).
4. phase09_acceptance.py exits 1 (Wave 0 RED baseline by design).
5. Phase 4-8 regression sweep still 986+ tests collecting (scaffold-only changes).
6. No skip_gates / TODO(next-session) / try-except-pass anywhere in Wave 0 files.
</verification>

<success_criteria>
Plan 09-00 is COMPLETE when:
- tests/phase09/ scaffold exists (1 __init__ + 1 conftest + 7 test stubs + 1 acceptance aggregator = 10 files).
- scripts/taste_gate/ namespace exists (7-line __init__.py mirror).
- docs/ directory exists (via .gitkeep).
- Wave 0 RED state proven: phase09_acceptance.py exits 1; downstream tests skip with importorskip for Plan 09-04 dependencies.
- All downstream Waves 1-3 unblocked:
  - Wave 1 Plan 09-01 (ARCHITECTURE.md) → test_architecture_doc_structure.py awaits
  - Wave 1 Plan 09-02 (kpi_log.md) → test_kpi_log_schema.py awaits
  - Wave 1 Plan 09-03 (taste_gate_*.md) → test_taste_gate_form_schema.py awaits
  - Wave 2 Plan 09-04 (record_feedback.py) → test_record_feedback.py + test_score_threshold_filter.py + test_failures_append_only.py await
  - Wave 3 Plan 09-05 (E2E + phase gate) → test_e2e_synthetic_dry_run.py + phase09_acceptance.py flip await
- Phase 4-8 986+ regression baseline preserved (scaffold-only change, no production side effects).
</success_criteria>

<output>
Create `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-00-SUMMARY.md` documenting:
- Files created (12: 1 pkg marker + 1 conftest + 7 test stubs + 1 aggregator + 1 namespace marker + 1 .gitkeep)
- 3 fixture signatures shipped
- 7 RED test file counts (grep test_ counts)
- phase09_acceptance.py exit 1 confirmed (Wave 0 RED baseline)
- Phase 4-8 collection pass confirmed
- Commit hashes (expected 3 atomic commits)
</output>
