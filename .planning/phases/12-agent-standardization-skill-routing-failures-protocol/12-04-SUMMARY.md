---
phase: 12-agent-standardization-skill-routing-failures-protocol
plan: 04
subsystem: infra
tags: [skill-routing, requirements-drift-rectification, ssot-matrix, reciprocity-verifier, tdd, wave-2]

# Dependency graph
requires:
  - phase: 12-agent-standardization-skill-routing-failures-protocol
    plan: 01
    provides: "5-block AGENT.md schema (trend-collector v1.2 prototype) + tests/phase12/ scaffold + verify_agent_md_schema.py CLI — reciprocity verifier mirror-pattern baseline"
provides:
  - "wiki/agent_skill_matrix.md SSOT — 31 agent × 5 공용 skill + 1 additional column matrix (14 producer + 17 inspector)"
  - "scripts/validate/verify_agent_skill_matrix.py CLI — bidirectional reciprocity check with --fail-on-drift flag"
  - "REQUIREMENTS.md §383 정정 — 8-column → 5 공용 + additional (Option A, D-2 Lock 보존)"
  - "tests/phase12/test_skill_matrix_format.py — 5 tests GREEN (4 pass + 1 Plan02/03-gated skip)"
affects: [Plan 02 producer migration (each producer AGENT.md <skills> must reciprocate matrix row), Plan 03 inspector migration (same reciprocity contract), Phase 13+ CI (pre-commit --fail-on-drift hook surface)]

# Tech tracking
tech-stack:
  added: []  # stdlib-only (argparse, re, pathlib, sys) per D-22 / Phase 10 stdlib-only 원칙
  patterns:
    - "Matrix SSOT → AGENT.md <skills> bidirectional reciprocity: required ↔ required literal, n/a ↔ skill absent"
    - "Lenient row regex tolerates flexible cell spacing (handles matrix authoring variance)"
    - "Race-condition-aware skip gate: enumerate all 31 migration targets, skip if ANY < v1.2 (survives parallel Plan 02/03 partial execution)"
    - "REQUIREMENTS drift rectification via Planner's Discretion (RESEARCH-flagged Open Question + Option A upstream approval)"

key-files:
  created:
    - "wiki/agent_skill_matrix.md"
    - "scripts/validate/verify_agent_skill_matrix.py"
  modified:
    - ".planning/REQUIREMENTS.md (§383 SKILL-ROUTE-01 정정)"
    - "tests/phase12/test_skill_matrix_format.py (red stubs → GREEN assertions)"

key-decisions:
  - "Row count = 31 (14 producer + 17 inspector), NOT plan's stated 30 — Plan 01 SUMMARY key-decisions §1 precedent (disk reality override plan frontmatter). Verifier + matrix + tests all aligned to 31."
  - "REQUIREMENTS §383 Option A 채택 — 8-column 초안을 5 공용 + additional 로 정정. D-2 Lock (2026-04-20 ~ 2026-06-20) 신규 SKILL.md 생성 금지 원칙 보존 (본 정정은 scope 조정이며 Lock 위반 아님). RESEARCH.md §Open Question Q1 인용 완료."
  - "Reciprocity skip-gate race-aware: parallel Plan 02/03 partial migration 상태 (일부 agent만 v1.2) 에서도 skip 으로 안전 처리 — 31개 전수 v1.2 확인 후에만 assertion 실행."

patterns-established:
  - "Pattern 1: SSOT matrix + reciprocity verifier pair — Phase 13+ CI 에서 hook 으로 enforce"
  - "Pattern 2: Planner's Discretion via RESEARCH Open Question Q1 Option A — 계획 drift 를 Plan 실행 중 rectify (REQUIREMENTS.md 직접 수정 권한)"
  - "Pattern 3: Race-aware skip gate for parallel-wave tests — enumerate all migration targets, skip if incomplete"

requirements-completed:
  - SKILL-ROUTE-01

# Metrics
duration: 4min
completed: 2026-04-20
---

# Phase 12 Plan 04: Skill-Matrix SSOT + Reciprocity Verifier Summary

**Agent × Skill SSOT 매트릭스 확보 (31 × 6 grid) + bidirectional reciprocity verifier CLI + REQUIREMENTS §383 drift 정정 (Option A) — SKILL-ROUTE-01 CI enforcement surface 개통.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-04-20T23:04:55Z
- **Completed:** 2026-04-20T23:08:42Z
- **Tasks:** 4 / 4
- **Files created:** 2
- **Files modified:** 2

## Accomplishments

