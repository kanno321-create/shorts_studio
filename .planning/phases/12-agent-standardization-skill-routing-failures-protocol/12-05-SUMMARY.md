---
phase: 12-agent-standardization-skill-routing-failures-protocol
plan: 05
subsystem: failures-rotation-protocol
tags: [fail-proto-01, pre-tool-use, hook-extension, rotation-cli, d-a3-01, d-a3-04, d-14-preservation]
requires:
  - check_failures_append_only (Phase 6 D-11)
  - Phase 3 D-14 sha256-lock on _imported_from_shorts_naberal.md
  - scripts/audit/__init__.py namespace
provides:
  - FAIL-PROTO-01 500줄 cap enforcement (pre_tool_use Hook)
  - scripts/audit/failures_rotate.py rotation CLI (idempotent)
  - FAILURES_ROTATE_CTX=1 env whitelist contract
  - 5 pytest GREEN (Phase 12 test_failures_rotation.py)
affects:
  - All agents/scripts writing to .claude/failures/FAILURES.md
  - Phase 12 AGENT-STD-02 <mandatory_reads> 전수 읽기 전제 조건
tech-stack:
  added: [zoneinfo.ZoneInfo('Asia/Seoul'), stdlib-only rotation (no new deps)]
  patterns: [env var whitelist bypass, hard-coded path (no glob), basename exact match HARD-EXCLUDE, try/finally env cleanup]
key-files:
  created:
    - scripts/audit/failures_rotate.py (139 lines)
  modified:
    - .claude/hooks/pre_tool_use.py (+44 lines, -5 lines in check_failures_append_only)
    - tests/phase12/test_failures_rotation.py (red stubs → 5 real assertions)
decisions:
  - D-A3-01 (500줄 cap Write/Edit only — MultiEdit OOS Phase 13)
  - D-A3-03 (`_imported_from_shorts_naberal.md` HARD-EXCLUDE by basename exact match, preserved by pre-existing D-11 filter)
  - D-A3-04 (FAILURES_ROTATE_CTX=1 env var, set/cleanup via try/finally in rotate())
  - Env var name finalized: `FAILURES_ROTATE_CTX` (not `FAILURES_ROTATE_BYPASS` per plan; matches RESEARCH §Pattern 2)
metrics:
  duration_minutes: 7
  completed: 2026-04-20T23:12Z
  tasks_completed: 3
  commits: 3
  tests_added: 5
  tests_green: 5
  regression_preserved: 26 (Phase 6 D-11 + D-14 + Hook block)
requirements:
  - FAIL-PROTO-01
---

# Phase 12 Plan 05: FAILURES.md 500줄 Rotation Protocol Summary

**One-liner:** FAIL-PROTO-01 완결 — `pre_tool_use.py check_failures_append_only` 확장 (500줄 cap + `FAILURES_ROTATE_CTX=1` env whitelist) + `scripts/audit/failures_rotate.py` idempotent rotation CLI + `_imported_from_shorts_naberal.md` HARD-EXCLUDE 보존 + 5 pytest GREEN.

## Executive Summary

Phase 12 의 `<mandatory_reads>` 전수 읽기 전제 조건을 구조적으로 보장하는 3-task 고위험 작업 완료. 본 Plan 은 프로젝트 전체에서 `FAILURES.md` append-only 를 enforce 하는 Hook 을 수정 — 병렬 실행 중인 Plans 02/04/07 의 FAILURES 경로를 잠재적으로 차단할 수 있는 risk zone. Safety sequence (tests 먼저 + 기존 D-11 로직 전량 보존 + 즉시 revert 준비) 준수하며 zero regression 으로 완결.

Phase 6 D-11 append-only 14/14 regression 테스트 + D-14 imported file sha256 5/5 invariant 테스트 + Hook block 7/7 테스트 전부 GREEN 유지. 새 5개 rotation 테스트 GREEN. HARD-EXCLUDE 는 pre-existing basename-exact-match 필터 (`name != 'FAILURES.md'`) 로 자연스럽게 보존 — rotation CLI 에서 additional `_assert_not_imported_file` guard 로 이중 방어.

