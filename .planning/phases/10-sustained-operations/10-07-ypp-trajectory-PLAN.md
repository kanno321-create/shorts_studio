---
phase: 10-sustained-operations
plan: 07
type: execute
wave: 3
depends_on: [10-03-youtube-analytics-fetch]
files_modified:
  - scripts/analytics/trajectory_append.py
  - wiki/ypp/trajectory.md
  - wiki/ypp/MOC.md
  - tests/phase10/test_trajectory_append.py
autonomous: true
requirements: [KPI-02]   # SC#6 (ROADMAP §276) phase-level criterion — 별도 REQ-ID 없음
phase_success_criteria: [SC-6]
tags: [ypp-trajectory, sc6-exit-criterion]
must_haves:
  truths:
    - "wiki/ypp/trajectory.md 가 3-milestone gate 정의 + 월별 snapshot 테이블 + Mermaid xychart 블록 을 포함한 scaffold 로 신규 생성된다"
    - "scripts/analytics/trajectory_append.py 가 월 1회 실행되어 구독자/뷰/3-gate 진행률을 계산 후 trajectory.md 에 row 를 append + Mermaid x-axis/line 을 갱신한다"
    - "1차 gate (2026-07-20 기준 subs<100) / 2차 gate (2026-10-20 subs<300 or retention<0.60) 미달 시 pivot warning 을 FAILURES.md F-YPP-XX 로 append"
    - "wiki/ypp/MOC.md 의 Planned Nodes 에 trajectory.md 라인 checkbox [x] flip"
  artifacts:
    - path: scripts/analytics/trajectory_append.py
      provides: "Monthly YPP trajectory appender — SC#6"
      min_lines: 150
    - path: wiki/ypp/trajectory.md
      provides: "YPP 진행률 scaffold (3-milestone + monthly table + mermaid)"
      min_lines: 60
    - path: wiki/ypp/MOC.md
      provides: "trajectory.md 체크박스 flip"
      contains: "trajectory.md"
    - path: tests/phase10/test_trajectory_append.py
      provides: "SC#6 unit"
      min_lines: 90
  key_links:
    - from: scripts/analytics/trajectory_append.py
      to: wiki/ypp/trajectory.md
      via: "TRAJECTORY_APPEND_MARKER insert row + mermaid data update"
      pattern: "TRAJECTORY_APPEND_MARKER"
    - from: scripts/analytics/trajectory_append.py
      to: FAILURES.md
      via: "pivot warning F-YPP-XX append (direct I/O)"
      pattern: "F-YPP"
---

<objective>
YPP 진입 궤도 (1000구독 + 10M views/년) 의 월별 snapshot 을 축적하고 3-milestone gate (3/6/12개월) 대비 진행률을 가시화한다. `wiki/ypp/trajectory.md` 신규 생성 + `trajectory_append.py` 가 월 1회 갱신 + gate 미달 시 FAILURES append.

**SC#6 phase-level criterion (ROADMAP §276)**: Phase 10 의 성공 선언 기준 "Rolling 12개월 구독자 ≥ 1000 + 뷰 ≥ 10M" 을 측정 가능 형태로 실증하는 플랜. 별도 REQ-ID 는 없으며 `phase_success_criteria: [SC-6]` frontmatter 필드로 추적 (WARNING #1).

Purpose: 매월 "어디까지 왔는가" 숫자 가시화 — D-2 저수지 규율의 외부 증거.
Output: trajectory.md + trajectory_append.py + MOC flip + 테스트.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/10-sustained-operations/10-CONTEXT.md
@.planning/phases/10-sustained-operations/10-RESEARCH.md
@.planning/phases/10-sustained-operations/10-VALIDATION.md
@wiki/ypp/MOC.md
@wiki/ypp/entry_conditions.md
@scripts/analytics/monthly_aggregate.py
@CLAUDE.md

<interfaces>
From CONTEXT 3-milestone (Locked):
- 1차: 2026-07-20 (3m) subs >= 100
- 2차: 2026-10-20 (6m) subs >= 300 + retention_3s >= 0.60
- 3차: 2027-04-20 (12m) rolling-12m subs >= 1000 + views >= 10M

PHASE_10_START_DATE = "2026-04-20"

