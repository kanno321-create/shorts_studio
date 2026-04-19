---
category: algorithm
status: ready
tags: [algorithm, shorts, ranking, retention, ctr, korean-seniors]
updated: 2026-04-19
source_notebook: shorts-production-pipeline-bible
---

# YouTube Shorts Ranking Factors

> 2026 기준 YouTube Shorts shelf 추천 + 재생 후 다음 영상 추천 알고리즘의 핵심 ranking 신호. 한국 시니어 시청자 skew (D-16) 반영.

## 핵심 신호 (우선순위 순)

1. **완주율 (Completion Rate)** — 영상 끝까지 시청 비율. Shorts shelf 진입 최대 신호. 목표 >40% (KPI-06). 한국 시니어는 긴 영상 중도 이탈이 빠름 → 60초 내 결론 도달 필수.
2. **3초 retention (3-second hook)** — 시청 시작 후 3초 시점의 잔존율. <50% 시 알고리즘이 추천 중단. 목표 >60% (KPI-06). 질문형 제목 + 숫자 ≥2자리 + 고유명사 ≥2자 hook 패턴 (CONTENT-01) 강제.
3. **CTR (Click-Through Rate)** — 썸네일 + 제목 노출 대비 클릭률. 썸네일 1-2 한글 글자 signature + Nano Banana Pro 94% 정확도. 하단 30% 회피 필수 (continuity_bible).
4. **재시청율 (Rewatch Ratio)** — 60초 Shorts의 경우 2회 이상 시청 비율. loop 유도 편집 + 마지막 1초 hook 회수 패턴으로 상향.
5. **보조 신호** — 좋아요/댓글/구독 클릭 (engagement) + 다음 Shorts 스와이프 지속 + 알림 설정. YPP 진입 후 가중치 증가.

## 한국 시니어 skew (D-16)

- **연령 50~65세 타겟** — 채도 낮은 톤, 빠른 정보 전달, 존댓말 narration 기본 (캐릭터 대사 예외는 CONTENT-02 duo persona — 탐정 하오체 + 조수 해요체).
- **인지 부하 낮은 편집** — 컷 전환 0.8~1.5초 간격 / 자막 16~20pt / 화면 하단 30% safe zone 확보.
- **알고리즘 함의** — 한국 시니어 Shorts 시청 피크 평일 20~23 KST / 주말 12~15 KST. 업로드 시각은 피크 3~6시간 전 (indexing lag 고려).

## 측정 소스

- **YouTube Analytics API `audienceRetention`** — 초 단위 잔존율. KPI-01 cron (Phase 10) 으로 월별 수집 → `kpi_log.md`.
- **`cardImpressionsRatio`** — 카드 노출 대비 클릭률. CTR 보조 신호.
- **Shorts shelf 진입 여부** — `trafficSource=SHORTS` 플래그. YouTube Analytics traffic-source breakdown 에서 집계.

## 피해야 할 패턴

- **AF-7 (Duplicate Tangent)** — 동일 thumbnail signature 7일 내 2회 이상 사용 금지. 알고리즘이 중복 판정 → 노출 감소.
- **AF-11 (Daily Upload Bot Pattern)** — 일일 업로드 = Inauthentic Content 직격. 주 3~4편 + 48시간+ 랜덤 간격 준수.
- **AF-2 (Clickbait Mismatch)** — 썸네일/제목 vs 영상 내용 불일치. 초기 3초 이탈 급증 → 3초 retention 파괴.

## Related

- [[../kpi/retention_3second_hook]] — 3초 retention >60% 목표 + 측정 방식
- [[../continuity_bible/channel_identity]] — 한국 시니어 시청자 skew (D-10 + D-16) 반영 시각 정체성
- [[MOC]]
