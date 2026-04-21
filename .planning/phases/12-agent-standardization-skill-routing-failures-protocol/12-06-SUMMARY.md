---
phase: 12-agent-standardization-skill-routing-failures-protocol
plan: 06
subsystem: agent-standardization
tags: [agent-md, mandatory-reads, prose-validator, pytest, agent-std-02, wave-4, ci-surface, negative-fixtures]

# Dependency graph
requires:
  - phase: 12-agent-standardization-skill-routing-failures-protocol
    plan: 01
    provides: "verify_agent_md_schema.py `_collect_all_agent_mds` + `EXCLUDED_AGENTS` scope SSOT; tests/phase12/test_mandatory_reads_prose.py red stubs (2 skipped)"
  - phase: 12-agent-standardization-skill-routing-failures-protocol
    plan: 02
    provides: "14 Producer AGENT.md v1.2 — all with 4 prose elements present (scan target)"
  - phase: 12-agent-standardization-skill-routing-failures-protocol
    plan: 03
    provides: "17 Inspector AGENT.md v1.1 — all with 4 prose elements present (scan target)"
provides:
  - "scripts/validate/verify_mandatory_reads_prose.py — AGENT-STD-02 CI surface (4-element prose check + skill-path on-disk drift guard)"
  - "tests/phase12/test_mandatory_reads_prose.py — 41 real assertions (replaces 2 skipped red stubs) covering positive 31-agent scan + negative fixtures + CLI entrypoint + Korean encoding smoke"
  - "4 negative fixtures under tests/phase12/fixtures/ — prove validator detects each failure mode (missing literal / wrong channel path / no block / orphan skill)"
  - "AGENT-STD-02 requirement close-out — was already [x] since Plan 01 SUMMARY; this Plan delivers the CI surface that substantiates the checkmark"
affects: [Phase 12 verifier gate (AGENT-STD-02 SC GREEN), Phase 13 hard-enforcement candidate (pre-commit hook invocation of verify_mandatory_reads_prose), future AGENT.md author contract (drift in mandatory_reads auto-caught)]

# Tech tracking
tech-stack:
  added: []  # stdlib-only (argparse, re, pathlib, sys) — Phase 12 D-22 stdlib-only budget honored
  patterns:
    - "CI validator reuses Plan 01 scope (`_collect_all_agent_mds` + `EXCLUDED_AGENTS`) — single SSOT for 31-agent Phase 12 scope"
    - "Strict-vs-conservative regex split — channel_identity path + Korean literal strict; FAILURES.md + skill path conservative (allows paraphrase) per Plan 06 HANDOFF"
    - "Drift guard via on-disk SKILL.md existence check — catches AGENT.md → `.claude/skills/` path drift without duplicating Plan 04 reciprocity verifier logic"
    - "Negative-fixture discipline — 4 bad AGENT.md under tests/phase12/fixtures/ prove each REQUIRED_LITERALS key rejects when absent (positive suite can pass with a silently-broken validator)"
    - "Windows cp949 guard stack — `sys.stdout.reconfigure(encoding='utf-8')` at CLI entry + `open(..., encoding='utf-8')` at verify_file + explicit UTF-8 round-trip smoke test"

key-files:
  created:
    - "scripts/validate/verify_mandatory_reads_prose.py — 178 lines, stdlib-only CLI with --all and --agent modes"
    - "tests/phase12/fixtures/bad_agent_missing_sampling_literal.md — element 4 negative fixture"
    - "tests/phase12/fixtures/bad_agent_missing_channel_bible.md — element 2 negative fixture (legacy path)"
    - "tests/phase12/fixtures/bad_agent_missing_block.md — block-absent negative fixture"
    - "tests/phase12/fixtures/bad_agent_orphan_skill.md — on-disk drift negative fixture"
    - ".planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-06-SUMMARY.md"
  modified:
    - "tests/phase12/test_mandatory_reads_prose.py — 14 lines (2 skipped stubs) → 202 lines (41 real assertions); zero skips remain"

