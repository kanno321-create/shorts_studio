---
phase: 12-agent-standardization-skill-routing-failures-protocol
plan: 01
subsystem: infra
tags: [agent-md, schema-verifier, pytest-scaffold, tdd, mock-cli, template-round-trip, wave-0]

# Dependency graph
requires:
  - phase: 11-orchestrator-production-wiring-deferred
    provides: "F-D2-EXCEPTION-01 JSON-only output discipline + invokers.py 4-kwargs call signature (L406-412) — MockClaudeCLI contract baseline"
  - phase: 04-agent-team-design
    provides: "30 AGENT.md baseline (14 producer + 17 inspector + 1 supervisor + 1 harvest-importer) — migration targets"
provides:
  - "5-block AGENT.md schema templates (producer + inspector) — Plan 02/03 clone base"
  - "tests/phase12/ scaffold + 16 red stubs + MockClaudeCLI defensive seam — Plan 02~07 populate path"
  - "verify_agent_md_schema.py CLI — AGENT-STD-01 regression gate"
  - "trend-collector AGENT.md v1.2 — first migration prototype proving template round-trip"
  - "12-VALIDATION.md wave_0_complete flip + 19-row Per-Task Verification Map"
affects: [Plan 02 producer migration, Plan 03 inspector migration, Plan 04 skill-matrix reciprocity, Plan 05 FAILURES rotation, Plan 06 mandatory_reads prose, Plan 07 supervisor compression]

# Tech tracking
tech-stack:
  added: []  # stdlib-only (argparse, re, pathlib, sys) per D-22 + Phase 10 stdlib-only 원칙
  patterns:
    - "5-XML-block AGENT.md schema: role → mandatory_reads → output_format → skills → constraints (DOTALL regex order lock)"
    - "MockClaudeCLI defensive *args/**kwargs — survives real _invoke_claude_cli signature drift"
    - "Template round-trip validation: first migration (trend-collector) proves template before batch migration"
    - "Verifier CLI exclusion list — harvest-importer + shorts-supervisor explicitly scoped out"

key-files:
  created:
    - ".planning/phases/12-.../templates/producer.md.template"
    - ".planning/phases/12-.../templates/inspector.md.template"
    - "tests/phase12/__init__.py"
    - "tests/phase12/conftest.py"
    - "tests/phase12/mocks/__init__.py"
    - "tests/phase12/mocks/mock_claude_cli.py"
    - "tests/phase12/fixtures/.gitkeep"
    - "tests/phase12/test_agent_md_schema.py"
    - "tests/phase12/test_mandatory_reads_prose.py"
    - "tests/phase12/test_skill_matrix_format.py"
    - "tests/phase12/test_failures_rotation.py"
    - "tests/phase12/test_f_d2_exception_batch.py"
    - "tests/phase12/test_supervisor_compress.py"
    - "scripts/validate/verify_agent_md_schema.py"
  modified:
    - ".claude/agents/producers/trend-collector/AGENT.md (v1.1 → v1.2 promotion)"
    - ".planning/phases/12-.../12-VALIDATION.md (frontmatter flip + 19-row test map)"

key-decisions:
  - "Verifier CLI scope = 14 producers + 17 inspectors = 31 agents (NOT plan's stated 30) — harvest-importer lives at .claude/agents/harvest-importer/ root-level dir, already outside producers/ scan path; shorts-supervisor explicit exclusion"
  - "MockClaudeCLI adopts *args/**kwargs defensive pattern to absorb real signature drift (6-arg real function vs 4-kwarg real call site)"
  - "trend-collector <mandatory_reads> item 2 path corrected v1.1 → v1.2: wiki/ypp/channel_bible.md → wiki/continuity_bible/channel_identity.md (RESEARCH.md §Q3 canonical) — drift rectification on first migration"

patterns-established:
  - "Pattern 1: 5-XML-block AGENT.md schema (D-A1-01) enforced via DOTALL regex in single CI tool"
  - "Pattern 2: TDD template round-trip — create template, build verifier, promote first real agent, confirm regression 0 — then scale to batch (Plan 02/03)"
  - "Pattern 3: MockClaudeCLI defensive signature absorbs future real-fn drift without test edits"

