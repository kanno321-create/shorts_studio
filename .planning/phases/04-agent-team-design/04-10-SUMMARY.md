---
phase: 04-agent-team-design
plan: 10
subsystem: integration-validation
tags: [harness-audit, gan-separation, logicqa-schema, sc1-reconciliation, phase-capstone]

requires:
  - phase: 04-01
    provides: "rubric-schema.json + agent-template.md + 5 stdlib validators + af_bank + korean_samples"
  - phase: 04-02..07
    provides: "17 Inspector AGENT.md (6 카테고리: structural 3 + content 3 + style 3 + compliance 3 + technical 3 + media 2) with LogicQA 5 sub_qs + RUB-06 GAN separation"
  - phase: 04-08
    provides: "14 Producer AGENT.md (Core 6 + 3단 분리 3 + Support 5) with <prior_vqqa> RUB-03 retry block"
  - phase: 04-09
    provides: "shorts-supervisor AGENT.md with _delegation_depth guard (AGENT-05)"

provides:
  - "scripts/validate/grep_gan_contamination.py — table-aware RUB-06 check (only Inputs section parsed, negation refs in MUST REMEMBER/docs allowed)"
  - "Updated scripts/validate/harness_audit.py — uses smart GAN check (score 100 on clean state, replaces raw regex that caused false positives)"
  - "tests/phase04/test_gan_separation.py — VALIDATION row 4-10-02 gate"
  - "tests/phase04/test_logicqa_schema.py — VALIDATION row 4-10-03 gate (17 inspectors × 5 sub_qs)"
  - "tests/phase04/test_harness_audit_integration.py — VALIDATION row 4-10-01 gate (score ≥ 80 AUDIT-02 baseline)"
  - "tests/phase04/test_total_agent_count.py — 32-agent invariant (17 + 14 + 1, excluding harvest-importer) with 6-category breakdown guard"
  - "04-VALIDATION.md frontmatter flipped: status=complete, nyquist_compliant=true, wave_0_complete=true; all 16 per-task rows ✅"
  - "ROADMAP.md Phase 4 SC1 reconciliation: '12~20 사이' → '총 32명' with D-9 rationale; Progress Table Phase 2/3/4 all ✅ Complete"
  - "REQUIREMENTS.md 34/34 Phase 4 REQs marked complete (100% Phase 4 coverage)"

affects: [phase-05-orchestrator, phase-07-integration-test, phase-10-sustained-operations]

tech-stack:
  added: []
  patterns:
    - "harness_audit pipeline: validate_all_agents (AGENT-07/08/09) + rubric_stdlib_validator (RUB-04) + grep_gan_contamination (RUB-06) → linear score (100 - 10×violations - 5×warnings)"
    - "Smart GAN contamination check: parses only ## Inputs Markdown table rows, not raw text. Allows negation references in documentation (MUST REMEMBER, RUB-06 variant notes, Supervisor fan-out rules). Previous raw regex in harness_audit.py produced 17 false positives; replaced."
    - "LogicQA schema invariant: <sub_qs> block contains exactly q1..q5 tokens (regex-anchored `\\b{qid}\\s*:`). Explicit q6/q7 guard prevents silent drift. Parametrized pytest across all 17 inspectors (34 tests: 17 sub_qs + 17 main_q)."
    - "32-agent count enforced by filesystem invariant (pathlib.rglob), excludes harvest-importer via string match. 6-category breakdown test guards against inspector count drift (structural 3 / content 3 / style 3 / compliance 3 / technical 3 / media 2)."

key-files:
  created:
    - "scripts/validate/grep_gan_contamination.py (85 lines) — table-aware RUB-06 enforcement"
    - "tests/phase04/test_gan_separation.py (24 lines)"
    - "tests/phase04/test_logicqa_schema.py (67 lines, 35 tests)"
    - "tests/phase04/test_harness_audit_integration.py (42 lines)"
    - "tests/phase04/test_total_agent_count.py (62 lines, 5 tests)"
    - ".planning/phases/04-agent-team-design/04-10-SUMMARY.md (this file)"
  modified:
    - "scripts/validate/harness_audit.py — stage 3 RUB-06 check replaced with grep_gan_contamination.check_file (smart table parse)"
    - ".planning/phases/04-agent-team-design/04-VALIDATION.md — frontmatter flipped complete/true/true; 16 rows ✅; Wave 0 checklist [x]; Sign-off [x]"
    - ".planning/ROADMAP.md — Phase 4 SC1 reconciled to '총 32명' with D-9 rationale note; Phase 4 list 10/10 ✅; Progress Table Phase 2/3/4 all Complete; Hard Constraints agent count amended"
    - ".planning/REQUIREMENTS.md — 10 remaining Phase 4 REQs (AGENT-01/02/03/05, RUB-03, CONTENT-03/07, AUDIO-01/02/03) marked [x] with 04-08/09 commit hashes"