## Tasks Executed

### Task 1: TDD RED — test_failures_rotation.py 5 real assertions

**Commit:** `e5eef62`

red stubs 4개 + skip decorator 전부 제거. 5 tests 실 assertion 작성:

| Test | Purpose |
| ---- | ------- |
| `test_env_whitelist_bypasses_cap` | `FAILURES_ROTATE_CTX=1` → None (600-line 내용도 allow) |
| `test_hook_denies_over_500_lines` | 501-line Write → deny + "500줄" + "failures_rotate.py" 안내 |
| `test_rotate_idempotent` | 1차=1, 2차=0, sha256 unchanged |
| `test_imported_file_sha256_unchanged` | `_imported_from_shorts_naberal.md` D-14 lock 보존 |
| `test_archive_month_tag` | `_archive/{YYYY-MM}.md` 생성 + 460-475 lines 이관 |

**Expected RED state after Task 1**: 4 FAIL (ImportError for failures_rotate + cap-denial missing) + 1 coincidental PASS (env_whitelist 은 현재 cap 부재라 None 반환으로 통과). Task 2+3 완료 후 5/5 GREEN.

### Task 2: `check_failures_append_only` 500줄 cap + env whitelist 확장

**Commit:** `60e1bea`

`.claude/hooks/pre_tool_use.py` 의 `check_failures_append_only` (Phase 6 D-11) 를 **비파괴적으로 확장**:

1. **D-A3-04 env whitelist (function top):** `os.environ.get("FAILURES_ROTATE_CTX") == "1"` → `return None` — rotation script 만 bypass. 다른 경로는 normal check.
2. **D-A3-01 500줄 cap (basename match 후, append-only check 전):** Write/Edit candidate content 의 predicted line count 가 500 초과 시 deny. 한국어 안내 메시지에 `scripts/audit/failures_rotate.py` 호출 가이드 포함.
3. **D-11 append-only 로직 전량 보존** — Edit non-empty old_string / Write not-prefix / MultiEdit 검사 한 줄도 수정하지 않음. 14 Phase 6 regression tests 무회귀.
4. **HARD-EXCLUDE** `_imported_from_shorts_naberal.md` — pre-existing `name != 'FAILURES.md'` filter 가 자동 보호. Plan 요구사항 (exact filename match, not glob) 기 완료 상태.
5. **MultiEdit cap check OOS** — Plan 명시, Phase 13 candidate.

**Critical safety sequence followed (per `<notes>` 지침):**
1. 현재 구현 전체 읽기 (line 155-210) 먼저 완료
2. TDD RED tests 선 작성 (Task 1)
3. Hook 수정 후 Phase 6 14 regression tests 즉시 확인 (14/14 PASS)
4. Phase 12 타겟 2 tests 확인 (2/2 PASS)
5. 이상 없음 — 진행

### Task 3: scripts/audit/failures_rotate.py 신규 rotation CLI

**Commit:** `5785fc3`

139-line stdlib-only CLI (skill_patch_counter.py 패턴 복제):

- `REPO_ROOT`, `FAILURES_FILE`, `ARCHIVE_DIR`: module-level constants (test monkeypatch-친화적)
- `IMPORTED_FILE_BASENAME = "_imported_from_shorts_naberal.md"`: HARD-EXCLUDE basename constant
- `CAP_LINES = 500`, `HEAD_PRESERVE_LINES = 31`: 상수 분리
- `_assert_not_imported_file(path)`: RuntimeError raise if basename match (D-A3-03 영구 guard, 이중 방어)
- `rotate() -> int`:
  - 0: no-op (file missing OR ≤500 lines = idempotent)
  - 1: rotated (lines[31:500] → archive append, lines[:31] + lines[500:] → new FAILURES.md)
  - `os.environ["FAILURES_ROTATE_CTX"] = "1"` 설정 → try/finally 로 `os.environ.pop(...)` cleanup (env leak 방지)