requirements-completed:
  - AGENT-STD-01
  - AGENT-STD-02

# Metrics
duration: 16min
completed: 2026-04-21
---

# Phase 12 Plan 01: Wave 0 Foundation Summary

**2 AGENT.md templates + tests/phase12/ scaffold + verify_agent_md_schema.py CLI + trend-collector v1.2 prototype migration — 5-block schema infrastructure for 30-agent Phase 12 standardization.**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-04-20T22:43:18Z
- **Completed:** 2026-04-20T22:59:03Z
- **Tasks:** 5 / 5
- **Files created:** 14
- **Files modified:** 2

## Accomplishments

- Producer + Inspector AGENT.md templates with 5-XML-block fixed-order schema (D-A1-01) including "샘플링 금지" Korean literal (AGENT-STD-02) and RUB-06 GAN separation mirroring (producer forbids inspector_prompt reading; inspector forbids producer_prompt reading)
- tests/phase12/ scaffold with 16 red-stub tests across 6 test files, all `@pytest.mark.skip` decorated so collection exits 0 while awaiting Plan 02~07 populate
- MockClaudeCLI with defensive `*args/**kwargs` signature absorbing real `_invoke_claude_cli` 6-arg real function vs `ClaudeAgentSupervisorInvoker._call` 4-kwarg call site — Plan 07 injection seam ready
- verify_agent_md_schema.py CLI — `--all` scans 14 producers + 17 inspectors (31 files) excluding harvest-importer and shorts-supervisor, Windows cp949 guard, per-file missing/misordered stderr report
- trend-collector AGENT.md v1.1 → v1.2 promotion: frontmatter version bump + 3 new XML blocks (role, skills, constraints) + channel_bible path drift rectification + body prose preserved byte-for-byte
- 12-VALIDATION.md frontmatter flipped `nyquist_compliant: true` + `wave_0_complete: true` + Per-Task Verification Map populated with 19 concrete test-case rows (15 test cases + 4 summary rows)

## Task Commits

Each task was committed atomically:

1. **Task 1: Producer + Inspector templates** — `e9fd3a3` (feat)
2. **Task 2: tests/phase12/ scaffold + MockClaudeCLI** — `6aac44b` (test)
3. **Task 3: verify_agent_md_schema.py CLI** — `a06dc9b` (feat)
4. **Task 4: trend-collector v1.1 → v1.2 migration** — `0ebb5e9` (feat; TDD — RED auto-verified by Task 3 CLI, GREEN commit is single code change)
5. **Task 5: 12-VALIDATION.md flip + test map populate** — `9a8db78` (docs)

## Files Created/Modified

### Created

- `.planning/phases/12-.../templates/producer.md.template` — 5-block schema baseline for 14 producer migrations (Plan 02)
- `.planning/phases/12-.../templates/inspector.md.template` — 5-block schema baseline for 17 inspector migrations (Plan 03)
- `tests/phase12/__init__.py` — Phase 4~11 convention
- `tests/phase12/conftest.py` — `tmp_failures_file` fixture (31-line head) + `synthetic_producer_output_small` (5 decisions × 2 error_codes)
- `tests/phase12/mocks/__init__.py` — empty namespace marker
- `tests/phase12/mocks/mock_claude_cli.py` — MockClaudeCLI defensive `*args/**kwargs` class
- `tests/phase12/fixtures/.gitkeep` — parent dir for Plan 07 Task 1 synthetic JSON
- `tests/phase12/test_agent_md_schema.py` — 2 red stubs (AGENT-STD-01)
- `tests/phase12/test_mandatory_reads_prose.py` — 2 red stubs (AGENT-STD-02)
- `tests/phase12/test_skill_matrix_format.py` — 3 red stubs (SKILL-ROUTE-01)
- `tests/phase12/test_failures_rotation.py` — 4 red stubs (FAIL-PROTO-01)
- `tests/phase12/test_f_d2_exception_batch.py` — 2 red stubs (FAIL-PROTO-02)
- `tests/phase12/test_supervisor_compress.py` — 3 red stubs (AGENT-STD-03)
- `scripts/validate/verify_agent_md_schema.py` — 5-block DOTALL regex verifier CLI

### Modified