- REQUIREMENTS.md §383 SKILL-ROUTE-01 정정 — "30 × 8 매트릭스" 초안을 "30 × 6 매트릭스 (5 공용 + additional)" 로 수정. notebooklm / korean-naturalness / korean-nat-rules 제거 (실측 부재). D-2 Lock 보존 명시 + RESEARCH §Open Question Q1 Option A 인용.
- `wiki/agent_skill_matrix.md` 신규 SSOT — 31 row × (5 공용 skill + 1 additional) grid. 14 producer + 17 inspector. Cell values ∈ {required, optional, n/a}. 모든 31 agent 가 `gate-dispatcher=required` 준수 (pipeline dispatch baseline invariant). ins-factcheck 의 `additional` 컬럼에 `notebooklm-query*` marker (D-2 Lock 기간 future-ref, Phase 13+ 에서 SKILL 실제 생성 시 drop).
- `scripts/validate/verify_agent_skill_matrix.py` CLI 개통 — stdlib-only (argparse/re/pathlib/sys) + Windows cp949 guard. `parse_matrix()` + `parse_agent_skills_block()` + `verify_reciprocity()`. `--fail-on-drift` 플래그로 exit 1 (CI 용); default exit 0 (dev-tolerant). trend-collector 는 이미 reciprocate (Plan 01 v1.2 prototype 덕분).
- `tests/phase12/test_skill_matrix_format.py` 5 tests — 4 PASS + 1 conditional SKIP (reciprocity, Plan 02+03 완료 대기). test names: `test_matrix_has_30_rows` (실제 31 assertion — 이름은 plan 추적 용도 유지) / `test_matrix_cell_values_legal` / `test_matrix_every_agent_has_required_gate_dispatcher` / `test_common_skills_count_is_5` / `test_matrix_reciprocity_with_agent_md`.

## Task Commits

Each task was committed atomically with `--no-verify` (parallel executor protocol):

1. **Task 1: REQUIREMENTS §383 정정** — `1960263` (docs)
2. **Task 2: wiki/agent_skill_matrix.md SSOT 신규** — `43000b8` (feat)
3. **Task 3: verify_agent_skill_matrix.py CLI** — `bd15bfd` (feat)
4. **Task 4: test_skill_matrix_format.py populate (TDD GREEN)** — `8e74ddd` (test)
5. **Rule 1 auto-fix: race-condition-aware skip gate** — `9211fb2` (fix)

## Files Created/Modified

### Created

- `wiki/agent_skill_matrix.md` — 31 × 6 SSOT grid, reciprocity contract, Phase 12 traceability, change history. 5211 bytes UTF-8.
- `scripts/validate/verify_agent_skill_matrix.py` — 201-line stdlib CLI. Exports: `parse_matrix`, `parse_agent_skills_block`, `verify_reciprocity`, `_agent_md_path`, `COMMON_SKILLS`, `PRODUCERS`, `INSPECTORS` (all importable by tests).

### Modified

- `.planning/REQUIREMENTS.md` — §383 single-line replacement (8-column → 5 공용 + additional, note on D-2 Lock + RESEARCH Q1 Option A)
- `tests/phase12/test_skill_matrix_format.py` — red stubs (3 NotImplementedError) → 5 real assertions with race-aware skip

## Decisions Made

- **Row count = 31 (not 30)** — Plan 04 frontmatter inherited "30 agents" wording, but Plan 01 SUMMARY key-decisions §1 already established disk reality = 14 producer + 17 inspector = 31. Matrix + verifier + tests all aligned to 31. Test name `test_matrix_has_30_rows` retained as plan-traceability marker (docstring clarifies assertion checks 31).
- **REQUIREMENTS §383 direct rewrite** — Option A mandate (RESEARCH Q1) authorized single-line edit in-plan rather than defer to Phase 13. Three key changes: (a) "30 × 8 매트릭스" → "30 × 6 매트릭스 (5 공용 + 1 additional)", (b) 8-skill column list → 5 공용 + additional, (c) "8 column" drift note + D-2 Lock preservation statement + RESEARCH Q1 back-reference.
- **Reciprocity skip-gate race-awareness** — Initial proxy (niche-classifier v1.2 presence) broke when parallel Plan 02 partial-migrated niche-classifier before other producers. Rule 1 auto-fix: enumerate all 31 migration targets, skip if ANY not at v1.2. Survives parallel wave partial execution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's `len(matrix) == 30` vs disk reality = 31**
- **Found during:** Task 4 (writing test assertion)
- **Issue:** Plan 04 Task 4 specified `assert len(matrix) == 30`. Disk has 14 producers + 17 inspectors = 31 (Plan 01 SUMMARY established this). Asserting 30 would regress the Plan 01 correction.
- **Fix:** Asserted `len(matrix) == 31` in test + matrix + verifier all use 31. Test name `test_matrix_has_30_rows` retained for plan traceability, docstring clarifies the actual assertion. Plan Task 2's matrix already listed 14 producers (trend-collector..publisher), so this is consistent with Plan's intent.
- **Files modified:** `tests/phase12/test_skill_matrix_format.py`, `wiki/agent_skill_matrix.md`, `scripts/validate/verify_agent_skill_matrix.py`
- **Committed in:** Tasks 2/3/4 commits (`43000b8`, `bd15bfd`, `8e74ddd`)

