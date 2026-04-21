---
phase: 12-agent-standardization-skill-routing-failures-protocol
plan: 02
subsystem: agent-standardization
tags: [agent-md, 5-block-schema, producer-migration, v1-2-promotion, rub-06-mirror, f-d2-exception-02, wave-2]

# Dependency graph
requires:
  - phase: 12-agent-standardization-skill-routing-failures-protocol
    plan: 01
    provides: "producer.md.template + verify_agent_md_schema.py CLI + trend-collector v1.2 prototype + tests/phase12/test_agent_md_schema.py red stubs"
  - phase: 11-orchestrator-production-wiring-deferred
    provides: "F-D2-EXCEPTION-01 JSON-only output discipline (trend-collector) — the single-file prototype this plan scales to 13 producers"
provides:
  - "13 Producer AGENT.md v1.2 — 5-block XML schema (role → mandatory_reads → output_format → skills → constraints) with Korean literal '매 호출마다 전수 읽기, 샘플링 금지' + RUB-06 GAN-separation mirror + JSON output_format + 5 forbidden-pattern examples"
  - "tests/phase12/test_agent_md_schema.py populated — 16 tests GREEN (2 collective + 14 parametrized per v1.2 producer, trend-collector + 13 new)"
  - "F-D2-EXCEPTION-02 Wave 2 batch entry in .claude/failures/FAILURES.md — single directive-authorized batch record for 7 commits / 13 files (AUDIT-05 idempotency style, supplements F-D2-EXCEPTION-01 prototype pattern)"
  - "Phase 4 RUB-05 maxTurns matrix restored — scripter/asset-sourcer/publisher regressions auto-fixed, 244 passed"
affects: [Plan 12-03 inspector 17 migration (same template + verifier), Plan 12-04 skill-matrix reciprocity (now resolvable — 14/14 producer rows reciprocate matrix), Plan 12-06 mandatory-reads prose (13 more targets ready), Phase 13+ live smoke retry (JSON-only output discipline 13-Producer-wide structural guarantee)]

# Tech tracking
tech-stack:
  added: []  # No new dependencies — pure content migration + test populate
  patterns:
    - "5-XML-block AGENT.md schema at scale — 13 producer batch migration honors Plan 01 template round-trip"
    - "marker-filtered git log query: --grep='[plan-02]' replaces fragile -n rev-count (Issue #5 convention)"
    - "Phase 4 regression gate as migration guard — maxTurns matrix auto-fix via Rule 1 before finalize commit"
    - "F-D2-EXCEPTION-02 as single batch entry vs 13 individual F-D2-NN — D-2 Lock idempotency architecture respected"

key-files:
  created:
    - ".planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-02-SUMMARY.md"
  modified:
    - ".claude/agents/producers/niche-classifier/AGENT.md (v1.2, Core 2/5)"
    - ".claude/agents/producers/researcher/AGENT.md (v1.2, Core 3/5; maxTurns 5→3 fix)"
    - ".claude/agents/producers/director/AGENT.md (v1.2, Core 4/5)"
    - ".claude/agents/producers/scripter/AGENT.md (v1.2, Core 5/5; maxTurns 5→3 fix)"
    - ".claude/agents/producers/metadata-seo/AGENT.md (v1.2, Core 5/5)"
    - ".claude/agents/producers/scene-planner/AGENT.md (v1.2, Support 1/7)"
    - ".claude/agents/producers/shot-planner/AGENT.md (v1.2, Support 2/7)"
    - ".claude/agents/producers/script-polisher/AGENT.md (v1.2, Support 3/7)"
    - ".claude/agents/producers/voice-producer/AGENT.md (v1.2, Support 4/7)"
    - ".claude/agents/producers/asset-sourcer/AGENT.md (v1.2, Support 5/7; maxTurns 5→3 fix)"
    - ".claude/agents/producers/thumbnail-designer/AGENT.md (v1.2, Support 6/7)"
    - ".claude/agents/producers/assembler/AGENT.md (v1.2, Support 7/7)"
    - ".claude/agents/producers/publisher/AGENT.md (v1.2, Support 7/7; maxTurns 2→3 fix)"
    - "tests/phase12/test_agent_md_schema.py (red stubs → 16 real assertions: 2 collective + 14 parametrized)"
    - ".claude/failures/FAILURES.md (+18 lines, F-D2-EXCEPTION-02 Wave 2 batch entry, append-only)"
    - "reports/skill_patch_count_2026-04.md (refreshed; 4 → 5 violations; AGENT.md patches correctly excluded from regex)"

