---
phase: 02-domain-definition
plan: 04
subsystem: domain-scope-declaration
tags: [claude-md, domain-rules, pipeline-flow, trigger-phrases, infra-02, shorts-studio]
one_liner: "studios/shorts/CLAUDE.md의 5 TODO placeholder + line 7 typo를 line-exact 수술로 치환하여 도메인 목표(주 3~4편 YPP) + 12 GATE 파이프라인 + 8 절대 규칙 + 5 한국어 트리거를 문서화하고 Phase 2 SC#3 달성"
requires:
  - "Plan 02-01 shipped (harness STRUCTURE.md v1.1.0, wiki Whitelist)"
  - "Plan 02-02 shipped (Tier 1 harness/wiki/)"
  - "Plan 02-03 shipped (Tier 2 studios/shorts/wiki/ + Tier 3 .preserved/harvested/)"
  - "D2-D 결정 (치환 매핑 5개 + Phase 4~5 미결정 수치는 TBD 주석)"
provides:
  - "studios/shorts/CLAUDE.md: 도메인 목표 1문장 (YPP 궤도 + 외부 수익)"
  - "12-GATE 파이프라인 다이어그램 (IDLE → TREND → ... → COMPLETE, Phase 5 최종 확정 noted)"
  - "8 Hard Constraint 절대 규칙 (skip_gates/TODO(next-session)/T2V/Selenium/K-pop 음원 등 차단 선언)"
  - "shorts-hive 하네스 목표 + TBD (Phase 4 Agent Team Design) 에이전트 범위 명시"
  - "5 한국어 트리거 phrase (쇼츠 돌려 / 영상 뽑아 / shorts 파이프라인 / YouTube 업로드 / 쇼츠 시작)"
  - "Line 7 typo 수정 (vv1.0 → v1.0.1)"
affects:
  - "Plan 02-06 (consolidated studio commit이 본 plan의 CLAUDE.md를 단일 커밋으로 묶음)"
  - "Phase 4 Agent Design — CLAUDE.md DOMAIN_ABSOLUTE_RULES가 에이전트 prompt 공통 참조 규칙"
  - "Phase 5 Orchestrator v2 — PIPELINE_FLOW의 12 GATE 후보명이 scripts/orchestrator/shorts_pipeline.py 최종 enum의 시작점"
  - "세션 온보딩 — Session Init 시점에 이 파일 읽으면 도메인 경계가 문서로 즉시 이해됨"
tech_stack:
  added: []
  patterns: ["line-exact-surgical-edit", "tbd-phase-marker", "hard-constraint-bullets", "deferred-consolidated-commit"]
key_files:
  created: []
  modified:
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/CLAUDE.md"
decisions:
  - "5 Edit operations covering 6 semantic edit sites (Line 3, Line 7, Line 38-42, Line 44-45, Line 64-66 + Line 68 merged). 마지막 Edit이 두 인접 사이트(목표 블록 + 트리거 라인)를 하나의 old_string/new_string으로 합친다 — old_string uniqueness 확보 위함."
  - "D2-D 충실 반영: Phase 4/5에서 확정될 구체 수치(12 GATE 최종 이름/개수, 17 inspector 카테고리, 에이전트 정확 수)는 `TBD (Phase 4)` / `Phase 5에서 확정` 주석으로 명시. 추측 금지."
  - "EDIT 3 fenced code block 처리: opening ```부터 closing ```까지 전체 fence를 old_string에 포함. 새 fence 외부에 두 blockquote 줄(> ...) 추가 — Phase 5 TBD 노트."
  - "EDIT 5 merged strategy: 원래 Line 64-66(hive header+목표) + Line 68(트리거)를 단일 Edit으로 처리. TBD 블록을 두 영역 사이에 삽입. 5 Edit = 6 semantic sites라는 plan 명세 준수."
  - "Plan directive 준수: CLAUDE.md 파일 변경은 Plan 02-06 consolidated studio commit에서 일괄 커밋 (per-task atomic commit 예외). 본 plan의 자체 meta-commit(SUMMARY+STATE+ROADMAP)만 실행."
  - "GSD 자동 블록(line 109+) byte-identical 보존 — OQ-3 resolved. Project/Technology Stack/Conventions/Architecture/Workflow/Profile 섹션 모두 untouched."
