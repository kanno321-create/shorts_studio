"""A-grade drift scanner wrapping harness drift_scan.py — AUDIT-03/04 / SC#4.

A급 drift 발견 시 `.planning/STATE.md` 의 frontmatter 에 phase_lock: true 세팅 +
gh issue 자동 생성. harness drift_scan.py 4 public 함수를 sys.path import 로 재사용
(복사 금지 — harness 업데이트 시 auto-sync).

Graceful degradation (Plan 02 WARNING #4):
  - harness_path 부재 → stderr WARN + local-only scan (deprecated_patterns.json 만)
  - --skip-harness-import → harness 로드 자체 skip, local scan 전용
  - GH Actions drift-scan-weekly.yml 에서 `--harness-path=../harness/scripts` 전달
  - CLAUDE.md "독립 git 저장소. 하네스 업데이트는 수동 pull" → submodule 아님

Exclude filter (Rule 3 deviation — filter real code drift, not docs/tests):
  --exclude PREFIX (repeatable) — relative path prefix to skip from findings.
  Default excludes preserve documentation / test fixtures / hook-validation
  meta-code that legitimately contains the forbidden patterns as string literals.

CLI:
    python -m scripts.audit.drift_scan [--studio-root <path>]
                                       [--harness-path <path>]
                                       [--skip-harness-import]
                                       [--dry-run]
                                       [--clear-lock]
                                       [--skip-github-issue]
                                       [--exclude PREFIX]...
                                       [--no-default-excludes]

Exit codes:
    0 — no A-grade drift (safe to proceed)
    1 — A-grade drift found (phase locked, issue auto-created)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# UTF-8 safeguard for Windows cp949 per Phase 6/9 precedent
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover - defensive
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover - defensive
        pass

KST = ZoneInfo("Asia/Seoul")

# scripts/audit/drift_scan.py -> parents[2] = studios/shorts/
STUDIO_ROOT = Path(__file__).resolve().parents[2]
# studios/shorts/ -> parents[2] = naberal_group/ -> harness/scripts/
DEFAULT_HARNESS_SCRIPTS = STUDIO_ROOT.parent.parent / "harness" / "scripts"

PHASE_LOCK_FIELDS = ("phase_lock", "block_reason", "block_since")

# Module-level flag set inside _resolve_harness_imports to surface 'mode' in summary.
_HARNESS_LOADED = False

# Default exclude prefixes (Rule 3 deviation — discriminate real code drift
# from legitimate string-literal references in docs/tests/hook-validators).
# Every prefix is matched against the POSIX-relative path of each finding.
DEFAULT_EXCLUDE_PREFIXES: tuple[str, ...] = (
    ".planning/",                          # plan docs / research / validation
    "docs/",                               # architecture / session log / handoff
    "tests/",                              # test fixtures reference forbidden patterns
    "wiki/",                               # navigator / kpi / taste-gate docs
    ".claude/deprecated_patterns.json",    # pattern source itself
    ".claude/failures/",                   # FAILURES.md records prior violations
    ".claude/memory/",                     # memory files record canonical forbidden list
    ".claude/agents/",                     # AGENT.md mentions forbidden patterns in rules
    ".claude/skills/",                     # SKILL.md documents the rules
    ".claude/hooks/pre_tool_use.py",       # the blocker itself
    "CLAUDE.md",                           # root constitution lists forbidden items
    "FAILURES.md",                         # FAILURES at repo root
    "WORK_HANDOFF.md",                     # handoff memos reference prior issues
    ".git/",                               # git internals
    ".pytest_cache/",                      # pytest runtime cache
    "outputs/",                            # runtime output (gitignored)
    ".preserved/",                         # harvested shorts_naberal originals (read-only per CLAUDE.md)
    "scripts/harvest/audit_log.md",        # harvest audit report (legitimate doc)
    "scripts/validate/verify_hook_blocks.py",  # meta-test for the hook
    "scripts/validate/harness_audit.py",   # audit meta-script references
    "scripts/validate/phase05_acceptance.py",  # SC5 validator searches for T2V
    "scripts/audit/drift_scan.py",         # self-reference
    "scripts/audit/skill_patch_counter.py", # Plan 10-01 companion scanner
    # Defensive meta-code documenting T2V-absence (D-13 / VIDEO-01). These files
    # define only image_to_video and/or assert that text_to_video is not present —
    # exclusion here means "T2V ban is enforced by these files", not "T2V code exists".
    "scripts/orchestrator/api/kling_i2v.py",
    "scripts/orchestrator/api/runway_i2v.py",
    "scripts/orchestrator/api/veo_i2v.py",
    "scripts/orchestrator/api/models.py",
    "scripts/orchestrator/gates.py",
    "scripts/notebooklm/fallback.py",      # hardcoded answer contains "T2V 금지" literal
)


# ---------------------------------------------------------------------------
# Harness import resolution (lazy + graceful fallback)
# ---------------------------------------------------------------------------


def _resolve_harness_imports(harness_path: Path | None, skip: bool) -> dict | None:
    """Resolve harness drift_scan 4 public functions.

    Returns dict of functions or None if skip=True / path missing / import failed
    → local-only fallback.

    WARNING #4: harness/ 는 shorts_studio 의 submodule 이 아님. GH Actions 은 별도
    checkout step 으로 마련하며, 로컬 실행에서는 ../../harness/scripts 가 default.
    """
    global _HARNESS_LOADED
    _HARNESS_LOADED = False

    if skip:
        print(
            "[INFO] --skip-harness-import: local-only drift scan "
            "(deprecated_patterns.json only)",
            file=sys.stderr,
        )
        return None

    resolved = harness_path if harness_path is not None else DEFAULT_HARNESS_SCRIPTS
    resolved = Path(resolved)

    if not resolved.exists():
        print(
            f"[WARN] harness/ not found at {resolved} — falling back to local-only "
            f"drift scan (deprecated_patterns.json only). "
            f"Pass --harness-path or --skip-harness-import to silence.",
            file=sys.stderr,
        )
        return None

    if str(resolved) not in sys.path:
        sys.path.insert(0, str(resolved))

    try:
        from drift_scan import (  # type: ignore[import-untyped]
            load_patterns,
            scan_studio,
            write_conflict_map,
            append_history,
        )
    except ImportError as exc:
        print(
            f"[WARN] harness drift_scan import failed: {exc} — local-only fallback",
            file=sys.stderr,
        )
        return None

    _HARNESS_LOADED = True
    return {
        "load_patterns": load_patterns,
        "scan_studio": scan_studio,
        "write_conflict_map": write_conflict_map,
        "append_history": append_history,
    }


# ---------------------------------------------------------------------------
# Local-only fallback (harness absent) — minimal regex scan
# ---------------------------------------------------------------------------


_LOCAL_EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules",
                       ".archive", "_legacy", ".pytest_cache", "outputs"}
_LOCAL_EXCLUDE_SUFFIXES = {".pyc", ".jsonl", ".log", ".png", ".jpg", ".jpeg",
                           ".mp4", ".mp3", ".wav", ".svg", ".gif", ".ico",
                           ".webp", ".bin", ".lock"}
_LOCAL_SCAN_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".ps1", ".sh",
                        ".txt", ".toml"}


def _local_load_patterns(studio_root: Path) -> list[dict]:
    """Fallback — load .claude/deprecated_patterns.json directly (harness absent)."""
    p = studio_root / ".claude" / "deprecated_patterns.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARN] Failed to read deprecated_patterns.json: {exc}", file=sys.stderr)
        return []
    return data.get("patterns", [])


def _local_scan_studio(studio_root: Path, pattern_defs: list[dict]) -> dict:
    """Fallback — minimal regex scan across studio files. harness 미포함 시 사용.

    Only scans files with _LOCAL_SCAN_SUFFIXES and skips _LOCAL_EXCLUDE_DIRS / SUFFIXES.
    """
    findings: dict[str, list[dict]] = {}
    if not pattern_defs:
        return findings

    compiled: list[tuple[str, re.Pattern[str]]] = []
    for pat in pattern_defs:
        name = pat.get("name") or pat.get("reason") or "unnamed"
        regex = pat.get("regex", "")
        try:
            compiled.append((name, re.compile(regex)))
        except re.error as exc:
            print(f"[WARN] Bad regex {regex!r}: {exc}", file=sys.stderr)

    for path in studio_root.rglob("*"):
        if not path.is_file():
            continue
        if any(seg in _LOCAL_EXCLUDE_DIRS for seg in path.parts):
            continue
        if path.suffix in _LOCAL_EXCLUDE_SUFFIXES:
            continue
        if path.suffix and path.suffix not in _LOCAL_SCAN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(studio_root)
        rel_str = str(rel).replace("\\", "/")
        for i, line in enumerate(text.splitlines(), 1):
            for name, rx in compiled:
                if rx.search(line):
                    findings.setdefault(name, []).append({
                        "file": rel_str, "line": i, "match": line.rstrip()[:200],
                    })
    return findings


# ---------------------------------------------------------------------------
# STATE.md frontmatter helpers (stdlib only, no pyyaml)
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> tuple[str, str, str]:
    """Return (before_fm, fm_body, after_fm_incl_closing_delim).

    The returned tuple concatenated reproduces the original text byte-for-byte.
    """
    m = re.match(r"(^---\n)(.*?)(\n---\n)", text, re.DOTALL)
    if not m:
        raise ValueError("STATE.md has no YAML frontmatter")
    before = m.group(1)
    body = m.group(2)
    tail = m.group(3) + text[m.end():]
    return before, body, tail


def _set_key(fm_body: str, key: str, value: str) -> str:
    """Set or replace a single top-level YAML key in frontmatter body.

    - If the key exists at top level → replace its value (preserve order).
    - If missing → insert before `progress:` if present, else append at end.
    """
    lines = fm_body.split("\n")
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}: {value}"
            return "\n".join(lines)
    # Missing — insert before "progress:" if found
    for i, line in enumerate(lines):
        if line.startswith("progress:"):
            lines.insert(i, f"{key}: {value}")
            return "\n".join(lines)
    # Otherwise append
    lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _remove_key(fm_body: str, key: str) -> str:
    """Remove a top-level YAML key line from frontmatter body (idempotent)."""
    lines = fm_body.split("\n")
    pattern = re.compile(rf"^{re.escape(key)}\s*:")
    return "\n".join(l for l in lines if not pattern.match(l))


def set_phase_lock(studio_root: Path, reason: str, now: datetime) -> None:
    """Set phase_lock: true + block_reason + block_since in STATE.md frontmatter.

    Idempotent — replaces existing keys without duplication.
    """
    state_md = studio_root / ".planning" / "STATE.md"
    text = state_md.read_text(encoding="utf-8")
    before, fm, after = _parse_frontmatter(text)
    fm = _set_key(fm, "phase_lock", "true")
    fm = _set_key(fm, "block_reason", json.dumps(reason, ensure_ascii=False))
    fm = _set_key(fm, "block_since", f'"{now.isoformat()}"')
    state_md.write_text(before + fm + after, encoding="utf-8")


def clear_phase_lock(studio_root: Path) -> None:
    """Reset phase_lock: false + strip block_reason/block_since from STATE.md."""
    state_md = studio_root / ".planning" / "STATE.md"
    text = state_md.read_text(encoding="utf-8")
    before, fm, after = _parse_frontmatter(text)
    fm = _set_key(fm, "phase_lock", "false")
    fm = _remove_key(fm, "block_reason")
    fm = _remove_key(fm, "block_since")
    state_md.write_text(before + fm + after, encoding="utf-8")


# ---------------------------------------------------------------------------
# GitHub issue auto-create
# ---------------------------------------------------------------------------


def _filter_findings_by_prefix(
    findings: dict[str, list[dict]],
    exclude_prefixes: tuple[str, ...],
) -> dict[str, list[dict]]:
    """Return a new findings dict with hits whose `file` starts with any
    `exclude_prefixes` entry removed. Pattern keys with zero remaining hits
    are dropped entirely.
    """
    if not exclude_prefixes:
        return findings
    filtered: dict[str, list[dict]] = {}
    for name, hits in findings.items():
        kept = [
            h for h in hits
            if not any(str(h.get("file", "")).replace("\\", "/").startswith(pfx)
                       for pfx in exclude_prefixes)
        ]
        if kept:
            filtered[name] = kept
    return filtered


def create_github_issue(a_grade_details: dict[str, int], reason: str, now: datetime) -> None:
    """Auto-create a GitHub issue for A-grade drift findings.

    Invokes `gh issue create --title ... --body-file - --label drift,critical,phase-10,auto`
    via subprocess (non-interactive). Caller must have gh auth configured.

    Labels MUST exist in repo beforehand — see Plan 02 BLOCKER #2 (Wave 0 manual
    dispatch #1 + Plan 4 `drift-scan-weekly.yml` step `Ensure labels exist` #2).
    """
    count = sum(a_grade_details.values())
    title = f"[AUDIT-04] A급 drift {count}건 — Phase 차단"
    body_lines = [
        "# A급 drift 감지",
        "",
        "- Detector: `scripts/audit/drift_scan.py`",
        f"- Timestamp: {now.isoformat()}",
        f"- Reason: {reason}",
        "",
        "## A급 findings (pattern → count)",
    ]
    for name, cnt in sorted(a_grade_details.items()):
        body_lines.append(f"- `{name}`: {cnt}건")
    body_lines.extend([
        "",
        "## Phase lock 상태",
        "- `.planning/STATE.md` frontmatter 에 `phase_lock: true` 세팅됨",
        f"- `block_reason`: {reason}",
        "",
        "## 복구 경로",
        "1. A급 drift 코드 수정",
        "2. `python -m scripts.audit.drift_scan` 재실행 → A급 0 확인",
        "3. `python -m scripts.audit.drift_scan --clear-lock` 로 STATE.md phase_lock=false 복귀",
        "4. 본 issue close",
    ])
    body = "\n".join(body_lines)
    subprocess.run(
        [
            "gh", "issue", "create",
            "--title", title,
            "--body-file", "-",
            "--label", "drift,critical,phase-10,auto",
        ],
        input=body,
        text=True,
        check=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="A-grade drift scanner — AUDIT-03/04 (Phase 10 Plan 02)",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="STATE.md 건드리지 않고 stdout JSON 만 출력")
    parser.add_argument("--clear-lock", action="store_true",
                        help="Reset phase_lock to false (after drift resolved)")
    parser.add_argument("--studio-root", default=str(STUDIO_ROOT), type=Path,
                        help="Studio root (default: auto-detected from this script)")
    parser.add_argument("--skip-github-issue", action="store_true",
                        help="Skip gh issue auto-create (local dry-run / offline)")
    parser.add_argument("--harness-path", type=Path, default=None,
                        help="Override harness/scripts path (default: ../../harness/scripts). "
                             "WARNING #4: harness/ 부재 시 local-only fallback.")
    parser.add_argument("--skip-harness-import", action="store_true",
                        help="Skip harness import entirely — local-only scan "
                             "(deprecated_patterns.json 만).")
    parser.add_argument("--exclude", action="append", default=None, metavar="PREFIX",
                        help="Repeatable — additional POSIX relative-path prefix "
                             "to exclude from findings (combined with defaults).")
    parser.add_argument("--no-default-excludes", action="store_true",
                        help="Disable the built-in DEFAULT_EXCLUDE_PREFIXES (docs/tests/"
                             "hook-validators). Use only for full-repo audits.")
    args = parser.parse_args(argv)

    studio_root = Path(args.studio_root).resolve()
    now = datetime.now(KST)

    if args.clear_lock:
        clear_phase_lock(studio_root)
        print(json.dumps({
            "phase_lock": False,
            "cleared_at": now.isoformat(),
        }, ensure_ascii=False, indent=2))
        return 0

    # Graceful harness import (WARNING #4)
    harness_funcs = _resolve_harness_imports(args.harness_path, args.skip_harness_import)

    if harness_funcs is not None:
        # Plan 02 DEVIATION (Rule 3): harness load_patterns() reads
        # `.claude/drift_patterns.json` but studio uses `.claude/deprecated_patterns.json`.
        # Harness API mismatch — we use local loader for patterns but delegate
        # scan/write/append to harness. This preserves "no-copy" principle (harness
        # scan_studio logic re-used) while honoring studio file naming convention.
        harness_patterns = harness_funcs["load_patterns"](studio_root)
        pattern_defs = harness_patterns if harness_patterns else _local_load_patterns(studio_root)
        findings = harness_funcs["scan_studio"](studio_root, pattern_defs)
    else:
        pattern_defs = _local_load_patterns(studio_root)
        findings = _local_scan_studio(studio_root, pattern_defs)

    # Rule 3 deviation — filter legitimate doc/test/hook string-literal references
    # so phase_lock only triggers on actual code drift.
    exclude_prefixes: tuple[str, ...] = ()
    if not args.no_default_excludes:
        exclude_prefixes = DEFAULT_EXCLUDE_PREFIXES
    if args.exclude:
        exclude_prefixes = exclude_prefixes + tuple(args.exclude)
    findings = _filter_findings_by_prefix(findings, exclude_prefixes)

    output_map = studio_root / ".planning" / "codebase" / "CONFLICT_MAP.md"
    output_map.parent.mkdir(parents=True, exist_ok=True)

    if not args.dry_run and harness_funcs is not None:
        harness_funcs["write_conflict_map"](studio_root, findings, pattern_defs, output_map)
        harness_funcs["append_history"](studio_root, findings)

    # Compute A-grade detail counts — grade defaults to "C" when field missing.
    a_grade_details: dict[str, int] = {}
    for p in pattern_defs:
        if (p.get("grade") or "C").upper() != "A":
            continue
        pname = p.get("name") or p.get("reason") or "unnamed"
        hits = findings.get(pname, [])
        if hits:
            a_grade_details[pname] = len(hits)
    a_grade_count = sum(a_grade_details.values())

    summary = {
        "a_grade_count": a_grade_count,
        "a_grade_details": a_grade_details,
        "total_patterns_checked": len(pattern_defs),
        "scan_time": now.isoformat(),
        "dry_run": args.dry_run,
        "harness_loaded": _HARNESS_LOADED,
        "mode": "harness" if _HARNESS_LOADED else "local-only",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if a_grade_count > 0 and not args.dry_run:
        reason = f"A급 drift {a_grade_count}건 — {now.date().isoformat()} drift_scan"
        set_phase_lock(studio_root, reason, now)
        if not args.skip_github_issue:
            try:
                create_github_issue(a_grade_details, reason, now)
            except subprocess.CalledProcessError as exc:
                # Plan 4 drift-scan-weekly.yml 의 `Ensure labels exist` step 이
                # label 422 를 1차 방어하고, Wave 0 manual dispatch 가 2차 방어.
                # 그래도 실패하면 GH Actions 가 실패 email 을 발송하므로 여기서
                # 명시적으로 raise (Project Rule 3 — try-except 침묵 폴백 금지).
                print(
                    f"[WARN] gh issue create failed rc={exc.returncode}: "
                    f"{getattr(exc, 'stderr', '')}",
                    file=sys.stderr,
                )
                raise
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
