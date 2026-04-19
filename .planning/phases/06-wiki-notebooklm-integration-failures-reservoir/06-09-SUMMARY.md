---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 09
subsystem: wave-4-failures-aggregation-dry-run
tags: [fail-02, d-13, d-14, aggregation-cli, stdlib-only, dry-run, sha256, korean-utf8]

# Dependency graph
requires:
  - phase: 06
    plan: 01
    provides: tests/phase06/__init__.py + conftest.py (fixtures_dir, failures_sample_text) + tests/phase06/fixtures/failures_sample.md
  - phase: 06
    plan: 08
    provides: .claude/failures/FAILURES.md (24-line seed with 10-field entry schema) + .claude/failures/_imported_from_shorts_naberal.md (500-line Phase 3 import, sha256-locked — D-14 invariant baseline) + scripts/failures/.gitkeep placeholder
  - phase: 03
    provides: .claude/failures/_imported_from_shorts_naberal.md (Phase 3 sha256=a1d92cc1... the file Plan 09 parses but MUST NOT modify)
  - plan: 06-CONTEXT.md D-13 + D-14 + 06-RESEARCH.md §Area 8 lines 923-1033 (implementation + collision analysis + dry-run constraint)
provides:
  - scripts/failures/__init__.py (NEW, 7 lines — namespace docstring only, documents Phase 6 dry-run vs Phase 10 promotion boundary)
  - scripts/failures/aggregate_patterns.py (NEW, 164 lines — stdlib-only argparse CLI: argparse + hashlib + json + re + collections.Counter + pathlib. 4 public functions: iter_entries, normalize_pattern_key, aggregate, main. 2 regex constants: ENTRY_RE, TRIGGER_RE. --dry-run store_true default=True; intentionally NOT BooleanOptionalAction so Phase 6 code cannot disable dry-run. ensure_ascii=False for Korean UTF-8 round-trip. sys.stdout.reconfigure fallback for Windows cp949 stdout.)
  - tests/phase06/test_aggregate_patterns.py (NEW, 224 lines, 21 unit tests — ENTRY_RE/TRIGGER_RE schema matching + multi-digit FAIL-NNNN ids + iter_entries fixture parse + missing-file warning + trigger-less entries + imported schema compatibility + normalize_pattern_key determinism + case-insensitivity + punctuation-strip + whitespace-collapse + Korean preservation + trigger[:80] truncation + aggregate threshold filtering + empty input + duplicate counting + examples cap at 3 + main CLI default threshold + --output file + --threshold override)
  - tests/phase06/test_aggregate_dry_run.py (NEW, 154 lines, 10 integration tests — CLI subprocess against real _imported_from_shorts_naberal.md + both-files parsing + high-threshold empty candidates + low-threshold finds entries + missing --input exits 2 + nonexistent input warning + D-13 NO SKILL.md.candidate file created anywhere + D-14 sha256 byte-identical before/after + Korean UTF-8 stdout round-trip + --output file JSON validity)
