---
phase: 10-sustained-operations
plan: 02
subsystem: audit-drift
tags: [drift-scan, phase-lock, audit-03, audit-04, harness-reuse, sustained-ops]
requires:
  - .claude/deprecated_patterns.json (Phase 5 Plan 01 시드 + Phase 6 Plan 08 확장, 본 Plan 에서 grade/name 필드 추가)
  - C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py (Layer 1 공용 4 함수)
  - .planning/STATE.md frontmatter (phase_lock 필드 삽입처)
  - gh CLI + kanno321-create/shorts_studio 저장소 권한
provides:
  - scripts/audit/drift_scan.py (A-grade drift scanner wrapper, 505 lines)
  - .claude/deprecated_patterns.json grade/name 확장 (A:4 / B:3 / C:1)
  - .planning/STATE.md phase_lock: false default field
  - tests/phase10/test_drift_scan.py (13 tests)
  - tests/phase10/test_phase_lock.py (8 tests)
  - gh labels (drift / phase-10 / auto / critical) repo 수준 pre-created
affects:
  - scripts/audit/ 네임스페이스 확장 (Plan 10-01 의 skill_patch_counter.py 와 나란히)
  - Phase 10 이후 Scheduler (Plan 10-04) 가 매주 월요일 KST 09:00 호출할 standalone CLI 확보
tech-stack:
  added:
    - harness drift_scan.py sys.path import (Layer 1 공용 — naberal_harness v1.0.1)
    - gh CLI subprocess (non-interactive issue auto-create)
  patterns:
    - "Stdlib-only YAML frontmatter parse (no pyyaml) — Phase 6 Plan 09 aggregate_patterns.py 선례"
    - "Lazy graceful-degradation import resolver (--harness-path / --skip-harness-import)"
    - "Exclude-prefix filter (DEFAULT_EXCLUDE_PREFIXES) — docs/tests/meta-code 구분"
key-files:
  created:
    - scripts/audit/drift_scan.py
    - tests/phase10/test_drift_scan.py
    - tests/phase10/test_phase_lock.py
  modified:
    - .claude/deprecated_patterns.json (grade/name 추가, regex/reason byte-identical)
    - .planning/STATE.md (frontmatter phase_lock: false default)
decisions:
  - "harness drift_scan.py 의 load_patterns() 는 `.claude/drift_patterns.json` 을 찾으나 studio 는 `deprecated_patterns.json` 을 사용한다 — wrapper 에서 local fallback loader 로 패턴만 공급하고 scan/write/append 는 harness 재사용"
  - "DEFAULT_EXCLUDE_PREFIXES 를 default 로 적용하여 실제 코드 drift 만 A급으로 판정 (docs/tests/defensive meta-code 의 string-literal 매칭 제외)"
  - "gh issue 생성 실패 시 Project Rule 3 준수 — 명시적 raise (침묵 폴백 금지), Plan 4 weekly cron 이 실패 email 로 인지"
metrics:
  duration: "~28분"
  completed: "2026-04-20T21:32:10+09:00"
  tasks: 2
  tests_added: 21
  commits: 2 (a753ad8 race-merged Task 1 + 4610ede Task 2)
  lines_added:
    - scripts/audit/drift_scan.py: 505
    - tests/phase10/test_drift_scan.py: ~403
    - tests/phase10/test_phase_lock.py: ~245
---

# Phase 10 Plan 02: drift-scan + phase-lock Summary

주 1회 A급 drift 자동 감지 + Phase 차단 신호를 구축했습니다. harness 공용 `scripts/drift_scan.py` 를
sys.path import 로 재사용하고 (`--harness-path` / `--skip-harness-import` flag 포함 graceful
fallback), `deprecated_patterns.json` 8 기존 entries 에 grade/name 필드를 추가했으며 (A급 4: skip_gates /
todo_next / t2v / selenium), A급 drift 발견 시 `.planning/STATE.md` frontmatter 에 phase_lock: true
세팅 + GitHub issue 자동 생성 로직을 완성했습니다. DEFAULT_EXCLUDE_PREFIXES 추가 (Rule 3 deviation)
로 실제 코드 drift 만 A급으로 판정합니다.

## Plan boundary

