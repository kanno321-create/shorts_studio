#!/usr/bin/env python3
"""Phase 8 acceptance aggregator — SC1-6 subprocess wrapper.

Mirrors scripts/validate/phase07_acceptance.py (Phase 7 Plan 07-08 canonical
format). Subprocess-invokes each SC's pytest bundle, labels PASS/FAIL per
SC line, and returns 0 iff all 6 SC groups report PASS.

SC mapping (canonical — see .planning/phases/08-remote-publishing-production-metadata/08-VALIDATION.md):
  SC1: GitHub mirror created + main pushed (REMOTE-01/02)
        -> test_github_remote_create.py + test_github_push_main.py
  SC2: Submodule + .gitmodules schema (REMOTE-03)
        -> test_submodule_add.py
  SC3: AI disclosure anchor + zero selenium/webdriver/playwright (PUB-01/02)
        -> test_ai_disclosure_anchor.py + test_no_selenium_anchor.py
  SC4: 48h+ lock + KST weekday 20-23 + KST weekend 12-15 (PUB-03)
        -> test_publish_lock_48h.py + test_kst_window_weekday.py
         + test_kst_window_weekend.py
  SC5: production_metadata 4-field + HTML comment (PUB-04)
        -> test_production_metadata_schema.py + test_metadata_html_comment.py
  SC6: Pinned comment + funnel + end-screen non-existent anchor (PUB-05)
        -> test_pinned_comment.py + test_endscreen_nonexistent_anchor.py
         + test_uploader_mocked_e2e.py

Run: python scripts/validate/phase08_acceptance.py
Exit 0 = ALL SC green. Exit 1 = any SC FAIL. Prints per-SC `SC<N>: STATUS — description`
lines + final `Phase 8 acceptance: ALL_PASS|FAIL` marker so downstream tooling
(tests/phase08/test_phase08_acceptance.py) can subprocess-assert the output.

Stdlib-only. UTF-8 subprocess encoding + errors="replace" to survive Windows
cp949 environments (Pitfall 3 / Phase 6 STATE #28).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# scripts/validate/phase08_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]


_SC_MAP: dict[str, dict] = {
    "SC1": {
        "description": "GitHub mirror created + main pushed (REMOTE-01/02)",
        "tests": [
            "tests/phase08/test_github_remote_create.py",
            "tests/phase08/test_github_push_main.py",
        ],
    },
    "SC2": {
        "description": "Submodule + .gitmodules schema (REMOTE-03)",
        "tests": [
            "tests/phase08/test_submodule_add.py",
        ],
    },
    "SC3": {
        "description": "AI disclosure anchor + zero selenium/webdriver/playwright (PUB-01/02)",
        "tests": [
            "tests/phase08/test_ai_disclosure_anchor.py",
            "tests/phase08/test_no_selenium_anchor.py",
        ],
    },
    "SC4": {
        "description": "48h+ lock + KST weekday 20-23 + KST weekend 12-15 (PUB-03)",
        "tests": [
            "tests/phase08/test_publish_lock_48h.py",
            "tests/phase08/test_kst_window_weekday.py",
            "tests/phase08/test_kst_window_weekend.py",
        ],
    },
    "SC5": {
        "description": "production_metadata 4-field + HTML comment (PUB-04)",
        "tests": [
            "tests/phase08/test_production_metadata_schema.py",
            "tests/phase08/test_metadata_html_comment.py",
        ],
    },
    "SC6": {
        "description": "Pinned comment + funnel + end-screen non-existent anchor (PUB-05)",
        "tests": [
            "tests/phase08/test_pinned_comment.py",
            "tests/phase08/test_endscreen_nonexistent_anchor.py",
            "tests/phase08/test_uploader_mocked_e2e.py",
        ],
    },
}


def main() -> int:
    results: dict[str, str] = {}
    for sc, spec in _SC_MAP.items():
        argv = [sys.executable, "-m", "pytest", *spec["tests"], "-q", "--no-cov"]
        proc = subprocess.run(
            argv,
            cwd=str(REPO),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        status = "PASS" if proc.returncode == 0 else "FAIL"
        results[sc] = status
        print(f"{sc}: {status} — {spec['description']}")
        if status == "FAIL":
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:])

    print("---")
    all_pass = all(v == "PASS" for v in results.values())
    print(f"Phase 8 acceptance: {'ALL_PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    # Windows cp949 guard — Pitfall 3 + Phase 6 STATE #28.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
