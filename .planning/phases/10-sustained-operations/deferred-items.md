# Phase 10 Deferred Items

> Out-of-scope discoveries during plan execution. Each entry includes the plan
> that discovered it, the scope boundary reasoning, and the proposed owner.

## D10-01-DEF-01 — Phase 5/6 pre-existing regressions (inherited)

**Discovered during:** Plan 10-01 (skill_patch_counter) regression sweep 2026-04-20.

**Failures:**
- `tests/phase05/test_kling_adapter.py::test_runway_valid_call_returns_path` — expects `gen3_alpha_turbo`, actual adapter emits `gen4.5` (Phase 9.1 stack migration `ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)`).
- `tests/phase05/test_blacklist_grep.py::test_no_t2v_in_orchestrator` — related stack migration artifact.
- `tests/phase05/test_line_count.py::test_api_adapters_under_soft_caps` — adapter line-count soft cap touched by Phase 9.1 rewrites.
- `tests/phase05/test_phase05_acceptance.py::*` — acceptance wrapper inherits the above.
- `tests/phase06/test_phase06_acceptance.py::test_full_phase06_suite_green` — cascades from Phase 5 regression.
- `tests/phase06/test_phase06_acceptance.py::test_phase05_suite_still_green` — same cascade.
- `tests/phase06/test_moc_linkage.py::test_moc_frontmatter_unchanged_scaffold` — wiki frontmatter drift since Phase 6.
- `tests/phase06/test_notebooklm_wrapper.py::test_default_skill_path_is_the_2026_install` — NotebookLM skill path constant drift.

**Scope boundary:** None of these tests touch `scripts/audit/`, `tests/phase10/`, or `reports/`. They are cascades from prior Phase 9.1 stack migration (`gen4.5` rename, Kling 2.6 Pro primary, Veo 3.1 Fast fallback) + Plan 06-08 `deprecated_patterns.json` 6→8 expansion + parallel Plan 10-02 executor (drift_scan) running concurrently. Plan 10-01 changes `scripts/audit/skill_patch_counter.py` + `tests/phase10/` + `reports/.gitkeep` + `scripts/audit/__init__.py` + `tests/phase10/conftest.py` only — zero file overlap with any failing test path.

**Evidence preserved:**
- `git log --oneline -3 -- scripts/orchestrator/api/runway_i2v.py` → `ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)` is the upstream cause of gen3_alpha_turbo → gen4.5 rename.
- STATE.md Session #19 entry: "2 Phase 5 regression failures attributable to Plan 06-08 scope (deprecated_patterns.json count 6->8) — out-of-boundary, logged for 06-08 follow-up."

**Proposed owner:** Phase 9.1 follow-up ticket or a dedicated `phase-regression-cleanup` plan after Phase 10 completion. Not Plan 10-01.

**Plan 10-01 in-scope tests:** `tests/phase10/` 11/11 GREEN (3 fixture + 8 CLI behavioural). Confirmed via `pytest tests/phase10/test_skill_patch_counter.py -q`.

**Phase 4 regression:** 244/244 GREEN (clean baseline preserved — phase04 untouched by any Phase 5/6/9.1 drift).

---

## D10-03-DEF-01 — Plan 10-02 drift_scan STATE.md frontmatter assertion

**Discovered during:** Plan 10-03 (fetch_kpi + monthly_aggregate) regression sweep 2026-04-20.

**Failure:**
- `tests/phase10/test_drift_scan.py::test_state_md_frontmatter_phase_lock_false_default` — asserts literal `phase_lock: false` substring must be present in `.planning/STATE.md` frontmatter, but current STATE.md frontmatter (written by `gsd-tools state advance-plan` after Plan 10-02) omits the `phase_lock` field when default is false.

**Current STATE.md frontmatter:**
```
gsd_state_version: 1.0
milestone: v1.0.1
milestone_name: milestone
status: executing
last_updated: "2026-04-20T..."
progress: { ... }
```

**Scope boundary:** Plan 10-03 only touches `scripts/analytics/`, `scripts/publisher/oauth.py` (Wave 0 done), `tests/phase10/test_fetch_kpi.py`, `tests/phase10/test_monthly_aggregate.py`, `wiki/kpi/kpi_log.md`, and `tests/phase08/test_oauth_installed_flow.py` (scope count fix). STATE.md frontmatter management is owned by gsd-tools orchestrator, not Plan 10-03. The assertion pattern should be `phase_lock: (false|true)? (missing means false)` — Plan 10-02 scope.

