---
phase: 13
slug: live-smoke
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-21
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Derived from 13-RESEARCH.md §Validation Architecture.

**핵심 전략**: Two-tier pytest separation
- **Tier 1 (always-run)**: Evidence-shape tests (mock-based, no API) — 매 commit 실행 안전
- **Tier 2 (opt-in)**: `@pytest.mark.live_smoke` + `--run-live` flag — 실 과금 실행 (대표님 승인 시점에만)

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Phase 14 pytest.ini 상속) |
| **Config additions** | `live_smoke` marker registration in pytest.ini (Wave 0) |
| **Always-run command** | `pytest tests/phase13 -m "not live_smoke" --tb=short -q` (≈ 10s, mock-only evidence shape) |
| **Live-smoke command** | `pytest tests/phase13 -m live_smoke --run-live --tb=long -v --no-cov` (≈ 15-30min, real API, ~$1.50-$3.00 spend) |
| **Contract-isolated command** | `pytest -m adapter_contract` (Phase 14 preserved — 30 tests green) |
| **Full gate command** | `python scripts/smoke/phase13_live_smoke.py --max-attempts 2 --budget-cap-usd 5.00` |

---

## Sampling Rate

- **Always (no API)**: 매 task commit 후 `pytest tests/phase13 -m "not live_smoke"` 실행 — evidence 파일 shape + budget counter + smoke plan builder 검증
- **Opt-in live**: Wave 4 Full E2E 시 1회만 `pytest -m live_smoke --run-live` — 대표님 승인 후 실 과금 smoke. 재실행 제한 (cooldown + publish_lock bypass via SHORTS_PUBLISH_LOCK_PATH env)
- **Budget enforcement**: live run 전 `budget_usage.json` 초기화 + 각 adapter 호출 후 누적 기록 + $5 초과 시 즉시 RuntimeError + upload 차단
- **Max feedback latency**: 10s (always-run) / 30min (live-smoke upper bound)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|:-:|:-:|
| 13-01-01 | 01 | 0 | SMOKE-05 infra | infra | `pytest tests/phase13/test_budget_counter.py` ≥5 tests | ❌ W0 | ⬜ |
| 13-01-02 | 01 | 0 | SMOKE-05 infra | infra | `test -f scripts/smoke/budget_counter.py && python -c "from scripts.smoke import budget_counter; budget_counter.reset()"` exit 0 | ❌ W0 | ⬜ |
| 13-01-03 | 01 | 0 | All SMOKE | infra | pytest.ini `live_smoke` marker 등록: `pytest --markers \| grep live_smoke` exit 0 | ❌ W0 | ⬜ |
| 13-01-04 | 01 | 0 | Preflight | infra | `python scripts/smoke/phase13_preflight.py` — ANTHROPIC_API_KEY + YouTube OAuth + API quota check exit 0 | ❌ W0 | ⬜ |
| 13-02-01 | 02 | 1 | SMOKE-01 | live smoke | Real Claude CLI producer: `pytest tests/phase13/test_smoke_01_producer.py -m live_smoke --run-live` — evidence `producer_output_YYYYMMDD.json` anchor | ✅ invokers.py ship | ⬜ |
| 13-02-02 | 02 | 1 | SMOKE-02 | live smoke | Real Claude CLI supervisor 17 fan-out: `pytest tests/phase13/test_smoke_02_supervisor.py -m live_smoke --run-live` — evidence `supervisor_output.json` + rc=1 재현 0회 검증 | ✅ Phase 12 compression | ⬜ |
| 13-03-01 | 03 | 2 | SMOKE-03 | live smoke | YouTube smoke upload unlisted+cleanup: `pytest tests/phase13/test_smoke_03_upload.py -m live_smoke --run-live` — video_id 수신 + auto delete 30s 내 | ✅ smoke_test.py ship | ⬜ |
| 13-03-02 | 03 | 2 | SMOKE-04 | live smoke | production_metadata readback: `videos.get` 로 description HTML comment 에서 4 필드 (script_seed/assets_origin/pipeline_version/checksum) 존재 | ✅ production_metadata.py ship | ⬜ |
| 13-04-01 | 04 | 3 | SMOKE-05 | evidence-shape | `pytest tests/phase13/test_budget_enforcement.py` — mock adapter 호출로 $4.99 → OK, $5.01 → RuntimeError | ❌ W0 | ⬜ |
| 13-04-02 | 04 | 3 | SMOKE-05 | live smoke | 실 run 후 `budget_usage.json` `total_cost_usd` ≤ $5.00 + 각 adapter 별 line item | — | ⬜ |
| 13-05-01 | 05 | 4 | SMOKE-06 | live smoke (E2E) | Full E2E: `python scripts/smoke/phase13_live_smoke.py --max-attempts 2` → TREND~COMPLETE 13 gate 전수 dispatched + final_video_id 수신 + cleanup + `smoke_e2e_YYYYMMDD.json` 기록 | ✅ phase11_full_run.py ship | ⬜ |
| 13-05-02 | 05 | 4 | SMOKE-06 | evidence-shape | `pytest tests/phase13/test_smoke_e2e_evidence.py` — evidence JSON 이 13 gate timestamps + final_video_id + total_cost_usd 필드 보유 | — | ⬜ |
| 13-06-01 | 06 | 5 | All SC (gate) | acceptance aggregator | `python scripts/validate/phase13_acceptance.py` — 6 SC 자동 검증 + acceptance.json anchor (phase14_acceptance.py 패턴 복제) | ❌ W0 | ⬜ |
| 13-06-02 | 06 | 5 | All SC (gate) | full regression | `pytest -m "not live_smoke"` 전수 green + Phase 14 `pytest -m adapter_contract` 30 tests 보존 | ✅ Phase 14 baseline | ⬜ |
| 13-06-03 | 06 | 5 | Traceability | docs | `.planning/phases/13-live-smoke/13-TRACEABILITY.md` anchor + VALIDATION sign-off flip | ❌ W0 | ⬜ |
| 13-06-04 | 06 | 5 | Phase complete | gate | HARD-GATE: `grep -q ALL_PASS 13-06-phase-gate.log \|\| exit 1` → VALIDATION flip to approved | ❌ W0 | ⬜ |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Coverage summary**: 16 rows × 6 SMOKE requirements. Tier 1 always-run (evidence-shape, mock) = 6 rows, Tier 2 live-smoke (opt-in `--run-live`) = 6 rows, 나머지 infra + docs.