From RESEARCH Plan 7 Open Q3 evaluate_gates:
```python
def evaluate_gates(snapshot, month_since_start):
    warnings = []
    if month_since_start >= 3 and snapshot["subs"] < 100:
        warnings.append("1st gate FAIL")
    if month_since_start >= 6 and (snapshot["subs"] < 300 or snapshot["retention_3s"] < 0.60):
        warnings.append("2nd gate FAIL")
    return {"warnings": warnings, "pivot_required": len(warnings) > 0}
```

From `wiki/ypp/MOC.md` (existing):
```
- [ ] trajectory.md — placeholder
```
→ to flip:
```
- [x] trajectory.md — 월별 snapshot + 3-milestone progress (Phase 10 Plan 07 ready)
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: trajectory.md scaffold + MOC.md checkbox flip</name>
  <files>
    wiki/ypp/trajectory.md,
    wiki/ypp/MOC.md
  </files>
  <read_first>
    - `wiki/ypp/MOC.md` 현재 Planned Nodes 라인
    - `wiki/ypp/entry_conditions.md` frontmatter 스타일
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 7 Open Q2
  </read_first>
  <action>
    1. `wiki/ypp/trajectory.md` 신규 생성 (60+ lines) 내용:
       - 프런트매터: node/kind/status/last_updated/auto_update_by 5 fields
       - 헤더 # YPP Trajectory — naberal-shorts-studio
       - `## 3-Milestone Gates` 테이블 (Gate/Deadline/Threshold/미달 조치)
       - `**Phase 10 시작일**: 2026-04-20`
       - `## Monthly Snapshots` + `<!-- TRAJECTORY_APPEND_MARKER -->` + table header (Month/Subs/Rolling12mViews/1stGate%/2ndGateSubs%/3rdGateSubs%/3rdGateViews%/Notes)
       - `## Trajectory Chart` + `<!-- MERMAID_DATA_MARKER -->` + ```mermaid xychart-beta 블록 (initial: x-axis [2026-04], line [0], y-axis 0-->1100)
       - `## Pivot Warning Thresholds` 3 항목
       - `## Cross-References` (kpi_log, entry_conditions, CONTEXT 링크)
    2. `wiki/ypp/MOC.md` 수정 — `- [ ] trajectory.md — placeholder` 를 `- [x] trajectory.md — 월별 snapshot + 3-milestone progress (Phase 10 Plan 07 ready)` 로 교체. 기타 라인은 byte-identical.
  </action>
  <acceptance_criteria>
    - `ls wiki/ypp/trajectory.md` 존재
    - `grep -c "TRAJECTORY_APPEND_MARKER" wiki/ypp/trajectory.md` == 1
    - `grep -c "MERMAID_DATA_MARKER" wiki/ypp/trajectory.md` == 1
    - `grep -c "2026-07-20\|2026-10-20\|2027-04-20" wiki/ypp/trajectory.md` >= 3
    - `grep -c "xychart-beta" wiki/ypp/trajectory.md` == 1
    - `wc -l wiki/ypp/trajectory.md` >= 60
    - `grep -c "\[x\] trajectory.md" wiki/ypp/MOC.md` == 1
    - `grep -c "\[ \] trajectory.md" wiki/ypp/MOC.md` == 0
    - Phase 6 wiki regression 보존: `pytest tests/phase06 -q --tb=no` exit 0
  </acceptance_criteria>
  <verify>
    <automated>python -c "from pathlib import Path; t=Path('wiki/ypp/trajectory.md').read_text(encoding='utf-8'); assert 'TRAJECTORY_APPEND_MARKER' in t and 'xychart-beta' in t; m=Path('wiki/ypp/MOC.md').read_text(encoding='utf-8'); assert '[x] trajectory.md' in m; print('OK')"</automated>
  </verify>
  <done>trajectory.md scaffold 완비, MOC.md checkbox flipped, Phase 6 wiki regression 보존</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: trajectory_append.py CLI + 3-gate evaluate + mermaid data update + 테스트</name>
  <files>
    scripts/analytics/trajectory_append.py,
    tests/phase10/test_trajectory_append.py
  </files>
  <read_first>
    - Task 1 산출물 `wiki/ypp/trajectory.md` (TRAJECTORY_APPEND_MARKER + MERMAID_DATA_MARKER 위치)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 7 Open Q3-Q4
    - `scripts/analytics/monthly_aggregate.py` (composite_score / aggregate_month 재사용 가능)
    - `scripts/audit/skill_patch_counter.py` Task 2 의 `append_failures()` 패턴
    - `tests/phase10/conftest.py` (`freeze_kst_now`)
  </read_first>
  <behavior>
    - Test 1 (test_evaluate_gates_before_3months): month_since_start=2, subs=10 → warnings [] + pivot_required False
    - Test 2 (test_evaluate_gates_first_gate_fail): month=3, subs=50 → "1st gate FAIL" in warnings
    - Test 3 (test_evaluate_gates_first_gate_pass): month=3, subs=150 → warnings [] (통과)
    - Test 4 (test_evaluate_gates_second_gate_fail_low_subs): month=6, subs=200, retention=0.7 → "2nd gate FAIL"
    - Test 5 (test_evaluate_gates_second_gate_fail_low_retention): month=6, subs=400, retention=0.50 → "2nd gate FAIL"
    - Test 6 (test_evaluate_gates_second_gate_pass): month=6, subs=400, retention=0.65 → warnings []
    - Test 7 (test_append_row_inserts_below_marker): tmp trajectory.md → append_row → row 가 TRAJECTORY_APPEND_MARKER 직후에 삽입
    - Test 8 (test_append_row_idempotent_same_month): 같은 month 재호출 → 기존 row replace (중복 방지) OR skip return False
    - Test 9 (test_mermaid_data_updated): 3 row 추가 후 mermaid xychart 의 x-axis 와 line data 가 3 entry 로 갱신
    - Test 10 (test_pivot_warning_appends_failures): evaluate_gates warnings 생성 → FAILURES.md F-YPP-01 append
    - Test 11 (test_cli_dry_run_no_mutation): --dry-run → trajectory.md + FAILURES.md 미수정 + stdout JSON
    - Test 12 (test_cli_month_since_start_calculation): freeze KST now 2026-07-25 → PHASE_10_START 2026-04-20 → month_since_start == 3
    - Test 13 (test_cli_missing_markers_raises): trajectory.md 에서 MARKER 제거 → RuntimeError explicit
  </behavior>
  <action>
    1. `scripts/analytics/trajectory_append.py` 작성 (≥150 lines):
       ```python
       """Monthly YPP trajectory appender — SC#6.

       Usage:
         python -m scripts.analytics.trajectory_append --subs 150 --views-12m 125000 --retention-3s 0.62 --year-month 2026-07
         python -m scripts.analytics.trajectory_append --dry-run --subs 150 --views-12m 125000

       Updates wiki/ypp/trajectory.md monthly table + Mermaid xychart.
       Emits FAILURES.md F-YPP-NN on gate miss.
       """
       from __future__ import annotations
       import argparse
       import json
       import re
       import sys
       from datetime import date, datetime
       from pathlib import Path
       from zoneinfo import ZoneInfo

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")
       PHASE_10_START = date(2026, 4, 20)
       GATE_1_SUBS = 100
       GATE_2_SUBS = 300
       GATE_2_RETENTION = 0.60
       GATE_3_SUBS = 1000
       GATE_3_VIEWS = 10_000_000
       APPEND_MARKER = "<!-- TRAJECTORY_APPEND_MARKER -->"
       MERMAID_MARKER = "<!-- MERMAID_DATA_MARKER -->"

       def months_since(start: date, current: date) -> int:
           return (current.year - start.year) * 12 + (current.month - start.month)

       def evaluate_gates(snapshot: dict, month_since_start: int) -> dict:
           warnings: list[str] = []
           if month_since_start >= 3 and snapshot.get("subs", 0) < GATE_1_SUBS:
               warnings.append(f"1st gate FAIL — subs {snapshot.get('subs', 0)} < {GATE_1_SUBS} — 니치/훅 iteration 필요")
           if month_since_start >= 6:
               if snapshot.get("subs", 0) < GATE_2_SUBS:
                   warnings.append(f"2nd gate FAIL — subs {snapshot.get('subs', 0)} < {GATE_2_SUBS}")
               if snapshot.get("retention_3s", 0) < GATE_2_RETENTION:
                   warnings.append(f"2nd gate FAIL — retention_3s {snapshot.get('retention_3s', 0):.3f} < {GATE_2_RETENTION}")
           return {"warnings": warnings, "pivot_required": len(warnings) > 0,
                   "month_since_start": month_since_start}

       def percent(current: float, target: float) -> float:
           return round(100.0 * current / target, 1) if target > 0 else 0.0

       def render_row(year_month: str, snapshot: dict, notes: str = "") -> str:
           subs = snapshot.get("subs", 0)
           views_12m = snapshot.get("views_12m", 0)
           pct_1st = percent(subs, GATE_1_SUBS)
           pct_2nd_subs = percent(subs, GATE_2_SUBS)
           pct_3rd_subs = percent(subs, GATE_3_SUBS)
           pct_3rd_views = percent(views_12m, GATE_3_VIEWS)
           return (f"| {year_month} | {subs} | {views_12m} | {pct_1st}% | {pct_2nd_subs}% "
                   f"| {pct_3rd_subs}% | {pct_3rd_views}% | {notes} |")

       def upsert_row(traj: Path, year_month: str, row: str) -> bool:
           """Insert new row right below TRAJECTORY_APPEND_MARKER. If year_month row exists, replace.
           Returns True if inserted or replaced."""
           text = traj.read_text(encoding="utf-8")
           if APPEND_MARKER not in text:
               raise RuntimeError(f"{APPEND_MARKER} missing in {traj}")
           head, tail = text.split(APPEND_MARKER, 1)
           # tail starts right after marker — look for existing row with same year-month
           pattern = re.compile(rf"^\|\s*{re.escape(year_month)}\s*\|.*\n", re.MULTILINE)
           if pattern.search(tail):
               new_tail = pattern.sub(row + "\n", tail, count=1)
           else:
               # Insert right after marker newline — find first empty-or-table-header line, append row
               lines = tail.split("\n")
               # find the end of table (first blank line after the header)
               # strategy: insert right after the `|-------|...|` separator
               insert_idx = 0
               for i, line in enumerate(lines):
                   if re.match(r"^\|[-:\s|]+\|$", line):
                       insert_idx = i + 1
                       break
               if insert_idx == 0:
                   # no table found — just append after marker
                   insert_idx = 1
               lines.insert(insert_idx, row)
               new_tail = "\n".join(lines)
           traj.write_text(head + APPEND_MARKER + new_tail, encoding="utf-8")
           return True

       def update_mermaid(traj: Path, snapshots: list[tuple[str, int]]) -> None:
           """Replace mermaid x-axis and line[] with all known snapshots."""
           if not snapshots:
               return
           text = traj.read_text(encoding="utf-8")
           x_axis = "[" + ", ".join(m for m, _ in snapshots) + "]"
           line_data = "[" + ", ".join(str(s) for _, s in snapshots) + "]"
           text = re.sub(r"x-axis\s+\[[^\]]*\]", f"x-axis {x_axis}", text, count=1)
           text = re.sub(r"line\s+\[[^\]]*\]", f"line {line_data}", text, count=1)
           traj.write_text(text, encoding="utf-8")

       def parse_existing_snapshots(traj: Path) -> list[tuple[str, int]]:
           text = traj.read_text(encoding="utf-8")
           if APPEND_MARKER not in text:
               return []
           _, tail = text.split(APPEND_MARKER, 1)
           # Parse rows: | YYYY-MM | subs | ... |
           out: list[tuple[str, int]] = []
           for m in re.finditer(r"^\|\s*(\d{4}-\d{2})\s*\|\s*(\d+)\s*\|", tail, re.MULTILINE):
               out.append((m.group(1), int(m.group(2))))
           return out

       def append_failures(failures: Path, year_month: str, warnings: list[str],
                           now: datetime) -> str | None:
           if not failures.exists():
               return None
           existing = failures.read_text(encoding="utf-8")
           ids = re.findall(r"### F-YPP-(\d{2})", existing)
           next_id = max((int(i) for i in ids), default=0) + 1
           entry_id = f"F-YPP-{next_id:02d}"
           body = [
               "",
               "",
               f"## {entry_id} — YPP trajectory gate 미달 ({year_month})",
               "",
               f"**검사 시각**: {now.isoformat()}",
               "",
               "**경보**:",
           ]
           for w in warnings:
               body.append(f"- {w}")
           body.extend([
               "",
               "**조치**:",
               "1. 현재 월 상위 3 영상 composite score 재분석 (`scripts.analytics.monthly_aggregate`)",
               "2. taste gate 회차 확인 (`wiki/kpi/taste_gate_*.md`) — 품질 판단 일치 여부",
               "3. 1차 gate 미달 시: 니치/훅 iteration Plan 추가 (Phase 11 candidate)",
               "4. 2차 gate 미달 시: 전략 재검토 + taste gate 주기 상향 (월 1회 → 2주 1회)",
               "",
               "**참조**: `wiki/ypp/trajectory.md` + Plan 10-08 ROLLBACK.md 학습 회로 오염 시나리오",
           ])
           with failures.open("a", encoding="utf-8") as f:
               f.write("\n".join(body) + "\n")
           return entry_id

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="YPP trajectory appender — SC#6")
           parser.add_argument("--subs", type=int, required=True)
           parser.add_argument("--views-12m", type=int, required=True,
                               help="Rolling 12-month view count")
           parser.add_argument("--retention-3s", type=float, default=0.0)
           parser.add_argument("--year-month", default=None,
                               help="YYYY-MM (default: current month KST)")
           parser.add_argument("--notes", default="")
           parser.add_argument("--trajectory", type=Path, default=Path("wiki/ypp/trajectory.md"))
           parser.add_argument("--failures", type=Path, default=Path("FAILURES.md"))
           parser.add_argument("--dry-run", action="store_true")
           args = parser.parse_args(argv)

           now = datetime.now(KST)
           ym = args.year_month or f"{now.year}-{now.month:02d}"
           current = date(int(ym[:4]), int(ym[5:7]), 1)
           m_since = months_since(PHASE_10_START, current)

           snapshot = {"subs": args.subs, "views_12m": args.views_12m,
                       "retention_3s": args.retention_3s}
           gate_eval = evaluate_gates(snapshot, m_since)

           row = render_row(ym, snapshot, args.notes)

           summary = {
               "year_month": ym,
               "month_since_start": m_since,
               "subs": args.subs,
               "views_12m": args.views_12m,
               "retention_3s": args.retention_3s,
               "gate_warnings": gate_eval["warnings"],
               "pivot_required": gate_eval["pivot_required"],
               "dry_run": args.dry_run,
           }

           if args.dry_run:
               summary["would_append_row"] = row
               print(json.dumps(summary, ensure_ascii=False, indent=2))
               return 0

           upsert_row(args.trajectory, ym, row)
           all_snaps = parse_existing_snapshots(args.trajectory)
           update_mermaid(args.trajectory, all_snaps)

           if gate_eval["warnings"]:
               entry_id = append_failures(args.failures, ym, gate_eval["warnings"], now)
               summary["failures_appended"] = entry_id

           print(json.dumps(summary, ensure_ascii=False, indent=2))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    2. `tests/phase10/test_trajectory_append.py` 작성 (≥90 lines) — 13 tests Test 1-13:
       - `evaluate_gates()` 단위 테스트 6종 (pre-3m / 1st-fail / 1st-pass / 2nd-fail-subs / 2nd-fail-retention / 2nd-pass)
       - `upsert_row()` — tmp trajectory.md (Task 1 scaffold 복사) → append + idempotent (같은 month 재호출 replace)
       - `update_mermaid()` — 3 snapshots → x-axis `[2026-04, 2026-05, 2026-06]` + line `[0, 5, 23]`
       - `append_failures()` — tmp FAILURES.md seed → F-YPP-01 추가 + strict prefix 유지
       - CLI `--dry-run` — trajectory.md sha256 전후 동일
       - `months_since(PHASE_10_START, date(2026,7,25))` == 3
       - Missing marker → RuntimeError
    3. 실행: `pytest tests/phase10/test_trajectory_append.py -xvs` → 13 tests GREEN
    4. 수동 실증: `python -m scripts.analytics.trajectory_append --dry-run --subs 150 --views-12m 125000 --retention-3s 0.62 --year-month 2026-07` → exit 0 + stdout JSON + `gate_warnings: []` (subs>=100 + month_since 3)
    5. 수동 실증 (pivot warning): `python -m scripts.analytics.trajectory_append --dry-run --subs 50 --views-12m 10000 --year-month 2026-07` → exit 0 + `"pivot_required": true` (1차 gate fail)
  </action>
  <acceptance_criteria>
    - `ls scripts/analytics/trajectory_append.py` 존재
    - `wc -l scripts/analytics/trajectory_append.py` >= 150
    - `python -c "from scripts.analytics.trajectory_append import main, evaluate_gates, upsert_row, update_mermaid, months_since, append_failures, render_row; print('OK')"` prints OK
    - `python -m scripts.analytics.trajectory_append --dry-run --subs 150 --views-12m 125000 --retention-3s 0.62 --year-month 2026-07` exit 0 + stdout JSON 에 `"gate_warnings": []` (통과)
    - `python -m scripts.analytics.trajectory_append --dry-run --subs 50 --views-12m 10000 --year-month 2026-07` exit 0 + stdout JSON 에 `"pivot_required": true`
    - `pytest tests/phase10/test_trajectory_append.py -q` 13 tests GREEN
    - `grep -c "GATE_1_SUBS = 100\|GATE_2_SUBS = 300\|GATE_2_RETENTION = 0.60\|GATE_3_SUBS = 1000\|GATE_3_VIEWS = 10_000_000" scripts/analytics/trajectory_append.py` == 5 (5 threshold 상수 정확)
    - `grep -c "PHASE_10_START = date(2026, 4, 20)" scripts/analytics/trajectory_append.py` == 1
    - `grep -c "F-YPP" scripts/analytics/trajectory_append.py` >= 2
    - Phase 6 wiki regression 보존: `pytest tests/phase06 -q --tb=no` exit 0
    - Phase 10 Plans 1-6 regression: `pytest tests/phase10 --ignore=tests/phase10/test_trajectory_append.py -q --tb=no` GREEN
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_trajectory_append.py -q && python -m scripts.analytics.trajectory_append --dry-run --subs 150 --views-12m 125000 --retention-3s 0.62 --year-month 2026-07</automated>
  </verify>
  <done>trajectory_append.py CLI 완비 (150+ lines), 3-gate logic + upsert + mermaid + FAILURES append, 13 tests GREEN, Phase 6/10 regression 보존</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_trajectory_append.py -v` 13 tests PASS
