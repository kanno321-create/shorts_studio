---
name: project_server_infrastructure_plan
description: 서버 인프라 전환 계획 — 현재 대표님 Windows PC (임시), 향후 Mac Mini 로 이관 (상시 가동 서버). Scheduler/cron 구현은 양쪽 호환
type: project
---

# 서버 인프라 전환 계획

**박제 trigger**: 세션 #27 대표님 "맥미니 셋팅을 안 해놔서 구현만 해놓고, 한동안은 내가 윈도우 PC 로 너와 작업함".

## 현재 상태 (2026-04-20 ~ Mac Mini 셋팅 완료 시점)

- **개발·운영 환경**: 대표님 Windows 11 PC (Desktop)
- **Scheduler 구현**: Windows Task Scheduler (`scripts/schedule/windows_tasks.ps1`)
- **제약**: PC 가 꺼져있으면 영상 생성/업로드 cron stop → 주 3~4편 페이스 유지에 "PC on" 의존

## 장기 계획 (Mac Mini 이관 시점)

- **목표 서버**: Mac Mini (상시 가동, 24/7 on, headless 운영 가능)
- **Scheduler 이관**: Windows Task Scheduler → macOS **launchd** (`~/Library/LaunchAgents/com.naberal.shorts.*.plist`) 또는 **crontab** (`crontab -e`)
- **설치 대상**:
  - 영상 생성 파이프라인 (Kling/Typecast/Nano Banana 호출)
  - YouTube 업로드 (youtube_uploader.py + publish_lock + kst_window)
  - 로컬 캐시 저장소

## Phase 10 설계 방침 (이관 호환)

- Plan 4 (Scheduler) 는 **Windows 전용 ps1 스크립트**로 구현하되, **Mac Mini migration note** 를 Plan 문서에 명시
- GitHub Actions cron (analytics-daily / drift-scan-weekly / skill-patch-count-monthly) 는 **클라우드 기반** 이라 서버 전환 영향 없음 → 그대로 유지
- Windows Task Scheduler 만 이관 대상 → 영상 생성 + 업로드 2종 script
- Python 스크립트 (`scripts/*.py`) 는 **cross-platform** 이어야 함 (경로는 `pathlib.Path`, OS 의존 코드 최소화)
- 실패 알림 경로 (PowerShell SMTP) 는 이관 시 `scripts/schedule/notify_failure.py` (cross-platform python) 재사용 가능

## 이관 절차 요약 (Phase 11 candidate)

1. Mac Mini OS 기본 셋팅 (Python 3.11+ / uv / ffmpeg / git)
2. 저장소 clone: `git clone https://github.com/kanno321-create/shorts_studio.git`
3. `.env` + `config/client_secret.json` + `config/youtube_token.json` 대표님 수동 복사
4. `brew install ffmpeg` 등 시스템 deps
5. `uv pip install -r requirements.txt`
6. Windows Task Scheduler 대응 launchd plist 3종 신규 작성:
   - `com.naberal.shorts.pipeline.plist` (영상 생성)
   - `com.naberal.shorts.upload.plist` (업로드)
7. `launchctl load ~/Library/LaunchAgents/com.naberal.shorts.*.plist`
8. GitHub Actions secrets 그대로 유지 (서버 이관 영향 없음)

## 이관 판정 질문

이관 가능 시점 = 다음 3 조건 모두 충족:
- [ ] Mac Mini 구매 + OS 셋팅 완료 (대표님)
- [ ] Mac Mini 가 상시 가동 상태 (전원 + 네트워크 + Remote access)
- [ ] Phase 10 Windows 운영 1개월+ 실적 수집 완료 (실 FAILURES.md 축적, 이관 시 회귀 검증 기준 확보)

## Related

- `.claude/memory/project_shorts_production_pipeline.md` — 4-stage chain 구성
- `.planning/phases/10-sustained-operations/10-04-scheduler-hybrid-PLAN.md` — Windows Task Scheduler 구현 + Mac migration note
- `.planning/phases/10-sustained-operations/10-08-rollback-docs-PLAN.md` — 서버 사고 복구 경로 (Mac 이관 후에도 유효)