**Plan 10-03 in-scope tests:** `tests/phase10/test_fetch_kpi.py` 10/10 GREEN + `tests/phase10/test_monthly_aggregate.py` 10/10 GREEN. Plan 10-01/10-02 in-scope tests 50/51 GREEN (1 pre-existing drift_scan failure out-of-scope).

**Proposed owner:** Plan 10-02 follow-up (either (a) harden test to accept missing `phase_lock` field as implicit `false`, OR (b) teach gsd-tools to always write `phase_lock: false` explicitly).

---

## D10-03-DEF-02 — Phase 5/6/7/8 regression cascade sweep (inherited)

**Discovered during:** Plan 10-03 background Phase 8 sweep 2026-04-20 (15m13s full).

**Failures (4, before Plan 10-03 Task 1 fix):**
- `tests/phase08/test_regression_986_green.py::test_phase05_green`
- `tests/phase08/test_regression_986_green.py::test_phase06_green`
- `tests/phase08/test_regression_986_green.py::test_phase07_green`
- `tests/phase08/test_regression_986_green.py::test_combined_986_green`

**Root cause:** Same inherited cascade as D10-01-DEF-01 (Phase 9.1 stack migration: gen3_alpha_turbo → gen4.5 + Kling 2.6 Pro primary). These sweep tests aggregate phase05+phase06+phase07 which contain pre-existing failures.

**Scope boundary:** Zero file overlap with Plan 10-03. Plan 10-03 fixed the 5th failure (`test_scopes_are_exactly_two_in_order` → `_three_in_order`) which was a direct regression caused by Plan 10-03 Wave 0 scope expansion — that fix is in-scope.

**Plan 10-03 verification:** `pytest tests/phase08/test_oauth_installed_flow.py -q` → 6/6 GREEN post-fix.

**Proposed owner:** Same as D10-01-DEF-01 — dedicated `phase-regression-cleanup` plan after Phase 10 main sequence.

---

## D10-06-DEF-01 — Plan 10-07 trajectory_append collection error (inherited from Plan 10-07 Wave 0 RED TDD)

**Discovered during:** Plan 10-06 (research_loop) regression sweep 2026-04-20.

**Failure:**
- `tests/phase10/test_trajectory_append.py` — ModuleNotFoundError: `No module named 'scripts.analytics.trajectory_append'`. Test file seeded as a RED TDD anchor in commit `39c79c1 test(10-07): RED — 13 failing tests for trajectory_append (SC#6)` before the Plan 10-07 implementation module was written.

**Scope boundary:** Plan 10-06 touches `scripts/research_loop/` + `tests/phase10/test_research_loop.py` + `wiki/kpi/monthly_context_template.md` + `FAILURES.md` appends only. Zero overlap with `scripts/analytics/trajectory_append.py` (Plan 10-07 territory). Plan 10-07 will satisfy this RED anchor when its GREEN phase ships.

**Plan 10-06 in-scope tests:** `tests/phase10/test_research_loop.py` 16/16 GREEN. Full Phase 10 sweep (excluding the Plan 10-07 RED file + D10-03-DEF-01 pre-existing failure): 95/96 GREEN.

**Proposed owner:** Plan 10-07 (trajectory_append) executor.

---

## D10-01-DEF-02 — skill_patch_counter idempotency 결함 (Phase 11 candidate)

**Discovered during:** Phase 10 post-verification FAILURES.md inspection 2026-04-21.

**증상:**
- `scripts/audit/skill_patch_counter.py` 가 동일 violation set 을 재실행할 때마다 새 `F-D2-NN` entry 를 FAILURES.md 에 append.
- Phase 10 execute 중 Wave 1 + verifier spot-check + manual smoke test 등으로 총 5회 실행되어 F-D2-01~F-D2-05 가 **완전 동일 내용으로 중복 기록** 됨.
- 대표님 승인 플랜 Risk #1 옵션 D (투명 기록) 는 violation 당 1 entry 의도 — 실행 횟수 비례 append 는 의도 외.

**사후 조치 (2026-04-21 commit):**
- FAILURES.md 에서 F-D2-02~F-D2-05 제거, F-D2-01 만 "directive-authorized" 주석과 함께 보존.
- 본 D10-01-DEF-02 에 defect 박제.