key-decisions:
  - "Strict channel_bible literal — `wiki/continuity_bible/channel_identity.md` only. Plan 01 SUMMARY deviation #2 already rectified the `wiki/ypp/channel_bible.md` legacy drift on trend-collector v1.2; Plan 02/03 propagated the canonical path to all 31 agents. Validator locks this forward — any future revert to the legacy path fails CI."
  - "Strict Korean literal `샘플링 금지` (대표님 session #29) — no romanization / paraphrase / translation tolerated. Variants ('표본 금지', 'sampling prohibited', etc.) reject. UTF-8 enforced at both CLI stream reconfiguration and per-file read."
  - "Skill-path drift guard scope — verify declared `.claude/skills/<name>/SKILL.md` path exists on disk, no bidirectional matrix cross-ref (Plan 04 owns that). Keeps Plan 06 validator single-responsibility: block content + file-existence only."
  - "Negative-fixture suite mandatory — 4 bad AGENT.md fixtures added because a positive-only suite cannot distinguish 'validator correctly scans 31 agents and finds nothing' from 'validator is silently broken and finds nothing'. Each REQUIRED_LITERALS key + block-absent path has one negative fixture asserting ok=False with correct missing-sentinel."

patterns-established:
  - "Pattern 4 (extends Plan 01 Pattern 1): Dual-layer AGENT.md compliance — schema structure (AGENT-STD-01, Plan 01) + prose content (AGENT-STD-02, Plan 06). Future AGENT.md authors must pass both verifiers."
  - "Pattern 5: Negative fixtures co-located with test file — `tests/phase12/fixtures/bad_agent_*.md` beside test module. Reusable by future validators that extend prose checks (Phase 13 candidate)."

requirements-completed:
  - AGENT-STD-02

# Metrics
duration: 12min
completed: 2026-04-21
---

# Phase 12 Plan 06: AGENT-STD-02 mandatory_reads Prose Validator Summary

**`verify_mandatory_reads_prose.py` CLI + 41 pytest assertions (replacing 2 skipped red stubs) validate that all 31 in-scope AGENT.md `<mandatory_reads>` blocks contain 4 prose elements (FAILURES.md ref, canonical channel_identity path, SKILL.md path cross-verified on disk, '샘플링 금지' Korean literal) — AGENT-STD-02 CI surface closure.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-04-21T15:46:00Z (approx — commit sequence baseline)
- **Completed:** 2026-04-21T15:58:00Z
- **Tasks:** 2 / 2
- **Files created:** 6 (1 validator + 4 negative fixtures + 1 SUMMARY)
- **Files modified:** 1 (test_mandatory_reads_prose.py)

## Accomplishments

- `scripts/validate/verify_mandatory_reads_prose.py` — 178-line stdlib-only CLI with `--all` (scans 31 in-scope AGENT.md) and `--agent <path>` (single file) modes. Checks 4 required prose elements + cross-verifies declared `.claude/skills/<name>/SKILL.md` paths exist on disk (drift guard). Reuses `_collect_all_agent_mds` + `EXCLUDED_AGENTS` from Plan 01 so scope stays single-source.
- `tests/phase12/test_mandatory_reads_prose.py` — 41 real assertions replacing 2 skipped red stubs. Coverage: validator contract lock, scope guard, collective sampling-literal scan, collective 3-item scan, 31 parametrized per-agent checks, UTF-8 round-trip smoke, 4 negative-fixture rejection proofs, CLI entrypoint exit 0.
- 4 negative fixtures under `tests/phase12/fixtures/` — one per failure mode (missing Korean literal, legacy channel path, absent block, orphan skill). Each asserts `verify_file(bad).ok is False` with the specific missing-sentinel name, closing the "silently broken validator" blind spot.
- Windows cp949 encoding hardening — CLI stream reconfiguration + per-file `encoding='utf-8'` + explicit smoke test reading trend-collector AGENT.md and asserting `'샘플링 금지' in text`.
- Disk-truth GREEN state at Plan 06 exit: `verify_mandatory_reads_prose.py --all` exit 0 (31/31 pass); `pytest tests/phase12/test_mandatory_reads_prose.py` 41 passed, 0 skipped, 0 failed.
- Regression clean: Phase 4 (244 passed), Phase 11 (36 passed), Phase 12 full (93 passed + 2 Plan 07 stubs skipped).