affects:
  - Plan 06-11 (phase gate — this plan flips 6-09-01/02 rows ✅ green in 06-VALIDATION.md; Plan 11 asserts all Wave 4 plans complete before E2E gate)
  - Phase 10 promotion (Plan 09 is the dry-run substrate; Phase 10 extends aggregate_patterns.py with --promote flag + SKILL.md.candidate writer + 7-day staged rollout state machine — intentionally deferred per D-13)
  - Phase 5/6 regressions: zero collisions. Plan 09 creates only scripts/failures/*.py + tests/phase06/test_aggregate*.py. Pre-existing 2 Phase 5 failures (test_deprecated_patterns_json::test_six_patterns + test_phase05_acceptance::test_pytest_phase05_sweep_green) trace entirely to Plan 06-08's deprecated_patterns.json 6→8 expansion — out-of-scope for Plan 09, already logged in STATE.md as Plan 08 follow-up.

# Tech tracking
tech-stack:
  added: []  # stdlib-only: argparse, hashlib, json, re, collections.Counter, pathlib, sys
  patterns:
    - "Dry-run-only CLI structurally enforced via argparse.store_true + default=True without BooleanOptionalAction. There is no --no-dry-run flag (future Phase 10 adds --promote as the opt-in, keeping dry-run as safe default). This makes the 'dry-run cannot be disabled in Phase 6' contract auditable at the argparse-parser level rather than relying on runtime branches."
    - "sha256[:12] 48-bit pattern key — RESEARCH Area 8 line 1032 collision analysis proves safety up to ~16M unique entries (birthday bound sqrt(2^48) ≈ 1.6e7). FAILURES reservoir expects thousands of entries over years, well within safe margin. Shorter prefix (sha256[:8]) would save bytes but birthday collisions at ~65K entries; longer (sha256[:16]) is overkill. 12-char is the chosen balance — keys fit in 6-byte hex strings, grep-friendly, no collisions in realistic operation."
    - "Section-split pre-regex pattern: `re.split(r'(?=^### FAIL-)', text, flags=re.MULTILINE)` before per-section ENTRY_RE + TRIGGER_RE lookups. This prevents one entry's Trigger from leaking into a subsequent entry's scope when an entry has no Trigger field (e.g., a corrupted or schema-template entry). Without section-split, a plain re.findall on the full file would pair mismatched (summary, trigger) tuples."
    - "ensure_ascii=False + sys.stdout.reconfigure(encoding='utf-8') for Korean round-trip. Python 3.11+ on Windows defaults stdout to cp949 (MBCS), which mangles Korean hex-escapes if json.dumps uses ensure_ascii=True. reconfigure is wrapped in try/except (AttributeError, OSError) because on non-Windows or older Python the attribute may not exist — silent fallback is acceptable here because the --output file path uses write_text(encoding='utf-8') and bypasses stdout entirely."
    - "Warning-instead-of-raise for missing inputs: iter_entries prints 'WARN:' to stderr and returns without yielding. Design choice: the CLI is a reporting tool, not a strict validator. Users may pass a mix of valid and deprecated input paths during rollout; aborting on the first missing file would obscure all other entries. Exit code stays 0. (A future Plan 10 could add a --strict mode that escalates to rc=1 — deferred.)"
    - "source: md_path.name (basename only, not full path) in the entry dict. Reason: output JSON must remain stable across developer machines with different repo-root absolute paths. Tests assert basename equality (e.g., 'failures_sample.md', '_imported_from_shorts_naberal.md') which survives Windows vs POSIX path differences."
    - "Intentional template-entry inclusion: the FAILURES.md schema template line `### FAIL-NNN: [one-line summary]` inside the Entry Schema code block IS parsed as a valid entry by design. Rationale: the regex is semantic (id + summary + trigger), not syntactic (code-block-aware). A future Phase 10 --promote step will filter template-like keys ('FAIL-NNN' literal id, '[one-line...]' bracket-prefixed summaries) before creating SKILL.md.candidate files. For the dry-run aggregator the template contributes +1 to total_entries, which is transparent and visible in the output — not a silent bug."

key-files:
  created:
    - scripts/failures/__init__.py (7 lines — namespace docstring)
    - scripts/failures/aggregate_patterns.py (164 lines — CLI)
    - tests/phase06/test_aggregate_patterns.py (224 lines, 21 unit tests)
    - tests/phase06/test_aggregate_dry_run.py (154 lines, 10 integration tests)
  modified:
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (rows 6-09-01 + 6-09-02 flipped from "❌ W0 / ⬜ pending" to "✅ on disk / ✅ green")

key-decisions:
  - "BooleanOptionalAction intentionally NOT used for --dry-run: the plan's D-13 contract states dry-run cannot be disabled in Phase 6. Using argparse.BooleanOptionalAction would allow `--no-dry-run` to set dry_run=False, creating a path where future code could accidentally short-circuit the guard. store_true + default=True with no negation flag means the parser itself rejects any attempt to disable dry-run — the guarantee is encoded in the CLI surface, not in implementation branches. Phase 10 will add --promote as an opt-in positive flag instead of removing --dry-run."
  - "Warning-on-missing-file instead of raise: iter_entries prints to stderr and returns empty when a path doesn't exist. Alternative was to raise FileNotFoundError, which matches fail-loud principles. Chose warn-and-continue because (a) the CLI's purpose is to aggregate across multiple files — aborting on one missing file hides data in the other files, (b) argparse already validates CLI shape (missing --input exits 2), (c) test_cli_nonexistent_input_continues_with_warning locks this as explicit behavior. The CLI surface remains graceful; strict validation would go in a Phase 10 --strict flag."
  - "Regex-level template-entry inclusion: the FAILURES.md seed contains `### FAIL-NNN: [one-line summary]` inside a markdown code block as the entry schema. The current regex picks this up as a real entry (adding +1 to total_entries). Considered filtering at regex time (negative lookahead for `[` or literal 'FAIL-NNN' id). Rejected because (a) the regex is shared between iter_entries and the documented schema pattern — tightening it risks missing real entries with bracketed summaries, (b) Phase 10 promotion will filter template-like keys before writing SKILL.md.candidate, (c) total_entries=13 (vs 12 if filtered) is transparent and observable, not a silent bug. Filter-on-promotion is the cleaner boundary."
  - "source field uses md_path.name not full path: tests assert basename-equality and the output JSON must be stable across developer machines. Full paths would break test_iter_entries_on_fixture's `source == 'failures_sample.md'` assertion on different CI environments and leak absolute filesystem structure into the output. Basename is the minimum identifier that preserves traceability back to the source file."
  - "Section-split then per-section regex over plain re.findall: tried re.findall over full text — produces mismatched pairs when entries lack Trigger fields (next entry's Trigger leaks into previous entry's scope). Switched to re.split on `(?=^### FAIL-)` to bound each section's lookup scope. Covered by test_iter_entries_without_trigger which proves trigger='' for an entry with no Trigger line."

patterns-established:
  - "Pattern: Dry-run-default CLI with structural disable-impossibility. For any tool where the Phase-N policy forbids side effects: (a) argparse --<policy> action='store_true' default=True, (b) NO BooleanOptionalAction (no `--no-` prefix), (c) Phase-N+1 opt-in adds a positive flag (e.g., --promote, --apply, --write). This keeps the safety contract visible in the CLI help output and enforceable at parse time rather than implementation time. Reusable for Phase 10 promotion + any future dry-run tool."
  - "Pattern: Source file name (not path) in aggregated output JSON. For aggregation tools that scan multiple input files: store md_path.name as the source identifier. Enables stable test assertions across machines, stable JSON snapshots for golden-file comparisons, no absolute-path leakage to consumers. If full-path is needed for tooling, derive it externally (consumers already have the --input arguments)."
  - "Pattern: Warn-and-continue for optional-input CLI. When a reporting CLI accepts repeated --input files and any file might not exist at runtime: print 'WARN:' to stderr per missing file, continue iteration, return 0. Opposite (raise-fast) is correct for strict validators but wrong for aggregators where hiding other-file data is worse than logging the miss."
  - "Pattern: sha256[:12] = 48-bit pattern key for medium-scale deduplication. For any keying need where expected unique count < 16M: sha256[:12] gives grep-friendly 12-char hex keys, birthday-collision-safe at sqrt(2^48)=1.6e7 entries, 3x shorter than full sha256 (64 chars). Appropriate for FAILURES aggregation, log deduplication, fingerprinting. For collision-critical uses (content-addressed storage), use full sha256."

requirements-completed: [FAIL-02]

# Metrics
duration: ~8m
completed: 2026-04-19
---

# Phase 6 Plan 09: FAILURES Aggregation Dry-Run Summary

**Wave 4 AGGREGATION DRY-RUN locking FAIL-02 + D-13 invariant. scripts/failures/aggregate_patterns.py (164 lines, stdlib-only argparse CLI) reads any number of FAILURES-schema markdown files (supports both the 500-line Phase 3 `_imported_from_shorts_naberal.md` and the Phase 6 Plan 08 seeded `FAILURES.md`), normalizes pattern keys via sha256[:12] (48-bit collision-safe per RESEARCH Area 8), counts recurrences with collections.Counter, and emits JSON `{candidates, total_entries}` where candidates exceed a --threshold (default 3). D-13 dry-run immutability is structurally enforced: --dry-run uses argparse store_true default=True without BooleanOptionalAction, so Phase 6 code cannot disable it — Phase 10 will add a positive --promote flag as the opt-in. 31 new tests (21 unit + 10 subprocess) lock ENTRY_RE/TRIGGER_RE schema matching, Korean UTF-8 round-trip, trigger[:80] truncation, examples-cap-at-3, missing-file warn-and-continue, D-13 NO SKILL.md.candidate created anywhere, and D-14 sha256 byte-identical `_imported_from_shorts_naberal.md` before/after CLI run. Phase 6 full suite 217/217 PASS. Phase 5 regression: 2 pre-existing failures trace entirely to Plan 06-08's deprecated_patterns.json 6→8 expansion (out-of-scope for Plan 09; already logged in STATE.md).**

## Performance

| Metric | Value |
|---|---|
| aggregate_patterns.py LOC | 164 (stdlib-only, zero external deps) |
| __init__.py LOC | 7 (namespace docstring) |
| Tests created | 31 (21 unit + 10 subprocess integration) |
| Test runtime (2 new files) | ~0.65s |
| Phase 6 full suite runtime | ~2.68s (217 tests) |
| Phase 6 regression | 186 prior tests + 31 new = 217/217 PASS |
| Phase 5 regression delta | 0 (Plan 09 touches only scripts/failures/ + tests/phase06/ — no Phase 5 collisions; the 2 pre-existing Phase 5 failures trace to Plan 06-08) |

## Sample CLI Output

**Threshold=3 against imported file (no candidates expected — all 12 imported entries are unique):**

```json
{
  "candidates": [],
  "total_entries": 12
}
```

**Threshold=1 against both files (all 13 unique entries become candidates, each with count=1):**

```
TOTAL: 13
CANDIDATES: 13
  key=4cabb996b663 count=1   (FAIL-NNN schema template from FAILURES.md)
  key=abafb04664b1 count=1   (FAIL-001 imported)
  key=ff53ce527e16 count=1   (FAIL-004 imported)
  ...
```

Note: `FAIL-NNN` is the schema-template line from the FAILURES.md seed's Entry Schema code block. It is parsed as a real entry by design — Phase 10's promotion step will filter template-like keys before creating SKILL.md.candidate files. Transparent inclusion beats silent regex tightening per key-decisions.

## D-13 Dry-Run Invariant Verification

`test_d13_no_candidate_file_created` (subprocess integration test) runs:
```
python scripts/failures/aggregate_patterns.py --input <imported-copy> --threshold 1
```
with threshold=1 (forcing all entries into candidates), then rglob-searches for `SKILL.md.candidate` across tmp_path, CLI source dir, and repo root. **Zero hits across all three roots → D-13 structurally held.**

## D-14 Imported-File Byte-Identical Verification

`test_d14_imported_file_byte_identical_after_run` computes sha256 before/after CLI execution:

| Phase | sha256 (.claude/failures/_imported_from_shorts_naberal.md) |
|-------|------------------------------------------------------------|
| Before Plan 09 execution | `a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa` |
| After Plan 09 execution (full suite) | `a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa` |

**Byte-identical → D-14 invariant preserved.** Phase 11 will add a dedicated sha256-verifier test to lock this across all Phase 6+ plans.

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| `python -c "import scripts.failures.aggregate_patterns"` exits 0 | ✅ |
| `grep -c "def iter_entries"` outputs 1 | ✅ |
| `grep -c "def normalize_pattern_key"` outputs 1 | ✅ |
| `grep -c "def main"` outputs 1 | ✅ |
| `grep -c "hashlib.sha256"` outputs ≥1 | ✅ (1) |
| `grep -cE "import\s+pandas\|import\s+numpy"` outputs 0 | ✅ (stdlib-only) |
| `grep -c "SKILL.md.candidate" aggregate_patterns.py` outputs 0 | ✅ (D-13 dry-run — no candidate writes) |
| `grep -c "BooleanOptionalAction"` outputs 0 | ✅ (no way to disable dry-run) |
| `python CLI --threshold 100` emits `"candidates": []` against imported | ✅ |
| `python CLI --threshold 1 total_entries >= 10` | ✅ (12) |
| `pytest tests/phase06/test_aggregate_patterns.py` | ✅ 21/21 PASS |
| `pytest tests/phase06/test_aggregate_dry_run.py` | ✅ 10/10 PASS |
| `grep -cE "^def test_" test_aggregate_patterns.py` ≥13 | ✅ (21) |
| `grep -cE "^def test_" test_aggregate_dry_run.py` ≥7 | ✅ (10) |
| `grep -c "SKILL.md.candidate" test_aggregate_dry_run.py` ≥1 | ✅ (D-13 guard present) |
| Full Phase 6 suite (217 tests) | ✅ 217/217 PASS |
| D-14 imported sha256 byte-identical | ✅ `a1d92cc1...` preserved |
| 06-VALIDATION.md 6-09-01/02 flipped ✅ green | ✅ |

## Deviations from Plan

None — plan executed exactly as written. The FAIL-NNN schema-template entry showing up in threshold=1 output is an intentional boundary clarification (see key-decisions) rather than a deviation: the regex is shared between the iter_entries parser and the documented schema, and Phase 10's promotion step will filter template-like keys.

## Commits

- `a690126` — test(06-09): add failing tests for FAILURES aggregate_patterns CLI (TDD RED)
- `921886e` — feat(06-09): add FAILURES aggregate_patterns dry-run CLI (FAIL-02, D-13)

## Self-Check: PASSED

All artifacts on disk, both commits present, all acceptance criteria met, Phase 6 regression green (217/217), D-13 + D-14 invariants verified.
