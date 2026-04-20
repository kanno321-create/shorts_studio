---
phase: 10-sustained-operations
plan: 06
type: execute
wave: 3
depends_on: [10-03-youtube-analytics-fetch]
files_modified:
  - scripts/research_loop/__init__.py
  - scripts/research_loop/monthly_update.py
  - wiki/shorts/kpi/monthly_context_template.md
  - tests/phase10/test_research_loop.py
autonomous: true
requirements: [KPI-03, KPI-04]
must_haves:
  truths:
    - "scripts/research_loop/monthly_update.py 가 이전 월 KPI aggregate 결과 (상위 3 composite score 영상) 와 NotebookLM 조회 응답을 결합한 monthly_context_YYYY-MM.md 를 wiki/shorts/kpi/ 에 생성한다"
    - "NotebookLM query 는 shorts_naberal/.claude/skills/notebooklm/scripts/run.py 를 subprocess 로 호출하며, 실패 시 3-tier fallback (이전 월 context 재사용 → 빈 context 생성 → FAILURES append) 으로 graceful degrade 한다"
    - "NotebookLM source 추가는 자동화 불가 (공식 API 미공개 — RESEARCH Pitfall 6). 대표님 수동 업로드 reminder 만 stdout + email 로 dispatch"
    - "Producer 가 monthly_context 를 @wiki/shorts/kpi/monthly_context_latest.md 로 참조할 수 있도록 template.md + symlink-like copy 규약 명시 (AGENT.md 수정은 D-2 Lock 범위)"
  artifacts:
    - path: scripts/research_loop/__init__.py
      provides: "scripts.research_loop namespace"
    - path: scripts/research_loop/monthly_update.py
      provides: "Auto Research Loop CLI — KPI-03 + KPI-04"
      min_lines: 180
    - path: wiki/shorts/kpi/monthly_context_template.md
      provides: "Template with {YEAR_MONTH} {TOP_3_TABLE} {SUCCESS_PATTERNS} {AVOIDANCE} 4 placeholders"
      min_lines: 30
    - path: tests/phase10/test_research_loop.py
      provides: "KPI-03/04 unit — NotebookLM subprocess mocked + template rendering"
      min_lines: 100
  key_links:
    - from: scripts/research_loop/monthly_update.py
      to: scripts/analytics/monthly_aggregate.py
      via: "composite_score import + aggregate_month() 재사용 (Plan 3 공유 헬퍼)"
      pattern: "from scripts\\.analytics\\.monthly_aggregate import"
    - from: scripts/research_loop/monthly_update.py
      to: NotebookLM skill (shorts_naberal)
      via: "subprocess.run([sys.executable, str(NLM_SKILL / 'scripts/run.py'), 'ask_question.py', '--question', q, '--notebook-id', nid])"
      pattern: "notebooklm.*scripts.*run\\.py"
    - from: scripts/research_loop/monthly_update.py
      to: wiki/shorts/kpi/monthly_context_YYYY-MM.md
      via: "Template rendering + .write_text() — wiki append 허용 (D-2 Lock 범위 외)"
      pattern: "monthly_context_"
---

<objective>
월 1회 Auto Research Loop 를 구축한다: 이전 월 상위 3 composite score 영상을 식별 → NotebookLM 에서 성공 패턴 retrospective query → `wiki/shorts/kpi/monthly_context_YYYY-MM.md` 파일을 생성하여 다음 월 Producer 입력에 반영되게 한다. NotebookLM source 자동 추가는 API 부재로 불가능 — 대표님이 브라우저로 월 1회 수동 업로드하도록 reminder email + stdout 알림만 dispatch.

Purpose: 데이터 축적만으로는 학습 회로 불충분. Producer prompt 에 전월 지표가 자동 주입되어야 "다음 달 Producer 입력에 KPI 반영" (KPI-04) 이 성립.
Output: monthly_update.py + template.md + NotebookLM subprocess wrapper + 3-tier fallback.
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
@scripts/analytics/monthly_aggregate.py
@scripts/analytics/fetch_kpi.py
@CLAUDE.md
@.claude/memory/reference_api_keys_location.md

<interfaces>
<!-- NotebookLM skill subprocess 호출 + Plan 3 공유 헬퍼 -->

