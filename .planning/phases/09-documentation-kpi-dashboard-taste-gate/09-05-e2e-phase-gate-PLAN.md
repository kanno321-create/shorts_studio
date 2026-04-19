---
plan: 09-05
phase: 9
wave: 3
depends_on: [09-00, 09-01, 09-02, 09-03, 09-04]
files_modified:
  - tests/phase09/test_e2e_synthetic_dry_run.py
  - tests/phase09/phase09_acceptance.py
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md
  - .planning/ROADMAP.md
  - .planning/STATE.md
files_read_first:
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md
  - .planning/phases/08-remote-publishing-production-metadata/08-TRACEABILITY.md
  - tests/phase09/test_e2e_synthetic_dry_run.py
  - tests/phase09/phase09_acceptance.py
  - tests/phase09/conftest.py
  - scripts/taste_gate/record_feedback.py
  - docs/ARCHITECTURE.md
  - wiki/kpi/kpi_log.md
  - wiki/kpi/taste_gate_protocol.md
  - wiki/kpi/taste_gate_2026-04.md
autonomous: true
requirements: [KPI-05, KPI-06]
tasks_addressed: [9-05-01, 9-05-02, 9-05-03]
success_criteria: [SC#4, PHASE_GATE]
estimated_commits: 4
parallel_boundary: sequential — depends on all prior Waves (needs ARCHITECTURE.md + kpi_log.md + taste_gate_*.md + record_feedback.py to exist)

must_haves:
  truths:
    - "tests/phase09/test_e2e_synthetic_dry_run.py finalized with 4 E2E tests GREEN"
    - "tests/phase09/phase09_acceptance.py SC 1-4 aggregators flipped from stub=False to concrete checks"
    - "python tests/phase09/phase09_acceptance.py exits 0 (all 4 SC PASS)"
    - "09-TRACEABILITY.md created with KPI-05 + KPI-06 × source × test × SC matrix"
    - "09-VALIDATION.md frontmatter status=complete, nyquist_compliant=true, wave_0_complete=true, completed=2026-04-20"
    - "ROADMAP.md Phase 9 row updated: [ ] → [x] COMPLETE with date"
    - "STATE.md Phase 9 marked complete with Plans 0/TBD → 6/6"
    - "Full regression sweep green: pytest tests/ -q exits 0"
    - "Phase 4-8 986+ baseline preserved"
    - "Synthetic dry-run against wiki/kpi/taste_gate_2026-04.md produces exactly 3 FAILURES.md escalations (SC#4 proven)"
  artifacts:
    - path: "tests/phase09/test_e2e_synthetic_dry_run.py"
      provides: "SC#4 end-to-end: dry-run file → record_feedback.py → FAILURES.md has [taste_gate] 2026-04 entry (4 tests)"
      min_lines: 80
    - path: "tests/phase09/phase09_acceptance.py"
      provides: "SC 1-4 aggregator finalized — exits 0 when all green (flipped from Wave 0 stub=False)"
      min_lines: 100
    - path: ".planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md"
      provides: "2-REQ × source × test × SC matrix (KPI-05 + KPI-06) mirroring Phase 8 08-TRACEABILITY.md format"
      min_lines: 60
  key_links:
    - from: "tests/phase09/phase09_acceptance.py"
      to: "tests/phase08/phase08_acceptance.py"
      via: "SC aggregator shape precedent — 4-function stub → concrete checks + sys.exit on all-green"
      pattern: "sys.exit|all\\(|def sc[1-4]"
    - from: ".planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md"
      to: ".planning/phases/08-remote-publishing-production-metadata/08-TRACEABILITY.md"
      via: "Format mirror — REQ × source × test × SC matrix + Plan audit trail"
      pattern: "^\\| REQ-ID \\|"
    - from: ".planning/ROADMAP.md"
      to: ".planning/phases/09-documentation-kpi-dashboard-taste-gate/09-05-e2e-phase-gate-PLAN.md"
      via: "Phase 9 row flip [ ] → [x] COMPLETE + date + 6/6 Plans count"
      pattern: "Phase 9.*Complete"
---

<objective>
Wave 3 phase gate — finalize Phase 9 completion. Three tasks:

1. **Finalize test_e2e_synthetic_dry_run.py** — convert RED stub (from Plan 09-00) to GREEN by adding full E2E assertions: synthetic dry-run file → record_feedback.py invocation → FAILURES.md has new `[taste_gate] 2026-04` entry with 3 escalated items.

2. **Flip phase09_acceptance.py** — replace 4 stub aggregator functions (each returning False) with concrete SC 1-4 checks (grep conditions, file existence, regex matches) that aggregate to exit 0 when Phase 9 is complete.

3. **Phase gate** — create 09-TRACEABILITY.md (2-REQ matrix), flip 09-VALIDATION.md frontmatter to complete, update ROADMAP.md Phase 9 row `[ ] → [x]`, update STATE.md to reflect 6/6 plans + Phase 9 complete. Full regression sweep.

Purpose: Target SC#4 (end-to-end synthetic dry-run flow proven) + phase gate closure. This is the final plan — after Plan 09-05, Phase 9 ships and Phase 10 Sustained Operations becomes the next target.

Output: 2 test files finalized + 1 traceability matrix + 1 validation flip + ROADMAP + STATE updates + Phase 9 complete banner.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md
@.planning/phases/08-remote-publishing-production-metadata/08-TRACEABILITY.md
@tests/phase09/test_e2e_synthetic_dry_run.py
@tests/phase09/phase09_acceptance.py
@tests/phase09/conftest.py
@scripts/taste_gate/record_feedback.py
@docs/ARCHITECTURE.md
@wiki/kpi/kpi_log.md
@wiki/kpi/taste_gate_protocol.md
@wiki/kpi/taste_gate_2026-04.md

<interfaces>
## Finalized test_e2e_synthetic_dry_run.py (expanded from Plan 09-00 stub)

The file MUST contain 4 tests, import `record_feedback` directly (no pytest.importorskip — Plan 09-04 shipped the module), use Plan 09-00 fixtures (synthetic_taste_gate_april / tmp_failures_md / freeze_kst_2026_04_01), and assert:

1. **test_e2e_parse_filter_append** — synthetic fixture → `main(["--month", "2026-04"])` → `FAILURES.md.startswith(prior)` AND contains `### [taste_gate] 2026-04` AND contains `jkl012`+`mno345`+`pqr678` AND escalation block "#### 세부 코멘트" does NOT contain `abc123`/`def456`/`ghi789`.

2. **test_e2e_dry_run_no_write** — `main(["--month", "2026-04", "--dry-run"])` returns 0 AND `FAILURES.md` byte-identical to prior state.

3. **test_e2e_escalation_count_exactly_3** — D-13 anchor: `parse_taste_gate("2026-04")` then `filter_escalate(rows)` returns list of length 3 with sorted scores `[1, 2, 3]`.

4. **test_e2e_korean_timestamp_format** — `build_failures_block("2026-04", escalated)` contains either `+09:00` (ISO offset) or `KST` marker (Asia/Seoul timezone anchor).

## Finalized phase09_acceptance.py (concrete checks replacing Wave 0 stubs)

Replace the 4 stub functions (each returning False) with concrete SC aggregators that read actual files and check literal strings:

- **sc1_architecture_doc()** returns True iff: `docs/ARCHITECTURE.md` exists AND `re.findall(r'^```mermaid\s*$', content, re.MULTILINE)` >= 3 AND `"stateDiagram-v2" in content` AND `re.search(r'flowchart (TD|LR)', content)` AND TL;DR line index < 50 AND `re.findall(r'⏱\s*~?(\d+)\s*min', content)` >= 4 AND sum of those ints <= 35.

- **sc2_kpi_log_hybrid()** returns True iff: `wiki/kpi/kpi_log.md` exists AND all 14 literal strings present: `Part A`, `Part B`, `Target Declaration`, `Monthly Tracking`, `60%`, `40%`, `3초 retention`, `완주율`, `youtubeanalytics.googleapis.com/v2/reports`, `yt-analytics.readonly`, `audienceWatchRatio`, `averageViewDuration`, `video_id`, `taste_gate_rank`.

- **sc3_taste_gate_protocol_and_dryrun()** returns True iff: both `wiki/kpi/taste_gate_protocol.md` AND `wiki/kpi/taste_gate_2026-04.md` exist AND protocol contains `매월 1일`/`KST 09:00`/`상위 3`/`하위 3` AND dry-run contains `status: dry-run` AND all 6 video_ids (abc123/def456/ghi789/jkl012/mno345/pqr678) AND NO `테스트용 쇼츠` (forbidden placeholder).

- **sc4_e2e_synthetic_dryrun()** returns True iff: `subprocess.run([sys.executable, "-m", "pytest", "tests/phase09/test_e2e_synthetic_dry_run.py", "-x", "--no-cov", "-q"], cwd=_REPO_ROOT)` returns 0.

**main()** prints each SC PASS/FAIL and returns 0 if `all(results.values())`, else 1. cp949 guard via `sys.stdout.reconfigure(encoding="utf-8")` in `__main__` block.

## 09-TRACEABILITY.md structure (mirror of 08-TRACEABILITY.md)

- Frontmatter: `phase: 9`, `slug: documentation-kpi-dashboard-taste-gate`, `status: complete`, `completed: 2026-04-20`, `coverage: 2/2 (100%)`
- H1: `# Phase 9 — Traceability Matrix`
- REQ × Source × Test × SC table — 2 rows:
  - KPI-05: wiki/kpi/taste_gate_protocol.md + taste_gate_2026-04.md + scripts/taste_gate/record_feedback.py → test_taste_gate_form_schema + test_record_feedback + test_score_threshold_filter + test_failures_append_only + test_e2e_synthetic_dry_run → SC#3, SC#4 → ✅ complete
  - KPI-06: wiki/kpi/kpi_log.md + docs/ARCHITECTURE.md §4 External → test_kpi_log_schema + test_architecture_doc_structure → SC#1, SC#2 → ✅ complete
- SC × Source × Test table — 4 rows (SC#1 / SC#2 / SC#3 / SC#4) with source file + test file + test counts
- Plan Audit Trail table — 6 rows (09-00 through 09-05) with Wave / Focus / Files / Tests / Shipped date columns
- Phase 9 Test Count: ~30 Phase 9 isolated + 986+ regression baseline preserved = ~1016+ combined
- References: ROADMAP / REQUIREMENTS / CONTEXT / RESEARCH / VALIDATION file paths
- Footer: `*Generated: 2026-04-20 (Phase 9 Plan 09-05 phase gate)*`

## 09-VALIDATION.md frontmatter final state

Before:
```yaml
---
phase: 9
slug: documentation-kpi-dashboard-taste-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-20
---
```

After:
```yaml
---
phase: 9
slug: documentation-kpi-dashboard-taste-gate
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-20
completed: 2026-04-20
---
```

Also flip bottom line: `**Approval:** pending (flip to approved 2026-04-XX after Wave 3 phase gate passes)` → `**Approval:** approved 2026-04-20 (Wave 3 phase gate passed)`.

## ROADMAP.md Phase 9 updates (3 sites)

**Site 1 — line 22 (Phases bullet list):**
- Before: `- [ ] **Phase 9: Documentation + KPI Dashboard + Taste Gate** — KPI 목표 설정 + 월 1회 대표님 taste 평가 회로 가동`
- After: `- [x] **Phase 9: Documentation + KPI Dashboard + Taste Gate** — KPI 목표 설정 + 월 1회 대표님 taste 평가 회로 가동 (세션 #23 완료 2026-04-20, 6/6 plans + 4/4 SC PASS + 2/2 REQs)`

**Site 2 — line 229 (Phase 9 detail):**
- Before: `**Plans:** TBD`
- After (multi-line):
  ```
  **Plans:** 6/6 plans complete
  - [x] 09-00-foundation-PLAN.md — Wave 0 FOUNDATION (test scaffolding + fixtures + namespace)
  - [x] 09-01-architecture-PLAN.md — Wave 1 ARCHITECTURE.md (3 Mermaid + reading time + TL;DR)
  - [x] 09-02-kpi-log-PLAN.md — Wave 1 kpi_log.md Hybrid (KPI-06 + API contract)
  - [x] 09-03-taste-gate-docs-PLAN.md — Wave 1 taste_gate_protocol.md + dry-run (KPI-05)
  - [x] 09-04-record-feedback-PLAN.md — Wave 2 record_feedback.py (D-12 + D-13)
  - [x] 09-05-e2e-phase-gate-PLAN.md — Wave 3 E2E + phase gate (SC#4 + TRACEABILITY + VALIDATION flip). **PHASE 9 COMPLETE.**
  ```

**Site 3 — line 261 (Progress Table row):**
- Before: `| 9. Docs + KPI + Taste Gate | 0/TBD | Not started | - |`
- After: `| 9. Docs + KPI + Taste Gate | 6/6 | ✅ Complete | 2026-04-20 |`

## STATE.md update

Find Phase 9 references and update:
- Current phase position → Phase 9 complete (2026-04-20)
- Plans complete: 0/TBD → 6/6
- Next phase target: Phase 10 Sustained Operations (영구 지속, 첫 1-2개월 D-2 저수지)
- Combined test count: Phase 4-9 (target ~1016+ tests green)
- Append entry under Recent Milestones / Completed Phases section (if present) documenting Phase 9 shipped 2026-04-20
</interfaces>
</context>

<tasks>

<task id="9-05-01">
  <action>
Replace `tests/phase09/test_e2e_synthetic_dry_run.py` with the finalized 4-test version. Requirements:

1. Remove the Wave 0 `pytest.importorskip("scripts.taste_gate.record_feedback", ...)` guard and use direct import: `from scripts.taste_gate import record_feedback`.

2. Write exactly these 4 tests (in this order):
   - `test_e2e_parse_filter_append(synthetic_taste_gate_april, tmp_failures_md, freeze_kst_2026_04_01, monkeypatch)` — monkeypatches TASTE_GATE_DIR and FAILURES_PATH, captures prior content, calls `record_feedback.main(["--month", "2026-04"])` expecting rc=0, asserts `after.startswith(prior)`, asserts `"### [taste_gate] 2026-04" in after`, asserts jkl012/mno345/pqr678 are in `after`, then extracts the escalation block via `after.split("### [taste_gate] 2026-04")[1].split("#### 세부 코멘트")[1]` and asserts abc123/def456/ghi789 are NOT in that `seditions_section`.
   - `test_e2e_dry_run_no_write(synthetic_taste_gate_april, tmp_failures_md, monkeypatch)` — monkeypatches, captures prior, calls `main(["--month", "2026-04", "--dry-run"])` rc=0, asserts `after == prior`.
   - `test_e2e_escalation_count_exactly_3(synthetic_taste_gate_april, monkeypatch)` — parses + filters + asserts `len(escalated) == 3` AND `sorted(r["score"] for r in escalated) == [1, 2, 3]`.
   - `test_e2e_korean_timestamp_format(synthetic_taste_gate_april, freeze_kst_2026_04_01, monkeypatch)` — builds block and asserts `"+09:00" in block or "KST" in block`.

3. Hook 3종 compliance — no skip_gates / no TODO(next-session) / no try-except-pass.

4. UTF-8 encoding throughout (Korean strings in assertion messages OK).

Then replace `tests/phase09/phase09_acceptance.py` with the finalized concrete-check version per the `<interfaces>` §Finalized phase09_acceptance.py block. Requirements:

1. Keep exact function names: `sc1_architecture_doc`, `sc2_kpi_log_hybrid`, `sc3_taste_gate_protocol_and_dryrun`, `sc4_e2e_synthetic_dryrun`.

2. Each SC function reads actual files (use `_REPO_ROOT = Path(__file__).resolve().parents[2]` resolved path prefix) and performs literal string checks per spec in `<interfaces>`.

3. `sc4_e2e_synthetic_dryrun` uses `subprocess.run([sys.executable, "-m", "pytest", "tests/phase09/test_e2e_synthetic_dry_run.py", "-x", "--no-cov", "-q"], capture_output=True, text=True, cwd=_REPO_ROOT)` and returns `result.returncode == 0`.

4. `main()` prints 4 PASS/FAIL lines and returns 0 iff `all(results.values())`, else 1.

5. `if __name__ == "__main__"` block with `sys.stdout.reconfigure(encoding="utf-8")` cp949 guard.

Verification sequence:
```
python -m pytest tests/phase09/test_e2e_synthetic_dry_run.py -v --no-cov
python tests/phase09/phase09_acceptance.py
```

Both MUST exit 0. phase09_acceptance.py stdout MUST contain all 4 "PASS" markers (one per SC).
  </action>
  <read_first>
    - tests/phase09/test_e2e_synthetic_dry_run.py (current Wave 0 stub — importorskip pattern to remove)
    - tests/phase09/phase09_acceptance.py (current Wave 0 stub — all 4 SC return False)
    - tests/phase09/conftest.py (fixture signatures: synthetic_taste_gate_april, tmp_failures_md, freeze_kst_2026_04_01)
    - scripts/taste_gate/record_feedback.py (public API: main, parse_taste_gate, filter_escalate, build_failures_block, TASTE_GATE_DIR, FAILURES_PATH)
    - tests/phase08/phase08_acceptance.py (concrete aggregator pattern precedent)
    - docs/ARCHITECTURE.md (sc1 check targets)
    - wiki/kpi/kpi_log.md (sc2 check targets)
    - wiki/kpi/taste_gate_protocol.md + wiki/kpi/taste_gate_2026-04.md (sc3 check targets)
  </read_first>
  <acceptance_criteria>
    - `grep -c 'def test_' tests/phase09/test_e2e_synthetic_dry_run.py` outputs `>= 4`
    - `grep -q 'test_e2e_parse_filter_append' tests/phase09/test_e2e_synthetic_dry_run.py` exits 0
    - `grep -q 'test_e2e_dry_run_no_write' tests/phase09/test_e2e_synthetic_dry_run.py` exits 0
    - `grep -q 'test_e2e_escalation_count_exactly_3' tests/phase09/test_e2e_synthetic_dry_run.py` exits 0
    - `grep -q 'test_e2e_korean_timestamp_format' tests/phase09/test_e2e_synthetic_dry_run.py` exits 0
    - `grep -c 'pytest.importorskip' tests/phase09/test_e2e_synthetic_dry_run.py` outputs `0` (guard removed)
    - `grep -q 'from scripts.taste_gate import record_feedback' tests/phase09/test_e2e_synthetic_dry_run.py` exits 0
    - `python -m pytest tests/phase09/test_e2e_synthetic_dry_run.py -v --no-cov 2>&1 | grep -c 'PASSED'` outputs `>= 4`
    - `python -m pytest tests/phase09/test_e2e_synthetic_dry_run.py -v --no-cov 2>&1 | grep -c 'FAILED\|ERROR'` outputs `0`
    - `grep -c 'def sc1_architecture_doc\|def sc2_kpi_log_hybrid\|def sc3_taste_gate_protocol_and_dryrun\|def sc4_e2e_synthetic_dryrun' tests/phase09/phase09_acceptance.py` outputs `4`
    - `grep -q 'youtubeanalytics.googleapis.com/v2/reports' tests/phase09/phase09_acceptance.py` exits 0 (sc2 literal check)
    - `grep -q 'stateDiagram-v2' tests/phase09/phase09_acceptance.py` exits 0 (sc1 literal check)
    - `grep -q 'subprocess.run' tests/phase09/phase09_acceptance.py` exits 0 (sc4 uses subprocess)
    - `python tests/phase09/phase09_acceptance.py; test $? -eq 0` exits 0
    - `python tests/phase09/phase09_acceptance.py 2>&1 | grep -c 'PASS'` outputs `>= 4`
    - `python tests/phase09/phase09_acceptance.py 2>&1 | grep -c 'FAIL'` outputs `0`
  </acceptance_criteria>
  <automated>python tests/phase09/phase09_acceptance.py</automated>
  <task_type>impl</task_type>
</task>

<task id="9-05-02">
  <action>
Create `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` with EXACTLY the structure shown in the `<interfaces>` §09-TRACEABILITY.md block. Required structure:

1. **Frontmatter block:**
```yaml
---
phase: 9
slug: documentation-kpi-dashboard-taste-gate
status: complete
completed: 2026-04-20
coverage: 2/2 (100%)
---
```

2. **H1 title:** `# Phase 9 — Traceability Matrix`

3. **Intro paragraph** noting 2/2 v1 REQ coverage (KPI-05 + KPI-06) mapped to source × test × SC.

4. **`## REQ × Source × Test × SC` table** — 2 rows:
   - KPI-05 row: Sources = `wiki/kpi/taste_gate_protocol.md<br>wiki/kpi/taste_gate_2026-04.md<br>scripts/taste_gate/record_feedback.py`, Tests = 5 Phase 9 test files (form_schema + record_feedback + score_threshold + failures_append_only + e2e_synthetic), SC = `SC#3, SC#4`, Status = `✅ complete`
   - KPI-06 row: Sources = `wiki/kpi/kpi_log.md<br>docs/ARCHITECTURE.md §4 External Integrations`, Tests = `test_kpi_log_schema.py<br>test_architecture_doc_structure.py`, SC = `SC#1, SC#2`, Status = `✅ complete`

5. **`## SC × Source × Test` table** — 4 rows mapping each SC to source file(s) + test file(s) + test count:
   - SC#1 (30-min onboarding): docs/ARCHITECTURE.md → test_architecture_doc_structure.py (6 tests)
   - SC#2 (KPI targets + measurement): wiki/kpi/kpi_log.md → test_kpi_log_schema.py (5 tests)
   - SC#3 (Taste Gate protocol + dry-run): wiki/kpi/taste_gate_protocol.md + taste_gate_2026-04.md → test_taste_gate_form_schema.py (6 tests)
   - SC#4 (synthetic E2E → FAILURES): scripts/taste_gate/record_feedback.py + taste_gate_2026-04.md + .claude/failures/FAILURES.md → test_e2e_synthetic_dry_run.py (4 tests)

6. **`## Plan Audit Trail` table** — 6 rows (09-00 through 09-05) with columns: Plan | Wave | Focus | Files | Tests | Shipped. Populate with concrete counts per Plan 09-00..05.

7. **`## Phase 9 Test Count` section:**
   - Phase 9 isolated: ~30 tests (documentation schema + parser + filter + append + E2E)
   - Phase 4-8 regression preserved: 986+ baseline
   - Combined: ~1016+ tests target

8. **`## References` section:**
   - `.planning/ROADMAP.md` §219-229 (Phase 9 goal + SC 1-4)
   - `.planning/REQUIREMENTS.md` §KPI (KPI-05, KPI-06)
   - `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md` (D-01 ~ D-14)
   - `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md` (HIGH confidence)
   - `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` (SC → test map)

9. **Footer:** `*Generated: 2026-04-20 (Phase 9 Plan 09-05 phase gate)*` + `*Coverage: 2/2 REQ + 4/4 SC = 100%*`

Then flip `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md`. Replace the current frontmatter block exactly:

From:
```yaml
---
phase: 9
slug: documentation-kpi-dashboard-taste-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-20
---
```

To:
```yaml
---
phase: 9
slug: documentation-kpi-dashboard-taste-gate
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-20
completed: 2026-04-20
---
```

Also replace the Approval line at file bottom:
- Before: `**Approval:** pending (flip to approved 2026-04-XX after Wave 3 phase gate passes)`
- After: `**Approval:** approved 2026-04-20 (Wave 3 phase gate passed)`

Do NOT modify other parts of 09-VALIDATION.md (Per-Task Verification Map / Wave 0 Requirements / Manual-Only Verifications sections etc.). This is a surgical frontmatter + approval flip.
  </action>
  <read_first>
    - .planning/phases/08-remote-publishing-production-metadata/08-TRACEABILITY.md (format precedent — mirror this shape)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md (current frontmatter + approval line to flip)
    - .planning/REQUIREMENTS.md lines 146-147 (KPI-05 + KPI-06 exact text)
    - .planning/ROADMAP.md §219-229 (Phase 9 SC 1-4 exact text)
  </read_first>
  <acceptance_criteria>
    - `test -f .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` exits 0
    - `wc -l < .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` outputs a number >= 60
    - `grep -q '^phase: 9$' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` exits 0
    - `grep -q '^status: complete$' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` exits 0
    - `grep -q 'KPI-05' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` exits 0
    - `grep -q 'KPI-06' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` exits 0
    - `grep -c 'SC#[1-4]' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` outputs `>= 8`
    - `grep -c '^| 09-0[0-5]' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` outputs `6`
    - `grep -q '^status: complete$' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` exits 0
    - `grep -q '^nyquist_compliant: true$' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` exits 0
    - `grep -q '^wave_0_complete: true$' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` exits 0
    - `grep -q '^completed: 2026-04-20$' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` exits 0
    - `grep -q 'approved 2026-04-20' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` exits 0
    - `grep -q 'status: draft' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` must return 1 (draft status removed)
    - `grep -q 'nyquist_compliant: false' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` must return 1
    - `grep -q 'wave_0_complete: false' .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` must return 1
  </acceptance_criteria>
  <automated>grep -q "^status: complete$" .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md && grep -q "^nyquist_compliant: true$" .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md && test -f .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md</automated>
  <task_type>impl</task_type>
</task>

<task id="9-05-03">
  <action>
Update `.planning/ROADMAP.md` at 3 sites per `<interfaces>` §ROADMAP.md Phase 9 updates:

**Site 1 (line 22):** Change `- [ ] **Phase 9: Documentation + KPI Dashboard + Taste Gate** — ...` to `- [x] **Phase 9: Documentation + KPI Dashboard + Taste Gate** — KPI 목표 설정 + 월 1회 대표님 taste 평가 회로 가동 (세션 #23 완료 2026-04-20, 6/6 plans + 4/4 SC PASS + 2/2 REQs)`

**Site 2 (line ~229):** Change `**Plans:** TBD` under Phase 9 section to the 8-line multi-line block listing all 6 Plans (09-00 through 09-05) with `[x]` checkboxes and brief descriptions, ending with `**PHASE 9 COMPLETE.**`

**Site 3 (line ~261 — Progress Table):** Change row `| 9. Docs + KPI + Taste Gate | 0/TBD | Not started | - |` to `| 9. Docs + KPI + Taste Gate | 6/6 | ✅ Complete | 2026-04-20 |`

Use search-replace operations scoped to these exact lines. Do NOT reformat other parts of ROADMAP.md. Do NOT change Phase 1-8 rows or Phase 10 row.

Update `.planning/STATE.md`. Open STATE.md, search for Phase 9 references, update:

1. If there's a "Current Phase" or "Active Phase" field → change to Phase 10 (or note Phase 9 complete + next target Phase 10 Sustained Operations).
2. If there's a "Plans Complete" counter for Phase 9 → change from `0/TBD` to `6/6`.
3. If there's a "Recent Milestones" / "Completed Phases" section → append entry: `- 2026-04-20 (세션 #23): Phase 9 Documentation + KPI Dashboard + Taste Gate COMPLETE. 6/6 plans + 4/4 SC + 2/2 REQs (KPI-05/06). docs/ARCHITECTURE.md + wiki/kpi/kpi_log.md + taste_gate_protocol + dry-run + scripts/taste_gate/record_feedback.py. Phase 4-8 986+ regression preserved. 욜로 연속 5세션.`

If STATE.md structure doesn't clearly match these patterns, use judgment to append a similar note near the top (after any frontmatter) reflecting Phase 9 completion. Do NOT restructure STATE.md — surgical additions only.

**Final phase gate verification** — run the full regression sweep to confirm all 9 phases pass:

```
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 tests/phase09 -x --no-cov
```

MUST exit 0 (Phase 4-8 986+ baseline + Phase 9 ~30 new = ~1016+ tests green).

```
python tests/phase09/phase09_acceptance.py
```

MUST exit 0 (all 4 SC PASS).

```
python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run
```

MUST exit 0 and produce `### [taste_gate] 2026-04` + 3 escalations in stdout + preserve `.claude/failures/FAILURES.md` sha256 unchanged.

Commit message suggestion for this phase gate (via gsd-tools commit wrapper):

```
docs(09): Phase 9 COMPLETE — documentation + KPI dashboard + taste gate

- 6/6 plans shipped across 3 waves
- 4/4 SC PASS (ARCHITECTURE.md 30-min + kpi_log Hybrid + taste_gate protocol+dryrun + E2E synthetic)
- 2/2 REQs complete (KPI-05 taste gate + KPI-06 3 target values)
- Phase 4-8 986+ regression preserved; Phase 9 adds ~30 tests
- D-2 저수지 규율 준수: no new SKILLs, no orchestrator changes, no agent adds
- Hook 3종 차단 preserved: record_feedback.py audit clean (no skip_gates/TODO/silent-pass)
- Session #23, YOLO 연속 5세션 완주

Next: Phase 10 Sustained Operations (영구 지속, 첫 1-2개월 SKILL patch 전면 금지).
```
  </action>
  <read_first>
    - .planning/ROADMAP.md (all 3 Phase 9 update sites + verify Phase 8 line format to mirror)
    - .planning/STATE.md (locate Phase 9 references + understand file structure for surgical edit)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md (confirm just-flipped to status=complete)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md (confirm just-created)
    - tests/phase09/phase09_acceptance.py (confirm aggregator exits 0)
  </read_first>
  <acceptance_criteria>
    - `grep -q '^- \[x\] \*\*Phase 9:' .planning/ROADMAP.md` exits 0
    - `grep -q '2026-04-20' .planning/ROADMAP.md` exits 0 (date appears; may already be present for other phases)
    - `grep -c '09-0[0-5].*PLAN.md' .planning/ROADMAP.md` outputs `>= 6` (all 6 plan filenames listed)
    - `grep -q 'PHASE 9 COMPLETE' .planning/ROADMAP.md` exits 0
    - `grep -q '^| 9\. Docs + KPI + Taste Gate | 6/6 | ✅ Complete | 2026-04-20 |' .planning/ROADMAP.md` exits 0
    - `grep -q '| 9\..*0/TBD.*Not started' .planning/ROADMAP.md` must return 1 (old row removed)
    - `grep -q 'Phase 9.*COMPLETE\|Phase 9.*complete\|Phase 9.*완료' .planning/STATE.md` exits 0
    - `python tests/phase09/phase09_acceptance.py; test $? -eq 0` exits 0
    - `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 tests/phase09 -x --no-cov` exits 0 (full regression green)
    - `python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run; test $? -eq 0` exits 0
    - `python -c "import hashlib, pathlib, subprocess, sys; p=pathlib.Path('.claude/failures/FAILURES.md'); before=hashlib.sha256(p.read_bytes()).hexdigest(); subprocess.run([sys.executable, 'scripts/taste_gate/record_feedback.py', '--month', '2026-04', '--dry-run'], check=True, capture_output=True); after=hashlib.sha256(p.read_bytes()).hexdigest(); assert before == after, 'FAILURES.md changed during --dry-run'"` exits 0
  </acceptance_criteria>
  <automated>python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 tests/phase09 -x --no-cov</automated>
  <task_type>impl</task_type>
</task>

</tasks>

<verification>
1. `tests/phase09/test_e2e_synthetic_dry_run.py` shipped with 4 GREEN tests (E2E + dry-run + count + timestamp).
2. `tests/phase09/phase09_acceptance.py` exits 0 — all 4 SC aggregators PASS against live repo state.
3. `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` created with 2-REQ × source × test × SC matrix + 4-SC table + 6-row Plan Audit Trail.
4. `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` frontmatter flipped (draft→complete, false→true on nyquist_compliant + wave_0_complete, completed=2026-04-20) + approval line flipped.
5. `.planning/ROADMAP.md` Phase 9 row updated at 3 sites (phases list / detail Plans / Progress Table).
6. `.planning/STATE.md` reflects Phase 9 completion + next target Phase 10.
7. Full regression sweep green: Phase 4+5+6+7+8+9 = 1016+ tests PASS.
8. Production dry-run against live taste_gate_2026-04.md produces 3 escalations + preserves FAILURES.md sha256.
9. No Hook 3종 violations anywhere in new code.
</verification>

<success_criteria>
Plan 09-05 is COMPLETE (and thus PHASE 9 is COMPLETE) when:

- `tests/phase09/test_e2e_synthetic_dry_run.py` ships with 4 GREEN tests (test_e2e_parse_filter_append + test_e2e_dry_run_no_write + test_e2e_escalation_count_exactly_3 + test_e2e_korean_timestamp_format).
- `tests/phase09/phase09_acceptance.py` flipped from Wave 0 stub (all False) to 4 concrete checks (all PASS against actual repo state) — exits 0.
- `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-TRACEABILITY.md` created mirroring Phase 8 format (2-REQ × source × test × SC + 4-SC mapping + 6-plan audit trail + test count + references).
- `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-VALIDATION.md` frontmatter shows `status: complete`, `nyquist_compliant: true`, `wave_0_complete: true`, `completed: 2026-04-20`; approval line shows `approved 2026-04-20`.
- `.planning/ROADMAP.md` Phase 9 row flipped from `[ ]` → `[x]` with `6/6 plans`, `4/4 SC PASS`, `2/2 REQs`, session #23, date 2026-04-20.
- `.planning/STATE.md` reflects Phase 9 completion.
- SC#4 proven: synthetic dry-run against real `wiki/kpi/taste_gate_2026-04.md` produces exactly 3 `[taste_gate] 2026-04` FAILURES escalations (scores 1/2/3; top 3 filtered out per D-13).
- Phase 4-8 986+ regression baseline preserved (run `pytest tests/phase04..08 -x --no-cov` = 0 exit).
- Phase 9 adds ~30 new tests to combined sweep (~1016+ tests total).
- FAILURES.md sha256 unchanged after all --dry-run executions (append-only Hook contract intact).
- PHASE 10 Sustained Operations is now the next target; D-2 저수지 규율 (첫 1-2개월 SKILL patch 전면 금지) ready to enforce.
</success_criteria>

<output>
Create `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-05-SUMMARY.md` documenting:
- 2 test files finalized (test_e2e_synthetic_dry_run.py + phase09_acceptance.py with line counts + test counts)
- 2 phase gate files (09-TRACEABILITY.md + 09-VALIDATION.md frontmatter flip)
- ROADMAP.md 3 sites updated (phases list + Phase 9 Plans detail + Progress Table)
- STATE.md Phase 9 completion reflected
- Full regression result: Phase 4-9 combined test count (actual number)
- phase09_acceptance.py output (4 PASS lines)
- Production dry-run output (3 escalations, jkl012/mno345/pqr678)
- FAILURES.md sha256 before/after (matching)
- Commit hashes (expected 4 atomic commits: test finalize / aggregator flip / traceability+validation / ROADMAP+STATE+phase-gate)
- **PHASE 9 COMPLETE** banner
- Next phase: Phase 10 Sustained Operations (영구 지속, 첫 1-2개월 SKILL patch 전면 금지 per D-2 저수지 규율)
</output>
