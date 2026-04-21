---
phase: 15-system-prompt-compression-user-feedback-loop
plan: 02
subsystem: orchestrator-cli-invoker
tags: [subprocess, claude-cli, tempfile, encoding, argv, korean, adapter-contract, spc-01, spc-05]

# Dependency graph
requires:
  - phase: 15-system-prompt-compression-user-feedback-loop/plan-01
    provides: "tests/phase15/ fixture 삼종 + SPC-01 mock reproducer 4 tests + SPC-04 empirical flag probe"
  - phase: 11-stdin-piping
    provides: "_invoke_claude_cli_once + MagicMock Popen 패턴 + D-01/D-02 stdin invariant"
  - phase: 14-api-adapter-remediation
    provides: "pytest.ini strict-markers + adapter_contract marker + tests/adapters/ conftest"
provides:
  - "scripts/orchestrator/invokers.py — tempfile + --append-system-prompt-file argv (SPC-01 fix)"
  - "tests/adapters/test_invokers_encoding_contract.py — SPC-05 10 contract tests (adapter_contract marker)"
  - "tests/phase15/test_encoding_repro.py — Wave 0 baseline flipped (post-fix assertions)"
  - "tests/phase11/test_invoker_stdin.py — argv canonical form sync (Phase 11 D-02 updated)"
affects:
  - 15-04-plan (Wave 3 UFL-01/02/03 revision — 이제 SPC-01 fix 기반으로 live retry 설계 가능)
  - 15-06-plan (Wave 5 SPC-06 live retry — encoding 장애물 해소, budget $5 cap 내 실행 가능)

# Tech tracking
tech-stack:
  added:
    - stdlib:tempfile (NamedTemporaryFile mode="w" suffix=".md" delete=False encoding="utf-8" newline="\n")
    - stdlib:os (os.unlink in explicit finally cleanup)
  patterns:
    - "tempfile 경유 + path-as-argv — 10KB+ Korean body Windows Python subprocess argv 한계 우회"
    - "finally 블록 명시적 cleanup + OSError logger.warning (CLAUDE.md 금기 #3 의미: 삼키는 폴백 금지, 명시 사유 warn+continue 는 허용)"
    - "TDD RED → GREEN 시 mock side_effect 리스트 시퀀스 (Popen.communicate 2회 호출: 1 TimeoutExpired + 1 drain)"

key-files:
  created:
    - "tests/adapters/test_invokers_encoding_contract.py"
  modified:
    - "scripts/orchestrator/invokers.py"
    - "tests/phase15/test_encoding_repro.py"
    - "tests/phase11/test_invoker_stdin.py"
    - ".planning/phases/15-system-prompt-compression-user-feedback-loop/15-VALIDATION.md"
    - ".planning/REQUIREMENTS.md"
    - ".planning/ROADMAP.md"

key-decisions:
  - "SPC-01 root cause 우회 — H1/H2/H3/H4 (cp949 spawn/argv byte-limit/pipe encoding/Windows spec) 의 정확한 원인을 특정하지 않고, tempfile 경유로 path 만 argv 에 전달하여 네 가설 모두에서 유효한 fix 를 채택. body 는 subprocess 가 파일 시스템 경로로 읽으므로 argv 인코딩 경로를 완전히 우회함."
  - "Phase 11 D-02 argv canonical form 개정 — 기존 `[cli, --print, --append-system-prompt, body, --json-schema, schema]` 는 Phase 15 SPC-01 fix 로 deprecated. 신규 canonical: `[cli, --print, --append-system-prompt-file, <tempfile_path>, --json-schema, schema]`. tests/phase11/test_invoker_stdin.py::test_invoker_argv_contains_expected_flags 를 Rule 1 auto-fix 로 동기화 (Plan 15-02 직접 scope — invokers.py argv shape 변경의 직접 결과)."
  - "Cleanup 은 명시적 finally + OSError logger.warning + raise 안 함 — CLAUDE.md 금기 #3 해석: '삼킨다 (silent pass)' 는 금지, '명시적 warn + 명시적 사유 (파일 permission/race 등) 로 continue' 는 허용. 테스트 `test_unlink_oserror_logged_not_raised` 로 이 행위를 계약으로 고정."
  - "tempfile suffix=.md + newline='\\n' + UTF-8 no-BOM — AGENT.md 원본 형식에 가장 근접한 on-disk 표현을 선택하여 CLI 가 body 를 markdown 으로 해석할 수 있게 함. BOM 부재는 `test_temp_file_utf8_encoding` 으로 계약."
  - "10 contract tests 전원 mock-only ($0) — 실 subprocess 호출 없이 argv shape + file content + cleanup 3 축을 계약으로 고정. Phase 14 30 + Phase 15 10 = 40 adapter_contract marker preserved."

