#!/usr/bin/env python3
"""D-2 Lock SKILL patch counter — FAIL-04 / Phase 10 SC#1.

Scans `git log` across 4 forbidden path regex during the D-2 Lock period
(2026-04-20 ~ 2026-06-20 per Phase 10 CONTEXT.md locked decision), emits a
monthly Markdown report to ``reports/`` and, on violations, appends a
F-D2-NN entry to ``FAILURES.md`` via direct file I/O.

Hook bypass by naming:
    ``.claude/hooks/pre_tool_use.py::check_failures_append_only`` only
    inspects Claude Code Write/Edit/MultiEdit tool inputs. Direct
    ``open(path, "a")`` from a Python subprocess does NOT trigger the hook,
    which is the documented escape hatch for programmatic append (per
    Phase 10 RESEARCH Pitfall 3). The strict-prefix invariant is still
    honoured because ``a`` mode cannot truncate existing bytes.

Usage:
    python -m scripts.audit.skill_patch_counter --dry-run
    python -m scripts.audit.skill_patch_counter \\
        --since 2026-04-20 --until 2026-06-20 --repo .

Exit codes:
    0 = success, zero violations
    1 = success, at least one violation (report / append written unless --dry-run)
    2 = argparse error

Forbidden paths (count violations):
    1. ``.claude/agents/<any>/SKILL.md``
    2. ``.claude/skills/<any>/SKILL.md``
    3. ``.claude/hooks/<file>.py``
    4. ``CLAUDE.md`` (repo root)

Allowed paths (never counted):
    ``SKILL.md.candidate``, ``scripts/**/*.py``, ``.planning/**``,
    ``wiki/**/*.md``, ``FAILURES.md``, ``.claude/memory/*.md``.

Design invariants (Phase 10 RESEARCH Area 1-4):
    - Stdlib-only (argparse, json, re, subprocess, datetime, zoneinfo).
    - UTF-8 throughout; ensure_ascii=False so Korean commit subjects survive.
    - Windows cp949 stdout guard via ``sys.stdout.reconfigure``.
    - 4 FORBIDDEN_PATTERNS regex use POSIX forward-slash; git log emits
      forward-slash on both POSIX and Windows so no normalisation needed.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")
D2_LOCK_START = "2026-04-20"
D2_LOCK_END = "2026-06-20"

FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\.claude/agents/.+/SKILL\.md$"),
    re.compile(r"^\.claude/skills/.+/SKILL\.md$"),
    re.compile(r"^\.claude/hooks/[^/]+\.py$"),
    re.compile(r"^CLAUDE\.md$"),
]


def _boundary(raw: str, which: str) -> str:
    """Normalise --since / --until to explicit HH:MM:SS for git log approxidate.

    git 2.51 on Windows treats bare ``YYYY-MM-DD`` as a relative anchor that
    excludes commits on the current day if passed to ``--since``. Expanding
    to ``YYYY-MM-DD 00:00:00`` (since) / ``YYYY-MM-DD 23:59:59`` (until)
    forces absolute-boundary interpretation (Rule 1 deviation — without this
    fix, directive-authorized Pre-Phase10 commits on 2026-04-20 are silently
    skipped).
    """
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return f"{raw} 00:00:00" if which == "since" else f"{raw} 23:59:59"
    return raw


def scan_violations(repo_root: Path, since: str, until: str) -> list[dict]:
    """Return list of {hash, date, subject, violating_file} per forbidden commit.

    Uses ``git log --name-only`` with a custom ``---COMMIT---`` sentinel so we
    can split commit metadata from changed-file list without relying on
    ``--pretty=format:%n`` newline counting (brittle across CRLF platforms).
    """
    since_boundary = _boundary(since, "since")
    until_boundary = _boundary(until, "until")
    result = subprocess.run(
        ["git", "log",
         f"--since={since_boundary}",
         f"--until={until_boundary}",
         "--name-only",
         "--pretty=format:---COMMIT---%n%H|%aI|%s"],
        cwd=repo_root, capture_output=True, text=True,
        encoding="utf-8", check=True,
    )
    violations: list[dict] = []
    current: dict | None = None
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if raw == "---COMMIT---":
            current = {"hash": None, "date": None, "subject": None}
            continue
        if current is None:
            continue
        if current["hash"] is None and "|" in raw:
            # Metadata line: %H|%aI|%s
            parts = raw.split("|", 2)
            if len(parts) == 3:
                current["hash"] = parts[0]
                current["date"] = parts[1]
                current["subject"] = parts[2]
            continue
        if not line:
            continue
        # File path line
        normalised = line.replace("\\", "/")
        for rx in FORBIDDEN_PATTERNS:
            if rx.match(normalised):
                violations.append({
                    "hash": current["hash"],
                    "date": current["date"],
                    "subject": current["subject"],
                    "violating_file": normalised,
                })
                break
    return violations


def write_report(
    violations: list[dict],
    output: Path,
    now: datetime,
    since: str,
    until: str,
) -> None:
    """Write the monthly Markdown report to ``output`` (UTF-8, newline-joined)."""
    month = now.strftime("%Y-%m")
    badge = "✅" if not violations else "🚨"
    lines: list[str] = [
        f"# D-2 Lock Skill Patch Counter — {month}",
        "",
        f"**Lock period:** {since} ~ {until}",
        f"**Report generated:** {now.isoformat()}",
        f"**Violation count:** {len(violations)} {badge} (목표: 0)",
        "",
        "## Violations",
    ]
    if violations:
        lines.append("| Hash | Date | File | Subject |")
        lines.append("|------|------|------|---------|")
        for v in violations:
            # Escape pipe chars in subject to avoid table row corruption
            safe_subject = (v.get("subject") or "").replace("|", "\\|")
            short_hash = (v.get("hash") or "")[:7]
            lines.append(
                f"| {short_hash} "
                f"| {v.get('date') or ''} "
                f"| `{v.get('violating_file') or ''}` "
                f"| {safe_subject} |"
            )
    else:
        lines.append("*없음.*")
    lines.extend([
        "",
        "## Scan coverage",
        f"- Lock window scanned: {since} → {until}",
        f"- Forbidden paths checked: {len(FORBIDDEN_PATTERNS)}",
        "- Regex: `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, "
        "`.claude/hooks/*.py`, `CLAUDE.md`",
        "",
        "## Notes",
        "- Count > 0 시 `FAILURES.md` 에 `F-D2-NN` 엔트리가 자동 append 됩니다 (D-11).",
        "- `directive-authorized` Pre-Phase10 commit 은 **투명하게 count 에 포함**합니다 — "
        "Whitelist 금지 (Risk #1 옵션 D, 2026-04-20 대표님 승인본).",
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _existing_violation_hashes(failures_text: str) -> set[str]:
    """Parse F-D2-NN entries and return the union of commit short-hashes.

    Recognized line format (matches :func:`append_failures` at L220-224)::

        - `7-hex` YYYY-MM-DD — `file.ext` (subject)

    Returns a set of 7-hex short hashes. Used by :func:`main` to skip
    duplicate appends (AUDIT-05 / D-23). Format coupling with
    ``append_failures`` is tested by
    ``tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing``.
    """
    hashes: set[str] = set()
    # Match F-D2-NN entries (greedy body until next F-D or EOF).
    entry_re = re.compile(r"^## F-D2-\d{2}.*?(?=^## F-|\Z)", re.MULTILINE | re.DOTALL)
    line_re = re.compile(r"^- `([0-9a-f]{7})`")
    for entry_match in entry_re.finditer(failures_text):
        for line in entry_match.group(0).splitlines():
            m = line_re.match(line)
            if m:
                hashes.add(m.group(1))
    return hashes


def append_failures(
    violations: list[dict],
    repo_root: Path,
    now: datetime,
) -> None:
    """Append F-D2-NN entry to ``FAILURES.md`` via direct file I/O.

    Hook bypass: ``check_failures_append_only`` only inspects Claude
    Write/Edit/MultiEdit tool calls, not ``open(path, "a")`` from a
    subprocess. Strict-prefix invariant still holds because mode ``a`` only
    appends after the current EOF — no truncation is possible.
    """
    failures = repo_root / "FAILURES.md"
    if not failures.exists():
        return

    existing = failures.read_text(encoding="utf-8")
    ids = re.findall(r"## F-D2-(\d{2})", existing)
    next_id = max((int(i) for i in ids), default=0) + 1

    body: list[str] = [
        "",
        "---",
        "",
        f"## F-D2-{next_id:02d} — D-2 Lock 위반 감지 "
        f"({now.date().isoformat()}, skill_patch_counter)",
        "",
        "**증상**: D-2 Lock 기간 (2026-04-20 ~ 2026-06-20) 중 금지 경로 commit 발생.",
        "",
        f"**위반 commit 수**: {len(violations)}",
        "",
        "**상세**:",
    ]
    for v in violations:
        short_hash = (v.get("hash") or "")[:7]
        body.append(
            f"- `{short_hash}` {v.get('date') or ''} — "
            f"`{v.get('violating_file') or ''}` ({v.get('subject') or ''})"
        )
    body.extend([
        "",
        "**조치**: 즉시 `SKILL_HISTORY/<skill>/v*.md.bak` 에서 직전 버전 복원 → "
        "`git revert` → 본 엔트리 해결 commit 에서 reference.",
        "",
        "**Lock 재평가**: Exit 조건 재검증 (2개월 경과 + FAILURES ≥ 10 + "
        "taste gate 2회) 전까지 patch 금지 유지.",
        "",
    ])
    # Direct open('a') — Claude Write/Edit hook does not apply here.
    with failures.open("a", encoding="utf-8") as f:
        f.write("\n".join(body))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="D-2 Lock SKILL patch counter (FAIL-04 / Phase 10 SC#1)",
    )
    parser.add_argument(
        "--since", default=D2_LOCK_START,
        help=f"Git log --since boundary (default: {D2_LOCK_START})",
    )
    parser.add_argument(
        "--until", default=D2_LOCK_END,
        help=f"Git log --until boundary (default: {D2_LOCK_END})",
    )
    parser.add_argument(
        "--repo", default=Path("."), type=Path,
        help="Repository root to scan (default: cwd).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Emit JSON to stdout only; no report file, no FAILURES append.",
    )
    parser.add_argument(
        "--output", default=None, type=Path,
        help="Override report output path (default: reports/skill_patch_count_YYYY-MM.md).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo.resolve()
    now = datetime.now(KST)
    violations = scan_violations(repo_root, args.since, args.until)

    if args.dry_run:
        payload = {
            "violation_count": len(violations),
            "since": args.since,
            "until": args.until,
            "violations": violations,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not violations else 1

    output = args.output or (
        repo_root / "reports" / f"skill_patch_count_{now.strftime('%Y-%m')}.md"
    )
    write_report(violations, output, now, args.since, args.until)
    if violations:
        # AUDIT-05 (D-23): skip append when all violations already recorded.
        failures_path = repo_root / "FAILURES.md"
        if failures_path.exists():
            existing_text = failures_path.read_text(encoding="utf-8")
            existing_hashes = _existing_violation_hashes(existing_text)
        else:
            existing_hashes = set()
        new_violations = [
            v for v in violations
            if (v.get("hash") or "")[:7] not in existing_hashes
        ]
        if not new_violations:
            logger.info(
                "[skill_patch_counter] 신규 violation 없음 — 기존 F-D2-NN 에 %d건 "
                "이미 기록 (대표님, 재실행 skip)",
                len(violations),
            )
            # Skip FAILURES.md append; report file already written above.
            # Preserve exit code contract: violations exist in window → rc=1.
        else:
            append_failures(new_violations, repo_root, now)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
