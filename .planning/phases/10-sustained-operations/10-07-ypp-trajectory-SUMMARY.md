---
phase: 10-sustained-operations
plan: 07
subsystem: [analytics, ypp-trajectory]
tags: [ypp-trajectory, sc6-exit-criterion, monthly-auto-append, 3-milestone-gate]
requires: [10-03-youtube-analytics-fetch]
provides: [monthly-ypp-snapshot, 3-gate-pivot-warning, mermaid-auto-rebuild]
affects: [wiki/ypp/trajectory.md, wiki/ypp/MOC.md, FAILURES.md]
phase_success_criteria: [SC-6]
requirements: [KPI-02]
tech_added: [mermaid-xychart-beta]
patterns: [idempotent-upsert-row, regex-marker-replace, hook-bypass-direct-io]
key_files_created:
  - scripts/analytics/trajectory_append.py
  - wiki/ypp/trajectory.md
  - tests/phase10/test_trajectory_append.py
key_files_modified:
  - wiki/ypp/MOC.md
decisions: []
metrics:
  duration_min: 22
  tasks_completed: 2
  tests_added: 14
  files_created: 3
  files_modified: 1
  commits: 3
completed: 2026-04-20
---

# Phase 10 Plan 07: YPP Trajectory Summary

> SC#6 (ROADMAP §276) monthly auto-append 회로 가동 준비 완료. `wiki/ypp/trajectory.md` 60+줄 scaffold + `scripts/analytics/trajectory_append.py` 370줄 CLI + 14 tests GREEN. 3-milestone gate 로직 (1차 100 subs @ 3m / 2차 300 subs + 0.60 retention @ 6m / 3차 1000 subs + 10M views @ 12m) locked. 실 데이터 누적은 Plan 10-04 Scheduler 가 월 1회 CLI 호출하면서 시작.

**One-liner**: Phase 10 SC#6 YPP 진입 궤도 월별 자동 append 회로 완비 — trajectory.md scaffold + 3-gate evaluation CLI + Mermaid auto-rebuild + FAILURES F-YPP-NN append (gate miss).

## Overview

Phase 10 CONTEXT §Exit Criterion 에서 locked 된 3-milestone gate (대표님 delegation) 를 월별 snapshot 으로 측정 가능하게 만드는 scaffold + appender 를 shipped. monthly_aggregate.py (Plan 10-03) 가 composite score 를 kpi_log.md 에 append 하는 것과 병행하여, trajectory_append.py 는 구독자/12-month-rolling-views/retention 3축을 wiki/ypp/trajectory.md 에 append + Mermaid xychart 를 재생성한다. gate 미달 시 FAILURES.md 에 F-YPP-NN entry 가 자동 append 되어 pivot 판단 근거를 박제한다.

## Tasks Completed

### Task 1: trajectory.md scaffold + MOC.md checkbox flip
- **Commit**: `6cad770` — `feat(10-07): trajectory.md scaffold + MOC.md checkbox flip`
- **Files**:
  - `wiki/ypp/trajectory.md` (70 lines, 신규): frontmatter 5 fields (`node / category / kind / status / last_updated / auto_update_by`) + `## 3-Milestone Gates` 테이블 (4열: Gate/Deadline/Threshold/미달 조치) + `## Monthly Snapshots` 섹션 + `<!-- TRAJECTORY_APPEND_MARKER -->` + `## Trajectory Chart` + `<!-- MERMAID_DATA_MARKER -->` + Mermaid ```xychart-beta``` 블록 (initial x-axis `[2026-04]` + line `[0]` + y-axis `0 --> 1100`) + `## Pivot Warning Thresholds` 3 항목 + `## Cross-References` (MOC/entry_conditions/kpi_log/taste_gate_protocol/CONTEXT/ROADMAP 링크).
  - `wiki/ypp/MOC.md` (기존): Planned Nodes 에 `- [x] trajectory.md — 월별 snapshot + 3-milestone progress (Phase 10 Plan 07 ready)` 라인 append (entry_conditions.md 아래). 기존 byte 는 모두 preserved — append-only diff.
