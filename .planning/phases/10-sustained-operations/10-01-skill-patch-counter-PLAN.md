---
phase: 10-sustained-operations
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/audit/__init__.py
  - scripts/audit/skill_patch_counter.py
  - tests/phase10/__init__.py
  - tests/phase10/conftest.py
  - tests/phase10/test_skill_patch_counter.py
  - reports/.gitkeep
autonomous: true
requirements: [FAIL-04]
must_haves:
  truths:
    - "scripts/audit/skill_patch_counter.py 가 D-2 Lock 기간 (2026-04-20~2026-06-20) 중 4 금지 경로에 대한 git log 커밋 위반을 count 한다"
    - "count > 0 시 reports/skill_patch_count_YYYY-MM.md 가 위반 테이블을 포함하여 생성되고 FAILURES.md 에 F-D2-XX 엔트리가 append 된다"
    - "count == 0 시 report 가 `**Violation count:** 0 ✅` 로 기록되고 exit 0 반환"
    - "--dry-run 모드는 파일 생성 없이 stdout JSON 출력만 한다"
  artifacts:
    - path: scripts/audit/skill_patch_counter.py
      provides: "D-2 Lock git log 위반 카운터 CLI (stdlib-only)"
      min_lines: 100
    - path: scripts/audit/__init__.py
      provides: "scripts.audit 패키지 네임스페이스"
    - path: tests/phase10/conftest.py
      provides: "tmp git repo fixture + 월/위반 빌더 헬퍼"
      min_lines: 60
    - path: tests/phase10/test_skill_patch_counter.py
      provides: "FAIL-04 유닛 테스트 (no-violation / 1-violation / 4-violation / dry-run)"
      min_lines: 80
    - path: reports/.gitkeep
      provides: "reports/ 폴더 git 추적용 placeholder (월간 리포트 출력처)"
  key_links:
    - from: scripts/audit/skill_patch_counter.py
      to: git subprocess
      via: "subprocess.run(['git','log','--since=...','--until=...','--name-only','--pretty=format:---COMMIT---%n%H|%aI|%s'])"
      pattern: "subprocess\\.run\\(\\[\"git\",\\s*\"log\""
    - from: scripts/audit/skill_patch_counter.py
      to: FAILURES.md
      via: "count>0 시 append-mode 직접 파일 open + F-D2-NN 엔트리 기록 (Claude Write tool 우회, Hook bypass by direct I/O)"
      pattern: "open\\(.*[Ff][Aa][Ii][Ll][Uu][Rr][Ee][Ss]\\.md.*[\"']a[\"']"
    - from: tests/phase10/test_skill_patch_counter.py
      to: tmp_path git repo
      via: "conftest.py tmp_git_repo fixture — subprocess init/add/commit 으로 synthetic violation 생성"
      pattern: "tmp_git_repo"
---

<objective>
D-2 Lock 규율 (Phase 10 첫 2개월 SKILL patch 전면 금지, FAIL-04) 을 물리적으로 증명하는 git log grep 기반 카운터 CLI 를 작성한다. 4 금지 경로 (`.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md` 본문) 에 대한 commit 위반을 월간 리포트 + FAILURES.md append 로 기록하여 Plan 4 Scheduler 가 월 1회 호출할 수 있는 standalone CLI 를 확보한다.

Purpose: 텍스트 약속만으로는 D-2 저수지 규율이 깨진다. git log 자동 검사만이 learning-pressure 에 저항한다.
Output: scripts/audit/skill_patch_counter.py (CLI) + reports/ 폴더 + tests/phase10/ 기반 scaffold + 월간 리포트 첫 empty row.
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
@CLAUDE.md
@FAILURES.md
@.claude/hooks/pre_tool_use.py
@scripts/failures/aggregate_patterns.py

<interfaces>
<!-- Key reusable contracts the executor needs. Extracted from codebase. -->

