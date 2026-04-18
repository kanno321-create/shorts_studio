---
phase: 03-harvest
plan: 01
subsystem: harvest-infrastructure
tags: [agent-spec, harvest-importer, python-stdlib, scaffold, AGENT-06, cli-orchestrator]
requires: ["path_manifest.json (Plan 03-02)", "02-HARVEST_SCOPE.md blacklist"]
provides:
  - "harvest-importer agent spec (AGENT-06)"
  - "8-stage CLI orchestrator (harvest_importer.py)"
  - "SINGLE SOURCE OF TRUTH blacklist parser (len==10 invariant)"
  - "CONFLICT_MAP parser (13/16/10 invariant)"
  - "5-rule decision algorithm + 39-row HARVEST_DECISIONS.md emitter"
  - "Recursive filecmp.dircmp wrapper"
  - "Windows cmd.exe attrib +R /S /D lockdown + PermissionError probe"
  - "13-check verify_harvest.py (--quick/--full)"
affects: [harvest_importer.py, Wave 1-4 Plans 03-03..03-09]
tech_stack:
  added: []
  patterns:
    - ast-literal-eval-safe-load
    - filecmp-dircmp-recursive
    - cmd-exe-attrib-invocation
    - permissionerror-probe-verify
    - stage-gated-orchestrator
    - argparse-cli-boundary
    - idempotent-append-only-merge
key_files:
  created:
    - .claude/agents/harvest-importer/AGENT.md
    - scripts/harvest/__init__.py
    - scripts/harvest/harvest_importer.py
    - scripts/harvest/blacklist_parser.py
    - scripts/harvest/conflict_parser.py
    - scripts/harvest/decision_builder.py
    - scripts/harvest/diff_verifier.py
    - scripts/harvest/lockdown.py
    - scripts/harvest/verify_harvest.py
    - .planning/phases/03-harvest/03-01-SUMMARY.md
  modified: []
decisions:
  - "AGENT.md = 107 lines (≤ 500 harness-audit limit) with 378-char description (≤ 1024)"
  - "blacklist_parser owns M-2 contract — `len != 10` raises ValueError (Plan 08 must NOT re-assert)"
  - "conflict_parser raises CONFLICT_MAP_COUNT_MISMATCH on 13/16/10 deviation (fail-loudly)"
  - "lockdown uses subprocess.run([\"cmd.exe\", \"/c\", ...]) — Git Bash glob path rejected"
  - "All modules stdlib-only (argparse/ast/datetime/filecmp/hashlib/json/pathlib/random/re/shutil/subprocess/sys/typing)"
  - "Zero eval/exec/bare except:pass across 8 scripts"
  - "harvest_importer + verify_harvest use sys.path fallback to work both as `-m` and as direct `python scripts/...py`"
metrics:
  duration_minutes: 7
  completed: 2026-04-19
  tasks_completed: 2
  commits: 2
requirements_completed: [AGENT-06]
---

# Phase 03 Plan 01: AGENT-SPEC Summary

Scaffolded the harvest-importer agent — 1 AGENT.md spec + 7 Python stdlib modules (plus `__init__.py`) under `scripts/harvest/`. Wave 1~4 of Phase 3 now has the single CLI entry point (`harvest_importer.py`) they depend on, and blacklist/conflict-map count invariants own their contracts at the parser layer so downstream plans cannot silently drift.

---

## What Was Built

### Task 1: AGENT.md (107 lines)

`studios/shorts/.claude/agents/harvest-importer/AGENT.md` — minimal spec (not pseudocode) with 7 sections:

1. **Purpose** — AGENT-06 one-shot executor, consumes pre-locked 02-HARVEST_SCOPE.md (never re-derives A-class 13).
2. **Inputs** — 10 CLI flags documented (`--source`, `--scope`, `--conflict-map`, `--manifest`, `--dest`, `--failures-out`, `--decisions-out`, `--audit-log`, `--lockdown`, `--stage`).
3. **Outputs** — 4 raw dirs + FAILURES merge + HARVEST_DECISIONS.md (39 rows) + audit_log.md + Tier 3 read-only attr.
4. **Invariants** — 8 hard rules enumerated (shorts_naberal read-only; lockdown last; ast.literal_eval only; no silent except; cmd.exe attrib; secret file filter; idempotency via source-marker; CONFLICT_MAP 13/16/10 invariant).
5. **Execution Order** — 8-stage sequence with parallelization notes.
6. **Deprecation** — one-shot, not importable from Phase 4+ code.
7. **References** — stdlib dependencies, decision docs, research artifacts, verification commands, CLI contract with downstream plans.

