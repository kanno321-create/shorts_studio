---
phase: 9
plan: 09-04
subsystem: record-feedback
tags: [phase-9, wave-2, taste-gate, kpi-05, sc-4-partial, python, stdlib-only, hook-compat]
requires:
  - 09-00 (Wave 0 — tests/phase09/conftest.py synthetic_taste_gate_april + tmp_failures_md + freeze_kst_2026_04_01 fixtures, scripts/taste_gate/__init__.py namespace, 3 RED test files)
  - 09-03 (Wave 1 — wiki/kpi/taste_gate_2026-04.md dry-run byte-match fixture)
provides:
  - scripts/taste_gate/record_feedback.py (277 LOC stdlib-only parser + D-13 filter + FAILURES.md appender + argparse CLI + cp949 guard)
  - Public API: parse_taste_gate, filter_escalate, build_failures_block, append_to_failures, main, TasteGateParseError
  - Module constants: FAILURES_PATH, TASTE_GATE_DIR, KST, ROW_RE (module-level for pytest monkeypatch)
affects:
  - Plan 09-05 (E2E synthetic dry-run test now has full parse → filter → build → append chain to exercise)
  - Phase 10 Month 1 (CLI ready for cron invocation `python scripts/taste_gate/record_feedback.py --month YYYY-MM`)
  - .claude/failures/FAILURES.md (D-11 Hook-compatible append path opened — future taste_gate entries land here)
tech_stack:
  added: [zoneinfo.ZoneInfo]
  patterns: [read-append-write-text, argparse-cli, named-group-regex, explicit-raise-korean, cp949-guard, module-level-constants-for-monkeypatch]
key_files:
  created:
    - scripts/taste_gate/record_feedback.py (277 lines, stdlib-only)
  modified: []
decisions:
  - 9-column row regex with named groups (rank/video_id/title/retention/completion/avg/score/comment/tag) — tolerates optional quoting on title, "_" sentinel for 미평가 rows, restricts score to [1-5] at regex level (Pitfall 5)
  - Read + concatenate + `write_text` pattern for FAILURES.md (NOT `open("a")`) — prior content preserved as strict prefix satisfies Phase 6 `check_failures_append_only` Hook contract; single-write atomicity; more auditable
  - cp949 guard moved from `__main__` guard into `main()` itself — Rule 1 Bug fix discovered during CLI smoke: subprocess invocations that `import rf; rf.main([...])` never trigger the `__main__` guard, so Korean print() crashed on Windows default encoding. Guarding at main() entry covers all invocation paths (direct / `-m` / `-c` import / pytest)
  - Defensive score range check inside parse_taste_gate even though regex restricts to [1-5] — belt + suspenders against regex regression
  - Korean-first error messages via explicit `raise TasteGateParseError(...)` — no silent try/except/pass (Pitfall 6, CLAUDE.md Hook 3종 compliance)
  - Module constants at module level (not function-local) — tests monkeypatch `TASTE_GATE_DIR` and `FAILURES_PATH` per conftest fixture contract; function-local would have broken test isolation
metrics:
  duration_minutes: 4
  commits: 2
  tasks_completed: 3
  files_changed: 1
  tests_passed: 16
  tests_failed: 0
completed: 2026-04-20
---

# Phase 9 Plan 09-04: record_feedback.py — Taste Gate → FAILURES.md Appender Summary

KPI-05 월 1회 평가 회로의 **파이썬 엔진** 완성. 대표님이 작성한 `taste_gate_YYYY-MM.md`를 파싱 → score ≤ 3 항목만 D-13 필터링 → Phase 6 Hook 호환 방식으로 FAILURES.md에 append. Phase 9 전체에서 유일한 비자명 코드 (약 5% of phase per RESEARCH §0).

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 9-04-01 | Ship record_feedback.py (full public API + stdlib-only + Korean errors + Hook compat) | `5638b55` | scripts/taste_gate/record_feedback.py (269 lines) |
| 9-04-02 | Run 3 Wave 2 test files + CLI smoke subprocess + Phase 4-7 regression (auto-fix cp949 guard — Rule 1) | `a9f3391` | scripts/taste_gate/record_feedback.py (+8 LOC, 277 total) |
| 9-04-03 | Production dry-run + 3 error paths + Phase 9 sweep (no code changes — pure verification) | (verify-only) | — |

## Success Criteria

- [x] `scripts/taste_gate/record_feedback.py` shipped — 277 LOC stdlib-only (argparse / re / sys / datetime / pathlib / zoneinfo)
- [x] Public API importable: `parse_taste_gate, filter_escalate, build_failures_block, append_to_failures, main, TasteGateParseError` + 4 module constants (`FAILURES_PATH, TASTE_GATE_DIR, KST, ROW_RE`)
- [x] 16 tests PASS (4 + 6 + 6) across `test_record_feedback.py` / `test_score_threshold_filter.py` / `test_failures_append_only.py`
- [x] AST scan clean: no `open(path, "w")` on FAILURES_PATH, no `skip_gates` string, no `TODO(next-session)` string, no `try/except: pass` — Hook 3종 준수
- [x] Korean error messages: `"파일 없음: {path} — ..."` + `"평가된 행이 없습니다: {path}"` + `"--month 형식 오류: ..."`
- [x] cp949 guard in `main()` itself so CLI / subprocess / import / pytest all get UTF-8 stdout+stderr
- [x] Production dry-run: 3 D-13 escalations (jkl012 score 3, mno345 score 2, pqr678 score 1) — top 3 (abc123 score 5, def456+ghi789 score 4) filtered out correctly
- [x] FAILURES.md sha256 UNCHANGED before/after `--dry-run` invocation: `6bff84a846a0...`
- [x] Error paths verified: `--month 2099-12` → rc=3 + "파일 없음" / `--month abc` → rc=2 + "--month 형식 오류"
- [x] Phase 9 sweep (33 tests across 5 test files) — all PASS, zero regression
- [x] Phase 4-7 regression: 986 tests collected, no new collection errors introduced (Phase 8 pre-existing mock import errors documented in deferred-items.md per prior plans)

