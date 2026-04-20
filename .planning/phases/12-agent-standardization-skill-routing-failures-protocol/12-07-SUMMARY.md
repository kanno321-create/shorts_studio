---
phase: 12-agent-standardization-skill-routing-failures-protocol
plan: 07
subsystem: orchestrator
tags: [supervisor, compression, claude-cli, agent-std-03, phase11-gap, invoker]

# Dependency graph
requires:
  - phase: 11-pipeline-real-run-activation-script-quality-mode
    provides: "retry-with-nudge wrapper (_invoke_claude_cli) + stdin piping + ClaudeAgentSupervisorInvoker cli_runner test seam (L383-393)"
  - phase: 12-agent-standardization-skill-routing-failures-protocol/01
    provides: "Wave 0 red stubs (tests/phase12/test_supervisor_compress.py + mocks/mock_claude_cli.py + fixtures/ dir)"
provides:
  - "_compress_producer_output(output) private function with 2000-char budget + severity_desc sort + 2-key fallback (decisions/evidence)"
  - "ClaudeAgentSupervisorInvoker.__call__ compression insertion point (1 line) preserving cli_runner + circuit_breaker test seams"
  - "tests/phase12/fixtures/producer_output_gate2_oversized.json (14KB synthetic replay fixture)"
  - "5 pytest tests covering compression ratio, critical preservation, error_codes 전수, raw_response drop, CLI-limit replay"
affects: [phase13-live-smoke-retry, phase12-plan-05-failures-rotation, agent-std-downstream-consumers]

# Tech tracking
tech-stack:
  added: []  # No new libraries — pure Python stdlib (json)
  patterns:
    - "Supervisor prompt compression (summary-only mode) before CLI body serialization"
    - "2-key fallback (decisions OR evidence) for rubric-schema drift resilience"
    - "Issue #3 invariant guard — pytest locks cli_runner kwarg existence"

key-files:
  created:
    - tests/phase12/fixtures/producer_output_gate2_oversized.json
  modified:
    - scripts/orchestrator/invokers.py
    - tests/phase12/test_supervisor_compress.py

key-decisions:
  - "Compression threshold: 2000-char budget on decisions/evidence entries (not a total-size threshold); simpler than dynamic size detection and produces ~27% compression ratio on 14KB fixture."
  - "Compression scope: applied ONLY at ClaudeAgentSupervisorInvoker.__call__ before CLI body serialization — full producer_output remains intact for upstream rubric aggregation, downstream fan-out, logging (per D-A4-02)."
  - "Summary payload shape: {gate, verdict, error_codes[], semantic_feedback_prefix(200), decisions OR evidence, _truncated?}. error_codes 전수 보존 (never truncated)."
  - "2-key fallback for decisions/evidence (RESEARCH Pitfall 4): ins-factcheck and other inspectors emit evidence[] as primary; decisions[] is Supervisor-native. Try decisions first, fall back to evidence."
  - "Guarantee at least 1 kept entry even if it exceeds budget alone — otherwise Supervisor loses all severity context."
  - "Fixture size 14.03KB (target 8-15KB) chosen to reproduce Phase 11 smoke 2차 'ë¡¤프트가 너무 깁니다' gap with comfortable margin; raw → compressed ratio 27% demonstrates >>40% reduction requirement."

patterns-established:
  - "Summary-only Supervisor prompts: Producer outputs flow through _compress_producer_output() before Claude CLI body serialization. Pattern replicable to future multi-gate supervisors."
  - "Invariant guard via pytest: Issue #3 cli_runner kwarg existence locked by test_phase11_smoke_replay_under_cli_limit — regression would surface as TypeError."
  - "2-key fallback compression: when upstream schemas drift (rubric-schema.json decisions vs evidence), compression functions should try multiple canonical keys."

requirements-completed: [AGENT-STD-03]

# Metrics
duration: 4min
completed: 2026-04-21
---

# Phase 12 Plan 07: Supervisor Prompt Compression (AGENT-STD-03) Summary

**_compress_producer_output() with 2000-char budget + severity_desc sort closes Phase 11 smoke 2차 "프롬프트가 너무 깁니다" (rc=1) gap; compressed Supervisor body stays under CLI context limit.**

## Performance

- **Duration:** ~4 min (execution window)
- **Started:** 2026-04-20T23:05:44Z
- **Completed:** 2026-04-20T23:10:09Z
- **Tasks:** 3
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- Synthetic 14KB producer_output fixture reproduces Phase 11 smoke 2차 attempt "프롬프트가 너무 깁니다" surface — 15 decisions (4 critical), 5 evidence entries, 4 error_codes, 2576-char semantic_feedback, 2100-char raw_response.
- `_compress_producer_output()` private function with 2000-char budget, severity_desc→score_asc sort, decisions/evidence 2-key fallback (RESEARCH Pitfall 4), error_codes 전수 보존, `_truncated` meta, `semantic_feedback_prefix` (first 200 chars) retention.
- `ClaudeAgentSupervisorInvoker.__call__` single-line insertion (L400) — 기존 test seam (`cli_runner`) + `circuit_breaker` + retry-with-nudge 경로 무변동.
- 5 pytest tests GREEN (ratio / critical-preservation / error_codes / raw_response-drop / end-to-end CLI-limit replay).
- Regression: Phase 11 (36) + Phase 4 (244) GREEN — Producer invoker 경로 무영향 확인.

