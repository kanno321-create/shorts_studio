# Phase 9: Documentation + KPI Dashboard + Taste Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-20
**Phase:** 09-documentation-kpi-dashboard-taste-gate
**Mode:** `--auto` (YOLO 연속 5세션, 질문 제로 완주 원칙)
**Areas discussed:** ARCHITECTURE.md 구조, KPI 템플릿 포맷, Taste Gate 프로토콜, FAILURES 피드백 경로

---

## Area 1: ARCHITECTURE.md 구조 설계

### Q1.1 — 구조 레이아웃

| Option | Description | Selected |
|--------|-------------|----------|
| Section-based | 컴포넌트별 독립 섹션 (components / flow / data / external) | |
| Layered (Recommended) | State machine → agents → wiki → external 순 레이어 | ✓ |
| Diagram-first | 대형 다이어그램 1장 + 부속 설명 | |

**User's choice:** Layered (auto-selected — recommended default)
**Notes:** ROADMAP SC#1 문구 "12 GATE state machine + 17 inspector 카테고리 + 3-Tier 위키 구조를 다이어그램과 함께"를 그대로 반영하는 구조가 SC 검증 가능성을 최대화. → D-01

### Q1.2 — 다이어그램 렌더링 도구

| Option | Description | Selected |
|--------|-------------|----------|
| Mermaid (Recommended) | GitHub/VSCode/Obsidian 네이티브, 외부 의존 0 | ✓ |
| PlantUML | 풍부한 기능, 외부 서버 또는 Java 의존 | |
| ASCII art | 완전 독립, 복잡한 플로우 표현 한계 | |

**User's choice:** Mermaid (auto-selected — recommended default)
**Notes:** 신규 세션 30분 온보딩 목표 + 기존 wiki 일부 Mermaid 사용 중 → 일관성. → D-02

### Q1.3 — 온보딩 30분 측정 방식 (SC#1 검증)

| Option | Description | Selected |
|--------|-------------|----------|
| "느낌"으로 판단 | 주관적, 검증 불가 | |
| Reading time 주석 (Recommended) | 섹션별 `⏱ N min` 주석 + 총합 ≤ 30 | ✓ |
| 외부 stopwatch 측정 | 대표님 시간 낭비 | |

**User's choice:** Reading time 주석 (auto-selected — recommended default)
**Notes:** SC 자동 검증 가능. 총합 30분 초과 시 Plan 단계에서 섹션 분리/압축 트리거. → D-03

### Q1.4 — 파일 분할 여부

