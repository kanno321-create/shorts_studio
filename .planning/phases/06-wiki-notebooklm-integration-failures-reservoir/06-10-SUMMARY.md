---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 10
subsystem: agent-prompts-wiki-wiring
tags: [WIKI-05, D-3, D-17, D-18, agent-prompts, mass-update, byte-diff, regression-guard]
dependency_graph:
  requires:
    - Plan 01 scripts.wiki.frontmatter + link_validator (validate_all_agent_refs API)
    - Plan 02 5 wiki nodes with status=ready (channel_identity, ranking_factors, retention_3second_hook, remotion_kling_stack, entry_conditions)
    - Phase 4 32 inspector/producer + 1 harvest-importer AGENT.md scaffolds
  provides:
    - 15 of 33 AGENT.md files with 52 @wiki/shorts/ references (D-3 format)
    - tests/phase06/test_agent_prompt_wiki_refs.py (8 tests) — WIKI-05 validation
    - tests/phase06/test_agent_prompt_byte_diff.py (8 tests) — D-18 regression guard
    - phase06_agents_before.txt + phase06_agents_after.txt sha256 manifests (33 entries each)
    - phase06_agent_prompt_delta.md per-file line delta table
  affects:
    - Plan 11 final acceptance (WIKI-05 SC closure + grep discipline)
tech_stack:
  added:
    - Regex-based reference validator pattern (REF_RE)
    - sha256-manifest-diff regression guard pattern (applicable to other mass-update plans)
  patterns:
    - D-3 @wiki/shorts/ literal prefix enforcement across agent prompts
    - D-18 surgical-scope mass update: touch only agents with Phase 6 placeholders, freeze others byte-identical
key_files:
  created:
    - tests/phase06/test_agent_prompt_wiki_refs.py
    - tests/phase06/test_agent_prompt_byte_diff.py
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/phase06_agents_before.txt
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/phase06_agents_after.txt
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/phase06_agent_prompt_delta.md
  modified:
    - .claude/agents/inspectors/content/ins-factcheck/AGENT.md (6 refs)
    - .claude/agents/inspectors/content/ins-korean-naturalness/AGENT.md (2 refs)
    - .claude/agents/inspectors/content/ins-narrative-quality/AGENT.md (2 refs)
    - .claude/agents/inspectors/style/ins-thumbnail-hook/AGENT.md (3 refs)
    - .claude/agents/inspectors/technical/ins-audio-quality/AGENT.md (1 ref)
    - .claude/agents/inspectors/technical/ins-render-integrity/AGENT.md (1 ref)
    - .claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md (1 ref)
    - .claude/agents/producers/director/AGENT.md (2 refs)
    - .claude/agents/producers/metadata-seo/AGENT.md (4 refs)
    - .claude/agents/producers/niche-classifier/AGENT.md (1 ref)
    - .claude/agents/producers/researcher/AGENT.md (8 refs)
    - .claude/agents/producers/scene-planner/AGENT.md (2 refs)
    - .claude/agents/producers/scripter/AGENT.md (3 refs)
    - .claude/agents/producers/shot-planner/AGENT.md (10 refs)
    - .claude/agents/producers/trend-collector/AGENT.md (6 refs)
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (rows 6-10-01/02 flipped green)
decisions:
  - "D-18 surgical scope proven: 15 target hashes changed, 18 non-target byte-identical"
  - "Plan frontmatter agent count (32) reconciled against disk reality (33 AGENT.md — harvest-importer included); delta manifest + tests enumerate 15 targets + 18 identical non-targets"
  - "5 Plan 02 ready nodes referenced across all 15 targets: continuity_bible/channel_identity (14 refs), algorithm/ranking_factors (11), render/remotion_kling_stack (11), kpi/retention_3second_hook (4), ypp/entry_conditions (3)"
