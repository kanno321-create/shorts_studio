#!/usr/bin/env python3
"""Phase 6 Success Criteria 1~6 acceptance verifier.

SC mapping (from ROADMAP.md Phase 6):
  SC1: 5 wiki categories each have >=1 ready node; refs resolve from agent prompts
  SC2: NotebookLM 2 notebooks in library.json; 1 sanity query succeeds (dry-run OK in Phase 6)
  SC3: Fallback Chain 3-tier works under simulated RAG failure
  SC4: Continuity Prefix auto-injected at Shotstack filter[0]
  SC5: FAILURES.md append-only enforced + SKILL_HISTORY backup created
  SC6: aggregate_patterns.py --dry-run emits valid JSON with candidates schema

Run: python scripts/validate/phase06_acceptance.py
Exit 0 = ALL SC green. Exit 1 = any SC FAIL. Prints markdown table so
downstream tooling can capture it.

At Wave 0 (after Plan 01 only), SC2-SC6 WILL report FAIL — their underlying
plans have not shipped yet. This script MUST NOT crash in that case; exit 1
with PASS/FAIL table is acceptable. Exit 2+ means the script itself broke.

Stdlib-only. UTF-8 subprocess encoding (STATE decision #28 — Windows cp949
cannot decode em-dash / Korean pytest output).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# scripts/validate/phase06_acceptance.py -> parents[2] = studios/shorts/
REPO = Path(__file__).resolve().parents[2]


def _run(
    cmd: list[str], cwd: Path = REPO, timeout: int = 60
) -> tuple[int, str, str]:
    """Run a subprocess; return (returncode, stdout, stderr).

    Uses UTF-8 decoding with replacement to survive cp949 environments.
    FileNotFoundError and TimeoutExpired are caught so the CLI never
    crashes on infrastructure gaps (Wave 0 acceptance requirement).
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, "", f"timeout: {e}"
    return p.returncode, p.stdout or "", p.stderr or ""


def sc1_wiki_ready_nodes() -> tuple[bool, str]:
    """SC 1: Every D-2 category has at least one status=ready .md node (excluding MOC.md)."""
    wiki = REPO / "wiki"
    if not wiki.exists():
        return False, "wiki/ missing"
    cats = ["algorithm", "ypp", "render", "kpi", "continuity_bible"]
    missing: list[str] = []
    for cat in cats:
        cat_dir = wiki / cat
        if not cat_dir.exists():
            missing.append(f"{cat} dir missing")
            continue
        ready_found = False
        for md in cat_dir.glob("*.md"):
            if md.name == "MOC.md":
                continue
            text = md.read_text(encoding="utf-8", errors="replace")
            if "status: ready" in text:
                ready_found = True
                break
        if not ready_found:
            missing.append(f"{cat}: no ready node")
    return (
        len(missing) == 0,
        "5/5 categories ready" if not missing else "; ".join(missing),
    )


def sc2_notebooklm_registered() -> tuple[bool, str]:
    """SC 2: Plan 04 appends naberal-shorts-channel-bible to external skill library.json."""
    rc, _out, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase06/test_library_json_channel_bible.py",
            "-q",
            "--no-cov",
        ]
    )
    return (
        rc == 0,
        "library.json channel-bible entry present" if rc == 0 else err[-400:],
    )


def sc3_fallback_chain() -> tuple[bool, str]:
    """SC 3: 3-tier NotebookLM fallback (RAG -> grep wiki -> hardcoded)."""
    rc, _out, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase06/test_fallback_chain.py",
            "tests/phase06/test_fallback_injection.py",
            "-q",
            "--no-cov",
        ]
    )
    return rc == 0, "fallback 3-tier green" if rc == 0 else err[-400:]


def sc4_continuity_prefix() -> tuple[bool, str]:
    """SC 4: ContinuityPrefix schema + Shotstack filter-order injection."""
    rc, _out, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase06/test_continuity_prefix_schema.py",
            "tests/phase06/test_shotstack_prefix_injection.py",
            "tests/phase06/test_filter_order_preservation.py",
            "-q",
            "--no-cov",
        ]
    )
    return (
        rc == 0,
        "prefix schema + filter order green" if rc == 0 else err[-400:],
    )


def sc5_failures_append_only() -> tuple[bool, str]:
    """SC 5: FAILURES.md append-only Hook + SKILL_HISTORY backup."""
    rc, _out, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase06/test_failures_append_only.py",
            "tests/phase06/test_hook_failures_block.py",
            "tests/phase06/test_skill_history_backup.py",
            "-q",
            "--no-cov",
        ]
    )
    return (
        rc == 0,
        "hook append-only + SKILL_HISTORY green" if rc == 0 else err[-400:],
    )


def sc6_aggregate_dry_run() -> tuple[bool, str]:
    """SC 6: aggregate_patterns.py --dry-run emits valid JSON candidate schema."""
    rc, _out, err = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/phase06/test_aggregate_patterns.py",
            "tests/phase06/test_aggregate_dry_run.py",
            "-q",
            "--no-cov",
        ]
    )
    return (
        rc == 0,
        "aggregate dry-run valid JSON" if rc == 0 else err[-400:],
    )


CHECKS = [
    ("SC1: 5 wiki categories with >=1 ready node", sc1_wiki_ready_nodes),
    ("SC2: NotebookLM 2-notebook registration", sc2_notebooklm_registered),
    ("SC3: Fallback Chain 3-tier", sc3_fallback_chain),
    ("SC4: Continuity Prefix Shotstack injection", sc4_continuity_prefix),
    ("SC5: FAILURES append-only + SKILL_HISTORY", sc5_failures_append_only),
    ("SC6: aggregate_patterns --dry-run", sc6_aggregate_dry_run),
]


def main() -> int:
    print("| SC | Result | Detail |")
    print("|----|--------|--------|")
    all_ok = True
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 — deliberate catch-all for CLI
            ok, detail = False, f"EXCEPTION: {type(e).__name__}: {e}"
        mark = "PASS" if ok else "FAIL"
        all_ok = all_ok and ok
        detail_compact = detail.replace("\n", " ")[:80]
        print(f"| {name} | {mark} | {detail_compact} |")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
