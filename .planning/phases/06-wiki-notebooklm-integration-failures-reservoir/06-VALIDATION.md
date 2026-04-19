---
phase: 6
slug: wiki-notebooklm-integration-failures-reservoir
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
completed: 2026-04-19
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Generated from RESEARCH.md §Area 12 Validation Architecture (line 1195).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (Phase 5 baseline 승계) |
| **Config file** | `pytest.ini` (기존) — Phase 6 test dir `tests/phase06/` 추가 |
| **Quick run command** | `python -m pytest tests/phase06/ -q --no-cov` |
| **Full suite command** | `python -m pytest tests/ -q --no-cov` |
| **Estimated runtime** | ~10s (Phase 5 329 tests ~5s + Phase 6 예상 40~60 tests ~5s) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase06/<affected_test>.py -q --no-cov`
- **After every plan wave:** Run `python -m pytest tests/phase06/ -q --no-cov`
- **Before `/gsd:verify-work`:** Full suite must be green (329 Phase 5 + Phase 6 전체 PASS)
- **Max feedback latency:** 10s

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 0 | WIKI-05 | unit | `pytest tests/phase06/test_wiki_frontmatter.py` | ✅ | ✅ green |
| 6-01-02 | 01 | 0 | WIKI-05 | unit | `pytest tests/phase06/test_wiki_reference_format.py` | ✅ | ✅ green |
| 6-02-01 | 02 | 1 | WIKI-01 | unit | `pytest tests/phase06/test_wiki_nodes_ready.py` | ✅ | ✅ green |
| 6-02-02 | 02 | 1 | WIKI-01 | integration | `pytest tests/phase06/test_moc_linkage.py` | ✅ | ✅ green |
| 6-02-03 | 02 | 1 | WIKI-02 | unit | `pytest tests/phase06/test_continuity_bible_node.py` | ✅ | ✅ green |
| 6-03-01 | 03 | 2 | WIKI-03 | unit | `pytest tests/phase06/test_notebooklm_wrapper.py` | ✅ | ✅ green |
| 6-03-02 | 03 | 2 | WIKI-03 | integration | `pytest tests/phase06/test_notebooklm_subprocess.py` | ✅ | ✅ green |
| 6-04-01 | 04 | 2 | WIKI-03 | unit | `pytest tests/phase06/test_library_json_channel_bible.py` | ✅ | ✅ green |
| 6-05-01 | 05 | 2 | WIKI-04 | unit | `pytest tests/phase06/test_fallback_chain.py` | ✅ | ✅ green |
| 6-05-02 | 05 | 2 | WIKI-04 | integration | `pytest tests/phase06/test_fallback_injection.py` | ✅ | ✅ green |
| 6-06-01 | 06 | 3 | WIKI-02 | unit | `pytest tests/phase06/test_continuity_prefix_schema.py` | ✅ | ✅ green |
| 6-06-02 | 06 | 3 | WIKI-02 | unit | `pytest tests/phase06/test_prefix_json_serialization.py` | ✅ | ✅ green |
| 6-07-01 | 07 | 3 | WIKI-02 | unit | `pytest tests/phase06/test_shotstack_prefix_injection.py` | ✅ | ✅ green |
| 6-07-02 | 07 | 3 | WIKI-02 | integration | `pytest tests/phase06/test_filter_order_preservation.py` | ✅ | ✅ green |
| 6-08-01 | 08 | 4 | FAIL-01 | unit | `pytest tests/phase06/test_failures_append_only.py` | ✅ | ✅ green |
| 6-08-02 | 08 | 4 | FAIL-01 | subprocess | `pytest tests/phase06/test_hook_failures_block.py` | ✅ | ✅ green |
| 6-08-03 | 08 | 4 | FAIL-03 | unit | `pytest tests/phase06/test_skill_history_backup.py` | ✅ | ✅ green |
| 6-09-01 | 09 | 4 | FAIL-02 | unit | `pytest tests/phase06/test_aggregate_patterns.py` | ✅ | ✅ green |
| 6-09-02 | 09 | 4 | FAIL-02 | integration | `pytest tests/phase06/test_aggregate_dry_run.py` | ✅ | ✅ green |
| 6-10-01 | 10 | 4 | WIKI-05 | unit | `pytest tests/phase06/test_agent_prompt_wiki_refs.py` | ✅ | ✅ green |
| 6-10-02 | 10 | 4 | WIKI-05 | integration | `pytest tests/phase06/test_agent_prompt_byte_diff.py` | ✅ | ✅ green |
| 6-11-01 | 11 | 5 | D-14 | unit | `pytest tests/phase06/test_imported_failures_sha256.py` | ✅ | ✅ green |
| 6-11-02 | 11 | 5 | ALL | E2E | `python scripts/validate/phase06_acceptance.py` | ✅ | ✅ green |
| 6-11-03 | 11 | 5 | ALL | regression | `pytest tests/phase05/ tests/phase04/ -q` | ✅ | ✅ green |

*Status legend: `pending` (not yet run) · `✅ green` (all tests passing) · `❌ red` (failing) · `⚠️ flaky` (intermittent)*

---

## Wave 0 Requirements

Wave 0은 Phase 6 실행의 최초 wave(Plan 01 — frontmatter + wiki lint baseline). 필요 인프라:

- [x] `tests/phase06/__init__.py` — package marker
- [x] `tests/phase06/conftest.py` — 공유 fixture (tmp wiki dir, mock notebooklm subprocess, mock pre_tool_use hook env)
- [x] `tests/phase06/fixtures/` — wiki 노드 sample frontmatter, library.json delta sample, FAILURES entry sample
- [x] `scripts/validate/phase06_acceptance.py` — SC 1-6 E2E wrapper (Phase 5 phase05_acceptance.py 패턴 승계)
- [x] `scripts/validate/verify_wiki_frontmatter.py` — WIKI-05 grep 검증 CLI

*Wave 0 완료: Plan 01 완료 시 `wave_0_complete: true` flipped 2026-04-19*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| NotebookLM 채널바이블 노트북 URL 획득 | WIKI-03 | 대표님이 Google NotebookLM 콘솔에서 직접 생성해야 함 | deferred-items.md에 TODO 기록 + placeholder `TBD-url-await-user`로 진행. 실 URL 확보 시 library.json 교체 |
| NotebookLM authentication refresh | WIKI-03 | browser_state 만료 시 대표님 1회 Google 로그인 재수행 필요 | 실 쿼리 실패 시 `playwright install` + `python scripts/notebooklm/refresh_auth.py` 가이드 제공 |
| Continuity 시각적 일관성 샘플 3개 연속 생성 | SC #4 | Phase 6은 mock 기반이라 실 렌더 없음 | Phase 7 E2E 통합 테스트에서 실 API 호출로 검증 이관 (Phase 6 VERIFICATION.md에 명시) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Completion Summary

**Phase 6:** Wiki + NotebookLM Integration + FAILURES Reservoir
**Status:** ✅ COMPLETE 2026-04-19
**Plans:** 11/11
**REQs:** 9/9 (WIKI-01~06 + FAIL-01~03)

### Success Criteria Results

| SC | Description | Status |
|----|-------------|--------|
| #1 | 5 categories ready + @wiki/shorts refs | ✅ PASS |
| #2 | NotebookLM 2-notebook setup | ✅ PASS |
| #3 | Fallback Chain graceful degradation | ✅ PASS |
| #4 | Continuity Prefix auto-inject at filter[0] | ✅ PASS |
| #5 | FAILURES append-only + SKILL_HISTORY backup | ✅ PASS |
| #6 | aggregate_patterns.py dry-run | ✅ PASS |

### Test Counts

- `tests/phase06/` total: 236 tests PASS (Plans 01-11 inclusive, including Plan 11's 19 new tests: 5 D-14 sha256 + 7 traceability + 7 acceptance wrapper)
- `tests/phase05/` regression: 329/329 PASS (deprecated_patterns baseline updated 6→8, production Hook behaviour unchanged)
- `scripts/validate/phase06_acceptance.py` exit 0 (all 6 SC PASS)

### D-14 Immutability Gate

- `_imported_from_shorts_naberal.md` sha256 `a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa` unchanged
- Line count 500 preserved
- File in `.claude/failures/` only; no wiki/ contamination

### Commit Hashes (Plan 06-11)

- `18bb414` test(06-11): D-14 imported FAILURES sha256 immutability gate
- `b64fbbe` test(06-11): update phase05 deprecated_patterns baseline 6→8 (Phase 6 evolution)
- `7373f4e` test(06-11): acceptance E2E wrapper + 9-REQ traceability matrix
- (plus this VALIDATION flip + final summary/state commits)

### Ready for

`/gsd:verify-work 6` then `/gsd:plan-phase 7`

---

*Created from template: $HOME/.claude/get-shit-done/templates/VALIDATION.md*
*Source: 06-RESEARCH.md §Area 12 Validation Architecture (line 1195)*
