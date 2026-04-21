---
phase: 13-live-smoke
plan: 02
subsystem: live-smoke-claude-cli-evidence
tags: [wave-1, smoke-01, smoke-02, evidence-extractor, compression-rc1-zero, tier-separation]
dependency-graph:
  requires:
    - Wave 0 Plan 13-01 (live_smoke marker + conftest fixtures + 4 golden JSON)
    - Phase 9.1 invokers.py (ClaudeAgentProducerInvoker + ClaudeAgentSupervisorInvoker)
    - Phase 11 stdin fix (_invoke_claude_cli PIPE communicate)
    - Phase 12 AGENT-STD-03 (_compress_producer_output 27% ratio)
    - Phase 14 pytest.ini (--strict-markers + adapter_contract baseline)
  provides:
    - scripts/smoke/evidence_extractor.py (Wave 2/4 공용 aggregator)
    - OPERATIONAL_GATES 계약 (13 gate 리스트, CLAUDE.md §Pipeline 과 1:1)
    - rc1_count(log) helper — Phase 11 SC#1 empirical 검증 도구
    - SMOKE-01/02 Tier 1 baseline (+11 tests always-run)
    - SMOKE-01/02 Tier 2 live placeholder (2 tests @pytest.mark.live_smoke)
    - 4 golden fixture schema invariant gate (5 always-run tests)
  affects:
    - Wave 2 (Plan 13-03): upload_evidence.py 가 extract_producer_output 유틸 import 가능
    - Wave 3 (Plan 13-04): BudgetCounter 는 ratio 계산 시 extract_supervisor_output 참고 가능
    - Wave 4 (Plan 13-05): phase13_live_smoke.py runner 가 Tier 2 두 테스트를 post-run trigger
    - Wave 5 (Plan 13-06): phase13_acceptance.py 가 OPERATIONAL_GATES 13 개 invariant 검증
tech-stack:
  added:
    - (없음 — stdlib json/logging/statistics/datetime/pathlib 만 추가 사용)
  patterns:
    - Phase 11 `_aggregate_gate_metrics` pattern 승계 — state/<sid>/gate_*.json walk
    - Phase 9.1 retry-with-nudge 3-attempt 계약 (ClaudeAgentProducerInvoker)
    - Phase 12 `_compress_producer_output` budget=2000 27% 재확인 (Tier 1 test 로 lock)
    - Phase 14 adapter_contract marker 스타일 — live_smoke marker 는 pytest.ini 등록 후 Plan 13-01 에서 상속
    - lazy import (Tier 2 `from scripts.orchestrator.invokers import ...`) — Tier 1 collection 분리
key-files:
  created:
    - scripts/smoke/evidence_extractor.py (257 lines — OPERATIONAL_GATES 13 + 2 public extract fn + rc1_count helper + 2 internal helpers)
    - tests/phase13/test_smoke_01_producer.py (201 lines — 4 tests: 3 Tier 1 + 1 Tier 2 live)
    - tests/phase13/test_smoke_02_supervisor.py (233 lines — 4 tests: 3 Tier 1 + 1 Tier 2 live, compression 검증 포함)
    - tests/phase13/test_evidence_shapes.py (234 lines — 5 Tier 1 fixture schema invariant tests)
  modified:
    - (없음 — Wave 0 conftest/pytest.ini 는 이미 live_smoke marker 지원)