From RESEARCH.md §Plan 6 Open Q1 — NotebookLM CLI wrapper path + invocation:
```python
NLM_SKILL_PATH = Path("C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm")

def query_notebook(question: str, notebook_id: str) -> tuple[str, bool]:
    """Return (answer_text, success). Graceful fail on subprocess error."""
    try:
        result = subprocess.run(
            [sys.executable, str(NLM_SKILL_PATH / "scripts/run.py"),
             "ask_question.py",
             "--question", question,
             "--notebook-id", notebook_id],
            cwd=NLM_SKILL_PATH,
            capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
        if result.returncode != 0:
            return (result.stderr, False)
        return (result.stdout, True)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return (f"NotebookLM subprocess failed: {exc}", False)
```

From RESEARCH.md §Plan 6 Open Q2 — Composite score (shared with Plan 3 monthly_aggregate):
```python
from scripts.analytics.monthly_aggregate import composite_score, aggregate_month
# composite_score(metrics) = 0.5*r + 0.3*c + 0.2*v/60
```

From RESEARCH.md §Plan 6 Open Q3 — monthly_context_YYYY-MM.md 포맷:
```markdown
<!-- wiki/shorts/kpi/monthly_context_2026-05.md (Plan 6 auto-generated 2026-05-01) -->
# Monthly KPI Context — 2026-05 Producer Input

## Top 3 영상 (2026-04 월간)
| video_id | title | 3s_retention | completion | avg_view | composite |
| abc123 | ... | 68% | 42% | 27s | 0.614 |

## 성공 패턴 (NotebookLM 요약)
- 훅: 첫 1.5초 고유명사 제시 패턴이 retention 에 +8% (notebook query 결과)
- 페르소나: "탐정 ↔ 조수" 대화체가 단일 화자 narration 대비 completion +12%

## 하위 3 영상 회피 사항
...
```

From RESEARCH.md §Plan 6 Open Q4 — 3-tier fallback:
1. NotebookLM query 실패 → 이전 월 monthly_context 복사 + "이전 달 context 재사용" 표기
2. YouTube aggregate 결과 0건 → empty context + FAILURES append (F-KPI-XX)
3. 둘 다 실패 → exit 1 + email reminder to 대표님

