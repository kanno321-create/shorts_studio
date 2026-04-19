---
phase: 5
slug: orchestrator-v2-write
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
completed: 2026-04-19
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from 05-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (already installed) |
| **Config file** | `pyproject.toml` (existing, Phase 4에서 설정됨) |
| **Quick run command** | `python -m pytest tests/phase05/ -q --no-cov` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~3~6 seconds (unit+integration mocked), ~15s with regression |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase05/<plan_dir>/ -q`
- **After every plan wave:** Run `python -m pytest tests/phase05/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green + line count verify + grep blacklist verify + hook mock verify all PASS
- **Max feedback latency:** 6 seconds (unit only); 20 seconds (full phase05)

---

## Per-Task Verification Map

Mapping of Plans × Test Files × REQ IDs × Success Criteria.

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 infra | W0 | ORCH-08, ORCH-09 | contract | `python -m pytest tests/phase05/test_deprecated_patterns_json.py -q` | ✅ on disk | ✅ green |
| 05-01-02 | 01 infra | W0 | ORCH-02 | unit | `python -m pytest tests/phase05/test_gate_enum.py -q` | ✅ on disk | ✅ green |
| 05-01-03 | 01 infra | W0 | ORCH-03 | unit | `python -m pytest tests/phase05/test_exceptions.py -q` | ✅ on disk | ✅ green |
| 05-01-04 | 01 infra | W0 | ORCH-07 | unit | `python -m pytest tests/phase05/test_dag_declaration.py -q` | ✅ on disk | ✅ green |
| 05-02-01 | 02 circuit_breaker | W1 | ORCH-06 | unit | `python -m pytest tests/phase05/test_circuit_breaker.py -q` | ✅ on disk | ✅ green |
| 05-02-02 | 02 circuit_breaker | W1 | ORCH-06 | integration (mock time) | `python -m pytest tests/phase05/test_circuit_breaker_cooldown.py -q` | ✅ on disk | ✅ green |
| 05-03-01 | 03 checkpointer | W1 | ORCH-05 | unit | `python -m pytest tests/phase05/test_checkpointer_roundtrip.py -q` | ✅ on disk | ✅ green |
| 05-03-02 | 03 checkpointer | W1 | ORCH-05 | unit | `python -m pytest tests/phase05/test_checkpointer_resume.py -q` | ✅ on disk | ✅ green |
| 05-04-01 | 04 gate_guard | W1 | ORCH-03, ORCH-04 | unit | `python -m pytest tests/phase05/test_gate_guard.py -q` | ✅ on disk | ✅ green |
| 05-04-02 | 04 gate_guard | W1 | ORCH-04 | unit | `python -m pytest tests/phase05/test_verify_all_dispatched.py -q` | ✅ on disk | ✅ green |
| 05-05-01 | 05 voice_first_timeline | W2 | ORCH-10, VIDEO-02, VIDEO-03 | unit | `python -m pytest tests/phase05/test_voice_first_timeline.py -q` | ✅ on disk | ✅ green |
| 05-05-02 | 05 voice_first_timeline | W2 | VIDEO-03 | unit | `python -m pytest tests/phase05/test_transition_shots.py -q` | ✅ on disk | ✅ green |
| 05-06-01 | 06 api_adapters | W3 | VIDEO-01, VIDEO-04 | unit | `python -m pytest tests/phase05/test_kling_adapter.py -q` | ✅ on disk | ✅ green |
| 05-06-02 | 06 api_adapters | W3 | VIDEO-04 | integration (mock) | `python -m pytest tests/phase05/test_kling_runway_failover.py -q` | ✅ on disk | ✅ green |
| 05-06-03 | 06 api_adapters | W3 | ORCH-10 | unit | `python -m pytest tests/phase05/test_typecast_adapter.py -q` | ✅ on disk | ✅ green |
| 05-06-04 | 06 api_adapters | W3 | ORCH-10 | unit | `python -m pytest tests/phase05/test_elevenlabs_adapter.py -q` | ✅ on disk | ✅ green |
| 05-06-05 | 06 api_adapters | W3 | ORCH-11, VIDEO-05 | unit | `python -m pytest tests/phase05/test_shotstack_adapter.py -q` | ✅ on disk | ✅ green |
| 05-07-01 | 07 pipeline | W4 | ORCH-01, ORCH-02 | unit | `python -m pytest tests/phase05/test_shorts_pipeline.py -q` | ✅ on disk | ✅ green |
| 05-07-02 | 07 pipeline | W4 | ORCH-07, ORCH-12 | integration (mock) | `python -m pytest tests/phase05/test_pipeline_e2e_mock.py -q` | ✅ on disk | ✅ green |
| 05-07-03 | 07 pipeline | W4 | ORCH-12 | unit | `python -m pytest tests/phase05/test_fallback_shot.py -q` | ✅ on disk | ✅ green |
| 05-07-04 | 07 pipeline | W4 | ORCH-11, VIDEO-05 | unit | `python -m pytest tests/phase05/test_low_res_first.py -q` | ✅ on disk | ✅ green |
| 05-08-01 | 08 hc_checks | W5 | ORCH-01 (regression) | regression | `python -m pytest tests/phase05/test_hc_checks_regression.py -q` | ✅ on disk | ✅ green |
| 05-08-02 | 08 hc_checks | W5 | ORCH-03 integration | unit | `python -m pytest tests/phase05/test_hc_checks_gate_integration.py -q` | ✅ on disk | ✅ green |
| 05-09-01 | 09 hook_extensions | W5 | ORCH-08, ORCH-09 | contract | `python scripts/validate/verify_hook_blocks.py` | ✅ on disk | ✅ green |
| 05-09-02 | 09 hook_extensions | W5 | VIDEO-01 | contract | `python -m pytest tests/phase05/test_hook_t2v_block.py -q` | ✅ on disk | ✅ green |
| 05-10-01 | 10 verification | W6 | SC 1 | contract | `python scripts/validate/verify_line_count.py scripts/orchestrator/shorts_pipeline.py 500 800` | ✅ on disk | ✅ green |
| 05-10-02 | 10 verification | W6 | SC 2 | contract (grep) | `! grep -rq "skip_gates" scripts/orchestrator/` | ✅ on disk | ✅ green |
| 05-10-03 | 10 verification | W6 | SC 5 (T2V 부재) | contract (grep) | `! grep -rqiE "t2v\|text_to_video\|text2video" scripts/orchestrator/` | ✅ on disk | ✅ green |
| 05-10-04 | 10 verification | W6 | SC 1~6 (전체) | E2E contract | `python scripts/validate/phase05_acceptance.py` | ✅ on disk | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

