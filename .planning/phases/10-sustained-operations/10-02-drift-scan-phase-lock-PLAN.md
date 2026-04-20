---
phase: 10-sustained-operations
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/audit/drift_scan.py
  - tests/phase10/test_drift_scan.py
  - tests/phase10/test_phase_lock.py
  - .claude/deprecated_patterns.json
  - .planning/STATE.md
autonomous: true
requirements: [AUDIT-03, AUDIT-04]
must_haves:
  truths:
    - "scripts/audit/drift_scan.py 가 harness 공용 drift_scan.py 의 4 함수 (load_patterns, scan_studio, write_conflict_map, append_history) 를 sys.path import 로 호출한다 (harness 경로 부재 시 local-only fallback)"
    - ".claude/deprecated_patterns.json 의 8 기존 entries 각각에 `grade` (A/B/C) + `name` 필드가 추가되며 Phase 5/6 regression 은 보존된다"
    - "A급 drift > 0 감지 시 .planning/STATE.md frontmatter 에 phase_lock/block_reason/block_since 3 필드가 삽입되고 gh issue 가 auto-create 된다 (mocked)"
    - "A급 drift == 0 시 exit 0 + CONFLICT_MAP.md 갱신만 (STATE.md 건드리지 않음)"
    - "CLI 는 `--harness-path` / `--skip-harness-import` flag 를 지원하여 harness/ 부재 시 graceful degradation (WARNING #4)"
  artifacts:
    - path: scripts/audit/drift_scan.py
      provides: "A-grade drift scanner wrapping harness drift_scan.py via sys.path — AUDIT-03/04"
      min_lines: 150
    - path: .claude/deprecated_patterns.json
      provides: "8 entries with grade/name fields (A: skip_gates/todo_next/t2v/selenium, B: segments_deprecated/try_pass_silent/failures_removal, C: skill_md_mention)"
      contains: "grade"
    - path: tests/phase10/test_drift_scan.py
      provides: "AUDIT-03 unit: load/scan/write/append harness functions mocked + import success + harness_path fallback"
      min_lines: 90
    - path: tests/phase10/test_phase_lock.py
      provides: "AUDIT-04 unit: STATE.md frontmatter write + gh issue subprocess mock"
      min_lines: 80
    - path: .planning/STATE.md
      provides: "frontmatter extension (phase_lock optional field)"
      contains: "gsd_state_version"
  key_links:
    - from: scripts/audit/drift_scan.py
      to: harness/scripts/drift_scan.py
      via: "sys.path.insert(0, str(harness_scripts)) — resolved via --harness-path flag or default"
      pattern: "sys\\.path\\.insert.*harness.*scripts"
    - from: scripts/audit/drift_scan.py
      to: .planning/STATE.md
      via: "set_phase_lock(reason, findings) — frontmatter 내 phase_lock/block_reason/block_since 삽입"
      pattern: "phase_lock.*:\\s*true"
    - from: scripts/audit/drift_scan.py
      to: gh CLI subprocess
      via: "subprocess.run(['gh','issue','create','--title','--body-file','-','--label','drift,critical,phase-10,auto'])"
      pattern: "gh.*issue.*create"
    - from: .claude/deprecated_patterns.json
      to: harness drift_scan.py
      via: "grade 필드 — 없으면 default 'C' (harness line 90-94). A급만 차단 트리거."
      pattern: "\"grade\"\\s*:\\s*\"A\""
---