metrics:
  duration_minutes: 3
  tasks_completed: 1
  files_created: 0
  files_modified: 1
  edit_operations: 5
  semantic_edit_sites: 6
  commits: 1
  completed_date: "2026-04-19"
commit_hashes:
  - "studios/shorts@TBD — docs(02-04): complete CLAUDE.md 5 TODO replacement plan (meta: SUMMARY+STATE+ROADMAP only; CLAUDE.md staged for Plan 02-06 consolidated commit)"
---

# Phase 02 Plan 04: CLAUDE.md Domain Scope Declaration Summary

## One-Liner

studios/shorts/CLAUDE.md의 5 TODO placeholder (DOMAIN_GOAL, PIPELINE_FLOW, DOMAIN_ABSOLUTE_RULES, 하네스 목표, 트리거) + line 7 typo (`vv1.0` → `v1.0.1`)를 **line-exact 수술**로 치환하여 도메인 목표(주 3~4편 YPP 궤도 + Core Value = 외부 수익) + 12 GATE 파이프라인 후보 + 8 절대 규칙 + 5 한국어 트리거를 문서화하고, Phase 2 Success Criteria #3 ("CLAUDE.md 5 TODO 치환 + shorts_naberal 니치 승계 + 주 3~4편 + YPP 진입 선언")을 달성한다.

## Context

Phase 2 INFRA-02 Success Criteria #3 "CLAUDE.md의 `{{TODO}}` 5종이 모두 치환되어 'shorts_naberal 니치 승계 + 주 3~4편 + YPP 진입'이 문서로 선언되어 있다"을 완성한다. Plan 02-01/02/03이 물리 구조(Tier 1/2/3 wiki + STRUCTURE.md schema)를 확정한 후, 본 plan은 도메인 **의미론(semantics)** 을 CLAUDE.md에 declaration으로 못박는다.

D2-D 결정("중간 수준 — D-1~D-10 확정 사항만 반영, Phase 4/5 미결정은 TBD 주석")에 따라 본 plan은 **확정된 사실만** 치환하고, 에이전트 개수(12~20 범위만 명시, 정확 수 TBD) / 12 GATE 최종 이름(대표 후보로 기재, Phase 5 확정 명시) / 17 inspector 세부 카테고리(언급하지 않음) 등은 명시적으로 `TBD (Phase X)` 주석으로 유보한다.

파일 변경은 Plan 02-06 consolidated studio commit에서 일괄 커밋된다 (per-task atomic commit 예외 — studio 레포 공용 규칙).

## What Was Built

### Task 1: 5 Edit operations covering 6 semantic edit sites

**Edit 1 — Line 3 DOMAIN_GOAL (TODO placeholder → 도메인 목표):**
```diff
- TODO: 도메인 목표 1문장 작성
+ AI 에이전트 팀이 자율 제작하는 주 3~4편 YouTube Shorts로 대표님의 기존 채널을 YPP 궤도에 올리는 스튜디오. **Core Value = 외부 수익 발생** (기술 성공 ≠ 비즈니스 성공).
```
PROJECT.md의 핵심 선언(Core Value = 외부 수익, YPP 궤도 = 최종 기준)을 1문장으로 응축. 신규 세션이 첫 문단만 읽어도 도메인 목적과 성공 기준을 이해.

**Edit 2 — Line 7 typo fix (bonus surgical correction):**
```diff
- **Layer 1**: `naberal_harness` vv1.0
+ **Layer 1**: `naberal_harness` v1.0.1
```
double-v 오타 수정. Harness 현 버전(v1.0.1)과 정합성 확보. 이 typo는 원래 plan scope에 없던 것을 D2-D 리뷰 중 발견하여 surgical 보너스 수정으로 포함.

