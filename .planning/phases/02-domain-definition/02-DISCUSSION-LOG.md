# Phase 2: Domain Definition - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 02-domain-definition
**Session:** #12 (세션 #11 /gsd:new-project 종료 직후 진입)
**Areas discussed:** Tier 1 wiki seed, Tier 2 wiki scaffold, Harvest scope, CLAUDE.md TODO 치환

---

## Gray Area Selection

**Question:** "Phase 2에서 논의할 gray areas를 선택해주십시오."

**Options presented (multiSelect):**

| Option | Description | Selected |
|--------|-------------|----------|
| Tier 1 wiki seed scope | naberal_harness/wiki/ 초기 시드 범위 결정 | ✓ |
| Tier 2 wiki scaffold depth | studios/shorts/wiki/ 초기 구조 깊이 결정 | ✓ |
| Harvest scope 폭 | CONFLICT_MAP 39건 판정 주체 Phase 2 vs Phase 3 | ✓ |
| CLAUDE.md 5 TODO 치환 수준 | 얇게/중간/두껍게 lock-in 수준 | ✓ |

**User's choice:** ALL 4 areas selected
**Notes:** 대표님이 4개 모두 선택하여 전 영역 논의 요청. 후속 진행은 각 영역에 대해 1개 핵심 결정 질문을 batch로 제시.

---

## Tier 1 seed

**Question:** "Tier 1 (naberal_harness/wiki/) 초기 시드 범위는? (Phase 6에서 NotebookLM RAG Fallback Chain 구축 예정)"

| Option | Description | Selected |
|--------|-------------|----------|
| 빈 폴더 + README만 (추천) | Phase 6에서 실 노드 추가. schema bump만 확정 | ✓ |
| fallback defaults 1-2개 | 공용 hardcoded defaults 노드 (korean_honorifics_baseline, youtube_api_limits) | |
| secondjob_naberal 이관 | API 규격/Compliance 도메인-독립 노드 이관 | |

**User's choice:** 빈 폴더 + README만 (추천)
**Notes:** Phase 6에서 Fallback Chain 실제 가동 시 정확한 노드 구성 확정됨을 근거로 선택. 선제 시드 = 나중 갈아엎기 리스크 회피.
**Rationale 기록:** 추후 stdio/rocket 스튜디오 창립 시 공통 노드 패턴 발견 후 batch 이관하는 것이 더 정확.

---

## Tier 2 scaffold

**Question:** "Tier 2 (studios/shorts/wiki/) 초기 스캐폴딩 깊이는? (Phase 4 에이전트 prompt가 @wiki/shorts/xxx.md 참조 가능해야 함)"

| Option | Description | Selected |
|--------|-------------|----------|
| 카테고리 5개 + MOC.md 스켈레톤 (추천) | algorithm/ypp/render/kpi/continuity_bible/ 폴더 + MOC 스켈레톤 | ✓ |
| 카테고리 폴더만 (파일 0) | 빈 폴더 5개. 참조 시 파일 부재 탐지 | |
| 완전 빈 wiki/ 폴더 | Phase 6에서 전체 구조 설계 | |

**User's choice:** 카테고리 5개 + MOC.md 스켈레톤 (추천)
**Notes:** Phase 4 에이전트 prompt가 @wiki/shorts/<category>/MOC.md 참조 경로를 미리 고정 가능. Phase 6에서 MOC 내용 채움. 존재하지 않는 파일을 참조해서 Phase 4 testing 시 조기 발견되는 리스크 방지.

---

## Harvest 39

**Question:** "CONFLICT_MAP 39건 판정을 Phase 2에서 어디까지 선제할지? (HARVEST_SCOPE.md 작성 지침)"

| Option | Description | Selected |
|--------|-------------|----------|
| A급 13건만 사전 판정 (추천) | A급=Blocking만 Phase 2에서 판정. B/C급은 Phase 3 harvest-importer에 위임 | ✓ |
| 39건 전수 사전 판정 | HARVEST_SCOPE.md를 Phase 3 blueprint 수준으로 작성. +1h 소요 | |
| 카테고리 범위만 선언 | 대분류만. 39건 전수는 Phase 3에서 | |

