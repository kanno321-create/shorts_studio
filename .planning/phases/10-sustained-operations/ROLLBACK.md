---
phase: 10-sustained-operations
kind: rollback-runbook
status: ready
last_updated: 2026-04-20
owner: 나베랄 감마
consumers: [대표님 실 사고 시 copy-paste, gsd-verifier, Phase 10 Continuous Monitoring]
---

# Phase 10 Rollback Runbook

> 무인 운영 중 사고 발생 시 대표님이 copy-paste 로 복구할 수 있는 수순서입니다.
> **모든 명령은 cwd = `C:\Users\PC\Desktop\naberal_group\studios\shorts\` 기준입니다.**
> 각 시나리오는 Detect / Stop / Diagnose / Recover / Verify 5 단계로 구성되며, 체크박스를 순서대로 체크하시면서 진행하시면 됩니다.

Phase 10 Sustained Operations 는 "예방 (Plan 01-07) + 복구 (Plan 08)" 의 2축 구조입니다. 본 runbook 은 후자의 관문으로, FAIL-04 삼중 안전망의 마지막 축을 담당합니다.

- 1축 — 감지: `skill_patch_counter.py` (Plan 10-01) 가 D-2 Lock 위반 count.
- 2축 — 잠금: `drift_scan.py` (Plan 10-02) 가 A급 drift 시 `.planning/STATE.md phase_lock: true`.
- 3축 — 복구: 본 runbook + `scripts/rollback/stop_scheduler.py` (Plan 10-08).

---

## 긴급 전체 중단 (2분 이내)

실 사고 감지 직후, 원인 파악보다 **중단이 우선**입니다. 다음 3 명령을 순차 실행하시면 파이프라인이 영구 block 됩니다.

```powershell
# 1. Windows Task 3종 정지 + Unregister (관리자 권한 PowerShell 필요)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\schedule\windows_tasks.ps1 -Unregister

# 2. Publish lock 을 미래 49시간으로 세팅 (publish_lock.py 48h+jitter 의 역활용)
python -m scripts.rollback.stop_scheduler --block-hours 49