patterns-established:
  - "Phase 15 contract test 는 tests/adapters/ 하위 + pytestmark = pytest.mark.adapter_contract — Phase 14 marker 승계, 장래 SPC-02/03 audit contract 도 동일 위치."
  - "Body-sensitive subprocess invocation 은 tempfile 경유가 default — Windows Python + cp949 locale + Korean text + 10KB+ argv 조합이 하나라도 있으면 file path 경유가 안전. 신규 CLI 호출 지점 (예: asset-sourcer nanobanana, publisher youtube_uploader) 도 동일 원칙 적용 예정."
  - "TDD RED → Rule 1 auto-fix 선순환 — invokers.py fix 로 발생한 Phase 11 test_invoker_argv_contains_expected_flags 실패는 contract 변경의 직접 결과 (not pre-existing drift) → scope 내 Rule 1 auto-fix 로 즉시 업데이트, deferred 하지 않음."

requirements-completed: [SPC-01, SPC-05]

# Metrics
duration: 26min
completed: 2026-04-21
---

# Phase 15 Plan 02: Wave 1 invokers.py Encoding Fix Summary

**SPC-01 root cause fix — invokers.py `_invoke_claude_cli_once` 가 UTF-8 tempfile + `--append-system-prompt-file` 경유로 전환되어 10KB+ Korean body rc=1 "프롬프트가 너무 깁니다" 우회 완결. SPC-05 10 contract tests (adapter_contract) green + Wave 0 baseline flipped + Phase 11 argv canonical form 개정. Wave 3/5 unblocked.**

## Performance

- **Duration:** 약 26분
- **Started:** 2026-04-21T18:08:22Z
- **Completed:** 2026-04-21T18:35:56Z
- **Tasks:** 2/2 (RED + GREEN, TDD)
- **Files created:** 1 (contract tests)
- **Files modified:** 3 code/test + 3 planning docs

## Accomplishments

- **SPC-01 root cause fix landed** — `scripts/orchestrator/invokers.py` `_invoke_claude_cli_once` 가 이제 `tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8", newline="\n")` 로 system_prompt 를 UTF-8 tempfile 에 기록한 뒤 `[cli, --print, --append-system-prompt-file, <path>, --json-schema, schema]` argv 로 호출합니다. body 10KB+ Korean text 가 argv 를 거치지 않으므로 Phase 13 live smoke 2026-04-22 시도에서 드러난 rc=1 "프롬프트가 너무 깁니다" 경로를 완전히 우회합니다 (H1/H2/H3/H4 원인 관계없이 fix 유효).
- **SPC-05 10 contract tests green** — `tests/adapters/test_invokers_encoding_contract.py` (310 lines, `adapter_contract` marker) 가 RED 단계에서 7 fail + 3 pass 로 기준선 확립, GREEN 단계에서 10 passed. 6 축 검증: argv shape (2) / large body 처리 (2) / cleanup 3 경로 (3) / UTF-8 BOM 부재 (1) / OSError warn (1) / Phase 11 stdin invariant (1).
- **Wave 0 baseline flipped + preserved** — `tests/phase15/test_encoding_repro.py` 의 `TestCurrentArgvShape` 두 test 가 post-fix assertions 로 전환됨 (body-NOT-in-argv + file-flag-present). `TestRc1Reproduction` + `TestPhase11Invariant` 는 fix 후에도 불변 계약으로 보존 — rc=1 오류가 여전히 Korean-first RuntimeError 로 surfacing 되고, user_prompt 는 여전히 stdin 경유.
- **Phase 11 D-02 argv canonical form 개정** — `tests/phase11/test_invoker_stdin.py::test_invoker_argv_contains_expected_flags` 를 Rule 1 auto-fix 로 업데이트 (Plan 15-02 argv shape 변경의 직접 결과). 신규 canonical: `[cli, --print, --append-system-prompt-file, <tempfile_path>.md, --json-schema, schema]`. 구 D-02 `--append-system-prompt` + body 직접 argv 가 완전히 제거되었는지 drift guard 포함.
- **Phase 14 30 + Phase 15 10 = 40 adapter_contract marker preserved** — `pytest -m adapter_contract --no-cov -q` 결과 40 passed, 1538 deselected. Phase 14 `test_veo_i2v_contract` + `test_elevenlabs_contract` + `test_shotstack_contract` + `test_adapter_contracts_doc` 30 tests 전원 regression 0.
- **Phase 13 baseline 60 + 5 skipped preserved** — `pytest tests/phase13 --no-cov -q` 60 passed + 5 skipped (live_smoke opt-in 마커, --run-live 없이는 skip 정상).
- **Phase 15 Wave 0 7 tests preserved (4 repro flipped + 3 probe)** — `pytest tests/phase15 --no-cov -q` 7 passed. Wave 0 reproducer 가 post-fix assertions 로 전환되었음에도 7 tests 유지 (RC1 reproduction + stdin invariant + 3 CLI flag probe 모두 불변).

