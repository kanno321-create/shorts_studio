---
category: kpi
status: ready
tags: [kpi, retention, hook, completion-rate, audience-retention, taste-gate]
updated: 2026-04-19
source_notebook: shorts-production-pipeline-bible
---

# 3-Second Hook Retention KPI

> Shorts 성과 최상위 지표 — 시청 시작 후 3초 시점 잔존율. KPI-06 목표 >60% + 완주율 >40% + 평균 시청 >25초 3종 패키지. 월 1회 kpi_log.md 자동 집계 + Taste Gate 대표님 샘플링 연동.

## 목표 (KPI-06)

| 지표 | 목표 | 임계 threshold | 측정 주기 |
|------|------|---------------|-----------|
| 3초 retention | **>60%** | <50% 시 영상 재제작 후보 | 업로드 7일 후 |
| 완주율 (Completion Rate) | **>40%** | <30% 시 구조 재검토 (스크립트/편집) | 업로드 7일 후 |
| 평균 시청 시간 | **>25초** (60초 Shorts 기준) | <18초 시 hook + 중반 편집 재점검 | 업로드 7일 후 |

3종 지표 중 2개 이상 FAIL 시 해당 에피소드 `kpi_log.md` 하위 3에 자동 배치 → 다음 Taste Gate 사이클 재검토.

## 측정 방식

- **YouTube Analytics API `audienceRetention`** — 초 단위 (0~60s) 잔존율 배열 반환. `retention[3]` 값이 3초 retention.
- **KPI-01 cron 수집** (Phase 10 도입) — 매일 03:00 KST 자동 실행, 전 영상의 30/60/90일 retention 업데이트.
- **KPI-02 월 1회 `kpi_log.md` 플러시** — `.planning/kpi_log.md` append-only 파일에 월별 상/하위 3 영상 + 지표 테이블 기록.
- **Shorts 전용 trafficSource 필터링** — `trafficSource=SHORTS` 플래그로 Shorts shelf 경유 시청만 집계. 검색/링크 유입은 별도 트래킹.

## Hook 설계 규칙 (CONTENT-01 하드코딩)

초기 3초 확보를 위해 Phase 4 `ins-narrative-quality` LogicQA q1/q2 에서 강제 검증:

- **q1: 질문형 제목** — 제목 또는 hook 문장이 `?` 로 끝나거나 의문 종결 (`~일까?`, `~할까요?`, `~인가?`). 존댓말 narration 원칙 준수.
- **q2: 숫자 ≥2자리 포함** — hook 3초 내 구체 수치 언급 (예: "23살", "100억", "3번째"). 추상 표현 단독 금지.
- **q3: 고유명사 ≥2자 포함** — 인물/지명/브랜드 고유명사 최소 1개. 모호한 대명사 단독 금지.

3 조건 중 2개 이상 FAIL 시 `ins-narrative-quality` main_q FAIL 강제 (Compliance 3 critical override 패턴 승계).

## Taste Gate 연동 (KPI-05)

- **월 1회 대표님 샘플링** — 상/하위 3 영상 각 3개 = 총 6개 블라인드 평가. 채점 기준: 3초 hook 몰입도 / 중반 이탈 지점 / 마지막 1초 회수 느낌.
- **FAILURES.md append** — 대표님 하위 3 평가에서 반복 지적 패턴 발견 시 `.claude/failures/FAILURES.md` 에 새 FAIL-NNN 항목 추가 (Phase 6 Plan 08 Hook append-only 규율 적용).
- **30일 집계** (Phase 10) — 동일 패턴 ≥3회 감지 시 `SKILL.md.candidate` 제안 → 7일 staged rollout 상태 기록.

## Related

- [[../algorithm/ranking_factors]] — 3초 retention = Shorts shelf 진입 최상위 ranking 신호
- [[../continuity_bible/channel_identity]] — 한국 시니어 타겟 + BGM tension preset (hook 3초 구간 전용)
- [[MOC]]
