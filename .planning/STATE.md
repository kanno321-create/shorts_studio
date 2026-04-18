---
gsd_state_version: 1.0
milestone: v1.0.1
milestone_name: milestone
status: executing
last_updated: "2026-04-19T04:20:00.000Z"
progress:
  total_phases: 10
  completed_phases: 1
  total_plans: 16
  completed_plans: 14
  percent: 87
---

# STATE — naberal-shorts-studio

**Last updated:** 2026-04-19
**Session:** #15 (Phase 3 Wave 3 COMPLETE — Plan 03-08 HARVEST-DECISIONS + BLACKLIST-AUDIT shipped studio@15b827f (Task 1: 03-HARVEST_DECISIONS.md 39 rows — A:13 verbatim + B:16 + C:10 via 5-rule algorithm) + studio@c14ab95 (Task 2: 7-check blacklist grep audit PASS, 0 matches across .preserved/harvested/**). Wave 2 previously: 03-07/ad98b32 aggregate diff ALL_CLEAN + 03-07/1ff5768 FAILURES merge. Wave 1 all 4 raw dirs: 03-03/fba21e4, 03-04/4bc7ece, 03-05/51205ba, 03-06/aeac16b. Next: 03-09 lockdown (W4).)

---

## Project Reference

- **Core Value:** 외부 수익(YouTube 광고) 실제 발생 — YPP 진입 궤도(1000구독 + 10M views/년) 확보. 기술 성공 ≠ 비즈니스 성공.
- **Project Type:** Layer 2 도메인 스튜디오 (첫 번째) — naberal_harness v1.0.1 상속
- **Granularity:** fine (10 phases)
- **Mode:** yolo (자율 실행, GATE로 인간 감독)
- **Through-line:** shorts_naberal 39 drift conflict (A:13/B:16/C:10) 재발 차단

---

## Current Position

Phase: 03 (harvest) — EXECUTING
Plan: 8 of 9 complete in Phase 3 — Wave 0 (03-01/02) + Wave 1 (03-03/04/05/06) + Wave 2 (03-07) + Wave 3 (03-08) all shipped; W4 (03-09 lockdown) pending

- **Phase:** 3
- **Next Phase:** 3 (Harvest) — Entry point: `/gsd:execute-phase 3` (continue at 03-09)
- **Status:** Wave 3 complete — HARVEST-07 + HARVEST-08 satisfied. 39-row decision table canonical, 7-check blacklist audit 0 violations, Plan 09 lockdown gate cleared.
- **Progress:** [█████████░] 87%

---

## Phase Completion