From RESEARCH.md §Plan 1 Open Q1 & Reusable Assets Map (aggregate_patterns.py design pattern):
```python
# Design patterns to reuse (DO NOT re-invent):
# 1. stdlib-only (no pandas / no pyyaml)
# 2. argparse + --output + --dry-run
# 3. sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows cp949 guard
# 4. UTF-8 ensure_ascii=False for Korean characters in FAILURES append
```

From .claude/hooks/pre_tool_use.py (D-11 FAILURES.md append enforcement):
```python
def check_failures_append_only(tool_name: str, tool_input: dict) -> dict | None:
    """FAILURES.md Write/Edit must preserve old content as strict prefix.
    Direct file open('a') bypasses this hook (hook only inspects Claude Write/Edit tool)."""
```

From RESEARCH.md §Plan 1 Open Q2 — 4 금지 regex (POSIX forward slash, Windows 포함 동일):
```python
FORBIDDEN_PATTERNS = [
    re.compile(r"^\.claude/agents/.+/SKILL\.md$"),
    re.compile(r"^\.claude/skills/.+/SKILL\.md$"),
    re.compile(r"^\.claude/hooks/[^/]+\.py$"),
    re.compile(r"^CLAUDE\.md$"),
]
```

From RESEARCH.md §Plan 1 Open Q1 (git log invocation — exact arg list):
```python
subprocess.run(
    ["git", "log",
     f"--since={D2_LOCK_START}",    # "2026-04-20"
     f"--until={D2_LOCK_END}",      # "2026-06-20"
     "--name-only",
     "--pretty=format:---COMMIT---%n%H|%aI|%s"],
    capture_output=True, text=True, encoding="utf-8", check=True,
)
```