key-decisions:
  - "Plan 02 Task 8 (skill_patch_counter.append_f_d2_exception_02 function + test_f_d2_exception_batch.py populate) intentionally deferred — HANDOFF narrowed scope to pure append in FAILURES.md + counter refresh. Reason: Plan 02's F-D2-EXCEPTION-02 record is semantically a single directive-authorized batch, not per-commit violations; skill_patch_counter's existing 4-regex forbidden paths do not capture AGENT.md patches (correct architectural split — AGENT roles vs SKILL learning). Residual 2 red stubs in test_f_d2_exception_batch.py deferred to future Plan 12-03 or Phase 13 counter extension."
  - "maxTurns Phase 4 regression auto-fix (Rule 1): scripter 5→3, asset-sourcer 5→3, publisher 2→3, researcher 5→3 — Plan 02's original migration set these per the plan text's <constraints> customization, but Phase 4 test_maxturns_matrix.py mandates all producers = 3 (only 5 inspectors allowed non-default). Rule 1 auto-fix restored 244 pytest phase04 GREEN. Documented as finalize commit 2d1aa23."
  - "niche-classifier cosmetic +1 blank line: not reverted — harmless whitespace addition from prior parallel execution, included in finalize commit for hygiene."
  - "Wave 2 parallel interrupt recovery: 6 migration commits (93a285b..172f623) landed pre-interrupt; finalize commit 2d1aa23 closes out the 15% gap (uncommitted diffs + test populate + Phase 4 fix) as a single logical unit."

patterns-established:
  - "Pattern 1: Wave batch migration + finalize-commit Rule-1 regression-gate auto-fix — scales Plan 01 single-file migration prototype to 13-file batch without sacrificing Phase 4 green"
  - "Pattern 2: Marker-filtered commit query ([plan-02]) — robust to per-task commit granularity drift and parallel-execution interrupt"
  - "Pattern 3: F-D2-EXCEPTION-NN batch entries as single directive-authorized records — respects FAIL-PROTO-02 idempotency (one batch ≠ N individual entries)"

requirements-completed:
  - AGENT-STD-01
  - AGENT-STD-02
  - FAIL-PROTO-02

# Metrics
duration: ~6h wallclock (8:09 → 15:03 KST, includes parallel-wave interrupt + resume); effective execution ~35min (6 migration commits @ ~5min each + finalize 5min)
completed: 2026-04-21
---

# Phase 12 Plan 02: Producer 13-Agent v1.2 Migration Summary

**13 Producer AGENT.md (niche-classifier through publisher) promoted to 5-block v1.2 schema — JSON output_format + RUB-06 GAN-separation mirror + 'sample 금지' literal + Phase 4 maxTurns matrix preserved; 16 Phase 12 schema tests GREEN; F-D2-EXCEPTION-02 single batch entry records the 7-commit/13-file directive-authorized patch.**

## Performance

- **Duration:** ~6h wallclock (2026-04-21T08:09:19+09:00 → 2026-04-21T15:02:57+09:00, includes Wave 2 parallel interrupt gap); effective execution ~35 min
- **Started:** 2026-04-21T08:09:19+09:00 (first commit `93a285b`)
- **Completed:** 2026-04-21T15:02:57+09:00 (finalize commit `2d1aa23`)
- **Tasks:** 7 / 8 (Task 8 skill_patch_counter extension + test_f_d2_exception_batch populate intentionally deferred — see key-decisions)
- **Files modified:** 14 (13 producer AGENT.md + 1 test) + 1 FAILURES append + 1 report refresh + 1 SUMMARY new

## Accomplishments

