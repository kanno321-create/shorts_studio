---
phase: 11
slug: pipeline-real-run-activation-script-quality-mode
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-21
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: RESEARCH.md §Validation Architecture (dim-8 Nyquist).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing; 986+ full-sweep baseline from STATE.md session #21) |
| **Config file** | none (pytest defaults + `tests/phase*/` convention) |
| **Quick run command** | `pytest tests/phase11/ -x` (~30s) |
| **Full suite command** | `pytest tests/ -q` (~9 min) |
| **Phase 11 live smoke** | `py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd 5.00` (one-shot, ~$2-5) |
| **Estimated runtime** | Quick ~30s · Full ~9m · Live smoke ~15-25m (real API) |

---

## Sampling Rate

- **After every task commit:** `pytest tests/phase11/ -x` (quick)
- **After every plan wave:** `pytest tests/phase10/ tests/phase11/ -q` (~2 min, regression cross-wave)
- **Before `/gsd:verify-work`:** Full suite (`pytest tests/ -q`) GREEN + `phase11_full_run.py --live` ONE-SHOT success
- **Max feedback latency:** 30 seconds for task-level · 9 minutes for phase-level

---

## Per-SC Verification Map (6 Success Criteria from ROADMAP §297-303)

| SC # | Plan | Wave | Requirement | Test Type | Automated Command | Manual? | Status |
|------|------|------|-------------|-----------|-------------------|---------|--------|
| **SC#1** Full 0→13 real-run smoke | 11-06 | 3 | PIPELINE-01 (validation) | live-smoke + file-count | `py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd 5.00` → exit 0; `ls state/<sid>/gate_*.json \| wc -l` == 14 | NO | ⬜ pending |
| **SC#2** 1 video published + SCRIPT-01 verdict | 11-06 | 3 | SCRIPT-01 | live-upload + manual eval | YouTube Studio shows video; `SCRIPT_QUALITY_DECISION.md` frontmatter `verdict: A\|B\|C` present | **YES (대표님 6-axis eval)** | ⬜ pending |
| **SC#3** skill_patch_counter idempotency | 11-05 | 2 | AUDIT-05 | unit | `pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -x` → GREEN | NO | ⬜ pending |
| **SC#4** `.env` auto-load | 11-02 | 1 | PIPELINE-02 | unit (13 edge cases) | `pytest tests/phase11/test_dotenv_loader.py -v` → all GREEN | NO | ⬜ pending |
| **SC#5** `run_pipeline.cmd/.ps1` wrapper | 11-04 | 2 | PIPELINE-04 | unit + file-existence + manual click | `pytest tests/phase11/test_wrapper_smoke.py -v` GREEN; files exist at repo root | **YES (대표님 double-click confirm)** | ⬜ pending |
| **SC#6** (OPTIONAL) Phase 04/08 retrospective | N/A | N/A | — | file-existence | `test -f .planning/phases/04-*/04-VERIFICATION.md && test -f .planning/phases/08-*/08-VERIFICATION.md` | NO | ⏸ deferred (per D-18 alternative) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky · ⏸ deferred*

### Per-Task Verification Matrix (more granular)

| Task ID | Plan | Wave | REQ | Test Type | Command | Status |
|---------|------|------|-----|-----------|---------|--------|
| 11-01-01 | 01 | 1 | PIPELINE-01 | unit | `pytest tests/phase11/test_invoker_stdin.py -v` (6 cases: stdin wire / timeout / rc!=0 / empty stdout / Korean round-trip / seam compat) | ⬜ |
| 11-02-01 | 02 | 1 | PIPELINE-02 | unit | `pytest tests/phase11/test_dotenv_loader.py -v` (13 edge cases: quoted / comments / BOM / etc.) | ⬜ |
| 11-03-01 | 03 | 1 | PIPELINE-03 | unit | `pytest tests/phase11/test_adapter_graceful_degrade.py -v` (5 tests: 5 adapters + helper) | ⬜ |
| 11-03-02 | 03 | 1 | PIPELINE-04 tie-in | unit | `pytest tests/phase11/test_argparse_session_id.py -v` (3 tests: required=False / auto-default / explicit override) | ⬜ |
| 11-04-01 | 04 | 2 | PIPELINE-04 | unit + file | `pytest tests/phase11/test_wrapper_smoke.py -v` + `test -f run_pipeline.cmd && test -f run_pipeline.ps1` | ⬜ |
| 11-05-01 | 05 | 2 | AUDIT-05 | unit | `pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -x` | ⬜ |
| 11-06-01 | 06 | 3 | PIPELINE-01 validation | live-smoke | `py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd 5.00` | ⬜ |
| 11-06-02 | 06 | 3 | SCRIPT-01 | manual | 대표님 fills `SCRIPT_QUALITY_DECISION.md` frontmatter + 6-axis table | ⬜ |