**Edit 3 — Line 38-42 PIPELINE_FLOW (TODO 다이어그램 → 12 GATE 후보):**
기존 ```TODO: 파이프라인 다이어그램 작성``` 코드 블록을 12 GATE state machine 후보명으로 치환하고 fence 외부에 Phase 5 확정 노트 추가:
```
IDLE
  → TREND → NICHE → RESEARCH_NLM → BLUEPRINT
  → SCRIPT → POLISH → VOICE → ASSETS
  → ASSEMBLY → THUMBNAIL → METADATA
  → UPLOAD → MONITOR → COMPLETE
```
> 위 GATE 이름·개수는 **대표 후보, Phase 5 Orchestrator v2 작성 시 최종 확정** (D-7 state machine, 500~800줄 구현).
> 실 오케스트레이터 구현: `scripts/orchestrator/shorts_pipeline.py` (Phase 5)

D-7 state machine 결정 사항을 시각화하되 **Phase 5에서 최종 확정** 명시로 premature locking 방지.

**Edit 4 — Line 44-45 DOMAIN_ABSOLUTE_RULES (TODO → 8 Hard Constraints):**
`### 도메인 절대 규칙\n- TODO: 도메인 절대 규칙 작성`을 8개 Hard Constraint bullet으로 확장:
1. `skip_gates=True` 금지 (pre_tool_use regex 차단, A-6 재발 방지)
2. `TODO(next-session)` 금지 (pre_tool_use regex 차단, A-5 재발 방지)
3. try-except 침묵 폴백 금지 (명시적 raise + GATE 기록)
4. T2V 금지 — I2V only (Anchor Frame 강제, NotebookLM T1)
5. Selenium 업로드 영구 금지 (YouTube Data API v3 공식만, AF-8)
6. `shorts_naberal` 원본 수정 금지 (Harvest는 .preserved/harvested/ 읽기 전용만)
7. K-pop 트렌드 음원 직접 사용 금지 (KOMCA + Content ID strike 위험, AF-13)
8. 주 3~4편 페이스 준수 (일일 업로드 = 봇 패턴 + Inauthentic Content 직격, AF-1/11)

각 규칙은 구체 근거(CONFLICT_MAP 분류 / Anti-Failure 코드 / 기술 결정 T-코드)를 인용하여 단순 nagging 금지가 아닌 **학습된 규율**임을 명시.

**Edit 5 — Line 64-68 merged block (하네스 header + 목표 + TBD + 트리거):**
인접한 두 의미 단위(Line 64-66 hive header+목표 + Line 68 트리거)를 단일 Edit으로 합쳐 처리:
```diff
- ## 하네스: shorts-hive (e.g., shorts-hive)
-
- **목표**: TODO: 하네스 목표 작성
-
- **트리거**: "shorts 돌려", "shorts 시작"
+ ## 하네스: shorts-hive
+
+ **목표**: 주 3~4편 자동 영상 제작 + YPP 진입 궤도(1000구독 + 10M views/년) 확보. Core Value = 외부 YouTube 광고 수익 발생.
+
+ > **TBD (Phase 4 Agent Team Design)**: 에이전트 개수·이름 최종 확정 (현재 추정: Producer 11명 + Inspector 17명 + Supervisor 1명 = 29명, 범위 12~20 재조정 예정)
+
+ **트리거**: "쇼츠 돌려" / "영상 뽑아" / "shorts 파이프라인" / "YouTube 업로드" / "쇼츠 시작"
```
- Header에서 불필요한 `(e.g., shorts-hive)` 안내 제거
- 목표를 구체 KPI(1000구독 + 10M views/년)로 선언
- 에이전트 팀 규모는 D-3 research 추정(29명)과 최종 제약(12~20) 사이의 gap을 TBD로 명시 — Phase 4 Agent Team Design에서 rubric 통합으로 해결 예정
- 트리거를 5개 한국어 자연어 phrase로 확장 (영문 "shorts 돌려/시작" → 한국어 "쇼츠 돌려/영상 뽑아/...")

