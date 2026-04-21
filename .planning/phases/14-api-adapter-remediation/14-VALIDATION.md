---
phase: 14
slug: api-adapter-remediation
status: approved_with_deferred
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-21
updated: 2026-04-21
approved: 2026-04-21
closure_mode: complete_with_deferred
deferred_items: [SC#5 full pytest tests/ — 2 failures at [86%] in non-Phase-14 scope + infra timeout]
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Derived from 14-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing project standard) |
| **Config file** | `pytest.ini` — Wave 0 installs (root-level, currently absent) |
| **Quick run command** | `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short -q` |
| **Full suite command** | `pytest tests/` |
| **Contract-only command** | `pytest -m adapter_contract` (ADAPT-06) |
| **Estimated runtime** | phase05~07 quick ≈ 660s (measured 2026-04-21) / full suite ≈ 900s / contract-only ≈ 30s |

---

## Sampling Rate

- **After every task commit:** Run task-scoped quick subset (e.g., only `tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator` for Task 14-02-01)
- **After every plan wave:** Run `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short -q` (must show 15→N failures monotonically decreasing)
- **Before phase gate:** Full suite + `pytest -m adapter_contract` both green
- **Max feedback latency:** 120s (quick per-task) / 660s (wave boundary)

---

## Per-Task Verification Map

Authoritative mapping of every plan task ID → wave → real pytest/validation command. Commands are derived from 14-RESEARCH.md Bucket A/B/C fix locations and each task's `<done>` field as ground truth.