## Task Commits

Each task was committed atomically (with --no-verify per parallel-execution orchestrator contract):

1. **Task 1: Oversized fixture** - `126fa63` (test) — tests/phase12/fixtures/producer_output_gate2_oversized.json
2. **Task 2: Compression function + invoker wiring** - `3b06203` (feat) — scripts/orchestrator/invokers.py
3. **Task 3: 5 pytest tests GREEN** - `00e08f5` (test) — tests/phase12/test_supervisor_compress.py

## Files Created/Modified
- `tests/phase12/fixtures/producer_output_gate2_oversized.json` (NEW, 14.03 KB) — Synthetic Phase 11 smoke 2차 replay surface. 15 decisions, 5 evidence, 4 error_codes, verbose prose.
- `scripts/orchestrator/invokers.py` (+113 lines) — `_compress_producer_output()` function + `_COMPRESS_CHAR_BUDGET = 2000` constant + 1-line insertion in `ClaudeAgentSupervisorInvoker.__call__`. No signature changes; Issue #3 `cli_runner` kwarg (L388) preserved.
- `tests/phase12/test_supervisor_compress.py` (+145 / -10 lines) — Replaced 3 red stubs with 5 real tests covering AGENT-STD-03 contract.

## Compression Empirics (fixture replay)

| Field | Raw | Compressed | Delta |
|-------|-----|-----------|-------|
| Total JSON bytes | 8887 | 2373 | -73.3% (ratio 26.7%) |
| decisions[] entries kept | 15 | 9 | 6 truncated (`_truncated` meta added) |
| evidence[] | 5 | 0 (decisions wins 2-key fallback) | — |
| error_codes[] | 4 | 4 | 전수 보존 ✓ |
| raw_response | 2100 chars | absent | dropped ✓ |
| semantic_feedback | 2576 chars | 200-char prefix | 92% reduction |
| first decision severity | rule_000 = critical | rule_000 = critical | severity_desc sort verified ✓ |

CLI-limit replay (Test 5): compressed `user_prompt` = ~2560 chars (compressed 2373 + JSON wrapper `{"gate":"SCRIPT","producer_output":...}`) << 10000-char CLI limit approximation. Phase 11 smoke 2차 "프롬프트가 너무 깁니다" no longer reachable via this path.

## Decisions Made

- **Compression threshold value (2000 chars):** Chose per-entry char budget instead of total-size threshold. Simpler to reason about, produces predictable severity-ordered truncation. RESEARCH §Pattern 3 recommended; empirically gives 27% ratio on 14KB fixture — well under the 60% ceiling required by `test_compression_ratio_over_40pct`.
- **2-key fallback (decisions OR evidence):** Inspector rubric-schema.json (per RESEARCH Pitfall 4) uses `evidence[]` primary while D-A4-01 assumed `decisions[]`. First non-empty list wins; decisions takes precedence when both present (Supervisor-native term).
- **Guarantee ≥1 kept entry:** Added defensive `if not kept and sorted_source: kept.append(sorted_source[0])` even if first entry exceeds budget. Prevents Supervisor receiving zero decisions when a single large critical decision > 2000 chars.
- **Scope boundary preservation:** Compression applied only inside `__call__`, not in factory or `__init__`. Full `output` remains intact for upstream callers (rubric aggregation, downstream fan-out, audit trail) — matches D-A4-02 scope.
- **Fixture agent_dir fallback:** `shorts-supervisor` primary, `ins-schema-integrity` fallback — AGENT.md body content doesn't matter for the test (only `load_agent_system_prompt` must succeed).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Agent directory path correction for Test 5**
- **Found during:** Task 3 (test_phase11_smoke_replay_under_cli_limit)
- **Issue:** Plan text specified `.claude/agents/supervisor/` but the actual supervisor agent lives at `.claude/agents/supervisor/shorts-supervisor/` (subdir). Using the plan-literal path would have caused `load_agent_system_prompt` to raise FileNotFoundError because no AGENT.md exists at the parent dir.
- **Fix:** Test 5 uses `.claude/agents/supervisor/shorts-supervisor/` as primary, `.claude/agents/inspectors/structural/ins-schema-integrity/` as fallback (both verified by `ls` before writing).
- **Files modified:** tests/phase12/test_supervisor_compress.py
- **Verification:** Test 5 passes; MockClaudeCLI.last_user_prompt captured; AGENT.md load succeeded.
- **Committed in:** `00e08f5` (Task 3 commit)

