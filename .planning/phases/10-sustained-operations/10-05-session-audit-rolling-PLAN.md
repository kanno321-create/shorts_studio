---
phase: 10-sustained-operations
plan: 05
type: execute
wave: 3
depends_on: [10-04-scheduler-hybrid]
files_modified:
  - scripts/audit/session_audit_rollup.py
  - tests/phase10/test_session_audit.py
  - logs/.gitkeep
autonomous: true
requirements: [AUDIT-01]
must_haves:
  truths:
    - "scripts/audit/session_audit_rollup.py 가 harness_audit.py --json-out 을 1회 실행하여 logs/session_audit.jsonl 에 append 한다"
    - "30일 rolling 윈도우의 session 점수 평균이 ≥ 80 이면 exit 0, < 80 이면 FAILURES.md F-AUDIT-XX append + exit 1 + stderr 경고"
    - "KST 기준 timestamp 사용 (pytz 금지 — zoneinfo only)"
    - "데이터 0건인 경우 (신규 스튜디오) 100.0 기본값으로 통과 (rolling_avg 빈 list guard)"
  artifacts:
    - path: scripts/audit/session_audit_rollup.py
      provides: "30-day rolling session audit score CLI — AUDIT-01"
      min_lines: 140
    - path: tests/phase10/test_session_audit.py
      provides: "AUDIT-01 unit — jsonl append + rolling avg + threshold < 80 FAILURES append"
      min_lines: 100
    - path: logs/.gitkeep
      provides: "logs/ dir git-tracked placeholder (session_audit.jsonl gitignored)"
  key_links:
    - from: scripts/audit/session_audit_rollup.py
      to: scripts/validate/harness_audit.py
      via: "subprocess.run([sys.executable, '-m', 'scripts.validate.harness_audit', '--json-out', str(tmp_json)])"
      pattern: "scripts\\.validate\\.harness_audit"
    - from: scripts/audit/session_audit_rollup.py
      to: logs/session_audit.jsonl
      via: "open('logs/session_audit.jsonl', 'a', encoding='utf-8') — 한 줄 = 한 세션 JSON record"
      pattern: "session_audit\\.jsonl"
    - from: scripts/audit/session_audit_rollup.py
      to: FAILURES.md
      via: "rolling avg < 80 시 F-AUDIT-XX append (direct I/O)"
      pattern: "F-AUDIT"
---

<objective>
매 세션 시작 시 자동 감사 점수를 기록하고 30일 rolling 평균이 ≥ 80 을 유지함을 증명하는 CLI 를 구축한다. D-2 Lock 경로인 `.claude/hooks/session_start.py` 자체는 수정 금지이므로, **Plan 5 는 별도 scripts/audit/session_audit_rollup.py 로 구성**하여 harness_audit.py 를 subprocess 호출하고 결과 JSON 을 `logs/session_audit.jsonl` 에 append 한다. 평균 미달 시 FAILURES.md append + exit 1 로 감사 실패를 신호화한다.

Purpose: D-2 Lock 기간 중 "조용히 점수가 떨어지는" 시나리오 방어. 매 세션 증적 + 30일 이동평균만이 continuous quality pass 증명.
Output: session_audit_rollup.py + 30일 rolling 로직 + logs/ dir placeholder.

