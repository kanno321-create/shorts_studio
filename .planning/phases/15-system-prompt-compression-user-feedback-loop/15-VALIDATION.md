---
phase: 15
slug: system-prompt-compression-user-feedback-loop
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-22
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Derived from 15-RESEARCH.md §Validation Architecture.

**핵심 전략**: Two-tier preserved from Phase 13
- **Tier 1 (always-run)**: SPC-01~05 + UFL all mock-based encoding + pipeline state tests
- **Tier 2 (opt-in)**: SPC-06 live smoke retry — `pytest -m live_smoke --run-live`

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Phase 14 pytest.ini + Phase 13 live_smoke marker 상속) |
| **Quick (always-run)** | `pytest tests/phase15 -m "not live_smoke" --tb=short -q` (≈ 15s 예상) |
| **Live smoke retry** | `pytest tests/phase15 -m live_smoke --run-live --tb=long -v --no-cov` (≈ 20-30 min, ~$1.50-$3.00) |
| **Phase 13/14 baseline** | `pytest tests/phase13 tests/adapters/ -m "not live_smoke" --no-cov -q` (60 + 30 = 90 passed preserved) |
| **Full gate** | `python scripts/validate/phase15_acceptance.py` |

---

## Sampling Rate

- **Per task commit**: Tier 1 subset for touched module
- **Per wave**: phase15 Tier 1 full + Phase 13/14 baseline regression (90 tests)
- **Phase gate**: `pytest -m "not live_smoke"` 전수 green + `pytest -m adapter_contract` 30 preserved
- **Live retry**: Wave 5 SPC-06 단 1회 (대표님 승인 지점)

---

## Per-Task Verification Map (draft — planner 가 확정)

| Task ID | Plan | Wave | Requirement | Test Type | Command | Status |
|---------|------|------|-------------|-----------|---------|:-:|
| 15-01-01 | 01 | 0 | SPC-01 | reproducer | `pytest tests/phase15/test_encoding_repro.py` 재현 시나리오 확정 | ⬜ |
| 15-02-01 | 02 | 1 | SPC-01 | invoker fix | `pytest tests/adapters/test_invokers_encoding_contract.py` green | ⬜ |
| 15-02-02 | 02 | 1 | SPC-05 | contract | 10KB+ Korean body mock subprocess green | ⬜ |
| 15-03-01 | 03 | 2 | SPC-02 | agent split | supervisor AGENT.md ≤ 6500 chars + references/ 2 files + AGENT-STD schema 31/31 | ⬜ |
| 15-03-02 | 03 | 2 | SPC-03 | size audit | `verify_agent_md_size.py` producer 14 + supervisor 1 ≤ CHAR_LIMIT | ⬜ |
| 15-03-03 | 03 | 2 | SPC-04 | CLI option | Claude CLI `--append-system-prompt-file` empirical verify (non-existent file → proper error) | ⬜ |
| 15-04-01 | 04 | 3 | UFL-01 | revision | `--revision-from SCRIPT --feedback "hook weak"` 테스트 | ⬜ |
| 15-04-02 | 04 | 3 | UFL-02 | script inject | `--revise-script path.md` 주입 + script-polisher 경로 | ⬜ |
| 15-04-03 | 04 | 3 | UFL-03 | pause | `--pause-after VOICE` 중단 + resume 확인 | ⬜ |
| 15-05-01 | 05 | 4 | UFL-04 | rating CLI | `rate_video.py --video-id X --rating 3 --feedback "조명 어두움"` → feedback_video_quality.md append | ⬜ |
| 15-06-01 | 06 | 5 | SPC-06 | live retry | `phase13_live_smoke.py --live --topic "해외범죄,..." --niche incidents` 13 gate 전수 dispatched + video_id + cleanup | ⬜ |
| 15-07-01 | 07 | 6 | All SC | acceptance | `phase15_acceptance.py` ALL_PASS + 15-TRACEABILITY.md + VALIDATION flip | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] `tests/phase15/__init__.py` + `conftest.py` (Phase 13/14 fixture 승계)
- [ ] `tests/phase15/test_encoding_repro.py` — SPC-01 empirical 재현
- [ ] Claude CLI `--append-system-prompt-file` empirical verify

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 대표님 실 과금 SPC-06 승인 | SPC-06 live retry | Budget $5 cap + 48h publish_lock | Wave 5 실행 전 대표님 명시 승인 |
| `--revise-script` 대본 품질 검토 | UFL-02 | AI 가 평가할 수 없는 대본 미학 | UFL-02 Task 완료 후 sample 대본 1편으로 대표님 수동 검증 |
| `rate_video.py` rating 의미 validation | UFL-04 | subjective rating 체계가 researcher 에이전트에 올바르게 전파되는지 | Wave 4 완료 후 rating 1회 입력 → 다음 Wave 5 live run 의 researcher prompt 에 반영 확인 |

---

## Validation Sign-Off

- [ ] 12 per-task verification rows 모두 automated or manual 지정
- [ ] Tier 1 / Tier 2 분리 준수 — 매 commit 시 실 과금 trigger 없음
- [ ] Wave 0 requirements 충족
- [ ] Phase 13/14 baseline 90 tests 보존 (60 phase13 + 30 phase14)
- [ ] `nyquist_compliant: true` flip (Wave 0 완료 후)

**Approval**: pending