From RESEARCH.md §Plan 1 Open Q3 (리포트 포맷 — Markdown H1 + 메타 + table):
```markdown
# D-2 Lock Skill Patch Counter — YYYY-MM

**Lock period:** 2026-04-20 ~ 2026-06-20
**Report generated:** ISO+09:00
**Violation count:** N {✅|🚨}

## Violations
| Hash | Date | File | Subject |
| ---- | ---- | ---- | ------- |
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: scripts/audit/ + tests/phase10/ 스캐폴드 + conftest fixture (Wave 0)</name>
  <files>
    scripts/audit/__init__.py,
    tests/phase10/__init__.py,
    tests/phase10/conftest.py,
    reports/.gitkeep
  </files>
  <read_first>
    - `scripts/failures/__init__.py` (7-line namespace, Phase 6 package style 참조)
    - `scripts/failures/aggregate_patterns.py` (stdlib-only argparse + sys.stdout.reconfigure 패턴)
    - `tests/phase06/conftest.py` 또는 `tests/phase07/conftest.py` (fixture 스타일 참조)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 1 + §Validation Architecture
  </read_first>
  <behavior>
    - Test 1 (test_tmp_git_repo_fixture_creates_repo): conftest.py 의 `tmp_git_repo` fixture 가 빈 git repo 를 tmp_path 에 init 한다 (`.git/` 존재 확인)
    - Test 2 (test_make_forbidden_commit_helper): conftest.py 의 `make_commit(repo, files, msg)` helper 가 임의 파일 + 메시지로 commit 생성, commit hash 반환
    - Test 3 (test_reports_gitkeep_exists): `reports/.gitkeep` 파일이 repo 루트에 존재 (Plan 1 월간 리포트 출력처 보장)
  </behavior>
  <action>
    1. `scripts/audit/__init__.py` 작성 (7-line 네임스페이스, `scripts.failures/__init__.py` 스타일):
       ```python
       """scripts.audit — D-2 Lock + drift 감사 CLI 모음. Phase 10 신규."""
       from __future__ import annotations
       __all__ = []   # 각 모듈이 직접 import (CLI entry points)
       ```
    2. `tests/phase10/__init__.py` 작성 (빈 파일, 패키지 마커)
    3. `tests/phase10/conftest.py` 작성 (≥60 lines):
       - `tmp_git_repo(tmp_path) -> Path` fixture: `subprocess.run(["git","init",str(tmp_path)])` + `git config user.email` + `user.name` 설정, 빈 initial commit 생성
       - `make_commit(repo: Path, files: dict[str, str], msg: str) -> str` helper: 각 file path 에 content 쓰기, `git add` + `git commit -m msg`, stdout 에서 commit hash parse 하여 반환
       - `freeze_kst_now(monkeypatch)` autouse fixture: `datetime.datetime.now(ZoneInfo("Asia/Seoul"))` → 2026-04-30T09:00:00+09:00 고정
       - `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` Windows cp949 가드를 top-of-file 에 포함
    4. `reports/.gitkeep` 빈 파일 생성 (월간 리포트 출력처)
    5. `tests/phase10/test_skill_patch_counter.py` 에 Task 1 범위 3 test (Test 1-3) 만 스캐폴드 (RED 상태) — 실제 skill_patch_counter 호출 테스트는 Task 2 에서 추가
    6. 실행: `pytest tests/phase10/ -q` — 3 tests 존재 확인 (RED 허용, conftest 만 통과하면 됨)
  </action>
  <acceptance_criteria>
    - `ls scripts/audit/__init__.py` 존재
    - `ls tests/phase10/__init__.py tests/phase10/conftest.py` 존재
    - `ls reports/.gitkeep` 존재
    - `pytest tests/phase10/conftest.py --collect-only -q` 가 syntax error 없이 fixture 3개 이상 enumerate
    - `pytest tests/phase10/test_skill_patch_counter.py::test_tmp_git_repo_fixture_creates_repo -x` PASS (conftest 기능만 검증)
    - `grep -c "sys.stdout.reconfigure" tests/phase10/conftest.py` ≥ 1
    - `grep -c "tmp_git_repo" tests/phase10/conftest.py` ≥ 1
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/ -q -k "tmp_git_repo_fixture or make_forbidden_commit_helper or reports_gitkeep" --tb=short</automated>
  </verify>
  <done>conftest + __init__ + reports/.gitkeep 완비, 3 fixture-only tests PASS, skill_patch_counter 구현부는 아직 RED 상태</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: skill_patch_counter.py CLI 구현 + 위반 시나리오 regression + FAILURES append</name>
  <files>
    scripts/audit/skill_patch_counter.py,
    tests/phase10/test_skill_patch_counter.py
  </files>
  <read_first>
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 1 Open Q1-Q4 + §Code Examples `Plan 1 skill_patch_counter (GREEN pseudocode)` (line 896-982)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pitfall 3 (FAILURES append hook bypass 규약)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pitfall 5 (Windows cp949 reconfigure 패턴)
    - `FAILURES.md` 전체 (append 포맷 참조: `### F-CTX-01 — ... (YYYY-MM-DD, ...)` 헤딩 스타일)
    - `scripts/failures/aggregate_patterns.py` (argparse + --output 스타일 precedent)
  </read_first>
  <behavior>
    - Test A (test_no_violations_in_clean_repo): 4 금지 경로 touch 없는 commit 만 존재 → `main()` exit 0 + report 에 `**Violation count:** 0 ✅` 포함
    - Test B (test_single_hook_violation_counts_1): `.claude/hooks/pre_tool_use.py` 수정 commit 1개 주입 → exit 1 + report violation table 1-row + FAILURES.md 에 F-D2-XX 엔트리 append 확인
    - Test C (test_all_four_forbidden_paths_count_4): 4 금지 경로 각각 1-commit 생성 → violation count == 4 + report table 4-row
    - Test D (test_files_outside_forbidden_not_counted): `scripts/audit/skill_patch_counter.py` 같은 허용 경로 commit → count 0
    - Test E (test_dry_run_skips_file_output): `--dry-run` 플래그 + violation 있음 → report 파일 **미생성** + FAILURES 미append + stdout JSON `{"violation_count": N, ...}` 출력
    - Test F (test_report_contains_kst_timestamp): report 의 `**Report generated:**` 라인이 `+09:00` 포함
    - Test G (test_failures_append_is_hook_safe): FAILURES.md 기존 내용 보존 (strict prefix) 후 새 엔트리 append — read_text() 전후 byte-level 비교
    - Test H (test_cli_since_until_override): `--since=2026-05-01 --until=2026-05-31` 커스텀 기간 accept + git log 인수에 그대로 전달 (monkeypatched subprocess)
  </behavior>
  <action>
    1. `scripts/audit/skill_patch_counter.py` 작성 (≥100 lines, stdlib only):
       ```python
       """D-2 Lock SKILL patch counter — FAIL-04 / SC#1.

       Scans git log across 4 forbidden paths during D-2 Lock period.
       Outputs monthly markdown report to reports/ and appends to FAILURES.md on violations.
       """
       from __future__ import annotations
       import argparse
       import json
       import re
       import subprocess
       import sys
       from datetime import datetime
       from pathlib import Path
       from zoneinfo import ZoneInfo

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")
       D2_LOCK_START = "2026-04-20"
       D2_LOCK_END = "2026-06-20"

       FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
           re.compile(r"^\.claude/agents/.+/SKILL\.md$"),
           re.compile(r"^\.claude/skills/.+/SKILL\.md$"),
           re.compile(r"^\.claude/hooks/[^/]+\.py$"),
           re.compile(r"^CLAUDE\.md$"),
       ]

       def scan_violations(repo_root: Path, since: str, until: str) -> list[dict]:
           """Return list of {hash, date, subject, violating_file} for each forbidden-path commit."""
           result = subprocess.run(
               ["git", "log",
                f"--since={since}",
                f"--until={until}",
                "--name-only",
                "--pretty=format:---COMMIT---%n%H|%aI|%s"],
               cwd=repo_root, capture_output=True, text=True, encoding="utf-8", check=True,
           )
           violations: list[dict] = []
           current: dict | None = None
           for line in result.stdout.splitlines():
               if line == "---COMMIT---":
                   current = {"hash": None, "date": None, "subject": None}
                   continue
               if current is None:
                   continue
               if current["hash"] is None and "|" in line:
                   h, d, s = line.split("|", 2)
                   current.update(hash=h, date=d, subject=s)
                   continue
               if line.strip():
                   for rx in FORBIDDEN_PATTERNS:
                       if rx.match(line.strip()):
                           violations.append({**current, "violating_file": line.strip()})
                           break
           return violations

       def write_report(violations: list[dict], output: Path, now: datetime, since: str, until: str) -> None:
           month = now.strftime("%Y-%m")
           badge = "✅" if not violations else "🚨"
           lines = [
               f"# D-2 Lock Skill Patch Counter — {month}",
               "",
               f"**Lock period:** {since} ~ {until}",
               f"**Report generated:** {now.isoformat()}",
               f"**Violation count:** {len(violations)} {badge} (목표: 0)",
               "",
               "## Violations",
           ]
           if violations:
               lines.append("| Hash | Date | File | Subject |")
               lines.append("|------|------|------|---------|")
               for v in violations:
                   lines.append(f"| {v['hash'][:7]} | {v['date']} | `{v['violating_file']}` | {v['subject']} |")
           else:
               lines.append("*없음.*")
           lines.extend([
               "",
               "## Scan coverage",
               f"- Lock window scanned: {since} → {until}",
               f"- Forbidden paths checked: {len(FORBIDDEN_PATTERNS)}",
           ])
           output.parent.mkdir(parents=True, exist_ok=True)
           output.write_text("\n".join(lines) + "\n", encoding="utf-8")

       def append_failures(violations: list[dict], repo_root: Path, now: datetime) -> None:
           """Append F-D2-XX entry to FAILURES.md via direct file I/O (bypasses Claude Write hook).

           Hook check_failures_append_only() only inspects Write/Edit tool calls from Claude;
           subprocess-style direct open('a') does NOT trigger it. Safe by design per D-11 RESEARCH Pitfall 3.
           """
           failures = repo_root / "FAILURES.md"
           if not failures.exists():
               return
           # derive next F-D2-NN id by scanning existing text
           existing = failures.read_text(encoding="utf-8")
           ids = re.findall(r"### F-D2-(\d{2})", existing)
           next_id = max((int(i) for i in ids), default=0) + 1
           body = [
               "",
               "",
               f"## F-D2-{next_id:02d} — D-2 Lock 위반 감지 ({now.date().isoformat()}, skill_patch_counter)",
               "",
               "**증상**: D-2 Lock 기간 중 금지 경로 commit 발생.",
               "",
               f"**위반 commit 수**: {len(violations)}",
               "",
               "**상세**:",
           ]
           for v in violations:
               body.append(f"- `{v['hash'][:7]}` {v['date']} — `{v['violating_file']}` ({v['subject']})")
           body.extend([
               "",
               "**조치**: 즉시 SKILL_HISTORY/*/v*.md.bak 에서 직전 버전 복원 → git revert → 본 엔트리 해결 commit 에서 reference.",
               "",
               "**Lock 재평가**: Exit 조건 재검증 (2개월 경과 + FAILURES ≥ 10 + taste gate 2회) 전까지 patch 금지 유지.",
           ])
           with failures.open("a", encoding="utf-8") as f:
               f.write("\n".join(body) + "\n")

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="D-2 Lock SKILL patch counter — FAIL-04")
           parser.add_argument("--since", default=D2_LOCK_START)
           parser.add_argument("--until", default=D2_LOCK_END)
           parser.add_argument("--repo", default=".", type=Path)
           parser.add_argument("--dry-run", action="store_true")
           parser.add_argument("--output", default=None, type=Path)
           args = parser.parse_args(argv)

           repo_root = args.repo.resolve()
           now = datetime.now(KST)
           violations = scan_violations(repo_root, args.since, args.until)

           if args.dry_run:
               print(json.dumps({
                   "violation_count": len(violations),
                   "since": args.since,
                   "until": args.until,
                   "violations": violations,
               }, ensure_ascii=False, indent=2))
               return 0 if not violations else 1

           output = args.output or (repo_root / "reports" / f"skill_patch_count_{now:%Y-%m}.md")
           write_report(violations, output, now, args.since, args.until)
           if violations:
               append_failures(violations, repo_root, now)
               return 1
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    2. `tests/phase10/test_skill_patch_counter.py` 확장 (Task 1 의 fixture-only 3 tests + 8 신규 Test A-H):
       - 각 test 에서 `tmp_git_repo` fixture 사용, `make_commit()` 로 시나리오 구축
       - `main(["--repo", str(tmp_git_repo), "--since", "2026-04-20", "--until", "2026-06-20"])` 호출
       - report 파일 존재/부재 + 내용 assertion
       - FAILURES.md 에 synthetic FAILURES.md 를 repo 에 미리 생성 후 append 검증 (test F-D2-01 엔트리 존재)
       - `--dry-run` 시 파일 미생성 + stdout JSON parse → `violation_count` key 존재
       - monkeypatch `datetime.now(KST)` 사용 (conftest freeze_kst_now fixture 재사용)
    3. 실행: `pytest tests/phase10/test_skill_patch_counter.py -xvs` — 8 tests + 3 fixture tests = 11 GREEN
    4. 수동 실증: `python -m scripts.audit.skill_patch_counter --dry-run --since=2026-04-20 --until=2026-06-20` — 현재 repo 에서 exit 0 + `violation_count: 0` JSON 출력 확인 (시작 시점 위반 0건 기대)
  </action>
  <acceptance_criteria>
    - `pytest tests/phase10/test_skill_patch_counter.py -q` 모든 tests GREEN (11+ tests)
    - `python -m scripts.audit.skill_patch_counter --dry-run` exit 0 + stdout 에 `"violation_count": 0` 포함
    - `python -m scripts.audit.skill_patch_counter --help` usage 출력 (argparse 정상)
    - `grep -c "FORBIDDEN_PATTERNS" scripts/audit/skill_patch_counter.py` ≥ 2 (정의 + 사용)
    - `grep -c "D2_LOCK_START = \"2026-04-20\"" scripts/audit/skill_patch_counter.py` == 1
    - `grep -c "D2_LOCK_END = \"2026-06-20\"" scripts/audit/skill_patch_counter.py` == 1
    - `grep -c "sys.stdout.reconfigure" scripts/audit/skill_patch_counter.py` ≥ 1 (Windows cp949 가드)
    - `grep -c "^\\s*#.*hook\\|Hook bypass\\|append-only" scripts/audit/skill_patch_counter.py` ≥ 1 (D-11 규약 문서화)
    - `wc -l scripts/audit/skill_patch_counter.py` ≥ 100 lines
    - Phase 4/5/6/7/8/9 regression: `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 tests/phase09 -q --tb=no` GREEN (기존 986+ tests 보존)
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_skill_patch_counter.py -q && python -m scripts.audit.skill_patch_counter --dry-run</automated>
  </verify>
  <done>skill_patch_counter.py CLI 완비, 4 금지 경로 regex 검증 + --dry-run + FAILURES append 모두 작동, 11+ tests GREEN, Phase 4-9 regression 보존</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_skill_patch_counter.py -v` — Task 1 fixture tests (3) + Task 2 핵심 tests (8) = 11+ PASS