## Production Dry-Run Output (first 18 lines of stdout)

```

### [taste_gate] 2026-04 리뷰 결과
- **Tier**: B
- **발생 세션**: 2026-04-20T02:10:19.621003+09:00
- **재발 횟수**: 1
- **Trigger**: 월간 Taste Gate 평가 점수 <= 3
- **무엇**: 대표님 평가 하위 항목 3건 — jkl012(3점), mno345(2점), pqr678(1점)
- **왜**: 채널 정체성 / 품질 기대치 미달 — 다음 월 Producer 입력 조정 필요
- **정답**: 하위 코멘트 패턴을 다음 월 niche-classifier / scripter 프롬프트에 반영
- **검증**: 다음 월 Taste Gate 동일 패턴 재발 여부
- **상태**: observed
- **관련**: wiki/kpi/taste_gate_2026-04.md

#### 세부 코멘트
- **jkl012** (3/5): hook 약함
- **mno345** (2/5): 지루함
- **pqr678** (1/5): 결말 처참
```

stderr: `[dry-run] FAILURES.md 추가 예정 항목: 3건`

## FAILURES.md sha256 Integrity

| Moment | sha256 prefix |
| ------ | ------------- |
| Before `--dry-run` | `6bff84a846a0...` |
| After `--dry-run`  | `6bff84a846a0...` (identical) |

Proves `--dry-run` never invokes `write_text` on `FAILURES_PATH`; D-11 Hook integrity preserved.

## Error Path Exit Codes Verified

| Invocation                 | rc | stderr content                                          |
| -------------------------- | -: | ------------------------------------------------------- |
| `--month 2099-12`          | 3  | `ERROR: 파일 없음: wiki/kpi/taste_gate_2099-12.md — ...` |
| `--month abc`              | 2  | `error: --month 형식 오류: 'abc' (YYYY-MM 예: 2026-04)` (argparse) |
| `--month 2026-04 --dry-run` | 0  | `[dry-run] FAILURES.md 추가 예정 항목: 3건`               |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] cp949 guard wasn't reached on subprocess/import invocations**
- **Found during:** Task 9-04-02 CLI smoke subprocess
- **Issue:** The original `__main__` guard pattern `if __name__ == "__main__": if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")` only ran when the script was invoked as the top-level script. A subprocess that did `python -c "from scripts.taste_gate import record_feedback; record_feedback.main([...])"` never triggered it, and Korean `print(block)` crashed with `UnicodeEncodeError: 'cp949' codec can't encode character '\u2014'`.
- **Fix:** Moved the reconfigure loop to the FIRST lines of `main()` itself and extended it to cover both `sys.stdout` and `sys.stderr`. Silent no-op (`hasattr` guard) on non-reconfigurable streams preserves pytest capture compatibility.
- **Files modified:** scripts/taste_gate/record_feedback.py (+8 LOC)
- **Commit:** `a9f3391`

No architectural changes. No Rule 4 stop conditions encountered.

## Known Stubs

None. Every public function is fully implemented and tested. The D-11 Phase 10 auto-cron invocation path is documented but intentionally deferred per CONTEXT.md scope guardrail (Phase 9 protocol only, Phase 10 cron).

## Deferred Issues

None from Plan 09-04. Pre-existing Phase 8 mock import errors are tracked in `deferred-items.md` (inherited from Plan 09-00, not caused by this plan).

## Regression Impact

- Phase 9 Wave 0 tests: still PASS (conftest + test stubs untouched)
- Phase 9 Wave 1 tests: still PASS (taste_gate_2026-04.md dry-run untouched)
- Phase 9 Wave 2 tests: **16 new PASS** (4 + 6 + 6 across 3 files — transitioned from importorskip-skipped to green)
- Phase 9 full sweep excluding Plan 09-05: **33/33 PASS** (0.11s)
- Phase 4-7 collection: 986 tests, clean (no new collection errors)

## Commits

- `5638b55` feat(09-04): ship record_feedback.py — D-12 Taste Gate appender + D-13 filter (KPI-05)
- `a9f3391` fix(09-04): move cp949 guard into main() — Rule 1 auto-fix

## Self-Check: PASSED

- scripts/taste_gate/record_feedback.py — FOUND (277 lines)
- Commit 5638b55 — FOUND
- Commit a9f3391 — FOUND
- 16 Wave 2 tests PASS — verified
- FAILURES.md sha256 unchanged after --dry-run — verified
- Error paths rc=3 / rc=2 / rc=0 — verified
- Hook 3종 AST scan clean — verified