- 13 Producer AGENT.md (niche-classifier, researcher, director, scripter, metadata-seo, scene-planner, shot-planner, script-polisher, voice-producer, asset-sourcer, thumbnail-designer, assembler, publisher) all at `version: 1.2` with 5-block XML schema; body prose (Purpose / Inputs / Outputs / Prompt / References / MUST REMEMBER) preserved per D-A1-01
- All 13 carry the Korean literal `매 호출마다 전수 읽기, 샘플링 금지` in `<mandatory_reads>` (D-A1-03 / AGENT-STD-02) — verified by parametrized pytest `test_producer_has_version_1_2_and_rub_06` across all 14 v1.2 producers (trend-collector + 13 new)
- All 13 carry `inspector_prompt 읽기 금지 (RUB-06 GAN 분리 mirror)` in `<constraints>` — forbids producers from reading inspector system prompts (GAN collapse prevention)
- All 13 carry `<output_format>` JSON schema + 5 forbidden-pattern examples (대화체 / 질문 / 옵션 / 서문 / 꼬리) — structural re-occurrence barrier for F-D2-EXCEPTION-01 (trend-collector Phase 11 smoke 1차 failure)
- Agent-specific customization honored per PLAN Tasks 1-6 customize lists — e.g., publisher AF-8 Selenium forbidden + containsSyntheticMedia hardcoded, asset-sourcer Anchor Frame forced (D-13 I2V-only), scripter drift-detection optional, researcher NotebookLM fallback chain mandatory
- Phase 4 RUB-05 maxTurns matrix preserved — 3 Rule 1 auto-fixes (scripter 5→3, asset-sourcer 5→3, publisher 2→3) in finalize commit after discovering migration drift; 244 tests GREEN
- F-D2-EXCEPTION-02 Wave 2 batch entry appended to `.claude/failures/FAILURES.md` (73 lines total, under 500 cap per FAIL-PROTO-01) — single directive-authorized record for 7 commits / 13 files / 대표님 세션 #29 authorization
- `tests/phase12/test_agent_md_schema.py` fully populated — 16 tests GREEN (2 collective + 14 parametrized); Plan 01 red stubs removed

## Task Commits

Tasks 1-7 each committed atomically per the Plan's Issue #5 convention — all subjects carry `[plan-02]` marker for robust `git log --grep='\[plan-02\]'` traceability:

1. **Task 1: niche-classifier v1.2** — `93a285b` (feat) — 2026-04-21T08:09:19
2. **Task 2: researcher v1.2** — `9ed8f31` (feat) — 2026-04-21T08:21:24
3. **Task 3: director + scripter + metadata-seo v1.2** — `2089449` (feat) — 2026-04-21T08:26:39
4. **Task 4: scene-planner + shot-planner + script-polisher v1.2** — `1226750` (feat) — 2026-04-21T08:30:49
5. **Task 5: voice-producer + asset-sourcer + thumbnail-designer v1.2** — `22b13bb` (feat) — 2026-04-21T08:44:06
6. **Task 6: assembler + publisher v1.2** — `172f623` (feat) — 2026-04-21T08:47:26
7. **Tasks 1/2/7 finalize + Phase 4 regression auto-fix** — `2d1aa23` (feat) — 2026-04-21T15:02:57

**Plan metadata:** [this SUMMARY + STATE + ROADMAP + REQUIREMENTS + FAILURES + report refresh, final docs commit to follow]

All 7 commits carry `[plan-02]` marker → marker-filtered query `git log --grep='\[plan-02\]' --name-only --pretty=format: | grep -c AGENT.md` = 13 (exactly matches scope).

## Files Created/Modified