Frontmatter description length: **378 chars** (well under 1024-char harness-audit limit).

### Task 2: 8 Python stdlib modules (1,329 total lines)

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 1 | Package marker |
| `harvest_importer.py` | 387 | 8-stage orchestrator CLI with audit_log structured logging |
| `blacklist_parser.py` | 80 | `ast.literal_eval` + **M-2 SSOT contract** (len==10 ValueError) + per-entry schema validation |
| `conflict_parser.py` | 85 | `^### [ABC]-N.` regex + 13/16/10 invariant via `CONFLICT_MAP_COUNT_MISMATCH` exception + `extract_entry_body` helper |
| `decision_builder.py` | 167 | 5-rule `judge()` + `build_decisions_md` emitter producing verbatim A + generated B/C rows |
| `diff_verifier.py` | 116 | `filecmp.dircmp` recursive walker with 4 mismatch categories + standalone CLI |
| `lockdown.py` | 121 | `apply_lockdown`/`verify_lockdown`/`unlock` via `cmd.exe /c attrib` + PermissionError probe |
| `verify_harvest.py` | 372 | 13 named checks in registry + `--quick`/`--full`/`--check`/`--list` CLI + sha256 10% spot sampler |

---

## Verification Results

### Task 1 acceptance criteria

- [x] `AGENT.md` exists at `studios/shorts/.claude/agents/harvest-importer/AGENT.md`
- [x] Line count = 107 (≤ 500 harness-audit)
- [x] description frontmatter = 378 chars (≤ 1024)
- [x] 8 invariants listed verbatim in `## Invariants` section
- [x] Trigger keywords `harvest-importer`, `Phase 3`, `AGENT-06` all present in description
- [x] `eval()` only appears in "ast.literal_eval only. `eval()` / `exec()` are PROHIBITED" context (1 mention)

### Task 2 acceptance criteria

- [x] All 8 `.py` files exist (`__init__` + 7 modules)
- [x] `python -c "import ast; [ast.parse(open(f, encoding='utf-8').read()) for f in ...]"` — all parse cleanly
- [x] `python -c "from scripts.harvest import blacklist_parser, conflict_parser, decision_builder, diff_verifier, lockdown"` — imports OK
- [x] `grep -rE "^\s*(eval|exec)\(" scripts/harvest/` → 0 matches (verified via Grep tool)
- [x] `grep -rnE "^\s*except\s*:\s*pass" scripts/harvest/` → 0 matches (single comment mention only, not code)
- [x] Stdlib-only imports (13 modules): `argparse`, `ast`, `datetime`, `filecmp`, `hashlib`, `json`, `pathlib`, `random`, `re`, `shutil`, `subprocess`, `sys`, `typing`
- [x] `python scripts/harvest/verify_harvest.py --help` exits 0
- [x] `python scripts/harvest/diff_verifier.py --help` exits 0
- [x] `python scripts/harvest/harvest_importer.py --help` exits 0
- [x] `lockdown.py` contains literal `"cmd.exe"` and `"attrib +R /S /D"` (verified Grep lines 31, 85)
- [x] `conflict_parser.py` contains explicit `assert len(... == 13/16/10)` trio (verified Grep lines 55-57)

### Live-data integration check (bonus)

Ran `python scripts/harvest/blacklist_parser.py .planning/phases/02-domain-definition/02-HARVEST_SCOPE.md`:
- Output: `[OK] parsed 10 blacklist entries` — M-2 contract holds against real scope file.
- All 10 entries resolve correctly (5 orchestrate.py + longform/ + create-video/ + create-shorts/SKILL.md + selenium pattern + orchestrate.py full-file).

---

## Deviations from Plan

### Minor additions (Rule 2 — critical functionality)

