---
phase: 02-domain-definition
plan: 05
subsystem: infra
tags: [harvest, conflict-map, phase3-input, blacklist, gsd]

requires:
  - phase: 02-domain-definition
    provides: "02-RESEARCH.md § HARVEST_SCOPE.md Schema (draft judgments pre-approved)"
  - phase: 01-scaffold
    provides: "naberal_harness v1.0.1 Hook 3종 (deprecated_patterns.json regex ↔ Harvest Blacklist 이중 차단)"
provides:
  - "A급 13건 사전 판정 (2 승계 / 3 폐기 / 8 통합-재작성)"
  - "HARVEST_BLACKLIST Python dict (11 entries) — Phase 3 harvest-importer import 차단 목록"
  - "4 raw 디렉토리 매핑 (HARVEST-01/02/03/05 ↔ theme_bible_raw/remotion_src_raw/hc_checks_raw/api_wrappers_raw)"
  - "FAILURES 이관 경로 (_imported_from_shorts_naberal.md, append-only concat)"
  - "B/C급 26건 Phase 3 위임 알고리즘 (5-rule pseudocode)"
  - "Harvest 성공 기준 체크리스트 (Phase 3 /gsd:verify-work 3 입력)"
affects:
  - "Phase 3 Harvest (harvest-importer 에이전트 입력 완성)"
  - "Phase 4 Agent Team Design (A급 8 통합-재작성 항목 → 에이전트 프롬프트 설계 근거)"
  - "Phase 5 Orchestrator v2 (A-5, A-6 전수 폐기 → skip_gates 파라미터 자체 부재 설계)"

tech-stack:
  added: []
  patterns:
    - "사전 판정 + 위임 분리 패턴 (A급 13 Phase 2 확정, B/C급 26 Phase 3 위임)"
    - "Python dict 형식 Blacklist (agent parseable)"
    - "5-컬럼 테이블 스키마 (ID/요약/판정/근거/실행 지시)"

key-files:
  created:
    - ".planning/phases/02-domain-definition/02-HARVEST_SCOPE.md"
  modified: []

key-decisions:
  - "Phase 2 는 A급 13건만 판정 (D2-C 결정) — B/C급 26건은 Phase 3 harvest-importer 에 위임하여 Phase 2 스코프 폭발 방지"
  - "판정 분포 2/3/8 = 승계/폐기/통합-재작성 — RESEARCH.md Draft Judgments 와 완전 일치"
  - "longform/ 디렉토리 전수 폐기 (A-11) — 본 스튜디오 shorts 전용 (D-10 주 3~4편 쇼츠 확정)"
  - "Harvest Blacklist Python dict 형식 채택 — Phase 3 agent 가 eval 없이 로드 가능, regex + 경로 + 이유 3 필드"
  - "Plan 06 에서 consolidated commit 예정 — Plan 05 단독 commit 하지 않음 (Wave 3 병렬 실행 + 5 colocated studio 파일 일괄 커밋)"

patterns-established:
  - "A/B/C 등급 사전 판정 분리: 핵심 blocking 항목은 Planner 가 수작업 판정, 나머지는 agent 위임"
  - "판정 근거 5-컬럼 테이블: ID / 요약 / 판정 / 근거 (D# or SUMMARY §) / 실행 지시"
  - "Blacklist 이중 차단: HARVEST_BLACKLIST + pre_tool_use.py deprecated_patterns.json regex"

requirements-completed:
  - "INFRA-02 (SC#4: HARVEST_SCOPE.md 존재 + Phase 3 무엇을 가져올지/버릴지 명확)"

duration: 12min
completed: 2026-04-19
---

# Phase 02 Plan 05: HARVEST_SCOPE.md Summary

**A급 13 drift 사전 판정 (2 승계 / 3 폐기 / 8 통합-재작성) + Harvest Blacklist Python dict (11 entries) + 4 raw 디렉토리 매핑 + B/C급 26 위임 알고리즘 — Phase 3 harvest-importer 에이전트 입력 완성**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-19T02:35:00Z
- **Completed:** 2026-04-19T02:47:00Z
- **Tasks:** 1 (file creation only, commit deferred to Plan 06)
- **Files created:** 1 (`02-HARVEST_SCOPE.md`, 175 lines)

## Accomplishments

- CONFLICT_MAP.md A급 13건 전수 사전 판정 — 5-컬럼 테이블 (ID/요약/판정/근거/실행 지시) 완성
- 판정 분포 검증: **승계 2 (A-2, A-9) + 폐기 3 (A-5, A-6, A-11) + 통합-재작성 8 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13)** — RESEARCH.md Draft 와 100% 일치
- HARVEST_BLACKLIST Python dict 완성 — 11 entries: orchestrate.py:1239-1291 (A-6), TODO 4곳 (A-5), longform/ (A-11), create-video/ (A-12), create-shorts/SKILL.md (A-3), selenium (AF-8), orchestrate.py 전체 (D-7)
- 4 raw 디렉토리 매핑 완성 — HARVEST-01/02/03/05 와 1:1 대응 (theme_bible_raw / remotion_src_raw / hc_checks_raw / api_wrappers_raw)
- FAILURES 이관 경로 명시 — `_imported_from_shorts_naberal.md` append-only concat + 출처 주석 유지 규칙
- B/C급 26건 위임 알고리즘 — 5-rule pseudocode (blacklist > scope > session-77 canonical > cosmetic cleanup > default rewrite) + Planner pre-검토 힌트 (B:폐기6/승계2/판정8, C:cleanup4/폐기3/판정2/해결1)
- Harvest 성공 기준 5-item 체크리스트 — Phase 3 /gsd:verify-work 3 입력 완성