- ✅ **Phase 1: Scaffold** — 2026-04-18 (session #10)
  - INFRA-01, INFRA-03, INFRA-04 완료
  - `studios/shorts/` 스캐폴드, Hook 3종 설치, 공용 5 스킬 상속
- ✅ **Phase 2: Domain Definition** — 2026-04-19 (session #14) — INFRA-02 완료
  - ✅ Plan 02-01: STRUCTURE.md v1.0.0 → v1.1.0 bump + wiki/ whitelisted (harness@8a8c32b)
  - ✅ Plan 02-02: harness/wiki/ Tier 1 scaffold (folder + README.md) created (harness@1ff2e34)
  - ✅ Plan 02-03: studios/shorts/wiki/ Tier 2 (5 categories + README + 5 MOC) + .preserved/harvested/ Tier 3 scaffold (committed in consolidated f360e17)
  - ✅ Plan 02-04: studios/shorts/CLAUDE.md 5 TODO replacement + line 7 typo fix (6 semantic sites via 5 Edit ops; committed in consolidated f360e17)
  - ✅ Plan 02-05: 02-HARVEST_SCOPE.md (175 lines) — A급 13 사전 판정 + HARVEST_BLACKLIST dict + 4 raw 매핑 + B/C 위임 알고리즘 (committed in consolidated f360e17)
  - ✅ Plan 02-06: 12/12 VALIDATION PASS + consolidated studio commit f360e17 (9 files, +449/-7) + SC 4/4 achieved + 02-VALIDATION.md frontmatter flipped (nyquist_compliant=true, wave_0_complete=true, status=complete)
- ⏳ **Phase 3~10**: Pending (Phase 3 entry-ready — 02-HARVEST_SCOPE.md 준비 완료)

---

## Performance Metrics

- **Requirements Mapped:** 96 / 96 (100%)
- **Orphaned REQ:** 0
- **Phases:** 10 (granularity=fine 목표 구간 내)
- **Harness Audit Baseline:** TBD (Phase 7 Integration Test에서 ≥ 80 확정)
- **YouTube 채널 구독자:** TBD (Phase 3 Harvest 시 현황 파악 — SUMMARY §12 open question)
- **월 운영비 예산:** ~$128/월 표준 (Sonnet $12 + Opus $9 + Kling $86.4 + Typecast $20 + Nano Banana $0.64)

---

## Accumulated Context

### Key Decisions (D-1 ~ D-10)

PROJECT.md § Key Decisions 참조. 10개 결정 모두 Pending 상태 — 각 Phase 완료 시점에 해당 D# 검증 + 상태 업데이트.

### Decisions Made This Session

1. **Phase 구조 10개 확정** — SUMMARY §10 Build Order 기반, DOMAIN_CHECKLIST 10단계와 1:1 대응
2. **Phase 4에 Content/Audio/Subt/Compliance REQ 통합** — rubric 동시 정의 원칙 적용 (분산 시 커플링 깨짐)
3. **Phase 5에 Video REQ 통합** — 오케스트레이터가 영상 생성 API wrapping 담당
4. **Phase 6에 FAIL-01~03 배치, FAIL-04는 Phase 10** — 저수지 인프라는 초기 구축, "첫 1~2개월 patch 금지"는 운영 단계 규율
5. **KPI-05/06(Taste Gate + 목표 지표)는 Phase 9, KPI-01~04(자동 수집 + Auto Research Loop)는 Phase 10** — taste 프로토콜 설치 후 실 운영에서 데이터 수집

### Session #12 Decisions (Phase 2 context)

6. **D2-A Tier 1 wiki = minimal** — 빈 폴더 + README.md만. 실 노드는 Phase 6. 이유: 선제 시드 = 나중 갈아엎기 리스크.
7. **D2-B Tier 2 wiki = MOC skeleton** — 5 카테고리(algorithm/ypp/render/kpi/continuity_bible) + 각 MOC.md. Phase 4 에이전트 prompt 참조 경로 고정 목적.
8. **D2-C Harvest scope = A급 13건 사전** — CONFLICT_MAP A급만 Phase 2에서 판정. B급/C급은 Phase 3 harvest-importer.
9. **D2-D CLAUDE.md 치환 = 중간** — D-1~D-10 반영, Phase 4~5 결정 수치는 TBD(Phase X) 명시.

### Session #14 Decisions (Plan 05 — HARVEST_SCOPE.md)

10. **A급 13 판정 분포 = 2/3/8** — 승계 2 (A-2 cuts[], A-9 탐정님 금지) / 폐기 3 (A-5 TODO, A-6 skip_gates, A-11 longform-scripter) / 통합-재작성 8 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13). RESEARCH.md Draft Judgments 와 100% 일치.
11. **HARVEST_BLACKLIST Python dict 형식** — Phase 3 harvest-importer 가 eval 없이 로드 가능. 11 entries: orchestrate.py:1239-1291 (A-6) + TODO 4곳 (A-5) + longform/ (A-11) + create-video/ (A-12) + create-shorts/SKILL.md (A-3) + selenium (AF-8) + orchestrate.py 전체 (D-7).
12. **4 raw 디렉토리 매핑 = HARVEST-01/02/03/05 와 1:1** — theme_bible_raw (HARVEST-01), remotion_src_raw (HARVEST-02), hc_checks_raw (HARVEST-03), api_wrappers_raw (HARVEST-05). HARVEST-04(FAILURES) 는 별도 이관 경로 (`_imported_from_shorts_naberal.md`).
13. **B/C급 26 위임 알고리즘 = 5-rule pseudocode** — blacklist > scope-boundary > session-77-canonical > cosmetic-cleanup > default-rewrite. Phase 3 harvest-importer 가 parse 하여 사용.

### Session #15 Decisions (Plan 03-07 — DIFF-VERIFY + FAILURES-MERGE)

18. **Aggregate diff = inline Python fallback** — diff_verifier.py --all flag not yet wired (Plan 01 scope limited to per-dir CLI). Inline implementation reuses identical deep_diff + filecmp.cmp(shallow=False) semantics; wiring --all is candidate improvement for future plan but not required for Phase 3 correctness.
19. **SOURCES locked list pattern (B-2 FIX)** — explicit `[Path('.../orchestrator.md')]` constant NOT glob expansion. RESEARCH.md §6 verified 1 source exists at 2026-04-19. Future FAILURES additions MUST extend list explicitly — code comment documents invariant. Prevents silent drift when shorts_naberal adds new FAILURES files.
20. **Ignore match via fnmatch.fnmatchcase** — matches shutil.ignore_patterns glob semantics used at Wave 1 copy time. Substring `in` containment would produce false positives on patterns like `*.pyc` vs `file.pyc.bak`. Critical for diff_verifier correctness.
21. **HARVEST-04 satisfied via idempotent marker-guarded append** — `<!-- source: ... -->` + `<!-- END source: ... -->` pair enables deterministic idempotency check; sha256 per source block provides downstream integrity audit path. Archive is read-only (D-2 저수지 regime reference for Phase 10 첫 1~2개월 SKILL patch 금지).

### Session #15 Decisions (Plan 03-08 — HARVEST-DECISIONS + BLACKLIST-AUDIT)

22. **Blacklist count invariant delegation (Plan 01 M-2 contract honored)** — Plan 08 does NOT re-assert `len(blacklist) == 10`; that invariant is owned by `blacklist_parser.parse_blacklist()` which raises ValueError on mismatch. Redundant asserts would violate DRY + SSoT. A/B/C count assertion (13/16/10) IS preserved at decision_builder entry because it validates a DIFFERENT invariant (CONFLICT_MAP parse integrity).
23. **Rule 1 deviation: narrowed Task 2 Audit 3 longform check** — plan's original `find ... -path "*/longform/*"` false-matched 6 legitimate Remotion composition files at `remotion_src_raw/components/longform/*.tsx` (harvested per Plan 03-04 studio@4bc7ece VALIDATION PASS). HARVEST_BLACKLIST `{path: "longform/"}` prohibits harvesting from `shorts_naberal/longform/` **source tree**, not arbitrary nested `longform/` subdirectories inside legitimately harvested source. Narrowed to `-maxdepth 1 -type d -name *longform*` — matches blacklist INTENT. Documented in audit_log.md + 03-08-SUMMARY.md.
24. **Inline Python fallback over harvest_importer --stage 6** — matches Wave 1 precedent (03-04-SUMMARY.md). Stage 6 requires prior stages 1-2 in same invocation to populate blacklist/manifest; direct call to `decision_builder.build_decisions_md()` is byte-identical semantics. `.tmp_build_decisions.py` used and deleted post-run (no repo pollution).
25. **39-row decision table verdict distribution locked** — 승계=2 (A-2, A-9) / 폐기=15 (A-5, A-6, A-11 + B-1, B-3, B-5, B-6, B-8, B-10, B-12, B-15 + C-1, C-6, C-7, C-8) / 통합-재작성=20 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13 + B-2, B-4, B-7, B-9, B-11, B-13, B-14, B-16 + C-3, C-4, C-9, C-10) / cleanup=2 (C-2, C-5). Rule distribution for B/C 26: rule1=10, rule2=2, rule3=0, rule4=2, rule5=12 (sum=26 ✓). Phase 4 agent designs can cite this table authoritatively.

