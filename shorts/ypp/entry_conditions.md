---
category: ypp
status: ready
tags: [ypp, shorts, monetization, korean-rpm, policy]
updated: 2026-04-19
source_notebook: shorts-production-pipeline-bible
---

# YPP (YouTube Partner Program) Entry Conditions

> 2026 기준 YPP 진입 기준 — Shorts 경로 공식 요건 + 한국 RPM baseline + 정책 risk + KPI 트래킹. Core Value = 외부 수익 실제 발생.

## 2026 진입 기준 (Shorts 경로)

- **1000 구독자** — 채널 전체 누적.
- **10M Shorts views / 90-day rolling window** — Shorts 경로 전용 threshold (long-form watch hour 경로와 별개).
- **long-form 경로 (4000 watch hours) 비적용** — 본 채널은 Shorts only 제작, watch hour 요건 미추구. Shorts 경로 단독 추적.
- **정책 준수 심사** — Community Guidelines + AdSense 계정 + 2-step verification + 18세+ (대표님 계정 조건 만족).
- **지역 요건** — 한국 eligible country 포함.

## Korean RPM (보수 baseline)

- **한국 Shorts RPM ~$0.20 / 1000 views** (2026 보수 추정; Shorts Fund 2023 종료 후 현 revenue share pool 45% 기준).
- **10M views / 90-day = ~$2000 USD 보수 baseline** — 월 환산 ~$667. YPP 진입 직후 최소 수익 기대치.
- **영어/일본어 더빙 확장 시 RPM 3~5배** (Phase 10 스택 확장 검토) — 단, 한국어 단독 채널 유지가 우선.

## 정책 risk (회피 필수)

- **Reused Content (E-P2)** — 재사용 판정 시 전체 채널 demonetize. PUB-04 Production metadata 첨부 (shotlist_manifest.json + voice attribution) 로 방어.
- **AI disclosure 누락 (COMPLY-03)** — AI 생성 영상은 YouTube 업로드 폼 `altered_content=synthetic` 플래그 필수. 누락 시 정책 위반.
- **AF-4 Voice Cloning** — 타인 목소리 합성 금지. Typecast + ElevenLabs voice library (공식 license) 만 사용. 대표님 본인 voice cloning 은 명시적 동의 기록 하에만.
- **AF-13 K-pop 직접 사용** — KOMCA + Content ID strike. 트렌딩 3~5초 sampling → royalty-free crossfade (T11 하이브리드 오디오).
- **COMPLY-04 중복 트랜스크립트 패턴** — Faceless + 동일 스크립트 템플릿 반복 시 AF-11 봇 패턴 판정. 주 3~4편 + 48시간+ 랜덤 간격.

## KPI 트래킹 (진입 궤도 측정)

- **월별 구독자 증가** — 목표 +50~100/월 (YPP 진입까지 10~20개월 런웨이).
- **90-day rolling Shorts views** — Analytics API `trafficSource=SHORTS` 필터링. KPI-01 cron 수집 (Phase 10).
- **진입률 (Completion Rate)** — 구독자 1000 / Shorts views 10M 각 %. 대시보드에 진입률 게이지 (Phase 9 대시보드).
- **월 단위 kpi_log.md 플러시** — KPI-02 정기 집계. Taste Gate (KPI-05) 월 1회 대표님 상/하위 3 평가와 연동.

## Related

- [[../algorithm/ranking_factors]] — Shorts shelf 진입 + 재생 ranking 신호 (views 10M 성취 수단)
- [[../kpi/retention_3second_hook]] — 3초 retention + 완주율 KPI (views 누적 전제 조건)
- [[MOC]]