---

## Wave 0 Requirements (test scaffold — each plan ships its own Wave 0 items)

- [ ] `tests/phase11/__init__.py` — new test dir marker
- [ ] `tests/phase11/conftest.py` — fixtures: `tmp_env_file`, `mock_cli_runner`, `fake_claude_cli_runner_factory`
- [ ] `tests/phase11/test_invoker_stdin.py` — 6 tests for PIPELINE-01 (Plan 11-01)
- [ ] `tests/phase11/test_dotenv_loader.py` — 13 edge-case tests for PIPELINE-02 (Plan 11-02)
- [ ] `tests/phase11/test_adapter_graceful_degrade.py` — 5 tests for PIPELINE-03 (Plan 11-03)
- [ ] `tests/phase11/test_argparse_session_id.py` — 3 tests for argparse relax (Plan 11-03)
- [ ] `tests/phase11/test_wrapper_smoke.py` — 2 tests for PIPELINE-04 wrapper (Plan 11-04)
- [ ] `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` — new test case extending existing file (Plan 11-05)
- [ ] `scripts/smoke/phase11_full_run.py` — full 0→13 live harness (Plan 11-06, skeleton from `scripts/smoke/phase091_stage2_to_4.py`)
- [ ] `.planning/phases/11-.../SCRIPT_QUALITY_DECISION.md` — eval capture template (Plan 11-06 produces)

*No framework install needed — pytest already in use. Wave 0 is plan-internal (test scaffold files ship in the same commit as the implementation).*

---

## Manual-Only Verifications

| Behavior | SC | Requirement | Why Manual | Test Instructions |
|----------|----|-------------|------------|-------------------|
| YouTube video actually published | SC#2 | SCRIPT-01 | External API side effect; cannot self-verify authoritatively from within test process | 대표님 opens https://studio.youtube.com → Videos tab → 최신 업로드 확인. URL을 `SCRIPT_QUALITY_DECISION.md` frontmatter `video_url:` 에 기록. |
| 대본 품질 6-axis 평가 | SC#2 | SCRIPT-01 | Human subjective judgment (훅 강도, 대사 자연스러움, 팩트, 듀오 리듬, 감정, 완성도) | 대표님 views published video → fills 6-axis 1-5 scores + verdict letter in `SCRIPT_QUALITY_DECISION.md` table |
| 더블클릭 wrapper 실제 실행 | SC#5 | PIPELINE-04 | Double-click UX is a desktop-shell behavior; automated test can dry-run parse but cannot emulate shell association | 대표님 opens 탐색기 → `run_pipeline.cmd` 더블클릭 → 창이 열리고 .env 로드 + 세션 시작 + pause-on-error 동작 확인 |
| Windows 11 ExecutionPolicy 우회 동작 | SC#5 | PIPELINE-04 | OS policy state varies per machine; need 대표님 PC 실행 | Same as above — if `.ps1`가 Notepad에서 열리면 실패; PowerShell 창에서 실행되면 성공 |

---

## Validation Sign-Off

- [ ] All tasks have `<acceptance_criteria>` or Wave 0 test dependencies specified
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (largest gap = SC#2 manual eval, isolated)
- [ ] Wave 0 covers all MISSING test files (8 new test files + 1 smoke script + 1 decision template)
- [ ] No watch-mode flags — all pytest commands use `-x` or `-q` (deterministic exit)
- [ ] Feedback latency < 30s for task-level, < 9m for phase-level
- [ ] `nyquist_compliant: true` set in frontmatter (after planner + checker pass)

**Approval:** pending