**Root cause 가설:**
- `skill_patch_counter.py` 가 append 전 기존 FAILURES.md 를 grep 하여 "동일 commit 집합이 이미 기록됐는가" 를 확인하지 않음.
- 결과: 월 1회 scheduler (Plan 10-04 `skill-patch-count-monthly.yml`) 가 실행될 때마다 같은 violation 을 중복 append 하는 버그 잠재.

**Scope boundary:** Phase 10 main sequence 완결 후 발견된 **구현 품질 defect**. Phase 10 verification blocker 아님 (violation 감지 + 기록 기본 기능은 정상 작동).

**권장 해결 (Phase 11 후보):**
1. `skill_patch_counter.py` 에 idempotency check 추가 — append 전 FAILURES.md grep 으로 동일 commit hash set 존재 여부 확인. 이미 기록된 violation 은 skip.
2. 월 1회 scheduler 가 재실행되어도 동일 사실을 반복 기록하지 않고, **신규 violation 만** append 하도록 동작.
3. `tests/phase10/test_skill_patch_counter.py` 에 idempotency 케이스 추가 (동일 git 상태에서 2회 연속 실행 → 첫 회만 append, 2회차는 skip).

**Proposed owner:** Phase 11 entry gate — scheduler 1차 월간 실행 (2026-05-20 경) 전 선행 필요.

---

## D10-SCRIPT-DEF-01 — scripter 대본 품질 NLM-direct 재설계 (Phase 11 candidate)

**Discovered during:** v1.0.1 milestone audit pre-flight 대화 2026-04-21 (대표님 질문 "대본의 질이 궁금하네").

**증상:**
- `wiki/script/NLM_2STEP_TEMPLATE.md` 는 대표님이 세션 70·77 에서 박제한 **NLM 2-step 대본 생성 규약** (Step 1 `crime-stories-+-typecast-emotion` 노트북 사건 발굴 → Step 2 `script-production-deep-research` 노트북 시나리오 제조, 대본 본문 NLM 단독 작성).
- 현재 `scripter` agent 는 Claude Opus 가 `blueprint + scenes + research manifest + channel bible` 을 받아 **직접 대본 JSON 을 생성**. NLM 은 `researcher` 를 통해 **citation 공급자 역할만** 수행.
- Gap: "방대한 소스 기반 NLM 이 대본 문장 자체를 생성" vs "NLM citation 기반 Claude 가 재창작" — source-grounded 강도 + 소스 디테일 전이 품질이 후자에서 열화 가능성.

**근본 원인 가설:**
- Phase 4~5 설계 시 Shorts 59s 는 NLM 2-step longform(15분) 템플릿 적용 대상 아니라고 판단됨. NLM_2STEP_TEMPLATE.md 는 박제만 되고 scripter agent 구조에 미반영.
- `scripts/notebooklm/query.py` default 노트북은 Step 2 (`script-production-deep-research`) 단일. Step 1 사건 발굴 노트북 호출 구조 부재.

**Scope boundary:** v1.0.1 milestone 구조 완결 범위 밖. 대표님 Core Value (외부 수익) 직결 품질 이슈이나 **구조(structure) 가 아닌 품질(quality) 차원** — milestone audit 의 requirement coverage + cross-phase integration blocker 아님.

**권장 해결 (Phase 11 candidate, 대표님 판단 대기):**
1. **옵션 A**: 현 시스템으로 영상 1~2편 실제 제작 → 품질 평가 → 부족 시 재설계 (경험적 검증, 즉시 실행 가능).
2. **옵션 B**: `scripter` 를 "NLM 2-step 호출 모드" 로 재설계 — Step 1 발굴 노트북 query → Step 2 시나리오 노트북 query → Claude 는 rubric 검수·후처리만. `scripts/notebooklm/query.py` 를 2-notebook 호출 구조로 확장.
3. **옵션 C**: Shorts/Longform 2-mode 분리 — Shorts(59s, 현 scripter 유지) + Longform(15분, 순수 NLM 2-step). channel_bible.길이 필드 기반 자동 routing.

**Proposed owner:** Phase 11 첫 영상 제작 직후 (2026-04-21~2026-05-05 경). 대표님의 실 영상 1~2편 품질 평가를 근거로 옵션 선택.
