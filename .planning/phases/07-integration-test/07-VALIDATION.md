---
phase: 7
slug: integration-test
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-04-19
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Generated from 07-RESEARCH.md §Validation Architecture (20 dimensions).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (Phase 5/6 baseline 승계) |
| **Config file** | `pytest.ini` (기존) — Phase 7 test dir `tests/phase07/` 추가 |
| **Quick run command** | `python -m pytest tests/phase07/ -q --no-cov` |
| **Full suite command** | `python -m pytest tests/ -q --no-cov` |
| **Estimated runtime** | ~15s (Phase 4 244 + Phase 5 329 + Phase 6 236 ~68s baseline + Phase 7 예상 40~60 tests ~10s) |
| **Regression baseline** | 809/809 green (Phase 4 244 + Phase 5 329 + Phase 6 236, 2026-04-19 실측) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase07/<affected_test>.py -q --no-cov`
- **After every plan wave:** Run `python -m pytest tests/phase07/ -q --no-cov` + sweep `pytest tests/phase04 tests/phase05 tests/phase06 -q --no-cov`
- **Before `/gsd:verify-work`:** 809 baseline + Phase 7 전체 PASS + `scripts/validate/phase07_acceptance.py` exit 0
- **Max feedback latency:** 15s

---

## Per-Task Verification Map (20 dimensions)

| Row | Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|-----|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1   | 7-01-01 | 01 | 0 | TEST-01 | scaffold | `pytest tests/phase07/test_infra_smoke.py -q` | ✅ | ✅ green |
| 2   | 7-01-02 | 01 | 0 | TEST-01 | unit | `pytest tests/phase07/test_mock_fixtures_bytes.py -q` | ✅ | ✅ green |
| 3   | 7-02-01 | 02 | 1 | TEST-01 | unit | `pytest tests/phase07/test_mock_kling_adapter.py -q` | ✅ | ✅ green |
| 4   | 7-02-02 | 02 | 1 | TEST-01 | unit | `pytest tests/phase07/test_mock_runway_adapter.py -q` | ✅ | ✅ green |
| 5   | 7-02-03 | 02 | 1 | TEST-01 | unit | `pytest tests/phase07/test_mock_typecast_adapter.py -q` | ✅ | ✅ green |
| 6   | 7-02-04 | 02 | 1 | TEST-01 | unit | `pytest tests/phase07/test_mock_elevenlabs_adapter.py -q` | ✅ | ✅ green |
| 7   | 7-02-05 | 02 | 1 | TEST-01 | unit | `pytest tests/phase07/test_mock_shotstack_adapter.py -q` | ✅ | ✅ green |
| 8   | 7-03-01 | 03 | 2 | TEST-01 | E2E | `pytest tests/phase07/test_e2e_happy_path.py -q` | ✅ | ✅ green |
| 9   | 7-03-02 | 03 | 2 | TEST-01 | integration | `pytest tests/phase07/test_notebooklm_tier2_only.py -q` | ✅ | ✅ green |
| 10  | 7-04-01 | 04 | 2 | TEST-02 | unit | `pytest tests/phase07/test_operational_gate_count_equals_13.py -q` | ✅ | ✅ green |
| 11  | 7-04-02 | 04 | 2 | TEST-02 | integration | `pytest tests/phase07/test_verify_all_dispatched_13.py -q` | ✅ | ✅ green |
| 12  | 7-04-03 | 04 | 2 | TEST-02 | unit | `pytest tests/phase07/test_gate_order_violation.py -q` | ✅ | ✅ green |
| 13  | 7-04-04 | 04 | 2 | TEST-02 | integration | `pytest tests/phase07/test_checkpointer_atomic_writes_13.py -q` | ✅ | ✅ green |
| 14  | 7-05-01 | 05 | 3 | TEST-03 | unit | `pytest tests/phase07/test_circuit_breaker_3x_open.py -q` | ✅ | ✅ green |
| 15  | 7-05-02 | 05 | 3 | TEST-03 | integration | `pytest tests/phase07/test_cooldown_300s_enforced.py -q` | ✅ | ✅ green |
| 16  | 7-06-01 | 06 | 3 | TEST-04 | integration | `pytest tests/phase07/test_fallback_ken_burns_thumbnail.py -q` | ✅ | ✅ green |
| 17  | 7-06-02 | 06 | 3 | TEST-04 | integration | `pytest tests/phase07/test_failures_append_on_retry_exceeded.py -q` | ✅ | ✅ green |
| 18  | 7-07-01 | 07 | 4 | AUDIT-02 | CLI | `python scripts/validate/harness_audit.py --json-out` | ✅ | ✅ green |
| 19  | 7-07-02 | 07 | 4 | AUDIT-02 | unit | `pytest tests/phase07/test_harness_audit_json_schema.py -q` | ✅ | ✅ green |
| 20  | 7-07-03 | 07 | 4 | AUDIT-02 | unit | `pytest tests/phase07/test_harness_audit_score_ge_80.py -q` | ✅ | ✅ green |
| 21  | 7-07-04 | 07 | 4 | AUDIT-02 | unit | `pytest tests/phase07/test_skill_500_line_scan.py -q` | ✅ | ✅ green |
| 22  | 7-08-01 | 08 | 5 | ALL | E2E | `python scripts/validate/phase07_acceptance.py` | ❌ W0 | ⬜ pending |
| 23  | 7-08-02 | 08 | 5 | ALL | unit | `pytest tests/phase07/test_traceability_matrix.py -q` | ❌ W0 | ⬜ pending |
| 24  | 7-08-03 | 08 | 5 | ALL | regression | `pytest tests/phase04 tests/phase05 tests/phase06 -q` | ✅ | ⬜ pending |
| 25  | 7-01-03 | 01 | 0 | TEST-01 | regression | `pytest tests/phase04 tests/phase05 tests/phase06 -q` (Wave 0 baseline sweep) | ✅ | ✅ green |
| 26  | 7-07-05 | 07 | 4 | AUDIT-02 | unit | `pytest tests/phase07/test_agent_count_invariant.py -q` | ✅ | ✅ green |
| 27  | 7-07-06 | 07 | 4 | AUDIT-02 | unit | `pytest tests/phase07/test_description_1024_scan.py -q` | ✅ | ✅ green |
| 28  | 7-07-04b | 07 | 4 | AUDIT-02 | unit | `pytest tests/phase07/test_a_rank_drift_zero.py -q` (D-12 drift gate; plan-checker M3 flagged missing row) | ✅ | ✅ green |

*Status legend: `pending` (not yet run) · `✅ green` (all tests passing) · `❌ red` (failing) · `⚠️ flaky` (intermittent)*

---

## Wave 0 Requirements

Wave 0은 Phase 7 실행의 최초 wave (Plan 01 — scaffold + mock fixtures base). 필요 인프라:

- [x] `tests/phase07/__init__.py` — package marker (Plan 07-01 ✅ shipped 2026-04-19)
- [x] `tests/phase07/conftest.py` — 공유 fixture (_fake_env + tmp_session_id + mock_pass_verdict + mock_fail_verdict + repo_root + phase07_fixtures, 93 lines, D-13 independent) (Plan 07-01 ✅)
- [x] `tests/phase07/fixtures/` — `mock_kling.mp4` + `mock_runway.mp4` + `mock_typecast.wav` + `mock_elevenlabs.wav` + `mock_shotstack.mp4` + `still_image.jpg` (모두 0-byte placeholder per Don't Hand-Roll) (Plan 07-01 ✅)
- [x] `tests/phase07/mocks/` — MockKlingI2V + MockRunwayI2V + MockTypecast + MockElevenLabs + MockShotstack (fault-injection capable) [Plan 07-02 Wave 1] (Plan 07-02 ✅ shipped 2026-04-19)
- [ ] `scripts/validate/phase07_acceptance.py` — SC 1-5 E2E wrapper (Phase 5/6 acceptance.py 패턴 승계) [Plan 07-08 Wave 5]
- [x] `scripts/validate/harness_audit.py --json-out` 플래그 추가 (기존 text 출력 backward-compatible) (Plan 07-01 ✅ — D-11 6-key schema emission)

*Wave 0 완료 조건: Plan 01 완료 시 `wave_0_complete: true` flip*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 실 API 실호출 smoke test (1건 per adapter) | TEST-01 | Phase 7 범위 외 (mock-only 원칙 D-1) | Phase 8 `scripts/validate/smoke_test_real_apis.py` 신규 작성 예정. 각 adapter별 < $1 비용 smoke test. |
| NotebookLM tier 0 RAG 실호출 경로 | - | Phase 7 tier 2 고정 (D-15) | Phase 8 온라인 활성화 후 `scripts/notebooklm/smoke_rag.py` 실행 |
| Continuity 시각 일관성 3편 연속 실 렌더 비교 | SC #4 (Phase 6) | mock 기반은 타임라인 JSON까지만 검증. 실 픽셀 비교는 실 렌더 필요 | Phase 8 `scripts/validate/visual_continuity_check.py` 신규. KOMCA/저작권 준수도 함께 확인. |
| harness-audit 월 1회 cron 실행 | AUDIT-02 (Phase 10) | Phase 7은 1회 실행 증명까지만 | Phase 10 `crontab -e` 설치 가이드 + `scripts/audit/monthly_harness_audit.sh` 작성 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (20 rows sequential — 매 task 자동 검증 가능)
- [ ] Wave 0 covers all MISSING references (tests/phase07/ infrastructure + scripts/validate/phase07_acceptance.py + harness_audit.py --json-out 확장)
- [ ] No watch-mode flags (모든 pytest 호출은 one-shot; `-f` / `--looponfail` 금지)
- [ ] Feedback latency < 15s (Phase 7 단독 ~10s + regression sweep ~68s = 한 wave당 최대 ~80s, task 개별은 < 5s)
- [ ] `nyquist_compliant: true` set in frontmatter (Phase 7 gate 완료 시 flip)

**Approval:** pending