Notes:
- 본 CLI 는 D-2 Lock 금지 경로 (`.claude/hooks/*.py`, `.claude/skills/*/SKILL.md`, `.claude/agents/*/SKILL.md`, `CLAUDE.md`) 를 **절대 수정하지 않는다**.
- 매 세션 실행은 Plan 4 Scheduler 또는 대표님 수동 호출로 dispatch. 이 Plan 은 CLI + 테스트만 shipping.
- **Depends on simplification (WARNING #2)**: `depends_on: [10-04-scheduler-hybrid]` 만 선언. Plan 2 (drift-scan-phase-lock) 는 Plan 4 가 이미 transit 의존 (Plan 4 의 `drift-scan-weekly.yml` 이 Plan 2 drift_scan.py 를 호출) — wave 병렬성 오판 방지를 위해 Plan 5 는 Plan 4 에만 직접 의존.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/STATE.md
@.planning/phases/10-sustained-operations/10-CONTEXT.md
@.planning/phases/10-sustained-operations/10-RESEARCH.md
@.planning/phases/10-sustained-operations/10-VALIDATION.md
@scripts/validate/harness_audit.py
@CLAUDE.md

<interfaces>
<!-- harness_audit.py public API (Phase 7 existing) -->

From `scripts/validate/harness_audit.py` (Phase 7 Plan 07-01 존재, 280줄):
```python
def run_audit() -> tuple[int, list[str], list[str]]:
    """Returns (score, violations, warnings). Score 0-100.
    Called by: main(["--json-out", path]) writes JSON file.
    --threshold N flag: exit 1 if score < N."""

def main(argv: list[str] | None = None) -> int:
    """CLI entry. --json-out PATH, --threshold 80, --verbose."""
```

From RESEARCH.md §Plan 5 Open Q1-Q4 — session_audit_rollup design:
```python
# Subprocess call (not direct import — preserves harness_audit testability)
result = subprocess.run(
    [sys.executable, "-m", "scripts.validate.harness_audit",
     "--json-out", str(tmp_json_path), "--threshold", "0"],
    capture_output=True, text=True, encoding="utf-8"
)
audit_json = json.loads(tmp_json_path.read_text(encoding="utf-8"))
score = audit_json["score"]   # int 0-100

# Rolling avg
def rolling_avg(jsonl_path: Path, days: int = 30) -> float:
    now = datetime.now(KST)
    cutoff = now - timedelta(days=days)
    scores = []
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            ts = datetime.fromisoformat(record["timestamp"]).astimezone(KST)
            if ts >= cutoff:
                scores.append(record["score"])
    if not scores:
        return 100.0   # empty = pass (신규 스튜디오)
    return sum(scores) / len(scores)
```

From `.gitignore` 규약 (RESEARCH Open Q2):
- `logs/session_audit.jsonl` 은 gitignored (개인 감사 기록)
- `logs/.gitkeep` 은 git-tracked (폴더 존재 placeholder)
- `logs/` 자체는 .gitignore 에 `logs/*` + `!logs/.gitkeep` 식으로 포함
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: session_audit_rollup.py + 30일 rolling + FAILURES append + 테스트 (single task — 자립적)</name>
  <files>
    scripts/audit/session_audit_rollup.py,
    tests/phase10/test_session_audit.py,
    logs/.gitkeep
  </files>
  <read_first>
    - `scripts/validate/harness_audit.py` 전체 (Phase 7 Plan 07-01, 280줄) — `run_audit()`, `--json-out` output schema
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 5 Open Q1-Q4 + §Code Example for Plan 5
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pitfall 5 (cp949 reconfigure)
    - `scripts/audit/skill_patch_counter.py` Plan 1 완성본 — `append_failures()` direct I/O 재사용 패턴
    - `tests/phase10/conftest.py` (`tmp_git_repo`, `freeze_kst_now` fixtures)
    - `.gitignore` 현재 파일 — logs/ 관련 규약 이미 있는지 확인
  </read_first>
  <behavior>
    - Test 1 (test_logs_gitkeep_exists_logs_jsonl_ignored): `logs/.gitkeep` 존재 + `logs/session_audit.jsonl` 은 .gitignore 에 포함
    - Test 2 (test_subprocess_call_to_harness_audit): monkeypatch `subprocess.run` → MockResult with returncode 0 + json file created → session_audit_rollup 가 tmp_json 경로 읽고 score parse
    - Test 3 (test_append_to_jsonl): 빈 jsonl → 1회 호출 후 1 line record with {timestamp, score, violations_count, warnings_count}
    - Test 4 (test_rolling_avg_empty_returns_100): 빈 jsonl → avg 100.0 반환 + exit 0
    - Test 5 (test_rolling_avg_below_80_triggers_failures_append): 3 records with scores [70, 75, 70] → avg = 71.67 → FAILURES.md F-AUDIT-01 append + exit 1
    - Test 6 (test_rolling_avg_at_80_passes): records [80, 80, 80] → avg 80 → exit 0 (경계값)
    - Test 7 (test_records_older_than_30_days_excluded): 60일 전 score 50 + 어제 score 90 → avg 90 → exit 0 (30일 cutoff 증명)
    - Test 8 (test_cli_dry_run_no_jsonl_mutation): `--dry-run` → jsonl 미수정 + stdout JSON 출력
    - Test 9 (test_cli_score_threshold_override): `--threshold 70` 으로 커스터마이즈 → avg 75 면 exit 0
    - Test 10 (test_cp949_safe_korean_reason): FAILURES append body 에 한글 포함 가능 (Windows cp949 reconfigure 확인)
    - Test 11 (test_harness_audit_subprocess_failure_explicit_raise): subprocess returncode != 0 → explicit raise (Project Rule 3 silent fallback 금지)
  </behavior>
  <action>
    1. `logs/.gitkeep` 빈 파일 생성
    2. `.gitignore` 확인 — `logs/session_audit.jsonl` 포함되어 있지 않으면 append (기존 `.gitignore` 는 **byte 수정 없이** 맨 아래 1 section 추가만 — Plan 5 scope 내 유일한 외부 파일 수정):
       ```
       # Phase 10 Plan 5 — session audit log (gitignored, logs/.gitkeep 만 git-tracked)
       logs/*.jsonl
       logs/*.json
       !logs/.gitkeep
       ```
       (이미 규약 있으면 skip)
    3. `scripts/audit/session_audit_rollup.py` 작성 (≥140 lines):
       ```python
       """Session audit 30-day rolling — AUDIT-01 / SC#3.

       Usage:
         python -m scripts.audit.session_audit_rollup            # runs harness_audit + appends + rolling check
         python -m scripts.audit.session_audit_rollup --dry-run  # check rolling avg only, no mutation
         python -m scripts.audit.session_audit_rollup --threshold 75   # override default 80

       Design:
         - Subprocess harness_audit.py (NOT direct import) → decouples failure modes
         - Append JSONL record to logs/session_audit.jsonl (gitignored)
         - Rolling 30-day avg via zoneinfo KST (pytz 금지)
         - avg < threshold → FAILURES.md F-AUDIT-NN append + exit 1

       NOTE: This CLI does NOT modify .claude/hooks/session_start.py (D-2 Lock forbidden path).
       It runs as an external rollup — can be invoked by .claude/hooks/session_start.py stdout
       hand-off OR standalone via Plan 4 Scheduler OR 대표님 manual.
       """
       from __future__ import annotations
       import argparse
       import json
       import re
       import subprocess
       import sys
       import tempfile
       from datetime import datetime, timedelta
       from pathlib import Path
       from zoneinfo import ZoneInfo

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")
       DEFAULT_THRESHOLD = 80
       DEFAULT_WINDOW_DAYS = 30
       DEFAULT_JSONL = Path("logs/session_audit.jsonl")
       DEFAULT_FAILURES = Path("FAILURES.md")

       def run_harness_audit(studio_root: Path) -> dict:
           """Invoke scripts.validate.harness_audit via subprocess + read JSON output."""
           with tempfile.NamedTemporaryFile(
               mode="w", suffix=".json", delete=False, encoding="utf-8"
           ) as tmp:
               tmp_path = Path(tmp.name)
           try:
               result = subprocess.run(
                   [sys.executable, "-m", "scripts.validate.harness_audit",
                    "--json-out", str(tmp_path), "--threshold", "0"],
                   capture_output=True, text=True, encoding="utf-8",
                   cwd=studio_root,
               )
               # threshold=0 → harness_audit exit 0 regardless of score (scoring only)
               if result.returncode != 0:
                   raise RuntimeError(
                       f"harness_audit subprocess failed rc={result.returncode}\n"
                       f"stdout: {result.stdout[-500:]}\nstderr: {result.stderr[-500:]}"
                   )
               return json.loads(tmp_path.read_text(encoding="utf-8"))
           finally:
               if tmp_path.exists():
                   tmp_path.unlink()

       def append_session_record(jsonl: Path, audit_json: dict, now: datetime) -> dict:
           record = {
               "timestamp": now.isoformat(),
               "score": audit_json.get("score", 0),
               "violations_count": len(audit_json.get("violations", [])),
               "warnings_count": len(audit_json.get("warnings", [])),
           }
           jsonl.parent.mkdir(parents=True, exist_ok=True)
           with jsonl.open("a", encoding="utf-8") as f:
               f.write(json.dumps(record, ensure_ascii=False) + "\n")
           return record

       def rolling_avg(jsonl: Path, days: int = DEFAULT_WINDOW_DAYS,
                       now: datetime | None = None) -> tuple[float, int]:
           """Return (avg_score, sample_count) over last `days` days of jsonl."""
           if now is None:
               now = datetime.now(KST)
           cutoff = now - timedelta(days=days)
           if not jsonl.exists():
               return (100.0, 0)
           scores: list[int] = []
           with jsonl.open(encoding="utf-8") as f:
               for line in f:
                   line = line.strip()
                   if not line:
                       continue
                   try:
                       record = json.loads(line)
                   except json.JSONDecodeError:
                       continue   # corrupt line — skip but don't raise
                   ts_raw = record.get("timestamp")
                   if not ts_raw:
                       continue
                   ts = datetime.fromisoformat(ts_raw).astimezone(KST)
                   if ts >= cutoff:
                       scores.append(int(record.get("score", 0)))
           if not scores:
               return (100.0, 0)
           return (sum(scores) / len(scores), len(scores))

       def append_failures(failures: Path, avg: float, sample_count: int,
                           threshold: int, now: datetime) -> str:
           if not failures.exists():
               raise FileNotFoundError(f"FAILURES.md not found at {failures}")
           existing = failures.read_text(encoding="utf-8")
           ids = re.findall(r"### F-AUDIT-(\d{2})", existing)
           next_id = max((int(i) for i in ids), default=0) + 1
           entry_id = f"F-AUDIT-{next_id:02d}"
           body = [
               "",
               "",
               f"## {entry_id} — Session audit rolling avg 미달 ({now.date().isoformat()})",
               "",
               f"**증상**: 최근 {DEFAULT_WINDOW_DAYS}일 rolling 평균 점수 {avg:.1f} < 임계값 {threshold}",
               "",
               f"**Sample count**: {sample_count}",
               f"**Measurement timestamp**: {now.isoformat()}",
               "",
               "**조치**:",
               "1. `scripts/validate/harness_audit.py` 수동 실행 → 최신 violations/warnings 확인",
               "2. SKILL 500줄 초과 / description 1024자 초과 / deprecated_patterns drift 등 원인 분류",
               "3. D-2 Lock 기간 중이면 `FAILURES.md` 에 근본 원인 기록 + 해결 계획 appendonly (SKILL patch 금지 유지)",
               "4. Lock 해제 후에는 해결 commit 에 본 엔트리 reference 필수",
               "",
               "**연계**: Plan 10-02 drift_scan (A급 drift 병행 확인) + Plan 10-08 ROLLBACK.md 참조",
           ]
           with failures.open("a", encoding="utf-8") as f:
               f.write("\n".join(body) + "\n")
           return entry_id

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="Session audit 30-day rolling — AUDIT-01")
           parser.add_argument("--studio-root", type=Path, default=Path("."))
           parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
           parser.add_argument("--failures", type=Path, default=DEFAULT_FAILURES)
           parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
           parser.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
           parser.add_argument("--dry-run", action="store_true")
           parser.add_argument("--skip-audit", action="store_true",
                               help="Skip harness_audit subprocess (rolling check only)")
           args = parser.parse_args(argv)

           studio_root = args.studio_root.resolve()
           now = datetime.now(KST)

           if not args.skip_audit and not args.dry_run:
               audit_json = run_harness_audit(studio_root)
               record = append_session_record(args.jsonl, audit_json, now)
           elif args.dry_run and not args.skip_audit:
               audit_json = run_harness_audit(studio_root)
               record = {
                   "timestamp": now.isoformat(),
                   "score": audit_json.get("score", 0),
                   "violations_count": len(audit_json.get("violations", [])),
                   "warnings_count": len(audit_json.get("warnings", [])),
                   "dry_run_would_append_to": str(args.jsonl),
               }
           else:
               record = {"timestamp": now.isoformat(), "skipped_audit": True}

           avg, count = rolling_avg(args.jsonl, args.window_days, now)
           summary = {
               "current_record": record,
               "rolling_avg": round(avg, 2),
               "sample_count": count,
               "threshold": args.threshold,
               "window_days": args.window_days,
               "passes": avg >= args.threshold,
               "dry_run": args.dry_run,
           }

           if avg < args.threshold and not args.dry_run and count > 0:
               entry_id = append_failures(args.failures, avg, count, args.threshold, now)
               summary["failures_appended"] = entry_id
               print(json.dumps(summary, ensure_ascii=False, indent=2))
               print(f"[FAIL] rolling avg {avg:.1f} < {args.threshold}", file=sys.stderr)
               return 1

           print(json.dumps(summary, ensure_ascii=False, indent=2))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    4. `tests/phase10/test_session_audit.py` 작성 (≥100 lines) — 11 tests (Test 1-11 behaviors):
       - `monkeypatch subprocess.run` 시 내부 tmp file 에 json 쓰도록 side_effect 구현
       - `freeze_kst_now` fixture 로 일정 시각 고정 (30일 이전 record 시나리오 빌드)
       - tmp FAILURES.md seed + append 검증 (strict prefix 유지)
       - `.gitignore` 체크: `Path('.gitignore').read_text()` 에 `logs/*.jsonl` 또는 비슷한 패턴 존재
    5. 실행: `pytest tests/phase10/test_session_audit.py -xvs` → 11 tests GREEN
    6. 수동 실증: `python -m scripts.audit.session_audit_rollup --dry-run --skip-audit` → exit 0 + stdout JSON `"rolling_avg": 100.0, "sample_count": 0, "passes": true`
    7. 수동 실증 (실 harness_audit 실행 — 현재 repo 에서 score ≥ 80 기대): `python -m scripts.audit.session_audit_rollup --dry-run` → exit 0 + score 확인 (현재 Phase 7 기준 score 90)
  </action>
  <acceptance_criteria>
    - `ls scripts/audit/session_audit_rollup.py logs/.gitkeep` 존재
    - `grep -c "logs/\\*\\.jsonl\\|logs/session_audit" .gitignore` ≥ 1
    - `python -c "from scripts.audit.session_audit_rollup import main, rolling_avg, append_failures, append_session_record, run_harness_audit; print('OK')"` prints OK
    - `python -m scripts.audit.session_audit_rollup --dry-run --skip-audit` exit 0 + stdout JSON `"passes": true` (빈 jsonl → 100.0 기본값)
    - `python -m scripts.audit.session_audit_rollup --dry-run` exit 0 + stdout JSON `"score"` key 존재 + score ≥ 80 (현재 repo 상태)
    - `pytest tests/phase10/test_session_audit.py -q` 11 tests GREEN
    - `grep -c "F-AUDIT" scripts/audit/session_audit_rollup.py` ≥ 2 (append_failures 에서 regex + id prefix)
    - `grep -c "zoneinfo\\|ZoneInfo" scripts/audit/session_audit_rollup.py` ≥ 2 (import + usage)
    - `grep -c "pytz" scripts/audit/session_audit_rollup.py` == 0 (zoneinfo only, pytz 금지)
    - `wc -l scripts/audit/session_audit_rollup.py` ≥ 140 lines
    - D-2 Lock 준수: Plan 5 의 files_modified 에 `.claude/hooks/*.py` / `.claude/skills/*/SKILL.md` / `.claude/agents/*/SKILL.md` / `CLAUDE.md` 없음 (frontmatter 재확인)
    - Phase 10 Plans 1-4 regression 보존: `pytest tests/phase10/test_skill_patch_counter.py tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py tests/phase10/test_fetch_kpi.py tests/phase10/test_monthly_aggregate.py tests/phase10/test_workflows_yaml.py tests/phase10/test_notify_failure.py -q --tb=no` GREEN
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_session_audit.py -q && python -m scripts.audit.session_audit_rollup --dry-run --skip-audit</automated>
  </verify>
  <done>session_audit_rollup.py 완비, 30일 rolling + FAILURES append, 11 tests GREEN, Phase 10 Plans 1-4 regression 보존, D-2 Lock 금지 경로 수정 없음</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_session_audit.py -v` 11 tests PASS
- `python -m scripts.audit.session_audit_rollup --dry-run --skip-audit` exit 0 + stdout JSON
- `python -m scripts.audit.session_audit_rollup --dry-run` exit 0 (실 harness_audit 호출 + jsonl 미수정)
- `logs/.gitkeep` 존재 + `logs/*.jsonl` .gitignore 등록
- AUDIT-01 requirement 코드+테스트 레벨 실증 완료
- D-2 Lock 금지 경로 수정 없음 (self-check)
- WARNING #2 depends_on 단순화: `[10-04-scheduler-hybrid]` 만 선언 — Plan 2 는 Plan 4 transit 의존
</verification>

<success_criteria>
1. `scripts/audit/session_audit_rollup.py` 140+ lines, stdlib only, zoneinfo KST 사용 (pytz 금지)
2. 3 CLI 모드: default (audit + append + rolling check), --dry-run (no mutation), --skip-audit (rolling only)
3. 11 tests GREEN covering 경계값 (0 records / 80 exact / 30day cutoff / corrupt line tolerance / korean reason)
4. Rolling avg < threshold 시 FAILURES.md F-AUDIT-NN append + exit 1 + stderr 경고
5. `logs/.gitkeep` placeholder + `.gitignore` 에 `logs/*.jsonl` 규약
6. AUDIT-01 checkbox trigger 준비 완료
7. D-2 Lock 금지 경로 수정 전혀 없음 (self-check 완료)
8. Phase 10 Plans 1-4 regression 전수 보존
9. WARNING #2 depends_on 단순화 완료 ([10-04-scheduler-hybrid] 만, Plan 2 는 transit 의존)
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-05-SUMMARY.md` with:
- Commits: (session_audit_rollup + tests + logs/.gitkeep + .gitignore append)
- Reusable assets: scripts/validate/harness_audit.py subprocess 호출
- AUDIT-01 checkbox trigger
- WARNING #2 depends_on 단순화 — Plan 2 는 Plan 4 transit 의존으로 wave 병렬성 오판 제거
- Next: Plan 6 (research loop NotebookLM) + Plan 7 (trajectory) — Wave 3 parallel
- 수동 dispatch: Plan 4 scheduler 가 Windows Task 로 session_audit_rollup 을 주기 실행하도록 `windows_tasks.ps1` 확장 (Plan 4 가 완료되어 있으면 이 Plan 에서 PowerShell 추가도 가능하지만, boundary 로 분리 유지)
</output>