- `.claude/agents/producers/trend-collector/AGENT.md` — v1.1 → v1.2 (version bump + 3 new XML blocks inserted + channel_bible path corrected; body Purpose/Inputs/Outputs/Prompt/References/MUST REMEMBER preserved byte-for-byte)
- `.planning/phases/12-.../12-VALIDATION.md` — frontmatter flip + 19-row test map + 15/15 Wave 0 checklist

## Decisions Made

- **Verifier scope = 31 AGENT.md (NOT 30)** — plan frontmatter stated 13 producer + 17 inspector = 30, but `.claude/agents/producers/` contains 14 real producer directories (harvest-importer lives separately at `.claude/agents/harvest-importer/AGENT.md` root-level, already outside the scan path). CLAUDE.md canonical count confirms Producer 14 + Inspector 17. Verifier CLI honors the actual disk layout; exclusion list only excises harvest-importer (defensive guard if future refactor moves it into producers/) and shorts-supervisor (Phase 12 scope out).
- **MockClaudeCLI defensive signature** — real `_invoke_claude_cli` is 6-arg positional-friendly (`system_prompt, user_prompt, json_schema, cli_path, timeout_s=..., agent_label=...`) but `ClaudeAgentSupervisorInvoker._call` only passes 4 kwargs. Using `*args, **kwargs` with explicit kwargs-first extraction absorbs both call styles and is resilient to future real-fn signature additions without test-side edits.
- **trend-collector <mandatory_reads> item 2 path corrected** — v1.1 referenced `wiki/ypp/channel_bible.md` (which does not exist); v1.2 points to `wiki/continuity_bible/channel_identity.md` (the canonical 5-component channel identity file from Phase 6 Plan 02). First migration was the right time to correct this drift before 13 more producers inherit it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Verifier expected 30 agents, disk has 31**
- **Found during:** Task 3 (verify_agent_md_schema.py --all sanity check)
- **Issue:** Plan 01 frontmatter stated "13 producer + 17 inspector = 30" but `.claude/agents/producers/` has 14 real producer directories. The plan's mental model assumed harvest-importer lived inside `producers/` (it does not — it lives at `.claude/agents/harvest-importer/` root-level, outside the scan target).
- **Fix:** Verifier uses disk reality (31 AGENT.md in scope after default exclusions). Acceptance criterion "≥ 29 violations before Task 4" still holds (31 ≥ 29). After Task 4: 30/31 violations (trend-collector passes). Documented in the key-decisions frontmatter of this SUMMARY; Plan 02/03 batch test `test_all_30_agents_have_5_blocks` will need to reconcile to 31 (rename or adjust assertion — flagged for Plan 02 executor).
- **Files modified:** `scripts/validate/verify_agent_md_schema.py` (no change — logic was correct; plan's 30 count was the drift)
- **Verification:** `py -3.11 scripts/validate/verify_agent_md_schema.py --all` exit 1 with `FAIL: 30/31 AGENT.md violate 5-block schema` after Task 4 (trend-collector passes, 30 remain for Plan 02/03)
- **Committed in:** `a06dc9b` (Task 3 CLI) — no fix commit needed, only doc reconciliation
- **Blast radius:** Plan 02 test_all_30_agents_have_5_blocks test name may need to be `test_all_31_agents_have_5_blocks`; Plan 02 executor should honor disk count.

**2. [Rule 1 - Bug] trend-collector v1.1 referenced non-existent channel bible path**
- **Found during:** Task 4 (trend-collector migration, reading v1.1 mandatory_reads block)
- **Issue:** v1.1 `<mandatory_reads>` item 2 said `wiki/ypp/channel_bible.md` which does not exist on disk. The canonical channel bible file is `wiki/continuity_bible/channel_identity.md` (Phase 6 Plan 02 D-10 5-component baseline).
- **Fix:** Changed path in v1.2 to `wiki/continuity_bible/channel_identity.md` + added niche-specific bible as dynamic inline reference (`.preserved/harvested/theme_bible_raw/<niche_tag>.md`). Template matches.
- **Files modified:** `.claude/agents/producers/trend-collector/AGENT.md`, `.planning/phases/12-.../templates/producer.md.template` (template already had correct path — no fix needed)
- **Verification:** `grep -c "wiki/continuity_bible/channel_identity.md" .claude/agents/producers/trend-collector/AGENT.md` = 1
- **Committed in:** `0ebb5e9` (Task 4 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs). Zero Rule 2/3/4 activations.
**Impact on plan:** Both auto-fixes are data-reality rectifications, not scope creep. Plan 02 executor must reconcile test name `test_all_30_agents_have_5_blocks` → `test_all_31_agents_have_5_blocks` or accept dynamic count.

## Issues Encountered

None — all 5 tasks executed exactly per plan, verification commands exit codes matched expectations (with documented 30/31 vs 30 disk-count reconciliation).

## Next Phase Readiness

### Ready for Plan 02 (Producer 14 migration)

- `.planning/phases/12-.../templates/producer.md.template` proven via trend-collector round-trip
- `verify_agent_md_schema.py` operational — each Plan 02 wave can run `--all` to track GREEN progression (currently 30 violations → target 17 after Plan 02 completes all 14 producers including already-done trend-collector)
- `tests/phase12/test_agent_md_schema.py` stubs ready to populate — uncomment `@pytest.mark.skip` and add real assertions

### Ready for Plan 03 (Inspector 17 migration)

- `.planning/phases/12-.../templates/inspector.md.template` ready (schema symmetry with producer, RUB-06 mirror in `<constraints>`)
- Same verifier CLI + test stubs applicable

### Ready for Plan 07 (Supervisor compression)

- `tests/phase12/mocks/mock_claude_cli.py::MockClaudeCLI` seam proven — defensive signature absorbs real 4-kwarg call path
- `tests/phase12/conftest.py::synthetic_producer_output_small` fixture primes a minimal baseline (5 decisions × 2 error_codes) below the 2000-char compression budget; Plan 07 Task 1 will add `producer_output_gate2_oversized.json` in `tests/phase12/fixtures/` for the over-budget replay

### Flags for downstream planners

- Plan 02 must reconcile `test_all_30_agents_have_5_blocks` name (disk has 31 in scope). Rename or parametrize.
- Plan 06 `<mandatory_reads>` prose validator should grep the literal `매 호출마다 전수 읽기, 샘플링 금지` — both templates carry it, trend-collector v1.2 inherits it.

## Regressions Verified

- `py -3.11 -m pytest tests/phase04/ -q` → 244 passed (Phase 4 baseline intact)
- `py -3.11 -m pytest tests/phase11/ -q` → 36 passed (Phase 11 baseline intact)
- `py -3.11 -m pytest tests/phase12/ -q` → 16 skipped, 0 failed (Wave 0 red stubs honored)
- `py -3.11 scripts/validate/verify_agent_md_schema.py .claude/agents/producers/trend-collector/AGENT.md` → exit 0
- `py -3.11 scripts/validate/verify_agent_md_schema.py --all` → exit 1 (30/31 violations — expected state; Plan 02/03 will drive this toward 0)

## Known Stubs

All 6 test files contain `@pytest.mark.skip(reason="Wave 0 red stub — populated by Plan NN")` decorators by design — this is the Wave 0 infrastructure pattern. Intentional:

- `tests/phase12/test_agent_md_schema.py` — 2 stubs for Plan 02/03
- `tests/phase12/test_mandatory_reads_prose.py` — 2 stubs for Plan 06
- `tests/phase12/test_skill_matrix_format.py` — 3 stubs for Plan 04
- `tests/phase12/test_failures_rotation.py` — 4 stubs for Plan 05
- `tests/phase12/test_f_d2_exception_batch.py` — 2 stubs for Plan 02
- `tests/phase12/test_supervisor_compress.py` — 3 stubs for Plan 07

Each plan's executor removes the skip decorator and fills in `raise NotImplementedError` → real assertions. No intentional stub carries into production; all are test-scaffolding.

## Self-Check: PASSED

All 17 claimed files verified present on disk (14 created + 2 modified + 1 SUMMARY).
All 5 task commits verified present in git log: `e9fd3a3`, `6aac44b`, `a06dc9b`, `0ebb5e9`, `9a8db78`.

---
*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Completed: 2026-04-21*