## Task Commits

1. **Task 1: verify_mandatory_reads_prose.py CLI** — `d1b2b99` (feat)
2. **Task 2: test_mandatory_reads_prose.py 41 assertions + 4 fixtures** — `40edbb0` (test, TDD GREEN; Task 1 validator was already GREEN at commit so RED→GREEN cycle collapsed into a single test-landing commit)

## Files Created/Modified

### Created

- `scripts/validate/verify_mandatory_reads_prose.py` — CLI validator with 4 required literal keys (`failures_md`, `channel_bible`, `skill_path`, `sampling_forbidden`) + `MANDATORY_READS_BLOCK_RE` + `_check_skill_paths_exist` drift guard + Windows cp949 guard
- `tests/phase12/fixtures/bad_agent_missing_sampling_literal.md` — element 4 missing (uses `샘플링<SPLIT>금지` to dodge any accidental substring match)
- `tests/phase12/fixtures/bad_agent_missing_channel_bible.md` — uses legacy `wiki/ypp/channel_bible.md` path, omits canonical `wiki/continuity_bible/channel_identity.md`
- `tests/phase12/fixtures/bad_agent_missing_block.md` — no `<mandatory_reads>` block at all
- `tests/phase12/fixtures/bad_agent_orphan_skill.md` — declares `.claude/skills/nonexistent-skill-xyz/SKILL.md` which does not exist on disk

### Modified

- `tests/phase12/test_mandatory_reads_prose.py` — Plan 01 red stubs (2 × `@pytest.mark.skip`) removed; 41 assertions added across 10 test functions

## Decisions Made

- **Strict channel_identity literal** — Plan 01 SUMMARY deviation #2 rectified trend-collector's `wiki/ypp/channel_bible.md` drift to `wiki/continuity_bible/channel_identity.md`. Plan 02/03 propagated the canonical path to all 31 agents (Phase 6 Plan 02 D-10 SSOT). Validator locks the canonical literal forward — any future revert fails CI. Rationale: `channel_bible` was the old name, `channel_identity` is the current SSOT; accepting both would let the drift regress.
- **Strict Korean literal (no paraphrase)** — 대표님 session #29 specified the exact phrase `매 호출마다 전수 읽기, 샘플링 금지`. Validator greps the sub-phrase `샘플링 금지` (shorter, still specific enough) with UTF-8 forced. Rationale: any translation/romanization/variant weakens the invocation contract.
- **Conservative regex for FAILURES.md + skill path** — Allows varying phrasing across 31 files (some use bullet, some use inline, some with additional context). Strict path literal match is sufficient to prove the reference is present; prose style is an authoring freedom the validator does not police.
- **Skill-path drift guard scope** — On-disk existence check only; no bidirectional cross-reference with `wiki/agent_skill_matrix.md` (Plan 04 owns that). Keeps Plan 06 validator single-responsibility: block content + file existence. A missing `.claude/skills/<name>/SKILL.md` directory while declared in AGENT.md is caught here; a matrix cell contradicting AGENT.md declarations is caught in Plan 04.
- **Negative-fixture mandate** — 4 bad AGENT.md fixtures (`tests/phase12/fixtures/bad_agent_*.md`) prove each REQUIRED_LITERALS key + the block-absent sentinel actually rejects when violated. Without these, a positive-only suite cannot distinguish "validator works" from "validator is silently broken and finds nothing". Each negative test asserts both `ok is False` and the specific missing-sentinel in the returned list.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] First negative fixture self-negated (channel_bible)**