## Task Commits

**Task 1: Write 02-HARVEST_SCOPE.md** — 커밋 deferred to Plan 06 (consolidated studio commit)

Plan 05 은 Wave 3 병렬 플랜으로 Plan 04 (CLAUDE.md 수정) 와 동일 레포에서 다른 파일을 작성. 플랜 명세 `action` 섹션의 "Do NOT commit in this plan — commit happens in Plan 06 (studio consolidated commit)" 지시 준수. 현재 파일은 git untracked 상태로 Plan 06 에서 다른 5개 studio 파일과 일괄 커밋 예정.

## Files Created/Modified

- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` (created, 175 lines) — Phase 3 harvest-importer 에이전트 입력 문서. A급 13 판정 테이블 + Harvest Blacklist Python dict + 4 raw 매핑 + FAILURES 이관 + B/C급 위임 알고리즘 + Harvest 성공 기준.

## Verification

All acceptance criteria from PLAN satisfied:

| 기준 | Expected | Actual |
|------|----------|--------|
| File exists | `test -f` exit 0 | PASS |
| Line count | ≥ 150 | 175 |
| A-1 ~ A-13 각 ≥1 | 13/13 | A-1:10, A-2:2, A-3:5, A-4:3, A-5:7, A-6:4, A-7:2, A-8:2, A-9:2, A-10:2, A-11:4, A-12:4, A-13:2 |
| 판정 분포 섹션 | =1 | 1 |
| HARVEST_BLACKLIST | ≥1 | 2 |
| skip_gates | ≥1 | 6 |
| selenium | ≥1 | 2 |
| TODO(next-session) | ≥1 | 8 |
| theme_bible_raw | ≥1 | 2 |
| remotion_src_raw | ≥1 | 2 |
| hc_checks_raw | ≥1 | 2 |
| api_wrappers_raw | ≥1 | 3 |
| _imported_from_shorts_naberal.md | ≥1 | 2 |
| B/C급 26건 | ≥1 | 2 |
| Harvest 성공 기준 | =1 | 1 |
| Phase 3 harvest-importer | ≥1 | 9 |

## Decisions Made

- **위치 선택**: `studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` (phase 디렉토리 내부) 채택 — 02-CONTEXT / 02-RESEARCH 패턴 일치, Phase 3 에서 `HARVEST_DECISIONS.md` 로 승격 예정
- **판정 근거 명시**: 13건 모두 "근거" 컬럼에 D-1~D-10 Key Decisions 또는 SUMMARY.md 섹션 번호 cross-reference — 추후 감사 시 추적 가능
- **longform 전수 폐기**: A-11 단일 판정 + Blacklist path entry 로 이중 확정 — shorts 스튜디오 스코프 경계 강화
- **B/C 위임 알고리즘 우선순위**: blacklist > scope-boundary > session-77-canonical > cosmetic > default-rewrite 의 5-rule 체이닝 — Phase 3 agent 가 모호성 없이 판정 가능

## Deviations from Plan

None - plan executed exactly as written.

Plan 의 "Do NOT commit in this plan" 지시는 deviation 이 아닌 설계 의도 (Plan 06 consolidated commit 패턴). 파일 내용은 RESEARCH.md § HARVEST_SCOPE.md Schema (line 629-772) verbatim 과 일치하되, 설명 문장은 가독성 향상을 위해 일부 문맥 추가 (판정 분포 해설, 해석 규칙 명시, Tier 3 Lockdown 설명 확장).

## Issues Encountered

None.

## User Setup Required

None - Phase 2 는 외부 서비스 설정 없는 순수 문서 작업.

## Next Phase Readiness

**Phase 2 Plan 05 완결. Plan 06 (consolidated studio commit) 대기 중.**

Plan 06 은 다음 5개 파일을 단일 커밋에 포함:
1. `studios/shorts/CLAUDE.md` (Plan 04 수정분)
2. `studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` (본 Plan 05 산출물)
3. `studios/shorts/wiki/**` (Plan 03 산출물, staged)
4. `studios/shorts/.claude/**` (Phase 1 scaffold, staged)
5. `studios/shorts/.preserved/**`, README.md, SESSION_LOG.md, WORK_HANDOFF.md, .gitignore (Phase 1~3 staged)

**Phase 3 Harvest 진입 준비 완료:**
- harvest-importer 에이전트는 본 HARVEST_SCOPE.md § A급 13 판정 테이블 + § Harvest Blacklist 를 입력으로 사용
- D-6 3중 방어선 (Hook / Dispatcher / Audit) 중 Hook 층이 Blacklist 와 동일한 regex 로 이중 방어
- Phase 3 `/gsd:verify-work 3` 체크리스트 5개 항목 (4 raw 존재 + chmod -w + HARVEST_DECISIONS.md 생성 + FAILURES 이관 + Blacklist 준수) 모두 본 문서에서 파생

---

## Self-Check: PASSED

**File existence:**
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` (175 lines)

**Acceptance criteria (automated verify):**
- All 16 checks PASS (A-1~13 present + judgment distribution + Blacklist + 4 raw dirs + FAILURES + B/C delegation + success criteria + Phase 3 reference)

**Commit verification:**
- N/A — Plan explicitly defers commit to Plan 06 (consolidated studio commit). File currently in `git status` untracked state, confirmed staged-for-Plan-06.

---

*Phase: 02-domain-definition*
*Plan: 05*
*Completed: 2026-04-19*