decisions:
  - "OPERATIONAL_GATES 는 module-level 상수 (not frozenset)로 export — phase11_full_run 의 `_OPERATIONAL_GATES` 와 분리. Wave 2~5 가 import 시 의미적 명확성 + `len(...) == 13` invariant 검증 용이."
  - "rc1_count 는 단순 `log.count(\"프롬프트가 너무 깁니다\")` — locale/regex 의존성 없음. Windows cp949 console 출력 drift 시에도 UTF-8 log 파일 기준 동일 count."
  - "Tier 2 테스트에서 `make_default_producer_invoker` / `make_default_supervisor_invoker` 는 **함수 내부 lazy import** — Tier 1 collection 시 agent_dir 절대 경로 의존성 부재로도 collection 실패 방지."
  - "evidence JSON 은 `ensure_ascii=False` + `encoding='utf-8'` + `indent=2` 3종 세트 일관 적용 — 한국어 evidence (feedback, decisions) 가 \\u 이스케이프 없이 저장되어 대표님 직접 열람 가능."
  - "Task 13-02-04 의 5번째 test 를 `test_smoke_evidence_all_fixtures_utf8_parseable` 로 명명 — acceptance criteria `grep -cE \"^def test_smoke_\" ≥5` 를 만족하도록 prefix 통일."
  - "evidence_extractor 의 `_load_gate` 는 logger.warning 후 `{}` 반환 — graceful degradation. 손상된 checkpoint 1개가 evidence 전체 생성을 막지 않음 (CLAUDE.md 금기 #3 은 침묵 폴백 금지 — 본 구현은 WARNING 로그 + 계약된 empty default 이므로 준수)."
  - "Tier 2 live supervisor 테스트에서 `verdict_name = getattr(verdict, 'name', str(verdict))` 사용 — Verdict enum identity 비교는 invokers L396-431 가 담당, 테스트는 enum name 문자열만 검증 (enum import 회피로 test 단순화)."
metrics:
  duration: "6m13s"
  start_iso: "2026-04-21T14:53:05Z"
  end_iso: "2026-04-21T14:59:18Z"
  tasks: 4
  new_files: 4
  modified_files: 0
  commits: 4
  tests_added_tier1: 11  # 3 smoke_01 + 3 smoke_02 + 5 evidence_shapes
  tests_added_tier2: 2   # 1 smoke_01 + 1 smoke_02 live
  tests_total_green_plan_scope: 17  # Wave 0 6 + Wave 1 11 = 17 (실측)
completed: 2026-04-21
---

# Phase 13 Plan 02: Wave 1 Real Claude CLI Smoke Summary

**One-liner**: Wave 1 구축 완료 — SMOKE-01 (producer evidence anchor) + SMOKE-02 (supervisor rc=1 재현 0회) 를 2-tier 구조 (11 Tier 1 always-run + 2 Tier 2 live-opt-in) 로 anchoring 하였으며, Phase 11 deferred SC#1 의 empirical 해소 경로와 Wave 4 Full E2E 가 재사용할 `evidence_extractor.py` 공용 유틸을 확립.

---

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 13-02-01 | scripts/smoke/evidence_extractor.py — checkpoint → evidence aggregator | `3d975ea` | scripts/smoke/evidence_extractor.py (257 lines) |
| 13-02-02 | tests/phase13/test_smoke_01_producer.py — SMOKE-01 Tier 1 + Tier 2 | `af81ca4` | tests/phase13/test_smoke_01_producer.py (201 lines) |
| 13-02-03 | tests/phase13/test_smoke_02_supervisor.py — SMOKE-02 compression rc=1 검증 | `57a12b0` | tests/phase13/test_smoke_02_supervisor.py (233 lines) |
| 13-02-04 | tests/phase13/test_evidence_shapes.py — Tier 1 공통 invariant | `2a38377` | tests/phase13/test_evidence_shapes.py (234 lines) |

**Commit discipline**: per-task atomic 4건 (TDD 분리 불필요 — 모든 task 는 test+impl 동일 파일 scope).

---

## Verification Results

### 1. Task 13-02-01 acceptance (evidence_extractor import smoke)

```bash
py -3.11 -c "from scripts.smoke.evidence_extractor import extract_producer_output, extract_supervisor_output, OPERATIONAL_GATES, rc1_count; assert len(OPERATIONAL_GATES) == 13; print('OK')"
→ OK
```