From RESEARCH.md §Pitfall 6 — NotebookLM source 추가 자동화 불가:
- Plan 6 는 "md 파일 자동 생성 + 대표님 월 1회 수동 업로드 reminder" 로 재설계
- `notebook_id` 는 shorts_naberal 의 `library.json` 에 이미 등록된 `naberal-shorts-channel-bible` 사용 (Phase 6 Plan 04 에서 세팅됨, D-04-01 대표님 URL 제공 후 notebook_id)
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: monthly_context template.md + monthly_update.py CLI + NotebookLM subprocess wrapper + 테스트 (single task)</name>
  <files>
    scripts/research_loop/__init__.py,
    scripts/research_loop/monthly_update.py,
    wiki/shorts/kpi/monthly_context_template.md,
    tests/phase10/test_research_loop.py
  </files>
  <read_first>
    - `.planning/phases/10-sustained-operations/10-RESEARCH.md` §Plan 6 Open Q1-Q4 + §Pitfall 6
    - `scripts/analytics/monthly_aggregate.py` (Plan 3 산출물) — composite_score + aggregate_month export 확인
    - `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/SKILL.md` (CLI wrapper 패턴)
    - `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/scripts/run.py` 존재 확인 (없으면 subprocess mock 으로만 tests 작성, runtime 은 graceful fail)
    - `scripts/schedule/notify_failure.py` (Plan 4 산출물 — email sender 재사용 가능)
    - `tests/phase10/conftest.py` (fixtures)
  </read_first>
  <behavior>
    - Test 1 (test_template_has_four_placeholders): monthly_context_template.md 에 `{YEAR_MONTH}`, `{TOP_3_TABLE}`, `{SUCCESS_PATTERNS}`, `{AVOIDANCE}` 4 placeholder 존재
    - Test 2 (test_query_notebook_subprocess_called): monkeypatch `subprocess.run` → 반환값 고정 → `query_notebook("q", "nid")` 호출 시 subprocess called with 정확한 argv (5 elements: python, run.py path, "ask_question.py", "--question", "--notebook-id")
    - Test 3 (test_query_notebook_returncode_nonzero_returns_false): mock subprocess returncode 1 → returns `(stderr, False)`
    - Test 4 (test_query_notebook_timeout_graceful): mock `subprocess.TimeoutExpired` → returns `("..timed out..", False)` (explicit raise 금지 — 3-tier fallback 사용)
    - Test 5 (test_render_template): fixture videos + NotebookLM response → template.format() → Top 3 table 정확 + Success patterns 렌더
    - Test 6 (test_top_3_by_composite_score): 5 videos → top 3 composite sorted 내림차순
    - Test 7 (test_fallback_tier1_previous_month_reuse): NotebookLM fail → 전월 monthly_context 파일 있으면 복사 + "이전 달 재사용" 헤더 추가
    - Test 8 (test_fallback_tier2_empty_context_failures_append): aggregate 결과 0 videos → FAILURES.md F-KPI-XX append + empty context 생성
    - Test 9 (test_fallback_tier3_both_fail_exit_1): NotebookLM fail + videos 0 → exit 1 + stderr alert
    - Test 10 (test_cli_dry_run_no_file_output): `--dry-run` → monthly_context 파일 미생성 + stdout JSON
    - Test 11 (test_cli_idempotent_skip_existing): 이미 `monthly_context_2026-04.md` 존재 → skip + exit 0 with `"skipped": true`
    - Test 12 (test_notebook_id_from_env_or_flag): `NOTEBOOK_ID` env var OR `--notebook-id` 플래그 둘 다 accept + 없으면 argparse error
    - Test 13 (test_email_reminder_for_manual_upload): NotebookLM success 후 stdout 메시지에 "대표님 수동 업로드 reminder" 문구 포함 (email 은 Plan 4 notify_failure 를 optional 호출 — monkeypatch 확인)
  </behavior>
  <action>
    1. `wiki/shorts/kpi/monthly_context_template.md` 작성 (≥30 lines):
       ```markdown
       <!-- AUTO-GENERATED by scripts.research_loop.monthly_update — DO NOT EDIT -->
       <!-- Plan 10-06 / KPI-03 + KPI-04 / Generated: {GENERATED_AT} -->

       # Monthly KPI Context — {YEAR_MONTH} Producer Input

       > 이 파일은 월 1회 `scripts/research_loop/monthly_update.py` 가 생성합니다.
       > Producer (scripter, director, scene-planner) AGENT.md 가 `@wiki/shorts/kpi/monthly_context_latest.md` 로 참조합니다.

       ## Part 1: Top 3 영상 (composite score 기준, 이전 월 aggregate)

       {TOP_3_TABLE}

       ## Part 2: 성공 패턴 (NotebookLM retrospective)

       {SUCCESS_PATTERNS}

       ## Part 3: 회피 사항 (하위 영상 공통 실패)

       {AVOIDANCE}

       ## Part 4: 다음 월 Producer 입력 지시

       - Hook 길이 목표: 1.5~2.0 초 (retention_3s top video 패턴)
       - Completion 개선: 서사 arc + pivot 배치 (Part 2 근거 기반)
       - 음성 페이스: avg_view 초 수 분포 참조 (Part 1 평균)

       ---

       <!-- source_videos: {SOURCE_VIDEO_IDS} -->
       <!-- notebook_id: {NOTEBOOK_ID} -->
       <!-- fallback_tier: {FALLBACK_TIER} -->
       ```
    2. `scripts/research_loop/__init__.py` 작성 (네임스페이스):
       ```python
       """scripts.research_loop — Auto Research Loop (KPI-03 / KPI-04). Phase 10 신규."""
       from __future__ import annotations
       __all__ = []
       ```
    3. `scripts/research_loop/monthly_update.py` 작성 (≥180 lines):
       ```python
       """Monthly research loop — KPI-03 / KPI-04 / SC#5.

       Aggregates previous month's KPI, queries NotebookLM for success patterns,
       renders wiki/shorts/kpi/monthly_context_YYYY-MM.md for next-month Producer input.

       Fallback chain (RESEARCH Open Q4):
         T0: happy path — aggregate + notebooklm + render
         T1: notebooklm fail → previous monthly_context reuse with header note
         T2: aggregate empty → empty context + FAILURES.md F-KPI-XX append
         T3: both fail → exit 1 + reminder email (via scripts.schedule.notify_failure)
       """
       from __future__ import annotations
       import argparse
       import json
       import os
       import subprocess
       import sys
       from datetime import datetime
       from pathlib import Path
       from zoneinfo import ZoneInfo

       if hasattr(sys.stdout, "reconfigure"):
           sys.stdout.reconfigure(encoding="utf-8", errors="replace")

       KST = ZoneInfo("Asia/Seoul")
       DEFAULT_NLM_SKILL = Path("C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm")
       DEFAULT_WIKI_DIR = Path("wiki/shorts/kpi")
       DEFAULT_TEMPLATE = DEFAULT_WIKI_DIR / "monthly_context_template.md"
       DEFAULT_LATEST_SYMLINK_COPY = DEFAULT_WIKI_DIR / "monthly_context_latest.md"

       # Shared from Plan 3:
       from scripts.analytics.monthly_aggregate import composite_score, aggregate_month

       def previous_year_month(now: datetime) -> str:
           if now.month == 1:
               return f"{now.year - 1}-12"
           return f"{now.year}-{now.month - 1:02d}"

       def top_n_by_composite(videos: dict[str, dict], n: int = 3) -> list[tuple[str, dict]]:
           return sorted(videos.items(), key=lambda kv: kv[1].get("composite", 0.0), reverse=True)[:n]

       def render_top_3_table(top: list[tuple[str, dict]]) -> str:
           if not top:
               return "| (no data) | | | | |"
           lines = [
               "| video_id | 3s_retention | completion | avg_view_s | composite |",
               "|----------|--------------|------------|------------|-----------|",
           ]
           for vid, m in top:
               lines.append(
                   f"| `{vid}` | {m.get('retention_3s', 0):.3f} | "
                   f"{m.get('completion_rate', 0):.3f} | {m.get('avg_view_sec', 0):.1f} | "
                   f"{m.get('composite', 0):.3f} |"
               )
           return "\n".join(lines)

       def query_notebook(question: str, notebook_id: str,
                          nlm_skill: Path = DEFAULT_NLM_SKILL,
                          timeout: int = 120) -> tuple[str, bool]:
           """Return (answer, success). Graceful on subprocess failure."""
           run_py = nlm_skill / "scripts" / "run.py"
           if not run_py.exists():
               return (f"NotebookLM skill not found at {run_py}", False)
           try:
               result = subprocess.run(
                   [sys.executable, str(run_py),
                    "ask_question.py",
                    "--question", question,
                    "--notebook-id", notebook_id],
                   cwd=str(nlm_skill),
                   capture_output=True, text=True, encoding="utf-8", timeout=timeout,
               )
               if result.returncode != 0:
                   return (result.stderr or result.stdout, False)
               return (result.stdout, True)
           except subprocess.TimeoutExpired:
               return ("NotebookLM query timed out", False)
           except FileNotFoundError as exc:
               return (f"NotebookLM skill path invalid: {exc}", False)

       def render_context(template_text: str, year_month: str, videos: dict[str, dict],
                          nlm_answer: str, fallback_tier: int, notebook_id: str,
                          now: datetime) -> str:
           top = top_n_by_composite(videos, n=3)
           bottom = sorted(videos.items(),
                           key=lambda kv: kv[1].get("composite", 0.0))[:3]
           top_table = render_top_3_table(top)

           if fallback_tier == 0:
               success_patterns = nlm_answer.strip() or "(NotebookLM returned empty)"
           elif fallback_tier == 1:
               success_patterns = ("_이전 달 monthly_context 재사용 — NotebookLM query 실패_\n\n"
                                   f"{nlm_answer[:800]}")
           else:
               success_patterns = "_데이터 부족 — 다음 월 aggregate 완료 시 재생성_"

           if bottom:
               avoidance_lines = ["아래 영상들의 공통 패턴을 다음 달에 회피:"]
               for vid, m in bottom:
                   avoidance_lines.append(f"- `{vid}`: composite={m.get('composite', 0):.3f}, "
                                          f"retention_3s={m.get('retention_3s', 0):.3f}")
               avoidance = "\n".join(avoidance_lines)
           else:
               avoidance = "_하위 영상 데이터 부족_"

           source_ids = ", ".join(f"`{vid}`" for vid, _ in top) if top else "(none)"
           return template_text.format(
               GENERATED_AT=now.isoformat(),
               YEAR_MONTH=year_month,
               TOP_3_TABLE=top_table,
               SUCCESS_PATTERNS=success_patterns,
               AVOIDANCE=avoidance,
               SOURCE_VIDEO_IDS=source_ids,
               NOTEBOOK_ID=notebook_id,
               FALLBACK_TIER=fallback_tier,
           )

       def find_previous_context(wiki_dir: Path, year_month: str) -> Path | None:
           y, m = year_month.split("-")
           prev_m = int(m) - 1
           prev_y = int(y)
           if prev_m == 0:
               prev_m = 12
               prev_y -= 1
           candidate = wiki_dir / f"monthly_context_{prev_y}-{prev_m:02d}.md"
           return candidate if candidate.exists() else None

       def append_failures_kpi(failures: Path, reason: str, year_month: str, now: datetime) -> str:
           if not failures.exists():
               return "(FAILURES.md missing — skipped append)"
           import re
           existing = failures.read_text(encoding="utf-8")
           ids = re.findall(r"### F-KPI-(\d{2})", existing)
           next_id = max((int(i) for i in ids), default=0) + 1
           entry_id = f"F-KPI-{next_id:02d}"
           body = [
               "",
               "",
               f"## {entry_id} — Research Loop 실패 ({now.date().isoformat()}, {year_month})",
               "",
               f"**증상**: {reason}",
               "",
               "**조치**:",
               "1. `scripts/analytics/monthly_aggregate.py --year-month <prev>` 직접 실행 + 데이터 유무 확인",
               "2. YouTube Analytics API 인증 상태 확인 (scope 재인증 필요 시 Plan 3 Wave 0 참조)",
               "3. NotebookLM browser session 만료 확인 (대표님 수동 로그인 + library 재연결)",
               "4. Plan 10-08 ROLLBACK.md 의 학습 회로 오염 시나리오 참조",
           ]
           with failures.open("a", encoding="utf-8") as f:
               f.write("\n".join(body) + "\n")
           return entry_id

       def main(argv: list[str] | None = None) -> int:
           parser = argparse.ArgumentParser(description="Monthly research loop — KPI-03/04")
           parser.add_argument("--year-month", default=None,
                               help="YYYY-MM (default: previous month)")
           parser.add_argument("--daily-dir", type=Path, default=Path("data/kpi_daily"))
           parser.add_argument("--wiki-dir", type=Path, default=DEFAULT_WIKI_DIR)
           parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
           parser.add_argument("--nlm-skill", type=Path, default=DEFAULT_NLM_SKILL)
           parser.add_argument("--notebook-id", default=os.environ.get("NOTEBOOK_ID"))
           parser.add_argument("--failures", type=Path, default=Path("FAILURES.md"))
           parser.add_argument("--dry-run", action="store_true")
           parser.add_argument("--force", action="store_true",
                               help="Regenerate even if target file exists")
           args = parser.parse_args(argv)

           now = datetime.now(KST)
           ym = args.year_month or previous_year_month(now)
           target = args.wiki_dir / f"monthly_context_{ym}.md"

           if target.exists() and not args.force:
               result = {"year_month": ym, "skipped": True, "target": str(target)}
               print(json.dumps(result, ensure_ascii=False, indent=2))
               return 0

           if args.notebook_id is None:
               print("[ERROR] --notebook-id or NOTEBOOK_ID env required (shorts_naberal library.json entry)",
                     file=sys.stderr)
               return 2

           videos = aggregate_month(args.daily_dir, ym)

           question = (
               f"지난 {ym} 기간 상위 retention + completion 영상들의 공통 성공 패턴을 "
               "3가지로 요약해 주세요 (훅 / 페르소나 / 음성 페이스)."
           )
           nlm_answer, nlm_success = query_notebook(question, args.notebook_id, args.nlm_skill)

           # Tier 결정
           fallback_tier = 0
           if not videos and not nlm_success:
               fallback_tier = 3   # 둘 다 실패
           elif not videos:
               fallback_tier = 2   # 데이터 없음
           elif not nlm_success:
               fallback_tier = 1   # notebooklm 실패, 데이터는 있음

           summary = {
               "year_month": ym,
               "videos_count": len(videos),
               "notebooklm_success": nlm_success,
               "fallback_tier": fallback_tier,
               "target": str(target),
           }

           if fallback_tier == 3 and not args.dry_run:
               append_failures_kpi(args.failures, "NotebookLM + aggregate 모두 실패", ym, now)
               print(json.dumps(summary, ensure_ascii=False, indent=2))
               print(f"[FAIL] research loop failed for {ym} — manual pivot", file=sys.stderr)
               return 1

           template_text = args.template.read_text(encoding="utf-8")
           effective_answer = nlm_answer
           if fallback_tier == 1:
               prev = find_previous_context(args.wiki_dir, ym)
               if prev:
                   effective_answer = prev.read_text(encoding="utf-8") + "\n\n---\n\n" + effective_answer

           rendered = render_context(
               template_text, ym, videos, effective_answer, fallback_tier,
               args.notebook_id, now,
           )

           if args.dry_run:
               summary["dry_run"] = True
               summary["rendered_preview"] = rendered[:400]
               print(json.dumps(summary, ensure_ascii=False, indent=2))
               return 0

           target.parent.mkdir(parents=True, exist_ok=True)
           target.write_text(rendered, encoding="utf-8")
           # Update "latest" copy (no symlink — Windows compat)
           DEFAULT_LATEST_SYMLINK_COPY.write_text(rendered, encoding="utf-8")

           if fallback_tier == 2:
               append_failures_kpi(args.failures,
                                   f"Aggregate 결과 0 videos — NotebookLM 성공 {nlm_success}",
                                   ym, now)

           # Manual upload reminder (dispatched to stdout; optional email via scripts.schedule.notify_failure)
           reminder = (
               f"[REMINDER to 대표님] {ym} monthly_context 생성됨. "
               f"NotebookLM 에 {target.name} 을 수동 업로드하여 다음 월 Producer 의 RAG 에 반영하세요. "
               "(Pitfall 6: NotebookLM source add API 미공개, 수동 필요)"
           )
           summary["reminder"] = reminder
           print(json.dumps(summary, ensure_ascii=False, indent=2))
           return 0

       if __name__ == "__main__":
           sys.exit(main())
       ```
    4. `tests/phase10/test_research_loop.py` 작성 (≥100 lines) — 13 tests (Test 1-13):
       - template.md 읽기 + placeholder 존재 확인
       - monkeypatch `subprocess.run` for `query_notebook` (3 시나리오: success / rc=1 / TimeoutExpired)
       - fixture videos dict 로 `top_n_by_composite`, `render_top_3_table`, `render_context` 검증
       - tmp_path 에 이전 월 context 파일 미리 생성 → Tier 1 fallback 검증
       - tmp FAILURES.md → Tier 2 append 검증
       - CLI `--dry-run`, `--force`, idempotent skip 검증
    5. 실행: `pytest tests/phase10/test_research_loop.py -xvs` → 13 tests GREEN
    6. 수동 실증: `NOTEBOOK_ID=demo python -m scripts.research_loop.monthly_update --dry-run --year-month 2026-04 --daily-dir /tmp/nonexistent` — exit 0 + stdout `"videos_count": 0, "fallback_tier": 2 or 3` + `"dry_run": true`
  </action>
  <acceptance_criteria>
    - `ls scripts/research_loop/monthly_update.py wiki/shorts/kpi/monthly_context_template.md` 존재
    - `grep -c "{YEAR_MONTH}\\|{TOP_3_TABLE}\\|{SUCCESS_PATTERNS}\\|{AVOIDANCE}" wiki/shorts/kpi/monthly_context_template.md` ≥ 4
    - `python -c "from scripts.research_loop.monthly_update import main, query_notebook, render_context, top_n_by_composite, composite_score; print('OK')"` prints OK
    - `NOTEBOOK_ID=demo python -m scripts.research_loop.monthly_update --dry-run --year-month 2026-04 --daily-dir /tmp/no_such_dir` exit 0 + stdout JSON 에 `"year_month": "2026-04"` + `"fallback_tier"` key 존재
    - `pytest tests/phase10/test_research_loop.py -q` 13 tests GREEN
    - `grep -c "3-tier\\|fallback_tier" scripts/research_loop/monthly_update.py` ≥ 3
    - `grep -c "NOTEBOOK_ID" scripts/research_loop/monthly_update.py` ≥ 1 (env var accept)
    - `grep -c "F-KPI" scripts/research_loop/monthly_update.py` ≥ 2
    - `grep -c "from scripts.analytics.monthly_aggregate import" scripts/research_loop/monthly_update.py` == 1 (composite_score + aggregate_month 재사용)
    - `wc -l scripts/research_loop/monthly_update.py` ≥ 180 lines
    - Phase 10 Plans 1-5 regression 보존: `pytest tests/phase10 -q --tb=no --ignore=tests/phase10/test_research_loop.py` GREEN
  </acceptance_criteria>
  <verify>
    <automated>pytest tests/phase10/test_research_loop.py -q && NOTEBOOK_ID=demo python -m scripts.research_loop.monthly_update --dry-run --year-month 2026-04 --daily-dir /tmp/nonexistent_dir</automated>
  </verify>
  <done>monthly_update.py CLI 완비, template.md 4 placeholder, 3-tier fallback, 13 tests GREEN, composite_score 공유 헬퍼 재사용, Phase 10 Plans 1-5 regression 보존</done>