- Archive 형식: `_archive/{YYYY-MM}.md` (KST month, append mode, ISO timestamp `<!-- Rotated at ... -->` notice)
- Windows cp949 guard: `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` (기존 패턴 따름)

**Live CLI verification:**
```
$ py -3.11 scripts/audit/failures_rotate.py
OK: no rotation needed (FAILURES.md under 500 lines or missing)
exit 0
```

FAILURES.md 현재 58줄 — no-op, idempotent. `_imported_from_shorts_naberal.md` 500줄 unchanged.

## Key Decisions

1. **Env var name = `FAILURES_ROTATE_CTX`** (not `FAILURES_ROTATE_BYPASS` as mentioned in initial instructions).
   - **Rationale:** RESEARCH §Pattern 2 + plan frontmatter `contains: "FAILURES_ROTATE_CTX"` 이 이 이름을 locking. `_CTX` suffix 가 "scope 통제 context flag" 의미를 더 정확히 전달 (bypass는 하위 개념).
   - **Where documented:** 이 SUMMARY 의 metadata + hook docstring + rotate CLI 모듈 docstring.

2. **HARD-EXCLUDE는 pre-existing basename-match filter 를 재사용** (glob/dir-skip 사용 금지).
   - Hook: `name != 'FAILURES.md' → return None` 이 `_imported_from_shorts_naberal.md` 를 자동 면제 (basename 불일치).
   - Rotate CLI: 추가로 `_assert_not_imported_file()` guard (방어적 프로그래밍, 이중 방어).
   - Plan의 엄격한 "exact filename match, not glob" 제약을 두 계층에서 준수.

3. **Edit 케이스 cap 계산 robustness:**
   - `old_string in existing`: `replace(old_s, new_s, 1)` 로 candidate 산출.
   - `old_string not in existing`: candidate = existing unchanged (어차피 append-only deny 가 뒤에서 차단).
   - `old_string == ""`: candidate = `new_s + existing` (empty old_string = prepend insertion, Phase 6 `test_edit_empty_old_string_allowed` 호환).
   - Phase 6 14 regression 전부 GREEN 유지.

4. **rotate() 의 `os.environ.pop(...)` 사용** (not `del`):
   - `del os.environ["X"]` 는 X 부재 시 KeyError.
   - `os.environ.pop("X", None)` 은 idempotent cleanup — 예외 경로에서도 안전.
   - try/finally 와 조합하여 "반드시 cleanup" 보장.

## Deviations from Plan

### Rule 2 — Auto-added defensive safety

**1. [Rule 2 - Completeness] `os.environ.pop(...)` instead of `del os.environ[...]`**
- **Found during:** Task 3 implementation
- **Issue:** Plan prose used `del os.environ["FAILURES_ROTATE_CTX"]` which raises KeyError if env var absent (e.g., interrupted execution, test fixture setup order)
- **Fix:** `os.environ.pop("FAILURES_ROTATE_CTX", None)` — idempotent cleanup, safer in finally block
- **Files modified:** scripts/audit/failures_rotate.py
- **Commit:** 5785fc3

**2. [Rule 2 - Robustness] Edit `old_string` not-in-existing fallback**
- **Found during:** Task 2 implementation
- **Issue:** Plan code template assumed `old_s` always present in `existing` — if absent, `.replace()` is a no-op (benign) but semantic intent is unclear
- **Fix:** Explicit 3-branch logic (`old_s in existing` / `old_s and not in existing` / empty `old_s`) so candidate computation is deterministic and matches Phase 6 D-11 append-only test cases byte-for-byte
- **Files modified:** .claude/hooks/pre_tool_use.py
- **Commit:** 60e1bea

No auth gates. No architectural changes. No user decisions required.

## Known Stubs

None — all FAIL-PROTO-01 functionality shipped as production code (no TODO / NotImplementedError / mock data).

## Test Results