**2. [Rule 2 - Missing Critical] Added ≥1 kept-entry guarantee in _compress_producer_output**
- **Found during:** Task 2 (writing compression function)
- **Issue:** If a single decision's JSON serialization exceeds 2000 chars (pathological but possible), the `char_used + entry_size > _COMPRESS_CHAR_BUDGET` check rejects it on the first iteration, leaving `kept = []` and the Supervisor receiving zero context. This would silently degrade Supervisor verdict quality.
- **Fix:** Added `if not kept and sorted_source: kept.append(sorted_source[0])` fallback after the loop. Guarantees at least the highest-priority entry is always sent to Supervisor.
- **Files modified:** scripts/orchestrator/invokers.py (10 lines in `_compress_producer_output`)
- **Verification:** All 5 phase12 tests pass; no regression in Phase 11 (36) or Phase 4 (244).
- **Committed in:** `3b06203` (Task 2 commit)

**3. [Rule 1 - Deviation] Fixture size calibration**
- **Found during:** Task 1 (fixture generation)
- **Issue:** Plan-literal fixture parameters (22 decisions × 500-char evidence prose, 15 evidence entries, `raw_response * 30`) produced a 35.6 KB file — 2.4× the 8-15 KB target. First tune (18 decisions / 10 evidence) = 16.5 KB, still over. Second tune (15 decisions / 7 evidence) = 15.54 KB, 0.54 KB over. Final tune (15 decisions / 5 evidence, shorter per-decision evidence prose, `raw_response * 25`) = 14.03 KB ✓.
- **Fix:** Calibrated fixture generator parameters within the plan's spec envelope (≥15 decisions, ≥3 error_codes, ≥2500-char semantic_feedback, ≥2000-char raw_response, critical severity present). All acceptance criteria met.
- **Files modified:** tests/phase12/fixtures/producer_output_gate2_oversized.json
- **Verification:** Plan's Task 1 verify command passed: `8 <= size_kb <= 15`, decisions ≥ 15, error_codes ≥ 3, critical in decisions.
- **Committed in:** `126fa63` (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 bug, 1 missing critical, 1 calibration)
**Impact on plan:** All auto-fixes stayed within the plan's spec envelope. No scope creep — all three were bounded by acceptance criteria in the plan text. The `≥1 kept entry` guarantee strengthens the compression contract beyond what the plan required (defense-in-depth for pathological payloads).

## Issues Encountered

- **Phase 12 red stubs in `test_failures_rotation.py`:** 3 failures (`test_rotate_idempotent`, `test_imported_file_sha256_unchanged`, `test_archive_month_tag`) due to missing `scripts.audit.failures_rotate` module. **Not in 12-07 scope** — these are Plan 12-05's red stubs awaiting implementation by the parallel executor. Per SCOPE BOUNDARY rule (only auto-fix issues DIRECTLY caused by current task's changes), these are deferred to Plan 12-05 and require no action here.

## User Setup Required

None — pure-Python changes, no external services, no env var additions, no schema migrations.

## Next Phase Readiness

- **Phase 11 Gap #1 structurally closed:** The Supervisor-side "프롬프트가 너무 깁니다" (rc=1) failure path is no longer reachable for typical Producer outputs up to ~14KB. Phase 13 live smoke retry path is open.
- **Phase 11 SC#1 (live smoke completion) pre-condition met** structurally (actual smoke rerun deferred to Phase 13 per CONTEXT.md D-A4-03).
- **Issue #3 invariant locked:** `cli_runner: Callable | None = None` kwarg at L388 is now guarded by `test_phase11_smoke_replay_under_cli_limit` — any future signature change removing the kwarg will cause TypeError at test time.
- **Parallel executor awareness:** Plans 12-02, 12-04, 12-05 are running concurrently. This plan's commits (`126fa63`, `3b06203`, `00e08f5`) touch only `scripts/orchestrator/invokers.py`, `tests/phase12/fixtures/`, and `tests/phase12/test_supervisor_compress.py` — no overlap with those plans' file scopes.

## Self-Check: PASSED

**Files verified (exist):**
- tests/phase12/fixtures/producer_output_gate2_oversized.json ✓
- scripts/orchestrator/invokers.py (modified) ✓
- tests/phase12/test_supervisor_compress.py (modified) ✓

**Commits verified (in git log):**
- 126fa63 (Task 1 fixture) ✓
- 3b06203 (Task 2 compression function + invoker) ✓
- 00e08f5 (Task 3 tests GREEN) ✓

**Tests verified GREEN:**
- tests/phase12/test_supervisor_compress.py: 5/5 passed ✓
- tests/phase11/: 36/36 passed (no regression) ✓
- tests/phase04/: 244/244 passed (no regression) ✓

**Contract invariants verified:**
- `grep -c "_compress_producer_output" scripts/orchestrator/invokers.py` = 3 (≥3 required) ✓
- `grep -c "_COMPRESS_CHAR_BUDGET = 2000" scripts/orchestrator/invokers.py` = 1 ✓
- `grep -c "cli_runner: Callable" scripts/orchestrator/invokers.py` = 2 (≥1 required, Issue #3 invariant) ✓

---
*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Plan: 07*
*Completed: 2026-04-21*