</task>

</tasks>

<verification>
- `pytest tests/phase10/test_research_loop.py -v` 13 tests PASS
- `NOTEBOOK_ID=demo python -m scripts.research_loop.monthly_update --dry-run --year-month 2026-04` exit 0 (data 없어도 graceful)
- `wiki/shorts/kpi/monthly_context_template.md` 4 placeholder 확인
- KPI-03 + KPI-04 requirement 코드+테스트 레벨 실증
- Pitfall 6 (NotebookLM source 추가 자동화 불가) 명시 — stdout reminder 로 대표님 dispatch
- Phase 10 Plans 1-5 regression 전수 보존
</verification>

<success_criteria>
1. `scripts/research_loop/monthly_update.py` 180+ lines, stdlib + scripts.analytics import
2. 3-tier fallback 구현 (happy / prev_month reuse / empty context + FAILURES / exit 1)
3. NotebookLM subprocess wrapper with timeout + FileNotFoundError graceful handling
4. Template 4 placeholder + Korean content 지원 (cp949 reconfigure)
5. `wiki/shorts/kpi/monthly_context_template.md` + `monthly_context_latest.md` 관리 규약 (Windows 호환 copy, symlink 금지)
6. 13 tests GREEN
7. KPI-03 + KPI-04 checkbox trigger
8. Phase 10 Plans 1-5 regression 보존
</success_criteria>

