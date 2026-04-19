#!/usr/bin/env python3
"""Phase 9 acceptance aggregator — SC 1-4 rolled into single exit code.

Mirror of ``scripts/validate/phase08_acceptance.py`` pattern (project
canonical shape — Phase 7/8 precedent), adapted to the Phase 9 SC surface.
SC 1-3 perform concrete literal-string checks against on-disk artifacts;
SC 4 delegates to the Phase 9 E2E pytest module so the synthetic dry-run
end-to-end chain is exercised without duplication.

Wave 0 shipped all four aggregators as stubs returning False (RED by design).
Plan 09-05 flips each to the concrete check described below.

Usage::

    python tests/phase09/phase09_acceptance.py

Exit codes
----------
* 0 = all SC green (phase gate open)
* 1 = any SC red (phase gate closed)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# SC#1 — ARCHITECTURE.md structural invariants (30-min onboarding anchor).
# ---------------------------------------------------------------------------


def sc1_architecture_doc() -> bool:
    """SC#1: ``docs/ARCHITECTURE.md`` exists and carries all structural
    invariants required for a 30-min onboarding read:

    * ≥ 3 fenced ``\u0060\u0060\u0060mermaid`` blocks (state + flow + sequence/etc).
    * Literal ``stateDiagram-v2`` (12 GATE state machine rendering).
    * Literal ``flowchart TD`` or ``flowchart LR`` (DAG/layered view).
    * ``TL;DR`` marker in the first 50 lines (near-top skim anchor).
    * ≥ 4 per-section reading-time markers (``⏱ ~N min`` / ``⏱ N min``).
    * Sum of declared reading-time minutes ≤ 35 (safety tolerance over
      the 30-min target).
    """
    path = _REPO_ROOT / "docs" / "ARCHITECTURE.md"
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")

    mermaid_blocks = re.findall(r"^```mermaid\s*$", content, re.MULTILINE)
    if len(mermaid_blocks) < 3:
        return False
    if "stateDiagram-v2" not in content:
        return False
    if re.search(r"flowchart (TD|LR)", content) is None:
        return False

    lines = content.splitlines()
    tldr_line = None
    for i, line in enumerate(lines[:50]):
        if "TL;DR" in line or "TLDR" in line:
            tldr_line = i
            break
    if tldr_line is None:
        return False

    reading_times = re.findall(r"⏱\s*~?(\d+)\s*min", content)
    if len(reading_times) < 4:
        return False
    if sum(int(t) for t in reading_times) > 35:
        return False

    return True


# ---------------------------------------------------------------------------
# SC#2 — kpi_log.md Hybrid format (Part A target + Part B tracking).
# ---------------------------------------------------------------------------


def sc2_kpi_log_hybrid() -> bool:
    """SC#2: ``wiki/kpi/kpi_log.md`` exists and embeds the 14 canonical
    literal strings anchoring the Hybrid format declared in KPI-06 +
    RESEARCH Area 3 (YouTube Analytics v2 API contract).
    """
    path = _REPO_ROOT / "wiki" / "kpi" / "kpi_log.md"
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    required = [
        "Part A",
        "Part B",
        "Target Declaration",
        "Monthly Tracking",
        "60%",
        "40%",
        "3초 retention",
        "완주율",
        "youtubeanalytics.googleapis.com/v2/reports",
        "yt-analytics.readonly",
        "audienceWatchRatio",
        "averageViewDuration",
        "video_id",
        "taste_gate_rank",
    ]
    for literal in required:
        if literal not in content:
            return False
    return True


# ---------------------------------------------------------------------------
# SC#3 — taste_gate_protocol.md + taste_gate_2026-04.md (KPI-05).
# ---------------------------------------------------------------------------


def sc3_taste_gate_protocol_and_dryrun() -> bool:
    """SC#3: ``wiki/kpi/taste_gate_protocol.md`` + ``wiki/kpi/
    taste_gate_2026-04.md`` both exist, protocol covers monthly cadence
    + top/bottom 3 selection + KST window, dry-run declares
    ``status: dry-run`` and carries all 6 synthetic video IDs (abc123,
    def456, ghi789, jkl012, mno345, pqr678) with no placeholder title
    ``테스트용 쇼츠`` (Research Pitfall 3 — obviously-fake IDs only).
    """
    protocol = _REPO_ROOT / "wiki" / "kpi" / "taste_gate_protocol.md"
    dryrun = _REPO_ROOT / "wiki" / "kpi" / "taste_gate_2026-04.md"
    if not protocol.exists() or not dryrun.exists():
        return False

    protocol_text = protocol.read_text(encoding="utf-8")
    for literal in ("매월 1일", "KST 09:00", "상위 3", "하위 3"):
        if literal not in protocol_text:
            return False

    dryrun_text = dryrun.read_text(encoding="utf-8")
    if "status: dry-run" not in dryrun_text:
        return False
    for vid in ("abc123", "def456", "ghi789", "jkl012", "mno345", "pqr678"):
        if vid not in dryrun_text:
            return False
    if "테스트용 쇼츠" in dryrun_text:
        return False

    return True


# ---------------------------------------------------------------------------
# SC#4 — synthetic dry-run E2E (subprocess-invoke Phase 9 test module).
# ---------------------------------------------------------------------------


def sc4_e2e_synthetic_dryrun() -> bool:
    """SC#4: ``tests/phase09/test_e2e_synthetic_dry_run.py`` passes in a
    clean subprocess (fixture-driven; monkeypatches
    ``record_feedback.TASTE_GATE_DIR`` and ``FAILURES_PATH`` to tmp
    paths, asserts 3 escalations + prefix preservation + KST marker).
    """
    argv = [
        sys.executable,
        "-m",
        "pytest",
        "tests/phase09/test_e2e_synthetic_dry_run.py",
        "-x",
        "--no-cov",
        "-q",
    ]
    result = subprocess.run(
        argv,
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------------------


def main() -> int:
    results = {
        "SC#1": sc1_architecture_doc(),
        "SC#2": sc2_kpi_log_hybrid(),
        "SC#3": sc3_taste_gate_protocol_and_dryrun(),
        "SC#4": sc4_e2e_synthetic_dryrun(),
    }
    for k, v in results.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    print("---")
    if all(results.values()):
        print("Phase 9 acceptance: ALL_PASS")
        return 0
    print("Phase 9 acceptance: FAIL")
    return 1


if __name__ == "__main__":
    # Windows cp949 guard — Phase 6 STATE #28 precedent.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
