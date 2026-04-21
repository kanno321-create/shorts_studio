---
phase: 15-system-prompt-compression-user-feedback-loop
plan: 01
subsystem: testing
tags: [pytest, subprocess, claude-cli, mock, fixtures, encoding, empirical-evidence]

# Dependency graph
requires:
  - phase: 11-stdin-piping
    provides: "_invoke_claude_cli_once + MagicMock Popen pattern"
  - phase: 13-live-smoke
    provides: "live_smoke marker + --run-live flag + repo_root sys.path pattern"
  - phase: 14-api-adapter-remediation
    provides: "pytest.ini strict-markers + adapter_contract marker baseline"
provides:
  - "tests/phase15/ package scaffold + __init__ marker"
  - "3 shared fixtures: mock_popen factory, tmp_agent_md (10KB Korean), fake_state_dir (14 gate stubs)"
  - "SPC-01 mock-based reproducer (4 tests) — Wave 1 before/after baseline anchor"
  - "SPC-04 empirical evidence — --append-system-prompt-file + --system-prompt-file CLI flag 인식 확증 log"
affects: [15-02-plan, 15-03-plan, 15-04-plan, 15-05-plan, 15-06-plan, 15-07-plan]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Append-only evidence log (.planning/phases/NN/evidence/*.log) — UTF-8 stdlib open('a')"
    - "Mock-only $0 reproducer (unittest.mock.patch on scripts.orchestrator.invokers.subprocess.Popen)"
    - "Non-API CLI probe via nonexistent-path arg — flag recognition 실측 without model 호출"

key-files:
  created:
    - "tests/phase15/__init__.py"
    - "tests/phase15/conftest.py"
    - "tests/phase15/test_encoding_repro.py"
    - "tests/phase15/test_cli_flag_probe.py"
    - ".planning/phases/15-system-prompt-compression-user-feedback-loop/evidence/15-01-cli-probe.log"
  modified: []

key-decisions:
  - "Single commit per task (3 atomic commits) — Wave 0 scope small, no TDD RED/GREEN split necessary since fixtures/anchors are verified by collect + fixture-list + reproducer execution"
  - "Evidence log 헤더 주석 포함 — append-only semantic 명시하여 후속 실행 시 누적 append 가 설계 의도임을 anchor"
  - "Option B (--system-prompt-file) 도 함께 실측 — Wave 1 Option A 선택의 차선책 가용성 기록, 장래 reversion 여지 보존"

patterns-established:
  - "Phase 15 fixture 삼종 세트 (mock_popen/tmp_agent_md/fake_state_dir) — Wave 1~6 plan 전원이 import 하여 reproduce/contract/resume 테스트 구성"
  - "SPC-01 현 drift 상태 고정 2 test (body-in-argv + no-file-path-yet) — Wave 1 에서 flip 될 before/after 기준선"
  - "CLI flag empirical probe — rc!=0 + stderr 파싱으로 flag 인식 증명 (unknown-option 부재를 negative evidence 로 활용)"

requirements-completed: [SPC-01, SPC-04]

# Metrics
duration: 5min14s
completed: 2026-04-21
---

# Phase 15 Plan 01: Wave 0 Reproducer Foundation Summary

**tests/phase15/ scaffold + 3 fixtures + SPC-01 mock reproducer (4 tests) + SPC-04 Claude CLI flag 실측 evidence log — $0, Wave 1~6 downstream 토대 확립**

## Performance

- **Duration:** 5분 14초
- **Started:** 2026-04-21T17:57:46Z
- **Completed:** 2026-04-21T18:03:00Z (approx)
- **Tasks:** 3/3
- **Files created:** 5

## Accomplishments

- **tests/phase15/ 패키지 구조 확립** — `__init__.py` + `conftest.py` (Phase 13 `sys.path` 선례 승계). 3 fixture (`mock_popen`, `tmp_agent_md`, `fake_state_dir`) 가 `pytest --fixtures` 에 등록되어 Wave 1~6 전원이 import 가능.
- **SPC-01 mock-based 재현 4 tests green** — `test_encoding_repro.py`: (1) body-in-argv 고정, (2) no-file-path-yet 고정, (3) rc=1 + 한국어 stderr → `RuntimeError("rc=1")` path, (4) Phase 11 stdin invariant 보존. Wave 1 fix 의 before/after 기준선 anchored. `$0` mock-only.
- **SPC-04 Claude CLI flag 실측 증거 영구 기록** — `--append-system-prompt-file` + `--system-prompt-file` 두 flag 모두 nonexistent 파일 경로에 대해 `rc=1 + "Error: Append system prompt file not found"` stderr 반환. `unknown option` / `unrecognized` 단 한 건도 부재 — negative evidence 로 flag 인식 empirical 증명. Wave 1 Option A 채택 근거 확립.
- **Phase 13/14 baseline 90 tests preserved** (tests/phase13 60 + tests/adapters 30, 26.05s). Phase 11 `test_invoker_stdin.py` 6/6 유지. 전 phase 제로 regression.

## Task Commits

각 task 는 atomically 커밋되었습니다 (3 commits):

1. **Task 15-01-01: tests/phase15/ scaffold + conftest** — `9cadef9` (test)
   - `tests/phase15/__init__.py` (1-line docstring package marker)
   - `tests/phase15/conftest.py` (95 lines, 3 fixtures, 대표님 baseline 5회)
2. **Task 15-01-02: test_encoding_repro.py SPC-01 reproducer** — `07cc3d5` (test)
   - `tests/phase15/test_encoding_repro.py` (117 lines, 4 tests, mock-only)
3. **Task 15-01-03: test_cli_flag_probe.py + evidence** — `1a53cf5` (test)
   - `tests/phase15/test_cli_flag_probe.py` (135 lines, 3 tests, 실 CLI 호출 but $0)
   - `.planning/phases/15-.../evidence/15-01-cli-probe.log` (27 lines, append-only)

**Plan metadata commit:** (이 SUMMARY + STATE.md + ROADMAP.md + REQUIREMENTS.md 묶음) — final commit hash 후속 `gsd-tools commit` 에서 부여.

## Files Created/Modified

### Created (5)
- `tests/phase15/__init__.py` — Phase 15 test package marker.
- `tests/phase15/conftest.py` — 3 fixtures (mock_popen/tmp_agent_md/fake_state_dir) + REPO_ROOT sys.path 보강.
- `tests/phase15/test_encoding_repro.py` — SPC-01 mock reproducer (4 tests): TestCurrentArgvShape (2) + TestRc1Reproduction (1) + TestPhase11Invariant (1).
- `tests/phase15/test_cli_flag_probe.py` — SPC-04 empirical probe (3 tests): binary resolvable + append-file flag + sys-file flag.
- `.planning/phases/15-system-prompt-compression-user-feedback-loop/evidence/15-01-cli-probe.log` — Claude CLI 실측 stdout/stderr/rc 로그, 주석 헤더 + 2 test block = 27 lines.

### Modified (0)
Wave 0 은 pure infra — 기존 파일 수정 없음 (pytest.ini 포함).

## Decisions Made

1. **Evidence log 헤더 주석 + append-only 의도 명시** — 후속 pytest 실행이 로그에 block 을 누적 append 하는 것은 설계 의도임을 헤더에 명시. Wave 1~6 에서 재실행 시 최초 anchored evidence 가 log 최상단에 보존되어 Wave 1 fix 의 근거로 불변.
2. **Option B (`--system-prompt-file`) 도 실측** — Wave 1 은 Option A (`--append-system-prompt-file`, append-semantics 승계) 로 확정되었으나, Option B 도 empirical 확증해두어 장래 reversion 시 근거 재사용 가능. 전체 +1 test, +0 cost.
3. **3 atomic commits (not TDD RED/GREEN split)** — plan 의 `tdd="true"` 지정에도 불구하고 Wave 0 은 fixtures + mock reproducer + empirical probe 의 composition 으로, RED 단계가 "tests 0 items collected" / "fixtures not listed" 같은 infra-level 부정형이 되어 TDD RED commit 을 독립적으로 두는 의미가 희박. 각 task 단위 single commit 으로 응축하여 history 간결화 (Phase 13 test scaffold plan 선례와 동일).
4. **fake_state_dir fixture 를 Wave 0 에서 선제 배치** — plan spec 에 포함되어 있고 Wave 3 UFL-01/02/03 resume 테스트에서 사용 예정. 지금 선제 구축해두면 Wave 3 plan 이 fixture 추가 작업 없이 바로 test 작성 가능.

## Deviations from Plan

**None** — plan executed exactly as written. All 3 tasks 의 acceptance criteria 모든 항목 그대로 충족.

확인된 준수:
- 금기 #3 (try-except 침묵 폴백): `except: pass` / `except Exception:` swallow 단 한 건도 없음 — 모든 assert 는 명시적 message + raise 경로.
- 금기 #5 (STRUCTURE.md Whitelist): `tests/phase15/` 는 `tests/phase13/` + `tests/phase14/` 선례 존재하여 Whitelist 범위 내 (Hook pre_tool_use 차단 없음).
- 필수 #7 (한국어 존댓말): conftest 5회 + test_encoding_repro 5회 + test_cli_flag_probe 11회 = 대표님 호칭 21회, 전원 표준 정중 존댓말.
- 필수 #8 (증거 기반 보고): `.planning/.../evidence/15-01-cli-probe.log` 실측 stderr 기록, `unknown option` 부재 negative evidence 로 flag 인식 증명.

## Issues Encountered

**Evidence log append 누적 현상** — pytest 재실행 시 `_append_evidence` 가 로그에 block 을 누적 append 하는 것을 처음엔 deduplication 문제로 오인했으나, 이는 design intent (durable empirical record) 에 부합. 헤더 주석에 "append-only 로그 — 후속 실행은 이 파일에 block 을 추가합니다" 명시하여 최초 anchored 2 block 이 Wave 1 근거로 영구 보존됨을 문서화. 해결됨.

## User Setup Required

**None** — no external service configuration required. Claude CLI 바이너리는 이미 `C:\Users\PC\AppData\Roaming\npm\claude.CMD` 에 설치되어 있고 (Max 구독 경로), `shutil.which("claude")` 로 resolve 가능. Claude CLI 미설치 환경에서는 `test_cli_flag_probe.py` 3 tests 가 `claude_bin` module-scope fixture 의 `pytest.skip` 로 자동 우회 — CI/local 모두 안전.

## Self-Check: PASSED

- tests/phase15/__init__.py 존재: **FOUND**
- tests/phase15/conftest.py 존재: **FOUND**
- tests/phase15/test_encoding_repro.py 존재: **FOUND**
- tests/phase15/test_cli_flag_probe.py 존재: **FOUND**
- evidence/15-01-cli-probe.log 존재: **FOUND**
- Commit 9cadef9 존재: **FOUND**
- Commit 07cc3d5 존재: **FOUND**
- Commit 1a53cf5 존재: **FOUND**
- Phase 15 7 tests green: **FOUND (7 passed in 2.17s)**
- Phase 13/14 baseline 90 tests: **FOUND (90 passed in 26.05s)**
- Phase 11 regression 6 tests: **FOUND (6 passed in 0.92s)**

## Next Phase Readiness

**Wave 1 Plan 15-02 UNBLOCKED** — 이 plan 의 test 인프라와 CLI flag 실측 증거 위에서 Plan 15-02 가 다음을 수행할 수 있습니다:

1. `scripts/orchestrator/invokers.py` L154~159 의 `--append-system-prompt` + body 직접 전달 argv 를 `--append-system-prompt-file` + tempfile path 로 전환 (SPC-01 fix).
2. `tests/adapters/test_invokers_encoding_contract.py` 신설 — 본 plan 의 `mock_popen` + `tmp_agent_md` fixture import 재사용.
3. `tests/phase15/test_encoding_repro.py::TestCurrentArgvShape` 의 2 test 를 flip (body-NOT-in-argv + file-path-in-argv) — 15-01 이 만든 "현 drift 고정" anchor 를 Wave 1 plan 이 계약 방향 역전으로 재활용.

Downstream Wave 2 (SPC-02/03), Wave 3 (UFL-01/02/03), Wave 4 (UFL-04), Wave 5 (SPC-06 live retry), Wave 6 (acceptance) 모두 `tests/phase15/conftest.py` fixture 세트를 import 할 준비 완료.

**Blocker: 없음.** Budget 변화 없음 ($0). Phase 13/14 baseline 무결. 대표님 Wave 1 진행 승인 대기.

---
*Phase: 15-system-prompt-compression-user-feedback-loop*
*Plan: 01 (Wave 0 — Reproducer Foundation)*
*Completed: 2026-04-21*