- `python -m scripts.audit.skill_patch_counter --dry-run --since=2026-04-20 --until=2026-06-20` exit 0 (현재 시점 위반 0)
- `ls reports/` 에 `.gitkeep` 존재 (월간 리포트 출력처 확보)
- `grep -c "2026-04-20\|2026-06-20" scripts/audit/skill_patch_counter.py` ≥ 2 (Lock 기간 하드코드)
- Phase 4-9 기존 regression 보존: `pytest tests/ -q --tb=no` (새로 추가된 phase10 외 모든 기존 통과 유지)
- D-2 Lock 파일 수정 금지 준수: `git diff --name-only HEAD^ HEAD` 가 `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md` 를 포함하지 **않음**
</verification>

<success_criteria>
1. `scripts/audit/skill_patch_counter.py` exists, 100+ lines, stdlib-only, 4 FORBIDDEN_PATTERNS 정확히 정의
2. `tests/phase10/conftest.py` exists with `tmp_git_repo` + `make_commit` + `freeze_kst_now` fixtures
3. `tests/phase10/test_skill_patch_counter.py` 11+ tests GREEN (fixture-only 3 + core 8)
4. CLI `--dry-run` exit 0 + JSON output with `violation_count` key
5. CLI `violations > 0` 시 `reports/skill_patch_count_YYYY-MM.md` 생성 + FAILURES.md append (direct file I/O, hook bypass)
6. Phase 4-9 regression 전체 보존 (`pytest tests/phase0[4-9]/ -q` GREEN)
7. D-2 Lock 금지 경로 파일 이 PLAN 의 `files_modified` 에 포함되지 않음 (위반 시 plan 무효)
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-01-SUMMARY.md` with:
- 2 commit hashes (Task 1 scaffold + Task 2 CLI+tests)
- Test count (11+ Phase 10 tests + regression pass count)
- Output artifacts: scripts/audit/skill_patch_counter.py, reports/.gitkeep
- Next: Plan 2 (drift_scan + phase lock) Wave 1 parallel execution
- Deviations from plan (Rule 1/2/3 per GSD protocol)
</output>