key-decisions:
  - "D-10-A: grep_gan_contamination.py parses ONLY the ## Inputs Markdown table section (regex-anchored) — explicitly whitelists MUST REMEMBER / RUB-06 variant notes / Supervisor fan-out documentation references to producer_prompt. Rationale: the original raw-regex in harness_audit.py produced 17 false positives because every inspector legitimately documents the RUB-06 rule ('producer_prompt 읽기 금지'), which is exactly the policy we want reinforced. Distinguishing TABLE FIELD (violation) from DOC MENTION (compliance) is the key insight."
  - "D-10-B: harness_audit.py updated to use grep_gan_contamination.check_file rather than maintaining two separate detectors. Single source of truth for RUB-06 check; harness_audit composes at the pipeline level. Score now 100 on clean state (was -70 with the old raw regex)."
  - "D-10-C: SC1 reconciliation text anchored at the plan-level not globally rewriting history. Original '12~20 사이' from Phase 2 kept as context ('Phase 2 ROADMAP 초기 추정치'), but REQUIREMENTS.md AGENT-01~05 enumeration (14+17+1=32) is declared canonical per D-9 PROJECT.md ('REQUIREMENTS 구체성 > ROADMAP SC 근사값'). This closes RESEARCH.md Open Question 1."
  - "D-10-D: VALIDATION.md flip gated on ALL gates green. If any one of (244/244 pytest, validate_all_agents, harness_audit≥80, grep_gan_contamination) had failed, VALIDATION.md stays at status=draft and Plan 10 would require revisit. All green on first attempt; flip applied."

patterns-established:
  - "Integration-plan scope: Wave 5 capstone plans consolidate STATE.md + ROADMAP.md + REQUIREMENTS.md atomic updates after parallel-Wave executors deliberately deferred them. This prevents merge-conflict churn when Waves 1-4 ran concurrently."
  - "Smart-check-over-raw-regex: When enforcing an architectural rule (RUB-06 GAN separation), differentiate between CODE/CONFIG locations that MUST NOT contain a pattern vs DOC locations that SHOULD reinforce the rule through negation. The parser/AST approach wins over flat grep."
  - "LogicQA schema invariants enforced at fs-level via parametrized pytest, not at runtime. Static compile-time check is strictly stronger than runtime assertion; prevents ever-shipping an inspector with 4 or 6 sub_qs."

requirements-completed: [AGENT-04, AGENT-05, AGENT-07, AGENT-08, AGENT-09, RUB-01, RUB-06]

duration: 14min
completed: 2026-04-19
---

# Phase 4 Plan 10: Wave 5 Integration — 32-Agent Canonical, harness_audit=100, RUB-06 Clean Summary

**Integration gate closed Phase 4 with 32 agents (Producer 14 + Inspector 17 + Supervisor 1), harness_audit score 100, 244/244 pytest PASS, GAN_CLEAN 17/17, and SC1 reconciliation ('12~20 사이' → '총 32명' per D-9 REQUIREMENTS 구체성 > ROADMAP 근사값).**

## Performance

- **Duration:** ~14 min (Task 1 11min / Task 2 2min / Task 3 1min, excluding REQUIREMENTS + SUMMARY)
- **Started:** 2026-04-19T12:00:00Z
- **Completed:** 2026-04-19T12:14:00Z
- **Tasks:** 3 (plus REQUIREMENTS completion + SUMMARY creation)
- **Files modified:** 10 (5 created + 5 modified)

## Accomplishments

- **harness_audit score 100** (threshold 80, AUDIT-02 Phase 10 baseline prep satisfied with 20-point margin)
- **17/17 inspectors clean on RUB-06 GAN separation** (table-aware check; 17 legitimate negation-doc references preserved)
- **17/17 inspectors pass LogicQA schema** (exactly 5 sub_qs, main_q present; parametrized pytest)
- **32-agent invariant holds** (17 Inspector + 14 Producer + 1 Supervisor; 6-category breakdown structural 3 / content 3 / style 3 / compliance 3 / technical 3 / media 2)
- **244/244 full Phase 4 pytest suite PASS** in 0.39s
- **validate_all_agents 32/32 OK** on `--exclude harvest-importer`
- **04-VALIDATION.md frontmatter flipped** (status=complete, nyquist_compliant=true, wave_0_complete=true); all 16 per-task rows + Wave 0 checklist + Sign-off marked ✅
- **ROADMAP.md SC1 reconciliation applied** (Open Question 1 from RESEARCH.md formally resolved)
- **34/34 Phase 4 REQs complete** in REQUIREMENTS.md (100% Phase 4 coverage; cumulative project 47/96 REQs = 49%)

