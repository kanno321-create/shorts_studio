---
phase: 10
plan: 01
subsystem: audit
tags: [d-2-lock, fail-04, git-log, regex, failures-append, markdown-report]
requires:
  - FAILURES.md (D-11 append-only reservoir)
  - .claude/hooks/pre_tool_use.py (check_failures_append_only reference for bypass-by-direct-I/O)
  - scripts/failures/aggregate_patterns.py (stdlib-only argparse pattern reused)
provides:
  - scripts/audit/skill_patch_counter.py (CLI — 291 lines, stdlib only)
  - scripts/audit/__init__.py (package namespace)
  - reports/.gitkeep (monthly report output placeholder)
  - tests/phase10/__init__.py + conftest.py + test_skill_patch_counter.py (Phase 10 test scaffold)
affects:
  - FAILURES.md (conditional append on violation > 0; direct open('a') hook-bypass per D-11)
  - reports/skill_patch_count_YYYY-MM.md (written on non-dry-run execution)
tech-stack:
  added: []
  patterns:
    - stdlib-only (argparse + subprocess + re + json + zoneinfo.ZoneInfo)
    - Windows cp949 stdout guard (sys.stdout.reconfigure encoding='utf-8' errors='replace')
    - UTF-8 ensure_ascii=False for Korean commit subject round-trip
    - Direct open('a') on FAILURES.md bypasses Claude Write/Edit hook (D-11 escape hatch)
    - git log --since=YYYY-MM-DD 00:00:00 --until=YYYY-MM-DD 23:59:59 (Rule 1 _boundary fix)
key-files:
  created:
    - scripts/audit/__init__.py
    - scripts/audit/skill_patch_counter.py (291 lines)
    - tests/phase10/__init__.py
    - tests/phase10/conftest.py (148 lines, 3 fixtures)
    - tests/phase10/test_skill_patch_counter.py (11 tests, 282 lines)
    - reports/.gitkeep
    - .planning/phases/10-sustained-operations/deferred-items.md (D10-01-DEF-01)
  modified: []
