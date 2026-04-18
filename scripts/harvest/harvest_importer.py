"""harvest_importer — Phase 3 one-shot orchestrator.

Orchestrates 8 stages:
  1. Load blacklist (blacklist_parser)
  2. Load manifest (json)
  3. Copy 4 raw dirs (shutil.copytree + cherry_pick)
  4. Diff verify each copied dir
  5. Merge FAILURES (append-only with source comments)
  6. Parse CONFLICT_MAP + 5-rule → HARVEST_DECISIONS.md
  7. Blacklist grep audit
  8. IF --lockdown: attrib +R + verify

No `except: pass`. Every exception either re-raises with context OR
appends `[STAGE_N_ERROR]` to audit_log and exits non-zero.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Support invocation both as `python -m scripts.harvest.harvest_importer`
# and as `python scripts/harvest/harvest_importer.py`.
if __package__ in (None, ""):
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

from scripts.harvest import (  # noqa: E402
    blacklist_parser,
    conflict_parser,
    decision_builder,
    diff_verifier,
    lockdown,
)

_SECRET_IGNORE_PATTERNS = (
    "client_secret*.json",
    "token_*.json",
    ".env*",
    "*.key",
    "*.pem",
)

_DEFAULT_IGNORE = (
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".venv",
    ".git",
)


def _audit_append(audit_log: Path, line: str) -> None:
    """Append timestamped line to audit log. Creates parent if missing."""
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with audit_log.open("a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {line}\n")


def _copy_raw_dir(
    name: str,
    manifest_entry: dict,
    source_root: Path,
    dest_root: Path,
) -> dict:
    """Copy one raw dir per manifest entry. Returns audit record."""
    dest = dest_root / name
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=False)

    ignore = shutil.ignore_patterns(*_DEFAULT_IGNORE, *_SECRET_IGNORE_PATTERNS)

    if manifest_entry.get("source"):
        src = source_root / manifest_entry["source"]
        if not src.is_dir():
            raise FileNotFoundError(
                f"source dir not found: {src} (manifest entry '{name}')"
            )
        shutil.copytree(str(src), str(dest), ignore=ignore, symlinks=False)
        file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
        return {"mode": "tree", "name": name, "files_copied": file_count}

    if manifest_entry.get("cherry_pick"):
        dest.mkdir(parents=True, exist_ok=False)
        count = 0
        for rel in manifest_entry["cherry_pick"]:
            src = source_root / rel
            tgt = dest / Path(rel).name
            if not src.is_file():
                raise FileNotFoundError(
                    f"cherry_pick source not found: {src} (name '{name}')"
                )
            shutil.copy2(str(src), str(tgt))
            count += 1
        return {"mode": "cherry_pick", "name": name, "files_copied": count}

    raise ValueError(
        f"manifest entry '{name}' has neither 'source' nor 'cherry_pick'"
    )


_SOURCE_MARKER_RE_TEMPLATE = r"<!-- source: {src} -->"


def _merge_failures(
    source_root: Path,
    failures_out: Path,
) -> dict:
    """Append-only merge of FAILURES files from shorts_naberal.

    Idempotent: checks `<!-- source: ... -->` marker before appending.
    """
    failures_dir = source_root / ".claude" / "failures"
    if not failures_dir.is_dir():
        return {"merged": 0, "skipped": 0, "reason": "failures dir missing"}

    failures_out.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if failures_out.is_file():
        existing = failures_out.read_text(encoding="utf-8")
    else:
        header = (
            "# FAILURES — Imported from shorts_naberal "
            f"({datetime.now(timezone.utc).date()} Phase 3 Harvest)\n\n"
            "> Read-only archive. Originals live in shorts_naberal/ (DO NOT modify).\n"
            "> D-2 저수지 연동: 첫 1~2개월 SKILL patch 금지 기간 동안 이 파일은 참조 전용.\n\n"
        )
        failures_out.write_text(header, encoding="utf-8")
        existing = header

    merged = 0
    skipped = 0
    for md in sorted(failures_dir.glob("*.md")):
        if md.name.lower() == "readme.md":
            continue
        rel_source = f"shorts_naberal/.claude/failures/{md.name}"
        marker = _SOURCE_MARKER_RE_TEMPLATE.format(src=re.escape(rel_source))
        if re.search(marker, existing):
            skipped += 1
            continue
        body = md.read_text(encoding="utf-8")
        block = (
            f"\n<!-- source: {rel_source} -->\n"
            f"<!-- imported: {datetime.now(timezone.utc).date()} "
            f"by harvest_importer.py v1.0 -->\n\n"
            f"{body}\n"
            f"<!-- END source: {rel_source} -->\n"
        )
        with failures_out.open("a", encoding="utf-8") as fh:
            fh.write(block)
        merged += 1

    return {"merged": merged, "skipped": skipped}


_BLACKLIST_GREP_PATTERNS = (
    re.compile(r"skip_gates\s*=\s*True"),
    re.compile(r"TODO\(next-session\)"),
)


def _blacklist_grep_audit(dest_root: Path) -> list[str]:
    """Scan harvested dirs for forbidden patterns. Returns match descriptions."""
    matches: list[str] = []
    if not dest_root.is_dir():
        return matches
    for path in dest_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as exc:
            matches.append(f"READ_ERROR: {path} ({exc})")
            continue
        for pattern in _BLACKLIST_GREP_PATTERNS:
            for m in pattern.finditer(text):
                matches.append(f"{pattern.pattern}: {path}:offset={m.start()}")
    return matches


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 3 harvest-importer — one-shot executor.",
    )
    parser.add_argument(
        "--source",
        default="C:/Users/PC/Desktop/shorts_naberal",
        help="shorts_naberal root (absolute path)",
    )
    parser.add_argument(
        "--scope",
        default=".planning/phases/02-domain-definition/02-HARVEST_SCOPE.md",
    )
    parser.add_argument(
        "--conflict-map",
        default=None,
        help="defaults to <source>/.planning/codebase/CONFLICT_MAP.md",
    )
    parser.add_argument(
        "--manifest",
        default=".planning/phases/03-harvest/path_manifest.json",
    )
    parser.add_argument("--dest", default=".preserved/harvested")
    parser.add_argument(
        "--failures-out",
        default=".claude/failures/_imported_from_shorts_naberal.md",
    )
    parser.add_argument(
        "--decisions-out",
        default=".planning/phases/03-harvest/03-HARVEST_DECISIONS.md",
    )
    parser.add_argument(
        "--audit-log",
        default="scripts/harvest/audit_log.md",
    )
    parser.add_argument("--lockdown", action="store_true")
    parser.add_argument(
        "--stage",
        type=int,
        default=0,
        help="run a specific stage only (1..8). 0 = run all.",
    )
    parser.add_argument("--name", default=None, help="stage 3 single dir name")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    source_root = Path(args.source)
    scope_md = Path(args.scope)
    conflict_map_path = (
        Path(args.conflict_map)
        if args.conflict_map
        else source_root / ".planning" / "codebase" / "CONFLICT_MAP.md"
    )
    manifest_path = Path(args.manifest)
    dest_root = Path(args.dest)
    failures_out = Path(args.failures_out)
    decisions_out = Path(args.decisions_out)
    audit_log = Path(args.audit_log)

    def stage_enabled(n: int) -> bool:
        return args.stage == 0 or args.stage == n

    # --- Stage 1: load blacklist ---
    blacklist: list[dict] = []
    if stage_enabled(1):
        try:
            blacklist = blacklist_parser.parse_blacklist(scope_md)
            _audit_append(audit_log, f"[STAGE_1_OK] blacklist entries={len(blacklist)}")
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_1_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_1_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 2: load manifest ---
    manifest: dict = {}
    if stage_enabled(2):
        try:
            if not manifest_path.is_file():
                raise FileNotFoundError(f"manifest not found: {manifest_path}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            _audit_append(audit_log, f"[STAGE_2_OK] manifest entries={len(manifest)}")
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_2_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_2_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 3: copy raw dirs ---
    if stage_enabled(3):
        try:
            names = [args.name] if args.name else list(manifest.keys())
            for name in names:
                entry = manifest.get(name)
                if not entry:
                    raise KeyError(f"manifest missing entry '{name}'")
                record = _copy_raw_dir(name, entry, source_root, dest_root)
                _audit_append(
                    audit_log,
                    f"[STAGE_3_OK] {record['name']} mode={record['mode']} "
                    f"files={record['files_copied']}",
                )
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_3_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_3_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 4: diff verify ---
    if stage_enabled(4):
        try:
            names = [args.name] if args.name else list(manifest.keys())
            all_mismatches: list[str] = []
            for name in names:
                entry = manifest.get(name, {})
                if not entry.get("source"):
                    continue  # cherry_pick mode skips deep_diff
                src = source_root / entry["source"]
                dst = dest_root / name
                mism = diff_verifier.deep_diff(src, dst)
                if mism:
                    all_mismatches.extend(f"{name}: {m}" for m in mism)
            if all_mismatches:
                for m in all_mismatches:
                    _audit_append(audit_log, f"[STAGE_4_MISMATCH] {m}")
                _audit_append(
                    audit_log,
                    f"[STAGE_4_ERROR] {len(all_mismatches)} mismatches",
                )
                print(f"[STAGE_4_ERROR] {len(all_mismatches)} mismatches", file=sys.stderr)
                return 1
            _audit_append(audit_log, "[STAGE_4_OK] all dirs match source")
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_4_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_4_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 5: merge FAILURES ---
    if stage_enabled(5):
        try:
            result = _merge_failures(source_root, failures_out)
            _audit_append(
                audit_log,
                f"[STAGE_5_OK] merged={result['merged']} skipped={result['skipped']}",
            )
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_5_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_5_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 6: parse CONFLICT_MAP + 5-rule ---
    if stage_enabled(6):
        try:
            entries = conflict_parser.parse_conflict_map(conflict_map_path)
            decision_builder.build_decisions_md(
                entries, blacklist, scope_md, conflict_map_path, decisions_out
            )
            _audit_append(
                audit_log,
                f"[STAGE_6_OK] decisions.md rows={len(entries)} out={decisions_out}",
            )
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_6_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_6_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 7: blacklist grep audit ---
    if stage_enabled(7):
        try:
            matches = _blacklist_grep_audit(dest_root)
            if matches:
                for m in matches:
                    _audit_append(audit_log, f"[STAGE_7_MATCH] {m}")
                _audit_append(audit_log, f"[STAGE_7_ERROR] {len(matches)} matches")
                print(f"[STAGE_7_ERROR] {len(matches)} forbidden patterns", file=sys.stderr)
                return 1
            _audit_append(audit_log, "[STAGE_7_OK] no forbidden patterns")
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_7_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_7_ERROR] {exc}", file=sys.stderr)
            return 1

    # --- Stage 8: lockdown ---
    if stage_enabled(8) and args.lockdown:
        try:
            lockdown.apply_lockdown(dest_root)
            lockdown.verify_lockdown(dest_root)
            _audit_append(audit_log, f"[STAGE_8_OK] lockdown applied + verified on {dest_root}")
        except Exception as exc:
            _audit_append(audit_log, f"[STAGE_8_ERROR] {type(exc).__name__}: {exc}")
            print(f"[STAGE_8_ERROR] {exc}", file=sys.stderr)
            return 1
    elif stage_enabled(8):
        _audit_append(audit_log, "[STAGE_8_SKIP] --lockdown not set")

    _audit_append(audit_log, "[HARVEST_COMPLETE] all requested stages OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