**tests/phase05/ 디렉토리 구조 생성 (Wave 0 Plan 01에서 처리):**

- [ ] `tests/phase05/__init__.py` — 디렉토리 마커
- [ ] `tests/phase05/conftest.py` — 공유 fixtures (mock session_id, tmp state dir, mock rubric verdicts)
- [ ] `tests/phase05/fixtures/` — 샘플 JSON (verdict_pass.json, verdict_fail.json, mock_audio_timestamps.json)
- [ ] `scripts/validate/verify_line_count.py` — 줄수 범위 검증
- [ ] `scripts/validate/verify_hook_blocks.py` — Hook regex 차단 실증 스크립트
- [ ] `scripts/validate/phase05_acceptance.py` — SC 1~6 전체 계약 검증
- [ ] `.claude/deprecated_patterns.json` — **중요**: Hook regex 패턴 파일 (RESEARCH에서 발견된 부재. ORCH-08/09 차단의 실질 source)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 720p → AI 업스케일 시각 품질 | ORCH-11 | Shotstack 업스케일 스코프 Phase 8 이관 결정(RESEARCH Open Q3) | Phase 5 단계에서는 720p 렌더 + documented deferral만 검증. 업스케일 시각 품질은 Phase 8에서 평가 |
| Kling 2.6 Pro 실 API 호출 성공 | VIDEO-04 | 실 API 키 + 크레딧 소모 | Phase 7 (Integration Test) + Phase 8 (Production)에서 실측 |
| 실제 영상 렌더 결과 | ORCH-10 | Shotstack composite 출력 대형 파일 | Phase 7 E2E에서 mock asset으로 구조 검증 → Phase 8 실 렌더 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (conftest.py, fixtures, deprecated_patterns.json, validate scripts)
- [x] No watch-mode flags
- [x] Feedback latency < 6s (unit) / 20s (full)
- [x] `nyquist_compliant: true` set in frontmatter (flipped 2026-04-19 by Plan 05-10 after all 29 task rows green + `phase05_acceptance.py` exits 0)

**Approval:** complete — 2026-04-19 (Plan 05-10 Wave 7)

---

## Completion Summary

**Phase 5 closed 2026-04-19 by Plan 05-10 Wave 7 (final verification).**

### Plans
- **Completed:** 10 / 10 (01 → 10)
- **Waves:** 7 (W1 infra → W2 support modules → W3 voice-first → W4 API adapters → W5 pipeline keystone → W6 hc_checks + Hook regression parallel → W7 SC acceptance)