### Created
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-02-SUMMARY.md` — this file

### Modified (Producer AGENT.md v1.2 promotions)
- `.claude/agents/producers/niche-classifier/AGENT.md` — 5-block + GATE 2 NICHE dispatch + CONTENT-03 bible mapping
- `.claude/agents/producers/researcher/AGENT.md` — 5-block + NotebookLM fallback chain (WIKI-04) 3-tier + maxTurns 5→3 (Phase 4 fix)
- `.claude/agents/producers/director/AGENT.md` — 5-block + Blueprint hook/act1/act2/climax/resolution/CTA schema
- `.claude/agents/producers/scripter/AGENT.md` — 5-block + drift-detection optional + duo dialogue + maxTurns 5→3 (Phase 4 fix)
- `.claude/agents/producers/metadata-seo/AGENT.md` — 5-block + YouTube ranking_factors reference + title ≤60 chars constraint
- `.claude/agents/producers/scene-planner/AGENT.md` — 5-block + scene[duration/setting/action/emotion] schema
- `.claude/agents/producers/shot-planner/AGENT.md` — 5-block + I2V-only (D-13) + i2v_hint-only constraint (t2v_hint 0 grep)
- `.claude/agents/producers/script-polisher/AGENT.md` — 5-block + QUALITY_PATTERNS.md reference + polish pass
- `.claude/agents/producers/voice-producer/AGENT.md` — 5-block + Typecast primary / ElevenLabs fallback stack
- `.claude/agents/producers/asset-sourcer/AGENT.md` — 5-block + Kling 2.6 primary + Anchor Frame forced + maxTurns 5→3 (Phase 4 fix)
- `.claude/agents/producers/thumbnail-designer/AGENT.md` — 5-block + text ≤20 chars constraint + ins-thumbnail-hook dependency
- `.claude/agents/producers/assembler/AGENT.md` — 5-block + Shotstack API + VoiceFirstTimeline (ORCH-10) + duration ≤60s
- `.claude/agents/producers/publisher/AGENT.md` — 5-block + YouTube Data API v3 + AF-8 Selenium forbidden + containsSyntheticMedia + 48h+ AF-1 + maxTurns 2→3 (Phase 4 fix)

### Modified (test + protocol)
- `tests/phase12/test_agent_md_schema.py` — red stubs removed, `_collect_all_agent_mds()` + `verify_file()` imported; 16 tests GREEN (2 collective + 14 parametrized over PRODUCERS_V1_2 list)
- `.claude/failures/FAILURES.md` — F-D2-EXCEPTION-02 Wave 2 batch entry appended (+18 lines, total 73 lines, under 500 cap)
- `reports/skill_patch_count_2026-04.md` — counter refreshed; 4 → 5 violations (added Plan 12-05 hook edit `60e1bea`); AGENT.md patches correctly excluded from the 4-regex forbidden paths (SKILL ≠ AGENT separation preserved)

## Decisions Made

- **Task 8 scope narrowing: no `append_f_d2_exception_02` function** — HANDOFF explicitly narrowed the last-mile to pure FAILURES append + counter refresh. The F-D2-EXCEPTION-02 Wave 2 batch is semantically a single directive-authorized record of Phase 12's 30+ file patch plan; `skill_patch_counter.py`'s 4-regex forbidden paths (`.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md`) correctly exclude AGENT.md — AGENT role definitions ≠ SKILL learning. Consequently: `test_f_d2_exception_batch.py` 2 red stubs remain deferred (Plan 12-03 or Phase 13 owns if the batch-append pattern becomes a repeated need). FAILURES.md append is direct via Edit tool through the D-11 append-only hook (73 lines, well under 500-line FAIL-PROTO-01 cap).
- **maxTurns Phase 4 regression auto-fix (Rule 1)** — Plan 02's Task 3/5/6 action text specified scripter/asset-sourcer=5 and publisher=2 as per-agent customization, but Phase 4 `test_maxturns_matrix.py::EXPECTED_NON_DEFAULT` mandates only 5 inspectors hold non-default values; ALL producers = 3. The migration introduced a 7-test Phase 4 regression. Rule 1 auto-fix: 4 producers (scripter/asset-sourcer/publisher + researcher staged pre-resume) frontmatter + description + `<constraints>` prose synchronized to maxTurns=3. Phase 4 restored to 244 GREEN (from 237/7 failed). Rationale: Phase 4 RUB-05 matrix predates Plan 02 and is the canonical source; Plan 02's customization exceeded the matrix envelope. Documented as commit `2d1aa23`.
- **Wave 2 parallel interrupt handling** — 6 migration commits landed pre-interrupt (93a285b..172f623, 8:09-8:47 KST) while 3 files sat uncommitted (niche-classifier blank-line, researcher maxTurns 5→3 edit, test_agent_md_schema.py populate). Resume in session #29 treated these as legitimate Plan 02 Task 1/2/7 artifacts per HANDOFF disk-truth, folded maxTurns regression fix into the same finalize commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] scripter maxTurns=5 violates Phase 4 RUB-05 matrix**
- **Found during:** Finalize gate (regression test phase04 before finalize commit)
- **Issue:** Plan 02 Task 3 action text for scripter specified `maxTurns=5` in `<constraints>` + `maxTurns: 5` frontmatter. Phase 4 `test_maxturns_matrix.py::EXPECTED_NON_DEFAULT` mandates producers = default (3); only 5 inspectors may hold non-default. 3 Phase 4 tests failed at scripter, plus aggregate `test_non_default_maxturns_count` + `test_scripter_frontmatter_is_producer_core_maxturns_3` + `test_frontmatter_role_producer_category_core_maxturns_3`.
- **Fix:** Changed frontmatter `maxTurns: 5 → 3`, description `maxTurns 5 → maxTurns 3 (Phase 4 regression 호환)`, `<constraints>` line from "maxTurns=5 준수" to "maxTurns=3 준수 (RUB-05, Phase 4 regression 호환) — 3턴 내 완성. 초과 임박 시 partial + maxTurns_exceeded 플래그, Supervisor circuit_breaker 라우팅."
- **Files modified:** `.claude/agents/producers/scripter/AGENT.md`
- **Verification:** `py -3.11 -m pytest tests/phase04/ -q` → 244 passed (from 237/7 failed)
- **Committed in:** `2d1aa23` (finalize commit)

**2. [Rule 1 - Bug] asset-sourcer maxTurns=5 violates Phase 4 matrix**
- **Found during:** Finalize gate (same regression run as #1)
- **Issue:** Plan 02 Task 5 action text for asset-sourcer specified maxTurns=5. Same Phase 4 matrix violation as scripter.
- **Fix:** Synchronized frontmatter / description / `<constraints>` to maxTurns=3 (Phase 4 regression 호환); Kling 2.6 rate-limit constraint preserved.
- **Files modified:** `.claude/agents/producers/asset-sourcer/AGENT.md`
- **Verification:** Phase 4 `test_maxturns_value_matches_matrix[asset-sourcer]` PASS
- **Committed in:** `2d1aa23`

**3. [Rule 1 - Bug] publisher maxTurns=2 violates Phase 4 matrix**
- **Found during:** Finalize gate
- **Issue:** Plan 02 Task 6 action text for publisher specified maxTurns=2 (justifying "업로드 계획 생성은 단순"). Phase 4 matrix permits producers=3 only (never 2). 3 Phase 4 tests failed.
- **Fix:** Synchronized frontmatter 2→3, description `maxTurns=2 → maxTurns=3 (Phase 4 regression 호환)`, `<constraints>` prose updated (재시도는 invoker 책임 semantics preserved).
- **Files modified:** `.claude/agents/producers/publisher/AGENT.md`
- **Verification:** Phase 4 `test_maxturns_value_matches_matrix[publisher]` PASS
- **Committed in:** `2d1aa23`

**4. [Rule 1 - Bug] researcher maxTurns=5 violates Phase 4 matrix**
- **Found during:** Pre-resume staged diff inspection (discovered already fixed in working tree)
- **Issue:** Plan 02 Task 2 original migration set researcher `maxTurns: 5` per the plan action text (NotebookLM fallback 3-tier consideration). Working-tree diff had already rolled back to `maxTurns: 3` matching the description field's canonical spec. Rule 1 auto-fix was already in progress pre-interrupt — no additional change needed beyond committing.
- **Fix:** Folded into finalize commit. Description text already updated to `maxTurns 3 (Phase 4 regression 호환)`.
- **Files modified:** `.claude/agents/producers/researcher/AGENT.md`
- **Verification:** Phase 4 `test_maxturns_value_matches_matrix[researcher]` PASS
- **Committed in:** `2d1aa23`

---

**Total deviations:** 4 auto-fixed (all Rule 1 — Phase 4 regression rectifications). Zero Rule 2/3/4 activations. All 4 fixes were bounded by the Phase 4 RUB-05 maxTurns matrix (pre-existing, canonical). Plan's per-agent customization text (Tasks 2/3/5/6) was the drift; Phase 4 matrix is the authority.
**Impact on plan:** Zero scope creep. The 4 auto-fixes restore pre-existing Phase 4 RUB-05 invariant (all producers maxTurns=3). No new behavior introduced.

## Issues Encountered

- **Wave 2 parallel interrupt** (initial execution session, 2026-04-21 morning KST) — 6 migration commits landed cleanly, then Plan 02 was interrupted leaving 3 uncommitted files in the working tree (niche-classifier cosmetic, researcher maxTurns fix, test populate). HANDOFF document (`12-02-HANDOFF.md`) authored at interrupt-time captured disk truth. Resume (session #29) re-read HANDOFF, confirmed the 3 diffs were legitimate (not divergent), ran Phase 4 regression, discovered additional scripter/asset-sourcer/publisher maxTurns violations, auto-fixed all 4, and committed everything as `2d1aa23`. Zero data loss.
- **Task 8 (skill_patch_counter extension) deferred** — HANDOFF narrowed last-mile scope to pure FAILURES append + counter refresh. Deferred because AGENT.md patches fall outside the counter's 4-regex forbidden paths (correct SKILL ≠ AGENT architectural split); the batch-append pattern has only 1 batch so far (this one), so the generic `append_f_d2_exception_02` function has no second consumer yet. If Plan 12-03 inspector batch (17 files) creates second-instance need, the function can be added then as part of that plan's scope.

## User Setup Required

None — pure content migration + test populate + append-only FAILURES entry. No external services, no env vars, no schema migrations.

## Next Phase Readiness

### Ready for Plan 12-03 (Inspector 17 migration)
- Same `inspector.md.template` from Plan 01 ready to clone
- Same `verify_agent_md_schema.py` CLI will track GREEN progression (currently 14/31 PASS → target 31/31 after Plan 12-03)
- Same `test_all_scoped_agents_have_5_blocks` test will expand to cover 17 inspectors automatically
- Phase 4 maxTurns matrix: 5 inspectors already hold non-default values (ins-factcheck=10, ins-tone-brand=5, ins-blueprint-compliance=1, ins-timing-consistency=1, ins-schema-integrity=1) — Plan 12-03 must preserve these during migration

### Ready for Plan 12-04 (skill-matrix reciprocity — already complete, awaiting Plan 03)
- All 14 v1.2 producers reciprocate the `wiki/agent_skill_matrix.md` SSOT per Plan 12-04's contract (gate-dispatcher=required + progressive-disclosure=optional; scripter/script-polisher/shot-planner/asset-sourcer also drift-detection=optional)
- Plan 12-04's `verify_agent_skill_matrix.py --fail-on-drift` currently skips (race-aware) until all 31 agents at v1.2 — Plan 12-03 completion unblocks full reciprocity verification

### Ready for Plan 12-06 (mandatory_reads prose enforcement)
- 13 more producer targets with populated `<mandatory_reads>` + `매 호출마다 전수 읽기, 샘플링 금지` literal — Plan 12-06's prose validator grep will find 14 ≥ 1 matches (trend-collector + 13 new)

### Flags for downstream planners
- **test_f_d2_exception_batch.py 2 red stubs still present** — if Plan 12-03's inspector batch generates a second F-D2-EXCEPTION-NN record, the generic `append_f_d2_exception_02` function should be added to `skill_patch_counter.py` at that point and these 2 stubs populated as reusable-function tests.
- **Phase 4 maxTurns matrix is authoritative** — future producer AGENT.md customization must consult `tests/phase04/test_maxturns_matrix.py::EXPECTED_NON_DEFAULT` first. Per-agent prose justifications for non-3 values must be accompanied by matrix-entry additions (Plan change).
- **F-D2-EXCEPTION-02 Wave 2 marker** appended; Plan 12-03 inspector batch should use `F-D2-EXCEPTION-02 — Wave 3` (or renumber as `F-D2-EXCEPTION-03`) to avoid ambiguity.

## Regressions Verified

- `py -3.11 -m pytest tests/phase04/ -q` → **244 passed** (restored from 237/7-failed intermediate state after maxTurns auto-fix)
- `py -3.11 -m pytest tests/phase11/ -q` → **36 passed** (unchanged from baseline)
- `py -3.11 -m pytest tests/phase12/ -q` → **30 passed + 5 skipped** (test_f_d2_exception_batch.py 2 intentional red stubs — Task 8 deferral; Plan 12-05's test_failures_rotation.py 3 were already GREEN — wait-flag shows 5 skipped includes reciprocity race-aware skips in test_skill_matrix_format.py Plan 12-04)
- `py -3.11 scripts/validate/verify_agent_md_schema.py --all` → **14/31 PASS** (14 producer PASS + 17 inspector FAIL — expected state pre-Plan-12-03)
- `py -3.11 -m pytest tests/phase12/test_agent_md_schema.py -v` → **16 passed** (2 collective + 14 parametrized per producer)
- `grep -c "F-D2-EXCEPTION-02" .claude/failures/FAILURES.md` → 3 (once in header, twice in body references — all legitimate)
- `wc -l .claude/failures/FAILURES.md` → 73 lines (well under 500 FAIL-PROTO-01 cap)
- `git log --grep='\[plan-02\]' --oneline | wc -l` → **7** (≥6 required per Plan's Issue #5 convention — Tasks 1-7 marker attached)
- `git log --grep='\[plan-02\]' --name-only --pretty=format: | grep -c "AGENT.md"` → **13** (≥12 required — exactly matches 13 producer scope)

## Known Stubs

- `tests/phase12/test_f_d2_exception_batch.py` — 2 red stubs remain (`test_batch_commit_single_entry`, `test_batch_idempotent_replay`). Documented deferral in key-decisions. Not blocking — FAIL-PROTO-02 record is live in `.claude/failures/FAILURES.md` via direct append; idempotency currently manual (marker text `F-D2-EXCEPTION-02 — Wave 2` can be grep-detected by future replay). Plan 12-03 or Phase 13+ owns the generic-function populate if second batch instance arises.

## Self-Check: PASSED

**Files verified on disk:**
- FOUND: `.claude/agents/producers/niche-classifier/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/researcher/AGENT.md` (v1.2, maxTurns=3)
- FOUND: `.claude/agents/producers/director/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/scripter/AGENT.md` (v1.2, maxTurns=3)
- FOUND: `.claude/agents/producers/metadata-seo/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/scene-planner/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/shot-planner/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/script-polisher/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/voice-producer/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/asset-sourcer/AGENT.md` (v1.2, maxTurns=3)
- FOUND: `.claude/agents/producers/thumbnail-designer/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/assembler/AGENT.md` (v1.2)
- FOUND: `.claude/agents/producers/publisher/AGENT.md` (v1.2, maxTurns=3)
- FOUND: `tests/phase12/test_agent_md_schema.py` (16 tests GREEN)
- FOUND: `.claude/failures/FAILURES.md` (73 lines, F-D2-EXCEPTION-02 Wave 2 entry)
- FOUND: `reports/skill_patch_count_2026-04.md` (refreshed)

**Commits verified in git log:**
- FOUND: `93a285b` (Task 1 niche-classifier)
- FOUND: `9ed8f31` (Task 2 researcher)
- FOUND: `2089449` (Task 3 director+scripter+metadata-seo)
- FOUND: `1226750` (Task 4 scene-planner+shot-planner+script-polisher)
- FOUND: `22b13bb` (Task 5 voice-producer+asset-sourcer+thumbnail-designer)
- FOUND: `172f623` (Task 6 assembler+publisher)
- FOUND: `2d1aa23` (Tasks 1/2/7 finalize + Phase 4 regression auto-fix)

**Tests verified GREEN:**
- tests/phase04/ → 244 passed ✓
- tests/phase11/ → 36 passed ✓
- tests/phase12/test_agent_md_schema.py → 16 passed ✓

---
*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Plan: 02 (Wave 2 — parallel-interrupt recovery, session #29 finalize)*
*Completed: 2026-04-21*
