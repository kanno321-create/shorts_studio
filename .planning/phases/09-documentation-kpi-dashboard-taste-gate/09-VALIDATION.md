---
phase: 9
slug: documentation-kpi-dashboard-taste-gate
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-20
completed: 2026-04-20
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `09-RESEARCH.md` §Validation Architecture (HIGH confidence).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (project baseline, inherited from Phase 4-8) |
| **Config file** | `pyproject.toml` / `pytest.ini` (existing, no change) |
| **Quick run command** | `pytest tests/phase09/ -x --tb=short` |
| **Full suite command** | `pytest tests/ --tb=short` (Phase 4+5+6+7+8 regression = 986+ tests; Phase 9 adds ~20-30) |
| **Phase 9 acceptance** | `python tests/phase09/phase09_acceptance.py` (mirrors `phase08_acceptance.py`) |
| **Estimated runtime** | ~1-2 seconds (Phase 9 isolated) / ~8-10 min (full regression) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/phase09/ -x --tb=short`
- **After every plan wave:** Run `pytest tests/ --tb=short` (full regression — Phase 4-8 baseline MUST stay green)
- **Before `/gsd:verify-work`:** Full suite must be green + `python tests/phase09/phase09_acceptance.py` exits 0
- **Max feedback latency:** 5 seconds for Phase 9 isolated; 10 min for full regression

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement/SC | Test Type | Automated Command | File Exists | Status |
|---------|------|------|---------------|-----------|-------------------|-------------|--------|
| 9-00-01 | 00 (Wave 0) | 0 | Wave 0 scaffolding | infra | `pytest tests/phase09/ --collect-only` | ❌ W0 | ⬜ pending |
| 9-01-01 | 01 | 1 | SC#1 (ARCHITECTURE.md) | unit | `pytest tests/phase09/test_architecture_doc_structure.py -x` | ❌ W0 | ⬜ pending |
| 9-01-02 | 01 | 1 | SC#1 (reading time) | unit | `pytest tests/phase09/test_architecture_doc_structure.py::test_reading_time -x` | ❌ W0 | ⬜ pending |
| 9-01-03 | 01 | 1 | SC#1 (TL;DR top 50 lines) | unit | `pytest tests/phase09/test_architecture_doc_structure.py::test_tldr_section_near_top -x` | ❌ W0 | ⬜ pending |
| 9-02-01 | 02 | 1 | KPI-06 (3 targets declared) | unit | `pytest tests/phase09/test_kpi_log_schema.py::test_target_declaration -x` | ❌ W0 | ⬜ pending |
| 9-02-02 | 02 | 1 | KPI-06 (API contract) | unit | `pytest tests/phase09/test_kpi_log_schema.py::test_api_contract_present -x` | ❌ W0 | ⬜ pending |
| 9-02-03 | 02 | 1 | SC#2 (Hybrid format) | unit | `pytest tests/phase09/test_kpi_log_schema.py::test_hybrid_structure -x` | ❌ W0 | ⬜ pending |
| 9-03-01 | 03 | 1 | KPI-05 (form schema) | unit | `pytest tests/phase09/test_taste_gate_form_schema.py -x` | ❌ W0 | ⬜ pending |
| 9-03-02 | 03 | 1 | SC#3 (protocol doc) | unit | `pytest tests/phase09/test_taste_gate_form_schema.py::test_protocol_doc -x` | ❌ W0 | ⬜ pending |
| 9-03-03 | 03 | 1 | SC#3 (dry-run exists) | unit | `pytest tests/phase09/test_taste_gate_form_schema.py::test_dry_run_exists -x` | ❌ W0 | ⬜ pending |
| 9-04-01 | 04 | 2 | KPI-05 (parse 6 rows) | unit | `pytest tests/phase09/test_record_feedback.py::test_parse_six_rows -x` | ❌ W0 | ⬜ pending |
| 9-04-02 | 04 | 2 | KPI-05 (D-13 score filter) | unit | `pytest tests/phase09/test_score_threshold_filter.py -x` | ❌ W0 | ⬜ pending |
| 9-04-03 | 04 | 2 | D-12 (Hook-valid append) | integration | `pytest tests/phase09/test_failures_append_only.py -x` | ❌ W0 | ⬜ pending |
| 9-05-01 | 05 | 3 | SC#4 (E2E synthetic dry-run) | integration | `pytest tests/phase09/test_e2e_synthetic_dry_run.py -x` | ❌ W0 | ⬜ pending |
| 9-05-02 | 05 | 3 | Phase gate (all SC) | aggregation | `python tests/phase09/phase09_acceptance.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase09/__init__.py` — package marker
- [ ] `tests/phase09/conftest.py` — fixtures (`synthetic_taste_gate_april`, `tmp_failures_md`, `freeze_kst_2026_04_01`)
- [ ] `tests/phase09/test_architecture_doc_structure.py` — SC#1 validators (Mermaid block count ≥3, state diagram present, flowchart present, reading time ≤ 35 min with tolerance, TL;DR in top 50 lines)
- [ ] `tests/phase09/test_kpi_log_schema.py` — SC#2 + KPI-06 validators (target declaration table 3 rows, YouTube Analytics v2 endpoint reference, OAuth scope `yt-analytics.readonly` mentioned, hybrid structure Part A + Part B)
- [ ] `tests/phase09/test_taste_gate_form_schema.py` — SC#3 + KPI-05 validators (form schema 6 rows, 1-5 score column, comment column, protocol doc with monthly cadence, dry-run YYYY-MM file exists)
- [ ] `tests/phase09/test_record_feedback.py` — KPI-05 parser (parse synthetic 6 rows correctly, extract video_id/title/score/comment)
- [ ] `tests/phase09/test_score_threshold_filter.py` — KPI-05 D-13 (scores > 3 excluded, scores ≤ 3 included in FAILURES payload)
- [ ] `tests/phase09/test_failures_append_only.py` — D-12 Hook compatibility (record_feedback.py uses read+append+write, NOT `open('a')`; prior content preserved as prefix)
- [ ] `tests/phase09/test_e2e_synthetic_dry_run.py` — SC#4 end-to-end (dry-run file → record_feedback.py → FAILURES.md new entry appears with `[taste_gate] 2026-04` tag)
- [ ] `tests/phase09/phase09_acceptance.py` — SC 1-4 aggregator (mirrors `tests/phase08/phase08_acceptance.py` pattern, exit 0 only if all SC green)

**Framework install:** None — pytest already in place since Phase 4 (329 tests baseline).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 30-min onboarding actually achieved | SC#1 | Requires fresh-mind reader; synthetic time declaration insufficient | Next new session (or Phase 10 handoff): reader starts stopwatch, reads ARCHITECTURE.md top-to-bottom, logs actual time. Target ≤ 30 min with ≤ 5 min tolerance. |
| Taste Gate UX is "편함" | KPI-05 / D-09 | Subjective UX check — 대표님 dry-run feedback | 대표님 opens `wiki/kpi/taste_gate_2026-04.md` in VSCode, fills evaluations, records whether format is comfortable (1-5 scale). Iteration acceptable before Phase 10. |
| Mermaid diagrams render in GitHub | SC#1 | Requires push to GitHub + visual inspection | After Phase 9 push: open commit on github.com/kanno321-create/shorts_studio, verify 3 Mermaid blocks render as SVG (not raw code). |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags (no `pytest-watch`, no `--forked`)
- [ ] Feedback latency < 5s for phase09 isolated suite
- [ ] `nyquist_compliant: true` set in frontmatter after all automated + manual gates pass

**Approval:** approved 2026-04-20 (Wave 3 phase gate passed)

---

## Escalation / D-2 저수지 인터락

- Phase 9는 인간 감독 게이트의 마지막 설치. 이번 phase에서 SKILL.md patch 금지 (Phase 10 D-2 규율 사전 준수).
- `record_feedback.py` 실행 실패 시 FAILURES.md 조용한 폴백 금지 (Hook 3종 차단). 에러는 raise하고 대표님에게 표시.
- 30-min onboarding 실패가 Phase 10 첫 세션에서 확인되면 Phase 10 첫 1-2개월 저수지 종료 후 batch로 해결 (즉시 ARCHITECTURE.md patch 금지 = D-2 규율).