### Tests Green
- **Total tests/phase05/:** 329 passing (224 Wave 5 baseline + 41 Plan 08 regression + 31 Plan 09 Hook + 33 Plan 10 verification)
- **Full pytest sweep:** `python -m pytest tests/phase05/ -q --no-cov` exits 0
- **Acceptance script:** `python scripts/validate/phase05_acceptance.py` exits 0 with all 6 SC reporting PASS
- **Hook verifier:** `python scripts/validate/verify_hook_blocks.py` exits 0 (5 hook enforcement checks green)

### Success Criteria

| SC | Status | Verified By |
|----|--------|-------------|
| SC 1: shorts_pipeline.py in [500, 800] lines | PASS (787 lines) | scripts/validate/verify_line_count.py + tests/phase05/test_line_count.py |
| SC 2: 0 skip_gates occurrences | PASS (0 matches) | scripts/validate/phase05_acceptance.py grep + tests/phase05/test_blacklist_grep.py |
| SC 3: GateGuard.dispatch + verify_all_dispatched | PASS | tests/phase05/test_gate_guard.py + test_verify_all_dispatched.py |
| SC 4: CircuitBreaker + regen loop Fallback | PASS | tests/phase05/test_circuit_breaker_cooldown.py + test_fallback_shot.py |
| SC 5: 0 T2V + I2V only | PASS (0 forbidden refs) | scripts/validate/phase05_acceptance.py grep + tests/phase05/test_hook_t2v_block.py |
| SC 6: Low-Res First + VoiceFirstTimeline | PASS | tests/phase05/test_low_res_first.py + test_voice_first_timeline.py |

### Plan Commit Hashes

| Plan | Close-out Commit | Title |
|------|------------------|-------|
| 05-01 | `eebfe32` | docs(05-01): complete Wave 1 foundation plan — SUMMARY + STATE + REQUIREMENTS |
| 05-02 | `c13c219` + `5ee9c19` | docs(05-02): complete CircuitBreaker plan (+ SUMMARY correction) |
| 05-03 | `2135745` | docs(05-03): Checkpointer plan complete — SUMMARY + STATE + REQUIREMENTS |
| 05-04 | `8380421` | docs(05-04): complete GateGuard plan — SUMMARY + STATE + REQUIREMENTS |
| 05-05 | `2a4cd49` | docs(05-05): complete VoiceFirstTimeline plan — SUMMARY + STATE + REQUIREMENTS |
| 05-06 | `ce8f4fe` | docs(05-06): complete API adapters plan — SUMMARY + STATE + ROADMAP + REQUIREMENTS |
| 05-07 | `16303f4` | docs(05-07): complete shorts_pipeline keystone plan — SUMMARY + STATE + REQUIREMENTS |
| 05-08 | `6b3f744` | docs(05-08): complete hc_checks regression port plan — SUMMARY + STATE |
| 05-09 | `9c7d266` | docs(05-09): complete Hook enforcement regression tests plan |
| 05-10 | (pending this plan's final commit) | docs(05-10): complete Phase 5 SC acceptance plan + flip nyquist_compliant |

### Source Artifacts

- `scripts/orchestrator/shorts_pipeline.py` — 787 lines, 12 GATE enum state machine, ShortsPipeline class
- `scripts/orchestrator/` support modules: `gates.py` (213) + `circuit_breaker.py` (215) + `checkpointer.py` (233) + `gate_guard.py` (197) + `voice_first_timeline.py` (283) + `fallback.py` (141)
- `scripts/orchestrator/api/` adapters: `models.py` (122) + `kling_i2v.py` (212) + `runway_i2v.py` (196) + `typecast.py` (365) + `elevenlabs.py` (311) + `shotstack.py` (369)
- `scripts/hc_checks/hc_checks.py` — 1176-line rewrite preserving 13 baseline public signatures
- `scripts/validate/` — 3 CLIs: `verify_line_count.py`, `verify_hook_blocks.py`, `phase05_acceptance.py`
- `.claude/deprecated_patterns.json` — 6 regex patterns denying the ORCH-08/09/AF-8/VIDEO-01 blacklist categories in pre_tool_use Hook
- `.planning/phases/05-orchestrator-v2-write/05-TRACEABILITY.md` — 17-REQ traceability matrix with commit audit trail

### Requirements
- **17 / 17 Phase 5 REQs marked [x] complete in REQUIREMENTS.md** — ORCH-01..12 + VIDEO-01..05
- Traceability verified by `tests/phase05/test_traceability_matrix.py` (8 tests green)

### Next Action
`/gsd:verify-work 05` — independent verifier run → expected GREEN.
Then `/gsd:plan-phase 6` — Wiki + NotebookLM + FAILURES Reservoir.