| Option | Description | Selected |
|--------|-------------|----------|
| 단일 docs/ARCHITECTURE.md (Recommended) | "어디부터 읽는가" 혼란 방지 | ✓ |
| 분할 docs/architecture/*.md | 모듈화, 신규 세션 탐색 부담 증가 | |

**User's choice:** 단일 파일 (auto-selected — recommended default)
**Notes:** 목차 + 외부 링크로 분할 없이 30분 온보딩 달성 가능. → D-04

---

## Area 2: KPI 템플릿 포맷

### Q2.1 — kpi_log.md 파일 경로

| Option | Description | Selected |
|--------|-------------|----------|
| `wiki/shorts/kpi_log.md` (ROADMAP 원문) | wiki 구조와 불일치 (`shorts` 하위 폴더 없음) | |
| `wiki/kpi/kpi_log.md` (Recommended) | 기존 5 카테고리 구조 정합 | ✓ |

**User's choice:** `wiki/kpi/kpi_log.md` (auto-selected — recommended default)
**Notes:** wiki/README.md가 이미 5 카테고리 확정. ROADMAP 경로 오기 수정으로 간주. → D-05

### Q2.2 — 데이터 포맷

| Option | Description | Selected |
|--------|-------------|----------|
| Monthly row table | 월 단위 집계만 | |
| Per-video time-series | 영상별 상세, 집계 부재 | |
| Hybrid (Recommended) | Target Declaration + Monthly Tracking 양립 | ✓ |

**User's choice:** Hybrid (auto-selected — recommended default)
**Notes:** SC#2가 "목표 선언 + 측정 방식 명시" 동시 요구 → hybrid 유일 정합. → D-06

### Q2.3 — 측정 방식 소스

| Option | Description | Selected |
|--------|-------------|----------|
| YouTube Analytics API v2 (Recommended) | 공식, audienceWatchRatio + averageViewDuration 필드 존재 | ✓ |
| YouTube Studio 수동 기록 | 대표님 시간 낭비, 자동화 불가 | |
| YouTube Data API v3 (기본 통계) | retention 세밀도 부족 | |

**User's choice:** YouTube Analytics API v2 (auto-selected — recommended default)
**Notes:** Phase 9는 API endpoint/필드명/주기만 템플릿에 선언. 실 연동 Phase 10. → D-07

---

## Area 3: Taste Gate 프로토콜

### Q3.1 — 영상 선별 방식

| Option | Description | Selected |
|--------|-------------|----------|
| 대표님이 직접 목록 선정 | 매월 6개 수동 선별, 부담 큼 | |
| Semi-automated (Recommended) | 스크립트가 KPI 기반 상위 3 / 하위 3 자동 선별 | ✓ |
| 무작위 샘플링 | 통계적 편향 없음, taste 평가 목적에 부합 X | |

**User's choice:** Semi-automated (auto-selected — recommended default)
**Notes:** 대표님 부담 최소화 + KPI 연동이 학습 회로의 본질. → D-08

### Q3.2 — 평가 폼 포맷

| Option | Description | Selected |
|--------|-------------|----------|
| Google Form | 외부 의존 + privacy + git 추적 불가 | |
| Markdown 단일 파일 (Recommended) | VSCode/Obsidian 직접 작성, git diff 추적 | ✓ |
| Web app (custom) | 과투자, 대표님 1인 사용에 부적합 | |

**User's choice:** Markdown 단일 파일 (auto-selected — recommended default)
**Notes:** `wiki/kpi/taste_gate_YYYY-MM.md` 형식. → D-09

### Q3.3 — 첫 회 dry-run 데이터 전략

| Option | Description | Selected |
|--------|-------------|----------|
| 실 영상 데이터 기다리기 | Phase 9 완결 30일 지연 | |
| 합성 샘플 6개 (Recommended) | 탐정/조수 페르소나 기반 그럴듯한 제목 | ✓ |
| Placeholder 텍스트 | 대표님 UX 검증 어려움 | |

**User's choice:** 합성 샘플 6개 (auto-selected — recommended default)
**Notes:** Phase 9 SC#3 "첫 회 dry-run 완료"를 실 데이터 없이 달성. 실 평가는 Phase 10 첫 월. → D-10

### Q3.4 — 평가 주기 자동화 시점

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 9에서 cron 완전 자동화 | 범위 초과, Phase 10 영역 | |
| 프로토콜 문서화만 (Recommended) | Phase 10에서 cron 구현 | ✓ |
| 수동 알림 | 대표님 reminder 피로 | |

**User's choice:** 프로토콜 문서화만 (auto-selected — recommended default)
**Notes:** `wiki/kpi/taste_gate_protocol.md` 작성. Phase 10 D-2 저수지 규율 준수. → D-11

---

## Area 4: FAILURES 피드백 경로

### Q4.1 — FAILURES.md append 방식

| Option | Description | Selected |
|--------|-------------|----------|
| 대표님 수동 복사-붙여넣기 | 누락 가능성, 피로도 | |
| Tagged auto-append 스크립트 (Recommended) | `scripts/taste_gate/record_feedback.py` 자동화 | ✓ |
| Git hook (post-commit) | 타이밍 불명확, 디버깅 어려움 | |

**User's choice:** Tagged auto-append (auto-selected — recommended default)
**Notes:** `[taste_gate]` prefix로 기존 FAILURES 엔트리와 구분. Phase 6 immutable 패턴 준수 (append only). → D-12

### Q4.2 — 어떤 점수부터 FAILURES 승격?

| Option | Description | Selected |
|--------|-------------|----------|
| 모든 평가 (상위 + 하위) | 노이즈 과다, 다음 월 Producer 입력 오염 | |
| 하위 3만 | 개선 신호는 포착하나 극명 실패 기준 불명확 | |
| 3점 이하만 (Recommended) | 실 실패 신호만 필터링, 노이즈 제거 | ✓ |

**User's choice:** 3점 이하만 (auto-selected — recommended default)
**Notes:** 5점 척도에서 3 = 평범. 3 이하 = 명확한 개선 필요 신호. → D-13

### Q4.3 — SC#4 샘플 검증 방법

| Option | Description | Selected |
|--------|-------------|----------|
| 실 영상 기다리기 | Phase 10까지 SC#4 미결 | |
| 합성 데이터로 end-to-end (Recommended) | dry-run 파일 → record_feedback.py → FAILURES entry 확인 | ✓ |
| 단위 테스트만 | "흘러드는 경로" 문구 요구 부족 | |

**User's choice:** 합성 데이터로 end-to-end (auto-selected — recommended default)
**Notes:** D-10의 합성 샘플 6개를 재사용. 스크립트 정합성 1회 실행 검증. → D-14

---

## Claude's Discretion

- Mermaid 다이어그램 내 노드 스타일 / 색상 / 정렬 순서
- taste_gate_YYYY-MM.md 평가 컬럼 세부 라벨 (품질 / 완성도 / 임팩트 중 선택)
- 스크립트 에러 메시지 언어 (한국어 default)
- ARCHITECTURE.md 내 코드 예시 언어 (Python default)

## Deferred Ideas

- 실 KPI 데이터 기반 첫 Taste Gate — Phase 10 Month 1
- YouTube Analytics API 실연동 — Phase 10
- Auto Research Loop (KPI → NotebookLM RAG) — Phase 10
- SKILL.md 자동 patch — Phase 10 Month 3+ (D-2 저수지 종료 후)
- 다국어 ARCHITECTURE.md — 필요성 미확정
- Taste Gate 기준 다변화 (3→5 KPI) — Phase 10 이후

---

*Mode note: `--auto` 플래그로 모든 옵션에서 "Recommended" 자동 선택. 대표님 리뷰 시 이 로그를 읽고 `09-CONTEXT.md` 수정 또는 재-discuss 요청 가능.*