## Task Commits

각 task 는 TDD RED/GREEN 패턴을 따라 atomically 커밋되었습니다 (4 commits):

1. **Task 15-02-01 RED: 10 contract tests (failing)** — `08954a7`
   - `tests/adapters/test_invokers_encoding_contract.py` 신규 (310 lines, adapter_contract marker, 대표님 20회)
   - RED 확인: 7 fail + 3 pass (argv-shape assertions 가 fix 미적용 상태에서 실패)
2. **Task 15-02-02 GREEN: invokers.py tempfile patch** — `b9a1262`
   - `scripts/orchestrator/invokers.py` `_invoke_claude_cli_once` body 교체 (73 insertions, 40 deletions)
   - imports: `tempfile, os` 추가
   - `NamedTemporaryFile` + `finally: os.unlink` + `except OSError: logger.warning`
3. **Task 15-02-02 flip Wave 0 baseline** — `c437d53`
   - `tests/phase15/test_encoding_repro.py` `TestCurrentArgvShape` 2 tests 을 post-fix assertions 로 전환 (40 insertions, 23 deletions)
   - class docstring + module docstring 도 post-fix 맥락으로 업데이트
4. **Task 15-02-02 Phase 11 argv contract sync (Rule 1 auto-fix)** — `616a577`
   - `tests/phase11/test_invoker_stdin.py::test_invoker_argv_contains_expected_flags` 를 신규 canonical argv 로 업데이트 (41 insertions, 9 deletions)
   - module docstring 에 Phase 15 SPC-01 fix 맥락 기록

**Plan metadata commit:** (이 SUMMARY + VALIDATION flip + ROADMAP + REQUIREMENTS mark-complete 묶음) — 후속 `gsd-tools commit` 에서 hash 부여.

## Files Created/Modified

### Created (1)
- `tests/adapters/test_invokers_encoding_contract.py` (310 lines, 10 tests, adapter_contract marker, mock-only $0)

### Modified (6)
- `scripts/orchestrator/invokers.py` — `_invoke_claude_cli_once` tempfile 경유 교체, imports (tempfile + os) 추가
- `tests/phase15/test_encoding_repro.py` — `TestCurrentArgvShape` 2 tests post-fix flip
- `tests/phase11/test_invoker_stdin.py` — argv canonical form sync (Rule 1 auto-fix, Plan 15-02 scope)
- `.planning/phases/15-system-prompt-compression-user-feedback-loop/15-VALIDATION.md` — rows 15-02-01/02 ⬜ → ✅
- `.planning/REQUIREMENTS.md` — SPC-05 [ ] → [x]
- `.planning/ROADMAP.md` — Progress Table Phase 13/14/15 rows 추가 (Phase 15 2/7 🔄 Executing)

## Decisions Made

