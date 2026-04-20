---
phase: 10
slug: sustained-operations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-20
---

# Phase 10 — Validation Strategy

> **Special note**: Phase 10 is **영구 지속 (sustained)** — traditional phase gate replaced with **Continuous Monitoring Validation Model**. See `10-RESEARCH.md` §Validation Architecture (line 1084).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing, shared with Phases 1-9.1) |
| **Config file** | `pytest.ini` (project root) |
| **Quick run command** | `pytest tests/unit/phase10/ -q` |
| **Full suite command** | `pytest tests/unit/phase10/ tests/integration/phase10/ --cov=scripts/audit --cov=scripts/analytics --cov=scripts/research_loop --cov=scripts/schedule` |
| **Estimated runtime** | ~30s unit / ~120s full |

---

## Sampling Rate

- **After every task commit:** Run quick command for affected plan
- **After every plan wave:** Run full suite
- **Before continuous monitoring activation:** Full suite must be green + smoke tests for GH Actions + Windows Task Scheduler
- **Max feedback latency:** 30s (quick) / 120s (full)
- **Continuous monitoring cadence (post-activation)**:
  - Daily: `analytics-daily.yml` GH Action success = continuous pass for KPI-01
  - Weekly: `drift-scan-weekly.yml` A급 drift = 0 → continuous pass for AUDIT-03/04
  - Monthly: `skill-patch-count-monthly.yml` count = 0 → continuous pass for FAIL-04

---