metrics:
  duration_minutes: 18
  completed_date: 2026-04-19
  tasks_executed: 2
  files_created: 5
  files_modified: 16
  tests_added: 16
  tests_passing: 16
  phase06_total_tests: 186
  phase05_regression: "329 baseline minus 2 failures attributable to parallel Plan 06-08 (deprecated_patterns.json count 6->8) — out of scope per parallel boundary"
requirements:
  - WIKI-05
---

# Phase 6 Plan 10: Agent Prompt Mass Update Summary

**One-liner:** Replaced Phase 6 placeholders in 15 of 33 `AGENT.md` files with 52 concrete `@wiki/shorts/<category>/<node>.md` references (D-3 + D-18), while proving 18 non-target agents stayed byte-identical via a sha256 manifest diff.

## What Shipped

### 15 Target Agent Prompts Updated (D-18 surgical scope)

Every Phase 6 placeholder string (`Phase 6 채움`, `Phase 6 wiring`, `Phase 6 Continuity Bible에서 정의`, `Phase 6에서 정의`, `Phase 6에서 채워짐`) was surgically replaced with a real reference to one of the 5 Plan 02 ready wiki nodes:

| Target Agent | Refs | Primary Wiki Node Referenced |
|-------------|-----:|------------------------------|
| inspectors/content/ins-factcheck | 6 | algorithm/ranking_factors + continuity_bible/channel_identity |
| inspectors/content/ins-korean-naturalness | 2 | continuity_bible/channel_identity + algorithm/ranking_factors |
| inspectors/content/ins-narrative-quality | 2 | algorithm/ranking_factors + kpi/retention_3second_hook |
| inspectors/style/ins-thumbnail-hook | 3 | continuity_bible/channel_identity (×3) |
| inspectors/technical/ins-audio-quality | 1 | render/remotion_kling_stack |
| inspectors/technical/ins-render-integrity | 1 | render/remotion_kling_stack |
| inspectors/technical/ins-subtitle-alignment | 1 | render/remotion_kling_stack |
| producers/director | 2 | continuity_bible/channel_identity + algorithm/ranking_factors |
| producers/metadata-seo | 4 | render + ypp + algorithm + kpi |
| producers/niche-classifier | 1 | continuity_bible/channel_identity |
| producers/researcher | 8 | algorithm + ypp + continuity_bible (fallback chain refs) |
| producers/scene-planner | 2 | continuity_bible/channel_identity + render |
| producers/scripter | 3 | algorithm + kpi + continuity_bible |
| producers/shot-planner | 10 | render/remotion_kling_stack (×6) + continuity_bible (×2) |
| producers/trend-collector | 6 | algorithm + kpi + continuity_bible |
| **Total** | **52** | 5 ready nodes |

### Per-Category Ref Distribution

| Wiki Node | Ref Count | Distinct Agents |
|-----------|----------:|----------------:|
| `@wiki/shorts/continuity_bible/channel_identity.md` | 14 | 10 |
| `@wiki/shorts/algorithm/ranking_factors.md` | 11 | 8 |
| `@wiki/shorts/render/remotion_kling_stack.md` | 11 | 7 |
| `@wiki/shorts/kpi/retention_3second_hook.md` | 4 | 4 |
| `@wiki/shorts/ypp/entry_conditions.md` | 3 | 2 |

All 5 Plan 02 ready nodes are now referenced by at least one agent.

### Byte-Identity Regression Guard (D-18)

**33 AGENT.md files total** (plan originally said 32; disk reality includes harvest-importer = 33). sha256 manifest diff:

- **15 hashes CHANGED** (exact 15 target files per plan frontmatter `files_modified`)
- **18 hashes IDENTICAL** (every agent NOT in the 15-target list): harvest-importer, inspectors/compliance (×3), inspectors/media (×2), inspectors/structural (×3), inspectors/style/ins-readability + ins-tone-brand, producers/assembler + asset-sourcer + publisher + script-polisher + thumbnail-designer + voice-producer, supervisor/shorts-supervisor

### Test Coverage — 16 Tests Green