decisions:
  - D-2 Lock 물리적 증명 CLI 는 stdlib-only + subprocess git log + 4 POSIX regex 로 확정
  - directive-authorized Pre-Phase10 commits (8172e9c, e57f891) 은 투명하게 count 에 포함 — Whitelist 금지 (Risk #1 옵션 D, 2026-04-20 대표님 승인본)
  - FAILURES append 은 direct open('a') 로 Claude Write hook 을 bypass (D-11 strict-prefix 는 append 모드가 원천 보장)
  - git 2.51 Windows approxidate bug 를 Rule 1 _boundary() helper 로 회피 — bare YYYY-MM-DD 를 YYYY-MM-DD HH:MM:SS 로 자동 확장
metrics:
  duration_min: 15
  tasks: 2
  commits: 3
  tests_added: 11
  tests_passing: 11
  regression_phase4: 244/244
  lines_production: 299
  lines_test: 430
completed: 2026-04-20
---

# Phase 10 Plan 01: Skill Patch Counter Summary

D-2 Lock 기간 (2026-04-20 ~ 2026-06-20) 중 4 금지 경로 commit 위반을 `git log` 으로 count 하고 월간 Markdown 리포트 + FAILURES.md F-D2-NN append 를 생성하는 stdlib-only Python CLI (`scripts/audit/skill_patch_counter.py`) 완성. 11/11 Phase 10 tests GREEN, Phase 4 regression 244/244 보존, 실 repo dry-run 에서 directive-authorized Pre-Phase10 commits 2건 × 2 forbidden paths = 4 violations 정확히 감지.

## What Was Built

### scripts/audit/skill_patch_counter.py (291 lines, stdlib-only)

**Public surface:**
- `FORBIDDEN_PATTERNS: list[re.Pattern[str]]` — 4 regex: `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md`
- `D2_LOCK_START = "2026-04-20"` + `D2_LOCK_END = "2026-06-20"` (locked CONTEXT decision)
- `KST = ZoneInfo("Asia/Seoul")`
- `scan_violations(repo_root, since, until) -> list[dict]` — git log driver
- `write_report(violations, output, now, since, until) -> None` — Markdown report writer
- `append_failures(violations, repo_root, now) -> None` — direct open('a') bypass
- `main(argv=None) -> int` — argparse CLI (--since / --until / --repo / --dry-run / --output)

**Design invariants:**
1. Stdlib-only — no pandas / no pyyaml / no click. Reuses `scripts/failures/aggregate_patterns.py` argparse pattern.
2. `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` Windows cp949 guard (top-of-file + redundantly after stdout.print).
3. `ensure_ascii=False` in json.dumps — Korean commit subjects (e.g. "세션 컨텍스트 단절 영구 수정") round-trip cleanly.
4. `---COMMIT---%n%H|%aI|%s` sentinel splits metadata from `--name-only` file list without CRLF-sensitive `%n` newline counting.
5. Regex uses POSIX forward-slash; line normalised via `line.replace("\\", "/")` before match (Windows `git log --name-only` already emits forward-slash but the normalisation is cheap insurance).
6. `append_failures()` uses `with failures.open("a", encoding="utf-8") as f:` — this is the **documented D-11 escape hatch** for programmatic append. The hook only inspects Claude Write/Edit/MultiEdit tool inputs; open('a') from a subprocess does NOT trigger it. The strict-prefix invariant still holds because mode `a` cannot truncate.
7. Auto-incrementing F-D2-NN id via `re.findall(r"## F-D2-(\d{2})", existing)` + `max(..., default=0) + 1`.

### tests/phase10/ scaffold

- `conftest.py` (148 lines):
  - `tmp_git_repo` fixture: `git init` + seed commit at 2026-04-20T10:00 with deterministic user.name/user.email.
  - `make_commit(files_dict, msg, when)` helper: writes files → `git add` → `git commit --no-verify --date`, returns commit hash.
  - `freeze_kst_now` autouse fixture: monkeypatches `datetime.now(KST)` to 2026-04-30T09:00 via `_FrozenDatetime` subclass (only when skill_patch_counter module is importable — gracefully no-op during Task 1 fixture-only phase).
  - `_subprocess_env()` — inherits PATH/HOME for Windows git while overriding GIT_AUTHOR_* for reproducibility.

- `test_skill_patch_counter.py` (11 tests, 282 lines):
  - 3 fixture tests (Task 1): `test_tmp_git_repo_fixture_creates_repo`, `test_make_forbidden_commit_helper`, `test_reports_gitkeep_exists`.
  - 8 behavioural tests (Task 2): A (clean), B (1 hook violation + F-D2 append), C (4 categories), D (allowed paths), E (--dry-run), F (+09:00 timestamp), G (byte-level prefix preservation), H (CLI --since/--until override via subprocess spy).

### reports/.gitkeep

Empty file establishing `reports/` as a tracked directory. Monthly reports (`skill_patch_count_YYYY-MM.md`) write here.

## Commits

| Task | Commit | Description |
| ---- | ------ | ----------- |
| 1 | `1d62d38` | `test(10-01): Phase 10 scaffold + conftest fixture 3 tests RED→GREEN` |
| 2a (RED) | `a753ad8` | `test(10-01): skill_patch_counter 8 regression tests RED (A-H)` |
| 2b (GREEN) | `b71f681` | `feat(10-01): skill_patch_counter CLI + GREEN (11/11 tests, 4 real violations)` |

## Verification Evidence

### Test suite

```text
$ python -m pytest tests/phase10/test_skill_patch_counter.py -q
...........
11 passed in 3.00s

$ python -m pytest tests/phase10/ -q
................................
32 passed in 4.49s   # 11 (Plan 10-01) + 21 (Plan 10-02 parallel executor, drift_scan)
```

### CLI smoke

```text
$ python -m scripts.audit.skill_patch_counter --dry-run --since=2026-04-20 --until=2026-06-20
{
  "violation_count": 4,
  "since": "2026-04-20",
  "until": "2026-06-20",
  "violations": [
    {"hash": "e57f8912...", "date": "2026-04-20T21:07:33+09:00",
     "subject": "docs(claude-md): slim to 96 lines + add Perfect Navigator (대표님 directive)",
     "violating_file": ".claude/hooks/session_start.py"},
    {"hash": "e57f8912...", ..., "violating_file": "CLAUDE.md"},
    {"hash": "8172e9cd...", "date": "2026-04-20T19:31:28+09:00",
     "subject": "fix(context): 세션 컨텍스트 단절 영구 수정 — memory 9종 + session_start Step 4-6 + FAILURES.md F-CTX-01",
     "violating_file": ".claude/hooks/session_start.py"},
    {"hash": "8172e9cd...", ..., "violating_file": "CLAUDE.md"}
  ]
}
```

**Interpretation:** 2 Pre-Phase10 commits × 2 forbidden paths each = 4 violations. Per 2026-04-20 대표님 승인본 Risk #1 옵션 D, these directive-authorized commits are **transparently recorded** (NOT whitelisted). Plan 1 itself does not modify any forbidden path — the 4 violations exist regardless of Plan 1 execution.

### Acceptance grep checks

```text
$ wc -l scripts/audit/skill_patch_counter.py          # 291 (≥100 required)
$ grep -c FORBIDDEN_PATTERNS scripts/audit/skill_patch_counter.py   # 4 (≥2 required)
$ grep -c 'D2_LOCK_START = "2026-04-20"' ...          # 1
$ grep -c 'D2_LOCK_END = "2026-06-20"' ...            # 1
$ grep -c sys.stdout.reconfigure ...                  # 2
$ grep -ci "hook bypass\|append-only\|check_failures_append_only" ...  # 3
```

### Regression: Phase 4 baseline

```text
$ python -m pytest tests/phase04 -q --tb=no
244 passed in 0.51s
```

Phase 4 regression preserved (244/244 GREEN).

## Deviations from Plan

### Rule 1 — Bug fix: git 2.51 Windows approxidate

**Found during:** Task 2 manual CLI smoke (`python -m scripts.audit.skill_patch_counter --dry-run`).

**Issue:** `git log --since=2026-04-20` on git 2.51 Windows returns zero commits even when today's commits exist. The bare `YYYY-MM-DD` form is parsed as a *relative* anchor which excludes commits earlier today. Without a fix, the directive-authorized 2026-04-20 commits (the exact rows we must detect) are silently dropped.

**Fix:** Added `_boundary(raw, which)` helper that expands bare `YYYY-MM-DD` to `YYYY-MM-DD 00:00:00` (since) / `YYYY-MM-DD 23:59:59` (until). Test H was updated from `assert "--since=2026-05-01" in flat` to `assert "2026-05-01" in flat` so the normalisation is test-tolerant.

**Files modified:** `scripts/audit/skill_patch_counter.py` (added `_boundary`), `tests/phase10/test_skill_patch_counter.py` (relaxed Test H assertions).

**Commit:** `b71f681`

## Known Stubs

None. All public surfaces are wired:
- `scan_violations` returns real `list[dict]` from `git log`.
- `write_report` writes a real file (when not `--dry-run`).
- `append_failures` performs a real `open('a')` append (when FAILURES.md exists).
- `main` returns real exit codes (0 / 1 / 2).
- `FORBIDDEN_PATTERNS` is a real `list[re.Pattern]` compiled at module import.

## Deferred Issues

### D10-01-DEF-01 — Phase 5/6 pre-existing regressions

Full detail in `.planning/phases/10-sustained-operations/deferred-items.md`.

Tests listed there fail because of Phase 9.1 stack migration (gen3_alpha_turbo → gen4.5, Kling 2.6 Pro primary, Veo 3.1 Fast fallback) and Plan 06-08 `deprecated_patterns.json` 6→8 expansion (now further bumped by Plan 10-02 parallel executor running drift_scan). None of these tests touch any file modified by Plan 10-01. Out of scope per the deviation-rules scope boundary.

## Authentication Gates

None. No external services, OAuth, or API keys required. git subprocess + local filesystem I/O only.

## Next Steps

Plan 02 (`10-02-drift-scan-phase-lock`) — running in parallel as the sibling Wave 1 executor (evidence: `tests/phase10/test_drift_scan.py` co-appeared during Plan 10-01's Task 2 RED commit). Plans 03 (YouTube Analytics fetch), 04 (Scheduler hybrid), 05-08 remain.

## Self-Check: PASSED

- [x] `scripts/audit/__init__.py` exists (8 lines)
- [x] `scripts/audit/skill_patch_counter.py` exists (291 lines ≥100 min)
- [x] `tests/phase10/conftest.py` exists (148 lines ≥60 min)
- [x] `tests/phase10/test_skill_patch_counter.py` exists (11 tests)
- [x] `reports/.gitkeep` exists
- [x] commit `1d62d38` in git log (`git log --all --oneline | grep 1d62d38`)
- [x] commit `a753ad8` in git log
- [x] commit `b71f681` in git log
- [x] FORBIDDEN_PATTERNS regex count = 4
- [x] D2_LOCK_START = "2026-04-20" literal present
- [x] D2_LOCK_END = "2026-06-20" literal present
- [x] sys.stdout.reconfigure guard present
- [x] `python -m scripts.audit.skill_patch_counter --dry-run` exits with expected code
- [x] `python -m scripts.audit.skill_patch_counter --help` prints argparse usage
- [x] 11/11 Phase 10 Plan 1 tests GREEN
- [x] 244/244 Phase 4 regression preserved