- `python -m scripts.analytics.trajectory_append --dry-run --subs 150 --views-12m 125000 --retention-3s 0.62 --year-month 2026-07` exit 0 + warnings empty
- `python -m scripts.analytics.trajectory_append --dry-run --subs 50 --views-12m 10000 --year-month 2026-07` exit 0 + pivot_required true
- trajectory.md + MOC.md 수정 완료, 다른 wiki 파일 byte-identical
- Phase 6 wiki regression 보존
- Phase 10 Plans 1-6 regression 보존
- SC#6 traceability (WARNING #1): frontmatter `phase_success_criteria: [SC-6]` + `tags: [ypp-trajectory, sc6-exit-criterion]` 로 ROADMAP §276 연결 명시
</verification>

<success_criteria>
1. `wiki/ypp/trajectory.md` 60+ lines scaffold (frontmatter + 3-gate table + markers + mermaid)
2. `wiki/ypp/MOC.md` trajectory.md line [ ] → [x] flipped (기타 라인 byte-identical)
3. `scripts/analytics/trajectory_append.py` 150+ lines (5 threshold 상수, evaluate_gates, upsert_row, update_mermaid, append_failures, months_since)
4. 13 tests GREEN
5. SC#6 본질 구조 확보 — `wiki/ypp/trajectory.md` 자동 append 회로 가동 준비
6. SC#6 traceability frontmatter 완비 (WARNING #1) — `phase_success_criteria: [SC-6]` + `tags` + `requirements` 주석
7. Phase 6 + Phase 10 Plans 1-6 regression 보존
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-07-SUMMARY.md` with:
- Commits: (trajectory scaffold + MOC flip + appender CLI + tests)
- SC#6 status (구조적 커버 — 실 데이터는 Plan 4 scheduler 실행 후 축적)
- SC#6 traceability (WARNING #1): frontmatter `phase_success_criteria: [SC-6]` + `tags: [sc6-exit-criterion]` — ROADMAP §276 visible trace 확보
- KPI-02 secondary trigger (monthly_aggregate 와 trajectory_append 결합으로 "월 1회 wiki/shorts/kpi_log.md 자동 생성" 범위 확장)
- Next: Plan 8 (ROLLBACK docs + stop_scheduler) — Wave 4 최종
- Plan 4 Scheduler 에 `ypp-trajectory-monthly.yml` 또는 Windows Task 추가 선택적 (본 Plan 범위 외)
</output>