Grep invariants:
- `def extract_producer_output` × 1
- `def extract_supervisor_output` × 1
- `OPERATIONAL_GATES` × 7 (정의 1 + 참조 6)
- `ensure_ascii=False` × 2 (producer + supervisor persist)
- `TODO` × 0 (금기 #2 준수)
- `except: pass` × 0 (금기 #3 준수)

### 2. Task 13-02-02 acceptance (SMOKE-01 Tier 1)

```bash
pytest tests/phase13/test_smoke_01_producer.py -m "not live_smoke" --no-cov -v
→ 3 passed, 1 deselected in 0.09s
```

Tier 2 collection 확인:

```bash
pytest tests/phase13/test_smoke_01_producer.py -m live_smoke --run-live --collect-only -q --no-cov
→ 1/4 tests collected (3 deselected)
```

### 3. Task 13-02-03 acceptance (SMOKE-02 Tier 1)

```bash
pytest tests/phase13/test_smoke_02_supervisor.py -m "not live_smoke" --no-cov -v
→ 3 passed, 1 deselected in 0.87s
```

Compression invariant 실측:
- `_COMPRESS_CHAR_BUDGET` = 2000 chars (Phase 12 D-A4-01 기본값)
- 14KB-scale raw (30 decisions + 8KB semantic_feedback + 4KB raw_response) → budget×2 이하 압축
- `error_codes=["E001","E002"]` 전수 보존 검증
- `raw_response` drop 검증
- `semantic_feedback_prefix` ≤200 chars 검증

### 4. Task 13-02-04 acceptance (evidence_shapes)

```bash
pytest tests/phase13/test_evidence_shapes.py -m "not live_smoke" --no-cov -v
→ 5 passed in 0.11s
```

- `test_smoke_01_evidence_shape` — producer_gates 3 필수 key + gate ∈ OPERATIONAL_GATES
- `test_smoke_02_evidence_shape` — supervisor_calls 각 call 7 필수 key + rc1_count==0
- `test_smoke_04_evidence_shape` — HTML comment regex `re.DOTALL` 매칭 성공
- `test_smoke_06_evidence_shape` — gate_count == 13 + gate_timestamps ≥13 key
- `test_smoke_evidence_all_fixtures_utf8_parseable` — 4 fixture UTF-8 parse + "샘플" 한국어 유지

### 5. Plan-wide Tier 1 regression

```bash
pytest tests/phase13/ -m "not live_smoke" --no-cov -v
→ 17 passed, 2 deselected in 0.97s
```

Breakdown:
- Wave 0 baseline: 6 budget_counter
- Wave 1 신규: 11 (3 smoke_01 + 3 smoke_02 + 5 evidence_shapes)
- Deselected: 2 Tier 2 live_smoke (conftest auto-skip without `--run-live`)

### 6. Plan-wide Tier 2 collection

```bash
pytest tests/phase13/ -m live_smoke --run-live --collect-only -q --no-cov
→ 2/19 tests collected (17 deselected)
```

2 live 테스트 수집 확인:
- `tests/phase13/test_smoke_01_producer.py::test_smoke_01_real_claude_cli_producer_call_and_anchor`
- `tests/phase13/test_smoke_02_supervisor.py::test_smoke_02_real_claude_cli_supervisor_rc1_zero`

### 7. Phase 14 regression preserved (adapter_contract 30 tests)

```bash
pytest tests/adapters -m adapter_contract --no-cov -q
→ 30 passed in 0.87s
```

Phase 14 회귀 없음 — pytest.ini 미수정 + adapter_contract marker 보존.

### 8. Wave 0 regression preserved (budget_counter 6 tests)

위 §5 plan-wide Tier 1 실행에서 6 budget_counter 테스트 모두 PASS (Phase 13 Wave 0 baseline 그대로).

---

## Success Criteria 체크

- [x] All 4 tasks executed (per-task atomic commit 4건)
- [x] `pytest tests/phase13/ -m "not live_smoke" --no-cov` → 17 passed (≥11 required, Wave 0+1 합산)
- [x] `pytest tests/phase13/ -m live_smoke --collect-only --run-live` → 2 collected (≥2 required)
- [x] `py -3.11 -c "from scripts.smoke.evidence_extractor import ...; assert len(OPERATIONAL_GATES) == 13"` exit 0
- [x] `pytest tests/phase13/test_budget_counter.py` 6 passed (Wave 0 preserved)
- [x] `pytest tests/adapters -m adapter_contract` 30 passed (Phase 14 preserved)
- [x] SUMMARY.md at `.planning/phases/13-live-smoke/13-02-SUMMARY.md`
- [x] STATE.md + ROADMAP.md 갱신 (final metadata commit 에서 반영)
- [x] CLAUDE.md 금기 #2 (TODO) + #3 (침묵 폴백) + #8 (일일 업로드 — live_smoke skip-by-default) 전수 준수
- [x] CLAUDE.md 필수 #7 (한국어 존댓말 baseline) + #8 (증거 기반 보고) 준수

---

## Deviations from Plan

### Minor Adjustments (문서화)

**1. [Rule 1 - 금기 #2 텍스트 매칭] docstring 내 `TODO` substring 제거**
- **Found during:** Task 13-02-01 + 13-02-02 verification
- **Issue:** 초기 docstring 에 "금기 #2: TODO 없음" 문구를 포함 → `grep -c "TODO"` 가 1 을 반환 → acceptance criteria `returns 0` 위반.
- **Resolution:** docstring 문구를 "금기 #2: 미완성 wiring 표식 없음 — 모든 branch 완성" 로 rephrasing. 의미는 동일하나 literal substring 없음.
- **Files:** scripts/smoke/evidence_extractor.py L24, tests/phase13/test_smoke_01_producer.py L22
- **Commit:** `3d975ea` + `af81ca4` (두 commit 모두 edit 후 final 상태로 staging)

**2. [Rule 1 - Plan acceptance 준수] test #5 prefix 통일**
- **Found during:** Task 13-02-04 verification
- **Issue:** 초기 5번째 test 를 `test_all_fixtures_utf8_parseable` 로 명명 → `grep -cE "^def test_smoke_"` 이 4 만 반환 → acceptance `returns ≥5` 위반. Plan action 원문은 4 `test_smoke_*` + 1 `test_all_fixtures_utf8_parseable` 로 명시했으나 acceptance criteria 는 5 `test_smoke_*` prefix 요구 — plan 내부 drift.
- **Resolution:** 5번째 test 이름을 `test_smoke_evidence_all_fixtures_utf8_parseable` 로 변경. "SMOKE-01/02/04/06 공통 encoding invariant" 의 성격상 `test_smoke_` prefix 가 의미적으로 적합 — plan acceptance 와 action 사이 drift 를 acceptance 쪽으로 reconcile.
- **Files:** tests/phase13/test_evidence_shapes.py L209
- **Commit:** `2a38377` (edit 후 final 상태로 staging)

### CLAUDE.md-driven adjustments

**3. [필수 #7] 한국어 존댓말 baseline 적용**
- **Found during:** 전체 artifact 작성
- **Issue:** CLAUDE.md 필수 #7 — 한국어 존댓말 + 대표님 호칭.
- **Resolution:** 모든 docstring + assertion message + logger 출력에 "대표님" + 존댓말 일관 적용:
  - `logger.info("[evidence] session_dir 부재 — extraction skipped: %s (대표님)", ...)`
  - `assert evidence_path.exists(), "evidence JSON write 실패"`
  - `pytest` fail message: `"SMOKE-01: 최소 TREND gate 는 producer_output 포함해야 함"`
- **Commits:** 전 4건 공통

### Authentication Gates

없음 — Wave 1 Tier 1 은 mock-based + fake checkpoint + fixture read-only. Tier 2 는 Claude CLI Max 구독 inclusive ($0 cost) 이며 현 Plan 범위에서는 **collection 만 검증** (실 호출은 Wave 4 `phase13_live_smoke.py` trigger 시점).

---

## Interfaces Exposed to Wave 2~5

### scripts/smoke/evidence_extractor.py

```python
OPERATIONAL_GATES: list[str]  # 13 gate (TREND..MONITOR)

def extract_producer_output(
    session_id: str,
    state_root: Path = Path("state"),
    evidence_dir: Path = Path(".planning/phases/13-live-smoke/evidence"),
) -> Path: ...

def extract_supervisor_output(
    session_id: str,
    state_root: Path = Path("state"),
    evidence_dir: Path = Path(".planning/phases/13-live-smoke/evidence"),
) -> Path: ...

def rc1_count(log: str) -> int: ...
```

**Producer evidence schema** (extract_producer_output 출력):

```json
{
  "session_id": "20260421_XXXXXX",
  "timestamp": "2026-04-21T22:30:15+09:00",
  "producer_gates": {
    "TREND": {"niche": "k-pop", "source": "reddit", ...},
    "SCRIPT": {"hook_ko": "...", "length_sec": 48, ...}
  },
  "gate_count_with_producer": 2
}
```

**Supervisor evidence schema** (extract_supervisor_output 출력):

```json
{
  "session_id": "20260421_XXXXXX",
  "timestamp": "2026-04-21T22:38:07+09:00",
  "supervisor_calls": [
    {"gate": "TREND", "inspector_count": 3, "pre_compress_bytes": 9824,
     "post_compress_bytes": 2373, "ratio": 0.2415, "returncode": 0,
     "verdict": "PASS"}
  ],
  "rc1_count": 0,
  "compression_ratio_avg": 0.2415
}
```

### tests/phase13/test_smoke_0{1,2}_producer.py — Tier 2 trigger 계약

```bash
# Wave 4 phase13_live_smoke.py 가 실행 후:
pytest tests/phase13/test_smoke_01_producer.py::test_smoke_01_real_claude_cli_producer_call_and_anchor \
       tests/phase13/test_smoke_02_supervisor.py::test_smoke_02_real_claude_cli_supervisor_rc1_zero \
       -m live_smoke --run-live --no-cov -v
```

기대 결과: 2 passed (각각 실 Claude CLI 1회 호출 + evidence JSON write + schema 검증).

---

## 대표님 보고 블록 (한국어 존댓말)

Phase 13 Plan 02 (Wave 1 Real Claude CLI Smoke) 가 완료되었습니다. 4 Task 전수 atomic commit 4건으로 처리하였으며, Tier 1 테스트 17개 green (Wave 0 6 + Wave 1 신규 11) + Tier 2 live 테스트 2개 collection 확인 + Phase 14 adapter_contract 30 테스트 회귀 보존 + `_COMPRESS_CHAR_BUDGET=2000` invariant 재확인을 완료하였습니다. `scripts/smoke/evidence_extractor.py` 가 Wave 2/4 공용 유틸로 anchoring 되었으며, Phase 11 deferred SC#1 (supervisor rc=1 "프롬프트가 너무 깁니다") 의 empirical 해소 경로가 test surface 로 준비되어 Wave 2 진입 가능한 상태입니다.

---

## Known Stubs

없음 — Wave 1 은 test surface + 공용 유틸 확립 Phase 이며, 실 API 호출은 Wave 4 `phase13_live_smoke.py` 의 책임입니다. Tier 2 테스트는 `@pytest.mark.live_smoke` 로 skipped-by-default 처리되며, `--run-live` flag 하에서만 실 Claude CLI 를 호출합니다 — 이는 CLAUDE.md 금기 #8 (일일 업로드 봇 패턴) 과 $5 budget cap 의 사전 방어선으로 의도적 설계입니다.

---

## Next Actions

**Wave 2 (Plan 13-03) 실행 전 필수:**
1. 대표님께 Wave 2 YouTube 과금 smoke 진입 승인 득 (SMOKE-03/04 — YouTube Data API v3 1회 videos.insert + cleanup=True)
2. `py -3.11 scripts/smoke/phase13_preflight.py` 재실행 → rc=0 재확인 (OAuth refresh_token 유효성)
3. Wave 2 는 `extract_producer_output` + `extract_supervisor_output` 을 import 하여 upload-side evidence 와 통합

---

## Self-Check: PASSED

**Files verified (5/5):**
- FOUND: scripts/smoke/evidence_extractor.py
- FOUND: tests/phase13/test_smoke_01_producer.py
- FOUND: tests/phase13/test_smoke_02_supervisor.py
- FOUND: tests/phase13/test_evidence_shapes.py
- FOUND: .planning/phases/13-live-smoke/13-02-SUMMARY.md

**Commits verified (4/4):**
- FOUND: 3d975ea (Task 13-02-01 — evidence_extractor)
- FOUND: af81ca4 (Task 13-02-02 — SMOKE-01 Tier 1+2)
- FOUND: 57a12b0 (Task 13-02-03 — SMOKE-02 Tier 1+2)
- FOUND: 2a38377 (Task 13-02-04 — evidence_shapes)

**Test execution results verified:**
- Plan scope Tier 1 baseline: 17 passed (2 deselected as expected)
- Tier 2 collection: 2 collected
- Phase 14 regression: 30 passed (adapter_contract preserved)
- Wave 0 regression: 6 budget_counter passed (within plan-wide baseline)
