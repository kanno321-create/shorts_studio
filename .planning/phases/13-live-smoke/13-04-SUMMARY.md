---
phase: 13-live-smoke
plan: 04
subsystem: live-smoke-infrastructure
tags: [wave-3, budget-cap, smoke-05, provider-rates, enforcement, mock-only]
dependency-graph:
  requires:
    - Wave 0 (Plan 13-01) BudgetCounter + BudgetExceededError SSOT
    - Wave 0 (Plan 13-01) live_smoke pytest marker + conftest fixtures
    - Phase 14 pytest.ini adapter_contract marker (baseline preservation)
  provides:
    - scripts/smoke/provider_rates.py — Provider unit price SSOT
    - PROVIDER_RATES_USD (8 adapters) — Wave 4 phase13_live_smoke.py 가 import
    - estimate_adapter_cost(provider, units) — 단가 계산 helper
    - all_known_providers() — audit/logging helper
    - tests/phase13/test_budget_enforcement.py — 7 Tier 1 tests (GREEN)
  affects:
    - Wave 4 (Plan 13-05) — phase13_live_smoke.py 가 rates SSOT 를 실 adapter 호출 후 charge
    - Wave 5 (Plan 13-06) — phase13_acceptance.py 가 budget_usage.json 5-key shape 검증
tech-stack:
  added:
    - (없음 — 기존 stdlib only, pytest 8.x, BudgetCounter Wave 0 재사용)
  patterns:
    - Phase 9.1 `_check_cost_cap` file-persisted 확장 (BudgetCounter Wave 0)
    - Research §SMOKE-05 provider unit prices table → 코드 SSOT anchoring
    - CLAUDE.md 금기 #3 (silent fallback) → explicit KeyError raise
    - CLAUDE.md 필수 #7 (존댓말 baseline) → "대표님" in error msg + metadata
    - CLAUDE.md 필수 #8 (증거 기반) → 모든 assertion 에 explicit 메시지
key-files:
  created:
    - scripts/smoke/provider_rates.py (83 lines — 8 adapter rates + 2 helpers)
    - tests/phase13/test_budget_enforcement.py (285 lines — 7 Tier 1 tests)
  modified:
    - (없음 — Wave 0 BudgetCounter 재사용, Plan 내 신규 파일 2종만)
decisions:
  - "provider key 는 lowercase + snake_case 고정 — grep 검색 용이성 + 대소문자 오타 KeyError 보장 (Test 7: 'Kling' 도 KeyError)"
  - "PROVIDER_RATES_USD 은 module-level constant + 직접 export — Wave 4 가 monkeypatch 가능 (future drift test 대비)"
  - "estimate_adapter_cost 기본값 units=1.0 — Kling/Runway 는 units=8, Typecast 는 units=1.5 (K chars) 등 유연 지원"
  - "unknown provider 시 KeyError raise — silent \$0 fallback 은 provider 오타 은폐 (금기 #3) + 과금 drift 위험"
  - "claude_cli/notebooklm/youtube_api \$0.00 ledger entry 허용 — Max 구독 + 무료 quota adapter 도 감사 trail 완결성 (Research Open Q #4)"
  - "atomic overage — raise BEFORE entries.append (charge 내부 순서 강제) — 실패 시 ledger 오염 방지 (Test 2 직접 검증)"
  - "test 파일은 live_smoke marker 미부착 — Tier 2 실 run evidence 는 Wave 4 Plan 05 책임, 본 Plan 은 Tier 1 전용"
metrics:
  duration: "0h35m"
  start_iso: "2026-04-21T14:50:00Z"
  end_iso: "2026-04-21T15:16:55Z"
  tasks: 2
  new_files: 2
  modified_files: 0
  commits: 2
  tests_added: 7
  tests_total_green: 32  # Phase 13 Tier 1 누적 (Wave 0 6 + Wave 1 11 + Wave 2 8 + Wave 3 7)
  live_api_calls: 0
  live_cost_usd: 0.00
completed: 2026-04-21
---

# Phase 13 Plan 04: Wave 3 Budget Cap Enforcement Summary

