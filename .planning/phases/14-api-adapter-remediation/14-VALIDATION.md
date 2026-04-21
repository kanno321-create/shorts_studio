---
phase: 14
slug: api-adapter-remediation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-21
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

- **After every task commit:** Run Phase-scoped quick subset (e.g., only `tests/phase05/test_video_generation.py` for ADAPT-01 task A)
- **After every plan wave:** Run `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short -q` (must show 15→N failures monotonically decreasing)
- **Before phase gate:** Full suite + `pytest -m adapter_contract` both green
- **Max feedback latency:** 120s (quick per-task) / 660s (wave boundary)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | ADAPT-06 | infra | `pytest --markers \| grep adapter_contract` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 0 | ADAPT-01/02/03 | infra | `test -d tests/adapters && ls tests/adapters/__init__.py` | ❌ W0 | ⬜ pending |
| 14-02-01 | 02 | 1 | ADAPT-04 (veo_i2v fixes) | regression | `pytest tests/phase05/test_video_generation.py -k veo_i2v --tb=short` | ✅ | ⬜ pending |
| 14-02-02 | 02 | 1 | ADAPT-04 (runway gen4.5) | regression | `pytest tests/phase05/test_video_generation.py -k runway --tb=short` | ✅ | ⬜ pending |
| 14-02-03 | 02 | 1 | ADAPT-04 (line caps 340→360) | regression | `pytest tests/phase05/test_line_count.py --tb=short` | ✅ | ⬜ pending |
| 14-02-04 | 02 | 1 | ADAPT-04 (line caps 400→420) | regression | `pytest tests/phase06/test_line_count.py --tb=short` | ✅ | ⬜ pending |
| 14-02-05 | 02 | 1 | ADAPT-04 (MOC status invariant) | regression | `pytest tests/phase06/test_wiki_frontmatter.py --tb=short` | ✅ | ⬜ pending |
| 14-02-06 | 02 | 1 | ADAPT-04 (notebooklm skill path) | regression | `pytest tests/phase06/test_notebooklm_skill.py --tb=short` | ✅ | ⬜ pending |
| 14-03-01 | 03 | 2 | ADAPT-01 | contract | `pytest tests/adapters/test_veo_i2v_contract.py` | ❌ W0 | ⬜ pending |
| 14-03-02 | 03 | 2 | ADAPT-02 | contract | `pytest tests/adapters/test_elevenlabs_contract.py` | ❌ W0 | ⬜ pending |
| 14-03-03 | 03 | 2 | ADAPT-03 | contract | `pytest tests/adapters/test_shotstack_contract.py` | ❌ W0 | ⬜ pending |
| 14-04-01 | 04 | 3 | ADAPT-05 | docs | `test -f wiki/render/adapter_contracts.md && grep -c '^## [A-Za-z]' wiki/render/adapter_contracts.md` (≥7) | ❌ W0 | ⬜ pending |
| 14-04-02 | 04 | 3 | ADAPT-06 (optional Hook) | hook | `.claude/hooks/pre_tool_use.py adapter scan (if opted in)` | N/A | ⬜ pending |
| 14-05-01 | 05 | 4 | ADAPT-04 (gate) | e2e regression | `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short` (0 failures) | ✅ | ⬜ pending |
| 14-05-02 | 05 | 4 | ADAPT-06 (gate) | contract gate | `pytest -m adapter_contract` (all green) | ✅ | ⬜ pending |
| 14-05-03 | 05 | 4 | Full regression | full suite | `pytest tests/` (exit 0) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pytest.ini` at repo root — `[pytest]` section with `markers = adapter_contract: marks tests as adapter contract tests (deselect with '-m \"not adapter_contract\"')` + `--strict-markers` default
- [ ] Pre-grep scan: `grep -rE "@pytest.mark.(?!(skip|skipif|xfail|parametrize|asyncio|adapter_contract))" tests/ scripts/` → any informal marker hits must be resolved before `--strict-markers` activates (R1 mitigation)
- [ ] `tests/adapters/__init__.py` (empty) to form package
- [ ] `tests/adapters/conftest.py` — shared fixtures: mock_kling / mock_runway / mock_veo_i2v / mock_elevenlabs / mock_shotstack / mock_typecast / mock_whisperx (reuse Phase 7 MockX classes via import)
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

- [ ] All 15 per-task verification rows have `<automated>` verify or Wave 0 dependency flagged
- [ ] Sampling continuity: Wave 1 regression-fix tasks each have dedicated pytest -k filter (no 3 consecutive tasks without automated verify)
- [ ] Wave 0 covers all ❌ W0 references (pytest.ini + tests/adapters/ scaffold)
- [ ] No watch-mode flags (all commands run-to-exit)
- [ ] Feedback latency: 120s per-task, 660s per-wave — both < 900s threshold
- [ ] `nyquist_compliant: true` flipped in frontmatter after Wave 0 ships

**Approval:** pending (will flip to `approved YYYY-MM-DD` after Wave 0 commits land)
