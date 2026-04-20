"""Phase 10 Plan 1 — skill_patch_counter tests (FAIL-04 / SC#1).

Test layout:
    Task 1 (3 tests): conftest infrastructure (tmp_git_repo, make_commit, reports/.gitkeep).
    Task 2 (8 tests): skill_patch_counter.main() behavioral contract.
        A. No violations → exit 0 + `Violation count: 0 ✅`
        B. Single hook violation → exit 1 + 1-row table + FAILURES.md F-D2-NN append
        C. All 4 forbidden paths touched → violation count == 4
        D. Files outside forbidden → count 0
        E. --dry-run skips file output (stdout JSON only)
        F. Report contains KST (+09:00) timestamp
        G. FAILURES.md append is hook-safe (strict prefix preservation)
        H. --since / --until override works (monkeypatched subprocess)

Total: 11 tests. All must be GREEN after Task 2.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Task 1: conftest infrastructure tests (fixture-only, no CLI invocation yet).
# ---------------------------------------------------------------------------


def test_tmp_git_repo_fixture_creates_repo(tmp_git_repo: Path) -> None:
    """conftest.tmp_git_repo must initialise .git/ in tmp_path."""
    assert (tmp_git_repo / ".git").is_dir(), "tmp_git_repo must contain .git/"
    out = subprocess.run(
        ["git", "-C", str(tmp_git_repo), "log", "--oneline"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    assert "seed repo" in out.stdout, "seed commit must exist"


def test_make_forbidden_commit_helper(tmp_git_repo: Path, make_commit) -> None:
    """conftest.make_commit helper must return a real commit hash."""
    commit_hash = make_commit(
        {"CLAUDE.md": "# modified\n"},
        "docs(test): synthetic CLAUDE.md edit",
    )
    assert len(commit_hash) == 40, "commit hash should be 40 hex chars"
    out = subprocess.run(
        ["git", "-C", str(tmp_git_repo), "log", "-1", commit_hash, "--name-only"],
        capture_output=True, text=True, check=True, encoding="utf-8",
    )
    assert "CLAUDE.md" in out.stdout, "CLAUDE.md must appear in commit name-only"


def test_reports_gitkeep_exists(repo_root: Path) -> None:
    """reports/.gitkeep must exist in the real repo root."""
    gk = repo_root / "reports" / ".gitkeep"
    assert gk.exists(), f"{gk} must exist as Plan 1 report output placeholder"


# ---------------------------------------------------------------------------
# Task 2: skill_patch_counter CLI behavioral tests (A-H).
# ---------------------------------------------------------------------------


def _seed_failures_md(repo: Path) -> Path:
    """Create a synthetic FAILURES.md so append() has a target file."""
    failures = repo / "FAILURES.md"
    failures.write_text(
        "# FAILURES.md — shorts_studio\n\n"
        "> **규율 (D-11)**: append-only (test seed).\n\n"
        "---\n\n"
        "## F-CTX-01 — 세션 컨텍스트 단절 (seed for phase10 tests)\n\n"
        "**증상**: seed entry so aggregate regex matches.\n",
        encoding="utf-8",
    )
    return failures


def test_A_no_violations_in_clean_repo(tmp_git_repo: Path, make_commit) -> None:
    """A. No forbidden-path commits → exit 0 + `Violation count: 0 ✅`."""
    from scripts.audit.skill_patch_counter import main

    # Only allowed-path edits
    make_commit(
        {"scripts/audit/skill_patch_counter.py": "print('ok')\n"},
        "feat: allowed scripts change",
    )
    rc = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc == 0, f"clean repo must return exit 0 (got {rc})"
    report = tmp_git_repo / "reports" / "skill_patch_count_2026-04.md"
    assert report.exists(), "report file must be written"
    text = report.read_text(encoding="utf-8")
    assert "**Violation count:** 0" in text, "count 0 must be reported"
    assert "✅" in text, "green badge required when count == 0"


def test_B_single_hook_violation_counts_1(tmp_git_repo: Path, make_commit) -> None:
    """B. One .claude/hooks/*.py commit → exit 1 + 1-row table + FAILURES append."""
    from scripts.audit.skill_patch_counter import main

    _seed_failures_md(tmp_git_repo)
    pre_append = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")
    pre_len = len(pre_append)

    make_commit(
        {".claude/hooks/pre_tool_use.py": "# violation\n"},
        "fix(hook): D-2 Lock 기간 중 hook 수정 (synthetic violation)",
    )

    rc = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc == 1, f"violation must return exit 1 (got {rc})"

    report = tmp_git_repo / "reports" / "skill_patch_count_2026-04.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "**Violation count:** 1" in text
    assert "🚨" in text
    assert "pre_tool_use.py" in text
    assert "| Hash |" in text, "violation table header required"

    # FAILURES.md append verification
    post = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")
    assert post.startswith(pre_append), "D-11 strict prefix preservation required"
    assert len(post) > pre_len, "new content must be appended"
    assert re.search(r"## F-D2-\d{2}", post), "F-D2-NN heading must be added"


def test_C_all_four_forbidden_paths_count_4(tmp_git_repo: Path, make_commit) -> None:
    """C. Touch all 4 forbidden pattern categories → count == 4."""
    from scripts.audit.skill_patch_counter import main

    _seed_failures_md(tmp_git_repo)

    make_commit(
        {".claude/agents/producers/scripter/SKILL.md": "# agent skill\n"},
        "fix(agent): scripter SKILL (violation 1)",
    )
    make_commit(
        {".claude/skills/notebooklm/SKILL.md": "# skill\n"},
        "fix(skill): notebooklm (violation 2)",
    )
    make_commit(
        {".claude/hooks/session_start.py": "# hook\n"},
        "fix(hook): session_start (violation 3)",
    )
    make_commit(
        {"CLAUDE.md": "# root claude md\n"},
        "docs(claude-md): edit (violation 4)",
    )

    rc = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc == 1

    report = tmp_git_repo / "reports" / "skill_patch_count_2026-04.md"
    text = report.read_text(encoding="utf-8")
    assert "**Violation count:** 4" in text

    # Table should have 4 data rows (excluding header + separator)
    lines = [ln for ln in text.splitlines() if ln.startswith("| ") and "Hash" not in ln and "----" not in ln]
    assert len(lines) == 4, f"4 violation rows expected, got {len(lines)}"


def test_D_files_outside_forbidden_not_counted(tmp_git_repo: Path, make_commit) -> None:
    """D. Edits to allowed paths → count 0."""
    from scripts.audit.skill_patch_counter import main

    make_commit(
        {"scripts/audit/skill_patch_counter.py": "# ok\n"},
        "feat: allowed script edit",
    )
    make_commit(
        {"wiki/algorithm/new_node.md": "# new wiki\n"},
        "docs(wiki): append allowed",
    )
    make_commit(
        {".planning/phases/10-sustained-operations/new.md": "# plan\n"},
        "docs(phase10): meta allowed",
    )
    rc = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc == 0

    report = tmp_git_repo / "reports" / "skill_patch_count_2026-04.md"
    text = report.read_text(encoding="utf-8")
    assert "**Violation count:** 0" in text


def test_E_dry_run_skips_file_output(tmp_git_repo: Path, make_commit, capsys) -> None:
    """E. --dry-run + violation → no report file + no FAILURES append + stdout JSON."""
    from scripts.audit.skill_patch_counter import main

    _seed_failures_md(tmp_git_repo)
    failures_pre = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")

    make_commit(
        {".claude/hooks/session_start.py": "# violation\n"},
        "fix(hook): test violation",
    )

    rc = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
        "--dry-run",
    ])
    assert rc == 1, "dry-run with violation must still exit 1"

    report = tmp_git_repo / "reports" / "skill_patch_count_2026-04.md"
    assert not report.exists(), "dry-run must NOT write report file"

    failures_post = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")
    assert failures_post == failures_pre, "dry-run must NOT append to FAILURES.md"

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["violation_count"] == 1
    assert "violations" in data
    assert data["since"] == "2026-04-20"
    assert data["until"] == "2026-06-20"


def test_F_report_contains_kst_timestamp(tmp_git_repo: Path, make_commit) -> None:
    """F. Report `Report generated:` line must carry +09:00 KST offset."""
    from scripts.audit.skill_patch_counter import main

    make_commit(
        {"scripts/audit/skill_patch_counter.py": "# ok\n"},
        "feat: allowed",
    )
    rc = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc == 0
    report = tmp_git_repo / "reports" / "skill_patch_count_2026-04.md"
    text = report.read_text(encoding="utf-8")
    assert "+09:00" in text, "KST offset must appear in report timestamp"
    assert "**Report generated:**" in text


def test_G_failures_append_is_hook_safe(tmp_git_repo: Path, make_commit) -> None:
    """G. Byte-level strict prefix preservation after append."""
    from scripts.audit.skill_patch_counter import main

    _seed_failures_md(tmp_git_repo)
    pre_bytes = (tmp_git_repo / "FAILURES.md").read_bytes()

    make_commit(
        {".claude/agents/shorts-supervisor/SKILL.md": "# violation\n"},
        "fix(agent): test violation",
    )

    main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])

    post_bytes = (tmp_git_repo / "FAILURES.md").read_bytes()
    assert post_bytes.startswith(pre_bytes), (
        "D-11 append-only: existing content must be byte-level strict prefix"
    )
    added = post_bytes[len(pre_bytes):].decode("utf-8")
    assert "F-D2-" in added, "F-D2-NN heading added"
    assert "SKILL.md" in added or "violation" in added


def test_H_cli_since_until_override(tmp_git_repo: Path, make_commit, monkeypatch) -> None:
    """H. --since / --until overrides are passed into git log verbatim."""
    from scripts.audit import skill_patch_counter as spc

    captured_args: list[list[str]] = []
    real_run = subprocess.run

    def _spy_run(cmd, *args, **kwargs):
        captured_args.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(spc.subprocess, "run", _spy_run)

    spc.main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-05-01",
        "--until", "2026-05-31",
        "--dry-run",
    ])

    # At least one captured invocation should be the git log
    log_calls = [c for c in captured_args if len(c) >= 2 and c[0] == "git" and c[1] == "log"]
    assert log_calls, "git log subprocess must have been invoked"
    flat = " ".join(log_calls[0])
    # _boundary() normalises bare YYYY-MM-DD to YYYY-MM-DD HH:MM:SS
    assert "2026-05-01" in flat, "--since override must appear in git log args"
    assert "2026-05-31" in flat, "--until override must appear in git log args"


# ---------------------------------------------------------------------------
# AUDIT-05 (Phase 11 Plan 11-05) — idempotency guard regression test (D-24).
# ---------------------------------------------------------------------------


def test_idempotency_skip_existing(tmp_git_repo: Path, make_commit) -> None:
    """D-24: counter run twice on same state MUST append only once.

    Phase A: fresh hook-file violation → rc=1 + 1 F-D2-NN entry appended.
    Phase B: identical state, run again → rc=1 but FAILURES.md byte-exact.
    Phase C: new violation → rc=1 + 1 more entry; Phase A entry preserved.
    """
    from scripts.audit.skill_patch_counter import main

    # Seed FAILURES.md so append_failures has a target
    failures_path = tmp_git_repo / "FAILURES.md"
    failures_path.write_text(
        "# FAILURES — append-only\n\n"
        "## F-D1-00 — 박제\n\n"
        "Pre-Phase10 seed entry (strict prefix preserved).\n\n",
        encoding="utf-8",
    )

    # Phase A: one hook-file violation
    make_commit({".claude/hooks/example.py": "# modified\n"}, "fix(hook): example edit")
    rc1 = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc1 == 1, f"Phase A: violations present → rc=1 (got {rc1})"
    post1 = failures_path.read_text(encoding="utf-8")
    assert post1.count("## F-D2-") == 1, (
        f"Phase A: exactly 1 F-D2 entry expected, got {post1.count('## F-D2-')}"
    )

    # Phase B: same git state, run again — MUST NOT append
    rc2 = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc2 == 1, f"Phase B: violations still exist → rc=1 (got {rc2})"
    post2 = failures_path.read_text(encoding="utf-8")
    assert post2 == post1, (
        "Phase B: FAILURES.md must be byte-exact unchanged on second run"
    )
    assert post2.count("## F-D2-") == 1, "Phase B: still exactly 1 F-D2 entry"

    # Phase C: new violation → append ONLY the new one
    make_commit({"CLAUDE.md": "# mod\n"}, "docs(test): second violation")
    rc3 = main([
        "--repo", str(tmp_git_repo),
        "--since", "2026-04-20",
        "--until", "2026-06-20",
    ])
    assert rc3 == 1, f"Phase C: violations present → rc=1 (got {rc3})"
    post3 = failures_path.read_text(encoding="utf-8")
    assert post3.count("## F-D2-") == 2, (
        f"Phase C: 2 F-D2 entries expected (A preserved + new), got {post3.count('## F-D2-')}"
    )
    assert post3.startswith(post1), (
        "Phase C: Phase A content preserved byte-exact as strict prefix (D-25)"
    )