**1. [Rule 2 - Missing critical functionality] sys.path bootstrap in harvest_importer.py + verify_harvest.py**
- **Found during:** Task 2 CLI verification (`python scripts/harvest/verify_harvest.py --help` failed with `ModuleNotFoundError: No module named 'scripts.harvest'`)
- **Issue:** Plan contract required CLI to be runnable via `python scripts/harvest/verify_harvest.py`, but plain `from scripts.harvest import ...` only resolves when invoked with `-m scripts.harvest.*` or when CWD is configured on sys.path.
- **Fix:** Added `if __package__ in (None, ""): sys.path.insert(0, <repo_root>)` bootstrap to both scripts. Now runnable both ways.
- **Files modified:** `scripts/harvest/harvest_importer.py` (lines 18-25), `scripts/harvest/verify_harvest.py` (lines 19-24).
- **Commit:** `2c630b5` (rolled into Task 2 commit).
- **Justification:** Plan acceptance criteria explicitly required `python scripts/harvest/verify_harvest.py --help` to exit 0 — without this fix, that criterion fails. Not architectural; pure boot path hygiene.

**2. [Rule 2 - Safety] `verify_lockdown` restores probe content on unexpected write-success before raising**
- **Found during:** Writing lockdown.py
- **Issue:** If lockdown failed and probe write succeeded, the probe file would be left containing `LOCKDOWN_VERIFY_TAMPER` — corrupting a harvested file mid-verification.
- **Fix:** Capture `original_content = probe.read_bytes()` before write attempt; on write-succeeds branch, restore `probe.write_bytes(original_content)` before `raise AssertionError`.
- **Files modified:** `scripts/harvest/lockdown.py` (lines 60-67).
- **Commit:** `2c630b5`.
- **Justification:** Correctness — verification must be non-destructive even in failure mode.

### Out-of-scope discoveries (logged, not fixed)

None.

### Blockers hit

None.

---

## Downstream Unblock Status

**Wave 1 (Plans 03-03..06 — copy operations) unblocked:**
- `harvest_importer.py --stage 3 --name <raw_dir>` is callable (verified via `--help`).
- `path_manifest.json` (Plan 02 output) integrates via `manifest.get(name)` lookup.
- Secret file ignore patterns (`client_secret*.json`, `token_*.json`, `.env*`, `*.key`, `*.pem`) enforced in `_copy_raw_dir`.

**Wave 2 (Plan 03-07 — diff verify + FAILURES merge) unblocked:**
- `deep_diff()` and `_merge_failures()` both implemented, invokable via `--stage 4,5`.

**Wave 3 (Plan 03-08 — CONFLICT_MAP + 5-rule + blacklist audit) unblocked:**
- `conflict_parser.parse_conflict_map` + `decision_builder.build_decisions_md` via `--stage 6`.
- `_blacklist_grep_audit` via `--stage 7`.
- **M-2 contract locked at parser layer** — Plan 08 acceptance must NOT re-assert `len(blacklist) == 10` (the parser already raised if not).

**Wave 4 (Plan 03-09 — Tier 3 lockdown + verify_harvest --full) unblocked:**
- `lockdown.apply_lockdown` + `lockdown.verify_lockdown` via `--stage 8 --lockdown`.
- `verify_harvest.py --full` runs 13 quick checks + deep_diff + sha256 10% sample.

---

## Commits Made

| Hash | Message | Files |
|------|---------|-------|
| `27b0c82` | `feat(03-01): add harvest-importer AGENT.md spec` | 1 file, +107 |
| `2c630b5` | `feat(03-01): add harvest-importer Python stdlib modules (8 files)` | 8 files, +1329 |

---

## Self-Check: PASSED

- `.claude/agents/harvest-importer/AGENT.md` — FOUND (107 lines)
- `scripts/harvest/__init__.py` — FOUND (1 line)
- `scripts/harvest/harvest_importer.py` — FOUND (387 lines)
- `scripts/harvest/blacklist_parser.py` — FOUND (80 lines)
- `scripts/harvest/conflict_parser.py` — FOUND (85 lines)
- `scripts/harvest/decision_builder.py` — FOUND (167 lines)
- `scripts/harvest/diff_verifier.py` — FOUND (116 lines)
- `scripts/harvest/lockdown.py` — FOUND (121 lines)
- `scripts/harvest/verify_harvest.py` — FOUND (372 lines)
- Commit `27b0c82` — FOUND in `git log`
- Commit `2c630b5` — FOUND in `git log`

All plan artifacts present on disk. All commits verified. No stubs — every module has a functional implementation (not placeholders).