- **Acceptance**: `TRAJECTORY_APPEND_MARKER` 1회 + `MERMAID_DATA_MARKER` 1회 + `xychart-beta` 1회 + 3 gate 날짜 (2026-07-20 / 2026-10-20 / 2027-04-20) 전부 포함 + 70 lines ≥ 60.

### Task 2: trajectory_append.py CLI + 14 tests
- **Commits**:
  - `39c79c1` — `test(10-07): RED — 13 failing tests for trajectory_append (SC#6)` (ModuleNotFoundError 로 13 test collection fail 확인)
  - `191da9d` — `feat(10-07): trajectory_append.py CLI — SC#6 YPP monthly appender (370 lines)` (14 tests GREEN)
- **Files**:
  - `scripts/analytics/trajectory_append.py` (370 lines, 신규): 7 threshold/path 상수 + 8 public 함수 (`months_since` / `evaluate_gates` / `render_row` / `upsert_row` / `parse_existing_snapshots` / `update_mermaid` / `append_failures` / `main`) + argparse CLI (`--subs --views-12m --retention-3s --year-month --notes --trajectory --failures --dry-run`). Stdlib-only (argparse + json + re + datetime + zoneinfo + pathlib + sys).
  - `tests/phase10/test_trajectory_append.py` (257 lines, 신규): 14 tests. 6 evaluate_gates (pre-3m / 1st-fail / 1st-pass / 2nd-fail-subs / 2nd-fail-retention / 2nd-pass) + 2 upsert_row (insert + idempotent replace) + 1 update_mermaid (3 snapshots → x-axis/line rewrite) + 1 append_failures (F-YPP-01→02 + strict-prefix) + 3 CLI (dry-run sha256 unchanged / months_since=3 for 2026-07-01 / missing marker RuntimeError) + 1 threshold constants lock.
- **Acceptance**:
  - `python -m scripts.analytics.trajectory_append --dry-run --subs 150 --views-12m 125000 --retention-3s 0.62 --year-month 2026-07` → exit 0, `gate_warnings: []`, `pivot_required: false`, `would_append_row: "| 2026-07 | 150 | 125000 | 150.0% | 50.0% | 15.0% | 1.2% |  |"`
  - `python -m scripts.analytics.trajectory_append --dry-run --subs 50 --views-12m 10000 --year-month 2026-07` → exit 0, `gate_warnings: ["1st gate FAIL — subs 50 < 100 — 니치/훅 iteration 필요"]`, `pivot_required: true`
  - `pytest tests/phase10/test_trajectory_append.py -q` → 14/14 PASS (0.13s)
  - 5 threshold constants literal (`GATE_1_SUBS = 100`, `GATE_2_SUBS = 300`, `GATE_2_RETENTION = 0.60`, `GATE_3_SUBS = 1000`, `GATE_3_VIEWS = 10_000_000`) + `PHASE_10_START = date(2026, 4, 20)` 전부 grep-exact present
  - `F-YPP` 토큰 7회 present (min 2 요건 초과)

## Integration Smoke

tmp copy 에서 real-append 실행 (not dry-run) 검증:

```
input: --subs 50 --views-12m 10000 --retention-3s 0.45 --year-month 2026-07
result:
  - trajectory.md row appended: | 2026-07 | 50 | 10000 | 50.0% | 16.7% | 5.0% | 0.1% | 1차 gate 미달 smoke |
  - Mermaid rebuilt: x-axis [2026-07] / line [50]
  - FAILURES.md strict-prefix preserved (byte.startswith = True)
  - F-YPP-01 entry appended (검사 시각 + 경보 + 조치 + 참조 7-section)
  - stdout: {"pivot_required": true, "failures_appended": "F-YPP-01", "appended": true}
```

## Decisions Made