**User's choice:** A급 13건만 사전 판정 (추천)
**Notes:** A급은 이미 D-1~D-10 + SUMMARY Build Order에서 대부분 방향 확정되어 문서화만으로 완료 가능. B/C급은 실제 Harvest 맥락 필요하므로 Phase 3 harvest-importer 에이전트가 판정하는 것이 정확.

---

## TODO 5 fill

**Question:** "CLAUDE.md 5개 TODO (DOMAIN_GOAL / PIPELINE_FLOW / DOMAIN_ABSOLUTE_RULES / hive 목표 / TRIGGER) 치환 수준은?"

| Option | Description | Selected |
|--------|-------------|----------|
| 중간 — D-1~D-10 반영, 미결정 TBD (추천) | 확정 사항만 구체 반영. Phase 4~5 결정 수치는 TBD(Phase X) 명시 | ✓ |
| 얇게 — 철학 선언만 | 1-2문장 placeholder. Phase 4~10에서 모두 구체화 | |
| 두껍게 — 파이프라인+에이전트 고착 | 12 GATE 다이어그램 + 17 inspector 카테고리 명시 | |

**User's choice:** 중간 — D-1~D-10 반영, 미결정 TBD (추천)
**Notes:** 확정된 D-1~D-10은 치환해도 드리프트 없고, 미확정 수치는 TBD로 남겨 Phase 4 변경 시 desync 방지. 리드리프트 방지 원칙과 일치.

---

## Readiness Check

**Question:** "4개 결정 확정 (Tier 1 minimal / Tier 2 MOC skeleton / A급 13 사전 / CLAUDE.md 중간). CONTEXT.md 작성할까요?"

| Option | Description | Selected |
|--------|-------------|----------|
| CONTEXT.md 작성 (추천) | 결정 4건 + canonical_refs + code_context 정리. 이어 커밋 + STATE.md 업데이트 | ✓ |
| 추가 gray area 탐색 | HARVEST_SCOPE.md 구조, A급 13건 판정 검토 방식 등 | |
| 이전 결정 수정 | 4개 중 재논의 | |

**User's choice:** CONTEXT.md 작성 (추천)
**Notes:** 4개 결정이 모두 self-contained이라 follow-up 질문 없이 진행. 대표님 스타일(단일 턴 결정)과 일치.

---

## Claude's Discretion (사전 합의된 자율 영역)

- Tier 1 README.md 문체/구조 (표준 템플릿 수준)
- Tier 2 카테고리별 MOC.md placeholder 문구
- HARVEST_SCOPE.md 표 컬럼 순서/디자인
- CLAUDE.md 치환 세부 문장 구조 (D-1~D-10 요지 유지 전제)
- STRUCTURE.md 백업 파일명 (STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak)
- CLAUDE.md 라인 8의 "vv1.0" 오타는 이번 기회에 "v1.0.1"로 수정

## Deferred Ideas

- Tier 1 실제 공용 노드 추가 → Phase 6
- Tier 2 wiki 본문 작성 → Phase 6
- CONFLICT_MAP B급 16건 + C급 10건 판정 → Phase 3
- 12 GATE 명칭 최종 확정 → Phase 5
- 17 inspector 6 카테고리 세부 → Phase 4
- 도메인-독립 Tier 1 노드 추출 (blog/rocket 창립 시) → 미래 스튜디오 생성 시

---

**메타 관찰 (non-decision, audit용)**: 대표님이 4개 gray area에 대해 모두 "추천" 옵션을 단일 턴으로 수락. 이는 Phase 1 시점의 7-question deep questioning에서 확정한 D-1~D-10이 Phase 2 gray area 프레이밍을 이미 제약하고 있음을 시사 — 실질 옵션 공간이 좁았고, 추천 옵션이 PROJECT.md/SUMMARY.md의 philosophy와 일치. Phase 3 이후 gray area는 이보다 실무 세부(rubric schema, state machine 구현)가 많아질 예정.