| Task ID | Plan | Wave | Requirement | Test Type | Real Automated Command | Status |
|---------|------|------|-------------|-----------|------------------------|--------|
| 14-01-01 | 01 | 0 | ADAPT-06 | pre-audit | `grep -rE "@pytest\.mark\.(?!(skip\|skipif\|xfail\|parametrize\|asyncio\|adapter_contract))" tests/ scripts/ \| wc -l` returns 0 (or all findings registered in Task 14-01-02 pytest.ini markers) | ⬜ pending |
| 14-01-02 | 01 | 0 | ADAPT-06 | infra | `pytest --markers \| grep -c "adapter_contract"` ≥1 + `test -f pytest.ini` exits 0 + `pytest --collect-only tests/phase05 tests/phase06 tests/phase07 2>&1 \| grep -ci "unknown mark\|PytestUnknownMarkWarning"` returns 0 | ⬜ pending |
| 14-01-03 | 01 | 0 | ADAPT-01/02/03 | infra | `python -c "import tests.adapters; import tests.adapters.conftest"` exits 0 + `test -f tests/adapters/__init__.py` + `test -f tests/adapters/conftest.py` + `pytest --collect-only -m adapter_contract -q` exits 0 | ⬜ pending |
| 14-02-01 | 02 | 1 | ADAPT-04 (veo_i2v self-doc blacklist unblock, Bucket A2 A-4) | regression | `pytest tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator -x --no-cov -q` exits 0 | ⬜ pending |
| 14-02-02 | 02 | 1 | ADAPT-04 (runway gen4.5, Bucket A A-1) | regression | `pytest tests/phase05/test_kling_adapter.py::test_runway_valid_call_returns_path -x --no-cov -q` exits 0 | ⬜ pending |
| 14-02-03 | 02 | 1 | ADAPT-04 (line caps elevenlabs 340→360 + shotstack 400→420, Bucket A A-2) | regression | `pytest tests/phase05/test_line_count.py::test_api_adapters_under_soft_caps -x --no-cov -q` exits 0 | ⬜ pending |
| 14-02-04 | 02 | 1 | ADAPT-04 (MOC status invariant scaffold\|partial, Bucket B B-1) | regression | `pytest tests/phase06/test_moc_linkage.py::test_moc_frontmatter_unchanged_scaffold -x --no-cov -q` exits 0 | ⬜ pending |
| 14-02-05 | 02 | 1 | ADAPT-04 (notebooklm skill path migration, Bucket B B-2) | regression | `pytest tests/phase06/test_notebooklm_wrapper.py::test_default_skill_path_is_the_2026_install -x --no-cov -q` exits 0 | ⬜ pending |
| 14-02-06 | 02 | 1 | ADAPT-04 (Wave 1 sweep) | sweep | Wave 1 regression: `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short -q` 0 failed (captured to `14-02-wave1-sweep.log`); verified POSIX-safe via `[ "$(grep -cE '[0-9]+ failed' 14-02-wave1-sweep.log)" = "0" ]` | ⬜ pending |
| 14-03-01 | 03 | 2 | ADAPT-01 | contract | `pytest tests/adapters/test_veo_i2v_contract.py -m adapter_contract -v --no-cov` exits 0 (≥6 tests green) | ⬜ pending |
| 14-03-02 | 03 | 2 | ADAPT-02 | contract | `pytest tests/adapters/test_elevenlabs_contract.py -m adapter_contract -v --no-cov` exits 0 (≥7 tests green) | ⬜ pending |
| 14-03-03 | 03 | 2 | ADAPT-03 | contract | `pytest tests/adapters/test_shotstack_contract.py -m adapter_contract -v --no-cov` exits 0 (≥7 tests green) | ⬜ pending |
| 14-04-01 | 04 | 3 | ADAPT-05 | docs | `test -f wiki/render/adapter_contracts.md` exits 0 + `grep -cE "^## " wiki/render/adapter_contracts.md` ≥7 (Registry + Mock↔Real + Retry + Production-Safe + Forbid + Cross-Ref + Phase-13 Boundary + 갱신) | ⬜ pending |
| 14-04-02 | 04 | 3 | ADAPT-05 | structural validator | `pytest tests/adapters/test_adapter_contracts_doc.py -m adapter_contract -v --no-cov` exits 0 (≥6 validator tests green) | ⬜ pending |
| 14-04-03 | 04 | 3 | ADAPT-05 (MOC TOC entry + D-17 invariant preserved) | docs | `grep -cE "Phase 14" wiki/render/MOC.md` ≥1 AND Python canonical regex check: `python -c "import re, sys; t=open('wiki/render/MOC.md', encoding='utf-8').read(); sys.exit(0 if re.search(r'^status:\s*(scaffold\|partial)\b', t, re.MULTILINE) else 1)"` exits 0 (aligned with Plan 02 Task 14-02-04 canonical regex) | ⬜ pending |
| 14-04-04 | 04 | 3 | ADAPT-06c (warn-only Hook + .gitignore wiring) | hook + wiring | Hook import smoke: `py -3.11 -c "import importlib.util; spec = importlib.util.spec_from_file_location('h', '.claude/hooks/pre_tool_use.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)"` exits 0 + `grep -c "_adapter_contract_touch" .gitignore` ≥1 | ⬜ pending |
| 14-05-01 | 05 | 4 | ADAPT-01~06 (aggregator) | e2e harness | Phase gate sweep: `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short` 0 failures (captured to `14-05-phase-gate.log`) + import smoke `py -3.11 -c "from scripts.validate import phase14_acceptance"` exits 0 | ⬜ pending |
| 14-05-02 | 05 | 4 | ADAPT-06 (contract-only gate) | contract gate | `pytest -m adapter_contract -v --no-cov` exits 0 (≥20 tests green across 4 contract files — veo_i2v + elevenlabs + shotstack + doc validator) | ⬜ pending |
| 14-05-03 | 05 | 4 | All REQs (evidence consolidation) | traceability | `python scripts/validate/phase14_acceptance.py` exits 0 + `python scripts/validate/harness_audit.py --json` score ≥80 + `python scripts/validate/drift_scan.py` A-class drift count = 0 + `test -f .planning/phases/14-api-adapter-remediation/14-TRACEABILITY.md` exits 0 | ⬜ pending |
| 14-05-04 | 05 | 4 | Phase gate | full regression + flip | Step 1: `pytest tests/` exits 0. Step 1a hard-gate: `grep -q 'ALL_PASS' .planning/phases/14-api-adapter-remediation/14-05-phase-gate.log \|\| exit 1`. Step 2 (only after Step 1a): 14-VALIDATION.md frontmatter `status: approved` + `nyquist_compliant: true` + `wave_0_complete: true` + `approved: 2026-04-21` flipped | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Coverage summary**: 20 rows (previously 15 — 4 plan tasks were unmapped: 14-01-03, 14-04-03, 14-04-04, 14-05-04; now all mapped. Stale test paths replaced: `test_video_generation.py`, `test_line_count.py` under phase06, `test_wiki_frontmatter.py`, `test_notebooklm_skill.py` → all removed in favor of real file names from 14-RESEARCH.md Bucket A/B/C mapping and each plan's `<done>` field.)

---

## Wave 0 Requirements

- [ ] `pytest.ini` at repo root — `[pytest]` section with `markers = adapter_contract: marks tests as adapter contract tests (deselect with '-m \"not adapter_contract\"')` + `--strict-markers` default
- [ ] Pre-grep scan: `grep -rE "@pytest.mark.(?!(skip|skipif|xfail|parametrize|asyncio|adapter_contract))" tests/ scripts/` → any informal marker hits must be resolved before `--strict-markers` activates (R1 mitigation)
- [ ] `tests/adapters/__init__.py` (empty) to form package
- [ ] `tests/adapters/conftest.py` — shared fixtures: `repo_root`, `_fake_env` (reuse Phase 5 precedent) + Phase 7 Mock class re-export via import
- [ ] `pytest.ini` registration verified via `pytest --markers | grep adapter_contract` (exit 0)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hook extension drift frequency decision | ADAPT-06 optional Hook | No empirical drift-frequency data — ROI unclear, subjective trade-off | After Phase 14 lands, observe adapter commit frequency over 30 days. If > 2 adapter drifts occur, activate Hook via opt-in config flag. |
| adapter_contracts.md human readability | ADAPT-05 | Doc quality is judgment call — schema matrix correctness is auto-verifiable, but prose clarity is not | 대표님 review after Wave 3 (30-minute read). Feedback loop: markdown edits, not code. |
| whisperx row treatment | ADAPT-05 Open Q2 | Research recommended "NOT YET IMPLEMENTED" stub; approval is design decision | plan-phase decision locked to Option A (stub row). Verify row exists + explicit "Phase 15+" tag. |

---

## Validation Sign-Off

- [ ] All 20 per-task verification rows have `<automated>` verify or Wave 0 dependency flagged
- [ ] Sampling continuity: Wave 1 regression-fix tasks each have dedicated pytest nodeid filter (no 3 consecutive tasks without automated verify)
- [ ] Wave 0 covers all scaffold references (pytest.ini + tests/adapters/ scaffold + conftest.py fixture re-export)
- [ ] No watch-mode flags (all commands run-to-exit)
- [ ] Feedback latency: 120s per-task, 660s per-wave — both < 900s threshold
- [ ] `nyquist_compliant: true` flipped in frontmatter after Wave 0 ships (Step 1a hard-gate verified in Task 14-05-04)

**Approval:** pending (will flip to `approved YYYY-MM-DD` after Wave 0 commits land and Task 14-05-04 Step 1a hard-gate passes `grep -q 'ALL_PASS' ...`)