## Per-Task Verification Map (to be expanded by gsd-planner)

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | FAIL-04 | unit | `pytest tests/unit/phase10/test_skill_patch_counter.py -q` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | FAIL-04 | integration | `python scripts/audit/skill_patch_counter.py --dry-run --since=2026-04-20` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | AUDIT-03 | unit | `pytest tests/unit/phase10/test_drift_scan.py -q` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 1 | AUDIT-04 | integration | `python scripts/audit/drift_scan.py --simulate-a-grade` (STATE.md phase_lock=true 확인) | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | KPI-01 | unit | `pytest tests/unit/phase10/test_fetch_kpi.py -q` (mock YouTube Analytics) | ❌ W0 | ⬜ pending |
| 10-03-02 | 03 | 2 | KPI-02 | integration | `python scripts/analytics/monthly_aggregate.py --dry-run` | ❌ W0 | ⬜ pending |
| 10-04-01 | 04 | 2 | (Scheduler) | smoke | `gh workflow run analytics-daily.yml --ref main` + 3-minute polling | ❌ W0 | ⬜ pending |
| 10-04-02 | 04 | 2 | (Scheduler) | smoke | `schtasks /Query /TN naberal_shorts_daily` | ❌ W0 | ⬜ pending |
| 10-05-01 | 05 | 3 | AUDIT-01 | unit | `pytest tests/unit/phase10/test_session_audit.py -q` | ❌ W0 | ⬜ pending |
| 10-06-01 | 06 | 3 | KPI-03 | unit | `pytest tests/unit/phase10/test_research_loop.py -q` (notebooklm skill mock) | ❌ W0 | ⬜ pending |
| 10-06-02 | 06 | 3 | KPI-04 | integration | Producer prompt template 에 `previous_month_kpi` 필드 존재 확인 | ❌ W0 | ⬜ pending |
| 10-07-01 | 07 | 3 | (SC#6) | unit | `pytest tests/unit/phase10/test_trajectory.py -q` | ❌ W0 | ⬜ pending |
| 10-08-01 | 08 | 4 | (FAIL-04 지원) | manual | `.planning/phases/10-sustained-operations/ROLLBACK.md` 3 시나리오 존재 확인 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

### Test stubs (신규 작성)
- [ ] `tests/unit/phase10/__init__.py` — package marker
- [ ] `tests/unit/phase10/conftest.py` — shared fixtures (tmp git repo, mock YouTube Analytics, mock notebooklm)
- [ ] `tests/unit/phase10/test_skill_patch_counter.py` — FAIL-04 stub
- [ ] `tests/unit/phase10/test_drift_scan.py` — AUDIT-03/04 stub
- [ ] `tests/unit/phase10/test_fetch_kpi.py` — KPI-01 stub
- [ ] `tests/unit/phase10/test_monthly_aggregate.py` — KPI-02 stub
- [ ] `tests/unit/phase10/test_session_audit.py` — AUDIT-01 stub
- [ ] `tests/unit/phase10/test_research_loop.py` — KPI-03/04 stub
- [ ] `tests/unit/phase10/test_trajectory.py` — SC#6 stub
- [ ] `tests/integration/phase10/` — GH Actions + Windows Task Scheduler smoke

### Repo infrastructure (각 Plan Wave 0 에서 설치)
- [ ] `reports/` 최상위 디렉토리 (Plan 1 + Plan 5 월간 리포트 출력처) — STRUCTURE.md whitelist 확장 필요
- [ ] `logs/` 최상위 디렉토리 (Plan 5 session audit jsonl) — STRUCTURE.md whitelist 확장 필요
- [ ] `.github/workflows/` 디렉토리 신설 (Plan 4)
- [ ] `.claude/deprecated_patterns.json` grade 필드 추가 (Plan 2 Wave 0 smoke — Phase 5/6 regression 검증)
- [ ] `.planning/STATE.md` frontmatter 확장 (`phase_lock` / `block_reason` / `block_since` 3 필드, Plan 2 Wave 0 smoke — GSD YAML parser 호환 검증)
- [ ] `scripts/publisher/oauth.py` SCOPES 에 `yt-analytics.readonly` 추가 + `youtube_token.json` 재발급 (Plan 3 Wave 0, 대표님 로컬 브라우저 재인증 1회)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Exit Criterion 1차 gate (3개월 누적 구독 ≥ 100) | SC#6 | 실시간 YouTube 데이터 + 대표님 pivot 판단 | 2026-07-20 기준 trajectory.md 확인 |
| Exit Criterion 2차 gate (6개월 누적 구독 ≥ 300 + 3초 retention ≥ 60%) | SC#6 | 동일 | 2026-10-20 기준 trajectory.md 확인 |
| Exit Criterion 3차 gate (12개월 rolling ≥ 1000 + 10M views) = YPP 진입 | SC#6 + Phase 목적 | 동일 | 2027-04-20+ 쿨다운 |
| NotebookLM source 월간 업로드 (대표님 수동) | KPI-03 | Google 공식 API 미공개 (2026-04 기준) | 월 1회 email reminder → 대표님 browser 수동 업로드 |
| D-2 Lock 해제 시점 Taste Gate 2회 완료 확인 | FAIL-04 exit | 주관 평가 | `wiki/kpi/taste_gate_*.md` 2개 파일 존재 확인 |
| SMTP email app password 설정 (Gmail/Naver) | Scheduler 실패 알림 | 대표님 계정 보안 설정 | 1회 Gmail → 계정 → 앱 비밀번호 생성 |
| OAuth token 재발급 (analytics scope 확장 후) | KPI-01/02 | 로컬 브라우저 OAuth flow | Plan 3 Wave 0 에서 `python scripts/publisher/oauth.py --refresh` 실행 |

---

## Continuous Monitoring Validation Model (Phase 10 특수)

전통적 "phase 완결 → verify" 모델 대신 **영구 monitoring** 으로 pass 판정:

| Signal | Frequency | Pass Condition | Fail Response |
|--------|-----------|----------------|---------------|
| `analytics-daily.yml` success | Daily | GH Action exit 0 + KPI row in kpi_log | 3회 연속 실패 → FAILURES.md F-OPS-XX + email alert |
| `drift-scan-weekly.yml` result | Weekly | A급 drift count = 0 | count > 0 → STATE.md phase_lock=true + GitHub issue 자동 |
| `skill-patch-count-monthly.yml` result | Monthly | count = 0 (2개월 lock 기간) | count > 0 → FAILURES.md F-D2-XX + lock 조기 재발동 |
| `session_start.py` rolling avg (30d) | Continuous | avg ≥ 80 | < 80 → FAILURES.md F-AUDIT-XX + session 시작 시 경고 |
| `wiki/ypp/trajectory.md` monthly append | Monthly | 새 row 추가 + 3-gate 진행률 계산 | 2개월 연속 miss → email alert + 수동 pivot discuss |
| NotebookLM RAG 월간 갱신 | Monthly | `.claude/memory/kpi_monthly_*.md` 생성 + 다음월 Producer 입력에 반영 | 반영 실패 2회 → FAILURES.md F-KPI-XX |

**Verification Ledger 6종** (Phase 10 continuous pass 증거):
1. `reports/skill_patch_count_YYYY-MM.md` — FAIL-04 월간 증명
2. `wiki/shorts/kpi_log.md` — KPI-01/02 월간 증명
3. `wiki/ypp/trajectory.md` — SC#6 월간 증명
4. `.planning/codebase/CONFLICT_MAP.md` — AUDIT-03/04 주간 drift 기록
5. `logs/session_audit.jsonl` — AUDIT-01 세션별 증명
6. `FAILURES.md` — 모든 실패 통합 append-only 증명

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s (quick) / 120s (full)
- [ ] Continuous monitoring signals defined for all 6 SCs
- [ ] Manual verifications explicitly marked (7 items)
- [ ] `nyquist_compliant: true` set in frontmatter (gsd-planner 완료 후)

**Approval:** pending (gsd-planner + gsd-plan-checker 완료 후 대표님 sign-off)
