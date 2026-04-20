---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 06
subsystem: orchestrator-live-smoke + script-quality-eval
tags: [pipeline-01-validation, script-01, live-smoke, retry-with-nudge, complete-with-deferred]
status: complete_with_deferred
dependency-graph:
  requires:
    - "Plan 11-01 stdin-piped invoker (`c361ce4`)"
    - "Plan 11-02 zero-dep .env loader (`c52c118`)"
    - "Plan 11-03 adapter graceful-degrade + argparse optional (`81ff924`)"
    - "Plan 11-04 run_pipeline.cmd/.ps1 wrapper (`93eb804`)"
    - "Plan 11-05 skill_patch_counter idempotency (`c3f87d3`)"
  provides:
    - "scripts/smoke/phase11_full_run.py — full 0→13 GATE live harness (harness SKELETON complete, execution BLOCKED at GATE 2)"
    - "SCRIPT_QUALITY_DECISION.md — 6-axis eval template (verdict placeholder, awaits Phase 12 first successful smoke)"
    - "REQUIREMENTS.md D-19 amendment — SCRIPT-01 'B/C 선택 시 Phase 12 조건부 발행' locked"
    - "trend-collector AGENT.md v1.1 — JSON-only + mandatory_reads (directive-authorized F-D2-EXCEPTION-01)"
    - "invokers.py retry-with-nudge — max 3 attempts + JSON-nudge on JSONDecodeError (Option D defense-in-depth)"
    - "2 live smoke failure audits (reports/phase11_smoke_*.json) — $0.00 consumed, root causes isolated"
  affects:
    - "Phase 12 entry gate: SC#1 + SC#2 now Phase 12 deliverables"
    - "New REQ candidate AGENT-STD-03 (supervisor producer_output summary-only mode)"
tech-stack:
  added: []
  patterns:
    - "Full-pipeline live smoke harness with cost cap + retry cap + state dir enforcement"
    - "Retry-with-nudge at invoker layer: JSONDecodeError → append nudge prompt → retry up to 3 attempts"
    - "Directive-authorized agent patch (F-D2-EXCEPTION-01) — D-2 저수지 예외, 대표님 직접 승인"
key-files:
  created:
    - "scripts/smoke/phase11_full_run.py (19480 bytes, 0→13 GATE live harness)"
    - ".planning/phases/11-.../SCRIPT_QUALITY_DECISION.md (6-axis eval template)"
    - "tests/phase11/test_invoker_retry.py (5 retry-with-nudge tests)"
    - "reports/phase11_smoke_phase11_20260421_031945.json (1차 smoke audit)"
    - "reports/phase11_smoke_20260421_034724.json (2차 smoke audit)"
  modified:
    - ".planning/REQUIREMENTS.md (SCRIPT-01 D-19 amendment + Phase 12 REQ table + AGENT-STD-03 candidate)"
    - ".claude/agents/producers/trend-collector/AGENT.md (v1.0 → v1.1 JSON-only + mandatory_reads)"
    - "scripts/orchestrator/invokers.py (retry-with-nudge added to ClaudeAgentProducerInvoker)"
    - ".claude/failures/FAILURES.md (F-D2-EXCEPTION-01 entry)"
key-decisions:
  - "Partial completion classification — Tasks 1-3a ✅ / Task 3b 2 attempts both aborted pre-billing / Task 4 not entered"
  - "Option D retry-with-nudge adopted (대표님 session #29 'a' approval) — invoker.py wrapper, GATE 1 2nd nudge 후 JSON 복구 실증"
  - "Supervisor prompt-too-long identified as out-of-Phase-11 scope — Phase 12 AGENT-STD-03 handoff"
  - "SCRIPT_QUALITY_DECISION.md frontmatter verdict: pending → deferred to post-Phase-12 fill"
  - "$5.00 cap preserved for Phase 12 (both attempts aborted pre-billing)"