1. **SPC-01 root cause 우회 전략 — file-path detour** — H1 (Popen cp949 spawn) / H2 (argv byte-limit) / H3 (pipe encoding vs argv encoding 비대칭) / H4 (Windows-specific Python `_execvpe` behavior) 중 정확한 원인을 empirical 로 pin down 하지 않고, tempfile 경유로 argv 에서 body 를 제거하여 네 가설 모두에서 유효한 fix 를 채택. 빠른 진행 + fix 확신도 모두 최대화.
2. **Phase 11 D-02 contract 개정 + Rule 1 scope 내** — Plan 15-02 가 argv shape 를 변경하는 것은 plan 의 본질 그 자체. 이로 인한 Phase 11 test 실패는 pre-existing drift 가 아니라 직접 영향 → Rule 1 auto-fix (scope 내) 로 즉시 업데이트. `tests/phase11/` deferred-items.md 로 넘기지 않음.
3. **finally 블록 cleanup + OSError warn — CLAUDE.md 금기 #3 해석 적용** — 금기 #3 은 "try-except 침묵 폴백 (`except: pass`)" 금지. 그러나 Windows tempfile 이 permission denied 또는 이미 삭제된 drift 상황에서 crash 하면 정상 반환 경로가 막히므로, `except OSError: logger.warning(...)` 으로 명시 사유 + 로그 기록 후 continue. `test_unlink_oserror_logged_not_raised` 로 이 행위를 계약으로 고정.
4. **`--append-system-prompt-file` 채택 (Option A) — append 의미 보존** — SPC-04 Wave 0 에서 `--system-prompt-file` 도 가용함을 empirical 확인했으나, 기존 `--append-system-prompt` 의 append 의미 (시스템 기본 프롬프트 위에 agent body 를 **추가**) 를 보존하기 위해 file 변형 중 append 쪽을 선택. `--system-prompt-file` 은 시스템 프롬프트 전체를 **대체** 하는 의미라서 Phase 4 agent design 과 호환 불충분.
5. **tempfile suffix=.md + newline=LF + UTF-8 no-BOM** — AGENT.md 원본 형식에 최대한 근접한 on-disk 표현. Claude CLI 가 body 를 markdown 으로 해석하기 용이하고, Windows LF 강제로 cp949 CRLF 혼입 방지, BOM 부재로 CLI 파서 edge case 회피.
6. **10 test mock-only $0 — 실 subprocess 우회** — Phase 14 adapter_contract 선례 승계. 실 subprocess 호출은 Wave 5 SPC-06 live retry 의 역할이고, Wave 1 은 argv shape + cleanup 3축을 mock 으로 고정하여 $0 로 CI 가능.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug in test mock] TimeoutExpired 시 Popen.communicate 2회 호출 side_effect 수정**
- **Found during:** Task 15-02-02 GREEN 첫 실행 (1 failed: `test_temp_file_cleanup_on_timeout`)
- **Issue:** invokers.py 의 TimeoutExpired 처리 경로가 `proc.kill(); proc.communicate()` 로 drain 을 한 번 더 호출하는데, 내 테스트 mock 의 `proc.communicate.side_effect = TimeoutExpired(...)` 는 매 호출 시 계속 raise 함. drain 호출이 두 번째 TimeoutExpired 를 발생시켜 finally 블록이 실행되기 전에 propagate.
- **Fix:** mock side_effect 를 리스트 시퀀스로 전환 — `[TimeoutExpired(...), ("", "")]` — 첫 호출은 timeout, 두 번째는 정상 drain. Phase 11 `test_invoker_timeout_raises_korean_runtime_error` 의 패턴과 정확히 일치 (선례 동기화).
- **Files modified:** `tests/adapters/test_invokers_encoding_contract.py::TestCleanup::test_temp_file_cleanup_on_timeout`
- **Commit:** (GREEN 전에 test 내부 수정 — 별도 commit 없이 `b9a1262` 에 포함)

**2. [Rule 1 — Direct contract consequence] Phase 11 argv canonical form 동기화**
- **Found during:** Task 15-02-02 GREEN verify (tests/phase11/test_invoker_stdin.py::test_invoker_argv_contains_expected_flags FAILED)
- **Issue:** Plan 15-02 의 argv shape 변경 (`--append-system-prompt` + body → `--append-system-prompt-file` + path) 이 Phase 11 에서 D-02 canonical form 으로 pin 되어 있던 test 를 자연스럽게 깨뜨림.
- **Fix:** Phase 11 test 를 신규 canonical argv 로 업데이트 — path 는 `.md` suffix + `SYS_BODY` literal 부재 + 구 flag `--append-system-prompt` drift guard 포함. module docstring 에 Phase 15 SPC-01 fix 맥락 기록.
- **Files modified:** `tests/phase11/test_invoker_stdin.py`
- **Commit:** `616a577`
- **Scope justification:** Plan 15-02 의 본질적 결과 → scope 내. tests/phase11/ deferred-items 로 넘길 "pre-existing drift" 가 아님.

### Deferred (Out of Scope)

- `tests/phase091/test_runway_ratios.py::test_ratio_auto_selects_first_valid` 1 failure — `git stash` + clean HEAD 에서 동일 에러 재현 확인, pre-existing (RunwayI2VAdapter 기본 ratio 가 `768:1280` 로 resolve 되어 oracle `16:9` 와 불일치). Phase 15 Plan 02 scope 밖. `.planning/phases/15-.../deferred-items.md` 에 anchor.