# 3. GH Actions 중단 (workflow 파일을 .github/workflows.disabled/ 로 이동)
mkdir -p .github/workflows.disabled
mv .github/workflows/*.yml .github/workflows.disabled/
git add .github/ && git commit -m "emergency(10): disable all scheduled workflows" && git push
```

**재개 조건:** 원인 분석 완료 + FAILURES.md append + 대표님 명시 승인. 자동 재개 절대 금지.

---

## 시나리오 1: 업로드 사고 (잘못된 영상 발행됨)

> 가장 위험한 시나리오입니다. YouTube 채널 리스크 + YPP 진입 궤도 손상 가능성이 있으므로 **2분 이내 중단** 이 필수입니다.

### Detect
- [ ] YouTube Studio 대시보드 (`https://studio.youtube.com`) 에서 의도치 않은 업로드 확인
- [ ] `.planning/publish_lock.json` 의 `last_upload_iso` 시각을 `schtasks /Query /TN ShortsStudio_Upload /V /FO LIST` 출력과 대조
- [ ] `ShortsStudio_Upload` Task 의 Last Run Result 확인 (0x0 = 성공, 그 외 = 실패)
- [ ] 대표님 email (`kanno3@naver.com`) 에 `[shorts_studio] ...` 발행 알림 / 실패 알림 확인

### Stop
- [ ] 긴급 전체 중단 3 명령 실행 (위 섹션 참조)
- [ ] YouTube Studio 에서 해당 영상을 **Unlisted** 로 즉시 변경 (대표님 browser 수동 조작)
- [ ] 정책 위반 수준이면 **삭제** 결정 (shorts 는 삭제 후 동일 thumbnail 재업로드 AF-1 리스크 있으므로 Unlisted 권장)
- [ ] 해시태그 / 댓글 고정이 이미 반영됐다면 YouTube Studio 에서 수동 철회

### Diagnose
- [ ] `scripts/publisher/publish_lock.py` 의 48h+jitter gate 가 왜 우회되었는지 git log 추적: `git log -5 scripts/publisher/publish_lock.py`
- [ ] `scripts/publisher/kst_window.py` 가 승인한 시각인지 (평일 20-23 / 주말 12-15 KST) 검증
- [ ] `ai_disclosure.containsSyntheticMedia=True` flag 누락 여부 검사 (Phase 8 ANCHOR A — `grep -n "containsSyntheticMedia" scripts/publisher/`)
- [ ] `production_metadata` 첨부 여부 (Phase 8 PUB-04, `script_seed/assets_origin/pipeline_version/checksum` 4 필드)
- [ ] `.planning/publish_lock.json` 이 manual edit 으로 과거 timestamp 로 세팅됐는지 의심

### Recover
- [ ] `FAILURES.md` 에 F-OPS-XX append (사고 상세 + root cause + 대응 commit hash)
- [ ] 원인 수정 commit — D-2 Lock 기간 (2026-04-20 ~ 2026-06-20) 이면 `FAILURES.md` append 와 `scripts/` 수정만 허용, `.claude/` + `CLAUDE.md` 수정 금지
- [ ] `.github/workflows.disabled/` → `.github/workflows/` 복귀는 **1개씩 점진적** 으로 재활성 (가장 안전한 `skill-patch-count-monthly.yml` 부터, 업로드 관련 workflow 는 마지막)

### Verify
- [ ] `python -m scripts.rollback.stop_scheduler --dry-run` 으로 현재 lock + Task 상태 점검
- [ ] `python -m scripts.publisher.smoke_test --dry-run` 으로 upload lane 정상성 확인
- [ ] 첫 재활성 workflow = `skill-patch-count-monthly.yml` (업로드 없음, 가장 안전)
- [ ] 3 일 관찰 후 `analytics-daily.yml` 재활성 → 7 일 관찰 후 `drift-scan-weekly.yml` → 14 일 관찰 후 `ShortsStudio_Pipeline` + `ShortsStudio_Upload` 재등록

---

## 시나리오 2: Scheduler 버그 (GH Actions cron 실패 반복)

> 업로드 직접 관련은 아니지만 무인 운영 **관측 실명** 리스크입니다. KPI / drift scan 이 멈추면 대표님 의사결정 근거가 사라집니다.

### Detect
- [ ] GH Actions 페이지 (`https://github.com/kanno321-create/shorts_studio/actions`) 에서 3 회 연속 ❌ 확인
- [ ] 대표님 email (`kanno3@naver.com`) 에 `[shorts_studio] FAILURE` 메일 ≥ 3 건 도착
- [ ] `FAILURES.md` F-OPS-XX 3 건 이상 축적 (check_failures_append_only Hook 으로 자동 append 됐을 것)
- [ ] Windows Task 쪽 실패면 `Get-ScheduledTask -TaskName ShortsStudio_* | Get-ScheduledTaskInfo` 으로 LastTaskResult 확인

### Stop
- [ ] 해당 workflow YAML 을 `.github/workflows.disabled/` 로 이동하여 cron 자체 중단
- [ ] 의심되는 script 의 최근 commit 추적: `git log -5 scripts/<module>/`
- [ ] Windows Task 쪽 실패면 `schtasks /End /TN ShortsStudio_<name>` 로 러닝 인스턴스 종료

### Diagnose
- [ ] Actions 로그 다운로드: `gh run list --workflow <name> --limit 5` + `gh run view <run-id> --log`
- [ ] 원인 분류
  - (a) secret 만료 (YOUTUBE_TOKEN_JSON / ANTHROPIC_ 이외 키)
  - (b) API rate limit (YouTube Analytics / NotebookLM)
  - (c) code bug (최근 commit regression)
  - (d) Google API 변경 (v3 deprecation / scope 축소)
- [ ] OAuth token 만료 의심 시: `python scripts/publisher/oauth.py --reauth` (대표님 로컬 브라우저로 재인증)

### Recover
- [ ] 원인별 조치
  - secret 만료 → GH Settings > Secrets > Update `YOUTUBE_TOKEN_JSON`
  - rate limit → cron 간격 늘리기 (daily → 2-day) + quota 확인
  - code bug → `git revert <commit>` 또는 fix 후 재배포
  - API 변경 → NotebookLM RAG 로 scope 문서 재조사 후 scope 업데이트
- [ ] FAILURES.md F-OPS-XX append (root cause 기록, 향후 aggregate_patterns.py 가 반복 패턴 감지)

### Verify
- [ ] `workflow_dispatch` 로 수동 1 회 실행: `gh workflow run <name>` → exit 0 확인
- [ ] 24 h 관찰 후 정상 cron 재가동
- [ ] `gh run list --workflow <name> --limit 3` 에서 최근 3 건 전부 ✅ 확인 후 closing

---

## 시나리오 3: 학습 회로 오염 (SKILL patch 금지 위반)

> D-2 Lock 위반은 Phase 10 최초 2 개월 규율의 근본 실패입니다. 단순 revert 가 아니라 **기간 재시작** 을 동반해야 합니다.

### Detect
- [ ] `skill_patch_counter.py` 월간 리포트 `reports/skill_patch_count_YYYY-MM.md` 의 `violation_count > 0`
- [ ] `FAILURES.md` 에 F-D2-XX 엔트리 존재
- [ ] 또는 `drift_scan.py` 가 A급 drift 발견 → `.planning/STATE.md` 의 `phase_lock: true`
- [ ] `.claude/skills/*/SKILL_HISTORY/` 에 비정상 시점의 `.bak` 파일 생성 (backup_skill_before_write Hook 이 기록)

### Stop
- [ ] 긴급 전체 중단 3 명령 실행 — D-2 Lock 위반은 **운영 지속 불가** 수준
- [ ] 위반 commit 들의 hash 수집: `git log --since=2026-04-20 --name-only --pretty=format:"%H|%s" | grep -B1 -E "^\\.claude/(agents|skills|hooks)|^CLAUDE\\.md"`

### Diagnose
- [ ] 각 위반 commit 을 diff 로 검토: `git show <hash>`
- [ ] 의도된 수정인지 사고인지 판단
  - 사고 (잘못된 자동 patch) → revert 필수
  - 의도됐으나 Lock 기간 내 위반 → 규율 실패로 간주, FAILURES append + 2 개월 Lock 기간 **재시작**
- [ ] 영향 범위 측정: `drift_scan.py` 를 scan-only 모드로 재실행하여 A / B / C 급 전수 재분류

### Recover
- [ ] SKILL_HISTORY 에서 직전 버전 복원 (backup_skill_before_write Hook 덕분에 `.bak` 존재 보장):
  ```bash
  ls SKILL_HISTORY/<skill_name>/v*.md.bak | sort | tail -1
  cp SKILL_HISTORY/<skill_name>/v<timestamp>.md.bak .claude/skills/<skill_name>/SKILL.md
  ```
- [ ] 또는 `git revert <violation_commit>` 으로 cleanly revert (Private repo 1 인 운영이므로 history 보존 버전 권장)
- [ ] FAILURES.md 에 F-D2-XX append (skill_patch_counter 가 자동 기록했을 가능성 크지만, context / root cause 는 대표님 또는 나베랄 감마가 수동 보강)
- [ ] A 급 drift 연관이면 수정 완료 후 `python -m scripts.audit.drift_scan --clear-lock` 으로 phase_lock 해제

### Verify
- [ ] `python -m scripts.audit.skill_patch_counter` → `violation_count == 0`
- [ ] `python -m scripts.audit.drift_scan` → exit 0
- [ ] `grep "phase_lock: false" .planning/STATE.md` 확인
- [ ] D-2 Lock 기간 **재시작** — 2 개월 count 를 원위치 (사실상 Lock 기간 연장, 규율 실패 비용)
- [ ] 다음 달 `skill-patch-count-monthly.yml` 의 violation_count == 0 확인

---

## Audit Trail

모든 rollback 실행은 `FAILURES.md` 에 append-only 로 기록해야 합니다 (append-only 규율, `check_failures_append_only` Hook 자동 강제). 본 runbook 에 항목 추가 시 commit message 는 `docs(10-08): extend rollback scenario N` 형식으로 작성해주십시오.

각 시나리오 대응 후에는 다음 3 파일에 흔적이 남아야 합니다.

1. `FAILURES.md` F-OPS-XX 또는 F-D2-XX entry
2. `.planning/STATE.md` 최근 세션 박스에 복구 요약
3. 관련 scripts / workflow 의 git commit (`emergency(10):` 또는 `fix(10-XX):` prefix)

## Related

- Plan 10-01 `skill_patch_counter.py` — D-2 Lock violation count (감지 축)
- Plan 10-02 `drift_scan.py` — A 급 drift → phase_lock (잠금 축)
- Plan 10-04 `scripts/schedule/windows_tasks.ps1` — `-Unregister` 모드 재사용
- Plan 10-05 `scripts/session_start.py` — 30 일 rolling audit (학습 오염 조기 감지)
- `.planning/PHASE_10_ENTRY_GATE.md` §4 — 최초 rollback skeleton (본 문서가 확장)
- `scripts/publisher/publish_lock.py` — `MIN_ELAPSED_HOURS = 48`, `MAX_JITTER_MIN = 720` 상수

## Rollback 실행 메타

본 runbook 자체의 신뢰 기반은 `scripts/rollback/stop_scheduler.py` + `tests/phase10/test_rollback_procedures.py` 입니다. 실 사고 전에 다음 검증을 최소 1 회 수행해주십시오.

- [ ] `python -m scripts.rollback.stop_scheduler --dry-run` 실행 → stdout JSON 유효 + `"dry_run": true` 확인
- [ ] `pytest tests/phase10/test_rollback_procedures.py -v` 전수 PASS 확인
- [ ] `scripts/rollback/stop_scheduler.py` 의 `WINDOWS_TASKS` 상수가 `windows_tasks.ps1` 의 task 이름 3 종 (`ShortsStudio_Pipeline` / `ShortsStudio_Upload` / `ShortsStudio_NotifyFailure`) 과 일치함을 grep 으로 확인