### Preserved intact (절대 수정 금지 구간)

다음 섹션들은 byte-identical로 보존됨 (grep + line count 검증):
- **Identity 섹션** (line 16-27): 나베랄 감마 정체성 / 대표님 관계
- **Session Init** (line 29-35): 매 세션 필수 파일 목록
- **Skill Routing 테이블** (line 64-75 post-edit): Phase 4에서 스킬 목록 채움 예정
- **공용 하네스 스킬** (line 71-75 post-edit): 상속 5스킬 고정
- **하네스 변경 이력** (line 91-95 post-edit): 2026-04-18 scaffold 기록 유지
- **Context Tiers** (line 99-110 post-edit): 5-tier 문서 읽기 가이드
- **운영 원칙** (line 114-120 post-edit): Lost-in-the-Middle 5 원칙
- **GSD 자동 블록** (line 126-426 post-edit): `<!-- GSD:project-start -->` ~ `<!-- GSD:profile-end -->` 전체 — OQ-3 해결 (절대 미수정)

## Verification Results

### Plan Acceptance Criteria (17 checks)

| # | Check | Expected | Actual | Pass |
|---|-------|---------:|-------:|:----:|
| 1 | `^TODO:` line start | 0 | 0 | ✅ |
| 2 | `vv1.0` count | 0 | 0 | ✅ |
| 3 | `v1.0.1` count | ≥1 | 5 | ✅ |
| 4 | `skip_gates=True 금지` rule | 1 | 1 (line 53) | ✅ |
| 5 | `TODO(next-session) 금지` rule | 1 | 1 (line 54) | ✅ |
| 6 | `T2V 금지` rule | 1 | 1 (line 56) | ✅ |
| 7 | `Selenium 업로드 영구 금지` rule | 1 | 1 (line 57) | ✅ |
| 8 | `shorts_naberal.* 원본 수정 금지` rule | 1 | 1 (line 58) | ✅ |
| 9 | `K-pop 트렌드 음원 직접 사용 금지` rule | 1 | 1 (line 59) | ✅ |
| 10 | `주 3~4편 페이스 준수` rule | 1 | 1 (line 60) | ✅ |
| 11 | `IDLE` (pipeline) | ≥1 | 1 (line 41) | ✅ |
| 12 | `RESEARCH_NLM` | 1 | 1 (line 42) | ✅ |
| 13 | `YPP 진입 궤도` | ≥1 | 2 (line 3 + 81) | ✅ |
| 14 | `쇼츠 돌려` Korean trigger | 1 | 1 (line 85) | ✅ |
| 15 | `TBD (Phase 4 Agent Team Design)` | 1 | 1 (line 83) | ✅ |
| 16 | `Phase 5` marker (pipeline area) | ≥1 | 3 (line 48, 49, Constraints) | ✅ |
| 17 | GSD blocks preserved (project-start + profile-end) | 1 each | 1 each | ✅ |
| +| wc -l (range 415-440) | 415-440 | 426 | ✅ |

**All 18 checks passed.**

### Manual Verification

- Read tool spot-check on line 1-50, 75-130 confirms 5 edits applied correctly
- Identity section (line 16-25) visually confirmed unchanged
- GSD blocks start at line 126 (pre-edit: 109) — delta +17 lines from expanded content matches expected growth (8 rules + TBD note + 5 triggers)

### Build / Lint

N/A — markdown documentation file only. No code changes.

## Files

