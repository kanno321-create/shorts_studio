---
phase: 13-live-smoke
plan: 01
subsystem: live-smoke-infrastructure
tags: [wave-0, preflight, pytest-marker, budget-counter, fixtures, smoke]
dependency-graph:
  requires:
    - pytest 8.x (Phase 4 baseline)
    - Phase 8 OAuth (config/client_secret.json + config/youtube_token.json)
    - Phase 9.1 invokers.py (Claude CLI Max 구독 경로)
    - Phase 14 pytest.ini (adapter_contract marker + --strict-markers)
  provides:
    - live_smoke pytest marker (tests/phase13/ + opt-in via --run-live)
    - BudgetCounter + BudgetExceededError SSOT (scripts/smoke/budget_counter.py)
    - phase13_preflight.py CLI (4 sanity checks + rc=0/1 contract)
    - Phase 13 공용 pytest fixtures (tests/phase13/conftest.py)
    - 4 golden evidence JSON fixtures (tests/phase13/fixtures/)
    - .planning/phases/13-live-smoke/evidence/ writable probe
  affects:
    - Wave 1 (Plans 13-02): producer/supervisor live smoke — budget_counter import
    - Wave 2 (Plans 13-03): YouTube upload — conftest.tmp_evidence_dir 사용
    - Wave 3 (Plans 13-04): Budget cap — budget_counter live wire
    - Wave 4 (Plan 13-05): E2E — 전체 fixture + marker 동원
    - Wave 5 (Plan 13-06): Phase gate — adapter_contract 30 tests 보존 검증
tech-stack:
  added:
    - (없음 — 기존 pytest 8.x + stdlib json/subprocess/pathlib 사용)
  patterns:
    - Phase 14 conftest.py repo_root + sys.path 패턴 재사용
    - Phase 11 phase11_full_run.py Windows cp949 guard + _load_dotenv 패턴 승계
    - Phase 9.1 _check_cost_cap named RuntimeError (→ BudgetExceededError 진화)
    - pytest addoption + collection_modifyitems hook (Phase 13 신규 도입)
key-files:
  created:
    - scripts/smoke/budget_counter.py (136 lines)
    - scripts/smoke/phase13_preflight.py (218 lines)
    - tests/phase13/__init__.py (package marker)
    - tests/phase13/conftest.py (99 lines — 3 fixture + 2 hook + repo_root)
    - tests/phase13/test_budget_counter.py (94 lines — 6 tests)
    - tests/phase13/fixtures/sample_producer_output.json
    - tests/phase13/fixtures/sample_supervisor_output.json
    - tests/phase13/fixtures/sample_smoke_upload.json
    - tests/phase13/fixtures/sample_smoke_e2e.json
  modified:
    - pytest.ini (+1 line — live_smoke marker)
decisions:
  - "live_smoke marker 는 Phase 14 adapter_contract 바로 아래 등록 — 동일 스타일 유지"
  - "BudgetExceededError 는 RuntimeError 상속 — Phase 9.1 _check_cost_cap 기존 패턴 호환 + 상위 좁은 catch 지원"
  - "evidence_path 는 constructor 주입 — SSOT 가 경로 결정을 호출자에게 위임 (Wave 별 다른 evidence JSON 파일명 가능)"
  - "total_usd 는 property (entries[] view) — mutable 중간 state 제거로 drift 방지"
  - "round(..., 4) 적용 — float epsilon drift 방지 (0.1+0.2=0.3000001 case)"
  - "pytest_addoption + collection_modifyitems 신규 도입 — Phase 14 에는 없던 hook, live_smoke 자동 skip 구조"
  - "check_youtube_oauth 는 파일 integrity + refresh_token field 만 확인, 실 API refresh 호출은 Wave 2 책임"
  - "check_env_keys 의 scripts.orchestrator._load_dotenv_if_present ImportError 는 명시적 stderr 기록 후 shell env fallback — 금기 #3 준수"
metrics:
  duration: "6m22s"
  start_iso: "2026-04-21T14:41:53Z"
  end_iso: "2026-04-21T14:48:15Z"
  tasks: 4
  new_files: 9
  modified_files: 1
  commits: 5
  tests_added: 6
  tests_total_green: 36  # 6 Phase 13 Tier 1 + 30 Phase 14 adapter_contract preserved
