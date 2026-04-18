---
phase: 02-domain-definition
plan: 03
subsystem: tier2-tier3-wiki-scaffold
tags: [wiki-tier2, wiki-tier3, moc-skeleton, infra-02, shorts-studio]
one_liner: "Tier 2 wiki/ 5 카테고리 MOC 스캐폴드 + Tier 3 .preserved/harvested/ 빈 디렉토리 물리 생성 — Phase 4 agent prompt 참조 경로(@wiki/shorts/<category>/MOC.md) 활성화 및 Phase 3 harvest-importer 타겟 확보"
requires:
  - "Plan 02-01 shipped (harness/STRUCTURE.md v1.1.0, wiki/ Whitelist)"
  - "studios/shorts repo clean master (no blocking uncommitted state)"
  - "D2-B 결정 (MOC skeleton only, 실 노드는 Phase 6)"
provides:
  - "studios/shorts/wiki/ 디렉토리 + README.md (Tier 2 home)"
  - "5 category folders (algorithm/, ypp/, render/, kpi/, continuity_bible/) each with MOC.md scaffold"
  - "studios/shorts/.preserved/harvested/ 빈 디렉토리 + .gitkeep (Tier 3 scaffold)"
  - "Phase 4 agent prompt 참조 경로 `@wiki/shorts/<category>/MOC.md` 유효화"
  - "Phase 3 harvest-importer (HARVEST-01~06)를 위한 Tier 3 쓰기 타겟"
affects:
  - "Plan 02-06 (consolidated studio commit이 본 plan의 7 파일 + 6 디렉토리를 단일 커밋으로 묶음)"
  - "Phase 3 Harvest — .preserved/harvested/ 4 raw subdirs 생성 + chmod -w 대상"
  - "Phase 4 Agent Design — 에이전트 prompts가 5 MOC.md를 @-reference로 참조"
  - "Phase 6 Wiki + NotebookLM — 각 MOC.md의 Planned Nodes 4~5개씩 총 22 노드 실 작성 대상"
tech_stack:
  added: []
  patterns: ["moc-skeleton-pattern", "tier-separation-physical", "gitkeep-placeholder", "deferred-consolidated-commit"]
key_files:
  created:
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/README.md"
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/algorithm/MOC.md"
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/ypp/MOC.md"
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/render/MOC.md"
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/kpi/MOC.md"
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/continuity_bible/MOC.md"
    - "C:/Users/PC/Desktop/naberal_group/studios/shorts/.preserved/harvested/.gitkeep"
  modified: []
decisions:
  - "Plan directive 준수: wiki/ + .preserved/ 컨텐츠 파일은 Plan 02-06 consolidated studio commit에서 일괄 커밋 (per-task atomic commit 예외). 본 plan의 자체 meta-commit(SUMMARY+STATE+ROADMAP)만 실행"
  - "Per-category Planned Nodes count: algorithm/ypp/kpi = 4 nodes each, render/continuity_bible = 5 nodes each (총 22 — RESEARCH.md line 426-460 verbatim)"
  - "MOC.md 공통 템플릿: frontmatter(category/status/tags/updated) + H1 + Scope(1-line) + Planned Nodes(checkbox list) + Related(3-item) + Source References(3-item)"
  - "`.preserved/harvested/.gitkeep` 내용 = 한 줄 주석 (빈 파일 대신). Phase 3 HARVEST-01~06 역할 명시로 의도 보존"
  - "Root CLAUDE.md 상대경로는 MOC.md 기준 [[../../CLAUDE.md]] (category/ → wiki/ → studio root)"
metrics:
  duration_minutes: 2
  tasks_completed: 2
  files_created: 7
  files_modified: 0
  directories_created: 6
  commits: 1
  completed_date: "2026-04-19"
commit_hashes:
  - "studios/shorts@c7292eb — docs(02-03): complete Tier 2 wiki scaffold + Tier 3 empty dir plan (meta: SUMMARY+STATE+ROADMAP only; wiki/ + .preserved/ staged for Plan 02-06 consolidated commit)"
---

# Phase 02 Plan 03: Tier 2 Wiki Scaffold + Tier 3 Empty Directory Summary

## One-Liner

studios/shorts 레포에 Tier 2 `wiki/` (5 카테고리 + README + 5 MOC.md 스캐폴드) 과 Tier 3 `.preserved/harvested/` (빈 디렉토리 + .gitkeep) 물리 구조를 생성하여, Phase 4 에이전트 프롬프트가 `@wiki/shorts/<category>/MOC.md` 형식으로 참조 가능한 상태를 만들고 Phase 3 harvest-importer의 쓰기 타겟을 확보한다.

## Context

Phase 2 INFRA-02 Success Criteria #1 "3개 Tier 디렉토리가 모두 존재한다"의 **Tier 2 + Tier 3 부분**을 완성한다. Tier 1(`harness/wiki/`)은 Plan 02-02에서 병렬 처리되며, 두 plan이 합쳐져 "3개 Tier 디렉토리 모두 존재" 상태를 만든다.

