---
phase: 12
slug: agent-standardization-skill-routing-failures-protocol
status: draft
nyquist_compliant: false
wave_0_complete: false
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

*Populated by Plan 01 (Wave 0) based on RESEARCH.md §Validation Architecture — Phase Requirements → Test Map (15 test cases).*

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-W0 | 01 | 0 | (infra) | scaffold | `ls tests/phase12/conftest.py` | ❌ W0 | ⬜ pending |
| 12-01-01 | 01 | 0 | AGENT-STD-01 | unit | `pytest tests/phase12/test_agent_md_schema.py -x` | ❌ W0 | ⬜ pending |
| *(planner fills remaining rows during Wave 0 — 1 row per acceptance_criterion)* | | | | | | | |

---

## Wave 0 Requirements

Inherits from RESEARCH.md §Validation Architecture — Wave 0 Gaps block:

- [ ] `tests/phase12/conftest.py` — 공통 fixture (tmp_path FAILURES.md / MockClaudeCLI / synthetic producer_output)
- [ ] `tests/phase12/__init__.py` — Phase 4~11 컨벤션 준수
- [ ] `tests/phase12/test_agent_md_schema.py` — 30 file × 5 block regex (AGENT-STD-01/02)
- [ ] `tests/phase12/test_mandatory_reads_prose.py` — 한국어 문구 literal + keyword 검증 (AGENT-STD-02)
- [ ] `tests/phase12/test_supervisor_compress.py` — Mock CLI + compression ratio + severity ordering (AGENT-STD-03)
- [ ] `tests/phase12/test_skill_matrix_format.py` — markdown table 파싱 + cell value validation (SKILL-ROUTE-01)
- [ ] `tests/phase12/test_failures_rotation.py` — Hook deny + rotation idempotency + immutable sha256 (FAIL-PROTO-01)
- [ ] `tests/phase12/test_f_d2_exception_batch.py` — batch commit replay + idempotency (FAIL-PROTO-02)
- [ ] `tests/phase12/fixtures/producer_output_gate2_oversized.json` — 합성 fixture (8~15KB, AGENT-STD-03 replay)
- [ ] `tests/phase12/mocks/mock_claude_cli.py` — Phase 7 MockClaudeCLI 패턴 재활용 또는 신규
- [ ] Framework install: **불필요** — pytest 기존 설치, 신규 종속성 0

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Phase 11 SC#1/SC#2 재도전 (live smoke 완주) | (Phase 13 handoff) | Claude CLI 실 API 과금 + 네트워크 + YouTube 계정 필요 | Phase 12 완결 후 `/gsd:plan-phase 13` 착수 시 별도 plan |

*Phase 12 내부 behaviors 는 모두 자동 검증 가능 (Mock CLI 경유).*

---

## Validation Sign-Off

- [ ] All 7 plans have `<automated>` verify per-task OR Wave 0 dependency reference
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (10 file + 1 fixture + 1 mock)
- [ ] No watch-mode flags in test commands
- [ ] Feedback latency < 90s (phase gate)
- [ ] `nyquist_compliant: true` set in frontmatter after Wave 0 merge
- [ ] `wave_0_complete: true` set after Plan 01 GREEN

**Approval:** pending (awaiting Plan 01 Wave 0 completion)

---

*Skeleton generated 2026-04-21 by /gsd:plan-phase 12 per workflow step 5.5. Detailed test map (15 cases) lives in 12-RESEARCH.md §Validation Architecture — this file is the **contract** consumed by gsd-executor and gsd-verifier.*
