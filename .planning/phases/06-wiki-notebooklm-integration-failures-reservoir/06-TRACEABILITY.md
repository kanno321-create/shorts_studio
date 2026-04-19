# Phase 6 REQ Traceability Matrix

**Generated:** 2026-04-19 (Plan 06-11 Wave 5 phase gate)
**Coverage:** 9/9 Phase 6 requirements mapped to at least one passing test.
**Source of truth:** `.planning/REQUIREMENTS.md` §WIKI + §FAIL + `tests/phase06/` actual file inventory.

Every REQ ID from REQUIREMENTS.md §WIKI + §FAIL MUST appear below with at least one passing test file and at least one acceptance SC. No orphans.

## Matrix

| REQ ID | Spec (short) | Primary Source File(s) | Primary Test File(s) | SC Acceptance |
|--------|--------------|-------------------------|----------------------|---------------|
| WIKI-01 | Tier 2 도메인 특화 노드 (알고리즘/YPP/렌더/KPI/Continuity) 5 ready 노드 + Obsidian 그래프 | wiki/algorithm/ranking_factors.md, wiki/ypp/entry_conditions.md, wiki/render/remotion_kling_stack.md, wiki/kpi/retention_3second_hook.md, wiki/continuity_bible/channel_identity.md, wiki/MOC.md | tests/phase06/test_wiki_frontmatter.py, tests/phase06/test_wiki_nodes_ready.py, tests/phase06/test_moc_linkage.py | SC #1 |
| WIKI-02 | Continuity Bible Prefix auto-inject at Shotstack filter[0] | scripts/orchestrator/api/models.py (ContinuityPrefix), scripts/orchestrator/api/shotstack.py (_load_continuity_preset + injection), wiki/continuity_bible/prefix.json, wiki/continuity_bible/channel_identity.md | tests/phase06/test_continuity_prefix_schema.py, tests/phase06/test_prefix_json_serialization.py, tests/phase06/test_shotstack_prefix_injection.py, tests/phase06/test_filter_order_preservation.py, tests/phase06/test_continuity_bible_node.py | SC #4 |
| WIKI-03 | NotebookLM 2-노트북 세팅 (일반 + 채널바이블) + subprocess wrapper | scripts/notebooklm/query.py, scripts/notebooklm/library.py | tests/phase06/test_notebooklm_wrapper.py, tests/phase06/test_notebooklm_subprocess.py, tests/phase06/test_library_json_channel_bible.py | SC #2 |
| WIKI-04 | NotebookLM Fallback Chain 3-tier (RAG -> grep -> hardcoded) | scripts/notebooklm/fallback.py | tests/phase06/test_fallback_chain.py, tests/phase06/test_fallback_injection.py | SC #3 |
| WIKI-05 | @wiki/shorts/ 참조 포맷 고정 + agent prompt mass update | scripts/wiki/link_validator.py, 15 edited .claude/agents/**/AGENT.md | tests/phase06/test_wiki_reference_format.py, tests/phase06/test_agent_prompt_wiki_refs.py, tests/phase06/test_agent_prompt_byte_diff.py | SC #1 (agent-visible refs) |
| WIKI-06 | SKILL.md ≤500줄 본문 감사 (measurement-only per D-15) | scripts/wiki/link_validator.py, scripts/validate/verify_wiki_frontmatter.py | tests/phase06/test_wiki_frontmatter.py (D-17 schema enforcement covers WIKI-06 validator scaffold) | Deferred to Phase 9 for actual SKILL splits |
| FAIL-01 | FAILURES.md append-only Hook (D-11) | .claude/hooks/pre_tool_use.py (check_failures_append_only), .claude/deprecated_patterns.json (+2 regex), .claude/failures/FAILURES.md, .claude/failures/FAILURES_INDEX.md | tests/phase06/test_failures_append_only.py, tests/phase06/test_hook_failures_block.py | SC #5 |
| FAIL-02 | 30-day aggregate dry-run CLI (D-13) | scripts/failures/aggregate_patterns.py | tests/phase06/test_aggregate_patterns.py, tests/phase06/test_aggregate_dry_run.py | SC #6 |
| FAIL-03 | SKILL_HISTORY backup on SKILL.md write (D-12) | .claude/hooks/pre_tool_use.py (backup_skill_before_write), .claude/SKILL_HISTORY/README.md | tests/phase06/test_skill_history_backup.py | SC #5 (adjacent) |

**Coverage check:** 9/9 REQs mapped, all 6 SC covered, no orphans.

## Success Criteria -> Primary Tests

