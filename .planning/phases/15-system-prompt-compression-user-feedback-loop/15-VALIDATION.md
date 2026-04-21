---
phase: 15
slug: system-prompt-compression-user-feedback-loop
status: draft
nyquist_compliant: false
wave_0_complete: true
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

## Per-Task Verification Map (revised — 14 rows)

| Task ID | Plan | Wave | Requirement | Test Type | Command | Status |
|---------|------|------|-------------|-----------|---------|:-:|
| 15-01-01 | 01 | 0 | SPC-01 | reproducer | `pytest tests/phase15/test_encoding_repro.py` 재현 시나리오 확정 | ✅ |
| 15-02-01 | 02 | 1 | SPC-01 | invoker fix | `pytest tests/adapters/test_invokers_encoding_contract.py` green | ✅ |
| 15-02-02 | 02 | 1 | SPC-05 | contract | 10KB+ Korean body mock subprocess green | ✅ |
| 15-03-01 | 03 | 2 | SPC-02 | agent split | supervisor AGENT.md ≤ 6500 chars + references/ 2 files + AGENT-STD schema 31/31 | ⬜ |
| 15-03-02 | 03 | 2 | SPC-03 | size audit | `verify_agent_md_size.py` producer 14 + supervisor 1 ≤ CHAR_LIMIT | ⬜ |
| 15-03-03 | 03 | 2 | SPC-04 | CLI option | Claude CLI `--append-system-prompt-file` empirical verify (non-existent file → proper error) | ⬜ |
| 15-04-00 | 04 | 3 | UFL-01/02/03 | evidence isolation | `grep -c "evidence-dir" scripts/smoke/phase13_live_smoke.py` ≥ 2 + `--help` 노출 | ⬜ |
| 15-04-01 | 04 | 3 | UFL-01 | revision | `--revision-from SCRIPT --feedback "hook weak"` 테스트 + Phase 12 compression verdict preserve | ⬜ |
| 15-04-02 | 04 | 3 | UFL-02 | script inject | `--revise-script path.md` 주입 + script-polisher 경로 | ⬜ |
| 15-04-03 | 04 | 3 | UFL-03 | pause | `--pause-after VOICE` 중단 + GateGuard ctx_config by-reference + Verdict dataclass + Phase 5/9.1 regression | ⬜ |
| 15-05-01 | 05 | 4 | UFL-04 | rating CLI | `rate_video.py --video-id X --rating 3 --feedback "조명 어두움"` → feedback_video_quality.md append | ⬜ |
| 15-05-02 | 05 | 4 | UFL-04 | format validator | `pytest tests/phase15/test_feedback_format.py` 4 passed + `verify_feedback_format.py` exit 0 | ⬜ |
| 15-05-03 | 05 | 4 | UFL-04 | researcher mandatory_reads | `grep feedback_video_quality .claude/agents/producers/researcher/AGENT.md` + `verify_agent_md_schema.py --fail-on-drift` 31/31 + `verify_mandatory_reads_prose.py` 31/31 | ⬜ |
| 15-06-01 | 06 | 5 | SPC-06 | live retry | `phase13_live_smoke.py --live --topic "해외범죄,..." --niche incidents` 13 gate 전수 dispatched + video_id + cleanup | ⬜ |
| 15-07-01 | 07 | 6 | All SC | acceptance | `phase15_acceptance.py` ALL_PASS + 15-TRACEABILITY.md + VALIDATION flip | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red*

**Coverage summary**: 14 automated rows + 1 acceptance aggregator = 15 total verification anchors. Plan 15-04 splits into 4 sub-tasks (00 evidence-dir + 01 UFL-01 + 02 UFL-02 + 03 UFL-03). Plan 15-05 splits into 3 sub-tasks (01 rate_video + 02 format validator + 03 researcher mandatory_reads).

---

## Wave 0 Requirements

- [x] `tests/phase15/__init__.py` + `conftest.py` (Phase 13/14 fixture 승계)
- [x] `tests/phase15/test_encoding_repro.py` — SPC-01 empirical 재현
- [x] Claude CLI `--append-system-prompt-file` empirical verify

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 대표님 실 과금 SPC-06 승인 | SPC-06 live retry | Budget $5 cap + 48h publish_lock | Wave 5 실행 전 대표님 명시 승인 |
| `--revise-script` 대본 품질 검토 | UFL-02 | AI 가 평가할 수 없는 대본 미학 | UFL-02 Task 완료 후 sample 대본 1편으로 대표님 수동 검증 |
| `rate_video.py` rating 의미 validation | UFL-04 | subjective rating 체계가 researcher 에이전트에 올바르게 전파되는지 | Wave 4 완료 후 rating 1회 입력 → 다음 Wave 5 live run 의 researcher prompt 에 반영 확인 |

---

## Validation Sign-Off

- [ ] 14 per-task verification rows 모두 automated or manual 지정
- [ ] Tier 1 / Tier 2 분리 준수 — 매 commit 시 실 과금 trigger 없음
- [ ] Wave 0 requirements 충족
- [ ] Phase 13/14 baseline 90 tests 보존 (60 phase13 + 30 phase14)
- [ ] `nyquist_compliant: true` flip (Wave 0 완료 후)

**Approval**: pending