---

## Wave 0 Requirements

- [ ] `pytest.ini` updated with `live_smoke` marker (leverages Phase 14 config)
- [ ] `scripts/smoke/budget_counter.py` (신규 — budget_usage.json persistence + enforce)
- [ ] `scripts/smoke/phase13_preflight.py` (신규 — API key + OAuth + quota sanity check)
- [ ] `tests/phase13/__init__.py` + `conftest.py` (mock fixtures for evidence-shape tier, Phase 14 conftest 참조)
- [ ] `tests/phase13/test_budget_counter.py` (Tier 1 always-run)
- [ ] `.env` 확인: `ANTHROPIC_API_KEY` 미필요 (Max 구독 CLI 경로), `SHORTS_PUBLISH_LOCK_PATH` env 준비
- [ ] `config/client_secret.json` + `config/youtube_token.json` 존재 확인 (Phase 8 shipped)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 대표님 실 과금 승인 타이밍 | SMOKE-03/04/06 Wave 4 trigger | Budget $5 소진 방지 + 1회 per 48h cooldown 준수 | Wave 4 실행 전 대표님 세션 내 "진행" 승인 대기 |
| Claude 생성 script safety 사전 확인 | SMOKE-02 supervisor fan-out | 실 API content 가 YouTube policy/한국 법 위반 가능 — supervisor 17 inspector fan-out 결과 대표님 검토 | Wave 1 완료 후 `supervisor_output.json` 수동 review, ins-safety + ins-platform-policy rubric 재확인 |
| YouTube video 실제 재생 + 자막 표시 | SMOKE-03 upload | 실제 업로드 후 unlisted URL 에서 재생 → 60초 이내 재생 + 자막 정상 표시 → 30초 내 cleanup 확인 | Wave 2 live run 직후 video URL 방문, 재생 확인, 삭제 확인 |

---

## Validation Sign-Off

- [ ] 16 per-task verification rows 모두 automated verify 또는 live_smoke opt-in 지정
- [ ] Tier 1 (always-run) 과 Tier 2 (live_smoke) 분리 준수 — pytest default 실행으로 실 과금 trigger 없음
- [ ] Wave 0 requirements 7건 모두 충족 (`❌ W0` → `✅`)
- [ ] Budget cap $5 hard enforcement 검증 (mock + live)
- [ ] 3 manual-only verification 대표님 승인 기록
- [ ] `nyquist_compliant: true` 플립 (Wave 0 완료 후)

**Approval**: pending (Wave 0 commits 후 → `approved YYYY-MM-DD`)