## Task Commits

1. **Task 1: Write GAN contamination check + 4 integration pytest files** — `778745a` (feat)
2. **Task 2: Run full pytest suite + flip VALIDATION.md** — `62c0758` (docs)
3. **Task 3: Update ROADMAP.md Phase 4 SC1 to reconcile 29/32 agent count** — `b35c64b` (docs)
4. **Mark 34/34 Phase 4 REQs complete** — `8452876` (docs)

## Files Created/Modified

### Created
- `scripts/validate/grep_gan_contamination.py` — Smart RUB-06 check parsing ## Inputs Markdown tables only
- `tests/phase04/test_gan_separation.py` — Subprocess wrapper PASS/FAIL gate
- `tests/phase04/test_logicqa_schema.py` — Parametrized inspector schema (17 × 5 = 85 micro-assertions)
- `tests/phase04/test_harness_audit_integration.py` — Score ≥ 80 gate
- `tests/phase04/test_total_agent_count.py` — 32-agent + 6-category breakdown invariants

### Modified
- `scripts/validate/harness_audit.py` — stage 3 now delegates to grep_gan_contamination.check_file (raw regex removed)
- `.planning/phases/04-agent-team-design/04-VALIDATION.md` — status/nyquist/wave_0 flipped, all 16 rows ✅
- `.planning/ROADMAP.md` — Phase 4 SC1 text amended (32 canonical), Phases header Phase 4 box checked, Plans 4/10 → 10/10 ✅ with commit hashes, Progress Table 3 rows ✅ Complete, Hard Constraints agent count "12~20" → "32"
- `.planning/REQUIREMENTS.md` — 10 remaining Phase 4 REQs marked [x] with 04-08/09 commit hashes + rationale

## Decisions Made

See frontmatter `key-decisions` D-10-A through D-10-D. Key insight: **smart-check over raw-regex** — the original `harness_audit.py` stage-3 had a flat `producer_prompt|producer_system_context` grep that produced 17 false positives because every well-documented inspector reinforces the RUB-06 rule through negation. The correct enforcement parses only the `## Inputs` Markdown table section and checks for the token as a **field-name** cell entry, not a documentation mention. This pattern (code-location vs doc-location distinction) generalizes to other compliance gates.

## Deviations from Plan

### Rule 1 — Auto-fixed Bug in Existing harness_audit.py

**1. [Rule 1 - Bug] Raw-regex RUB-06 check in harness_audit.py produced 17 false positives**
- **Found during:** Task 1 verify step
- **Issue:** The existing `scripts/validate/harness_audit.py` stage 3 used `re.compile(r"\b(producer_prompt|producer_system_context)\b")` and reported every inspector as violating RUB-06, because every inspector legitimately documents the rule ("producer_prompt 읽기 금지") in MUST REMEMBER / RUB-06 variant notes. With 17 violations × 10 points = -170 penalty, the audit score was -70 before Task 1.
- **Fix:** Replaced stage 3 with `grep_gan_contamination.check_file(md)` call (new module written for Task 1). This parses only the `## Inputs` Markdown table section and flags forbidden tokens only when they appear as table-row field names. Negation references in documentation remain allowed (and encouraged).
- **Files modified:** `scripts/validate/harness_audit.py`
- **Verification:** `py -3.11 -m scripts.validate.harness_audit --agents-root .claude/agents --exclude harvest-importer` → `HARNESS_AUDIT_SCORE: 100 violations: 0 warnings: 0`
- **Committed in:** `778745a` (bundled with Task 1 since the bug was uncovered while writing grep_gan_contamination.py; fixing harness_audit at the same time avoids a broken intermediate state)

### No other deviations

Tasks 2 and 3 executed exactly as specified in the plan.

## SC1 Reconciliation Note (Open Question 1 — RESOLVED)

Original Phase 2 ROADMAP SC1: *"총 에이전트 수가 12~20 사이다"* (conservative estimate with Producer 11 count).