### Session #14 Decisions (Plan 06 — Phase 2 Gate)

14. **Phase 2 게이트 = 12/12 VALIDATION PASS + consolidated commit** — Phase 3 진입 허가. 모든 pre-commit check 통과 시에만 commit, 하나라도 FAIL 시 commit 보류 원칙 (다행히 전부 통과).
15. **2-W3-03 literal pattern mismatch 관리** — VALIDATION.md status 컬럼에 나노트 ("literal pattern mismatch due to backticks — 8 rules semantically present, verified via flexible grep") 기록. 규칙 자체는 완전 존재, Phase 3 이후 validation script 개선 time 에 패턴 수정.
16. **Consolidated commit 스코프 = Phase 2 artifacts only** — `.claude/`, `.gitignore`, `README.md`, `SESSION_LOG.md`, `WORK_HANDOFF.md`, `.planning/config.json` 은 Phase 2 산출물이 아니므로 미포함. CLAUDE.md + wiki/ + .preserved/harvested/.gitkeep + 02-HARVEST_SCOPE.md 만 staged.
17. **harness vs studio 레포 분리 유지** — harness (8a8c32b + 1ff2e34) + studio (f360e17) 두 레포가 독립적으로 commit. REMOTE-02 (Phase 8) 전까지 푸시 없음.

### Active Todos (Phase 3 Harvest next)