D2-B 결정("Tier 2 wiki = MOC skeleton만, 실 노드는 Phase 6")에 따라 본 plan은 **디렉토리 + 스켈레톤 파일**만 생성한다. 실제 지식 노드(ranking_factors.md, kling_api_spec.md 등 22건)는 Phase 6 (Wiki + NotebookLM Integration)에서 채워진다.

Plan 02-01(harness STRUCTURE.md v1.1.0 bump, harness@8a8c32b)이 선행 완료되었으나 본 plan은 `studios/shorts` 레포에서 단독 실행 — harness Whitelist 영향 없음(studio 레포는 자체 STRUCTURE.md 없음, OQ-1 해결됨).

## What Was Built

### Task 1: Tier 2 wiki/ Scaffold (6 files + 6 directories)

**Directory creation:**
```bash
mkdir -p wiki/{algorithm,ypp,render,kpi,continuity_bible}
```
6 디렉토리 생성: `wiki/` + 5 카테고리 서브폴더.

**File 1: `wiki/README.md`** — Tier 2 home 문서
- 3-Tier 분류 설명 (harness/wiki, studios/shorts/wiki, .preserved/harvested)
- 5 카테고리 테이블 + Obsidian-style `[[category/MOC]]` 링크
- NotebookLM 2-노트북 연동 계획 ("노트북 A: 일반", "노트북 B: 채널바이블")
- Fallback Chain: NotebookLM RAG → grep wiki → hardcoded defaults (WIKI-04 선언)
- 현재 상태 ("Phase 2 scaffold, 실 노드는 Phase 6")와 추가 절차 3단계

**Files 2-6: 5 MOC.md 스캐폴드** — 카테고리별 Map of Content
- 공통 구조: frontmatter(category/status=scaffold/tags/updated) + H1 title + Scope(1-line) + Planned Nodes(checkbox list) + Related(Tier 1 ref + cross-category + Root CLAUDE.md) + Source References(SUMMARY/REQUIREMENTS/Phase 4 consumer)
- Planned Nodes count (per plan, RESEARCH.md line 426-460 verbatim):
  - `algorithm/MOC.md` — 4 nodes (ranking_factors, viewer_retention_curve, cross_platform_penalties, shorts_shelf_selection)
  - `ypp/MOC.md` — 4 nodes (shorts_fund_history, rpm_korean_benchmark, eligibility_path, reused_content_defense)
  - `render/MOC.md` — 5 nodes (kling_api_spec, runway_fallback_policy, remotion_composition_schema, shotstack_color_grading, low_res_first_pipeline)
  - `kpi/MOC.md` — 4 nodes (three_second_hook_target, completion_rate_target, avg_watch_duration_target, kpi_log_template)
  - `continuity_bible/MOC.md` — 5 nodes (color_palette, camera_lens_spec, visual_style_prefix, duo_persona_bible, thumbnail_signature)
- 총 22 placeholder nodes — Phase 6 실 작성 대상

### Task 2: Tier 3 .preserved/harvested/ Scaffold (1 file + 1 directory)