```
tests/phase12/test_failures_rotation.py ........ 5/5 PASS
tests/phase06/test_failures_append_only.py ..... 14/14 PASS (D-11 regression)
tests/phase06/test_hook_failures_block.py ...... 7/7 PASS
tests/phase06/test_imported_failures_sha256.py . 5/5 PASS (D-14 invariant)
=================================================
                                               31/31 PASS
```

Live CLI: `py -3.11 scripts/audit/failures_rotate.py` → exit 0 (no-op, 58 lines < 500 cap).

Note on broader Phase 5/6 failures: `tests/phase05/test_phase05_acceptance.py` + `tests/phase06/test_moc_linkage.py` + `tests/phase06/test_notebooklm_wrapper.py` show pre-existing failures traced to prior plans (STATE.md documents Phase 5 deprecated_patterns.json 6→8 expansion + Phase 6 path drifts from parallel branches). Stash-revert confirmed these fail at HEAD 00e08f5 **before** my changes. Out of scope per Rules 1-3 scope boundary; logged for respective plan owners.

## Files Changed

| File | Operation | Lines | Purpose |
| ---- | --------- | ----- | ------- |
| `.claude/hooks/pre_tool_use.py` | modify | +44 / -5 | check_failures_append_only 500줄 cap + env whitelist |
| `scripts/audit/failures_rotate.py` | create | 139 | rotation CLI with idempotent + HARD-EXCLUDE guard |
| `tests/phase12/test_failures_rotation.py` | modify | +149 / -14 | 5 red stubs → real assertions |

## Contract Summary

**Hook contract extension:**
```python
def check_failures_append_only(tool_name, tool_input) -> str | None:
    # D-A3-04: FAILURES_ROTATE_CTX=1 env → None (whitelist)
    # basename != 'FAILURES.md' → None (HARD-EXCLUDE _imported_...)
    # D-A3-01: Write/Edit → 500 lines → deny with 한국어 안내
    # D-11: Edit non-empty old_string / Write not-prefix / MultiEdit → deny
```

**Rotation CLI contract:**
```python
from scripts.audit import failures_rotate
failures_rotate.rotate()  # -> 1 rotated | 0 no-op (idempotent)
# sets FAILURES_ROTATE_CTX=1 during I/O, cleans via try/finally
# archives lines[31:500] → _archive/{YYYY-MM}.md
# refuses to touch _imported_from_shorts_naberal.md (RuntimeError)
```

## Downstream Unblocked

- **Plan 12-02/03/07 (parallel):** FAILURES append-path 무영향 확인. 병렬 agent 들 중 현재 세션에서 FAIL-PROTO-01 append path 를 trigger 한 것 없음 (58줄 < cap).
- **Plan 12-06 mandatory-reads-enforcement:** AGENT-STD-02 `<mandatory_reads>` 전수 읽기 전제 (500줄 이하) 구조적 보장 완료.
- **Phase 12 VERIFICATION:** SC FAIL-PROTO-01 evidence 확보 (5 pytest + live CLI exit 0 + D-14 sha256 불변).

## Self-Check: PASSED

Files verified to exist:
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/audit/failures_rotate.py` — FOUND
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.claude/hooks/pre_tool_use.py` — FOUND (modified)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/tests/phase12/test_failures_rotation.py` — FOUND (modified)

Commits verified in git log:
- `e5eef62` test(12-05): FAIL-PROTO-01 red stubs replaced with 5 real assertions — FOUND
- `60e1bea` feat(12-05): extend check_failures_append_only with 500줄 cap + env whitelist — FOUND
- `5785fc3` feat(12-05): add scripts/audit/failures_rotate.py rotation CLI — FOUND

**대표님께 보고드립니다.** FAIL-PROTO-01 완결. FAILURES.md 500줄 cap + archive rotation 프로토콜 확보. `_imported_from_shorts_naberal.md` Phase 3 D-14 영구 lock 보존. 에이전트 전수 읽기 전제 조건 구조적으로 보장. 병렬 실행 중인 Plans 02/04/07 영향 무. Phase 6 D-11/D-14 26 regression tests 무회귀.