completed: 2026-04-21
---

# Phase 13 Plan 01: Wave 0 Preflight Infrastructure Summary

**One-liner**: Wave 0 구축 완료 — live_smoke pytest marker + BudgetCounter SSOT + Phase 13 fixtures + 4-check preflight CLI 를 일괄 anchoring 하여 Wave 1~5 live run 의 모든 infrastructure 전제조건을 충족.

---

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 13-01-01 | pytest.ini live_smoke marker 등록 | `56b5da0` | pytest.ini |
| 13-01-02 RED | Failing tests for BudgetCounter | `2a9eb3d` | tests/phase13/__init__.py, tests/phase13/test_budget_counter.py |
| 13-01-02 GREEN | BudgetCounter + BudgetExceededError implementation | `8a7a1c1` | scripts/smoke/budget_counter.py |
| 13-01-03 | conftest.py + 4 golden fixtures | `3827ae5` | tests/phase13/conftest.py, tests/phase13/fixtures/*.json |
| 13-01-04 | phase13_preflight.py CLI | `4349deb` | scripts/smoke/phase13_preflight.py |

**Commit discipline**: per-task atomic (TDD split Task 13-01-02 into RED + GREEN separate commits per tdd.md).

---

## Verification Results

### 1. pytest.ini markers (`grep -E`)
```
    adapter_contract: Phase 14 adapter contract tests (tests/adapters/) — run with -m adapter_contract
    live_smoke: Phase 13 live smoke tests (tests/phase13/) — real API 호출, opt-in via --run-live flag + explicit -m live_smoke
```
Phase 14 marker preserved; Phase 13 marker added.

### 2. Tier 1 baseline (always-run, no API)
```
pytest tests/phase13/ -m "not live_smoke" --no-cov -q
→ 6 passed in 0.09s
```
SMOKE-05 core 6 tests GREEN — BudgetCounter initial state + charge + overage + $0 entry + persist + metadata.

### 3. Phase 14 regression (adapter_contract 30 tests)
```
pytest tests/adapters/ -m adapter_contract -v --no-cov
→ 30 passed in 0.91s
```
Phase 14 회귀 없음 — pytest.ini addopts 미수정 + adapter_contract marker 보존.

### 4. live_smoke collection (Wave 0 에는 0 live tests 예정)
```
pytest -m live_smoke --collect-only -q --no-cov
→ no tests collected (1502 deselected)
```
Marker 등록은 완료 (no error); Wave 1~4 에서 실 live_smoke test 추가 예정.

### 5. BudgetCounter import smoke
```
py -3.11 -c "from scripts.smoke.budget_counter import BudgetCounter, BudgetExceededError; ..."
→ OK
```

### 6. phase13_preflight.py 실행 (현재 환경)
```
py -3.11 scripts/smoke/phase13_preflight.py
→ [OK] claude_cli: 2.1.63 (Claude Code)
  [OK] youtube_oauth: has_refresh_token=True
  [OK] env_keys: required 3/3 + FAL_KEY + optional 2종
  [OK] evidence_dir: writable
  Overall: ALL_PASS (rc=0)
```
Wave 1~5 진입 전 4 sanity check 모두 통과 — 실 환경이 live run ready 상태.

---

## Success Criteria 체크

- [x] 4 tasks executed (per-task commit 5건: RED+GREEN split 적용)
- [x] pytest `--markers` 에 live_smoke 등록 확인
- [x] `from scripts.smoke.budget_counter import BudgetCounter, BudgetExceededError` 성공
- [x] pytest Tier 1 ≥5 tests green (6/6 green)
- [x] `import tests.phase13` + conftest 성공 (collection 에러 없음)
- [x] phase13_preflight.py rc=0 (4 check ALL_PASS — 현재 환경)
- [x] evidence dir writable (probe PASS)
- [x] 4 golden fixture JSON 모두 UTF-8 parseable
- [x] Phase 14 regression 보존 (30 adapter_contract tests green)
- [x] STATE.md + ROADMAP.md 갱신 (final metadata commit 에서 반영)
- [x] SUMMARY.md at `.planning/phases/13-live-smoke/13-01-SUMMARY.md`

---

## Deviations from Plan

### Minor Adjustments (문서화)

**1. [문서화] Task 13-01-02 grep acceptance criteria — docstring occurrence counting**
- **Found during:** Task 13-01-02 verification
- **Issue:** Plan acceptance criteria 중 `grep -c "class BudgetCounter"` returns 1 조건은, 구현 시 module docstring 의 Contract 블록에 class 선언을 예시로 인용하면 자연스럽게 grep count=2 가 됨 (실제 class 정의 1줄 + docstring 내 예시 1줄).
- **Resolution:** material acceptance 는 통과 (class 존재 + import 성공 + 6 tests GREEN). docstring 내 Contract 블록은 13-01-PLAN.md `<interfaces>` 섹션 그대로 반영하여 계약을 명시 — 삭제보다 유지가 SSOT 완전성에 유리.
- **Files:** scripts/smoke/budget_counter.py L9-15 (docstring Contract example)
- **Commit:** `8a7a1c1`

### CLAUDE.md-driven adjustments

**2. [Rule 2 - 필수] 금기 #3 침묵 폴백 방지**
- **Found during:** Task 13-01-04 설계
- **Issue:** `check_env_keys` 의 `from scripts.orchestrator import _load_dotenv_if_present` 가 ImportError 발생 가능 (본 모듈이 standalone 실행되는 경우).
- **Resolution:** `try/except ImportError` 에서 `sys.stderr.write(...)` 로 명시적 기록 + shell env fallback — CLAUDE.md 금기사항 #3 "try-except 침묵 폴백 금지" 준수.
- **Files:** scripts/smoke/phase13_preflight.py L128-133
- **Commit:** `4349deb`

**3. [Rule 2 - 필수] 한국어 존댓말 baseline 적용**
- **Found during:** 전체 artifacts 작성
- **Issue:** CLAUDE.md 필수사항 #7 — 한국어 존댓말 baseline + 대표님 호칭.
- **Resolution:** 모든 docstring + error message + 출력 헤더에 "대표님" + 존댓말 일관 적용:
  - BudgetExceededError message: `"예산 상한 초과 ... 대표님 중단 (직전: ...)"`
  - preflight 헤더: `"Phase 13 Preflight Report (대표님)"`
  - conftest fixture docstring: 존댓말 유지
- **Commits:** `8a7a1c1`, `3827ae5`, `4349deb`

### Authentication Gates

없음 — Wave 0 은 infrastructure 전용 ($0 cost, no external API calls).

**4. [Rule 1 - Bug] gsd-tools requirements mark-complete 오표시 revert**
- **Found during:** state_updates 단계
- **Issue:** PLAN.md frontmatter `requirements: [SMOKE-01~06]` 은 본 Plan 이 관련된 requirement 를 의미하지만, `gsd-tools requirements mark-complete` 를 호출하면 Wave 0 infrastructure 완료만으로 requirements 전체를 [x] 표시함. 실제 SMOKE-01~06 은 Wave 1~5 의 live run 이 요구되는 requirement 로, Plan 13-06 (Wave 5 Phase Gate) 에서만 정당하게 close 가능.
- **Resolution:** `git checkout -- .planning/REQUIREMENTS.md` 로 revert — Wave 0 Plan 에서는 requirements 를 mark-complete 하지 않음. Plan 13-06 (Wave 5) 가 Phase Gate 에서 SMOKE-01~06 check 를 수행한 뒤 마크.
- **Files:** .planning/REQUIREMENTS.md (revert — 수정 없음)
- **Commit:** (no commit — revert 만 수행)

---

## Interfaces Exposed to Wave 1~5

### scripts/smoke/budget_counter.py

```python
class BudgetExceededError(RuntimeError): ...

class BudgetCounter:
    def __init__(self, cap_usd: float, evidence_path: Path) -> None: ...
    @property
    def total_usd(self) -> float: ...
    def charge(self, provider: str, amount_usd: float,
               metadata: dict | None = None) -> None: ...
    def persist(self) -> Path: ...
```

**Evidence schema** (persist() output):
```json
{
  "cap_usd": 5.00,
  "total_usd": 2.93,
  "breached": false,
  "entry_count": 6,
  "entries": [
    {"timestamp": "2026-04-21T22:30:15+09:00", "provider": "kling",
     "amount_usd": 0.35, "cumulative_usd": 0.35, "metadata": {...}},
    ...
  ]
}
```

### tests/phase13/conftest.py

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `repo_root` | session | studios/shorts/ Path (Phase 14 계약 승계) |
| `tmp_evidence_dir` | function | tmp evidence/ + SHORTS_PUBLISH_LOCK_PATH monkeypatch |
| `fixtures_dir` | function | tests/phase13/fixtures/ Path |
| `fake_claude_cli_output` | function | mock producer JSON payload |

**Hooks:**
- `pytest_addoption` — `--run-live` CLI flag
- `pytest_collection_modifyitems` — skip live_smoke unless `--run-live`

### scripts/smoke/phase13_preflight.py

```python
def check_claude_cli() -> dict           # {ok, version, path, error}
def check_youtube_oauth() -> dict         # {ok, has_refresh_token, token_path, error}
def check_env_keys() -> dict              # {ok, missing_required, any_of_missing, present_optional}
def check_evidence_dir_writable() -> dict # {ok, path, error}
def main() -> int                         # 0 if ALL_PASS, 1 otherwise
```

---

## 대표님 보고 블록 (한국어 존댓말)

Phase 13 Plan 01 (Wave 0 Preflight Infrastructure) 가 완료되었습니다. 4 Task 전수 atomic commit 5건으로 처리하였으며, pytest Tier 1 6개 테스트 green + Phase 14 adapter_contract 30 개 회귀 보존 + preflight CLI 4 체크 ALL_PASS (rc=0) 확인하였습니다. Wave 1~5 가 필요한 live_smoke marker, BudgetCounter SSOT, 공용 fixture 5종, preflight CLI 모두 anchoring 완료되어 Wave 1 진입 가능한 상태입니다.

---

## Known Stubs

없음 — Wave 0 은 infrastructure 전용 이며 모든 artifact 가 완전 wiring. Wave 1~4 가 생성할 evidence JSON 은 본 Plan scope 외 (sample golden fixture 는 제공됨).

---

## Next Actions

**Wave 1 (Plan 13-02) 실행 전 필수:**
1. 대표님께 live_smoke 진입 승인 득 (Wave 1 은 Claude CLI only — $0 예상)
2. `py -3.11 scripts/smoke/phase13_preflight.py` 재실행 → rc=0 재확인
3. BudgetCounter instance 를 Wave 1 테스트 시작 시 초기화 + evidence/budget_usage.json 에 persist

**본 Plan 의 완료 가능 조건**: 위 Verification Results 전수 green.

---

## Self-Check: PASSED

**Files verified (11/11):**
- FOUND: pytest.ini
- FOUND: scripts/smoke/budget_counter.py
- FOUND: scripts/smoke/phase13_preflight.py
- FOUND: tests/phase13/__init__.py
- FOUND: tests/phase13/conftest.py
- FOUND: tests/phase13/test_budget_counter.py
- FOUND: tests/phase13/fixtures/sample_producer_output.json
- FOUND: tests/phase13/fixtures/sample_supervisor_output.json
- FOUND: tests/phase13/fixtures/sample_smoke_upload.json
- FOUND: tests/phase13/fixtures/sample_smoke_e2e.json
- FOUND: .planning/phases/13-live-smoke/13-01-SUMMARY.md

**Commits verified (5/5):**
- FOUND: 56b5da0 (Task 13-01-01 — pytest.ini marker)
- FOUND: 2a9eb3d (Task 13-01-02 RED — failing tests)
- FOUND: 8a7a1c1 (Task 13-01-02 GREEN — BudgetCounter impl)
- FOUND: 3827ae5 (Task 13-01-03 — conftest + fixtures)
- FOUND: 4349deb (Task 13-01-04 — phase13_preflight CLI)
