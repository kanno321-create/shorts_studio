---
phase: 12
slug: agent-standardization-skill-routing-failures-protocol
status: wave_0_complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-21
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> **Body populated by Plan 01 (Wave 0) from 12-RESEARCH.md §Validation Architecture.**

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (기존 `tests/` infrastructure, Phase 4 이후 안정) |
| **Config file** | `pyproject.toml` (inherited from parent naberal_harness) + `tests/phase12/conftest.py` (Wave 0 신규) |
| **Quick run command** | `py -3.11 -m pytest tests/phase12/ -q` |
| **Full suite command** | `py -3.11 -m pytest tests/ -q` |
| **Phase gate command** | `py -3.11 -m pytest tests/phase04/ tests/phase10/test_skill_patch_counter.py tests/phase11/ tests/phase12/ -q` + `py -3.11 scripts/validate/verify_agent_md_schema.py --all` + `py -3.11 scripts/validate/verify_agent_skill_matrix.py` |
| **Estimated runtime** | ~90 seconds (phase gate) |

---

## Sampling Rate

- **After every task commit:** Run quick-scope pytest (해당 task 가 건드린 파일만 대상, `-k` 필터, < 5 초)
- **After every plan wave:** Run `py -3.11 -m pytest tests/phase12/ -q` (phase12 전체, ~30~60 초)
- **Before `/gsd:verify-work`:** Phase gate command (280 baseline + phase12 신규 ≈ 315 tests, ~90 초) — 전수 GREEN
- **Max feedback latency:** 5 초 (per-task), 60 초 (per-wave)

---

## Per-Task Verification Map

*Populated by Plan 01 (Wave 0) based on RESEARCH.md §Validation Architecture — Phase Requirements → Test Map (15 test cases + 4 wave-gate summary rows = 19 rows).*

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-W0-01 | 01 | 0 | AGENT-STD-01 | unit | `pytest tests/phase12/test_agent_md_schema.py::test_all_30_agents_have_5_blocks -x` | ✅ | ⬜ pending |
| 12-01-W0-02 | 01 | 0 | AGENT-STD-01 (neg) | unit | `pytest tests/phase12/test_agent_md_schema.py::test_excluded_agents_not_scanned -x` | ✅ | ⬜ pending |
| 12-01-W0-03 | 01 | 0 | AGENT-STD-01 | integration | `py -3.11 scripts/validate/verify_agent_md_schema.py .claude/agents/producers/trend-collector/AGENT.md` | ✅ | ✅ green (Plan 01 Task 4, commit 0ebb5e9) |
| 12-02-01 | 02 | 1 | AGENT-STD-01 | batch | `pytest tests/phase12/test_agent_md_schema.py::test_all_30_agents_have_5_blocks -x` (after 14 producer migration) | ✅ | ⬜ pending |
| 12-03-01 | 03 | 2 | AGENT-STD-01 | batch | `pytest tests/phase12/test_agent_md_schema.py::test_all_30_agents_have_5_blocks -x` (after 17 inspector migration) | ✅ | ⬜ pending |
| 12-04-01 | 04 | 1 | SKILL-ROUTE-01 | unit | `pytest tests/phase12/test_skill_matrix_format.py::test_matrix_has_30_rows -x` | ✅ | ⬜ pending |
| 12-04-02 | 04 | 1 | SKILL-ROUTE-01 | unit | `pytest tests/phase12/test_skill_matrix_format.py::test_matrix_cell_values_legal -x` | ✅ | ⬜ pending |
| 12-04-03 | 04 | 1 | SKILL-ROUTE-01 (recip) | integration | `py -3.11 scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` | ✅ | ⬜ pending |
| 12-05-01 | 05 | 1 | FAIL-PROTO-01 | unit | `pytest tests/phase12/test_failures_rotation.py::test_hook_denies_over_500_lines -x` | ✅ | ⬜ pending |
| 12-05-02 | 05 | 1 | FAIL-PROTO-01 | unit | `pytest tests/phase12/test_failures_rotation.py::test_rotate_idempotent -x` | ✅ | ⬜ pending |
| 12-05-03 | 05 | 1 | FAIL-PROTO-01 | unit | `pytest tests/phase12/test_failures_rotation.py::test_imported_file_sha256_unchanged -x` | ✅ | ⬜ pending |
| 12-05-04 | 05 | 1 | FAIL-PROTO-01 | unit | `pytest tests/phase12/test_failures_rotation.py::test_archive_month_tag -x` | ✅ | ⬜ pending |
| 12-06-01 | 06 | 3 | AGENT-STD-02 | unit | `pytest tests/phase12/test_mandatory_reads_prose.py::test_sampling_forbidden_literal -x` | ✅ | ⬜ pending |
| 12-06-02 | 06 | 3 | AGENT-STD-02 | unit | `pytest tests/phase12/test_mandatory_reads_prose.py::test_three_mandatory_items_present -x` | ✅ | ⬜ pending |
| 12-07-01 | 07 | 1 | AGENT-STD-03 | unit | `pytest tests/phase12/test_supervisor_compress.py::test_compression_ratio_over_40pct -x` | ✅ | ⬜ pending |
| 12-07-02 | 07 | 1 | AGENT-STD-03 | unit | `pytest tests/phase12/test_supervisor_compress.py::test_critical_decisions_preserved -x` | ✅ | ⬜ pending |
| 12-07-03 | 07 | 1 | AGENT-STD-03 | integration | `pytest tests/phase12/test_supervisor_compress.py::test_phase11_smoke_replay_under_cli_limit -x` | ✅ | ⬜ pending |
| 12-02-f-d2 | 02 | 1 | FAIL-PROTO-02 | unit | `pytest tests/phase12/test_f_d2_exception_batch.py::test_batch_commit_single_entry -x` | ✅ | ⬜ pending |
| 12-02-idemp | 02 | 1 | FAIL-PROTO-02 | unit | `pytest tests/phase12/test_f_d2_exception_batch.py::test_batch_idempotent_replay -x` | ✅ | ⬜ pending |