- Plan 02 는 CLAUDE.md / hooks / skills / agents 를 건드리지 않습니다 (D-2 Lock 자기검증 준수).
- 수정된 파일: `.claude/deprecated_patterns.json` (데이터 파일, Lock 제외) + `.planning/STATE.md` (GSD state) + 신설된 `scripts/audit/drift_scan.py` + `tests/phase10/*`.

## Commits

| Task   | Name                                 | Commit     | Files                                                                                  |
| ------ | ------------------------------------ | ---------- | -------------------------------------------------------------------------------------- |
| Task 1 | Wave 0 smokes + deprecated grade     | a753ad8 *  | `.claude/deprecated_patterns.json`, `.planning/STATE.md`, `tests/phase10/test_drift_scan.py` |
| Task 2 | drift_scan.py wrapper + gh issue     | 4610ede    | `scripts/audit/drift_scan.py`, `tests/phase10/test_drift_scan.py` (시나리오 추가), `tests/phase10/test_phase_lock.py` |

\* a753ad8 은 병렬 executor (Plan 10-01) 가 `git add` race 로 내 Task 1 변경사항을 함께 커밋한 결과입니다 (Deviations §1 참조). commit message 는 `test(10-01): ...` 이지만 실제 diff 에는 Plan 10-02 의 Task 1 파일 3개가 포함되어 있습니다.

## Wave 0 smoke 결과

```
tests/phase10/test_drift_scan.py::test_deprecated_patterns_has_grade_and_name PASSED
tests/phase10/test_drift_scan.py::test_deprecated_patterns_a_grade_exact_four PASSED
tests/phase10/test_drift_scan.py::test_deprecated_patterns_regex_and_reason_byte_identical PASSED
tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default PASSED
tests/phase10/test_drift_scan.py::test_phase5_6_regression_preserved PASSED
```

- 8 entries 전원 grade ∈ {A,B,C} + name 보유
- A급 정확히 4건 (skip_gates_usage / todo_next_session / t2v_code_path / selenium_import)
- 기존 regex + reason 문자열 byte-identical (Phase 5/6 regression 보존)
- STATE.md frontmatter 에 `phase_lock: false` 기본 필드 삽입
- Phase 5 `test_deprecated_patterns_json.py` 5/5 GREEN 확인

## Task 2 결과

```
tests/phase10/test_drift_scan.py  (13 tests) — 5 Wave 0 + 8 main 시나리오
tests/phase10/test_phase_lock.py  ( 8 tests) — helper idempotency + gh subprocess + E2E
전체 21/21 GREEN (1.4s)
```

실증 실행:

```
$ python -m scripts.audit.drift_scan --dry-run --skip-github-issue
→ harness mode, a_grade_count=0, mode=harness

$ python -m scripts.audit.drift_scan --dry-run --skip-github-issue --skip-harness-import
→ local-only mode, a_grade_count=0, mode=local-only
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Parallel executor race on `git add` (Task 1 commit attribution)**
- **Found during:** Task 1 commit attempt
- **Issue:** Plan 10-01 executor 가 병렬로 돌며 공용 git index 에 내 Task 1 파일 (`.claude/deprecated_patterns.json`, `.planning/STATE.md`, `tests/phase10/test_drift_scan.py`) 을 자기 `git add` 와 함께 집어넣어 `test(10-01): skill_patch_counter 8 regression tests RED (A-H)` 커밋 (a753ad8) 에 racing-merge 되었습니다. 내 `git commit` 은 "no changes" 로 실패.
- **Fix:** 이후 Task 2 에서는 파일명을 explicit 하게 나열하여 `git add scripts/audit/drift_scan.py tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py` 로 좁혀 race 를 회피. a753ad8 diff 는 Plan 02 Task 1 의 내용을 그대로 포함하므로 functional 하게는 정상 landing — commit message 만 Plan 10-01 로 표기됐다는 attribution 오류만 남음.
- **Files modified:** 없음 (scoping change only)
- **Commit:** a753ad8 (race-merged) + 4610ede (clean)

**2. [Rule 3 — Blocking] Harness `load_patterns()` 파일명 불일치**
- **Found during:** Task 2 실증 실행
- **Issue:** `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` 의 `load_patterns(studio_root)` 는 `.claude/drift_patterns.json` 을 찾지만, studio 는 Phase 5 Plan 01 이후 `.claude/deprecated_patterns.json` 을 사용합니다. 결과적으로 harness 모드에서 `pattern_defs = []` 반환 → scan_studio 가 zero findings → A급 drift 0 이 무조건 return (false green).
- **Fix:** `drift_scan.py` main() 에서 `harness_patterns if harness_patterns else _local_load_patterns(studio_root)` fallback 을 추가. harness 의 scan_studio / write_conflict_map / append_history 는 그대로 재사용하여 "복사 금지" 원칙 유지. 파일명 일치화는 harness 업데이트 window 에 별도 처리 (수동 pull).
- **Files modified:** `scripts/audit/drift_scan.py` main() body
- **Commit:** 4610ede

**3. [Rule 3 — Blocking] 890 legitimate hits 가 A급으로 집계**
- **Found during:** Task 2 첫 실증 실행 `python -m scripts.audit.drift_scan --dry-run --skip-github-issue`
- **Issue:** harness scan_studio 가 legit document / test fixture / defensive meta-code (e.g. `orchestrator/api/veo_i2v.py` 의 "T2V 부재 assertion", `scripts/validate/phase05_acceptance.py` 의 SC5 T2V-hunt, `.preserved/harvested/` 의 read-only 보존) 에서 금지 패턴을 문자열로 매치하여 890 건의 A급 drift 를 집계 → 매주 Scheduler 가 의미 없는 issue spam 생성.
- **Fix:** `DEFAULT_EXCLUDE_PREFIXES` 정의 + `_filter_findings_by_prefix()` 헬퍼 추가. 기본 제외 21 경로:
  - docs: `.planning/`, `docs/`, `wiki/`
  - tests: `tests/`, `.pytest_cache/`
  - meta: `.claude/{deprecated_patterns.json, failures, memory, agents, skills, hooks/pre_tool_use.py}`, `CLAUDE.md`, `FAILURES.md`, `WORK_HANDOFF.md`
  - runtime: `.git/`, `outputs/`, `.preserved/`
  - defensive: `scripts/validate/{verify_hook_blocks, harness_audit, phase05_acceptance}.py`, `scripts/orchestrator/api/{kling_i2v, runway_i2v, veo_i2v, models}.py`, `scripts/orchestrator/gates.py`, `scripts/notebooklm/fallback.py`, `scripts/harvest/audit_log.md`, 자기 자신 (`scripts/audit/drift_scan.py` + `skill_patch_counter.py`)
  - CLI: `--exclude PREFIX` (repeatable) + `--no-default-excludes` (full-repo audit 용)
- **결과:** 890 → 0 (harness mode) / 875 → 0 (local-only mode). 모든 21 tests GREEN 유지.
- **Files modified:** `scripts/audit/drift_scan.py` (DEFAULT_EXCLUDE_PREFIXES 정의 + main() integration)
- **Commit:** 4610ede

## Acceptance criteria 검증

### Task 1

- [x] `jq '.patterns | length' .claude/deprecated_patterns.json` == 8 (python json 로 확인)
- [x] A 등급 entry 정확히 4 (skip_gates_usage / todo_next_session / t2v_code_path / selenium_import)
- [x] 모든 entry 에 grade + name 필드 존재
- [x] `grep "phase_lock: false" .planning/STATE.md` 1 match
- [x] Wave 0 4 tests PASS
- [x] Phase 5 `test_deprecated_patterns_json.py` 5/5 PASS (count=8 baseline 통과)
- [x] 기존 regex + reason byte-identical (새 필드만 추가)
- [x] BLOCKER #2 redundant safety #1 — gh label 4종 repo 수준 사전 생성 (drift / phase-10 / auto / critical)

### Task 2

- [x] `python -c "...; assert hasattr(drift_scan,'main')"` exits 0 (test_drift_scan_imports_and_exports_public_api 로 대체)
- [x] `pytest tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py -q` — 21 tests GREEN (13 + 8)
- [x] `python -m scripts.audit.drift_scan --dry-run --skip-github-issue --skip-harness-import` exit 0 + `"a_grade_count": 0` + `"mode": "local-only"`
- [x] `grep sys.path.insert` ≥ 1 (실측 1)
- [x] `grep "from drift_scan import"` == 1 (실측 1)
- [x] 4 harness 함수 호출 ≥ 4 (실측 19)
- [x] `grep "'gh', 'issue', 'create'"` ≥ 1 (실측 double-quote 변형 4)
- [x] `grep "drift,critical,phase-10,auto"` ≥ 1 (실측 2)
- [x] `grep "--harness-path\|--skip-harness-import"` ≥ 2 (실측 8)
- [x] `grep "_local_scan_studio\|_local_load_patterns\|local-only"` ≥ 3 (실측 13)
- [x] `wc -l scripts/audit/drift_scan.py` ≥ 150 (실측 505)
- [x] STATE.md frontmatter YAML 파싱 무결성 (regex match 성공)

## Deferred Issues (Out-of-scope)

**Phase 5 / Phase 6 pre-existing regressions (Plan 02 무관):**
전체 sweep `pytest tests/phase05 tests/phase06 -q` 에서 10 failures — 모두 Phase 9.1 engine wiring /
Phase 6 MOC path drift 로 인한 것으로 Plan 02 와 무관합니다:

1. `test_api_adapters_under_soft_caps` — Phase 9.1 elevenlabs.py/shotstack.py 라인 수 증가
2. `test_runway_valid_call_returns_path` — Phase 9.1 Runway model `gen3_alpha_turbo` → `gen4.5` 전환
3. `test_phase05_acceptance` 3종 — acceptance E2E 가 위 실패를 cascade
4. `test_moc_frontmatter_unchanged_scaffold` — `wiki/render/MOC.md` status `scaffold` → `partial`
5. `test_default_skill_path_is_the_2026_install` — `secondjob_naberal` → `shorts_naberal` 경로 drift
6. `test_phase06_acceptance` 2종 — 위 실패 cascade

이들은 STATE.md 세션 이력 에도 "Plan 08 deprecated_patterns 6->8 expansion" + "Phase 9.1 drift" 로 이미 기록된 pre-existing 이슈이며, 해결은 별도 plan (향후 regression 갱신 배치) 에 위임됩니다. Plan 02 자체의 regression 검증 (`test_deprecated_patterns_json.py` 5/5) 은 GREEN 확인.

**BLOCKER #2 redundant safety #2 — Plan 4 GH Actions `Ensure labels exist` step:**
Plan 4 (`drift-scan-weekly.yml`) 에서 redundant 로 `gh label create` 3종을 재호출하는 step 은 Plan 4 implementation 시 추가 대기 (Plan 02 scope 밖).

## Reusable Assets Used

- `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` — 4 public 함수 (load_patterns / scan_studio / write_conflict_map / append_history) sys.path import 로 재사용 (복사 금지)
- Phase 6 Plan 09 `scripts/failures/aggregate_patterns.py` stdlib-only CLI 패턴 (argparse + UTF-8 reconfigure + sys.stdout.reconfigure Windows cp949 가드)
- Phase 7 Plan 03 mocks monkeypatch pattern (`monkeypatch.setattr(mod.subprocess, "run", _fake_run)`)
- Phase 9 conftest `freeze_kst` 패턴 (test_phase_lock 의 datetime freezer)

## Self-Check: PASSED

### Files

- [x] FOUND: scripts/audit/drift_scan.py
- [x] FOUND: tests/phase10/test_drift_scan.py
- [x] FOUND: tests/phase10/test_phase_lock.py
- [x] FOUND: .claude/deprecated_patterns.json (수정)
- [x] FOUND: .planning/STATE.md (수정 — phase_lock: false)

### Commits

- [x] FOUND: a753ad8 (race-merged Task 1)
- [x] FOUND: 4610ede (Task 2)

### Pipeline evidence

- [x] 21 tests GREEN (tests/phase10/test_drift_scan.py + test_phase_lock.py)
- [x] `python -m scripts.audit.drift_scan --dry-run --skip-github-issue` exit 0 + a_grade_count=0 (harness mode)
- [x] `--skip-harness-import` local-only mode 정상 (WARNING #4 확보)
- [x] `--clear-lock` 서브커맨드 작동
- [x] Phase 5 `test_deprecated_patterns_json.py` 5/5 GREEN
- [x] gh labels 4종 repo 수준 생성 완료

---

Next:
- Plan 10-03 (KPI fetch) + Plan 10-04 (Scheduler) — Wave 2 parallel 가능
- Plan 10-04 에서 `drift-scan-weekly.yml` GH Actions 에 `Ensure labels exist` step (redundant #2) + `--harness-path=../harness/scripts` 인자 전달 + 실패 시 email → `kanno3@naver.com`
- Plan 10-02 가 만든 CLI 는 이미 standalone — 대표님 수동 `python -m scripts.audit.drift_scan` 도 가능