Phase 4 RESEARCH.md Appendix C and REQUIREMENTS.md AGENT-01~05 enumerate **Producer 14 (Core 6 + 3단 분리 3 + Support 5) + Inspector 17 (6 categories) + Supervisor 1 = 32** total. This is the canonical count.

**Resolution applied by Plan 10:**
- ROADMAP.md Phase 4 SC1 amended to "**총 32명**" with explicit reconciliation note
- Hard Constraints agent count "12~20" → "32" with D-9 rationale
- Phases header Phase 4 box flipped ✅ with studio@62c0758 commit reference
- Progress Table Phase 4 row: 4/10 → 10/10 ✅ Complete / 2026-04-19

**D-9 principle applied:** REQUIREMENTS.md 구체성 (specific enumeration) > ROADMAP SC 근사값 (approximation). When the two conflict, REQUIREMENTS wins because it represents the authoritative spec at plan-authoring time while ROADMAP SC represents best-effort estimation at scaffold time.

## Phase 4 Final Statistics

| Metric | Value |
|-------:|:------|
| Total agents shipped | 32 (17 Inspector + 14 Producer + 1 Supervisor) |
| Total AGENT.md files | 33 (including harvest-importer Phase 3 legacy) |
| Phase 4 plans | 10/10 ✅ Complete |
| Phase 4 REQs satisfied | 34/34 ✅ 100% |
| harness_audit final score | 100 (threshold 80) |
| Full pytest suite | 244/244 PASS in 0.39s |
| GAN_CLEAN inspectors | 17/17 |
| LogicQA schema compliant | 17/17 (5 sub_qs + main_q) |
| validate_all_agents | 32/32 OK |
| Cumulative project REQs | 47/96 (49%) |

## Open Deferrals for Phase 5+

- **NotebookLM 프로그래매틱 API 호출** — deferred to Phase 6 (Wiki + NotebookLM Integration). Current Phase 4 inspector prompts reference `@wiki/shorts/*.md` Fallback Chain assumption; actual API binding awaits Phase 6.
- **Phase 5 orchestrator 실 Inspector invocation** — Plan 10 verified agent FILES exist and satisfy schema; actual runtime `Task(agent_path)` dispatch requires Phase 5 orchestrator (scripts/orchestrator/shorts_pipeline.py 500~800줄 state machine). Phase 4 guarantees agents will be VALID when called; Phase 5 delivers CALLING them.
- **AUDIT-02 monthly harness_audit cron** — ROADMAP.md Phase 10 FAIL-04 / AUDIT-02 territory. Plan 10 established the baseline (score 100); Phase 10 schedules monthly execution + threshold-breach FAILURES append.
- **RUB-03 semantic_feedback runtime loop** — Inspector schema accepts `semantic_feedback: string`; Producer prompts accept `<prior_vqqa>`. End-to-end Producer→Inspector→Producer retry with VQQA feedback injection tested via mock in Phase 7 Integration Test, not in Phase 4.

## Known Stubs

**None.** All 32 AGENT.md files contain complete prompt bodies with real LogicQA blocks, real Inputs/Outputs tables, real MUST REMEMBER clauses. No placeholder text ("TODO", "FIXME", "coming soon") detected. No hardcoded empty arrays/objects flowing to output. This was verified by the full validate_all_agents + harness_audit run.

## Self-Check: PASSED

- [x] `scripts/validate/grep_gan_contamination.py` exists (85 lines)
- [x] `tests/phase04/test_gan_separation.py` exists
- [x] `tests/phase04/test_logicqa_schema.py` exists
- [x] `tests/phase04/test_harness_audit_integration.py` exists
- [x] `tests/phase04/test_total_agent_count.py` exists
- [x] Commit `778745a` (Task 1 feat) visible in `git log`
- [x] Commit `62c0758` (Task 2 VALIDATION flip) visible
- [x] Commit `b35c64b` (Task 3 ROADMAP SC1) visible
- [x] Commit `8452876` (REQUIREMENTS 34/34) visible
- [x] `04-VALIDATION.md` contains `status: complete` + `nyquist_compliant: true` + `wave_0_complete: true`
- [x] `ROADMAP.md` contains `Producer 14` + `Inspector 17` + `총 32명` + `SC1 reconciliation`
- [x] 34/34 Phase 4 REQs marked `[x]` in REQUIREMENTS.md
- [x] harness_audit score 100 on clean run
- [x] 244/244 pytest PASS
