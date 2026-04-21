# Plan 13-05 Summary — Full E2E Smoke Runner (SMOKE-06)

**Plan**: 13-05 (Wave 4)
**Status**: complete (Tier 1 only — Tier 2 placeholder)
**Completed**: 2026-04-22

---

## Tasks Completed

| Task | Description | Status | Commit |
|------|-------------|--------|--------|
| 13-05-01 | `scripts/smoke/phase13_live_smoke.py` runner (phase11_full_run.py 패턴 복제) | ✅ | `52f8371` |
| 13-05-02 | `tests/phase13/test_smoke_e2e_evidence.py` — 6 Tier 1 evidence shape tests | ✅ | (this commit bundle) |
| 13-05-03 | `tests/phase13/test_live_run.py` — 1 Tier 1 dry-run + 1 Tier 2 live subprocess placeholder | ✅ | (this commit bundle) |

---

## Verification Results

```
Phase 13 Tier 1 cumulative: 39 passed in 2.13s
  - Wave 0 (budget_counter):     6
  - Wave 1 (smoke_01/02 + shapes): 11
  - Wave 2 (smoke_03/04):        8
  - Wave 3 (budget_enforcement): 7
  - Wave 4 (e2e_evidence + dry-run): 7

Phase 13 Tier 2 collected (live_smoke opt-in): 5
  - test_smoke_01_producer (real Claude CLI)
  - test_smoke_02_supervisor (real supervisor fan-out)
  - test_smoke_03_upload_contract (real YouTube unlisted + cleanup)
  - test_smoke_04_readback (real videos.list 4-field readback)
  - test_live_run (full subprocess --live E2E)

Phase 14 regression: 30 adapter_contract passed (baseline preserved)
```

---

## Runner CLI (scripts/smoke/phase13_live_smoke.py)

```
py -3.11 scripts/smoke/phase13_live_smoke.py --help

flags:
  --live                  Real API calls. Default: False (dry-run preview)
  --max-attempts N        Retry attempts on mid-run failure (default 2)
  --budget-cap-usd USD    Hard cost cap (default 5.00, SMOKE-05)
  --session-id <sid>      Custom session identifier (default timestamp)
  --state-root <path>     Checkpointer state dir (default 'state')
  --verbose-compression   Dump raw supervisor payload pre-compression
  --log-level LEVEL       Python logging level (default INFO)
```

**Dry-run (no --live flag, $0 cost)**: runner 가 mock evidence 생성 후 rc=0 종료.
**Live run (--live flag)**: 실 Claude CLI + YouTube API + Kling/Typecast/Nano 호출. $5 HARD cap + cleanup=True + SHORTS_PUBLISH_LOCK_PATH tmp override.

---

## Deviations

- Wave 4 Task 13-05-01 은 이전 agent 세션에서 commit 완료 (52f8371). Task 13-05-02/03 은 API overloaded error 로 인해 메인 세션에서 inline 처리됨 — 최종 결과 동일.
- Tier 2 live_smoke 테스트 **실 API 호출 없이 placeholder 등록**. `--run-live` 없으면 자동 skip. 실 과금 smoke 는 대표님 별도 승인 지점에서 `pytest --run-live` 또는 `python scripts/smoke/phase13_live_smoke.py --live` 수동 실행.

---

## 대표님께 드리는 요약 보고

대표님, Phase 13 Wave 4 (Full E2E Smoke Runner) 작업을 완결했습니다.

**phase13_live_smoke.py runner** 가 완성되어 4 flag (`--live`, `--max-attempts`, `--budget-cap-usd`, `--verbose-compression`) 으로 제어 가능합니다. `--live` 없이 실행 시 $0 cost dry-run 모드로 작동하며, 대표님께서 `--live` 를 명시하실 때에만 실 과금 smoke 가 활성됩니다.

**Tier 1 (always-run) 39 tests GREEN** — 매 commit 에서 안전하게 실행됩니다. **Tier 2 (live_smoke opt-in) 5 tests** 는 `pytest --run-live` 명령 시에만 활성되어 실 API 호출이 일어납니다.

**예상 live run 비용**: $1.50~$3.00 (Kling 8 cuts × $0.35 dominant + Typecast $0.12 + Nano $0.04). $5 HARD cap 으로 보호됩니다.

Phase 14 baseline 30 adapter_contract 테스트 보존 확인했습니다. Wave 5 (Phase Gate + VALIDATION flip) 진입 가능합니다.

---

## Files Changed

- `scripts/smoke/phase13_live_smoke.py` (새로 생성, 250+ lines — commit 52f8371)
- `tests/phase13/test_smoke_e2e_evidence.py` (새로 생성, 6 Tier 1 tests)
- `tests/phase13/test_live_run.py` (새로 생성, 1 Tier 1 + 1 Tier 2)
- `.planning/phases/13-live-smoke/13-05-SUMMARY.md` (this file)

---

## Self-Check: PASSED

- [x] phase13_live_smoke.py shipped (≥250 lines)
- [x] --help shows 4 documented flags
- [x] Tier 1 dry-run subprocess test green
- [x] Tier 2 live subprocess placeholder collected (--run-live skip)
- [x] 6 e2e_evidence shape tests green
- [x] Phase 13 Tier 1 cumulative 39 passed
- [x] Phase 14 baseline 30 adapter_contract preserved
- [x] No real API calls triggered (Tier 2 skipped without --run-live)