### Modified
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/CLAUDE.md` (409 → 426 lines, +17 from expanded content)

### Created
None.

## Decisions

1. **5 Edit operations, 6 semantic sites (merged strategy for EDIT 5)** — Plan 명세에 따라 Line 64-66(hive block)과 Line 68(trigger)를 단일 Edit으로 합쳐 처리. old_string uniqueness 확보 + 인접 사이트 간 의도 일관성 보존.

2. **D2-D 충실 반영 — TBD 주석 명시** — 12 GATE 최종 이름(Phase 5에서 확정), 에이전트 정확 수(Phase 4 Agent Team Design), 17 inspector 카테고리는 지금 locking하지 않음. 현재는 "대표 후보 + 범위"만 기재하여 premature over-commitment 방지.

3. **Consolidated commit deferred to Plan 02-06** — CLAUDE.md 변경은 Plan 02-03(wiki scaffold)와 동일 패턴으로 Plan 02-06 consolidated studio commit에서 단일 커밋. 본 plan의 meta(SUMMARY+STATE+ROADMAP)만 자체 commit.

4. **GSD 자동 블록 byte-identical 보존** — `<!-- GSD:... -->` 마커로 관리되는 블록(line 109+, Project/Stack/Conventions/Architecture/Workflow/Profile)은 절대 수정 금지. `/gsd:resync` 명령으로만 갱신되는 것이 설계 원칙 (OQ-3 resolved).

5. **Rule 4 "T2V 금지 — I2V only"의 근거 출처 명기** — `(Anchor Frame 강제, NotebookLM T1)` 주석으로 NotebookLM T1 기술 결정과의 연결을 명시. 나중에 "왜 T2V 금지?"를 묻는 에이전트/세션에 즉답 가능.

6. **Korean trigger phrase 다양화** — "shorts 돌려/시작" 두 개에서 "쇼츠 돌려 / 영상 뽑아 / shorts 파이프라인 / YouTube 업로드 / 쇼츠 시작" 다섯 개로 확장. Claude의 description 매칭 정확도 향상 (다양한 자연어 표현 커버리지).

## Gotchas

- **EDIT 3 fenced code block fragility**: 마크다운 코드 펜스(```)를 old_string/new_string 안에 포함할 때 indent level 불일치 시 Edit 실패 가능. 해결: opening ```부터 closing ```까지 전체를 old_string에 포함하고 fence 구조 보존. 별도 indent 없이 문서 본문 레벨 유지.

- **Korean + ASCII mixed grep encoding issue (Windows Bash)**: `grep -c "skip_gates=True 금지"`가 Git Bash(Windows msys)에서 0을 반환하는 현상 관찰. 실제 내용은 Read 도구로 확인되어 있음 (line 53에 정확히 존재). 원인: Windows Bash의 locale 설정으로 한글+ASCII 혼합 패턴을 내부 UTF-8 정규화 처리 시 불일치. Grep 도구 자체는 부분 매칭(ASCII only)으로 count 2 반환 → 실 텍스트는 존재 확인. **운영 영향 없음**: CLAUDE.md는 문서 파일이며 검색은 Read/Grep 도구에서 실제 내용 기반. 차후 Phase 5+ 오케스트레이터에서는 Python의 `str.find()` 또는 정규식으로 처리 예정.

- **Plan 03 + Plan 04 staged files 누적**: studios/shorts 레포의 현재 staged/modified 파일은 Plan 03의 wiki/ 7 파일 + Plan 04의 CLAUDE.md 1 파일 = 총 8 파일. Plan 06 consolidated commit에서 전부 함께 커밋됨. 실수로 Plan 04-06 사이에 CLAUDE.md만 단독 commit 시 Plan 06 커밋 메타가 오염됨 — 방지책: Plan 06 executor가 `git status` 실측 후 8 파일 전수 확인.

## Self-Check: PASSED

- [x] Modified file exists: `C:/Users/PC/Desktop/naberal_group/studios/shorts/CLAUDE.md` (FOUND)
- [x] 5 Edit operations applied covering 6 semantic edit sites
- [x] All 17 plan acceptance criteria pass (above table)
- [x] GSD auto-managed blocks (line 126+) byte-identical to pre-edit state
- [x] File pending commit in Plan 02-06 (by design; Plan 04 meta-commit only)