metrics:
  tasks_attempted: 4
  tasks_completed: 3  # Task 1 template, Task 2 D-19 amendment, Task 3a harness, Task 3b deferred, Task 4 deferred
  tasks_deferred: 2  # Task 3b full live smoke, Task 4 VERIFICATION wrap-up done by gsd-verifier
  live_smoke_attempts: 2
  live_smoke_cost_usd: 0.00
  commits: 8  # c5a0c81 5830862 9e0c4c9 6b1dba4 10ba7b6 acb2ba3 96001d3 7eb569b
  completed_date: 2026-04-21
  duration_sec: null  # partial — not measured
requirements-attempted: [PIPELINE-01 validation, SCRIPT-01 verdict]
requirements-completed: []  # both deferred to Phase 12 execution
requirements-deferred: [PIPELINE-01 SC#1 full run, SCRIPT-01 verdict lock]
---

# Phase 11 Plan 06: Full Smoke + Script Decision Summary (Partial — Complete with Deferred)

**One-liner**: Full 0→13 live smoke harness + SCRIPT-01 evaluation template shipped; 2 live smoke attempts both aborted pre-billing ($0.00 consumed); GATE 1 TREND JSON issue resolved via Option D retry-with-nudge (invoker.py, 5 tests GREEN); GATE 2 supervisor prompt-too-long isolated as Phase 12 handoff (new REQ candidate AGENT-STD-03).

## Objective Status

**Task-level accounting**:

| Task | Description | Status | Evidence |
|------|-------------|:------:|----------|
| Task 1 | SCRIPT_QUALITY_DECISION.md 6-axis template | ✅ | commit `5830862` |
| Task 2 | REQUIREMENTS.md D-19 amendment (SCRIPT-01) | ✅ | commit `c5a0c81` |
| Task 3a | `scripts/smoke/phase11_full_run.py` 0→13 harness | ✅ | commit `9e0c4c9` (19480 bytes) |
| Task 3b | Full live smoke execution 0→13 | ❌ DEFERRED | 2 attempts failed pre-billing — reports/phase11_smoke_*.json |
| Task 4 | SCRIPT_QUALITY_DECISION.md 대표님 fill + verdict | ❌ DEFERRED | awaits first successful smoke (Phase 12) |

**Task 3b failure chain** (2 attempts, both $0.00 due to pre-billing abort):

**Attempt 1** (`phase11_20260421_031945.json`, 149.74s):
- GATE 1 TREND trend-collector → returned Korean conversational text instead of JSON
- `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- `RuntimeError: Producer 'trend-collector' JSON 미준수 (대표님)`
- Root cause: trend-collector AGENT.md v1.0 lacked strict output format enforcement
- **Resolution applied** (session #29 directive):
  1. `acb2ba3`: trend-collector AGENT.md v1.0 → v1.1 with `<mandatory_reads>` + `<output_format>` blocks + 5 forbidden-pattern examples
  2. `96001d3`: invokers.py gained retry-with-nudge (max 3 attempts with JSON-nudge prompt on JSONDecodeError) — **Option D defense-in-depth**
  3. F-D2-EXCEPTION-01 logged in `.claude/failures/FAILURES.md` as directive-authorized exception (D-2 저수지 기본 원칙은 SKILL patch 금지이나, 본 patch 는 출력 형식 강제 + 실패 인지 주입이므로 학습 충돌이 아닌 인프라 확립으로 분류)

**Attempt 2** (`phase11_smoke_20260421_034724.json`, 69.73s):
- GATE 1 TREND → **retry-with-nudge 작동 확인** (1차 JSON 실패 → 2차 nudge 후 JSON 복구, 실증 완료)
- GATE 2 supervisor → `claude CLI 실패 (rc=1, 대표님): 프롬프트가 너무 깁니다` (cp949 mojibake but error text decoded)
- Root cause: `ClaudeAgentSupervisorInvoker.__call__` injects full producer_output JSON into `--append-system-prompt` body → Claude CLI context limit exceeded
- **Not Phase 11 scope** per 대표님 session #29 directive — this is an agent-layer architectural issue, not a 5-error-chain defect. Re-scoped to Phase 12 new REQ candidate `AGENT-STD-03: Supervisor invoker producer_output summary-only mode`

## Deliverables

### Infrastructure (shipped + working)
- `scripts/smoke/phase11_full_run.py` — full 0→13 GATE live harness (19480 bytes, exit code 0/2/3/4/5 taxonomy)
- `scripts/orchestrator/invokers.py` retry-with-nudge (ClaudeAgentProducerInvoker, max 3 attempts, Korean nudge prompt)
- `tests/phase11/test_invoker_retry.py` 5 retry tests GREEN (case 1-5: first-success / 2nd-success / 3rd-success / all-fail / nudge-prompt-exact-Korean)

### Documentation (shipped + awaits fill)
- `SCRIPT_QUALITY_DECISION.md` with `verdict: pending` frontmatter + 6-axis table + A/B/C selection logic
- `REQUIREMENTS.md` SCRIPT-01 D-19 amendment ("B/C 선택 시 Phase 12 조건부 발행")
- `REQUIREMENTS.md` Phase 12 5 REQ section (AGENT-STD-01/02 + SKILL-ROUTE-01 + FAIL-PROTO-01/02) pre-positioned
- `.claude/failures/FAILURES.md` F-D2-EXCEPTION-01 entry (trend-collector patch authorization)

### Reports (audit trail)
- `reports/phase11_smoke_phase11_20260421_031945.json` — 1차 실패 audit ($0.00)
- `reports/phase11_smoke_20260421_034724.json` — 2차 실패 audit ($0.00, retry-with-nudge 실증)

## Deferred to Phase 12

1. **Task 3b Full 0→13 live smoke execution** — requires supervisor prompt compression (new REQ AGENT-STD-03)
2. **Task 4 SCRIPT_QUALITY_DECISION.md verdict lock** — depends on successful smoke + 대표님 6-axis evaluation
3. **30명 AGENT.md 전수 표준화** (already planned: Phase 12 AGENT-STD-01/02)
4. **Skill routing matrix** (already planned: Phase 12 SKILL-ROUTE-01)
5. **FAILURES rotation policy** (already planned: Phase 12 FAIL-PROTO-01)

## 대표님 Approvals Consumed

1. Session #29 "둘다" — Option D retry-with-nudge 승인 + Phase 12 발의 양쪽 모두
2. Session #29 "a" — Phase 11 complete-with-deferred classification 승인 (full publication을 Phase 12 로 양보)

## Metrics

- **Budget**: $0.00 / $5.00 cap (preserved)
- **Live smoke attempts**: 2 (both aborted pre-billing)
- **Tests added**: 5 (test_invoker_retry.py)
- **Commits**: 8 (`c5a0c81`, `5830862`, `9e0c4c9`, `6b1dba4`, `10ba7b6`, `acb2ba3`, `96001d3`, `7eb569b`)
- **Files created**: 4 (smoke harness + script decision template + retry tests + 2 audit reports)
- **Files modified**: 4 (REQUIREMENTS + trend-collector AGENT + invokers + FAILURES)
- **Test regression**: 244 phase04 + 12 phase10 counter + 36 phase11 = **280/280 GREEN preserved**

## One-line Takeaway

Phase 11 infrastructure (Plans 11-01 through 11-05) is fully verified and ready; Phase 11 live-smoke publication (Plan 11-06) requires supervisor prompt compression now scoped to Phase 12 — 대표님 Core Value (외부 수익) 경로 **구조적으로 준비 완료, 실 개통은 Phase 12**.

---

_Written: 2026-04-21 (session #29)_
_Classification: complete_with_deferred per 대표님 direct approval_