**Directory creation:**
```bash
mkdir -p .preserved/harvested
```
`.preserved/harvested/` 빈 디렉토리 생성 (`.preserved/` 자체는 세션 #10 Phase 1 scaffold에서 이미 생성된 상태였음).

**File 7: `.preserved/harvested/.gitkeep`** — Tier 3 empty directory marker
- Content: `# Phase 3 populates this directory with 4 raw harvest subdirs + chmod -w` (1-line comment)
- 의도: git이 빈 디렉토리를 추적하도록 placeholder 확보. Phase 3 HARVEST-01~05이 4 raw subdirs(theme_bible_raw, remotion_src_raw, hc_checks_raw, api_wrappers_raw) 생성 + HARVEST-06 `chmod -w` 적용.

## Success Criteria Verified

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | 5 Tier 2 category directories exist | `for d in algorithm ypp render kpi continuity_bible; do test -d wiki/$d; done` → all exit 0 |
| 2 | Each category has MOC.md scaffold | `grep -l "Map of Content" wiki/*/MOC.md \| wc -l` → 5 |
| 3 | Tier 2 README.md exists with NotebookLM 2-notebook plan | `grep -c "노트북 A: 일반"` → 1, `grep -c "노트북 B: 채널바이블"` → 1, `grep -c "Tier 2 Wiki"` → 1 |
| 4 | Tier 3 `.preserved/harvested/` exists with .gitkeep | `test -d .preserved/harvested && test -f .preserved/harvested/.gitkeep` → exit 0 |
| 5 | Files staged for Plan 02-06 consolidated commit | 7 untracked files ready in `git status` |
| 6 | Each MOC has `status: scaffold` frontmatter | `grep -l "status: scaffold" wiki/*/MOC.md \| wc -l` → 5 |
| 7 | Each MOC has `## Planned Nodes` section | `grep -l "## Planned Nodes" wiki/*/MOC.md \| wc -l` → 5 |
| 8 | render/continuity_bible MOC = 5 nodes each; algorithm/ypp/kpi = 4 each | `grep -c "^- \[ \]"` per category: algorithm=4, ypp=4, kpi=4, render=5, continuity_bible=5 |

## Deviations from Plan

None — plan executed exactly as written. Both tasks' acceptance criteria verified on first pass. No Rule 1/2/3 auto-fixes triggered.

## Commit Strategy (Non-Standard)

**Per-task atomic commit was deferred** per explicit plan directive. The plan's success criteria #5 states "Files not yet committed — consolidated commit in Plan 06" and each task's `<done>` block reiterates this. Rationale: Plan 02-06 batches all Phase 2 studio changes (this plan's 7 files + Plan 02-04 CLAUDE.md edits + Plan 02-05 HARVEST_SCOPE.md) into a single commit for atomic Phase 2 completion in the studio repo.

**What IS committed in this plan's meta-commit:** `.planning/phases/02-domain-definition/02-03-SUMMARY.md` + `.planning/STATE.md` + `.planning/ROADMAP.md` + `.planning/REQUIREMENTS.md` (SUMMARY/STATE/ROADMAP updates per executor protocol's final_commit).

**What remains uncommitted after this plan:** 7 wiki/.preserved content files (to be picked up by Plan 02-06 consolidated commit).

## Files Created

- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/README.md` (Tier 2 home, ~40 lines)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/algorithm/MOC.md` (4 Planned Nodes)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/ypp/MOC.md` (4 Planned Nodes)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/render/MOC.md` (5 Planned Nodes)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/kpi/MOC.md` (4 Planned Nodes)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/continuity_bible/MOC.md` (5 Planned Nodes)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.preserved/harvested/.gitkeep` (1-line comment)

## Directories Created

- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/`
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/algorithm/`
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/ypp/`
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/render/`
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/kpi/`
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/continuity_bible/`
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.preserved/harvested/` (`.preserved/` pre-existed from Phase 1 scaffold)

## Commits

| Repo | Hash | Message | Files |
|------|------|---------|-------|
| studios/shorts | `c7292eb` | `docs(02-03): complete Tier 2 wiki scaffold + Tier 3 empty dir plan` | SUMMARY + STATE + ROADMAP (meta only) |
| studios/shorts | (Plan 02-06 future) | Consolidated studio Phase 2 commit | wiki/ + .preserved/ content (7 files) |

## Unblocks

- **Plan 02-04**: `CLAUDE.md` 5 TODO 치환 (독립, 본 plan과 병렬 가능했음)
- **Plan 02-05**: `HARVEST_SCOPE.md` 작성 (독립, 본 plan과 병렬 가능했음)
- **Plan 02-06**: Consolidated studio Phase 2 commit — 본 plan의 7 untracked 파일을 흡수
- **Phase 3 Harvest**: `.preserved/harvested/`에 4 raw subdirs 생성 가능 (HARVEST-01~05)
- **Phase 4 Agent Design**: 에이전트 prompts가 `@wiki/shorts/<category>/MOC.md` 참조 path-not-found 없이 작동
- **Phase 6 NotebookLM**: 22 Planned Node placeholder를 실 노드로 승격, NotebookLM 2-노트북 세팅 대상 확보

## Self-Check: PASSED

**Files verified exist (8/8):**
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/README.md`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/algorithm/MOC.md`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/ypp/MOC.md`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/render/MOC.md`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/kpi/MOC.md`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/continuity_bible/MOC.md`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/.preserved/harvested/.gitkeep`
- FOUND: `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/02-domain-definition/02-03-SUMMARY.md`

**Directories verified exist (7/7):**
- FOUND dir: `wiki/`
- FOUND dir: `wiki/algorithm/`
- FOUND dir: `wiki/ypp/`
- FOUND dir: `wiki/render/`
- FOUND dir: `wiki/kpi/`
- FOUND dir: `wiki/continuity_bible/`
- FOUND dir: `.preserved/harvested/`

**Acceptance criteria summary (all 8 checks):**
- 5 directories exist, 5 MOC.md files exist → all pass
- `wiki/README.md` exists with `Tier 2 Wiki` (1), `노트북 A: 일반` (1), `노트북 B: 채널바이블` (1) → all pass
- `grep -l "Map of Content" wiki/*/MOC.md \| wc -l` → 5
- `grep -l "status: scaffold" wiki/*/MOC.md \| wc -l` → 5
- `grep -l "## Planned Nodes" wiki/*/MOC.md \| wc -l` → 5
- Planned Node counts: algorithm=4, ypp=4, kpi=4, render=5, continuity_bible=5 → all match plan spec
- `.preserved/harvested/.gitkeep` exists, only 1 file in directory → pass