<objective>
주 1회 A급 drift 자동 감지 + Phase 차단 신호를 구축한다. harness 공용 `scripts/drift_scan.py` 를 sys.path import 로 재사용하여 복사 금지 원칙을 유지하고 (harness/ 경로 부재 시 local-only fallback 포함 — BLOCKER #2/WARNING #4 대응), `deprecated_patterns.json` 8 기존 entries 에 grade/name 필드를 추가하며 (A급: skip_gates/todo_next/t2v/selenium), A급 drift 발견 시 `.planning/STATE.md` 의 frontmatter 에 phase_lock 플래그를 세팅 + GitHub issue 를 non-interactive 로 자동 생성한다. GSD YAML parser 호환성은 Wave 0 smoke 에서 1회 실증한다. gh label (drift/phase-10/auto) 는 Wave 0 manual dispatch 와 Plan 4 GH Actions step 에서 이중 방어선으로 사전 생성한다 (BLOCKER #2).

Purpose: SKILL patch 금지는 소극적 규율, drift_scan 은 적극적 안전망. 이 둘이 함께 작동해야 D-2 저수지가 실증된다.
Output: `scripts/audit/drift_scan.py` + grade-annotated `deprecated_patterns.json` + STATE.md frontmatter 확장 + mocked gh issue + `--harness-path` / `--skip-harness-import` CLI flag.
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
@.claude/deprecated_patterns.json
@CLAUDE.md

<interfaces>
<!-- harness public API (DO NOT re-invent) -->

From `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` (soft-verified from RESEARCH §Plan 2 Open Q1):
```python
def load_patterns(studio_root: Path) -> list[dict]:
    """Load .claude/deprecated_patterns.json — returns list of {regex, reason, grade?, name?}.
    Default grade 'C' if missing."""

def scan_studio(studio_root: Path, pattern_defs: list[dict]) -> dict:
    """Returns: {pattern_name: [{"file": str, "line": int, "match": str}, ...]}"""

def write_conflict_map(studio_root: Path, findings: dict, pattern_defs: list[dict], output: Path) -> None:
    """Writes .planning/codebase/CONFLICT_MAP.md"""

def append_history(studio_root: Path, findings: dict) -> None:
    """Appends to .planning/codebase/CONFLICT_HISTORY.jsonl"""
```

From RESEARCH.md §Plan 2 Open Q2 — 8 entries with grade (A=4, B=3, C=1):
```json
{
  "patterns": [
    {"regex": "skip_gates\\s*=", "reason": "ORCH-08", "grade": "A", "name": "skip_gates_usage"},
    {"regex": "TODO\\s*\\(\\s*next-session", "reason": "ORCH-09", "grade": "A", "name": "todo_next_session"},
    {"regex": "(?i)(text_to_video|text2video|(?<![a-z])t2v(?![a-z]))", "reason": "VIDEO-01", "grade": "A", "name": "t2v_code_path"},
    {"regex": "segments\\s*\\[\\s*\\]", "reason": "segments[] deprecated", "grade": "B", "name": "segments_deprecated"},
    {"regex": "\\bimport\\s+selenium\\b|\\bfrom\\s+selenium\\s+import", "reason": "AF-8", "grade": "A", "name": "selenium_import"},
    {"regex": "try\\s*:[^\\n]*\\n\\s+pass\\s*$", "reason": "Project Rule 3", "grade": "B", "name": "try_pass_silent"},
    {"regex": "(?i)\\[REMOVED\\]|\\[DELETED\\]|delete this entry", "reason": "FAIL-01 / D-11", "grade": "B", "name": "failures_removal_marker"},
    {"regex": "SKILL\\.md", "reason": "FAIL-03 / D-12", "grade": "C", "name": "skill_md_mention"}
  ]
}
```

From RESEARCH.md §Plan 2 Open Q3 — STATE.md frontmatter 확장:
```yaml
---
gsd_state_version: 1.0
milestone: v1.0.1
milestone_name: milestone
status: executing
last_updated: "2026-04-20T13:00:00.000Z"
phase_lock: true                # 신규 (optional field)
block_reason: "A급 drift 3건 — 2026-04-27 drift_scan"
block_since: "2026-04-27T09:00:00+09:00"
progress:
  total_phases: 11
  completed_phases: 9
  total_plans: 83
  completed_plans: 83
  percent: 100
---
```

From RESEARCH.md §Plan 2 Open Q4 — gh issue create non-interactive:
```bash
gh issue create \
  --title "[AUDIT-04] A급 drift ${count}건 — Phase 차단" \
  --body-file - \
  --label "drift,critical,phase-10,auto" \
  << EOF
...
EOF
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Wave 0 smokes — deprecated_patterns.json grade 확장 + STATE.md frontmatter 확장 + gh label 사전 생성 + regression 무결성 확인</name>
  <files>
    .claude/deprecated_patterns.json,
    .planning/STATE.md,
    tests/phase10/test_drift_scan.py
  </files>
  <read_first>
    - `.claude/deprecated_patterns.json` (현재 8 entries — regex/reason 만 있음)
    - `.planning/STATE.md` frontmatter (line 1-13)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 2 Open Q2 + Pitfall 7 (STATE.md GSD 호환 smoke)
    - `tests/phase05/` 및 `tests/phase06/` 중 `deprecated_patterns.json` 을 참조하는 테스트 (RESEARCH §Risk Register "grade 필드 추가 시 regression" mitigation — `grep -r "deprecated_patterns" tests/`)
  </read_first>
  <behavior>
    - Test W0-a (test_deprecated_patterns_has_grade_and_name): 8 entries 모두 `grade` ∈ {A,B,C} + `name` string 보유
    - Test W0-b (test_deprecated_patterns_a_grade_exact_four): A 등급 entry == 정확히 4 (skip_gates/todo_next/t2v/selenium)
    - Test W0-c (test_state_md_frontmatter_loads_yaml_clean): `.planning/STATE.md` 의 `---` 블록을 stdlib (line-split) 으로 파싱 — phase_lock 필드 부재 시 default 해석 허용 (optional)
    - Test W0-d (test_phase5_6_regression_preserved): `pytest tests/phase05 tests/phase06 -q` 가 Phase 10 Plan 2 작업 후에도 GREEN (별도 subprocess 로 실행, assertion result.returncode == 0)
  </behavior>
  <action>
    1. `grep -rn "deprecated_patterns" tests/` 실행 → 참조 파일 enumerate. 테스트 코드 중 `len(data["patterns"]) == 8` 또는 특정 인덱스 기반 접근이 있는지 확인. 있으면 grade 추가로 regression 위험, 없으면 append-only.
    2. `.claude/deprecated_patterns.json` 재작성 — RESEARCH §Plan 2 Open Q2 의 정확한 JSON (8 entries, grade/name 필드 각각 추가). 기존 regex/reason 문자열은 **byte-identical 유지** (Phase 5/6 regex 매칭 regression 방지).
    3. `.planning/STATE.md` frontmatter 에 phase_lock 관련 필드는 **이 시점에 삽입하지 않음**. 단, `phase_lock: false` default 만 1회 추가 (GSD parser 영향 smoke 검증 목적). 전체 frontmatter 에 아래 1-line 만 `last_updated` 직후 추가:
       ```yaml
       phase_lock: false
       ```
       (Task 2 의 drift_scan.py 가 True 로 toggle 할 때 이 key 를 수정하도록 idempotent — missing 시 insert, exists 시 replace 로 구현)
    4. `tests/phase10/test_drift_scan.py` 의 Wave 0 test 4개 (W0-a ~ W0-d) 작성. Wave 0 smoke 먼저 GREEN 확인:
       ```python
       def test_deprecated_patterns_has_grade_and_name():
           data = json.loads(Path(".claude/deprecated_patterns.json").read_text(encoding="utf-8"))
           for entry in data["patterns"]:
               assert entry.get("grade") in {"A", "B", "C"}, entry
               assert isinstance(entry.get("name"), str) and entry["name"], entry

       def test_deprecated_patterns_a_grade_exact_four():
           data = json.loads(Path(".claude/deprecated_patterns.json").read_text(encoding="utf-8"))
           a_names = {e["name"] for e in data["patterns"] if e.get("grade") == "A"}
           assert a_names == {"skip_gates_usage", "todo_next_session", "t2v_code_path", "selenium_import"}

       def test_state_md_frontmatter_phase_lock_false_default():
           text = Path(".planning/STATE.md").read_text(encoding="utf-8")
           # frontmatter 은 첫 `---` 블록
           m = re.search(r"^---\n(.*?)\n---\n", text, re.DOTALL | re.MULTILINE)
           assert m, "STATE.md frontmatter missing"
           fm = m.group(1)
           assert "phase_lock: false" in fm

       def test_phase5_6_regression_preserved():
           result = subprocess.run(
               [sys.executable, "-m", "pytest", "tests/phase05", "tests/phase06",
                "-q", "--tb=no", "-p", "no:cacheprovider"],
               capture_output=True, text=True, cwd=Path.cwd(),
           )
           assert result.returncode == 0, f"regression:\n{result.stdout[-2000:]}\n{result.stderr[-500:]}"
       ```
    5. **대표님 manual step (Wave 0 smoke 일부) — gh label 사전 생성 (BLOCKER #2, redundant safety #1/2)**:
       shorts_studio 저장소에 대해 아래 3 label 을 사전 생성하여 `gh issue create --label "drift,critical,phase-10,auto"` 호출이 HTTP 422 로 실패하지 않도록 한다:
       ```
       gh label create drift --color "d73a4a" --description "drift detection (auto)" || true
       gh label create phase-10 --color "0075ca" --description "Phase 10 sustained ops" || true
       gh label create auto --color "ededed" --description "automated issue" || true
       # critical 은 GitHub default label 이므로 생성 불필요
       ```
       `|| true` 로 이미 존재해도 무시. Plan 4 GH Actions `drift-scan-weekly.yml` 의 `Ensure labels exist` step 이 redundant safety #2 로 동일 명령을 실행하므로, 로컬 manual 을 건너뛰어도 첫 weekly run 에서 label 이 생성된다 (단, 수동 `python -m scripts.audit.drift_scan` 실행 시에는 이 단계 완료 필수).
    6. Wave 0 smoke 실행: `pytest tests/phase10/test_drift_scan.py::test_deprecated_patterns_has_grade_and_name tests/phase10/test_drift_scan.py::test_deprecated_patterns_a_grade_exact_four tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default -v` → GREEN
    7. 전체 regression smoke: `pytest tests/phase10/test_drift_scan.py::test_phase5_6_regression_preserved -v` → GREEN (subprocess 가 phase05/06 GREEN 확인)
  </action>
  <acceptance_criteria>
    - `jq '.patterns | length' .claude/deprecated_patterns.json` == 8
    - `jq '[.patterns[] | select(.grade == "A")] | length' .claude/deprecated_patterns.json` == 4 (jq 없으면 python json + list comp 로 대체)
    - `python -c "import json; d=json.load(open('.claude/deprecated_patterns.json',encoding='utf-8')); assert all('grade' in e and 'name' in e for e in d['patterns']); print('OK')"` prints OK
    - `grep "phase_lock: false" .planning/STATE.md` == 1 match
    - `pytest tests/phase10/test_drift_scan.py -k "W0 or deprecated_patterns or frontmatter or regression" -v` 4 tests PASS
    - `pytest tests/phase05 tests/phase06 -q --tb=no` 전체 GREEN (Phase 5: 329/329, Phase 6: 236/236)
    - 기존 8 entries 의 `regex` 및 `reason` 값이 byte-identical 유지 (새 필드만 추가, 기존 필드 미수정):
      `python -c "import json; d=json.load(open('.claude/deprecated_patterns.json',encoding='utf-8')); assert [e['regex'] for e in d['patterns']] == ['skip_gates\\\\s*=', 'TODO\\\\s*\\\\(\\\\s*next-session', '(?i)(text_to_video|text2video|(?<![a-z])t2v(?![a-z]))', 'segments\\\\s*\\\\[\\\\s*\\\\]', '\\\\bimport\\\\s+selenium\\\\b|\\\\bfrom\\\\s+selenium\\\\s+import', 'try\\\\s*:[^\\\\n]*\\\\n\\\\s+pass\\\\s*\\$', '(?i)\\\\[REMOVED\\\\]|\\\\[DELETED\\\\]|delete this entry', 'SKILL\\\\.md']; print('OK')"`
    - BLOCKER #2 Wave 0 manual dispatch 문서화 확인 (action step 5 에 `gh label create drift` / `gh label create phase-10` / `gh label create auto` 3 명령 존재)
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_drift_scan.py -q --tb=short && pytest tests/phase05 tests/phase06 -q --tb=no</automated>
  </verify>
  <done>8 entries grade/name 필드 확장 완료, STATE.md phase_lock: false 삽입, Phase 5/6 regression GREEN 유지, 4 Wave 0 smoke tests GREEN, gh label 3종 (drift/phase-10/auto) 대표님 manual dispatch 문서화 (BLOCKER #2 redundant safety #1)</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: drift_scan.py wrapper 구현 + harness import (graceful) + set_phase_lock + gh issue auto-create + --harness-path/--skip-harness-import CLI</name>
  <files>
    scripts/audit/drift_scan.py,
    tests/phase10/test_drift_scan.py,
    tests/phase10/test_phase_lock.py
  </files>
  <read_first>
    - `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` (4 public 함수 시그니처 확인 — 읽기 전용)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 2 Open Q1-Q4 + §Code Examples `Plan 2 drift_scan wrapper (GREEN pseudocode)` (line 985-1040)
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Pitfall 7 (STATE.md GSD 혼란 방지)
    - `tests/phase10/conftest.py` (Plan 1 Task 1 에서 생성 — `tmp_git_repo`, `freeze_kst_now`)
    - `scripts/audit/skill_patch_counter.py` (Plan 1 Task 2 — CLI argparse 패턴 일관성)
  </read_first>
  <behavior>
    - Test 1 (test_drift_scan_imports_harness): `from drift_scan import load_patterns, scan_studio, write_conflict_map, append_history` 성공 (sys.path 올바름) when harness/ 경로 존재
    - Test 2 (test_main_exit_0_when_no_a_grade): `scan_studio` 를 mock 하여 빈 dict 반환 → main() exit 0 + CONFLICT_MAP.md 생성 + STATE.md `phase_lock: false` 유지
    - Test 3 (test_main_exit_1_when_a_grade_found): `scan_studio` mock → `skip_gates_usage: [{file, line, match}]` 반환 → main() exit 1 + STATE.md 에 `phase_lock: true` + `block_reason` 세팅 + gh subprocess mock called
    - Test 4 (test_set_phase_lock_idempotent): STATE.md 에 이미 `phase_lock: true` 존재 → 재실행 시 중복 key 없이 replace
    - Test 5 (test_set_phase_lock_removes_on_clear): 별도 `clear_phase_lock()` helper — `phase_lock: false` 로 toggle + `block_reason`/`block_since` 제거
    - Test 6 (test_gh_issue_body_contains_findings_details): gh subprocess mock 이 받는 body stdin 에 findings summary 표시, label 에 `drift,critical,phase-10,auto` 포함
    - Test 7 (test_a_grade_count_uses_grade_field): findings dict 에 B/C 급 pattern 만 있어도 main() exit 0 (A 급만 차단)
    - Test 8 (test_cli_dry_run_no_state_md_mutation): `--dry-run` 시 STATE.md 건드리지 않고 stdout JSON 만 출력
    - Test 9 (test_cli_harness_path_override): `--harness-path=/custom/harness/scripts` → sys.path 에 해당 경로 삽입 검증 (WARNING #4)
    - Test 10 (test_cli_skip_harness_import_local_only): `--skip-harness-import` flag → harness 미로드 + deprecated_patterns 만 scan (load_patterns/scan_studio 는 local re-implementation 또는 graceful skip) (WARNING #4)
    - Test 11 (test_harness_missing_path_falls_back_to_local_only): harness_path 지정됐지만 존재하지 않음 → stderr WARN + local-only scan (exit code 0 if no A-grade) (WARNING #4)
  </behavior>
  <action>
    1. `scripts/audit/drift_scan.py` 작성 (≥150 lines, RESEARCH §Code Example 확장). WARNING #4: harness 경로 부재 시 graceful degradation + CLI `--harness-path` / `--skip-harness-import` flag 추가:
       ```python
       """A-grade drift scanner wrapping harness drift_scan.py — AUDIT-03/04 / SC#4.

       A급 drift 발견 시 .planning/STATE.md 의 frontmatter 에 phase_lock: true 세팅 +
       gh issue 자동 생성. harness drift_scan.py 4 public 함수를 sys.path import 로 재사용
       (복사 금지 — harness 업데이트 시 auto-sync).

       Graceful degradation (WARNING #4):
         - harness_path 부재 → stderr WARN + local-only scan (deprecated_patterns.json 만)
         - --skip-harness-import → harness 로드 자체 skip, local scan 전용
         - GH Actions drift-scan-weekly.yml 에서 `--harness-path=../harness` 전달
         - CLAUDE.md "독립 git 저장소. 하네스 업데이트는 수동 pull" → submodule 아님
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
       STUDIO_ROOT = Path(__file__).resolve().parents[2]
       DEFAULT_HARNESS_SCRIPTS = STUDIO_ROOT.parent.parent / "harness" / "scripts"

       PHASE_LOCK_FIELDS = ("phase_lock", "block_reason", "block_since")

       # Harness imports are resolved lazily in main() — see _resolve_harness_imports()
       _HARNESS_LOADED = False

       def _resolve_harness_imports(harness_path: Path | None, skip: bool) -> dict | None:
           """Resolve harness drift_scan 4 functions. Returns dict of functions or None
           if skip=True or path missing (→ local-only fallback).

           WARNING #4: harness/ 는 shorts_studio 의 submodule 이 아님. GH Actions 은 별도
           checkout step 으로 마련하며, 로컬 실행에서는 ../../harness 가 default.
           """
           global _HARNESS_LOADED
           if skip:
               print("[INFO] --skip-harness-import: local-only drift scan (deprecated_patterns.json only)",
                     file=sys.stderr)
               return None
           resolved = harness_path or DEFAULT_HARNESS_SCRIPTS
           if not resolved.exists():
               print(f"[WARN] harness/ not found at {resolved} — falling back to local-only "
                     f"drift scan (deprecated_patterns.json only). "
                     f"Pass --harness-path or --skip-harness-import to silence.",
                     file=sys.stderr)
               return None
           if str(resolved) not in sys.path:
               sys.path.insert(0, str(resolved))
           try:
               from drift_scan import (  # type: ignore[import-untyped]
                   load_patterns, scan_studio, write_conflict_map, append_history,
               )
               _HARNESS_LOADED = True
               return {"load_patterns": load_patterns, "scan_studio": scan_studio,
                       "write_conflict_map": write_conflict_map, "append_history": append_history}
           except ImportError as exc:
               print(f"[WARN] harness drift_scan import failed: {exc} — local-only fallback",
                     file=sys.stderr)
               return None

       def _local_load_patterns(studio_root: Path) -> list[dict]:
           """Fallback — load .claude/deprecated_patterns.json directly (harness absent)."""
           p = studio_root / ".claude" / "deprecated_patterns.json"
           if not p.exists():
               return []
           data = json.loads(p.read_text(encoding="utf-8"))
           return data.get("patterns", [])

       def _local_scan_studio(studio_root: Path, pattern_defs: list[dict]) -> dict:
           """Fallback — minimal regex scan across studio files. harness 미포함 시 사용."""
           findings: dict = {}
           # Scan scripts/, wiki/, .planning/ 대상 (skip .git/, __pycache__/, node_modules/)
           for p in studio_root.rglob("*"):
               if not p.is_file():
                   continue
               rel = p.relative_to(studio_root)
               s = str(rel)
               if any(seg in s for seg in (".git", "__pycache__", "node_modules", ".venv")):
                   continue
               if p.suffix not in {".py", ".md", ".json", ".yml", ".yaml", ".ps1"}:
                   continue
               try:
                   text = p.read_text(encoding="utf-8", errors="replace")
               except (OSError, UnicodeDecodeError):
                   continue
               for pat in pattern_defs:
                   name = pat.get("name") or pat.get("reason") or "unnamed"
                   rx = re.compile(pat["regex"])
                   for i, line in enumerate(text.splitlines(), 1):
                       m = rx.search(line)
                       if m:
                           findings.setdefault(name, []).append(
                               {"file": str(rel).replace("\\", "/"), "line": i, "match": m.group(0)})
           return findings

       def _parse_frontmatter(text: str) -> tuple[str, str, str]:
           """Return (before_fm, fm_body, after_fm) — splits first --- block."""
           m = re.match(r"(^---\n)(.*?)(\n---\n)", text, re.DOTALL)
           if not m:
               raise ValueError("STATE.md has no YAML frontmatter")
           return m.group(1), m.group(2), m.group(3) + text[m.end():]

       def _set_key(fm_body: str, key: str, value: str) -> str:
           """Set or replace a single YAML key in frontmatter body (stdlib, no pyyaml)."""
           lines = fm_body.split("\n")
           pattern = re.compile(rf"^{re.escape(key)}\s*:")
           for i, line in enumerate(lines):
               if pattern.match(line):
                   lines[i] = f"{key}: {value}"
                   return "\n".join(lines)
           for i, line in enumerate(lines):
               if line.startswith("progress:"):
                   lines.insert(i, f"{key}: {value}")
                   return "\n".join(lines)
           lines.append(f"{key}: {value}")
           return "\n".join(lines)

       def _remove_key(fm_body: str, key: str) -> str:
           lines = fm_body.split("\n")
           pattern = re.compile(rf"^{re.escape(key)}\s*:")
           return "\n".join(l for l in lines if not pattern.match(l))

       def set_phase_lock(studio_root: Path, reason: str, now: datetime) -> None:
           state_md = studio_root / ".planning" / "STATE.md"
           text = state_md.read_text(encoding="utf-8")
           before, fm, after = _parse_frontmatter(text)
           fm = _set_key(fm, "phase_lock", "true")
           fm = _set_key(fm, "block_reason", json.dumps(reason, ensure_ascii=False))
           fm = _set_key(fm, "block_since", f'"{now.isoformat()}"')
           state_md.write_text(before + fm + after, encoding="utf-8")

       def clear_phase_lock(studio_root: Path) -> None:
           state_md = studio_root / ".planning" / "STATE.md"
           text = state_md.read_text(encoding="utf-8")
           before, fm, after = _parse_frontmatter(text)
           fm = _set_key(fm, "phase_lock", "false")
           fm = _remove_key(fm, "block_reason")
           fm = _remove_key(fm, "block_since")
           state_md.write_text(before + fm + after, encoding="utf-8")

       def create_github_issue(a_grade_details: dict, reason: str, now: datetime) -> None:
           title = f"[AUDIT-04] A급 drift {sum(a_grade_details.values())}건 — Phase 차단"
           body_lines = [
               "# A급 drift 감지",
               "",
               f"- Detector: `scripts/audit/drift_scan.py`",
               f"- Timestamp: {now.isoformat()}",
               f"- Reason: {reason}",
               "",
               "## A급 findings (pattern → count)",
           ]
           for name, count in sorted(a_grade_details.items()):
               body_lines.append(f"- `{name}`: {count}건")
           body_lines.extend([
               "",
               "## Phase lock 상태",
               "- `.planning/STATE.md` frontmatter 에 `phase_lock: true` 세팅됨",
               f"- `block_reason`: {reason}",
               "",
               "## 복구 경로",
               "1. A급 drift 코드 수정",
               "2. `python -m scripts.audit.drift_scan` 재실행 → A급 0 확인",
               "3. `python -m scripts.audit.drift_scan --clear-lock` 로 STATE.md phase_lock=false 복귀",
               "4. 본 issue close",
           ])
           body = "\n".join(body_lines)
           subprocess.run(
               ["gh", "issue", "create",
                "--title", title,
                "--body-file", "-",
                "--label", "drift,critical,phase-10,auto"],
               input=body, text=True, check=True, encoding="utf-8",
           )

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="A-grade drift scanner — AUDIT-03/04")
           parser.add_argument("--dry-run", action="store_true")
           parser.add_argument("--clear-lock", action="store_true",
                               help="Reset phase_lock to false (after drift resolved)")
           parser.add_argument("--studio-root", default=str(STUDIO_ROOT), type=Path)
           parser.add_argument("--skip-github-issue", action="store_true",
                               help="Skip gh issue auto-create (local dry-run)")
           parser.add_argument("--harness-path", type=Path, default=None,
                               help="Override harness/scripts path (default: ../../harness/scripts). "
                                    "WARNING #4: harness/ 부재 시 local-only fallback.")
           parser.add_argument("--skip-harness-import", action="store_true",
                               help="Skip harness import entirely — local-only scan "
                                    "(deprecated_patterns.json 만).")
           args = parser.parse_args(argv)

           studio_root = Path(args.studio_root).resolve()
           now = datetime.now(KST)

           if args.clear_lock:
               clear_phase_lock(studio_root)
               print(json.dumps({"phase_lock": False, "cleared_at": now.isoformat()}))
               return 0

           # Graceful harness import (WARNING #4)
           harness_funcs = _resolve_harness_imports(args.harness_path, args.skip_harness_import)

           if harness_funcs:
               pattern_defs = harness_funcs["load_patterns"](studio_root)
               findings = harness_funcs["scan_studio"](studio_root, pattern_defs)
           else:
               pattern_defs = _local_load_patterns(studio_root)
               findings = _local_scan_studio(studio_root, pattern_defs)

           output = studio_root / ".planning" / "codebase" / "CONFLICT_MAP.md"
           output.parent.mkdir(parents=True, exist_ok=True)
           if not args.dry_run and harness_funcs:
               harness_funcs["write_conflict_map"](studio_root, findings, pattern_defs, output)
               harness_funcs["append_history"](studio_root, findings)

           a_grade_details: dict[str, int] = {}
           for p in pattern_defs:
               if (p.get("grade") or "C").upper() == "A":
                   hits = findings.get(p.get("name") or "", [])
                   if hits:
                       a_grade_details[p.get("name") or "unnamed"] = len(hits)
           a_grade_count = sum(a_grade_details.values())

           summary = {
               "a_grade_count": a_grade_count,
               "a_grade_details": a_grade_details,
               "total_patterns_checked": len(pattern_defs),
               "scan_time": now.isoformat(),
               "dry_run": args.dry_run,
               "harness_loaded": _HARNESS_LOADED,
               "mode": "harness" if _HARNESS_LOADED else "local-only",
           }
           print(json.dumps(summary, ensure_ascii=False, indent=2))

           if a_grade_count > 0 and not args.dry_run:
               reason = f"A급 drift {a_grade_count}건 — {now.date().isoformat()} drift_scan"
               set_phase_lock(studio_root, reason, now)
               if not args.skip_github_issue:
                   try:
                       create_github_issue(a_grade_details, reason, now)
                   except subprocess.CalledProcessError as exc:
                       # gh auth 미설정 / label 미생성 등 — Project Rule 3 silent-fallback 금지.
                       # Plan 4 drift-scan-weekly.yml 의 `Ensure labels exist` step 이 label 422 를
                       # 1차 방어하고, Wave 0 manual dispatch 가 2차 방어. 그래도 실패하면 GH Actions
                       # 가 실패 email 을 발송하므로 여기서 raise 해야 scheduler 가 인지.
                       print(f"[WARN] gh issue create failed rc={exc.returncode}: {exc.stderr}",
                             file=sys.stderr)
                       raise
               return 1
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    2. `tests/phase10/test_drift_scan.py` 확장 (Wave 0 4 tests + main 시나리오 7 tests = 11+ total):
       - Test 1-2: Task 1 의 Wave 0 이미 GREEN
       - Test 3 (test_drift_scan_imports_harness): `from scripts.audit.drift_scan import main, set_phase_lock, create_github_issue` 기본 import 성공 (lazy harness resolve)
       - Test 4 (test_main_exit_0_when_no_a_grade): monkeypatch `_resolve_harness_imports` → Mock harness funcs 주입 → scan_studio 빈 dict → main() returncode 0
       - Test 7 (test_a_grade_count_uses_grade_field): mock harness → `{"segments_deprecated": [{"file":"x.py","line":1,"match":"segments[]"}]}` → exit 0 (B급, A가 아님)
       - Test 8 (test_cli_dry_run_no_state_md_mutation): STATE.md sha256 before/after 동일
       - Test 9 (test_cli_harness_path_override): `--harness-path=/tmp/nonexistent` → stderr WARN "harness/ not found" + local-only mode + summary `"mode": "local-only"` (WARNING #4)
       - Test 10 (test_cli_skip_harness_import_local_only): `--skip-harness-import` → stderr INFO "local-only drift scan" + harness_loaded False
       - Test 11 (test_harness_missing_path_falls_back_to_local_only): `DEFAULT_HARNESS_SCRIPTS` 를 monkeypatch 로 nonexistent → WARN + _local_scan_studio 호출 path 커버
    3. `tests/phase10/test_phase_lock.py` 생성 (AUDIT-04 분리, 80+ lines):
       - Test (test_set_phase_lock_inserts_three_fields): 빈 STATE.md sample → `set_phase_lock()` 호출 → frontmatter 에 3 fields (phase_lock/block_reason/block_since) 존재
       - Test (test_set_phase_lock_replaces_existing): `phase_lock: false` → `set_phase_lock()` → `phase_lock: true` (중복 key 없음, line count 유지)
       - Test (test_clear_phase_lock_removes_block_fields): set 후 clear → `phase_lock: false` + `block_reason`/`block_since` 라인 없음
       - Test (test_create_github_issue_subprocess_args): monkeypatch `subprocess.run` → 받은 args 검증 (`gh`, `issue`, `create`, `--title`, `--body-file`, `-`, `--label`, `drift,critical,phase-10,auto`)
       - Test (test_create_github_issue_body_includes_counts): subprocess mock `.input` 에 A급 pattern 이름 + 개수 포함
       - Test (test_main_exit_1_triggers_phase_lock_and_gh_issue): end-to-end — monkeypatch `_resolve_harness_imports` + subprocess.run → main() exit 1 + STATE.md phase_lock true + subprocess called once with `gh` argv
    4. 실행: `pytest tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py -xvs` — 모두 GREEN
    5. 실증 검증 (no-op 실행 — 현재 repo 에 실제 A급 drift 없음 가정):
       `python -m scripts.audit.drift_scan --dry-run --skip-github-issue --skip-harness-import` — exit 0 + JSON `{"a_grade_count": 0, "mode": "local-only", ...}` 출력.
       만약 a_grade_count > 0 이 출력되면 즉시 Plan 2 가 기존 drift 를 발견한 것 — commit 전 반드시 대표님께 보고 후 drift 먼저 해결.
  </action>
  <acceptance_criteria>
    - `python -c "import sys; sys.path.insert(0,'scripts/audit'); import drift_scan; assert hasattr(drift_scan,'main')"` exits 0
    - `pytest tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py -q` 17+ tests GREEN (Wave 0 4 + main 7 + phase_lock 6)
    - `python -m scripts.audit.drift_scan --dry-run --skip-github-issue --skip-harness-import` exit 0 + stdout JSON 에 `"a_grade_count"` key + `"mode": "local-only"` (WARNING #4 fallback 실증)
    - `grep -c "sys.path.insert" scripts/audit/drift_scan.py` ≥ 1
    - `grep -c "from drift_scan import" scripts/audit/drift_scan.py` == 1
    - `grep -c "load_patterns\\|scan_studio\\|write_conflict_map\\|append_history" scripts/audit/drift_scan.py` ≥ 4
    - `grep -c "gh.*issue.*create\\|'gh', 'issue', 'create'" scripts/audit/drift_scan.py` ≥ 1
    - `grep -c "drift,critical,phase-10,auto" scripts/audit/drift_scan.py` ≥ 1
    - `grep -c "\\-\\-harness-path\\|\\-\\-skip-harness-import" scripts/audit/drift_scan.py` >= 2 (WARNING #4 CLI flag)
    - `grep -c "_local_scan_studio\\|_local_load_patterns\\|local-only" scripts/audit/drift_scan.py` >= 3 (graceful fallback path)
    - `wc -l scripts/audit/drift_scan.py` ≥ 150 lines
    - Phase 5/6 regression 보존: `pytest tests/phase05 tests/phase06 -q --tb=no` exit 0
    - STATE.md frontmatter YAML 파싱 무결성: `python -c "import re; t=open('.planning/STATE.md',encoding='utf-8').read(); m=re.match(r'^---\\n(.*?)\\n---\\n',t,re.DOTALL); assert m, 'frontmatter missing'; assert 'gsd_state_version' in m.group(1); print('OK')"` prints OK
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py -q && python -m scripts.audit.drift_scan --dry-run --skip-github-issue --skip-harness-import</automated>
  </verify>
  <done>drift_scan.py wrapper 완비 (150+ lines), harness 4 함수 sys.path import + graceful fallback (WARNING #4), --harness-path/--skip-harness-import CLI flag 지원, set/clear_phase_lock idempotent, gh issue auto-create (mocked in tests), AUDIT-03/04 두 requirement 의 코드/테스트 레벨 실증 완료</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_drift_scan.py tests/phase10/test_phase_lock.py -v` 17+ tests PASS
- `python -m scripts.audit.drift_scan --dry-run --skip-github-issue --skip-harness-import` exit 0 (local-only mode, A급 drift 0 기대)
- `python -m scripts.audit.drift_scan --clear-lock` exit 0 + STATE.md `phase_lock: false` 확인
- Phase 5 + Phase 6 regression: 전체 329 + 236 tests PASS 보존
- `.claude/deprecated_patterns.json` 8 entries grade/name 필드 완비 (A:4, B:3, C:1)
- `.planning/STATE.md` frontmatter 에 `phase_lock: false` 존재 (Plan 10 Wave 0 smoke)
- Wave 0 manual dispatch (BLOCKER #2 redundant safety #1): 대표님이 `gh label create drift/phase-10/auto` 3 명령 1회 실행
- CLI graceful harness path (WARNING #4): `--harness-path` / `--skip-harness-import` 두 flag 작동
</verification>

<success_criteria>
1. `scripts/audit/drift_scan.py` 150+ lines, harness `drift_scan.py` 4 함수 sys.path import + graceful fallback (`_local_load_patterns`, `_local_scan_studio`), STATE.md frontmatter 수정 + gh issue 자동 생성 로직 완비
2. `.claude/deprecated_patterns.json` — 8 entries × (regex, reason, grade, name) 4 필드 (grade A:4 / B:3 / C:1)
3. `.planning/STATE.md` frontmatter 에 `phase_lock: false` default 필드 — GSD parser 호환 smoke 완료
4. `tests/phase10/test_drift_scan.py` + `test_phase_lock.py` 17+ tests GREEN (Wave 0 4 + main 7 + phase_lock 6)
5. CLI 모드: `--dry-run`, `--clear-lock`, `--skip-github-issue`, `--harness-path`, `--skip-harness-import` 각각 작동
6. A급 drift 감지 시 set_phase_lock + gh issue 호출 — subprocess mocked tests PASS
7. Phase 5/6 regression 보존 (329/329 + 236/236 전수 GREEN)
8. BLOCKER #2 redundant safety 방어선 #1 (Wave 0 manual `gh label create` 3종) 문서화
9. WARNING #4 graceful degradation — harness/ 부재 시 local-only scan 작동
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-02-SUMMARY.md` with:
- Commits: (Task 1 Wave 0 smoke + label manual dispatch + Task 2 wrapper implementation)
- Test count: Phase 10 Plan 2 (17+ tests) + regression preservation proof
- Reusable assets used: harness drift_scan.py (4 functions imported via sys.path, graceful fallback 내장)
- AUDIT-03 + AUDIT-04 checkbox 전환 trigger
- BLOCKER #2 label 사전 생성 — Wave 0 manual dispatch #1 완료 + Plan 4 GH Actions #2 대기
- WARNING #4 harness graceful fallback — local-only mode 확보
- Next: Plan 3 (KPI fetch) + Plan 4 (Scheduler) Wave 2 parallel execution
</output>