**One-liner**: Wave 3 — `PROVIDER_RATES_USD` 8-adapter SSOT (Research §SMOKE-05 L322-331 원표) + 7 Tier 1 테스트 (atomic overage + \$0 ledger + 5-key evidence shape + KeyError 금기 #3) 를 일괄 anchoring하여 Wave 4 Full E2E 가 실 adapter 호출 전 enforcement 계약을 regression suite 로 보유.

---

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 13-04-01 | scripts/smoke/provider_rates.py — unit price SSOT | `d29265d` | scripts/smoke/provider_rates.py |
| 13-04-02 | tests/phase13/test_budget_enforcement.py — 7 Tier 1 tests | `f243642` | tests/phase13/test_budget_enforcement.py |

**Commit discipline**: per-task atomic (2 commits, no TDD RED/GREEN split — Task 13-04-02 는 Wave 0 의 이미 shipped `BudgetCounter` + Task 13-04-01 의 이미 shipped `provider_rates` 를 consume 만 하므로 test-only 단일 commit).

---

## Verification Results

### 1. provider_rates.py automated check (Task 13-04-01 verify block)
```
py -3.11 -c "from scripts.smoke.provider_rates import
  PROVIDER_RATES_USD, estimate_adapter_cost, all_known_providers;
  assert len(PROVIDER_RATES_USD) >= 8;
  assert PROVIDER_RATES_USD['claude_cli'] == 0.00;
  assert PROVIDER_RATES_USD['kling'] == 0.35;
  assert estimate_adapter_cost('kling', 8) == 2.80;
  print('providers:', all_known_providers())"
→ providers: ['claude_cli', 'elevenlabs', 'kling', 'nanobanana',
              'notebooklm', 'runway', 'typecast', 'youtube_api']
```
8 adapter 전수 registered + Kling 8 cuts = \$2.80 정확 산출.

### 2. File size + grep counts (13-04-01 acceptance_criteria)
```
wc -l scripts/smoke/provider_rates.py → 83  (≥40 ✓)
grep -c "PROVIDER_RATES_USD" → 8  (≥2 ✓)
grep -c "def estimate_adapter_cost" → 1  (==1 ✓)
grep -c "def all_known_providers" → 1  (==1 ✓)
grep -c "TODO" → 0  (==0 ✓)
```

### 3. Tier 1 budget enforcement tests (Task 13-04-02 verify block)
```
py -3.11 -m pytest tests/phase13/test_budget_enforcement.py
  -m "not live_smoke" --no-cov -v
→ 7 passed in 0.10s
```

| # | Test | Status |
|---|------|--------|
| 1 | `test_under_cap_accumulates_correctly` | PASSED |
| 2 | `test_cap_overage_raises_and_atomic` | PASSED |
| 3 | `test_zero_cost_claude_cli_ledger_entry_allowed` | PASSED |
| 4 | `test_full_run_simulation_under_cap` | PASSED |
| 5 | `test_persist_evidence_shape_5_keys` | PASSED |
| 6 | `test_provider_rates_integration` | PASSED |
| 7 | `test_unknown_provider_in_rates_raises_keyerror` | PASSED |

### 4. test file grep counts (13-04-02 acceptance_criteria 전수)
```
wc -l tests/phase13/test_budget_enforcement.py → 285  (≥100 ✓)
grep -cE "^def test_" → 7  (≥7 ✓)
grep -c "BudgetExceededError" → 4  (≥2 ✓)
grep -c "PROVIDER_RATES_USD" → 5  (≥2 ✓)
grep -c "estimate_adapter_cost" → 11  (≥2 ✓)
grep -c "pytest.raises(BudgetExceededError)" → 1  (≥1 ✓)
grep -c "pytest.raises(KeyError)" → 3  (≥1 ✓)
grep -c "claude_cli" → 10  (≥2 ✓)
grep -c "atomic" → 7  (≥1 ✓)
grep -c "대표님" → 5  (≥1 ✓)
grep -c "TODO" → 0  (==0 ✓ — 금기 #2)
grep -c "pytest.mark.live_smoke" → 0  (==0 ✓ — Tier 1 전용)
```

### 5. Phase 13 cumulative Tier 1 regression (Wave 0 → Wave 3)
```
py -3.11 -m pytest tests/phase13/ -m "not live_smoke" --no-cov -q
→ 32 passed, 4 deselected in 0.97s
```
- Wave 0 (Plan 13-01): 6 tests (test_budget_counter.py)
- Wave 1 (Plan 13-02): 11 tests (test_smoke_01/02_*.py + test_evidence_shapes.py)
- Wave 2 (Plan 13-03): 8 tests (test_smoke_03/04_*.py)
- **Wave 3 (Plan 13-04): +7 tests (test_budget_enforcement.py) ✓**
- Total: 32 Tier 1 GREEN, 4 live_smoke deselected (정상)

### 6. Phase 14 adapter_contract regression (baseline preservation)
```
py -3.11 -m pytest tests/adapters/ -m adapter_contract --no-cov -q
→ 30 passed in 0.92s
```
Wave 3 변경이 Phase 14 baseline 30 tests 에 회귀 없음 확인.

### 7. Unknown provider 금기 #3 enforcement 실증
```python
>>> estimate_adapter_cost("fake_provider")
KeyError: "unknown provider 'fake_provider' — Research §SMOKE-05
           rates table 미등록 (대표님: provider_rates.py 수정 필요)"
>>> estimate_adapter_cost("klin")   # 오타
KeyError: "unknown provider 'klin' — ..."
>>> estimate_adapter_cost("Kling")  # 대소문자
KeyError: "unknown provider 'Kling' — ..."
```
silent \$0 fallback 완전 차단 — 과금 drift 구조적 방어.

---

## Success Criteria 체크

- [x] 2 Task executed atomically (`d29265d`, `f243642`)
- [x] `scripts/smoke/provider_rates.py` 신설 + `PROVIDER_RATES_USD` 8 키 + 2 helper
- [x] `tests/phase13/test_budget_enforcement.py` 7 Tier 1 tests GREEN (0.10s)
- [x] `estimate_adapter_cost("kling", 8) == 2.80` 실측 확인
- [x] `PROVIDER_RATES_USD['claude_cli'] == 0.00` (Max 구독 완결성) 확인
- [x] atomic overage: overage 시 entries 미변경 (Test 2 직접 검증)
- [x] \$0 ledger entry 허용 (Test 3 — Max 구독 claude_cli)
- [x] Unknown provider KeyError (Test 7 — 금기 #3 silent fallback 차단)
- [x] 5-key evidence shape: `cap_usd`, `total_usd`, `breached`, `entry_count`, `entries` (Test 5)
- [x] Entry 5-key shape: `timestamp`, `provider`, `amount_usd`, `cumulative_usd`, `metadata` (Test 5)
- [x] Phase 13 Tier 1 cumulative 32 green (Wave 0-3 합산 ≥31 요구 대비 +1)
- [x] Phase 14 adapter_contract 30 green 보존
- [x] 실 API 호출 0회 (\$0 cost — live_smoke marker 미부착)
- [x] CLAUDE.md 금기 #2 (TODO 0건) + 금기 #3 (silent fallback 0건) + 필수 #7 (존댓말) + 필수 #8 (증거) 전수 준수

---

## Deviations from Plan

### Minor Adjustments (문서화)

**1. [문서화] Task 13-04-02 TDD RED/GREEN split 생략**
- **Plan directive:** `type="auto" tdd="true"` → TDD execution flow (RED commit → GREEN commit)
- **실제 실행:** 단일 test-add commit (`f243642`)
- **Rationale:** TDD 의 RED/GREEN 순서는 "테스트 대상 구현이 아직 없을 때" 유효. 본 test 가 소비하는 `BudgetCounter` + `BudgetExceededError` 는 Wave 0 (Plan 13-01, `8a7a1c1`) 에서 이미 shipped 이며 `PROVIDER_RATES_USD` + `estimate_adapter_cost` 도 같은 Plan 의 선행 Task 13-04-01 (`d29265d`) 에서 shipped. 따라서 test 추가 시점에서 구현은 이미 존재 → RED 단계가 자연발생 불가. 대신 test 작성 후 즉시 GREEN 확인 (7/7 passed 0.10s) → 단일 commit 으로 응축.
- **증거 기반:** Test 실행 로그 `7 passed in 0.10s` (회차 1 + 회차 2 에서 escape fix 후 재실행) 가 GREEN 확인. RED 단계 불필요성이 실행 로그로 검증됨.
- **대체 보증:** Wave 0 BudgetCounter 는 Plan 13-01 Task 02 에서 정식 RED (`2a9eb3d`) → GREEN (`8a7a1c1`) 수행 — 본 Plan 의 consumer test 는 pure regression add.

### Minor polish

**2. [Rule 1 - Bug] f-string escape sequence 정리**
- **Found during:** Task 13-04-02 verify block 초기 실행
- **Issue:** Test 파일 내부 assertion message 에 `\$` escape 사용 (e.g., `f"expected \$0.51"`) — Python 3.12+ DeprecationWarning ("invalid escape sequence '\\$'")
- **Fix:** `\$` → `$` (f-string 내부 `$` 는 escape 불필요, 단순 literal 처리)
- **Files modified:** tests/phase13/test_budget_enforcement.py (17 warnings → 0)
- **Verification:** `py -3.11 -m pytest ... -v → 7 passed in 0.10s` (warnings 0)
- **Commit:** `f243642` (escape fix 는 initial write 의 같은 commit 에 포함)

### CLAUDE.md-driven adjustments

**3. [필수 #7] 한국어 존댓말 baseline — test assertion + rates error msg**
- **Applied to:** 
  - provider_rates.py KeyError message: `"... (대표님: provider_rates.py 수정 필요)"`
  - test_budget_enforcement.py Test 2: `counter.entries[0]["provider"] == "kling"` 확인 assertion — "대표님" 5건 포함
  - Test 3 metadata: `{"reason": "Max 구독 — 비과금 엔트리 (대표님 감사 trail)"}`
- **Commits:** `d29265d`, `f243642`

**4. [금기 #3] silent \$0 fallback 방지 — KeyError explicit raise**
- **Design decision:** `estimate_adapter_cost("unknown")` 이 `0.0` 반환이 아닌 `KeyError` raise
- **Rationale:** silent fallback 시 `adapter_rates["klin"]` (오타) 이 \$0 으로 기록 → 실 API 는 \$0.35 과금 → ledger 와 실제 과금 drift. KeyError 로 즉시 실패 시 과금 전 provider 검증 강제.
- **Test 7:** 오타 (`"klin"`) + 대소문자 (`"Kling"`) 모두 KeyError 보장
- **Commits:** `d29265d`, `f243642`

### Authentication Gates

없음 — Wave 3 은 100% mock, 실 API 호출 0회, \$0 cost.

---

## Interfaces Exposed to Wave 4~5

### scripts/smoke/provider_rates.py

```python
PROVIDER_RATES_USD: dict[str, float] = {
    "claude_cli":  0.00,  # Max 구독
    "notebooklm":  0.00,  # Max 구독
    "youtube_api": 0.00,  # Free within 10K/day
    "nanobanana":  0.04,  # per image
    "kling":       0.35,  # per 5s clip
    "runway":      0.25,  # per 5s clip (fallback)
    "typecast":    0.12,  # per 1K chars
    "elevenlabs":  0.30,  # per 1K chars (fallback)
}

def estimate_adapter_cost(provider: str, units: float = 1.0) -> float:
    """KeyError on unknown provider — 금기 #3 침묵 금지."""

def all_known_providers() -> list[str]:
    """Sorted list — audit/logging용."""
```

### Wave 4 usage pattern (phase13_live_smoke.py 가 사용할 계약)

```python
from scripts.smoke.budget_counter import BudgetCounter, BudgetExceededError
from scripts.smoke.provider_rates import PROVIDER_RATES_USD, estimate_adapter_cost

counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence_dir / "budget_usage.json")

# Nanobanana 썸네일 1 image
result_img = call_nanobanana(...)
counter.charge("nanobanana", estimate_adapter_cost("nanobanana", 1),
               metadata={"prompt": result_img.prompt_preview})

# Kling I2V 8 cuts
for cut in cuts:
    clip = call_kling_i2v(cut)
    counter.charge("kling", estimate_adapter_cost("kling", 1),
                   metadata={"cut_index": cut.index, "duration_s": 5.0})

# Typecast TTS
vo = call_typecast(script, chars=953)
counter.charge("typecast", estimate_adapter_cost("typecast", chars / 1000),
               metadata={"chars": chars})

counter.persist()  # → budget_usage.json (5-key schema)
```

### Wave 5 acceptance contract (Plan 13-06 이 검증할 invariant)

```python
payload = json.loads(evidence_dir / "budget_usage.json")
assert set(payload.keys()) == {
    "cap_usd", "total_usd", "breached", "entry_count", "entries",
}
assert payload["cap_usd"] == 5.00
assert payload["total_usd"] <= 5.00
assert payload["breached"] is False
for entry in payload["entries"]:
    assert set(entry.keys()) == {
        "timestamp", "provider", "amount_usd", "cumulative_usd", "metadata",
    }
```

---

## 대표님 보고 블록 (한국어 존댓말)

Phase 13 Plan 04 (Wave 3 Budget Cap Enforcement — SMOKE-05) 가 완료되었습니다. 2 Task 를 atomic commit 2건으로 처리하였으며, 신규 `provider_rates.py` SSOT (8 adapter 단가 + 2 helper) + `test_budget_enforcement.py` 7 Tier 1 테스트 (0.10s GREEN) 를 anchoring 하였습니다. 실 API 호출 0회·비용 \$0.00 유지하면서 atomic overage·\$0 ledger·5-key evidence shape·KeyError silent fallback 차단을 전수 검증하였으며, Phase 13 Tier 1 누적 32 green + Phase 14 adapter_contract 30 green 회귀 보존을 확인하였습니다. Wave 4 Plan 05 가 실 adapter 호출 후 `counter.charge(provider, estimate_adapter_cost(provider, units))` 로 SSOT 를 consume 할 준비가 완료되었습니다.

---

## Known Stubs

없음 — Wave 3 은 rates SSOT + Tier 1 test 전용이며 모든 artifact 가 완전 wiring.
- `PROVIDER_RATES_USD` 는 module-level constant 로 즉시 import 가능 (no deferred load)
- `estimate_adapter_cost` / `all_known_providers` 는 pure function (no external dependency)
- 7 Tier 1 테스트는 실제 `BudgetCounter` + `PROVIDER_RATES_USD` 를 실행 — mock 없음 (단 실 API 호출은 0회, in-memory 과금 시뮬레이션)

---

## Next Actions

**Wave 4 (Plan 13-05 `phase13_live_smoke.py`) 실행 전 필수:**
1. 대표님께 live_smoke Wave 4 진입 승인 득 (Kling/Typecast/Nanobanana 실 과금, 예상 \$1.50~\$3.00)
2. `py -3.11 scripts/smoke/phase13_preflight.py` 재실행 → rc=0 재확인 (OAuth + env keys)
3. Wave 4 orchestrator 가 본 Plan 의 SSOT 를 import — `from scripts.smoke.provider_rates import PROVIDER_RATES_USD, estimate_adapter_cost`
4. Wave 4 실행 완료 시 `evidence/budget_usage.json` 이 본 Plan Test 5 schema 와 일치하는지 Plan 13-06 `phase13_acceptance.py` 가 검증

**본 Plan 의 완료 가능 조건**: 위 Verification Results 7개 섹션 전수 green (확인 완료).

---

## Self-Check: PASSED

**Files verified (3/3):**
- FOUND: scripts/smoke/provider_rates.py (83 lines)
- FOUND: tests/phase13/test_budget_enforcement.py (285 lines)
- FOUND: .planning/phases/13-live-smoke/13-04-SUMMARY.md

**Commits verified (2/2):**
- FOUND: d29265d (Task 13-04-01 — provider_rates.py SSOT)
- FOUND: f243642 (Task 13-04-02 — 7 Tier 1 tests GREEN)

**Test evidence verified:**
- FOUND: `pytest tests/phase13/test_budget_enforcement.py -m "not live_smoke" --no-cov -v` → 7 passed in 0.10s
- FOUND: `pytest tests/phase13/ -m "not live_smoke" --no-cov -q` → 32 passed, 4 deselected in 0.97s
- FOUND: `pytest tests/adapters/ -m adapter_contract --no-cov -q` → 30 passed in 0.92s