본 Plan 범위 내 신규 아키텍처 결정 없음 — Phase 10 CONTEXT §Exit Criterion (Locked by 대표님 delegation) + RESEARCH §Plan 7 Open Q3-Q4 를 구현. 세부 구현 선택 (render_row 8열 포맷 / Mermaid x-axis-line 파싱 / upsert regex + chronological sort / F-YPP-NN 독립 namespace) 은 모두 Claude's Discretion 범위 내 결정.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan interface "- [ ] trajectory.md — placeholder" 현실 불일치 수정**
- **Found during**: Task 1
- **Issue**: PLAN.md `<interfaces>` 섹션은 MOC.md 에 `- [ ] trajectory.md — placeholder` 라인이 "existing" 이라고 명시하고 `- [x] ...` 로 flip 해야 한다고 지시. 실제 `wiki/ypp/MOC.md` 현재 상태에는 해당 라인 없음 (Phase 2 scaffold 이후 placeholder 미추가).
- **Fix**: append-only 로 `- [x] trajectory.md — 월별 snapshot + 3-milestone progress (Phase 10 Plan 07 ready)` 신규 라인을 entry_conditions 아래에 추가. 결과적으로 acceptance 의 `[x] trajectory.md == 1` + `[ ] trajectory.md == 0` 동일 보장.
- **Files modified**: `wiki/ypp/MOC.md`
- **Commit**: `6cad770`

**2. [Rule 2 - Missing Critical] 초기 MOC 편집 시 backtick 오타 자동수정**
- **Found during**: Task 1 verification
- **Issue**: 첫 MOC 편집에서 다른 노드 스타일과 일관성 위해 `` `trajectory.md` `` (backtick) 로 기재. Acceptance grep pattern `[x] trajectory.md` 가 backtick 때문에 match 실패 (backtick 사이에 삽입됨).
- **Fix**: backtick 제거 후 plain `trajectory.md` 로 수정. 다른 라인 (`entry_conditions.md` 등) 에 backtick 유지 — scope 최소.
- **Files modified**: `wiki/ypp/MOC.md`
- **Commit**: `6cad770` (동일 commit 내 수정)

**3. [Rule 1 - Bug] 초기 trajectory.md 테이블 separator 중복 수정**
- **Found during**: Task 1 initial Write
- **Issue**: Write 시 table header separator 를 실수로 2줄 작성 (`|-------|...|` × 2).
- **Fix**: 2번째 separator 삭제 → 표준 Markdown 테이블 header + 1 separator + marker 구조.
- **Files modified**: `wiki/ypp/trajectory.md`
- **Commit**: `6cad770` (Edit 직후 correction, 동일 commit)

**4. [Rule 1 - Bug] threshold 상수 type annotation 제거**
- **Found during**: Task 2 acceptance grep verification
- **Issue**: 초기 GREEN 구현에서 `GATE_1_SUBS: int = 100` 타입 annotation 사용. Plan acceptance 는 `grep -c "GATE_1_SUBS = 100"` 정확 substring 매칭 요구. annotation 이 있으면 `GATE_1_SUBS: int = 100` 이라 match 실패.
- **Fix**: 7 상수 (KST + PHASE_10_START + 5 GATE_* + 2 _MARKER) 에서 type annotation 제거 → bare 할당문. 기능적 영향 없음 (타입 추론 동일).
- **Files modified**: `scripts/analytics/trajectory_append.py`
- **Commit**: `191da9d` (GREEN 커밋 내 correction)

## Deferred Issues

본 Plan 에서 발견된 추가 deferrable 사항 없음. 기존 `deferred-items.md` 항목 (D10-01-DEF-01 phase-regression-cascade, D10-03-DEF-01 drift_scan STATE.md frontmatter, D10-03-DEF-02 phase 8 sweep) 은 Plan 10-07 범위 밖으로 재확인.

## Regression Status