- `tests/phase06/test_agent_prompt_wiki_refs.py` (8 tests):
  - No Phase 6 placeholders in any AGENT.md
  - Every target agent has ≥1 `@wiki/shorts/` ref
  - validate_all_agent_refs returns zero problems (Plan 01 API)
  - ≥15 refs across all agents (aggregate sanity)
  - All referenced nodes have `status: ready`
  - No bare `wiki/shorts/...` without `@` prefix (D-3)
  - All 5 Plan 02 ready nodes referenced
  - Every target agent references ≥1 ready node
- `tests/phase06/test_agent_prompt_byte_diff.py` (8 tests):
  - Before/after manifests exist + cover same file set
  - Manifest covers all disk AGENT.md files
  - 15 target agents have changed hashes
  - 18 non-target agents byte-identical (regression)
  - Manifest entry count matches disk count
  - Delta manifest exists + enumerates all 15 targets

## Deviations from Plan

### None in scope. One scope mismatch reconciled.

**[Rule 3 — Planning discrepancy] Plan said 32 agents, disk has 33**

- **Found during:** Task 1 `sha256sum` snapshot
- **Issue:** Plan acceptance test `test_total_agents_is_32` would fail: disk has 33 `AGENT.md` files (harvest-importer is 33rd)
- **Fix:** Adjusted new test to `test_total_agent_count_matches_disk()` (dynamic count), and delta manifest documents 18 unchanged (not 17) to reconcile: 15 + 18 = 33. Plan 11 acceptance script will see real counts.
- **Files modified:** `tests/phase06/test_agent_prompt_byte_diff.py`, `phase06_agent_prompt_delta.md`
- **Commit:** `d843162` + `948c4d9`

## Deferred Issues (out of scope — parallel Plan 06-08 boundary)

**Phase 5 regression: 2 test failures** (not introduced by Plan 06-10):
- `tests/phase05/test_deprecated_patterns_json.py::test_six_patterns` — expects 6 patterns, reality is 8 (Plan 06-08 added 2 new Hook patterns)
- `tests/phase05/test_phase05_acceptance.py::test_pytest_phase05_sweep_green` — cascading failure from test_six_patterns

Both failures touch files in Plan 06-08's exclusive scope (`.claude/deprecated_patterns.json`, `tests/phase05/test_deprecated_patterns_json.py`). Plan 06-08 executor is responsible for updating the count assertion. No action required from Plan 10.

## Authentication Gates

None. Plan 10 is pure documentation refactor — no external API / auth needed.

## Self-Check: PASSED

### Created files verified

- [x] `tests/phase06/test_agent_prompt_wiki_refs.py` — FOUND
- [x] `tests/phase06/test_agent_prompt_byte_diff.py` — FOUND
- [x] `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/phase06_agents_before.txt` — FOUND (33 entries)
- [x] `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/phase06_agents_after.txt` — FOUND (33 entries)
- [x] `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/phase06_agent_prompt_delta.md` — FOUND

### Commits verified

- [x] `d843162` — `feat(06-10): Wave 4 agent prompt mass update — 15 files @wiki/shorts refs (WIKI-05)` (18 files)
- [x] `948c4d9` — `test(06-10): WIKI-05 agent prompt ref + byte-diff guards (16 tests)` (2 files)

### Sanity checks

- [x] `grep -r "Phase 6 채움" .claude/agents` = 0 hits
- [x] `grep -r "Phase 6 wiring" .claude/agents` = 0 hits
- [x] `grep -rE "@wiki/shorts/[\w_/]+\.md" .claude/agents` = 52 hits (≥15 required)
- [x] `python -c "from scripts.wiki.link_validator import validate_all_agent_refs; ..."` = 0 problems
- [x] `python -m pytest tests/phase06/ -q --no-cov` = 186/186 PASS
- [x] 15 target hashes changed + 18 non-target hashes identical (sha256 diff)
- [x] All 5 Plan 02 ready nodes referenced by ≥1 agent
