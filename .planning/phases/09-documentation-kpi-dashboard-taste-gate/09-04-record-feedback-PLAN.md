---
plan: 09-04
phase: 9
wave: 2
depends_on: [09-00, 09-01, 09-02, 09-03]
files_modified:
  - scripts/taste_gate/record_feedback.py
files_read_first:
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
  - tests/phase09/test_record_feedback.py
  - tests/phase09/test_score_threshold_filter.py
  - tests/phase09/test_failures_append_only.py
  - tests/phase09/conftest.py
  - scripts/failures/aggregate_patterns.py
  - scripts/publisher/smoke_test.py
  - .claude/failures/FAILURES.md
  - .claude/hooks/pre_tool_use.py
  - wiki/kpi/taste_gate_2026-04.md
  - scripts/taste_gate/__init__.py
autonomous: true
requirements: [KPI-05]
tasks_addressed: [9-04-01, 9-04-02, 9-04-03]
success_criteria: [SC#4_PARTIAL_PARSER_AND_APPEND]
estimated_commits: 3
parallel_boundary: sequential — Wave 2 depends on Wave 1 (taste_gate_2026-04.md format frozen by Plan 09-03 before parser can be written)

must_haves:
  truths:
    - "scripts/taste_gate/record_feedback.py exists and is ~150-250 lines stdlib-only"
    - "Module imports successfully: `from scripts.taste_gate.record_feedback import parse_taste_gate, filter_escalate, build_failures_block, append_to_failures, main, TasteGateParseError`"
    - "parse_taste_gate('2026-04') on synthetic fixture returns 6 rows with video_id/title/score/comment extracted correctly"
    - "filter_escalate applies D-13: scores <= 3 pass, scores > 3 filtered out"
    - "append_to_failures uses read+append+write pattern (preserves prior FAILURES.md content as prefix; Hook-compatible)"
    - "CLI --month 2026-04 --dry-run prints block to stdout without modifying FAILURES.md"
    - "CLI --month 2026-04 (without --dry-run) appends ### [taste_gate] 2026-04 리뷰 결과 section"
    - "Korean error messages raised via TasteGateParseError (Pitfall 5)"
    - "cp949 guard present (sys.stdout.reconfigure for Windows; Pitfall 7)"
    - "No skip_gates / TODO(next-session) / try-except-pass (Hook 3종 차단)"
    - "pytest tests/phase09/test_record_feedback.py -x exits 0"
    - "pytest tests/phase09/test_score_threshold_filter.py -x exits 0"
    - "pytest tests/phase09/test_failures_append_only.py -x exits 0"
  artifacts:
    - path: "scripts/taste_gate/record_feedback.py"
      provides: "D-12 taste_gate → FAILURES.md appender + D-13 score filter + argparse CLI + cp949 guard + Korean errors"
      min_lines: 150
      contains: "TasteGateParseError"
  key_links:
    - from: "scripts/taste_gate/record_feedback.py"
      to: "scripts/failures/aggregate_patterns.py"
      via: "Pattern mirror — stdlib-only argparse + re + pathlib + cp949 sys.stdout.reconfigure guard + Korean error strings"
      pattern: "sys.stdout.reconfigure|argparse|re.compile"
    - from: "scripts/taste_gate/record_feedback.py"
      to: ".claude/failures/FAILURES.md"
      via: "Append-only write path — read existing + add [taste_gate] block + write full content (Hook-compatible per Pitfall 2)"
      pattern: "FAILURES_PATH|read_text.*write_text"
    - from: "scripts/taste_gate/record_feedback.py"
      to: "wiki/kpi/taste_gate_YYYY-MM.md"
      via: "Parser reads Plan 09-03 dry-run output format"
      pattern: "TASTE_GATE_DIR|taste_gate_.*\\.md"
    - from: "scripts/taste_gate/record_feedback.py"
      to: ".claude/hooks/pre_tool_use.py:check_failures_append_only"
      via: "Hook compatibility — prior FAILURES.md content preserved as prefix; no open('w') on FAILURES_PATH"
      pattern: "read_text.*encoding.*write_text"
---

<objective>
Write `scripts/taste_gate/record_feedback.py` (~150-250 lines) — the Phase 9 Python glue that parses `wiki/kpi/taste_gate_YYYY-MM.md` evaluation forms, applies D-13 score threshold filter (<= 3 escalates), and appends `### [taste_gate] YYYY-MM 리뷰 결과` section to `.claude/failures/FAILURES.md` in a Phase 6 Hook-compatible manner (read existing content → append new block → write full content back).

Purpose: KPI-05 (월 1회 Taste gate) implementation — 대표님 수동 copy-paste 제거. D-12 auto-append. D-13 noise filter. This is Phase 9's only non-trivial code (~5% of the phase per Research Summary).

Implementation strictly mirrors `scripts/failures/aggregate_patterns.py` discipline:
- stdlib-only (argparse / re / pathlib / datetime / zoneinfo / sys / hashlib — NO third-party)
- Korean error messages via explicit raise (no try-except-pass; Pitfall 6)
- cp949 guard for Windows stdout (Pitfall 7)
- Strict row regex with named groups (Pitfall 5)
- Read+append+write pattern for FAILURES.md (Pitfall 2; Hook check_failures_append_only compatible)

TDD required — Plan 09-00 already shipped 3 RED test files (test_record_feedback.py + test_score_threshold_filter.py + test_failures_append_only.py) that skip via pytest.importorskip until this module lands.

Output: 1 stdlib-only Python script (~200 LOC) + 3 test files transition from skipped → green.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
@tests/phase09/test_record_feedback.py
@tests/phase09/test_score_threshold_filter.py
@tests/phase09/test_failures_append_only.py
@tests/phase09/conftest.py
@scripts/failures/aggregate_patterns.py
@scripts/publisher/smoke_test.py
@.claude/failures/FAILURES.md
@.claude/hooks/pre_tool_use.py
@wiki/kpi/taste_gate_2026-04.md

<interfaces>
## Complete record_feedback.py skeleton (verbatim from 09-RESEARCH.md §Code Examples Example 1)

The implementation MUST match this signature surface exactly — tests import specific names. Adapt docstrings/formatting to project style but keep public names identical:

```python
#!/usr/bin/env python3
"""Taste Gate → FAILURES.md appender (D-12 implementation).

Parses wiki/kpi/taste_gate_YYYY-MM.md, filters rows with score <= 3 (D-13),
appends `### [taste_gate] YYYY-MM 리뷰 결과` block to .claude/failures/FAILURES.md.

Hook compatibility (Phase 6 D-11): uses read+append+write pattern so prior
FAILURES.md content is preserved as prefix (check_failures_append_only accepts).

Usage:
    python scripts/taste_gate/record_feedback.py --month 2026-04
    python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run

Exit codes:
    0 = success (block appended or dry-run printed)
    2 = argparse error
    3 = taste_gate file not found / parse error
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FAILURES_PATH = Path(".claude/failures/FAILURES.md")
TASTE_GATE_DIR = Path("wiki/kpi")
KST = ZoneInfo("Asia/Seoul")

# Parses table row: | rank | video_id | title | 3sec | completion | avg | score | comment | tag |
ROW_RE = re.compile(
    r"^\|\s*(?P<rank>\d+)\s*\|\s*(?P<video_id>[\w-]+)\s*\|\s*\"?(?P<title>[^\"\|]+?)\"?\s*\|"
    r"\s*(?P<retention>[^\|]*?)\s*\|\s*(?P<completion>[^\|]*?)\s*\|\s*(?P<avg>[^\|]*?)\s*\|"
    r"\s*(?P<score>[1-5]|_)\s*\|\s*(?P<comment>[^\|]*?)\s*\|\s*(?P<tag>[^\|]*?)\s*\|",
    re.MULTILINE,
)


class TasteGateParseError(Exception):
    """Raised on malformed taste_gate_YYYY-MM.md."""


def parse_taste_gate(month: str) -> list[dict]:
    """Return list of evaluated rows. Raises TasteGateParseError on malformed input."""
    path = TASTE_GATE_DIR / f"taste_gate_{month}.md"
    if not path.exists():
        raise TasteGateParseError(f"파일 없음: {path} — 월별 평가 폼을 먼저 생성하세요")
    text = path.read_text(encoding="utf-8")
    rows: list[dict] = []
    for m in ROW_RE.finditer(text):
        d = m.groupdict()
        if d["score"] == "_":
            print(f"WARN: rank {d['rank']} 미평가 (score='_') — 건너뜀", file=sys.stderr)
            continue
        try:
            d["score"] = int(d["score"])
        except ValueError as e:
            raise TasteGateParseError(f"rank {d['rank']} 점수 오류: {d['score']}") from e
        rows.append(d)
    if not rows:
        raise TasteGateParseError(f"평가된 행이 없습니다: {path}")
    return rows


def filter_escalate(rows: list[dict]) -> list[dict]:
    """D-13: only score <= 3 escalates to FAILURES.md."""
    return [r for r in rows if r["score"] <= 3]


def build_failures_block(month: str, escalated: list[dict]) -> str:
    """Build the `### [taste_gate] YYYY-MM 리뷰 결과` block (Phase 6 FAILURES schema)."""
    now_kst = datetime.now(KST).isoformat()
    lines = [
        "",
        f"### [taste_gate] {month} 리뷰 결과",
        f"- **Tier**: B",
        f"- **발생 세션**: {now_kst}",
        f"- **재발 횟수**: 1",
        f"- **Trigger**: 월간 Taste Gate 평가 점수 <= 3",
        f"- **무엇**: 대표님 평가 하위 항목 {len(escalated)}건 — " + ", ".join(
            f"{r['video_id']}({r['score']}점)" for r in escalated
        ),
        f"- **왜**: 채널 정체성 / 품질 기대치 미달 — 다음 월 Producer 입력 조정 필요",
        f"- **정답**: 하위 코멘트 패턴을 다음 월 niche-classifier / scripter 프롬프트에 반영",
        f"- **검증**: 다음 월 Taste Gate 동일 패턴 재발 여부",
        f"- **상태**: observed",
        f"- **관련**: wiki/kpi/taste_gate_{month}.md",
        "",
        "#### 세부 코멘트",
    ]
    for r in escalated:
        lines.append(f"- **{r['video_id']}** ({r['score']}/5): {r['comment']}")
    return "\n".join(lines)


def append_to_failures(block: str) -> None:
    """D-11 append-only compliant: read existing + append + write full.

    Hook check_failures_append_only (Phase 6) accepts writes where prior content
    is preserved as prefix of new content. Using open('a') would ALSO work but
    this read+append+write pattern is more auditable and atomic.
    """
    existing = FAILURES_PATH.read_text(encoding="utf-8")
    new_content = existing + "\n" + block + "\n"
    FAILURES_PATH.write_text(new_content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Taste Gate → FAILURES.md appender (D-12).")
    parser.add_argument("--month", required=True, help="YYYY-MM (예: 2026-04)")
    parser.add_argument("--dry-run", action="store_true", help="FAILURES.md에 쓰지 않고 블록만 출력")
    args = parser.parse_args(argv)

    if not re.match(r"^\d{4}-\d{2}$", args.month):
        parser.error(f"--month 형식 오류: {args.month!r} (예: 2026-04)")

    try:
        rows = parse_taste_gate(args.month)
    except TasteGateParseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3

    escalated = filter_escalate(rows)
    block = build_failures_block(args.month, escalated)

    if args.dry_run:
        print(block)
        print(f"[dry-run] FAILURES.md 추가 예정 항목: {len(escalated)}건", file=sys.stderr)
        return 0

    if not escalated:
        print(f"승격 대상 없음 (모두 score > 3) — FAILURES.md 변경 없음", file=sys.stderr)
        return 0

    append_to_failures(block)
    print(f"FAILURES.md 추가 완료: {len(escalated)}건 ({args.month})")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
```

## Public API surface (tests depend on these exact names)

- Module-level constants: `FAILURES_PATH`, `TASTE_GATE_DIR`, `KST`, `ROW_RE`
- Public functions: `parse_taste_gate(month) -> list[dict]`, `filter_escalate(rows) -> list[dict]`, `build_failures_block(month, escalated) -> str`, `append_to_failures(block) -> None`, `main(argv) -> int`
- Public exception: `TasteGateParseError`

## Forbidden patterns (Hook 3종 차단 + CLAUDE.md)

- `skip_gates=True` or `skip_gates` string — physical ban (pre_tool_use regex)
- `TODO(next-session)` — physical ban (pre_tool_use regex)
- `try: ... except: pass` — silent fallback ban (Pitfall 6)
- `open(FAILURES_PATH, 'w')` — truncates FAILURES.md, violates Phase 6 D-11 Hook
- Placeholder titles "테스트용 쇼츠 #1" etc. — CONTEXT forbids

## Test-time fixture monkeypatching (how Plan 09-00 tests invoke)

Tests use `monkeypatch.setattr(record_feedback, "TASTE_GATE_DIR", synthetic_taste_gate_april.parent)` to redirect parser to fixture location, and `monkeypatch.setattr(record_feedback, "FAILURES_PATH", tmp_failures_md)` to redirect writer to tmp FAILURES.md. Module constants MUST be module-level `Path` attributes (not locals inside functions) for this monkeypatch to work.
</interfaces>
</context>

<tasks>

<task id="9-04-01">
  <action>
Create `scripts/taste_gate/record_feedback.py` with EXACTLY the content shown in the `<interfaces>` block above (the full 200-line skeleton from 09-RESEARCH.md §Code Examples Example 1). Literal requirements:

1. **Shebang:** `#!/usr/bin/env python3` first line
2. **Docstring:** Multi-line module docstring explaining purpose + Hook compatibility + usage + exit codes
3. **Imports:** stdlib-only — `argparse`, `re`, `sys`, `datetime`, `pathlib`, `zoneinfo`. No third-party imports allowed.
4. **Module constants MUST be module-level (not inside functions):**
   - `FAILURES_PATH = Path(".claude/failures/FAILURES.md")`
   - `TASTE_GATE_DIR = Path("wiki/kpi")`
   - `KST = ZoneInfo("Asia/Seoul")`
   - `ROW_RE = re.compile(...)` — the 9-field regex with named groups for rank/video_id/title/retention/completion/avg/score/comment/tag
5. **Public exception class:** `TasteGateParseError(Exception)` with docstring
6. **Public function `parse_taste_gate(month: str) -> list[dict]`:** opens `TASTE_GATE_DIR / f"taste_gate_{month}.md"`; raises `TasteGateParseError` with literal Korean `f"파일 없음: {path} — 월별 평가 폼을 먼저 생성하세요"` on missing file; skips rows with score='_' via print to stderr; raises on unparseable score; raises `f"평가된 행이 없습니다: {path}"` if no evaluated rows
7. **Public function `filter_escalate(rows: list[dict]) -> list[dict]`:** returns `[r for r in rows if r["score"] <= 3]` — D-13 filter
8. **Public function `build_failures_block(month: str, escalated: list[dict]) -> str`:** produces the 14-line Phase 6 FAILURES schema block + "#### 세부 코멘트" section + one `- **{video_id}** ({score}/5): {comment}` line per escalated row. Uses `datetime.now(KST).isoformat()` for 발생 세션 timestamp.
9. **Public function `append_to_failures(block: str) -> None`:** `existing = FAILURES_PATH.read_text(encoding="utf-8")`, then `FAILURES_PATH.write_text(existing + "\n" + block + "\n", encoding="utf-8")`. This pattern (read + concatenate + write) keeps prior content as PREFIX which the Phase 6 Hook `check_failures_append_only` accepts. MUST NOT use `open(path, "w")` as the direct write — the read+append+write via Path methods is semantically equivalent to what Hook expects.
10. **Public function `main(argv: list[str] | None = None) -> int`:**
    - `argparse.ArgumentParser(description=...)` with `--month` (required) + `--dry-run` (store_true)
    - Regex validate month format `^\d{4}-\d{2}$` via `parser.error`
    - Try `parse_taste_gate` → on `TasteGateParseError` print to stderr and return 3
    - `filter_escalate` → `build_failures_block`
    - If `--dry-run`: print block + "`[dry-run] FAILURES.md 추가 예정 항목: {n}건`" → return 0
    - If empty escalated: print "`승격 대상 없음 (모두 score > 3)`" → return 0
    - Else `append_to_failures(block)` + success print → return 0
11. **Main guard** with cp949 reconfigure:
    ```python
    if __name__ == "__main__":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.exit(main())
    ```
12. **NO forbidden patterns** — no `skip_gates`, no `TODO(next-session)`, no `try: ... except: pass`, no `open(FAILURES_PATH, "w")`.

File size target: 150-250 lines (Research estimate was ~150-200 LOC; acceptable up to 250 LOC with docstrings/comments).
  </action>
  <read_first>
    - tests/phase09/test_record_feedback.py (imports expected: parse_taste_gate + TasteGateParseError + TASTE_GATE_DIR)
    - tests/phase09/test_score_threshold_filter.py (imports expected: filter_escalate + parse_taste_gate + TASTE_GATE_DIR)
    - tests/phase09/test_failures_append_only.py (imports expected: build_failures_block + append_to_failures + FAILURES_PATH + AST scan for no-open-w)
    - tests/phase09/conftest.py (synthetic_taste_gate_april fixture layout — verify path.parent convention matches module expectations)
    - scripts/failures/aggregate_patterns.py (canonical stdlib-only CLI pattern — argparse + re + pathlib + cp949 guard)
    - scripts/publisher/smoke_test.py (CLI + cp949 reconfigure + Korean errors precedent)
    - .claude/failures/FAILURES.md (entry schema lines — Phase 6 Tier/발생 세션/재발 횟수/Trigger/무엇/왜/정답/검증/상태/관련)
    - .claude/hooks/pre_tool_use.py:check_failures_append_only (Phase 6 D-11 Hook logic — verify prior content must be preserved as prefix)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Code Examples Example 1 (verbatim skeleton) + §Pitfall 2 (Hook compat) + §Pitfall 5 (regex + Korean errors) + §Pitfall 6 (Hook 3종) + §Pitfall 7 (cp949)
    - wiki/kpi/taste_gate_2026-04.md (parser input format — confirm 9-column table shape matches ROW_RE)
  </read_first>
  <acceptance_criteria>
    - `test -f scripts/taste_gate/record_feedback.py` exits 0
    - `wc -l < scripts/taste_gate/record_feedback.py` outputs a number >= 150
    - `wc -l < scripts/taste_gate/record_feedback.py` outputs a number <= 280
    - `python -c "import ast; ast.parse(open('scripts/taste_gate/record_feedback.py', encoding='utf-8').read())"` exits 0
    - `python -c "from scripts.taste_gate.record_feedback import parse_taste_gate, filter_escalate, build_failures_block, append_to_failures, main, TasteGateParseError, FAILURES_PATH, TASTE_GATE_DIR, KST, ROW_RE"` exits 0
    - `grep -q 'class TasteGateParseError' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'def parse_taste_gate' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'def filter_escalate' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'def build_failures_block' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'def append_to_failures' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'def main' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'sys.stdout.reconfigure' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'ZoneInfo..Asia/Seoul' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q '파일 없음' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q '평가된 행이 없습니다' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -qE 'r\["score"\] <= 3' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -qE 'read_text.*encoding.*utf-8' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -qE 'write_text.*encoding.*utf-8' scripts/taste_gate/record_feedback.py` exits 0
    - `grep -q 'skip_gates' scripts/taste_gate/record_feedback.py` must return 1 (not present — Hook 3종 차단)
    - `grep -q 'TODO(next-session)' scripts/taste_gate/record_feedback.py` must return 1
    - `python -c "import ast, pathlib; tree = ast.parse(pathlib.Path('scripts/taste_gate/record_feedback.py').read_text(encoding='utf-8')); failures = []; [failures.append('open w mode') for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'open' and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == 'w']; assert not failures, failures"` exits 0
    - Only stdlib imports: `python -c "import ast, pathlib; tree = ast.parse(pathlib.Path('scripts/taste_gate/record_feedback.py').read_text(encoding='utf-8')); allowed = {'argparse','re','sys','datetime','pathlib','zoneinfo','__future__'}; imports = set(); [imports.update({n.name.split('.')[0] for n in node.names}) if isinstance(node, ast.Import) else imports.add(node.module.split('.')[0]) if isinstance(node, ast.ImportFrom) and node.module else None for node in ast.walk(tree)]; extras = imports - allowed; assert not extras, f'non-stdlib imports: {extras}'"` exits 0
  </acceptance_criteria>
  <automated>python -c "from scripts.taste_gate.record_feedback import parse_taste_gate, filter_escalate, build_failures_block, append_to_failures, main, TasteGateParseError, FAILURES_PATH, TASTE_GATE_DIR, KST, ROW_RE; print('import OK')"</automated>
  <task_type>impl</task_type>
</task>

<task id="9-04-02">
  <action>
Run the 3 Phase 9 Wave 2 test files that were RED stubs in Plan 09-00. They MUST all transition to GREEN now that record_feedback.py is shipped:

```
python -m pytest tests/phase09/test_record_feedback.py -x --no-cov -v
python -m pytest tests/phase09/test_score_threshold_filter.py -x --no-cov -v
python -m pytest tests/phase09/test_failures_append_only.py -x --no-cov -v
```

All three MUST exit 0. Expected test counts:
- test_record_feedback.py: ≥ 3 tests PASS (test_parse_six_rows, test_parse_extracts_required_fields, test_parse_raises_on_missing_file)
- test_score_threshold_filter.py: ≥ 5 tests PASS (score_1, score_2, score_3_boundary, score_4, score_5, mixed_six_rows)
- test_failures_append_only.py: ≥ 5 tests PASS (source_file_exists, no_open_w, append_preserves_prior, no_skip_gates_string, no_todo_next_session, no_try_except_silent_fallback)

If any test fails, debug by:
1. Confirming monkeypatch on `TASTE_GATE_DIR` / `FAILURES_PATH` module-level constants works (not function-local)
2. Confirming ROW_RE matches all 6 synthetic rows from tests/phase09/conftest.py fixture
3. Confirming Korean strings match test expectations literally
4. Confirming append_to_failures preserves prior content as PREFIX (startswith check)

Then run a manual CLI smoke test via subprocess to catch integration issues:

```
python -c "
import subprocess
from pathlib import Path
import tempfile
import os

tmpdir = tempfile.mkdtemp()
# Seed the synthetic taste_gate file
taste_gate = Path(tmpdir) / 'wiki' / 'kpi' / 'taste_gate_2026-04.md'
taste_gate.parent.mkdir(parents=True)
src = Path('wiki/kpi/taste_gate_2026-04.md').read_text(encoding='utf-8')
taste_gate.write_text(src, encoding='utf-8')
failures = Path(tmpdir) / 'FAILURES.md'
failures.write_text('# FAILURES\n\nexisting content\n', encoding='utf-8')

# Override constants via env-agnostic subprocess module call
result = subprocess.run(
    ['python', '-c', f'''
import sys, pathlib
sys.path.insert(0, \".\")
from scripts.taste_gate import record_feedback as rf
rf.TASTE_GATE_DIR = pathlib.Path(r\"{tmpdir}/wiki/kpi\")
rf.FAILURES_PATH = pathlib.Path(r\"{tmpdir}/FAILURES.md\")
sys.exit(rf.main([\"--month\", \"2026-04\", \"--dry-run\"]))
'''],
    capture_output=True, text=True
)
print('stdout:', result.stdout[:500])
print('stderr:', result.stderr[:500])
print('rc:', result.returncode)
assert result.returncode == 0, f'--dry-run failed: {result.stderr}'
print('CLI smoke --dry-run OK')
"
```

Smoke test MUST exit 0 with "CLI smoke --dry-run OK" in output.

Finally run Phase 4-8 regression collection sweep to confirm no prior test broken:

```
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 -q --no-cov --co
```

MUST exit 0.
  </action>
  <read_first>
    - scripts/taste_gate/record_feedback.py (just-written module)
    - tests/phase09/test_record_feedback.py
    - tests/phase09/test_score_threshold_filter.py
    - tests/phase09/test_failures_append_only.py
    - tests/phase09/conftest.py
  </read_first>
  <acceptance_criteria>
    - `python -m pytest tests/phase09/test_record_feedback.py -x --no-cov` exits 0
    - `python -m pytest tests/phase09/test_score_threshold_filter.py -x --no-cov` exits 0
    - `python -m pytest tests/phase09/test_failures_append_only.py -x --no-cov` exits 0
    - `python -m pytest tests/phase09/test_record_feedback.py tests/phase09/test_score_threshold_filter.py tests/phase09/test_failures_append_only.py -v --no-cov 2>&1 | grep -c 'PASSED'` outputs `>= 13` (combined >= 13 test cases PASS)
    - `python -m pytest tests/phase09/test_record_feedback.py tests/phase09/test_score_threshold_filter.py tests/phase09/test_failures_append_only.py -v --no-cov 2>&1 | grep -c 'FAILED\|ERROR'` outputs `0`
    - `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov` exits 0
    - CLI smoke subprocess returns 0 with synthetic fixture
  </acceptance_criteria>
  <automated>python -m pytest tests/phase09/test_record_feedback.py tests/phase09/test_score_threshold_filter.py tests/phase09/test_failures_append_only.py -x --no-cov</automated>
  <task_type>verify</task_type>
</task>

<task id="9-04-03">
  <action>
Run a real-file non-destructive dry-run against the actual wiki/kpi/taste_gate_2026-04.md (not a fixture copy) to confirm production path works end-to-end. This uses the script's real `FAILURES_PATH` and `TASTE_GATE_DIR` constants without monkeypatch — however it MUST use `--dry-run` flag so NO write to FAILURES.md occurs.

```
python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run
```

Expected stdout content (partial match):
- `### [taste_gate] 2026-04 리뷰 결과`
- `- **Tier**: B`
- `월간 Taste Gate 평가 점수 <= 3`
- `대표님 평가 하위 항목 3건` (D-13 filter: scores 3/2/1 from dry-run fixture)
- `- **jkl012**` / `- **mno345**` / `- **pqr678**` (3 escalated items)
- `- **abc123**` must NOT appear (score 5 filtered out)

Expected stderr content (partial):
- `[dry-run] FAILURES.md 추가 예정 항목: 3건`

Expected exit code: 0

MUST NOT modify `.claude/failures/FAILURES.md` — verify via sha256:

```
python -c "
import hashlib, pathlib, subprocess, sys
p = pathlib.Path('.claude/failures/FAILURES.md')
before = hashlib.sha256(p.read_bytes()).hexdigest()
result = subprocess.run(['python', 'scripts/taste_gate/record_feedback.py', '--month', '2026-04', '--dry-run'], capture_output=True, text=True)
after = hashlib.sha256(p.read_bytes()).hexdigest()
assert before == after, f'FAILURES.md changed! dry-run violated append-only.\nBefore: {before}\nAfter: {after}'
assert result.returncode == 0, f'rc={result.returncode}'
assert '### [taste_gate] 2026-04' in result.stdout, f'block header missing in stdout'
assert '3건' in result.stderr or '3건' in result.stdout, f'escalation count 3건 missing'
print('PRODUCTION DRY-RUN OK — FAILURES.md sha256 preserved:', before[:12])
"
```

Also test error paths:

1. **Missing file:** Invoke with `--month 2099-12` (file doesn't exist). Expected rc=3 + stderr contains "파일 없음".

```
python scripts/taste_gate/record_feedback.py --month 2099-12 2>&1 | tee /tmp/missing-month.log
test $? -eq 3
grep -q '파일 없음' /tmp/missing-month.log
```

2. **Invalid month format:** Invoke with `--month abc`. Expected rc=2 (argparse error) + stderr contains "--month 형식 오류".

```
python scripts/taste_gate/record_feedback.py --month abc 2>&1 | tee /tmp/bad-month.log
test $? -eq 2
grep -q "--month 형식 오류" /tmp/bad-month.log
```

3. **Empty escalation:** Create a tmp file where all scores are > 3, verify rc=0 + stderr "승격 대상 없음".

NO code changes — pure verification of Plan 09-04 production behavior. If any check fails, escalate with diagnostic output.

Run final full Phase 9 sweep to confirm all Wave 2 tests still green:

```
python -m pytest tests/phase09/ -v --no-cov --ignore tests/phase09/test_e2e_synthetic_dry_run.py --ignore tests/phase09/phase09_acceptance.py
```

(exclude Plan 09-05 test and aggregator which still RED at this point). MUST exit 0.
  </action>
  <read_first>
    - scripts/taste_gate/record_feedback.py
    - wiki/kpi/taste_gate_2026-04.md (production dry-run input)
    - .claude/failures/FAILURES.md (verify sha256 unchanged after dry-run)
  </read_first>
  <acceptance_criteria>
    - `python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run` exits 0
    - stdout of above contains `### [taste_gate] 2026-04`
    - stdout contains `jkl012` AND `mno345` AND `pqr678` (3 D-13 escalated items)
    - stdout does NOT contain `abc123` in escalation context (score 5, filtered out — it may appear in Trigger description acceptable)
    - stderr contains `3건` (escalation count)
    - sha256 of `.claude/failures/FAILURES.md` is identical before and after --dry-run invocation
    - `python scripts/taste_gate/record_feedback.py --month 2099-12; test $? -eq 3` exits 0
    - `python scripts/taste_gate/record_feedback.py --month abc 2>&1; test $? -eq 2` exits 0
    - `python -m pytest tests/phase09/ -v --no-cov --ignore tests/phase09/test_e2e_synthetic_dry_run.py --ignore tests/phase09/phase09_acceptance.py` exits 0
    - `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov` exits 0
  </acceptance_criteria>
  <automated>python scripts/taste_gate/record_feedback.py --month 2026-04 --dry-run</automated>
  <task_type>verify</task_type>
</task>

</tasks>

<verification>
1. `scripts/taste_gate/record_feedback.py` ships with exact public API (parse_taste_gate / filter_escalate / build_failures_block / append_to_failures / main / TasteGateParseError + 4 module-level constants).
2. File is stdlib-only (no third-party imports).
3. Hook 3종 compliance verified via AST scan: no open('w') on FAILURES_PATH, no skip_gates, no TODO(next-session), no try/except: pass.
4. cp949 guard present (sys.stdout.reconfigure).
5. Korean error messages via explicit raise.
6. All 13+ Wave 2 test cases transition RED → GREEN.
7. Production dry-run against real wiki/kpi/taste_gate_2026-04.md succeeds with 3 D-13 escalations + preserves FAILURES.md sha256.
8. Error paths (missing file rc=3, bad format rc=2, empty escalation rc=0) all behave correctly.
9. Phase 4-8 986+ regression collection preserved.
</verification>

<success_criteria>
Plan 09-04 is COMPLETE when:
- `scripts/taste_gate/record_feedback.py` exists with full public API (150-250 LOC stdlib-only).
- All 3 Wave 2 test files GREEN (13+ tests PASS combined).
- Production dry-run works against real taste_gate_2026-04.md + produces exactly 3 D-13 escalations (scores 3/2/1 filtered in; scores 5/4/4 filtered out).
- FAILURES.md sha256 UNCHANGED after --dry-run (proving append-only safety + Hook compatibility).
- 3 error paths exit with correct codes (missing file=3, bad format=2, empty=0).
- Phase 4-8 986+ regression collection preserved.
- KPI-05 parser + filter + appender backbone shipped. Plan 09-05 now has all pieces for E2E phase gate.
</success_criteria>

<output>
Create `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-04-SUMMARY.md` documenting:
- File created (scripts/taste_gate/record_feedback.py with LOC count)
- Public API surface (5 functions + 1 exception + 4 constants)
- Test results: test_record_feedback.py / test_score_threshold_filter.py / test_failures_append_only.py (all PASS counts)
- Production dry-run output (first 30 lines of stdout)
- FAILURES.md sha256 before/after (matching)
- Error path exit codes verified (3/2/0)
- Phase 4-8 regression collection result
- Commit hashes (expected 3 atomic commits: RED skel + GREEN impl + verification)
</output>