### Phase 6 (pre-existing failures only)
- 4 failures inherited (`test_moc_linkage.py::test_moc_frontmatter_unchanged_scaffold` + `test_notebooklm_wrapper.py::test_default_skill_path_is_the_2026_install` + `test_phase06_acceptance.py::test_full_phase06_suite_green` + `test_phase06_acceptance.py::test_phase05_suite_still_green`) — D10-01-DEF-01 inherited cascade.
- **Stash-verified before Plan 10-07 touch**: same 4 failures pre-existing → OUT OF SCOPE.
- 232/236 PASS (98.3%).

### Phase 10 Plans 1-6 (pre-existing failure only)
- 1 failure (`test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default`) — D10-03-DEF-01.
- 95/96 PASS (98.9%) excluding test_trajectory_append.py.
- Plan 10-07 in-scope: 14/14 GREEN (`pytest tests/phase10/test_trajectory_append.py -q` 0.13s).

## SC#6 Status & Traceability

**SC#6 (ROADMAP §276)**: "Rolling 12개월 구독자 ≥ 1000 + 뷰 ≥ 10M" — Phase 10 "성공 선언" 기준.

**구조적 커버**: 완료. `wiki/ypp/trajectory.md` + `scripts/analytics/trajectory_append.py` 가 월 1회 실행되면서 rolling 12-month 값을 축적. 1차/2차 gate 조기 경보로 12m deadline 이전에 pivot 판단 가능.

**실 데이터 수집**: Plan 10-04 Scheduler (Windows Task Scheduler 또는 `.github/workflows/ypp-trajectory-monthly.yml`) 가 매월 1일 KST 09:00 에 trajectory_append CLI 를 호출하면서 시작. Scheduler wiring 은 Plan 10-04 범위 완료 후 optional follow-up (본 Plan 범위 외).

**Traceability (WARNING #1)**:
- PLAN.md frontmatter: `phase_success_criteria: [SC-6]` + `tags: [ypp-trajectory, sc6-exit-criterion]` + `requirements: [KPI-02]`
- ROADMAP.md §276 → Plan 10-07 → `wiki/ypp/trajectory.md` (scaffold) + `scripts/analytics/trajectory_append.py` (CLI) 체인 성립.
- REQUIREMENTS.md KPI-02 (월별 kpi_log 플러시) secondary trigger — monthly_aggregate.py (Plan 10-03) 와 trajectory_append.py 결합으로 "월 1회 자동 wiki append" 범위 확장.

## Commit Hashes

- Task 1: `6cad770e586ccc0f45c24b4efd18178cca1d7f67`
- Task 2 RED: `39c79c16f73c1ac9ed0f06c80d84907bd85dca36`
- Task 2 GREEN: `191da9d4cc6513250cf1ff500c58c966c8cade4b`

## Next

- **Plan 10-08** (ROLLBACK docs + stop_scheduler) — Phase 10 Wave 4 최종 plan.
- **Plan 10-04 Scheduler follow-up** (optional, 본 Plan 범위 외): `.github/workflows/ypp-trajectory-monthly.yml` 또는 Windows Task Scheduler 월 1회 `trajectory_append` invocation 등록.
- **실 데이터 Month 1** (2026-05-20 이후): Plan 10-03 fetch_kpi daily CSV 축적 + Plan 10-04 scheduler 가동 → 2026-05 snapshot 첫 row 생성 예정.

## Self-Check: PASSED

- `scripts/analytics/trajectory_append.py` — FOUND (370 lines)
- `wiki/ypp/trajectory.md` — FOUND (70 lines)
- `wiki/ypp/MOC.md` — FOUND (trajectory.md `[x]` line present)
- `tests/phase10/test_trajectory_append.py` — FOUND (257 lines, 14 tests)
- Commit `6cad770` — FOUND in `git log --oneline -5`
- Commit `39c79c1` — FOUND in `git log --oneline -5`
- Commit `191da9d` — FOUND in `git log --oneline -5`
- 14/14 pytest — GREEN (0.13s)
- CLI gate-pass smoke — exit 0, warnings []
- CLI gate-fail smoke — exit 0, pivot_required true
- tmp real-append smoke — row + Mermaid + FAILURES F-YPP-01 strict-prefix OK
