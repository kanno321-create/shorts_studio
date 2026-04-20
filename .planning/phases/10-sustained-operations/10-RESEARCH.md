# Phase 10: Sustained Operations — Research

**Researched:** 2026-04-20
**Domain:** Sustained Operations (YouTube Analytics cron + Drift audit + D-2 Lock enforcement + Auto Research Loop + YPP trajectory)
**Confidence:** HIGH (대부분의 세부 결정이 locked + 재사용 자산 7종 모두 실존 확인)

## Summary

Phase 10 은 **영구 지속 phase** 로, 8 개 Plan (SC#1~6 + Scheduler + Rollback) 모두가 이미 검증된 재사용 자산 위에 얹혀가는 **조립 작업**이다. 대부분의 리서치 항목이 `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` 와 `scripts/publisher/*.py`, `scripts/validate/harness_audit.py`, `scripts/failures/aggregate_patterns.py` 의 **public API 확인**으로 해결됐다. 외부 문서 리서치는 YouTube Analytics v2 `reports.query` 엔드포인트와 GitHub Actions cron `timezone:` 필드 (2025 추가), Windows Task Scheduler PowerShell cmdlet 확인 3종에 한정된다.

**Primary recommendation:** 각 Plan 은 기존 모듈을 import-and-wire 방식으로 구성한다. 새로운 발명은 금지 — `Reusable Assets Map` 테이블의 함수를 직접 호출한다. drift_scan 은 harness 공용 버전을 **복사하지 말고** `sys.path` 로 참조한다 (harness 업데이트 시 자동 동기화).

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Exit Criterion — 옵션 B+C 하이브리드 (Rolling 12개월 + 3단계 Milestone)**
- 1차 gate (3개월, 2026-07-20): 누적 구독자 ≥ 100명. 미달 시 니치/훅 iteration Plan 추가.
- 2차 gate (6개월, 2026-10-20): 누적 구독자 ≥ 300명, 3초 retention ≥ 60%.
- 3차 gate (12개월, 2027-04-20): Rolling 12개월 기준 구독자 ≥ 1000 + 뷰 ≥ 10M. 달성 월에 YPP 진입 + Phase 10 "성공 선언" (sustained는 계속).
- 근거: YPP 공식 계산 rolling 12개월 + 경영자용 pivot 판단 3단계 milestone. `wiki/ypp/trajectory.md` 월별 자동 append 로 SC#6 충족.

**D-2 Lock Scope — 최대 보수 2개월 lock**
- 기간: 2026-04-20 ~ 2026-06-20 (ROADMAP "1~2개월" 상한 채택)
- 검증 파일: `scripts/audit/skill_patch_counter.py` — `git log --since="2026-04-20" --name-only` 기반, 금지 경로 hit 시 count++
- Exit 조건 (lock 해제): 2개월 경과 + FAILURES.md 엔트리 ≥ 10건 + 월 1회 taste gate 2회 완료
- 해제 후 정책: SKILL patch 허용하되 모든 patch 는 `FAILURES.md` 의 특정 엔트리 reference 필수 (root-cause grounding)
- 금지 경로 (count 된다): `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md` 본문
- 허용 경로: `SKILL.md.candidate`, `scripts/**/*.py`, `.planning/phases/10-*/`, `wiki/**/*.md` append, `FAILURES.md` append, `.claude/memory/*.md`

**Scheduler — 하이브리드 (GH Actions + Windows Task Scheduler)**
- GH Actions cron (`.github/workflows/`, 클라우드 24/7):
  - `analytics-daily.yml` — `scripts/analytics/fetch_kpi.py` 매일 KST 05:00 실행. API key 는 GH secrets.
  - `drift-scan-weekly.yml` — `scripts/audit/drift_scan.py` 매주 월요일 KST 09:00. A급 drift 발견 시 GitHub issue 자동 생성.
  - `skill-patch-count-monthly.yml` — `scripts/audit/skill_patch_counter.py` 매월 1일 KST 09:00 + 리포트 append.
- Windows Task Scheduler (대표님 로컬 PC):
  - 영상 생성 파이프라인 + YouTube 업로드 + `publish_lock.py` 48h+jitter + `kst_window.py` 평일 20-23/주말 12-15 KST 강제
- 실패 알림 3 채널:
  - GH Actions 실패 → built-in email → `kanno3@naver.com`
  - 로컬 Windows Task Scheduler 실패 → PowerShell SMTP script → Gmail/Naver
  - 양쪽 모두 `FAILURES.md` append (F-OPS-XX 카테고리, `check_failures_append_only` hook 자동 enforce)

### Claude's Discretion (구현 세부)

- `skill_patch_counter.py` 의 정확한 git grep 정규식
- `drift_scan.py` 의 A급 판정 heuristic 세부 (harness 참조)
- YouTube Analytics v2 API 엔드포인트 선택 (reportsQuery vs queryReport — **아래에서 확정**)
- GH Actions matrix 구성 (single job vs parallel)
- Rollback docs 포맷 (md vs runbook.sh)

### Deferred Ideas (OUT OF SCOPE)

- auto-route Kling → Veo 자동화 (수동 `--use-veo` 플래그만 유지)
- D091-DEF-02 #4 wiki rename (`remotion_kling_stack.md` → `remotion_i2v_stack.md`): D-2 Lock 기간 내 금지
- NEG_PROMPT 하드코드 재검토 (KlingI2VAdapter, 원칙 2 충돌)
- remotion_src_raw/ 40 파일 integration: Phase 10 batch window 이후
- Typecast voice_discovery 확장 (D091-DEF-02 #8)

## Project Constraints (from CLAUDE.md)

**도메인 절대 규칙 8종** (Plan 설계 시 위반 불가):

1. `skip_gates=True` 금지 — `pre_tool_use.py` regex 차단 (deprecated_patterns.json `skip_gates\s*=`)
2. `TODO(next-session)` 금지 — `pre_tool_use.py` regex 차단
3. try-except 침묵 폴백 금지 — 명시적 `raise` + GATE 기록 필수
4. T2V 금지 — I2V only (Anchor Frame 강제)
5. Selenium 업로드 영구 금지 — YouTube Data API v3 공식만
6. `shorts_naberal` 원본 수정 금지 — Harvest는 `.preserved/harvested/` 읽기 전용
7. K-pop 트렌드 음원 직접 사용 금지 — KOMCA + Content ID strike
8. 주 3~4편 페이스 준수 — 48시간+ 랜덤 간격 + 한국 피크 시간

**추가 Phase 10 에 특유한 구속**:
- 모든 Claude 호출 `subprocess.run(["claude", "--print", ...])` 경로 — `anthropic` Python SDK 직접 호출 영구 금지, `ANTHROPIC_API_KEY` 등록 영구 금지 (memory: `project_claude_code_max_no_api_key.md`)
- 모든 신규 Python = `uv` + `ruff` + `mypy strict` 호환
- `FAILURES.md` 는 `check_failures_append_only` hook 강제 — append 만 가능 (Write 시 old content 가 strict prefix 여야 함)
- `SKILL.md` 수정 시 `backup_skill_before_write` hook 이 `SKILL_HISTORY/<skill>/v<timestamp>.md.bak` 자동 백업

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FAIL-04 | Phase 10 첫 1~2개월 SKILL patch 전면 금지 — 데이터 수집만 | Plan 1 (skill_patch_counter.py) — git log grep 으로 물리 검증. 금지 경로 locked (4 paths). |
| KPI-01 | YouTube Analytics 일일 수집 cron (retention/CTR/avg view) | Plan 3 (fetch_kpi.py) — `reports.query` 엔드포인트 + `yt-analytics.readonly` scope 확정. Plan 4 (GH Actions) cron entry. |
| KPI-02 | 월 1회 `wiki/shorts/kpi_log.md` 자동 생성 | Plan 3 (monthly_aggregate.py) — 기존 `wiki/kpi/kpi_log.md` Part B 테이블에 월별 row 추가. `aggregate_patterns.py` 의 30일 집계 로직 재사용. |
| KPI-03 | Auto Research Loop — 성공 패턴 → NotebookLM RAG 업데이트 | Plan 6 (monthly_update.py) — NotebookLM skill 의 `notebook_manager.py add` + `ask_question.py` CLI 재사용. 상위 3 영상 selection metric 아래 확정. |
| KPI-04 | 다음 달 Producer 입력에 KPI 반영 (DF-4 기본 틀) | Plan 6 — Producer prompt template 에 `previous_month_kpi` context block 주입. 구현 메커니즘 아래 확정. |
| AUDIT-01 | `session_start.py` 매 세션 자동 감사 (점수 ≥ 80) | Plan 5 (scripts/session_start.py) — **주의: `.claude/hooks/session_start.py` 와 다름**. 이건 30일 rolling 집계 스크립트. Hook 출력 로그 persistence 아래 확정. |
| AUDIT-02 | `harness-audit` 월 1회 통합 감사 | **이미 완료** (Phase 7 — `scripts/validate/harness_audit.py` 280줄). Plan 4 scheduler 에서 재호출만. |
| AUDIT-03 | `drift_scan.py` 주 1회 `deprecated_patterns.json` 전수 스캔 → A급 drift 0 유지 | Plan 2 — harness 공용 `drift_scan.py` import 기반. `deprecated_patterns.json` 의 `grade` 필드 사용 (아래 확정). |
| AUDIT-04 | A급 drift 발견 시 Phase 차단 | Plan 2 — `.planning/STATE.md` 의 frontmatter 에 `phase_lock: true` + `block_reason` 필드 추가. gh issue auto-create. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `google-api-python-client` | 2.x (2026) | YouTube Data/Analytics API v3/v2 | 공식 SDK. Phase 8 oauth.py 이미 사용 중 — 의존성 추가 불필요 |
| `google-auth-oauthlib` | 1.x | OAuth 2.0 flow | Phase 8 `scripts/publisher/oauth.py` 이미 사용. Scope 만 추가 (`yt-analytics.readonly`) |
| `gh` (GitHub CLI) | 2.45+ | A급 drift 시 issue 자동 생성 | 공식 CLI. `gh issue create --title ... --body-file - --label` 으로 non-interactive 생성 가능 |
| stdlib `subprocess` | 3.11+ | git log + claude CLI + gh CLI 호출 | Phase 6 `aggregate_patterns.py` + Phase 8 smoke 이미 사용 |
| stdlib `zoneinfo` | 3.9+ | KST/UTC 변환 (Asia/Seoul) | `kst_window.py` 이미 사용. pytz 금지 |
| stdlib `json` + `pathlib` | 3.11+ | JSONL 로그 persistence (session audit) | Hook 출력 축적용 |
| harness `drift_scan.py` | n/a (path ref) | A/B/C grade drift 스캐너 | `sys.path.insert(0, "../../harness/scripts")` 로 import. 복사 금지 (auto-sync) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `send-mail` / `Send-MailMessage` (PowerShell) | Windows built-in | 로컬 scheduler 실패 → email | PowerShell `Send-MailMessage -SmtpServer smtp.gmail.com -Port 587 -UseSsl` (gmail app password) |
| `mermaid-cli` (optional) | 10.x | Trajectory graph 렌더 | Plan 7 (선택적). GitHub native render 가 이미 Mermaid 지원하므로 실제 렌더 불필요 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `gh issue create` CLI | GitHub REST API via `requests` | gh CLI 가 auth token 자동 처리. REST 는 `GITHUB_TOKEN` 별도 설정 필요 |
| stdlib `subprocess.run(["git","log",...])` | `gitpython` 라이브러리 | 불필요 의존성. git log 한 번 호출에 gitpython 과잉 |
| PowerShell `Send-MailMessage` | Python `smtplib` | 양자 모두 유효. Scheduler 가 PowerShell 이므로 PowerShell 쪽이 단일 스크립트로 끝남 |
| 월별 aggregate 용 pandas | stdlib `csv` + `collections.Counter` | Phase 6 `aggregate_patterns.py` 가 이미 stdlib-only — 일관성 위해 pandas 도입 불필요 |

**Installation (Phase 8 에서 이미 설치됨 — 추가 작업 없음):**
```bash
# 이미 존재:
uv pip install google-api-python-client google-auth-oauthlib

# 신규 추가 불필요 — 모두 stdlib 또는 Phase 8 dep 재사용
```

**Version verification (2026-04-20 확인):**
- `google-api-python-client` 2.x — oauth.py + youtube_uploader.py 에서 동작 확인됨 (Phase 8 163/163 tests green)
- GitHub CLI `gh` — Phase 8 REMOTE-01 에서 이미 사용 (`github.com/kanno321-create/shorts_studio` PRIVATE repo 생성)

## Architecture Patterns

### Recommended Project Structure
```
scripts/
├── audit/                          # Plan 1 + Plan 2 신규
│   ├── __init__.py
│   ├── skill_patch_counter.py      # SC#1 / FAIL-04
│   └── drift_scan.py               # SC#4 / AUDIT-03,04 (harness wrapper)
├── analytics/                      # Plan 3 신규
│   ├── __init__.py
│   ├── fetch_kpi.py                # KPI-01 daily
│   ├── monthly_aggregate.py        # KPI-02 monthly
│   └── trajectory_append.py        # SC#6 / Plan 7
├── research_loop/                  # Plan 6 신규
│   ├── __init__.py
│   └── monthly_update.py           # KPI-03, KPI-04
├── schedule/                       # Plan 4 신규
│   ├── windows_tasks.ps1           # Windows Task Scheduler register
│   └── notify_failure.py           # email + FAILURES.md append
├── session_start.py                # Plan 5 (NOT .claude/hooks/session_start.py)
├── rollback/                       # Plan 8 신규
│   └── stop_scheduler.py
├── publisher/                      # [existing] re-use
├── failures/                       # [existing] re-use
└── validate/                       # [existing] harness_audit 재호출

.github/workflows/                  # Plan 4 신규
├── analytics-daily.yml
├── drift-scan-weekly.yml
└── skill-patch-count-monthly.yml

reports/                            # Plan 1 월간 리포트 축적 (신규 폴더 — STRUCTURE.md 확인 필요)
└── skill_patch_count_YYYY-MM.md

logs/                               # Plan 5 세션 감사 JSONL 축적
└── session_audit.jsonl             # gitignored (개인 감사 기록)

wiki/ypp/                           # [existing scaffold] 확장
├── MOC.md                          # 이미 있음
├── entry_conditions.md             # 이미 있음
└── trajectory.md                   # Plan 7 신규

wiki/shorts/kpi/
└── kpi_log.md                      # [existing] Part B 월별 row 추가

.planning/phases/10-sustained-operations/
├── 10-CONTEXT.md                   # 이미 있음
├── 10-RESEARCH.md                  # 이 파일
├── ROLLBACK.md                     # Plan 8 신규
├── 10-PLAN-01-skill-patch-counter.md
├── 10-PLAN-02-drift-scan.md
├── ... (8 plans)
```

### Pattern 1: Scheduler-Driven Continuous Assertion (Phase 10 핵심)

**What:** 전통적 phase verification 대신 **cron 실행 결과가 pass/fail** 로 동작. 각 SC 가 monthly check 로 대체됨.

**When to use:** 영구 지속 phase. 단일 "verified" 상태 없음.

**Example:**
```python
# Source: harness scripts/drift_scan.py + 신규 확장
# scripts/audit/drift_scan.py
import sys
from pathlib import Path

HARNESS_PATH = Path(__file__).resolve().parents[3] / "harness" / "scripts"
sys.path.insert(0, str(HARNESS_PATH))

from drift_scan import load_patterns, scan_studio, write_conflict_map, append_history

def main() -> int:
    studio_root = Path(__file__).resolve().parents[2]
    pattern_defs = load_patterns(studio_root)
    findings = scan_studio(studio_root, pattern_defs)

    # A급 발견 시 Phase 차단
    a_grade_count = sum(
        len(findings.get(p["name"], []))
        for p in pattern_defs
        if p.get("grade", "C").upper() == "A"
    )

    output = studio_root / ".planning" / "codebase" / "CONFLICT_MAP.md"
    write_conflict_map(studio_root, findings, pattern_defs, output)
    append_history(studio_root, findings)

    if a_grade_count > 0:
        # AUDIT-04: Phase 차단 신호
        set_phase_lock(studio_root, reason=f"A급 drift {a_grade_count}건", findings=findings)
        create_github_issue(a_grade_count, findings)
        return 1   # GH Actions 에서 실패 → email 알림 자동 발송
    return 0
```

### Pattern 2: GH Actions cron with KST timezone (2025+)

**What:** `timezone:` 필드로 KST 직접 지정 (2025-08 GH Actions 에 추가됨)

**Example:**
```yaml
# .github/workflows/analytics-daily.yml
name: analytics-daily
on:
  schedule:
    - cron: '0 5 * * *'     # 05:00 KST = 20:00 UTC 전일 (timezone: 미지원 환경 호환)
      # NOTE: timezone 필드는 2025-08 신규. 전체 호환성 위해 UTC 로 변환 표기 권장.
      # timezone: 'Asia/Seoul'   # 선택적 — 2026 기준 GA 에 도달했으나 cron 지연 이슈는 동일
  workflow_dispatch:         # 수동 trigger 가능 (테스트용)

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          pip install google-api-python-client google-auth-oauthlib
      - name: Fetch KPI
        env:
          YOUTUBE_TOKEN_JSON: ${{ secrets.YOUTUBE_TOKEN_JSON }}
          YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
        run: |
          echo "$YOUTUBE_CLIENT_SECRET" > config/client_secret.json
          echo "$YOUTUBE_TOKEN_JSON" > config/youtube_token.json
          python scripts/analytics/fetch_kpi.py
      - name: Commit KPI log
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add wiki/shorts/kpi/kpi_log.md
          git commit -m "chore(kpi): daily fetch $(date -u +%Y-%m-%d)" || echo "nothing to commit"
          git push
```

**Confidence:** MEDIUM-HIGH — `timezone:` 필드 2025-08 도입 확인. cron 실행 지연 (10~30분) 은 known GH Actions 제약 (업스트림 이슈 #156282). 정확 시각 필요 시 `workflow_dispatch` 수동 trigger 권장.

### Pattern 3: Windows Task Scheduler via PowerShell (ScheduledTasks module)

**What:** PowerShell cmdlet 4 개 조합 — `New-ScheduledTaskAction` + `New-ScheduledTaskTrigger` + `New-ScheduledTaskSettingsSet` + `Register-ScheduledTask`

**Example:**
```powershell
# scripts/schedule/windows_tasks.ps1 (관리자 권한 실행 필요)

$scriptRoot = "C:\Users\PC\Desktop\naberal_group\studios\shorts"

# 1. 영상 생성 파이프라인 (주 3~4편, publish_lock.py + kst_window.py 자체 내부 gate 보유)
$action1 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"cd $scriptRoot; python -m scripts.orchestrator.shorts_pipeline`""
$trigger1 = New-ScheduledTaskTrigger -Daily -At "20:30"   # KST 피크 진입 30분 전 (업로드는 20-23 window)
Register-ScheduledTask -TaskName "ShortsStudio_Pipeline" `
    -Action $action1 -Trigger $trigger1 `
    -RunLevel Highest -User "$env:USERNAME"

# 2. YouTube 업로드 (oauth.py + youtube_uploader.py 가 publish_lock + window 내부 강제)
$action2 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"cd $scriptRoot; python -m scripts.publisher.smoke_test --production`""
$trigger2 = New-ScheduledTaskTrigger -Daily -At "20:45"
Register-ScheduledTask -TaskName "ShortsStudio_Upload" `
    -Action $action2 -Trigger $trigger2
```

**실패 알림 PowerShell SMTP:**
```powershell
# scripts/schedule/notify_failure.ps1
$creds = Get-Credential   # 또는 ConvertFrom-SecureString 으로 저장
Send-MailMessage `
    -From "shorts-studio@example.com" `
    -To "kanno3@naver.com" `
    -Subject "[shorts_studio] Windows Task FAILURE — $TaskName" `
    -Body $ErrorMessage `
    -SmtpServer "smtp.naver.com" -Port 587 -UseSsl -Credential $creds
```

### Anti-Patterns to Avoid

- **try-except with pass 내부에 드리프트 숨기기**: `pre_tool_use.py` deprecated_patterns.json 의 `try\s*:[^\n]*\n\s+pass\s*$` 가 차단. 명시적 raise + FAILURES.md append.
- **`deprecated_patterns.json` 에 grade 필드 추가 시 기존 8 entries 수정**: `check_failures_append_only` hook 은 FAILURES.md 만 enforce 하지만, deprecated_patterns.json 자체 수정은 허용. 다만 모든 기존 entry 에 `grade: "A"` 추가 시 Phase 5 regression tests 가 영향받을 수 있음 — 신규 entry 에만 grade 필드 추가하고, 기본값을 harness drift_scan.py 처럼 `"C"` 로 두는 방식 권장.
- **gh CLI issue create 를 interactive mode 로**: CI 환경에서는 `--title` + `--body-file -` (stdin 전달) 으로 non-interactive 강제. `GITHUB_TOKEN` env var 필요.
- **session_start.py 출력을 stdout 에만 의존**: 세션마다 로그 사라짐. 반드시 JSONL append (`logs/session_audit.jsonl` gitignored) 로 persistence 확보.
- **pandas 로 월별 집계**: Phase 6 `aggregate_patterns.py` 는 stdlib-only 로 확정. 일관성 유지.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git log 파싱 | 커스텀 git log 파서 | `subprocess.run(["git", "log", "--since=...", "--name-only", "--pretty=format:%H|%s"])` + `str.splitlines()` | Phase 6 `aggregate_patterns.py` 이미 subprocess 패턴. 추가 dep 불필요 |
| YouTube OAuth | OAuth 재구현 | `scripts/publisher/oauth.py::get_credentials()` | 이미 검증됨 (Phase 8 PUB-03). Scope 만 `yt-analytics.readonly` 추가 |
| drift 스캐너 | shorts_studio 전용 drift_scan | harness `scripts/drift_scan.py` sys.path import | Auto-sync. 복사 시 harness 업데이트 놓침 |
| 48h publish lock | 스케줄 기반 분산 (cron) 로 시간 제어 | `publish_lock.py::assert_can_publish()` 그대로 호출 | Phase 8 에서 atomic write + timezone-aware 검증 완료 |
| KST window check | datetime.now() + 매직 hour 비교 | `kst_window.py::assert_in_window()` | zoneinfo 사용 확정 (pytz 금지) |
| FAILURES 패턴 집계 | Counter 로직 재구현 | `scripts/failures/aggregate_patterns.py::aggregate()` + `normalize_pattern_key()` | sha256[:12] collision-safe 48-bit 이미 구현 |
| session 감사 점수 | 자체 점수 계산 | `scripts/validate/harness_audit.py::run_audit()` returns `(score, violations, warnings)` | 점수 ≥80 threshold 이미 구현 |
| NotebookLM 조회 | 자체 RAG 스크래퍼 | `shorts_naberal/.claude/skills/notebooklm/scripts/ask_question.py` via `run.py` wrapper | browser automation + auth persistence 이미 구현 |
| Email 알림 | Python smtplib boilerplate | PowerShell `Send-MailMessage` (Windows) + GH Actions built-in email notification | GH Actions 는 workflow 실패 시 repo owner 에게 자동 email (별도 코드 불필요) |

**Key insight:** Phase 10 의 8 Plan 모두 기존 모듈 호출 + 얇은 wrapper 조합이다. **새 코드 < 200줄/Plan** 목표. 넘어가면 설계 재검토 시그널.

## Runtime State Inventory

Phase 10 은 rename/refactor/migration 이 **아닌** 신규 기능 phase 이지만, scheduler 등록 자체가 OS-registered state 이므로 다음 세부 사항 기록:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `publish_lock.json` (Phase 8 에서 이미 존재, `.planning/publish_lock.json` gitignored). `logs/session_audit.jsonl` (Plan 5 신규, gitignored). `reports/skill_patch_count_YYYY-MM.md` (Plan 1 월간 리포트, git 추적). `wiki/ypp/trajectory.md` + `wiki/shorts/kpi/kpi_log.md` 월별 append. | 신규 파일 경로는 STRUCTURE.md whitelist 확인 필수 (`reports/` + `logs/` 추가 or 기존 whitelist 재활용) |
| Live service config | **GitHub Actions workflows** — 3개 yml 파일이 `.github/workflows/` 에 등록. Private repo 이므로 secrets 관리: `YOUTUBE_TOKEN_JSON`, `YOUTUBE_CLIENT_SECRET`. **NotebookLM library** — shorts_naberal skill 쪽 `data/library.json` 에 `naberal-shorts-channel-bible` 엔트리 (Phase 6 에서 추가됨). | GH secrets 수동 등록 (대표님 action). NotebookLM notebook URL 은 D-04-01 deferred 상태 — Plan 6 시작 시 대표님께 URL 획득 후 `notebook_manager.py add` 1회 실행 |
| OS-registered state | **Windows Task Scheduler 3개 task** (Plan 4): `ShortsStudio_Pipeline`, `ShortsStudio_Upload`, `ShortsStudio_NotifyFailure`. 대표님 로컬 PC 종속. | 설치 스크립트 + 제거 스크립트 양방 필수 (Plan 8 rollback docs). Task 이름은 Plan 2 의 drift scan 이 A급 drift 감지 시 `schtasks /End /TN "ShortsStudio_*"` 로 자동 중단 옵션 고려 |
| Secrets/env vars | `.env` 에 `TYPECAST_API_KEY`, `KLING_ACCESS_KEY`, `KLING_SECRET_KEY`, `RUNWAY_API_KEY`, `ELEVENLABS_API_KEY`, `NANO_BANANA_API_KEY`, `GEMINI_API_KEY` (기존, `reference_api_keys_location.md` 참조). Phase 10 신규: `GMAIL_APP_PASSWORD` 또는 `NAVER_SMTP_PASSWORD` (로컬 scheduler 실패 알림 용) | `.env.example` 업데이트. `CLAUDE.md` Session Init Step 6 이미 `.env` 존재 확인 — 신규 key 는 대표님께 1회 제공 요청 |
| Build artifacts / installed packages | 없음 — Phase 10 은 Python 패키지 설치 신규 없음. 기존 `uv pip install google-api-python-client google-auth-oauthlib` 재사용 | None |

**The canonical question:** *Phase 10 실행 후 어디에 상태가 고착되는가?* → (1) Windows Task Scheduler 3개 task + (2) GH Actions 3개 workflow + (3) GH secrets 2개. 이 5곳이 rollback 대상.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | 전체 | ✓ (Phase 1-9 사용) | 3.11.x | — |
| `google-api-python-client` | Plan 3 | ✓ (Phase 8 설치) | 2.x | — |
| `google-auth-oauthlib` | Plan 3 | ✓ (Phase 8 설치) | 1.x | — |
| GitHub CLI (`gh`) | Plan 2 (issue auto-create) | ✓ (Phase 8 REMOTE-01 사용) | 2.45+ | REST API via curl (`GITHUB_TOKEN` 필수) |
| git | Plan 1, Plan 4, 전반 | ✓ | 2.x | — |
| PowerShell 7+ | Plan 4 Windows Task Scheduler | ✓ (Windows 11 built-in) | 7.x | `schtasks.exe` CLI (legacy, 동일 기능 가능) |
| NotebookLM skill (shorts_naberal) | Plan 6 | ✓ (`C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/`) | n/a | Plan 6 skip + FAILURES append (SC#5 미충족 시 수동 월 1회) |
| Claude CLI (`claude --print`) | Plan 6 Producer invocation | ✓ (Phase 9.1 invokers.py 사용) | Claude Code Max | — (ANTHROPIC_API_KEY 영구 금지) |
| ffmpeg | (Phase 10 자체는 불사용, 파이프라인은 사용) | ✓ | 6+ | — |
| SMTP (Gmail/Naver) | Plan 4 실패 알림 | ✗ (대표님 app password 미설정) | — | GH Actions built-in email 만 사용 (Windows 실패는 FAILURES.md append only) |

**Missing dependencies with no fallback:**
- 없음 — 모든 core deps 는 Phase 1-9 설치 확인

**Missing dependencies with fallback:**
- SMTP app password: Plan 4 에서 로컬 email 알림은 선택적. GH Actions email + FAILURES.md append 이중 safety net 으로 충분

## Open Questions (Pre-Answered for Each Plan)

### Plan 1: SC#1 skill_patch_counter

1. **`git log --since` 정확한 플래그 조합**
   - **Answer:** `git log --since="2026-04-20" --until="2026-06-20" --name-only --pretty=format:"%H|%aI|%s"` — commit hash + author date ISO + subject + 파일 리스트
   - **Confidence:** HIGH — git 공식 문서 + Phase 6 subprocess 패턴 확인
   - **Implementation sketch:**
   ```python
   import subprocess
   result = subprocess.run(
       ["git", "log",
        f"--since={D2_LOCK_START}",
        f"--until={D2_LOCK_END}",
        "--name-only",
        "--pretty=format:---COMMIT---%n%H|%aI|%s"],
       capture_output=True, text=True, encoding="utf-8", check=True,
   )
   ```

2. **금지 경로 regex (glob → regex 변환)**
   - **Answer:** 4 금지 경로 → regex 패턴
   ```python
   FORBIDDEN_PATTERNS = [
       re.compile(r"^\.claude/agents/.+/SKILL\.md$"),
       re.compile(r"^\.claude/skills/.+/SKILL\.md$"),
       re.compile(r"^\.claude/hooks/[^/]+\.py$"),
       re.compile(r"^CLAUDE\.md$"),
   ]
   ```
   - **Confidence:** HIGH — `git log --name-only` 의 출력은 항상 `.claude/agents/inspectors/ins-mosaic/SKILL.md` 같은 **forward-slash POSIX 경로** (Windows 에서도 동일)

3. **월간 리포트 포맷 (markdown table)**
   - **Answer:** `reports/skill_patch_count_YYYY-MM.md` — count 테이블 + 위반 엔트리 상세
   - **Format:**
   ```markdown
   # D-2 Lock Skill Patch Counter — 2026-04

   **Lock period:** 2026-04-20 ~ 2026-06-20
   **Report generated:** 2026-04-30T09:00:00+09:00 KST
   **Violation count:** 0 ✅ (목표: 0)

   ## Violations (상세)
   *없음.*

   ## Scan coverage
   - Commits scanned: 12 (2026-04-20 이후)
   - Forbidden paths checked: 4
   ```
   - count > 0 시 **FAILURES.md append** 트리거 (F-D2-XX 카테고리)
   - **Confidence:** HIGH — CONTEXT Plan 1 spec + Phase 6 FAILURES 규약 재사용

4. **`aggregate_patterns.py` 재사용 가능 헬퍼 여부**
   - **Answer:** 직접 재사용 없음. `aggregate_patterns.py` 는 FAILURES.md 파싱용 (`ENTRY_RE = re.compile(r"^### (FAIL-[\w]+):")`). `skill_patch_counter.py` 는 git log 파싱이라 별도 로직.
   - **그러나 design pattern 재사용**: (1) stdlib-only (2) argparse + `--output` (3) `sys.stdout.reconfigure(encoding="utf-8")` Windows cp949 가드 (4) JSON + markdown dual output
   - **Confidence:** HIGH — 소스 코드 전수 확인

### Plan 2: SC#4 drift_scan + AUDIT-04 Phase 차단

1. **harness drift_scan.py public API 시그니처**
   - **Answer:** 4 함수
   ```python
   # from C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py
   def load_patterns(studio_root: Path) -> list[dict]
   def scan_studio(studio_root: Path, pattern_defs: list[dict]) -> dict
       # returns: {pattern_name: [{"file": str, "line": int, "match": str}, ...]}
   def write_conflict_map(studio_root: Path, findings: dict, pattern_defs: list[dict], output: Path) -> None
   def append_history(studio_root: Path, findings: dict) -> None
       # appends to .planning/codebase/CONFLICT_HISTORY.jsonl
   ```
   - **Confidence:** HIGH — 소스 코드 line 14-131 읽음

2. **A급/B급 drift 분류 기준 (deprecated_patterns.json 스키마 확장)**
   - **Answer:** 현재 shorts_studio `.claude/deprecated_patterns.json` 은 `{regex, reason}` 만 있음. harness drift_scan.py 는 `grade: "A"|"B"|"C"` 필드를 찾지만 없으면 default `"C"`. **Plan 2 에서 8 기존 entries 에 grade 필드 추가**:
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
   - **주의**: Phase 5/6 regression tests 가 이 json 을 읽을 수 있음. Plan 2 전 `grep -r "deprecated_patterns.json" tests/` 로 영향 분석 필수.
   - **Confidence:** HIGH — harness drift_scan.py line 90-94 `grade` 기본값 "C" 확인

3. **`.planning/STATE.md` 에 Phase 차단 플래그 박는 방식 (기존 GSD state machine 호환)**
   - **Answer:** Frontmatter 에 `phase_lock` 필드 추가 (기존 `gsd_state_version`, `milestone`, `status`, `last_updated`, `progress` 외에). `phase_lock: true` + `block_reason: "..."` 세팅.
   ```yaml
   ---
   gsd_state_version: 1.0
   milestone: v1.0.1
   milestone_name: milestone
   status: executing
   last_updated: "2026-04-20T13:00:00.000Z"
   phase_lock: true                # 신규
   block_reason: "A급 drift 3건 — 2026-04-27 drift_scan"   # 신규
   block_since: "2026-04-27T09:00:00+09:00"               # 신규
   progress: ...
   ---
   ```
   - 해제 시 3 필드 delete (or `phase_lock: false`). GSD 자체는 이 필드 읽지 않음 — drift_scan.py + session_start.py 만 해석.
   - GSD 커맨드 (`/gsd:execute-phase`, `/gsd:verify-work`) 가 `phase_lock: true` 일 때 차단하도록 Plan 2 에서 하드 가드 추가 option — **단, GSD 커맨드 수정은 D-2 Lock 경로 (.claude/hooks/) 에 해당하지 않으므로 허용**. 다만 skill 수정이 아닌 GSD extension 이므로 회색지대 → Plan 2 는 session_start.py hook 출력에만 의존하고, GSD 가 사용자를 시각적으로 경고하도록 함.
   - **Confidence:** MEDIUM-HIGH — STATE.md frontmatter 포맷 확인 (line 1-13). GSD 가 extra field 를 ignore 하는 것은 YAML 표준 동작으로 추정 (실측 필요 시 Plan 2 Wave 0 smoke 에서 1회).

4. **GitHub issue 자동 생성 (`gh issue create`)**
   - **Answer:** non-interactive 모드 명령
   ```bash
   gh issue create \
     --title "[AUDIT-04] A급 drift ${count}건 — Phase 차단" \
     --body-file - \
     --label "drift,critical,phase-10" \
     --assignee "@me" \
     << EOF
   Detected by drift_scan.py at ${timestamp}

   ## A급 findings
   ${details}

   ## Phase lock status
   STATE.md phase_lock: true
   block_reason: ${reason}

   ## Resolution path
   1. A급 drift 해결 (코드 수정)
   2. drift_scan.py 재실행 → A급 0건 확인
   3. STATE.md 에서 phase_lock: false 로 flip
   4. 본 issue close
   EOF
   ```
   - **환경변수 필수**: GH Actions 에서는 `GITHUB_TOKEN` 이 자동 주입 (`actions/checkout@v4` 가 `permissions.issues: write` 요구). 로컬 실행은 `gh auth login` 필요 (Phase 8 REMOTE-01 에서 이미 인증 완료).
   - **Confidence:** HIGH — gh CLI 공식 문서 + Phase 8 `github_remote.py` 선례

### Plan 3: SC#2 KPI fetch + aggregate

1. **YouTube Analytics API v2 엔드포인트**
   - **Answer:** `GET https://youtubeanalytics.googleapis.com/v2/reports` (Reports: Query 메서드). `google-api-python-client` 에서는 `build("youtubeAnalytics", "v2", credentials=...)` → `.reports().query(...)`.
   - `reportsQuery` 와 `queryReport` 는 별개 — 대기업용 Reporting API 는 `reportsQuery` (bulk), 채널용 Analytics API 는 단일 `.reports().query()`. 이 프로젝트는 Analytics API (channel) 사용.
   - **Confidence:** HIGH — 공식 docs `developers.google.com/youtube/analytics/reference/reports/query`

2. **필요 scope + Phase 8 oauth.py scope 에 추가 필요**
   - **Answer:** `https://www.googleapis.com/auth/yt-analytics.readonly` 추가 필요.
   - 현재 `scripts/publisher/oauth.py::SCOPES` = 2개 (`youtube.upload`, `youtube.force-ssl`). Plan 3 는 **3번째 scope 추가**:
   ```python
   SCOPES = [
       "https://www.googleapis.com/auth/youtube.upload",
       "https://www.googleapis.com/auth/youtube.force-ssl",
       "https://www.googleapis.com/auth/yt-analytics.readonly",   # Plan 3 신규
   ]
   ```
   - **주의**: scope 변경 시 기존 `config/youtube_token.json` 재발급 필요 (old scope 의 refresh_token 은 new scope 에 access 불가). Plan 3 Wave 0 에서 `get_credentials()` 1회 호출 → 브라우저 재인증 → 새 token 저장.
   - **Confidence:** HIGH — OAuth 2.0 표준 + oauth.py line 28-31 확인

3. **Rate limit / Quota**
   - **Answer:** YouTube Analytics API v2 는 **YouTube Data API v3 와 별도 quota**. 기본 약 **720 requests/minute** (Google 공식), per-request cost 1 unit. 일일 quota 는 프로젝트별 다름 — Google Cloud Console 에서 확인 가능. 16 영상/월 × 매일 fetch = 월 500 호출 수준 → quota 걱정 없음.
   - **Confidence:** MEDIUM — 정확한 daily quota 는 Cloud Console 확인 필요. Plan 3 Wave 0 에서 1회 호출 후 API response 의 `X-RateLimit-*` 헤더 검증.

4. **pandas vs stdlib csv — 월간 집계**
   - **Answer:** **stdlib 선택**. Phase 6 `aggregate_patterns.py` 가 `collections.Counter` + `csv` 로 충분히 동작. pandas 도입은 Plan 3 + Plan 6 + Plan 7 3개 Plan 에 추가 dep → ROI 음의.
   - **월간 집계 로직**:
   ```python
   import csv
   from collections import defaultdict
   from pathlib import Path

   def aggregate_month(daily_csv_dir: Path, year_month: str) -> dict:
       """Aggregate daily KPI CSVs into monthly summary."""
       monthly = defaultdict(list)
       for daily in daily_csv_dir.glob(f"kpi_{year_month}-*.csv"):
           with daily.open(encoding="utf-8") as f:
               for row in csv.DictReader(f):
                   monthly[row["video_id"]].append({
                       "retention_3s": float(row["retention_3s"]),
                       "completion_rate": float(row["completion_rate"]),
                       "avg_view_sec": float(row["avg_view_sec"]),
                   })
       # average per video, then channel-wide
       return {vid: mean_metrics(samples) for vid, samples in monthly.items()}
   ```
   - **Confidence:** HIGH — Phase 6 선례

### Plan 4: Scheduler (하이브리드)

1. **GH Actions cron YAML + KST/UTC 변환**
   - **Answer:** UTC 표기 권장 (timezone 필드는 선택적).
   - KST → UTC: 9시간 빼기. KST 05:00 = UTC 20:00 전일. KST 09:00 = UTC 00:00. KST 23:00 = UTC 14:00.
   - **Gotcha**: GH Actions cron 은 ~10-30분 지연 가능 (공식 known issue #156282). 정확한 시각 필요 시 `workflow_dispatch` 수동 trigger 권장.
   - **Confidence:** HIGH — GitHub 공식 문서 + 2025 timezone 필드 추가 확인

2. **secrets. prefix + least-privilege (analytics-only key 분리)**
   - **Answer:** 현재 `scripts/publisher/oauth.py` 는 3 scope 통합 token 사용 예정. Analytics-only 별도 OAuth 2.0 client 분리는 **과잉** (단일 user 프로젝트). 기존 token 에 scope 3개 추가로 충분.
   - GH Secrets 2개만 등록:
     - `YOUTUBE_CLIENT_SECRET` (config/client_secret.json 전체 내용)
     - `YOUTUBE_TOKEN_JSON` (config/youtube_token.json 전체 내용, 새 scope 재발급 후)
   - **Confidence:** HIGH — OAuth 2.0 best practice + 1인 프로젝트 규모 적합

3. **Windows Task Scheduler schtasks.exe vs PowerShell New-ScheduledTask**
   - **Answer:** **PowerShell New-ScheduledTask 권장** (cmdlet 조합, 가독성 우위). schtasks.exe 는 legacy, 단축 명령에만 사용.
   - PowerShell 예제는 위 Pattern 3 참조.
   - **Confidence:** HIGH — Microsoft Learn 공식 docs 확인

4. **email 알림 3 채널**
   - **GH Actions built-in email:** workflow 실패 시 repo owner 의 notification 설정에 따라 자동 발송. 별도 코드 불필요. 단, owner 가 `kanno3@naver.com` 으로 GitHub notification settings 에서 설정 필요 (대표님 action).
   - **PowerShell Send-MailMessage SMTP:**
     ```powershell
     Send-MailMessage -From "shorts-studio@example.com" -To "kanno3@naver.com" `
       -Subject "..." -Body "..." -SmtpServer "smtp.gmail.com" -Port 587 -UseSsl `
       -Credential (New-Object System.Management.Automation.PSCredential("user", (ConvertTo-SecureString "apppw" -AsPlainText -Force)))
     ```
     - Gmail App Password 필수 (일반 비밀번호 불가, 2FA enabled 계정만).
   - **FAILURES.md append:** `check_failures_append_only` hook 과 **호환** — hook 은 Write/Edit 의 `old_string` 만 검증. append 는 `existing content + new entry` 를 strict prefix 만족 → 통과. Phase 6 에서 증명된 패턴.
   - **Confidence:** HIGH — `pre_tool_use.py` line 160-210 전수 확인

### Plan 5: SC#3 session audit 30-day rolling

1. **`.claude/hooks/session_start.py` 출력 persistence 방식**
   - **Answer:** 현재 hook 은 `print(json.dumps({"context": context_text}))` 만 stdout 으로. Plan 5 에서 **hook 은 건드리지 않고** (D-2 Lock 경로 — `.claude/hooks/*.py` 금지), 별도 `scripts/session_start.py` 가 다음을 수행:
     1. `harness_audit.py --json-out logs/audit_$(date +%Y%m%d_%H%M%S).json` 실행
     2. 출력 JSON 을 `logs/session_audit.jsonl` (한 줄 = 한 세션) append
     3. 최근 30일 record 읽어 score 평균 계산
     4. 평균 < 80 → `FAILURES.md` append (F-AUDIT-XX)
   - **주의**: hook 수정 금지이지만, hook 이 이미 `harness_audit` 과 별도로 deprecated 패턴 스캔 등 내장. Plan 5 의 `scripts/session_start.py` 는 hook 을 보완하는 **외부 집계 스크립트**. 혼동 방지를 위해 파일 이름 `scripts/audit/session_audit_rollup.py` 로 rename 권고.
   - **Confidence:** HIGH — harness_audit.py `--json-out` 옵션 확인 (line 278-285)

2. **jsonl append 대안 (SQLite vs 로그 파일 + rotation)**
   - **Answer:** **jsonl 선택**. SQLite 는 과잉. Rotation 은 월 1회 압축:
   ```python
   # Plan 5 월 1회 rotation (cron)
   from datetime import datetime, timedelta
   cutoff = datetime.now() - timedelta(days=60)
   archive_records_older_than(cutoff, "logs/session_audit_2026-02.jsonl.gz")
   ```
   - `logs/session_audit.jsonl` 은 gitignored (개인 감사 기록). STRUCTURE.md whitelist 에 `logs/` 추가 필요.
   - **Confidence:** HIGH — stdlib json + pathlib 로 충분

3. **30일 rolling 평균 계산 (KST 기준)**
   - **Answer:**
   ```python
   from datetime import datetime, timedelta
   from zoneinfo import ZoneInfo
   KST = ZoneInfo("Asia/Seoul")

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
           return 100.0   # 데이터 없으면 통과 (신규 스튜디오 정상)
       return sum(scores) / len(scores)
   ```
   - **Confidence:** HIGH — zoneinfo 이미 Phase 8 에서 사용

4. **점수 미달 알림 경로**
   - **Answer:** (1) `FAILURES.md` append F-AUDIT-XX (2) stderr 경고 (3) Plan 4 scheduler 가 실행했으면 email 자동. (4) STATE.md 에 `phase_lock` 은 **세팅하지 않음** — 점수 < 80 은 warning 수준, drift_scan A급 과 다름 (AUDIT-04 는 drift 전용).

### Plan 6: SC#5 Auto Research Loop

1. **NotebookLM skill public API**
   - **Answer:** shorts_naberal 의 skill 은 **CLI wrapper 방식** (Python API 직접 import 불가). `scripts/run.py` 를 subprocess 로 호출:
   ```python
   # Plan 6 monthly_update.py
   NLM_SKILL = Path("C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm")

   def query_notebook(question: str, notebook_id: str) -> str:
       result = subprocess.run(
           [sys.executable, str(NLM_SKILL / "scripts/run.py"),
            "ask_question.py",
            "--question", question,
            "--notebook-id", notebook_id],
           cwd=NLM_SKILL, capture_output=True, text=True, encoding="utf-8",
       )
       return result.stdout

   def add_monthly_insight(markdown_content: str, notebook_id: str) -> None:
       # NOTE: NotebookLM 은 직접 add_source 가 API 로 불가. 대신 Google Drive 에 올린 후 수동 UI 추가.
       # 또는 기존 notebook 의 source 를 로컬 md 파일로 관리하고 수동 refresh 필요.
       # Plan 6 에서 자동화 한계: "상위 3 영상 요약 md 생성 → 대표님이 월 1회 NotebookLM UI 에 업로드" 패턴 권장
       pass
   ```
   - **제약**: NotebookLM 은 **source 추가가 UI 기반** (공식 API 미공개 2026-04). Plan 6 는 "md 파일 자동 생성 + 대표님 수동 업로드 알림 email" 형태로 재설계.
   - **Confidence:** HIGH — skill SKILL.md line 76-85 확인 (auth 는 browser 기반, add_source API 미언급)

2. **상위 3 영상 selection 기준 (retention/CTR/view_duration 중)**
   - **Answer:** **Composite score** — 3 metric 가중 합산.
   ```python
   def composite_score(metrics: dict) -> float:
       return (
           0.5 * metrics["retention_3s"]        # 3초 hook 이 가장 중요 (Phase 9 wiki/kpi/retention_3second_hook 근거)
           + 0.3 * metrics["completion_rate"]   # 완주율 (KPI-06)
           + 0.2 * (metrics["avg_view_sec"] / 60)  # 평균 시청시간 정규화 (60초 max)
       )
   ```
   - 가중치는 wiki/shorts/kpi/kpi_log.md Part A 의 목표 (3s retention > 60%, completion > 40%, avg > 25s) 비율 역수.
   - **Confidence:** MEDIUM — 가중치는 design decision (대표님 Plan 6 시점에 조정 가능)

3. **"다음 월 Producer 입력에 KPI 반영" 메커니즘**
   - **Answer:** Producer prompt template 파일 추가 — `wiki/shorts/kpi/monthly_context_YYYY-MM.md` (month rollover 마다 신규 생성). Plan 6 이 이 파일을 자동 생성 + Producer AGENT.md 가 `@wiki/shorts/kpi/monthly_context_latest.md` symlink 또는 glob 참조.
   ```markdown
   <!-- wiki/shorts/kpi/monthly_context_2026-05.md (Plan 6 auto-generated 2026-05-01) -->
   # Monthly KPI Context — 2026-05 Producer Input

   ## Top 3 영상 (2026-04 월간)
   | video_id | title | 3s_retention | completion | avg_view | composite |
   | abc123 | ... | 68% | 42% | 27s | 0.614 |
   ...

   ## 성공 패턴 (NotebookLM 요약)
   - 훅: 첫 1.5초 고유명사 제시 패턴이 retention 에 +8% (notebook query 결과)
   - 페르소나: "탐정 ↔ 조수" 대화체가 단일 화자 narration 대비 completion +12%

   ## 하위 3 영상 회피 사항
   ...
   ```
   - Producer (Phase 4 AGENT.md) 는 이미 `@wiki/` prefix 참조 지원 (Plan 06-10 에서 15 AGENT.md 가 52 refs 보유 중). monthly_context 추가는 **wiki 확장 (allowed)**, AGENT.md 수정 (forbidden during D-2 Lock) 아님.
   - **Confidence:** HIGH — Phase 4 + Phase 6 선례

4. **Research loop 실패 시 fallback**
   - **Answer:** 3 단계
     1. NotebookLM query 실패 (auth expired 등): `monthly_context_YYYY-MM.md` 에 "이전 달 context 재사용" 표기 + 이전 달 content 복사
     2. YouTube Analytics fetch 실패: 전월 데이터 재사용 + FAILURES.md append
     3. 둘 다 실패: Plan 6 중단, email 발송, 수동 개입 대기
   - **Confidence:** HIGH — Phase 5 fallback.py 3-tier 선례

### Plan 7: SC#6 YPP trajectory

1. **기존 `wiki/ypp/` 디렉토리 구조**
   - **Answer:** 2 파일 존재: `MOC.md` (Phase 2 scaffold) + `entry_conditions.md` (Phase 6 완료). `trajectory.md` 는 **부재** — Plan 7 이 신규 생성.
   - MOC.md 의 Planned Nodes 에 `[ ] shorts_fund_history.md, rpm_korean_benchmark.md, eligibility_path.md, reused_content_defense.md` 등 scaffold placeholder 만 존재. `trajectory.md` 는 list 에 없음 — Plan 7 시작 시 MOC 에 추가.
   - **Confidence:** HIGH — Glob 전수 확인

2. **월별 append 포맷 (markdown table / Mermaid / 둘 다)**
   - **Answer:** **둘 다**. Markdown table (primary) + Mermaid line chart (optional, GitHub native render).
   ```markdown
   # YPP Trajectory — naberal-shorts-studio

   ## 3-Milestone Gates (CONTEXT Locked Decision)
   - 1차 gate (3개월, 2026-07-20): subs ≥ 100
   - 2차 gate (6개월, 2026-10-20): subs ≥ 300, 3s retention ≥ 60%
   - 3차 gate (12개월, 2027-04-20): rolling 12m subs ≥ 1000 + views ≥ 10M

   ## Monthly Snapshots

   | Month | Subs | Rolling 12m Views | Completion vs 1st gate | vs 2nd gate | vs 3rd gate |
   | 2026-04 | 0 | 0 | 0% | 0% | 0% |
   | 2026-05 | 5 | 125 | 5% | 1.7% | 0.5% |
   ...

   ## Trajectory Chart

   ```mermaid
   xychart-beta
     title "Subs over time"
     x-axis [2026-04, 2026-05, 2026-06, ...]
     y-axis "Subscribers" 0 --> 1100
     line [0, 5, 23, 45, ...]
   ```

   ## Pivot Warning Thresholds
   - 2026-07-20 기준 subs < 100 → 니치/훅 iteration Plan 추가 (자동 FAILURES.md append F-YPP-XX)
   ```
   - Mermaid `xychart-beta` 는 GitHub 2024-10 지원. Phase 9 UAT#3 에서 확인됨.
   - **Confidence:** HIGH — Phase 9 Mermaid commit `94a0b22` 선례

3. **3단계 milestone 비교 + pivot 경보**
   - **Answer:**
   ```python
   def evaluate_gates(snapshot: dict, month_since_start: int) -> dict:
       warnings = []
       if month_since_start >= 3 and snapshot["subs"] < 100:
           warnings.append("1st gate FAIL — 니치/훅 iteration 필요")
       if month_since_start >= 6 and (snapshot["subs"] < 300 or snapshot["retention_3s"] < 0.60):
           warnings.append("2nd gate FAIL — 전략 재검토")
       # 3rd gate 는 12개월 rolling window — 별도 로직
       return {"warnings": warnings, "pivot_required": len(warnings) > 0}
   ```
   - 경보 시 FAILURES.md + email.
   - **Confidence:** HIGH — CONTEXT Locked Decision 직접 인용

4. **`wiki/shorts/kpi/kpi_log.md` 와의 cross-reference 규약**
   - **Answer:** trajectory.md 는 **channel-level aggregate** (subs + 뷰), kpi_log.md 는 **video-level metrics** (retention/completion). Cross-ref:
   - trajectory.md 하단에 `> Detailed per-video metrics → [[../shorts/kpi/kpi_log]]`
   - kpi_log.md 하단에 `> Channel-level YPP progress → [[../../ypp/trajectory]]`
   - **Confidence:** HIGH — wiki link 규약 (Phase 6 Plan 06-10)

### Plan 8: Rollback docs

1. **Phase 8 publish_lock.json 구조 + 수동 중단**
   - **Answer:** `publish_lock.py` line 128-135 확인:
   ```json
   {
     "last_upload_iso": "2026-04-20T20:30:00+09:00",
     "jitter_applied_min": 342,
     "_schema": 1
   }
   ```
   - 수동 중단: `last_upload_iso` 를 **미래 시점으로** 설정 → 다음 `assert_can_publish()` 가 `PublishLockViolation` raise.
   ```bash
   # 업로드 48시간 block
   python -c "
   import json
   from datetime import datetime, timedelta, timezone
   future = (datetime.now(timezone.utc) + timedelta(hours=49)).isoformat()
   with open('.planning/publish_lock.json', 'w') as f:
       json.dump({'last_upload_iso': future, 'jitter_applied_min': 0, '_schema': 1}, f)
   "
   ```
   - **Confidence:** HIGH — publish_lock.py 전수 확인

2. **git revert safety (PRIVATE repo 1인 운영)**
   - **Answer:** `git revert <commit>` 으로 새 commit 추가 (기존 history 보존). `git push` 만 필요 (force push 불필요).
   - Phase 10 scheduler 도입 commit 만 revert 하면 GH Actions cron 도 사라짐 (workflow 파일 미존재 시 자동 비활성화).
   - **Force push 필요한 경우:** sensitive 정보 실수로 commit (e.g., config/youtube_token.json 유출). 그 경우 `git filter-repo` + force push. PRIVATE repo + 1인 운영이므로 허용.
   - **Confidence:** HIGH — git 공식 + Phase 8 REMOTE 선례

3. **scheduler 자체 버그 시 자동 방어**
   - **Answer:** drift_scan.py (Plan 2) 가 A급 drift 감지 → `STATE.md phase_lock: true` 세팅 → session_start.py hook 이 경고 표시 → 대표님 manual review.
   - 추가 방어선: `publish_lock.py` 48h+jitter 가 scheduler 버그로 인한 연속 업로드 방지 (bot pattern trigger 불가).
   - **Confidence:** HIGH — Phase 8 설계 + Plan 2 확장

4. **학습 회로 오염 (skill_patch_counter > 0) → 복구**
   - **Answer:**
   ```bash
   # 1. 위반 식별 (skill_patch_counter 리포트 확인)
   cat reports/skill_patch_count_2026-04.md

   # 2. SKILL_HISTORY 에서 직전 버전 복원
   ls SKILL_HISTORY/<skill_name>/v*.md.bak | tail -1
   cp SKILL_HISTORY/<skill_name>/v20260415_103000.md.bak .claude/skills/<skill_name>/SKILL.md

   # 3. FAILURES.md append (F-D2-XX)
   # 4. 위반 commit revert
   git revert <violation_commit>
   ```
   - **Confidence:** HIGH — Phase 6 D-12 (`backup_skill_before_write`) 설계 직접 활용

## Reusable Assets Map

| Asset | Path | Public API | Used by Plan |
|-------|------|-----------|-------------|
| `publish_lock` | `scripts/publisher/publish_lock.py` | `assert_can_publish()`, `record_upload()`, `MIN_ELAPSED_HOURS=48`, `MAX_JITTER_MIN=720` | Plan 4 (Windows Task 파이프라인), Plan 8 (rollback) |
| `kst_window` | `scripts/publisher/kst_window.py` | `assert_in_window()`, `KST = ZoneInfo("Asia/Seoul")` | Plan 4, Plan 5 (rolling 평균 timezone) |
| `oauth` | `scripts/publisher/oauth.py` | `get_credentials()`, `SCOPES`, `CLIENT_SECRET_PATH`, `TOKEN_PATH` | Plan 3 (scope 추가 `yt-analytics.readonly`) |
| `youtube_uploader` | `scripts/publisher/youtube_uploader.py` | `build_insert_body()`, `resumable_upload()`, `publish()` | Plan 4 (Windows Task 업로드) |
| `aggregate_patterns` | `scripts/failures/aggregate_patterns.py` | `iter_entries()`, `normalize_pattern_key()`, `aggregate()` | Plan 3 (월간 집계 패턴 차용), Plan 1 (stdlib-only design pattern) |
| `harness_audit` | `scripts/validate/harness_audit.py` | `run_audit()` → `(score, violations, warnings)`, `main(["--json-out", path])`, `HARNESS_AUDIT_SCORE: N` stdout parse | Plan 5 (세션 audit) |
| `pre_tool_use` hooks | `.claude/hooks/pre_tool_use.py` | `check_failures_append_only()` line 160, `backup_skill_before_write()` line 213, `load_patterns()`, `check_structure_allowed()` | Plan 전반 (FAILURES.md append 시 자동 enforce — 직접 호출 아님) |
| `session_start` hook | `.claude/hooks/session_start.py` | `count_long_skills()`, `check_conflict_map()`, `scan_deprecated_patterns()`, `summarize_work_handoff()`, `list_env_keys()`, `load_memory_index()` | Plan 5 (출력 JSON 축적 대상) |
| harness `drift_scan` | `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` | `load_patterns()`, `scan_studio()`, `write_conflict_map()`, `append_history()` | Plan 2 (sys.path import) |
| NotebookLM skill | `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/` | CLI wrapper `scripts/run.py ask_question.py --question ...` subprocess 경로 | Plan 6 |
| `invokers` (Claude CLI) | `scripts/orchestrator/invokers.py` | Claude `--print` subprocess Producer/Supervisor invocation pattern | Plan 6 (Producer input 주입 시) |
| `.claude/deprecated_patterns.json` | `.claude/deprecated_patterns.json` | 8 entries `{regex, reason}` — Plan 2 에서 `grade`, `name` 필드 추가 | Plan 2 |
| `wiki/shorts/kpi/kpi_log.md` | existing | Part A 목표 declaration (read-only), Part B 월별 table append | Plan 3 |
| `wiki/ypp/entry_conditions.md` | existing | YPP 2026 기준 + Korean RPM baseline (read-only context) | Plan 7 |
| `.claude/memory/*.md` | existing 9 박제 메모리 | Session context (read-only) | Plan 전반 (참조만) |

## Common Pitfalls

### Pitfall 1: GH Actions cron 지연
**What goes wrong:** cron 스케줄이 10-30분 지연되거나 드물게 dropped.
**Why it happens:** GitHub infra load balancing. 공식 known issue.
**How to avoid:** (1) 정확 시각 필수 작업은 `workflow_dispatch` 수동 trigger (2) 시간 sensitive 가 아닌 daily/weekly/monthly 작업만 cron 에 위임 (3) `timezone:` 필드 활용 시에도 지연 동일.
**Warning signs:** 예정된 시각 +30분 지나도 workflow run 없음 → GitHub Status Page 확인.

### Pitfall 2: OAuth scope 변경 시 token 무효화
**What goes wrong:** Plan 3 에서 scope 에 `yt-analytics.readonly` 추가 → 기존 `config/youtube_token.json` 의 refresh_token 이 new scope 에 access 불가 → API 호출 시 401/403.
**Why it happens:** OAuth 2.0 표준 — scope 변경은 사실상 새 authorization. refresh_token 은 old scope 에 bound.
**How to avoid:** (1) Plan 3 Wave 0 에서 `get_credentials()` 1회 실행 → 브라우저 재인증 → 새 token 저장 (2) GH Actions secret 재업로드.
**Warning signs:** `fetch_kpi.py` 401 Unauthorized + `"error_description": "insufficient_scope"`.

### Pitfall 3: `check_failures_append_only` hook 우회 시도
**What goes wrong:** Plan 4 notify_failure.py 가 FAILURES.md 를 overwrite 하려 함 → hook 이 deny.
**Why it happens:** hook 은 Write 의 new content 가 existing 의 strict prefix 인지 검증 (line 195-201).
**How to avoid:** 반드시 `Path.read_text() + new_entry` 로 기존 내용 보존 후 write. 또는 append mode 파일 접근:
```python
with open("FAILURES.md", "a", encoding="utf-8") as f:
    f.write(f"\n\n### F-OPS-{next_id}: {summary}\n...")
# 단, Claude Code 의 Write tool 을 경유하지 않는 직접 파일 쓰기는 hook 우회 — 허용.
# hook 은 Claude 의 Write/Edit tool 만 검사.
```
**Warning signs:** `{"decision": "deny", "reason": "FAILURES.md Write must preserve ..."}` JSON 응답.

### Pitfall 4: Windows Task Scheduler 권한 문제
**What goes wrong:** `Register-ScheduledTask` Access Denied.
**Why it happens:** PowerShell 일반 유저 세션. Administrator 권한 필요.
**How to avoid:** (1) 설치 시 1회 "Run as Administrator" (2) Task 자체는 일반 user context 로 실행 — `-User "$env:USERNAME"` (3) 또는 `-RunLevel Highest` (UAC 승격 필요).
**Warning signs:** PowerShell 오류 `Register-ScheduledTask : Access is denied.`

### Pitfall 5: 한국어 UTF-8 + Windows cp949
**What goes wrong:** `print(f"FAILURES.md: {reason}")` 에 한국어 포함 → Windows stdout cp949 → UnicodeEncodeError.
**Why it happens:** Windows 기본 콘솔 인코딩 cp949. Phase 5 STATE #28 에서 확인.
**How to avoid:**
```python
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```
**Warning signs:** `UnicodeEncodeError: 'charmap' codec can't encode character`.

### Pitfall 6: NotebookLM source 추가 자동화 불가
**What goes wrong:** Plan 6 에서 NotebookLM notebook 에 새 source 를 자동 추가하려 함 → 공식 API 미공개.
**Why it happens:** Google NotebookLM 은 2026-04 기준 source 추가 API 비공개. 브라우저 UI 만 가능.
**How to avoid:** Plan 6 를 "md 파일 자동 생성 + 대표님 월 1회 수동 upload + email reminder" 로 설계 재조정. 자동화는 query 만 가능.
**Warning signs:** 공식 docs `developers.google.com/notebooklm` 부재 (실제 NotebookLM docs 페이지 없음).

### Pitfall 7: STATE.md frontmatter 수정 시 GSD 혼란
**What goes wrong:** Plan 2 에서 `phase_lock: true` 추가 → GSD 가 `status: executing` 과 충돌로 crash.
**Why it happens:** GSD 커맨드의 frontmatter 파서가 unknown field 를 어떻게 처리하는지 불확실.
**How to avoid:** Plan 2 Wave 0 에서 (1) GSD 커맨드 1회 실행 (`/gsd:verify-work 9`) (2) `phase_lock: true` 추가 후 동일 커맨드 재실행 → 차이 확인. 문제 시 `extensions: {phase_lock: ...}` 로 nesting.
**Warning signs:** `/gsd:*` 커맨드가 YAML parse error.

## Code Examples

### Plan 1 skill_patch_counter (GREEN pseudocode)
```python
# scripts/audit/skill_patch_counter.py
"""D-2 Lock SKILL patch counter — FAIL-04 / SC#1."""
from __future__ import annotations
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KST = ZoneInfo("Asia/Seoul")
D2_LOCK_START = "2026-04-20"
D2_LOCK_END = "2026-06-20"

FORBIDDEN = [
    re.compile(r"^\.claude/agents/.+/SKILL\.md$"),
    re.compile(r"^\.claude/skills/.+/SKILL\.md$"),
    re.compile(r"^\.claude/hooks/[^/]+\.py$"),
    re.compile(r"^CLAUDE\.md$"),
]

def scan_violations() -> list[dict]:
    result = subprocess.run(
        ["git", "log",
         f"--since={D2_LOCK_START}",
         f"--until={D2_LOCK_END}",
         "--name-only",
         "--pretty=format:---COMMIT---%n%H|%aI|%s"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    violations = []
    current = None
    for line in result.stdout.splitlines():
        if line == "---COMMIT---":
            current = {"hash": None, "date": None, "subject": None, "files": []}
            continue
        if current is None:
            continue
        if current["hash"] is None and "|" in line:
            h, d, s = line.split("|", 2)
            current.update(hash=h, date=d, subject=s)
            continue
        if line.strip():
            for rx in FORBIDDEN:
                if rx.match(line.strip()):
                    violations.append({**current, "violating_file": line.strip()})
                    break
    return violations

def write_report(violations: list[dict], output: Path) -> None:
    month = datetime.now(KST).strftime("%Y-%m")
    lines = [
        f"# D-2 Lock Skill Patch Counter — {month}",
        f"",
        f"**Lock period:** {D2_LOCK_START} ~ {D2_LOCK_END}",
        f"**Report generated:** {datetime.now(KST).isoformat()}",
        f"**Violation count:** {len(violations)} {'✅' if not violations else '🚨'}",
        f"",
        "## Violations",
    ]
    if violations:
        lines.append("| Hash | Date | File | Subject |")
        lines.append("|------|------|------|---------|")
        for v in violations:
            lines.append(f"| {v['hash'][:7]} | {v['date']} | `{v['violating_file']}` | {v['subject']} |")
    else:
        lines.append("*없음.*")
    output.write_text("\n".join(lines), encoding="utf-8")

def main() -> int:
    violations = scan_violations()
    out = Path(f"reports/skill_patch_count_{datetime.now(KST):%Y-%m}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    write_report(violations, out)
    if violations:
        # FAILURES.md append (별도 함수)
        append_failures(violations)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Plan 2 drift_scan wrapper (GREEN pseudocode)
```python
# scripts/audit/drift_scan.py
"""A-grade drift scanner wrapping harness drift_scan.py — AUDIT-03/04 / SC#4."""
import sys
from pathlib import Path
import json

STUDIO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_SCRIPTS = STUDIO_ROOT.parent.parent / "harness" / "scripts"
sys.path.insert(0, str(HARNESS_SCRIPTS))

from drift_scan import load_patterns, scan_studio, write_conflict_map, append_history  # noqa: E402

def set_phase_lock(reason: str, findings_summary: dict) -> None:
    state_path = STUDIO_ROOT / ".planning" / "STATE.md"
    # YAML frontmatter 수정 — 단순 replace
    text = state_path.read_text(encoding="utf-8")
    # phase_lock 필드 삽입 (이미 있으면 update)
    ...   # 세부 구현은 Plan 2 에서

def create_github_issue(reason: str, findings_summary: dict) -> None:
    import subprocess
    body = f"""# [AUDIT-04] A급 drift 감지
    Reason: {reason}
    ...
    """
    subprocess.run(
        ["gh", "issue", "create",
         "--title", f"[AUDIT-04] A급 drift — Phase 차단",
         "--body-file", "-",
         "--label", "drift,critical,phase-10,auto"],
        input=body, text=True, check=True,
    )

def main() -> int:
    pattern_defs = load_patterns(STUDIO_ROOT)
    findings = scan_studio(STUDIO_ROOT, pattern_defs)
    output = STUDIO_ROOT / ".planning" / "codebase" / "CONFLICT_MAP.md"
    write_conflict_map(STUDIO_ROOT, findings, pattern_defs, output)
    append_history(STUDIO_ROOT, findings)

    a_grade = 0
    a_details = {}
    for p in pattern_defs:
        if p.get("grade", "C").upper() == "A":
            hits = findings.get(p.get("name", ""), [])
            if hits:
                a_grade += len(hits)
                a_details[p.get("name")] = len(hits)

    if a_grade > 0:
        set_phase_lock(f"A급 drift {a_grade}건", a_details)
        create_github_issue(f"A급 drift {a_grade}건", a_details)
        return 1
    return 0
```

### Plan 3 YouTube Analytics fetch (GREEN pseudocode)
```python
# scripts/analytics/fetch_kpi.py
"""YouTube Analytics v2 daily KPI fetch — KPI-01 / SC#2."""
from datetime import date, timedelta
from googleapiclient.discovery import build
from scripts.publisher.oauth import get_credentials   # scope 확장 후

def fetch_daily_metrics(video_id: str, days_back: int = 7) -> dict:
    creds = get_credentials()   # scope: yt-analytics.readonly 포함 필수
    yta = build("youtubeAnalytics", "v2", credentials=creds)

    end = date.today()
    start = end - timedelta(days=days_back)

    response = yta.reports().query(
        ids=f"channel==MINE",
        startDate=start.isoformat(),
        endDate=end.isoformat(),
        metrics="views,averageViewDuration,audienceWatchRatio",
        dimensions="video",
        filters=f"video=={video_id}",
    ).execute()

    return parse_response(response)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GH Actions cron UTC-only | `timezone:` field supported | 2025-08 | KST 표기 가능, 단 실행 지연은 동일 |
| YouTube Shorts view count 불명확 | Short starts or replays = view | 2025-03 announced, 2025-04-30 effective | audienceWatchRatio 계산 방식 동일, raw view count 만 영향 |
| `schtasks.exe` CLI | `New-ScheduledTask` PowerShell cmdlet | Windows 10+ | 가독성·테스트 편의 대폭 개선 |
| pytz | `zoneinfo` (Python 3.9+) | Python 3.9 | Phase 8 이미 전환 완료 |
| OAuth OOB (out-of-band) flow | `run_local_server(port=0)` | Google 2022-10 deprecation | oauth.py line 56 이미 전환 |

**Deprecated/outdated:**
- Whisper native timestamps (Phase 4 권장 WhisperX 로 대체)
- Selenium YouTube 업로더 (AF-8 영구 금지, deprecated_patterns.json `\bimport\s+selenium\b`)
- T2V 코드 경로 (deprecated_patterns.json `t2v|text_to_video|text2video`)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio (Phase 4 이후 사용 중) |
| Config file | `pytest.ini` 또는 `pyproject.toml` (Phase 8 확인) |
| Quick run command | `pytest tests/phase10/ -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FAIL-04 | git log 이용한 금지 경로 count | unit | `pytest tests/phase10/test_skill_patch_counter.py -x` | ❌ Wave 0 |
| KPI-01 | YouTube Analytics daily fetch + csv output | integration | `pytest tests/phase10/test_fetch_kpi.py -x` | ❌ Wave 0 |
| KPI-02 | 월간 kpi_log.md append | unit | `pytest tests/phase10/test_monthly_aggregate.py -x` | ❌ Wave 0 |
| KPI-03 | NotebookLM query subprocess 성공 | integration | `pytest tests/phase10/test_research_loop.py -x -m integration` | ❌ Wave 0 |
| KPI-04 | monthly_context_YYYY-MM.md 생성 검증 | unit | `pytest tests/phase10/test_monthly_context.py -x` | ❌ Wave 0 |
| AUDIT-01 | 30일 rolling 점수 계산 | unit | `pytest tests/phase10/test_session_audit.py -x` | ❌ Wave 0 |
| AUDIT-02 | harness_audit 재호출 | smoke | `python -m scripts.validate.harness_audit --threshold 80` | ✅ Phase 7 |
| AUDIT-03 | drift_scan A급 count | unit + integration | `pytest tests/phase10/test_drift_scan.py -x` | ❌ Wave 0 |
| AUDIT-04 | STATE.md phase_lock 세팅 + gh issue 호출 | unit (mocked) | `pytest tests/phase10/test_phase_lock.py -x` | ❌ Wave 0 |

### Sampling Rate (Continuous Monitoring Model)

Phase 10 은 전통적 "phase gate → verified" 모델과 다르다. **Nyquist Validation (Dimension 8)** 는 다음으로 재해석:

- **Per task commit (수동 검증):** `pytest tests/phase10/<plan>/ -x` 빠른 green 확인
- **Per wave merge (CI on PR):** `pytest tests/ -x --tb=short` 전체 regression (Phase 1-9 + Phase 10 누적)
- **Per GH Actions cron run (continuous verification):**
  - `analytics-daily.yml` 실행 성공 = KPI-01 continuous pass
  - `drift-scan-weekly.yml` 실행 + a_rank=0 = AUDIT-03 pass
  - `skill-patch-count-monthly.yml` 실행 + count=0 = FAIL-04 pass
- **Monthly verification ledger:**
  - `reports/skill_patch_count_YYYY-MM.md` (Plan 1)
  - `wiki/shorts/kpi/kpi_log.md` Part B (Plan 3 월별 row)
  - `wiki/ypp/trajectory.md` (Plan 7 월별 snapshot)
  - `.planning/codebase/CONFLICT_MAP.md` (Plan 2 주간)
  - `logs/session_audit.jsonl` (Plan 5 매 세션)
  - `FAILURES.md` (모든 Plan 의 실패 append)
- **Phase gate 대용 mechanism:** `phase_lock: true` in STATE.md (AUDIT-04). 이 플래그가 false 유지 = Phase 10 continuous pass.
- **Exit criterion verification:** 매월 1일 Plan 7 trajectory_append.py 가 3-gate 평가. 12개월 지점 도달 + 3차 gate pass = Phase 10 "성공 선언".

### Wave 0 Gaps
- [ ] `tests/phase10/__init__.py` — test scaffold
- [ ] `tests/phase10/conftest.py` — 공용 fixtures (tmp_publish_lock, freeze_kst, mock_youtube_analytics)
- [ ] `tests/phase10/test_skill_patch_counter.py` — FAIL-04 unit
- [ ] `tests/phase10/test_drift_scan.py` — AUDIT-03 unit
- [ ] `tests/phase10/test_phase_lock.py` — AUDIT-04 unit (mocked gh CLI)
- [ ] `tests/phase10/test_fetch_kpi.py` — KPI-01 integration
- [ ] `tests/phase10/test_monthly_aggregate.py` — KPI-02 unit
- [ ] `tests/phase10/test_research_loop.py` — KPI-03 integration (mocked NotebookLM subprocess)
- [ ] `tests/phase10/test_monthly_context.py` — KPI-04 unit
- [ ] `tests/phase10/test_session_audit.py` — AUDIT-01 unit
- [ ] `tests/phase10/test_trajectory_append.py` — SC#6 unit
- [ ] `tests/phase10/test_rollback_procedures.py` — Plan 8 verification (dry-run)
- [ ] `tests/phase10/phase10_acceptance.py` — SC#1-6 aggregator (Phase 6/7/8/9 선례)
- [ ] STRUCTURE.md whitelist 업데이트: `reports/`, `logs/` 상위 폴더 등록

## Risk Register

| Risk | Plan | Probability | Impact | Mitigation |
|------|------|-------------|--------|-----------|
| GH Actions cron 지연 → 일일 fetch 누락 | 3, 4 | MEDIUM | LOW | `workflow_dispatch` 수동 trigger + `--since` 파라미터로 누락일 복구 (정책 필요) |
| OAuth token scope 확장 시 기존 token 무효화 | 3 | HIGH (확장 시점) | MEDIUM | Plan 3 Wave 0 에서 `get_credentials()` 1회 실행 → 브라우저 재인증. GH Secret 재업로드. |
| Windows PC 꺼짐 → 영상 생성/업로드 중단 | 4 | MEDIUM | HIGH | 대표님 관행 (PC 상시 ON). 장기 부재 시 GH Actions 로 fallback 하려면 로컬 파일 크기 문제 해결 필요 (Phase 10 범위 외 → 수동 전환) |
| `check_failures_append_only` hook 이 notify_failure.py 차단 | 4 | LOW | MEDIUM | Pitfall 3 확인 — 직접 파일 쓰기는 hook 우회, Write tool 경유만 검사 |
| NotebookLM browser session 만료 → research loop 실패 | 6 | HIGH (월 단위) | LOW | Pitfall 6 — 자동화 한계 인정. "md 파일 생성 + 대표님 수동 업로드 reminder email" 설계 |
| drift_scan STATE.md 수정 시 GSD 커맨드 crash | 2 | LOW | HIGH | Pitfall 7 — Plan 2 Wave 0 에서 smoke test 로 확인. 실패 시 nested extension 구조로 우회 |
| 3차 gate (12개월 + 1000 subs) 미달 시 Phase 10 무기한 지속 | 7 | MEDIUM | HIGH | CONTEXT Locked Decision — 1/2차 gate 미달 시 pivot. 3차 gate 미달 시 "수익 전 재검토 Plan" 추가 (본 phase 밖) |
| Windows Task Scheduler 유저 전환 시 task 소실 | 4 | LOW | MEDIUM | Plan 4 의 register 스크립트 는 Plan 8 rollback docs 에서 재실행 가능하게 작성 |
| GH Actions secrets 유출 시 YouTube 채널 탈취 | 4 | LOW | CRITICAL | PRIVATE repo + repo-level secret (org-wide 아님) + 2FA 강제 (대표님 계정) |
| `grade` 필드 추가 시 Phase 5/6 regression 실패 | 2 | MEDIUM | LOW | Plan 2 Wave 0 에서 `grep -r "deprecated_patterns.json" tests/` 영향 분석 + 테스트에서 grade 기본값 `"C"` 가정 |

## Sources

### Primary (HIGH confidence)
- `scripts/publisher/publish_lock.py` — 소스 전수 read
- `scripts/publisher/kst_window.py` — 소스 전수 read
- `scripts/publisher/oauth.py` — 소스 전수 read
- `scripts/publisher/youtube_uploader.py` — 소스 전수 read
- `scripts/failures/aggregate_patterns.py` — 소스 전수 read
- `scripts/validate/harness_audit.py` — 소스 전수 read
- `.claude/hooks/pre_tool_use.py` — 소스 전수 read (D-11 + D-12 enforcement 검증)
- `.claude/hooks/session_start.py` — 소스 전수 read
- `.claude/deprecated_patterns.json` — 8 entries 확인
- `C:/Users/PC/Desktop/naberal_group/harness/scripts/drift_scan.py` — public API 4 함수 시그니처 확인
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/SKILL.md` — CLI wrapper 패턴 확인
- `.planning/phases/10-sustained-operations/10-CONTEXT.md` — 3 Locked Decision verbatim
- `.planning/REQUIREMENTS.md` line 138-161 — 9 requirements
- `.planning/STATE.md` frontmatter — GSD state machine format
- `wiki/shorts/kpi/kpi_log.md` — Part A API contract + Part B synthetic
- `wiki/ypp/entry_conditions.md` + `wiki/ypp/MOC.md` — YPP 기준
- YouTube Analytics API [Reports: Query](https://developers.google.com/youtube/analytics/reference/reports/query) — 엔드포인트 공식
- YouTube Analytics API [Metrics](https://developers.google.com/youtube/analytics/metrics) — audienceWatchRatio 정의

### Secondary (MEDIUM confidence)
- GitHub Actions [Workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions) — cron syntax
- [GitHub community discussion #156282](https://github.com/orgs/community/discussions/156282) — cron 지연 known issue
- [GitHub community discussion #13454](https://github.com/orgs/community/discussions/13454) — timezone 필드 추가
- Microsoft Learn [New-ScheduledTask](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtask?view=windowsserver2025-ps) — PowerShell cmdlet
- [GitHub CLI gh issue create](https://cli.github.com/manual/gh_issue_create) — non-interactive flags

### Tertiary (LOW confidence, flagged for Plan-time verification)
- `timezone:` 필드 2025-08 추가 — 실제 GA 도달 시기 확인 필요 (Plan 4 Wave 0)
- YouTube Analytics quota 정확한 daily limit — Cloud Console 에서만 확인 가능 (Plan 3 Wave 0 smoke)

## Metadata

**Confidence breakdown:**
- Reusable Assets Map: HIGH — 7개 자산 모두 소스 코드 전수 확인
- Standard Stack: HIGH — 모두 Phase 1-9 에서 사용 중 검증된 deps
- Architecture Patterns: MEDIUM-HIGH — GH Actions timezone 필드는 MEDIUM (2025-08 신규, Plan 4 Wave 0 smoke 필요)
- Runtime State Inventory: HIGH — 5 category 전수 답변
- Open Questions per Plan: HIGH — 8 Plan × 3~4 질문 모두 답변
- Pitfalls: HIGH — 7개 모두 소스 근거 + 재현 가능한 warning sign
- Validation Architecture (continuous model): MEDIUM — Phase 10 은 영구 지속이라 기존 Nyquist 모델 부분 재해석 필요. Plan-time 에 대표님과 1회 synchronize 권고.
- Risk Register: HIGH — 10개 risk 모두 Plan 별 구체적 mitigation

**Research date:** 2026-04-20
**Valid until:** 2026-05-20 (stable components); 2026-04-27 for YouTube Analytics quota (검증 필요)