## Issues Encountered

- **pytest background runs 가 일관되게 output 을 산출하지 않음** — Windows bash 환경에서 `py -3.11 -m pytest` 가 `run_in_background=True` 또는 shell redirect 로 실행될 때 .output 파일이 비어있음. 해결: 모든 검증 pytest 를 foreground 로 실행하여 tail -10 으로 즉시 확인. 최종 verification 은 `pytest tests/adapters/test_invokers_encoding_contract.py tests/phase15 tests/phase11/test_invoker_stdin.py --no-cov -q` 로 23 passed 확인.

## User Setup Required

**None** — no external services, no API keys, no configuration changes. All tests are mock-only $0. invokers.py 의 변경 사항은 Phase 15 Plan 06 Wave 5 live retry 에서 실 Claude CLI 호출로 empirical 검증됩니다 (별도 대표님 승인 지점).

## Self-Check: PASSED

- `tests/adapters/test_invokers_encoding_contract.py` 존재: **FOUND**
- `scripts/orchestrator/invokers.py` `tempfile.NamedTemporaryFile` 포함: **FOUND** (grep count 1)
- `scripts/orchestrator/invokers.py` `--append-system-prompt-file` 포함: **FOUND** (grep count 2)
- `scripts/orchestrator/invokers.py` 구 `--append-system-prompt` + body 직접 패턴: **ABSENT** (grep count 0)
- `scripts/orchestrator/invokers.py` `os.unlink` 포함: **FOUND** (grep count 1)
- `scripts/orchestrator/invokers.py` "삭제 실패" 한국어 warn: **FOUND** (grep count 1)
- `scripts/orchestrator/invokers.py` `except: pass` silent: **ABSENT** (grep count 0)
- Commit 08954a7 존재: **FOUND** (test(15-02): RED — 10 contract tests)
- Commit b9a1262 존재: **FOUND** (feat(15-02): SPC-01 tempfile fix)
- Commit c437d53 존재: **FOUND** (test(15-02): Wave 0 baseline flip)
- Commit 616a577 존재: **FOUND** (test(15-02): Phase 11 argv sync)
- SPC-05 10 contract tests green: **FOUND** (10 passed in 0.86s)
- adapter_contract marker gate 40 tests green: **FOUND** (Phase 14 30 + Phase 15 10 = 40 passed, 1538 deselected)
- Phase 13 baseline 60 tests preserved: **FOUND** (60 passed, 5 skipped in 28.49s)
- Phase 15 Wave 0 7 tests preserved: **FOUND** (7 passed in ~1.5s)
- Phase 11 regression 6 tests: **FOUND** (6 passed in ~1s — test_invoker_stdin.py 전수 green)

## Next Phase Readiness

**Wave 2 Plan 15-03 UNBLOCKED** — 이 plan 의 SPC-01 fix 위에서 Plan 15-03 (SPC-02/03/04) 가 shorts-supervisor AGENT.md 를 6500자 이하로 압축 + Producer 14 size audit + `verify_agent_md_size.py` 추가 작업을 수행할 수 있습니다. tempfile 경유 fix 는 body 크기 제한을 이론적으로 제거했지만, Progressive Disclosure 원칙 (필수 #2) 은 여전히 AGENT.md 를 500~6500자 범위로 유지할 것을 요구합니다.

**Wave 3 Plan 15-04 UNBLOCKED (간접)** — `--revision-from` / `--revise-script` / `--pause-after` CLI 가 결국 Claude CLI 를 호출하여 재작업 루프를 돌릴 것이므로, SPC-01 fix 는 이들 UFL-01/02/03 의 안정적 실행을 담보.

**Wave 5 Plan 15-06 (SPC-06 live retry) UNBLOCKED (경로 의존)** — live retry 의 성패는 SPC-01 fix 에 직접 의존. 본 plan 완결로 live retry 가 drift 재발 위험 없이 재시도 가능한 상태. 실제 live run 은 대표님 직접 승인 + budget $5 cap 필요.

**Blocker: 없음.** Budget 변화 없음 ($0 mock-only). Phase 13/14 baseline 무결. Phase 11 regression preserved.

---
*Phase: 15-system-prompt-compression-user-feedback-loop*
*Plan: 02 (Wave 1 — invokers.py Encoding Fix, SPC-01 + SPC-05)*
*Completed: 2026-04-21*