- **Found during:** Task 2 first pytest run
- **Issue:** `bad_agent_missing_channel_bible.md` had the canonical path `wiki/continuity_bible/channel_identity.md` in a NOTE explanation, causing the fixture to accidentally pass the validator (element 2 was actually present). Test expected `ok=False`; actual `ok=True`.
- **Fix:** Rewrote the NOTE to describe the canonical path abstractly (`canonical channel-identity 경로 (wiki/ SSOT path)`) without emitting the literal string anywhere in the fixture. Re-ran — all 41 tests GREEN.
- **Files modified:** `tests/phase12/fixtures/bad_agent_missing_channel_bible.md`
- **Verification:** `grep -c "wiki/continuity_bible/channel_identity.md" tests/phase12/fixtures/bad_agent_missing_channel_bible.md` → 0
- **Committed in:** `40edbb0` (rolled into the same Task 2 commit — single round of fix before commit)
- **Blast radius:** Self-contained to the fixture; no scope change.

### Rule 2/3/4 activations

None — plan executed essentially as written. The validator content plan proposed 4 keys with slightly different literal/regex specs (plan suggested `channel_identity.md|channel_bible` as regex-or; HANDOFF's user-notes section tightened this to strict `wiki/continuity_bible/channel_identity.md` only, which I adopted). No architectural decision needed.

## Plan-vs-Implementation Nuances

The plan body's example code used `channel_identity.md|channel_bible` as a tolerant regex — the HANDOFF's `<notes>` section later tightened this to a strict literal (`wiki/continuity_bible/channel_identity.md` only). I followed the HANDOFF (stricter) because:

1. Disk reality post-Plan 02/03: all 31 agents use the canonical path (verified via dry-run before writing validator).
2. Strict lock prevents Plan 01 deviation #2 drift from regressing.
3. The plan's tolerant regex was pre-Plan 02/03 compatibility hedging that is no longer needed.

The HANDOFF also requested `--agent <path>` flag name (singular) vs the plan's positional `path` argument style. I implemented `--agent <path>` per HANDOFF (matches the success criteria bullet explicitly).

## Regressions Verified

- `py -3.11 scripts/validate/verify_mandatory_reads_prose.py --all` → `OK: 31/31 AGENT.md pass AGENT-STD-02 prose check` (exit 0)
- `py -3.11 scripts/validate/verify_mandatory_reads_prose.py --agent .claude/agents/producers/trend-collector/AGENT.md` → `OK: 1/1 ...` (exit 0)
- `py -3.11 -m pytest tests/phase12/test_mandatory_reads_prose.py -v` → 41 passed, 0 skipped, 0 failed
- `py -3.11 -m pytest tests/phase12/ -q` → 93 passed, 2 skipped (Plan 07 supervisor_compress remaining stubs — not in Plan 06 scope)
- `py -3.11 -m pytest tests/phase04/ -q` → 244 passed (Phase 4 reciprocity regression clean)
- `py -3.11 -m pytest tests/phase11/ -q` → 36 passed (Phase 11 orchestrator regression clean)
- `py -3.11 scripts/validate/verify_agent_md_schema.py --all` → `OK: 31/31 AGENT.md comply with 5-block schema` (Plan 01 gate clean)

## Known Stubs

None from Plan 06. `tests/phase12/test_mandatory_reads_prose.py` now has 0 skips. The 2 remaining Phase 12 skips are in `test_supervisor_compress.py` — owned by Plan 07 (out of Plan 06 scope, intentional).

## Authentication Gates

None encountered.

## Self-Check: PASSED

All claimed files verified on disk:
- `scripts/validate/verify_mandatory_reads_prose.py` — present
- `tests/phase12/fixtures/bad_agent_missing_sampling_literal.md` — present
- `tests/phase12/fixtures/bad_agent_missing_channel_bible.md` — present
- `tests/phase12/fixtures/bad_agent_missing_block.md` — present
- `tests/phase12/fixtures/bad_agent_orphan_skill.md` — present
- `tests/phase12/test_mandatory_reads_prose.py` — present (202 lines, 0 skips)

All claimed commits verified in `git log`:
- `d1b2b99` — Task 1 validator CLI
- `40edbb0` — Task 2 tests + fixtures

REQUIREMENTS.md AGENT-STD-02 already `[x]` (marked by Plan 01 SUMMARY close-out for schema-level block presence); Plan 06 delivers the CI surface that substantiates the checkmark with prose-content validation.

---
*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Completed: 2026-04-21*