---

## Wave 0 Requirements

Inherits from RESEARCH.md §Validation Architecture — Wave 0 Gaps block:

- [x] `tests/phase12/conftest.py` — 공통 fixture (tmp_failures_file / MockClaudeCLI / synthetic_producer_output_small)
- [x] `tests/phase12/__init__.py` — Phase 4~11 컨벤션 준수
- [x] `tests/phase12/test_agent_md_schema.py` — 30 file × 5 block regex stub (AGENT-STD-01/02)
- [x] `tests/phase12/test_mandatory_reads_prose.py` — 한국어 문구 literal + keyword 검증 stub (AGENT-STD-02)
- [x] `tests/phase12/test_supervisor_compress.py` — Mock CLI + compression ratio + severity ordering stub (AGENT-STD-03)
- [x] `tests/phase12/test_skill_matrix_format.py` — markdown table 파싱 + cell value validation stub (SKILL-ROUTE-01)
- [x] `tests/phase12/test_failures_rotation.py` — Hook deny + rotation idempotency + immutable sha256 stub (FAIL-PROTO-01)
- [x] `tests/phase12/test_f_d2_exception_batch.py` — batch commit replay + idempotency stub (FAIL-PROTO-02)
- [x] `tests/phase12/fixtures/.gitkeep` — 합성 fixture 부모 dir (Plan 07 Task 1 이 producer_output_gate2_oversized.json 생성)
- [x] `tests/phase12/mocks/mock_claude_cli.py` — MockClaudeCLI defensive *args/**kwargs 패턴
- [x] Framework install: **불필요** — pytest 기존 설치, 신규 종속성 0
- [x] `.planning/phases/12-.../templates/producer.md.template` — 5-block schema baseline (Task 1)
- [x] `.planning/phases/12-.../templates/inspector.md.template` — 5-block schema baseline (Task 1)
- [x] `scripts/validate/verify_agent_md_schema.py` — AGENT-STD-01 CI 엔트리포인트 (Task 3)
- [x] `.claude/agents/producers/trend-collector/AGENT.md` — v1.1 → v1.2 prototype (Task 4)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Phase 11 SC#1/SC#2 재도전 (live smoke 완주) | (Phase 13 handoff) | Claude CLI 실 API 과금 + 네트워크 + YouTube 계정 필요 | Phase 12 완결 후 `/gsd:plan-phase 13` 착수 시 별도 plan |

*Phase 12 내부 behaviors 는 모두 자동 검증 가능 (Mock CLI 경유).*

---

## Validation Sign-Off

- [x] All 7 plans have `<automated>` verify per-task OR Wave 0 dependency reference
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (11 file + 1 fixture + 1 mock + 2 templates + 1 verifier CLI + 1 v1.2 prototype)
- [x] No watch-mode flags in test commands
- [x] Feedback latency < 90s (phase gate)
- [x] `nyquist_compliant: true` set in frontmatter after Wave 0 merge
- [x] `wave_0_complete: true` set after Plan 01 GREEN

**Approval:** GREEN (Plan 01 Wave 0 완결 2026-04-21)

---

*Skeleton generated 2026-04-21 by /gsd:plan-phase 12 per workflow step 5.5. Detailed test map (15 cases + 4 summary rows) populated 2026-04-21 by Plan 01 Task 5. This file is the **contract** consumed by gsd-executor and gsd-verifier.*
