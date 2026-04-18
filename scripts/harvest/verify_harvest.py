"""verify_harvest — 13 task-level checks mapped to 03-VALIDATION.md.

CLI modes:
  --quick  : run all 13 checks (file-exists / grep / python-probe), ~5s
  --full   : quick + recursive deep_diff + sha256 10% spot sample, ~30s
  --check <name> : run a single named check

Each check emits `[OK] <name>` or `[FAIL] <name>: <detail>`.
Final exit: 0 iff all OK, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Callable

# Support invocation both as `python -m scripts.harvest.verify_harvest`
# and as `python scripts/harvest/verify_harvest.py`.
if __package__ in (None, ""):
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

from scripts.harvest import diff_verifier  # noqa: E402


# --------------------------------------------------------------------------
# Path configuration (relative to studios/shorts/ working directory)
# --------------------------------------------------------------------------

STUDIO_ROOT = Path(".")
DEST_ROOT = STUDIO_ROOT / ".preserved" / "harvested"
SOURCE_ROOT = Path("C:/Users/PC/Desktop/shorts_naberal")
MANIFEST_PATH = STUDIO_ROOT / ".planning" / "phases" / "03-harvest" / "path_manifest.json"
DECISIONS_MD = STUDIO_ROOT / ".planning" / "phases" / "03-harvest" / "03-HARVEST_DECISIONS.md"
FAILURES_OUT = STUDIO_ROOT / ".claude" / "failures" / "_imported_from_shorts_naberal.md"
SCOPE_MD = STUDIO_ROOT / ".planning" / "phases" / "02-domain-definition" / "02-HARVEST_SCOPE.md"
AGENT_MD = STUDIO_ROOT / ".claude" / "agents" / "harvest-importer" / "AGENT.md"


# --------------------------------------------------------------------------
# Check registry
# --------------------------------------------------------------------------

CheckFn = Callable[[], tuple[bool, str]]

_CHECKS: dict[str, CheckFn] = {}


def _register(name: str):
    def deco(fn: CheckFn) -> CheckFn:
        _CHECKS[name] = fn
        return fn

    return deco


# --------------------------------------------------------------------------
# Individual checks (13 total — per 03-VALIDATION.md Per-Task map)
# --------------------------------------------------------------------------


@_register("3-01-agent-md-exists")
def check_agent_md() -> tuple[bool, str]:
    if not AGENT_MD.is_file():
        return (False, f"not found: {AGENT_MD}")
    lines = AGENT_MD.read_text(encoding="utf-8").count("\n") + 1
    if lines > 500:
        return (False, f"line count {lines} > 500")
    return (True, f"{lines} lines")


@_register("3-01-agent-md-description-length")
def check_description_length() -> tuple[bool, str]:
    if not AGENT_MD.is_file():
        return (False, f"not found: {AGENT_MD}")
    text = AGENT_MD.read_text(encoding="utf-8")
    m = re.search(r"^description:\s*(.+)$", text, re.M)
    if not m:
        return (False, "description field not found in frontmatter")
    desc = m.group(1).strip()
    if len(desc) > 1024:
        return (False, f"description {len(desc)} > 1024 chars")
    return (True, f"{len(desc)} chars")


@_register("3-01-scripts-harvest-package")
def check_package() -> tuple[bool, str]:
    required = [
        "__init__.py",
        "harvest_importer.py",
        "blacklist_parser.py",
        "conflict_parser.py",
        "decision_builder.py",
        "diff_verifier.py",
        "lockdown.py",
        "verify_harvest.py",
    ]
    base = STUDIO_ROOT / "scripts" / "harvest"
    missing = [f for f in required if not (base / f).is_file()]
    if missing:
        return (False, f"missing: {missing}")
    return (True, f"{len(required)} files present")


@_register("3-02-manifest-valid-json")
def check_manifest_json() -> tuple[bool, str]:
    if not MANIFEST_PATH.is_file():
        return (False, f"manifest not found: {MANIFEST_PATH}")
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (False, f"invalid JSON: {exc}")
    if not isinstance(data, dict) or not data:
        return (False, "manifest is empty or not a dict")
    return (True, f"{len(data)} entries")


@_register("3-03-theme-bible-raw-exists")
def check_theme_bible() -> tuple[bool, str]:
    target = DEST_ROOT / "theme_bible_raw"
    if not target.is_dir():
        return (False, f"dir not found: {target}")
    mds = list(target.glob("*.md"))
    if len(mds) < 7:
        return (False, f"expected >=7 .md files, got {len(mds)}")
    return (True, f"{len(mds)} .md files")


@_register("3-04-remotion-src-raw-exists")
def check_remotion_src() -> tuple[bool, str]:
    target = DEST_ROOT / "remotion_src_raw"
    if not target.is_dir():
        return (False, f"dir not found: {target}")
    node_modules = target / "node_modules"
    if node_modules.exists():
        return (False, "node_modules was copied (ignore pattern failed)")
    return (True, "node_modules excluded")


@_register("3-05-hc-checks-raw-exists")
def check_hc_checks() -> tuple[bool, str]:
    target = DEST_ROOT / "hc_checks_raw" / "hc_checks.py"
    if not target.is_file():
        return (False, f"not found: {target}")
    return (True, f"{target.stat().st_size} bytes")


@_register("3-06-api-wrappers-raw-cherry-pick")
def check_api_wrappers() -> tuple[bool, str]:
    target = DEST_ROOT / "api_wrappers_raw"
    if not target.is_dir():
        return (False, f"dir not found: {target}")
    pys = list(target.glob("*.py"))
    if len(pys) < 5:
        return (False, f"expected >=5 .py files, got {len(pys)}")
    return (True, f"{len(pys)} cherry-picked files")


@_register("3-07-failures-merge-has-source-comment")
def check_failures_merge() -> tuple[bool, str]:
    if not FAILURES_OUT.is_file():
        return (False, f"not found: {FAILURES_OUT}")
    text = FAILURES_OUT.read_text(encoding="utf-8")
    markers = re.findall(r"<!--\s*source:\s*shorts_naberal", text)
    if not markers:
        return (False, "no <!-- source: shorts_naberal ... --> marker found")
    return (True, f"{len(markers)} source markers")


@_register("3-08-decisions-md-39-rows")
def check_decisions() -> tuple[bool, str]:
    if not DECISIONS_MD.is_file():
        return (False, f"not found: {DECISIONS_MD}")
    text = DECISIONS_MD.read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(A|B|C)-\d+\s*\|", text, re.MULTILINE)
    if len(rows) != 39:
        return (False, f"expected 39 data rows, got {len(rows)}")
    return (True, "39 rows (13+16+10)")


@_register("3-08-blacklist-grep-skip-gates")
def check_grep_skip_gates() -> tuple[bool, str]:
    if not DEST_ROOT.is_dir():
        return (False, f"dest root not found: {DEST_ROOT}")
    pattern = re.compile(r"skip_gates\s*=\s*True")
    matches = []
    for path in DEST_ROOT.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pattern.search(text):
            matches.append(str(path))
    if matches:
        return (False, f"{len(matches)} matches: {matches[:3]}")
    return (True, "0 matches")


@_register("3-08-blacklist-grep-todo")
def check_grep_todo() -> tuple[bool, str]:
    if not DEST_ROOT.is_dir():
        return (False, f"dest root not found: {DEST_ROOT}")
    pattern = re.compile(r"TODO\(next-session\)")
    matches = []
    for path in DEST_ROOT.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pattern.search(text):
            matches.append(str(path))
    if matches:
        return (False, f"{len(matches)} matches: {matches[:3]}")
    return (True, "0 matches")


@_register("3-09-lockdown-write-denied")
def check_lockdown() -> tuple[bool, str]:
    if not DEST_ROOT.is_dir():
        return (False, f"dest root not found: {DEST_ROOT}")
    probe = next(DEST_ROOT.rglob("*.md"), None)
    if probe is None:
        return (False, "no *.md probe file under DEST_ROOT")
    original = probe.read_bytes()
    try:
        probe.write_text("LOCKDOWN_VERIFY_TAMPER", encoding="utf-8")
    except PermissionError:
        return (True, f"write denied on {probe.name}")
    # Restore content if write succeeded
    probe.write_bytes(original)
    return (False, f"write SUCCEEDED on {probe} — lockdown not applied")


# --------------------------------------------------------------------------
# Full-mode extras
# --------------------------------------------------------------------------


def _deep_diff_all() -> tuple[bool, str]:
    if not MANIFEST_PATH.is_file():
        return (False, f"manifest not found: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    total = 0
    for name, entry in manifest.items():
        # Skip top-level metadata keys (manifest_version, generated_at,
        # source_root, global_ignore, blacklist_exclusions) which are not
        # raw_dir entries. A raw_dir entry must be a dict containing a
        # 'dest' key and either a 'source' (tree copy) or 'cherry_pick' (file list).
        if not isinstance(entry, dict):
            continue
        if "dest" not in entry:
            continue
        if not entry.get("source"):
            # Cherry-pick entries have source=None; deep_diff only applies
            # to tree copies. Skip cherry-pick entries here.
            continue
        src = SOURCE_ROOT / entry["source"]
        dst = DEST_ROOT / name
        if not src.is_dir() or not dst.is_dir():
            return (False, f"{name}: src={src.is_dir()} dst={dst.is_dir()}")
        mism = diff_verifier.deep_diff(src, dst)
        if mism:
            return (False, f"{name}: {len(mism)} mismatches ({mism[:2]})")
        total += 1
    return (True, f"{total} dirs clean")


def _sha256_spot_sample(rate: float = 0.1) -> tuple[bool, str]:
    if not MANIFEST_PATH.is_file():
        return (False, f"manifest not found: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rng = random.Random(42)
    total_checked = 0
    total_failed = 0
    for name, entry in manifest.items():
        # Skip top-level metadata keys — only raw_dir entries (dict with 'dest')
        # are sampled. Tree copies (source set) AND cherry-picks (cherry_pick
        # set) are both eligible; sha256 samples from dst tree regardless.
        if not isinstance(entry, dict):
            continue
        if "dest" not in entry:
            continue
        # For sha256 check, we need a source directory. Cherry-pick entries
        # have source=None; skip them here (files are scattered across src tree).
        if not entry.get("source"):
            continue
        src = SOURCE_ROOT / entry["source"]
        dst = DEST_ROOT / name
        if not dst.is_dir():
            continue
        files = [p for p in dst.rglob("*") if p.is_file()]
        sample_size = max(1, int(len(files) * rate))
        sample = rng.sample(files, min(sample_size, len(files)))
        for dst_file in sample:
            rel = dst_file.relative_to(dst)
            src_file = src / rel
            if not src_file.is_file():
                total_failed += 1
                continue
            src_hash = hashlib.sha256(src_file.read_bytes()).hexdigest()
            dst_hash = hashlib.sha256(dst_file.read_bytes()).hexdigest()
            if src_hash != dst_hash:
                total_failed += 1
            total_checked += 1
    if total_failed:
        return (False, f"{total_failed}/{total_checked} hash mismatches")
    return (True, f"{total_checked} files hash-matched")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _run_check(name: str) -> bool:
    fn = _CHECKS[name]
    try:
        ok, detail = fn()
    except Exception as exc:
        print(f"[FAIL] {name}: exception {type(exc).__name__}: {exc}")
        return False
    tag = "[OK]" if ok else "[FAIL]"
    print(f"{tag} {name}: {detail}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 harvest verifier — 13 task-level checks."
    )
    parser.add_argument("--quick", action="store_true", help="run 13 basic checks")
    parser.add_argument(
        "--full",
        action="store_true",
        help="quick + deep_diff + sha256 10%% spot sample",
    )
    parser.add_argument("--check", help="run a single named check")
    parser.add_argument("--list", action="store_true", help="list all check names")
    args = parser.parse_args()

    if args.list:
        for name in _CHECKS:
            print(name)
        return 0

    if args.check:
        if args.check not in _CHECKS:
            print(f"[FAIL] unknown check: {args.check}", file=sys.stderr)
            return 2
        return 0 if _run_check(args.check) else 1

    # Default to --quick if neither flag given
    if not args.full and not args.quick:
        args.quick = True

    failed = 0
    for name in _CHECKS:
        if not _run_check(name):
            failed += 1

    if args.full:
        print("\n--- full-mode extras ---")
        ok, detail = _deep_diff_all()
        tag = "[OK]" if ok else "[FAIL]"
        print(f"{tag} 3-full-deep-diff: {detail}")
        if not ok:
            failed += 1
        ok, detail = _sha256_spot_sample()
        tag = "[OK]" if ok else "[FAIL]"
        print(f"{tag} 3-full-sha256-sample: {detail}")
        if not ok:
            failed += 1

    total = len(_CHECKS) + (2 if args.full else 0)
    passed = total - failed
    print(f"\n--- summary: {passed}/{total} passed, {failed} failed ---")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