<output>
After completion, create `.planning/phases/10-sustained-operations/10-06-SUMMARY.md` with:
- Commits: (monthly_update + template + __init__ + tests)
- Reusable assets: composite_score from Plan 3, NotebookLM skill subprocess (shorts_naberal)
- Manual dispatch 대표님: 월 1회 browser 에서 monthly_context_latest.md 를 NotebookLM 에 수동 업로드 (Pitfall 6)
- KPI-03 + KPI-04 checkbox trigger
- **KPI-04 커버리지 (INFO #2)**:
  - 코드 레벨: `monthly_context_latest.md` 생성 파이프라인 완비 (본 Plan)
  - End-to-end: Producer AGENT.md 에 `@wiki/shorts/kpi/monthly_context_latest.md` wikilink 추가 필요 — AGENT.md 는 `.claude/agents/*/` 아래 위치하므로 D-2 Lock (2026-06-20) 해제 후 별도 Plan 에서 수행. 10-CONTEXT.md Deferred Ideas 에 "Producer AGENT.md monthly_context wikilink 추가 — Plan 11 candidate" 엔트리 추가 기록.
- Next: Plan 7 (trajectory) — Plan 3 aggregate 결과 활용, SC#6 커버
- Plan 4 Scheduler 가 `monthly-research-loop.yml` workflow 추가 여부는 Plan 7 완료 후 Plan 10 SUMMARY 단계에서 판단 (현재는 수동 dispatch 또는 Windows Task 로 대표님 편의대로)
</output>