- [x] Phase 2 gray areas 확정 (4건: Tier1 minimal / Tier2 MOC skeleton / A급 13 사전 판정 / CLAUDE.md 중간)
- [x] 02-CONTEXT.md + 02-DISCUSSION-LOG.md 커밋 (9b9039f)
- [x] `/gsd:plan-phase 2` 실행 → 02-01~06-PLAN.md 생성 (6 plans)
- [x] **Phase 2 Plan 01 execute → STRUCTURE.md v1.0.0→v1.1.0 bump (harness@8a8c32b, 2026-04-19)**
- [x] **Phase 2 Plan 02 execute → harness/wiki/ Tier 1 scaffold 생성 (harness@1ff2e34, 2026-04-19)**
- [x] **Phase 2 Plan 03 execute → studios/shorts/wiki/ Tier 2 + Tier 3 scaffold 생성 (committed in f360e17, 2026-04-19)**
- [x] **Phase 2 Plan 04 execute → CLAUDE.md 5 TODO 치환 + line 7 typo fix (committed in f360e17, 2026-04-19)**
- [x] **Phase 2 Plan 05 execute → 02-HARVEST_SCOPE.md A급 13 사전 판정 (175 lines, committed in f360e17, 2026-04-19)**
- [x] **Phase 2 Plan 06 execute → studio Phase 2 consolidated commit f360e17 + 12/12 VALIDATION PASS + SC 4/4 achieved (2026-04-19)**
- [x] **Phase 3 Harvest 진입**: `/gsd:execute-phase 3` — harvest-importer 에이전트 입력 = 02-HARVEST_SCOPE.md
- [x] **Phase 3 Plan 03-02 execute** → path_manifest.json ground-truth registry (studio@609c3f8, 2026-04-19) — 4 raw_dir sources verified, global_ignore blocks 5 secret patterns, 5/5 api_wrapper cherry_picks confirmed present
- [x] **Phase 3 Plan 03-01 execute** → harvest-importer AGENT.md + 7 Python stdlib modules (AGENT-06) — shipped prior to Wave 1
- [x] **Phase 3 Plan 03-03 execute** → theme_bible_raw copy (studio@fba21e4, 2026-04-19) — 7 channel bibles byte-identical, diff_verifier mismatches=[] (HARVEST-01)
- [x] **Phase 3 Plan 03-05 execute** → hc_checks_raw cherry_pick (studio@51205ba, 2026-04-19) — hc_checks.py 1129 lines + test_hc_checks.py byte-identical, orchestrate.py blacklist enforced (HARVEST-03)
- [x] **Phase 3 Plan 03-06 execute** → api_wrappers_raw cherry_pick (studio@aeac16b, 2026-04-19) — 5/5 wrappers byte-identical (elevenlabs_alignment, tts_generate, _kling_i2v_batch, runway_client, heygen_client), 0 selenium imports, orchestrate.py absent (HARVEST-05)
- [x] **Phase 3 Plan 03-04 execute** → remotion_src_raw copy (studio@4bc7ece, 2026-04-19) — 40 files / 0.161 MB, node_modules 758 MB excluded via shutil.ignore_patterns, diff_verifier mismatches=[], __pycache__/secret 0 hits (HARVEST-02)
- [x] **Phase 3 Wave 1 complete** → all 4 raw dirs shipped: theme_bible_raw (03-03) + remotion_src_raw (03-04) + hc_checks_raw (03-05) + api_wrappers_raw (03-06)
- [x] **Phase 3 Plan 03-07 execute** → aggregate diff ALL_CLEAN (studio@ad98b32) + FAILURES merge _imported_from_shorts_naberal.md (studio@1ff5768, 500 lines, sha256=978bb9381fee..., idempotent SOURCES-locked, HARVEST-04 satisfied, D-2 저수지 regime ready)
- [x] **Phase 3 Plan 03-08 execute** → 03-HARVEST_DECISIONS.md 39 rows (studio@15b827f, A:13 verbatim + B:16 + C:10 via 5-rule algorithm, verdict dist 2/15/20/2, rule dist 10/2/0/2/12 for B/C) + 7-check blacklist grep audit PASS (studio@c14ab95, 0 matches across all audits, Rule 1 deviation: narrowed longform check from overbroad */longform/* to top-level raw dir detection). HARVEST-07 + HARVEST-08 satisfied.
- [ ] **Phase 3 Wave 4** → lockdown (03-09, chmod -w / attrib +R on .preserved/harvested/, HARVEST-06)

### Blockers

- **현재 없음** (Roadmap 확정 완료)

### Open Questions (Phase별 deferred — SUMMARY §12)

| Question | Phase |
|----------|-------|
| 기존 YouTube 채널 현황 (구독/히스토리/니치) | Phase 3 |
| WhisperX + kresnik 실측 정확도 | Phase 4 |
| NotebookLM 프로그래매틱 API + rate limits | Phase 6 |
| KOMCA whitelist + AI 음악 정책 | Phase 5 |
| Runway vs Kling 한국 사용자 실측 | Phase 4 |
| transitions 라이브러리 vs 수동 | Phase 5 |
| 17 inspector 총 비용 (Fan-out calibration) | Phase 5 |
| YouTube Analytics 일일 한도 + cron | Phase 10 |
| Shotstack vs Remotion-only 색보정 | Phase 5 |
| Phase 03-harvest P01 | 7 | 2 tasks | 10 files |

### Plan Execution Log

| Plan | Duration (min) | Tasks | Files |
|------|----------------|-------|-------|
| Phase 02-domain-definition P02 | 2 | 1 | 1 |
| Phase 02-domain-definition P03 | 2 | 2 | 7 |
| Phase 02-domain-definition P05 | 12 | 1 | 1 |
| Phase 02-domain-definition P04 | 3 | 1 | 1 (5 Edit ops / 6 sites) |
| Phase 02-domain-definition P06 | 18 | 3 | 9 committed (f360e17) + 2 meta (VALIDATION, SUMMARY) |
| Phase 03-harvest P02 | 3 | 2 | 1 committed (609c3f8) + 1 meta (SUMMARY) |
| Phase 03-harvest P05 | 1 | 1 | 2 committed (51205ba: hc_checks.py 1129 lines + test_hc_checks.py) + 1 meta (SUMMARY) |
| Phase 03-harvest P06 | 4 | 1 | 6 committed (aeac16b: 5 wrappers + audit_log) + 1 meta (SUMMARY) |
| Phase 03-harvest P04 | 1 | 1 | 40 committed (4bc7ece: Remotion src tree — Root.tsx + index.ts + components/15 + compositions/11 + lib/12) + 1 meta (SUMMARY) |
| Phase 03-harvest P03 | 1 | 1 | 8 committed (fba21e4: 7 channel bibles + audit_log) + 1 meta (SUMMARY) |
| Phase 03-harvest P07 | 5 | 2 | 2 committed (ad98b32: audit_log Task 1 + 1ff5768: _imported_from_shorts_naberal.md 500 lines + audit_log Task 2) + 1 meta (SUMMARY) |
| Phase 03-harvest P08 | 3 | 2 | 2 committed (15b827f: 03-HARVEST_DECISIONS.md 39 rows + audit_log Task 1 / c14ab95: audit_log Task 2 blacklist audit PASS) + 1 meta (SUMMARY) |

---

## Session Continuity

### Files of Record

- `.planning/PROJECT.md` — 10 Key Decisions + Active 10 REQ (창업 비전)
- `.planning/REQUIREMENTS.md` — 96 v1 REQ / 17 카테고리 + Phase Traceability
- `.planning/ROADMAP.md` — 10 Phase 구조 (본 세션 생성)
- `.planning/STATE.md` — 본 파일 (세션 연속성)
- `.planning/research/SUMMARY.md` — Research 합성 (Build Order 기준점)
- `.planning/research/{STACK, FEATURES, ARCHITECTURE, PITFALLS, NOTEBOOKLM_RAW}.md` — 상세 리서치
- `.planning/config.json` — granularity=fine, mode=yolo

### Next Session Entry Point

```

1. Read .planning/STATE.md (← 본 파일)
2. Read .planning/phases/02-domain-definition/02-CONTEXT.md (Phase 2 결정 4건)
3. Execute: /gsd:plan-phase 2

```

### Hard Constraints (세션마다 재확인)

- `skip_gates=True`, `TODO(next-session)` 물리 차단 (pre_tool_use Hook)
- SKILL.md ≤ 500줄, description ≤ 1024자
- 에이전트 총합 12~20명
- 오케스트레이터 500~800줄
- `shorts_naberal` 원본 수정 금지 (Harvest는 읽기만)
- Phase 10 첫 1~2개월 SKILL patch 전면 금지 (D-2 저수지)

---

## Identity Reference

- **AI 정체성:** 나베랄 감마
- **호칭:** 대표님
- **작업 원칙:** 품질 최우선, 구조적 통제, 반복 drift 거부
- **세션 프로토콜:** WORK_HANDOFF.md → DESIGN_BIBLE.md → failures/orchestrator.md 순으로 로드 (secondjob_naberal CLAUDE.md 기준)

---

*Generated 2026-04-19 at roadmap creation. This file is the living memory of the project — update at every phase transition.*