**2. [Rule 1 - Bug] Race condition in reciprocity skip-gate (parallel Plan 02 interference)**
- **Found during:** Final verification run of Task 4 tests
- **Issue:** Plan's skip gate checked only `trend-collector` v1.2. Parallel Plan 02 (concurrently executing Wave 2) migrated `niche-classifier` while other producers still at v1.1, tripping the skip-gate into "migration complete" → test failed with 29 drifts. Plan 04 is NOT dependent on Plan 02 (Wave 2 parallel), so reciprocity test must tolerate partial-migration state.
- **Fix:** Skip-gate now enumerates all 31 migration targets (14 producer + 17 inspector) via `_agent_md_path()` + checks `version: 1.2` presence. Skips if ANY target not yet migrated. When all 31 are v1.2 AND drift > 0 → actual failure (legitimate drift).
- **Files modified:** `tests/phase12/test_skill_matrix_format.py`
- **Verification:** `py -3.11 -m pytest tests/phase12/test_skill_matrix_format.py -v` → 4 passed + 1 skipped
- **Committed in:** `9211fb2` (fix)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — plan-vs-reality rectifications). Zero Rule 2/3/4.
**Impact on plan:** Both fixes harden parallel-wave robustness; do not change acceptance semantics.

## Issues Encountered

None — all 4 tasks passed acceptance criteria after the two Rule 1 auto-fixes. Parallel Plan 02 execution (Wave 2 concurrent) was detected and handled via race-aware skip gate.

## Next Phase Readiness

### Ready for Plan 02 executor (concurrent Wave 2)

- `wiki/agent_skill_matrix.md` is now the SSOT Plan 02 must reciprocate. Each producer migration must ensure AGENT.md `<skills>` block contains literals:
  - `gate-dispatcher (required)` (all 14 producers)
  - `progressive-disclosure (optional)` (all 14 producers)
  - `drift-detection (optional)` for: scripter, script-polisher, shot-planner, asset-sourcer (others: skill absent)
  - Other 3 공용 skill: must be ABSENT from `<skills>` block (n/a semantic)
- After Plan 02 + Plan 03 complete: `py -3.11 scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` should exit 0.

### Ready for Plan 03 executor (concurrent Wave 2)

- All 17 inspectors need `<skills>` block with:
  - `gate-dispatcher (required)` (baseline)
  - `drift-detection (optional)` for: ins-factcheck, ins-tone-brand
  - `context-compressor (optional)` for: ins-korean-naturalness
  - Others: absent from block (n/a semantic)
- `ins-factcheck` AGENT.md `<skills>` should reference `notebooklm-query*` in description (SKILL doesn't exist yet — `*` marker is intentional).

### Ready for Phase 13+ CI hook

- `verify_agent_skill_matrix.py --fail-on-drift` is hook-ready. Add to pre-commit or CI pipeline after Plans 02+03 close out drift.

### Flags for downstream planners

- Test name `test_matrix_has_30_rows` should be renamed to `test_matrix_has_31_rows` at a convenient future boundary (not done here to preserve Plan 04 traceability).
- `additional` column is currently only populated for `ins-factcheck` (`notebooklm-query*`). If Phase 13 adds real notebooklm SKILL, drop the `*` marker.

## Regressions Verified

- `py -3.11 -m pytest tests/phase12/test_skill_matrix_format.py -v` → 4 passed + 1 skipped (reciprocity — awaiting Plan 02+03)
- `py -3.11 scripts/validate/verify_agent_skill_matrix.py` → exit 0 (drift-tolerant default)
- `py -3.11 scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` → exit 1 (currently 29 drifts — expected state; Plans 02+03 drive toward 0)
- `grep -c "5 공용 skill" .planning/REQUIREMENTS.md` = 1 ✓
- `grep -c "30 × 8 매트릭스" .planning/REQUIREMENTS.md` = 0 ✓
- `grep -c "30 × 6 매트릭스" .planning/REQUIREMENTS.md` = 1 ✓
- `grep -c "korean-nat-rules" .planning/REQUIREMENTS.md` = 0 ✓
- Note: `tests/phase12/test_failures_rotation.py` has 4 pre-existing failures — Plan 05 scope, out of Plan 04 boundary (deferred).

## Known Stubs

None. All 5 tests are operational (4 assertions + 1 conditional skip). No TODO/FIXME/NotImplementedError remain in Plan 04 files. The reciprocity skip is intentional and documented (awaits sibling Wave 2 plans).

## Self-Check: PASSED

All 4 created/modified files verified on disk:
- FOUND: `wiki/agent_skill_matrix.md` (5211 bytes)
- FOUND: `scripts/validate/verify_agent_skill_matrix.py`
- FOUND: `.planning/REQUIREMENTS.md` (§383 patched, grep verified)
- FOUND: `tests/phase12/test_skill_matrix_format.py`

All 5 task commits verified in git log:
- FOUND: `1960263` (docs 12-04: REQUIREMENTS §383)
- FOUND: `43000b8` (feat 12-04: agent_skill_matrix.md)
- FOUND: `bd15bfd` (feat 12-04: verify_agent_skill_matrix.py)
- FOUND: `8e74ddd` (test 12-04: test_skill_matrix_format.py populate)
- FOUND: `9211fb2` (fix 12-04: race-condition-aware skip gate)

---
*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Plan: 04 (Wave 2 — parallel with 02, 05, 07)*
*Completed: 2026-04-20*