| SC  | Focus | REQs | Representative Tests |
|-----|-------|------|----------------------|
| SC #1 | 5 categories ready + @wiki/shorts agent refs resolve | WIKI-01, WIKI-05 | test_wiki_nodes_ready.py, test_moc_linkage.py, test_agent_prompt_wiki_refs.py |
| SC #2 | NotebookLM 2-notebook setup (library.json) | WIKI-03 | test_library_json_channel_bible.py, test_notebooklm_subprocess.py |
| SC #3 | Fallback Chain graceful degradation (RAG -> grep -> hardcoded) | WIKI-04 | test_fallback_chain.py, test_fallback_injection.py |
| SC #4 | Continuity Prefix auto-inject at filter[0] | WIKI-02 | test_shotstack_prefix_injection.py, test_filter_order_preservation.py |
| SC #5 | FAILURES append-only + SKILL_HISTORY backup | FAIL-01, FAIL-03 | test_failures_append_only.py, test_hook_failures_block.py, test_skill_history_backup.py |
| SC #6 | aggregate_patterns dry-run emits candidate JSON | FAIL-02 | test_aggregate_patterns.py, test_aggregate_dry_run.py |

All 6 SC green in `scripts/validate/phase06_acceptance.py` as of 2026-04-19.

## D-14 Immutability Gate

Orthogonal to REQ coverage, D-14 `_imported_from_shorts_naberal.md` sha256 immutability is verified by `tests/phase06/test_imported_failures_sha256.py` — if this test fails, STOP Phase 6 / investigate commit trail:

- Expected full-file sha256: `a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa`
- Expected line count: 500
- Restore command: `git checkout HEAD -- .claude/failures/_imported_from_shorts_naberal.md`

## Enforcement Tests

Automation that guards this matrix from silent drift:

- `tests/phase06/test_traceability_matrix.py` — asserts every REQ in `PHASE6_REQS` has at least one test file whose stem matches a registered marker; fails if a new REQ is added without test coverage or a test file is renamed without updating the marker map.
- `tests/phase06/test_phase06_acceptance.py` — asserts `scripts/validate/phase06_acceptance.py` exits 0 with all 6 SC labels PASS; closes the SC loop.
- `tests/phase06/test_imported_failures_sha256.py` — D-14 full-file hash + 500-line contract.

## Plan -> REQ -> Commit Audit Trail

| Plan | Wave | Primary REQs Addressed | Key Commits |
|------|------|------------------------|-------------|
| 06-01 | W0 | WIKI-05 (validator scaffold), WIKI-06 (measurement scaffold) | 6690e12 |
| 06-02 | W1 | WIKI-01, WIKI-02 (node placement) | (see 06-02-SUMMARY.md) |
| 06-03 | W2 | WIKI-03 (NotebookLM wrapper) | (see 06-03-SUMMARY.md) |
| 06-04 | W2 | WIKI-03 (library.json channel-bible) | (see 06-04-SUMMARY.md) |
| 06-05 | W2 | WIKI-04 (Fallback Chain) | 25993bb |
| 06-06 | W3 | WIKI-02 (ContinuityPrefix data model) | f661fa7 |
| 06-07 | W3 | WIKI-02 (Shotstack filter[0] injection) | 20cdeed |
| 06-08 | W4 | FAIL-01, FAIL-03 (Hook + deprecated_patterns +2) | 88a3ae5 |
| 06-09 | W4 | FAIL-02 (aggregate_patterns dry-run) | 921886e |
| 06-10 | W4 | WIKI-05 (15 agent prompt mass update) | 948c4d9 |
| 06-11 | W5 | Phase gate (D-14 sha256 + acceptance E2E + matrix + VALIDATION flip) | 18bb414, b64fbbe, <this plan's hashes> |

Phase 6 status: shippable when all listed tests are green.

## Plan Summary

| Plan | Tasks | Artifacts | Gate |
|------|-------|-----------|------|
| 06-01 | 3 | scripts/wiki/ + tests/phase06/ scaffold + phase06_acceptance.py | Wave 0 |
| 06-02 | 3 | 5 wiki ready nodes + 5 MOC updates + 3 test files | Wave 1 |
| 06-03 | 2 | scripts/notebooklm/query.py + 2 test files | Wave 2 |
| 06-04 | 2 | scripts/notebooklm/library.py + 1 test file + deferred-items.md | Wave 2 |
| 06-05 | 2 | scripts/notebooklm/fallback.py + 2 test files | Wave 2 |
| 06-06 | 2 | ContinuityPrefix append to models.py + prefix.json + 2 test files | Wave 3 |
| 06-07 | 2 | shotstack.py extension + 2 test files | Wave 3 |
| 06-08 | 2 | Hook extension + 2 deprecated_patterns entries + seeds + 3 test files | Wave 4 |
| 06-09 | 2 | aggregate_patterns.py + 2 test files | Wave 4 |
| 06-10 | 2 | 15 agent edits + sha256 manifests + 2 test files | Wave 4 |
| 06-11 | 3 | 3 test files + 06-TRACEABILITY.md + 06-VALIDATION.md flip | Wave 5 gate |

---

*Generated: 2026-04-19 (Plan 06-11 Wave 5 — Phase 6 final verification)*
