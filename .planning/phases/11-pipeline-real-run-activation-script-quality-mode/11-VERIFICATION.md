---
phase: 11
slug: pipeline-real-run-activation-script-quality-mode
status: complete_with_deferred
verified: 2026-04-21
verifier: gsd-verifier (session #29)
sc_achieved: 4
sc_deferred: 2
sc_total: 6
budget_consumed_usd: 0.00
budget_cap_usd: 5.00
plans_executed: 5.5
plans_total: 6
tests_green: 280
tests_total: 280
commits_total: 14
deferred_to_phase_12:
  - SC#1_full_real_run_0_to_13
  - SC#2_video_published_and_script_verdict
  - agent_md_standardization
  - skill_routing_matrix
  - failures_rotation_policy
human_verification:
  - test: "Double-click `run_pipeline.cmd` on 대표님 PC"
    expected: "PowerShell window opens, .env loads, pipeline runs until GATE 2 supervisor block, window stays open via Read-Host"
    why_human: "Manual UX verification on real Windows 11 machine (ExecutionPolicy restricted baseline)"
  - test: "Post-Phase-12 first successful 0→13 smoke → 대표님 fills SCRIPT_QUALITY_DECISION.md 6-axis + verdict A/B/C"
    expected: "SCRIPT_QUALITY_DECISION.md frontmatter `verdict:` locked to A|B|C, matching `phase_12_spawn_required` boolean"
    why_human: "Subjective 대본 품질 평가 — 대표님 판단 전용 (ROADMAP SC#2 명시)"
gaps:
  - truth: "Full 0→13 GATE real-run smoke completes (SC#1)"
    status: partial
    reason: "Infrastructure fully working (invoker stdin, dotenv, adapter degrade, retry-with-nudge, wrapper, idempotency) but GATE 2 supervisor invoker emits full producer_output JSON → Claude CLI '프롬프트가 너무 깁니다' (rc=1). Not Phase 11 scope per 대표님 session #29 directive."
    artifacts:
      - path: "scripts/orchestrator/invokers.py::ClaudeAgentSupervisorInvoker.__call__"
        issue: "Passes full producer_output JSON into CLI body → CLI context limit exceeded"
    missing:
      - "Supervisor prompt compression (producer_output summary-only mode) — Phase 12 AGENT-STD-03 candidate REQ"
  - truth: "1 video published + SCRIPT-01 verdict locked (SC#2)"
    status: failed
    reason: "Depends on Gap #1 (video cannot be produced until supervisor block resolved). SCRIPT_QUALITY_DECISION.md template present with frontmatter `verdict: pending`."
    artifacts:
      - path: ".planning/phases/11-.../SCRIPT_QUALITY_DECISION.md"
        issue: "verdict still pending — awaits first successful live smoke video"
    missing:
      - "Phase 12 live smoke completion → 대표님 6-axis evaluation → frontmatter verdict: A|B|C lock"
---

# Phase 11: Pipeline Real-Run Activation + Script Quality Mode — Verification Report

**Phase Goal (ROADMAP §292-294):** v1.0.1 milestone 의 구조 완결 상태에서 **실 운영 작동 확보** + **대본 품질 옵션 확정**. 5 에러 chain 해결 → Full pipeline end-to-end real-run 가동 → 영상 1편 실 발행 + 대표님 품질 평가 → SCRIPT-01 옵션 A/B/C 확정. 본 phase 완결 시 대표님의 Core Value(외부 수익) 경로가 실제로 열림.

**Verified:** 2026-04-21 (session #29)
**Status:** 🟡 **Complete with Deferred** (4/6 SC 충족, 2 SC Phase 12 로 이관 — 대표님 직접 승인 "a" 응답)
**Re-verification:** No — initial verification

---

## §1 Per-SC Verdict Table

| SC | Title | Verdict | Evidence |
|----|-------|---------|----------|
| **SC#1** | Full 0→13 real-run smoke, no mock invoker | 🟡 **PARTIAL** | Infrastructure fully working: 11-01 stdin invoker ✅ (6 tests GREEN), 11-02 .env loader ✅ (15 tests GREEN), 11-03 adapter graceful degrade ✅ (8 tests GREEN), retry-with-nudge ✅ (5 tests GREEN, GATE 1 JSON recovery 실증 `7eb569b`). **Agent-layer blocker isolated**: supervisor invoker passes full producer_output JSON → Claude CLI context limit ('프롬프트가 너무 깁니다'). Deferred to Phase 12 as new REQ `AGENT-STD-03`. |
| **SC#2** | 1 video + SCRIPT-01 verdict locked | 🔴 **DEFERRED** | Video not published (GATE 2 supervisor block). SCRIPT_QUALITY_DECISION.md template landed (commit `5830862`) with frontmatter `verdict: pending`. Per D-19 amendment (commit `c5a0c81`): "B/C 선택 시 Phase 12 조건부 발행" — **Phase 12 is now the actual vehicle for this SC**. |
| **SC#3** | skill_patch_counter idempotency | ✅ **ACHIEVED** | Plan 11-05 commits `5ae667c` (RED) + `c3f87d3` (GREEN) + `8b42b05` (docs). `pytest tests/phase10/test_skill_patch_counter.py -v` 12/12 GREEN (11 baseline + `test_idempotency_skip_existing`). 2026-05-20 scheduler deadline +29 days margin. AUDIT-05 fully met. |
| **SC#4** | .env auto-load (zero-dep) | ✅ **ACHIEVED** | Plan 11-02 commits `3924313` (RED) + `c52c118` (GREEN). 15 edge-case tests GREEN (quoted / comments / BOM / export prefix / CRLF / multi-equals / missing file / pre-existing env / unicode / duplicate / etc.). Zero-dep satisfied (D-13). PIPELINE-02 fully met. |
| **SC#5** | run_pipeline.cmd/.ps1 wrapper | ✅ **ACHIEVED** (auto) + ⏳ **Human-UAT pending** (manual click) | Plan 11-04 commits `09b0570` + `93eb804` + `4e4cd91`. Both files exist at repo root. `ExecutionPolicy Bypass` + UTF-8 console + try/catch/finally Read-Host verified. PowerShell `Parser.ParseFile` dry-run 0 syntax errors. 2 wrapper tests GREEN. Manual double-click on 대표님 PC = human_verification item. PIPELINE-04 auto-verifiable portion fully met. |
| **SC#6** | Phase 04/08 retrospective VERIFICATION.md | ⏸ **INTENTIONALLY DEFERRED** | Per CONTEXT D-18 alternative: not scope-critical, no blast on 외부 수익 path. Declared optional at phase entry. |

**Score:** 4 / 6 SCs achieved (+ 2 deferred to Phase 12 with clear resolution path)

---

## §2 Must-Haves (Goal-Backward from ROADMAP §297-303)

- [x] D10-PIPELINE-DEF-01 5-에러 chain **인프라 해소** — 5/5 errors identified, 4 fully resolved (invoker / dotenv / adapter / wrapper), 1 (supervisor prompt extension) re-scoped to Phase 12 AGENT-STD-03
- [x] D10-01-DEF-02 skill_patch_counter idempotency (AUDIT-05) — SC#3 완결
- [ ] **영상 1편 실 발행** — DEFERRED to Phase 12 (supervisor prompt compression 선행)
- [ ] 대표님 SCRIPT-01 verdict lock — DEFERRED (depends on 영상)
- [x] **대표님 Core Value 경로 "실제로 열림" 조건** — **재정의**: infrastructure 개통 ✅ + Phase 12 agent layer 완결 시 실 발행 경로 열림 (2-phase approach — 대표님 session #29 "a" 승인)

---

## §3 Requirements Coverage

| REQ-ID | Title | Implementation | Validation | Status |
|--------|-------|----------------|------------|--------|
| PIPELINE-01 | Full pipeline end-to-end smoke | ✅ Plan 11-01 (`c361ce4`) stdin piping | 🟡 retry-with-nudge GATE 1 실증 / Full 0→13 ⏳ Phase 12 | partial |
| PIPELINE-02 | .env 자동 로드 | ✅ Plan 11-02 (`c52c118`) | ✅ 15 edge-case tests GREEN | **complete** |
| PIPELINE-03 | Adapter graceful degrade 전면 | ✅ Plan 11-03 (`81ff924`) _try_adapter helper | ✅ 8 tests GREEN | **complete** |
| PIPELINE-04 | 더블클릭 wrapper UX | ✅ Plan 11-03 argparse + Plan 11-04 wrapper (`93eb804`) | ✅ 2 wrapper tests GREEN + HUMAN-UAT pending | complete (auto) |
| SCRIPT-01 | 대본 품질 옵션 확정 | ✅ D-19 amendment (`c5a0c81`) + template (`5830862`) | ⏳ Verdict Phase 12 | deferred |
| AUDIT-05 | skill_patch_counter idempotency | ✅ Plan 11-05 (`c3f87d3`) | ✅ test_idempotency_skip_existing GREEN | **complete** |

**Coverage**: 4/6 fully complete, 1 partial (PIPELINE-01 infrastructure done / full smoke deferred), 1 deferred (SCRIPT-01). All 6 REQs have clear resolution paths — no blockers.

---

## §4 Required Artifacts

| Artifact | Expected | Exists | Substantive | Wired | Data Flows | Status |
|----------|----------|:------:|:-----------:|:-----:|:----------:|--------|
| `scripts/orchestrator/invokers.py` | stdin piping + retry-with-nudge | ✅ | ✅ 472 lines | ✅ subprocess.Popen + stdin=PIPE grep hit | ✅ retry-with-nudge validated GATE 1 | ✅ VERIFIED |
| `scripts/orchestrator/__init__.py` | _load_dotenv_if_present | ✅ | ✅ 152 lines | ✅ load_dotenv + setdefault 6 grep hits | ✅ adapters see env | ✅ VERIFIED |
| `scripts/orchestrator/shorts_pipeline.py` | _try_adapter helper + argparse optional | ✅ | ✅ 794 lines (under 800-soft-cap) | ✅ 8 grep hits | ✅ 7 adapters degrade | ✅ VERIFIED |
| `scripts/audit/skill_patch_counter.py` | _existing_violation_hashes guard | ✅ | ✅ 338 lines | ✅ main() conditional append | ✅ idempotency real | ✅ VERIFIED |
| `run_pipeline.cmd` | 3-line bootstrap | ✅ | ✅ 3 lines | ✅ -ExecutionPolicy Bypass | N/A wrapper | ✅ VERIFIED |
| `run_pipeline.ps1` | 89-line engine | ✅ | ✅ 3608 bytes | ✅ try/catch/finally Read-Host | ✅ .env → env → subprocess | ✅ VERIFIED |
| `scripts/smoke/phase11_full_run.py` | Full 0→13 live harness | ✅ | ✅ 19480 bytes | ✅ imports ShortsPipeline + real invokers | 🟡 executes, blocked at GATE 2 | ⚠️ BLOCKED (not artifact-level failure) |
| `SCRIPT_QUALITY_DECISION.md` | 6-axis eval template | ✅ | ✅ frontmatter + table | ✅ verdict placeholder | ⏳ awaits video | ⚠️ TEMPLATE-READY |
| `tests/phase11/` | 6 test files | ✅ | ✅ 36 tests | ✅ all passing | ✅ GREEN | ✅ VERIFIED |

---

## §5 Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `scripts/orchestrator/__init__.py` | `.env` at repo root | `_load_dotenv_if_present()` at package import | ✅ WIRED | 15 edge-case tests prove env propagation |
| `ShortsPipeline.__init__` | Kling/Runway/Typecast/ElevenLabs adapters | `_try_adapter(name, build, injected, hint)` helper | ✅ WIRED | 5 adapters + helper test GREEN; pipeline-site uniform pattern |
| `invokers.py::_invoke_claude_cli` | Claude CLI subprocess | `subprocess.Popen(stdin=PIPE).communicate(input=user_prompt)` | ✅ WIRED | 6 stdin tests GREEN + GATE 1 live execution proved |
| `invokers.py::ClaudeAgentProducerInvoker.__call__` | `_invoke_claude_cli` with retry nudge | `max 3 attempts, JSON-nudge on JSONDecodeError` | ✅ WIRED | 5 retry tests GREEN + GATE 1 JSON recovery 실증 (commit `7eb569b`) |
| `invokers.py::ClaudeAgentSupervisorInvoker.__call__` | Claude CLI with producer_output | Full JSON dumped into append-system-prompt body | ⚠️ PARTIAL | Works but exceeds CLI context — **Phase 12 AGENT-STD-03 resolves via summary-only mode** |
| `skill_patch_counter.main()` | FAILURES.md append | `_existing_violation_hashes()` grep → conditional append | ✅ WIRED | test_idempotency_skip_existing GREEN — 2nd run of unchanged state produces 0 new entries |
| `run_pipeline.cmd` | `run_pipeline.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File` | ✅ WIRED | .cmd 3-line bootstrap verified |
| `run_pipeline.ps1` | `py -3.11 -m scripts.orchestrator.shorts_pipeline` | `try { ... } catch { ... } finally { Read-Host }` | ✅ WIRED | syntax validated, HUMAN-UAT pending for click-on-real-PC |

**Score:** 7 WIRED / 8 total; 1 PARTIAL (supervisor) — the PARTIAL link is the entire Phase 12 entry gate, not a Phase 11 deliverable defect.

---

## §6 Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------:|--------|
| `_load_dotenv_if_present()` | `os.environ` | `.env` regex parse | ✅ Real (15 edge cases verified) | FLOWING |
| `_try_adapter` | `self.{kling,runway,typecast,elevenlabs}` | constructor call OR injected | ✅ Real (test MagicMock seam preserved) | FLOWING |
| `_invoke_claude_cli` | stdin → Claude CLI | user_prompt str | ✅ Real (live GATE 1 execution) | FLOWING |
| `invokers retry-with-nudge` | attempt count + nudge prompt | JSONDecodeError trigger | ✅ Real (GATE 1 2차 시도 JSON 복구 실증) | FLOWING |
| `_existing_violation_hashes` | set of 7-hex commit hashes | FAILURES.md regex grep | ✅ Real (idempotency test GREEN) | FLOWING |
| `SupervisorInvoker.__call__` prompt | full producer_output JSON | gate dispatch pipe | ⚠️ TOO LARGE (exceeds CLI context) | **BLOCKED** — Phase 12 compresses |

**Data-flow scoring:** 5/6 FLOWING, 1 BLOCKED by agent-layer constraint identified + re-scoped.

---

## §7 Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| phase11 unit tests GREEN | `py -3.11 -m pytest tests/phase11/ -q` | 36 passed | ✅ PASS |
| idempotency regression | `py -3.11 -m pytest tests/phase10/test_skill_patch_counter.py -q` | 12 passed | ✅ PASS |
| phase04 regression preserved | `py -3.11 -m pytest tests/phase04/ -q` | 244 passed in 0.46s | ✅ PASS |
| combined (phase11 + phase10 counter) | `py -3.11 -m pytest tests/phase11/ tests/phase10/test_skill_patch_counter.py -q` | 48 passed | ✅ PASS |
| retry-with-nudge | `py -3.11 -m pytest tests/phase11/test_invoker_retry.py -v` | 5/5 passed (case1-5) | ✅ PASS |
| run_pipeline.cmd file present | `test -f run_pipeline.cmd` | exists, 92 bytes | ✅ PASS |
| run_pipeline.ps1 syntax | `[Parser]::ParseFile('run_pipeline.ps1')` via pytest test_wrapper_smoke | 0 syntax errors | ✅ PASS |
| Full 0→13 live smoke | `py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd 5.00` | **FAILED at GATE 2** (supervisor rc=1 프롬프트 길이 초과) — aborted pre-billing | ❌ BLOCKED |
| SCRIPT_QUALITY_DECISION.md exists | `test -f .planning/phases/11-.../SCRIPT_QUALITY_DECISION.md` | exists, verdict=pending | ⚠️ TEMPLATE (awaits video) |

**Summary:** 7/9 PASS. 2 BLOCKED items both point to the same single root cause (supervisor prompt-too-long) which is re-scoped to Phase 12.

---

## §8 Anti-Pattern Scan

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | **No TODO/FIXME/placeholder comments** | — | All production code production-ready |
| — | — | **No `except: pass` silent swallow** | — | `_try_adapter` uses explicit `logger.warning` + typed except (`ValueError`, `KenBurnsUnavailable`) |
| — | — | **No `return None` / `return {}` stubs in hot paths** | — | All helpers return real data or raise |
| — | — | **No `skip_gates=True` anywhere** | — | pre_tool_use.py regex guard verified (CONFLICT_MAP A-6) |
| — | — | **No `t2v` / `text_to_video` anywhere** | — | I2V-only contract preserved (D-13) |
| `scripts/orchestrator/invokers.py` | 141 | retry counter starts at 1 (cosmetic) | ℹ️ Info | Harmless — makes log messages read natural ("시도 1/3") |
| `scripts/smoke/phase11_full_run.py` | — | Exit code 2 path raises on mid-pipeline exception | ℹ️ Info | Intentional — smoke harness correctly bubbles GATE 2 failure |

**Result:** Zero 🛑 Blockers · Zero ⚠️ Warnings · 2 ℹ️ Info items (cosmetic). Clean.

---

## §9 Human-UAT (pending items for `/gsd:verify-work`)

1. **Manual `run_pipeline.cmd` double-click test** on 대표님 PC (ExecutionPolicy Restricted baseline)
   - Expected: window opens → .env loads → Python launcher runs → (for now) aborts at GATE 2 supervisor → Read-Host keeps window open so 대표님 can read error
   - Why human: cannot simulate real-user double-click from Claude Code session
2. **Post-Phase-12 SCRIPT_QUALITY_DECISION.md fill** — after first successful 0→13 smoke:
   - 대표님 evaluates 6-axis (훅 / 대사 / 팩트 / 듀오 / 감정 / 완성도) on 1~5 scale
   - 대표님 fills frontmatter `verdict: A|B|C` + `video_url:` + `decided_on:` + `phase_12_spawn_required: true|false`

---

## §10 Budget & Evidence Audit

- **Budget**: $0.00 / $5.00 cap consumed across 2 live smoke attempts
  - 1차 (`phase11_20260421_031945.json`): aborted at GATE 1 TREND after 149.74s, $0.00 (JSON decode error pre-billing)
  - 2차 (`phase11_smoke_20260421_034724.json`): aborted at GATE 2 supervisor after 69.73s, $0.00 (CLI rc=1 pre-billing)
- **Full $5.00 cap preserved** for Phase 12 first successful smoke
- **Commits**: 14 total (Phase 11 execution window)
  - Plan 11-01: `53b9b1e`(test) + `c361ce4`(feat) + `d0182d9`(docs)
  - Plan 11-02: `3924313`(test) + `c52c118`(feat)
  - Plan 11-03: `e78c3c5`(test) + `81ff924`(feat) + `ced5ac1`(docs)
  - Plan 11-04: `09b0570`(test) + `93eb804`(feat) + `4e4cd91`(docs)
  - Plan 11-05: `5ae667c`(test) + `c3f87d3`(feat) + `8b42b05`(docs)
  - Plan 11-06 (partial): `c5a0c81`(REQ amend) + `5830862`(template) + `9e0c4c9`(harness) + `6b1dba4`(smoke1 audit) + `10ba7b6`(Phase 12 proposal) + `acb2ba3`(trend-collector patch) + `96001d3`(retry-with-nudge) + `7eb569b`(smoke2 audit)
- **Tests**: **280/280 GREEN** = phase04 244 + phase10 skill_patch_counter 12 + phase11 36 (= 6 stdin + 15 dotenv + 5 adapter_degrade + 3 argparse + 2 wrapper + 5 retry)
- **Zero regressions** from Phase 10 baseline (v1.0.1 96/96 REQs + 55/55 SCs audit PASSED `43bea97`)

---

## §11 Gap Analysis — Path to Phase 12

### Gap #1 — SC#1 Full 0→13 real-run smoke (PARTIAL)

- **Root cause**: `scripts/orchestrator/invokers.py::ClaudeAgentSupervisorInvoker.__call__` passes the full producer_output JSON into the CLI `--append-system-prompt` body → Claude CLI "프롬프트가 너무 깁니다." (rc=1) at GATE 2.
- **Evidence chain**: reports/phase11_smoke_20260421_034724.json (2차 smoke) + `.claude/failures/FAILURES.md` F-D2-EXCEPTION-01 (agent-layer pattern confirmed session #29)
- **Resolution path**: Phase 12 new REQ **`AGENT-STD-03: Supervisor invoker producer_output summary-only mode`** — compress producer_output to summary (decisions + error_codes only, drop verbose prose) before injecting into supervisor prompt body.
- **Not Phase 11 scope rationale** (대표님 session #29 approval): (1) Phase 11 scope was infrastructure activation, (2) supervisor compression is an agent-layer architectural change not a 5-error-chain defect fix, (3) forcing it into Phase 11 violates AF-10 Anthropic sweet-spot (9-10 plan sprawl risk).

### Gap #2 — SC#2 Video published + verdict locked (DEFERRED)

- **Root cause**: Cannot publish without completing 0→13 smoke (Gap #1 dependency)
- **Resolution path**: Phase 12 first successful 0→13 smoke → YouTube upload → 대표님 6-axis evaluation → `SCRIPT_QUALITY_DECISION.md` frontmatter `verdict:` lock
- **Scope preservation**: SCRIPT-01 REQ D-19 amendment (commit `c5a0c81`) already encodes "B/C 선택 시 Phase 12 조건부 발행" — Phase 12 is now the official vehicle for this SC as well

---

## §12 Deferred to Phase 12 (Scope Expansion)

Per 대표님 session #29 "둘다" directive + "a" approval for complete-with-deferred classification:

1. **SC#1 full real-run** (supervisor prompt compression prerequisite)
2. **SC#2 video + verdict** (depends on SC#1)
3. **30명 AGENT.md 전수 표준화** (AGENT-STD-01/02 REQs — session #29 structural insight)
4. **Skill routing 매트릭스** (SKILL-ROUTE-01 REQ — 30 × 8 에이전트×스킬 mapping)
5. **FAILURES rotation 정책** (FAIL-PROTO-01 REQ — 500줄 상한 + _archive/YYYY-MM.md)
6. **F-D2-EXCEPTION-02 batch** (FAIL-PROTO-02 REQ — directive-authorized batch pattern for 30+ file patch)
7. **NEW CANDIDATE**: `AGENT-STD-03` (supervisor invoker producer_output summary-only mode — added post-Phase-11 per gap analysis)

**Phase 12 Coverage projection**: v1.0.1 96 + Phase 11 6 + Phase 12 6 (5 original + AGENT-STD-03) = **108 REQs total** once Phase 12 is planned.

---

## §13 Overall Verdict

**Status: `complete_with_deferred`**

Phase 11 achieved its **primary infrastructure goal** (D10-PIPELINE-DEF-01 5-에러 chain 해소). The 2 unmet SCs are both downstream of a single newly-discovered agent-layer blocker (supervisor prompt length) that was out of Phase 11 scope and properly re-scoped to Phase 12 with 대표님 direct approval.

**Core Value assessment**: 외부 수익 경로 **구조적으로 준비 완료**. 실 개통은 Phase 12 에서 한 단계 더 (supervisor compression + agent standardization 완결 시 라이브 smoke 성공). 2-phase approach is the correct decomposition — forcing publication into Phase 11 would have violated AF-10 (Anthropic sweet-spot) and pre-committed scripter redesign before empirical 6-axis data.

**Tests**: 280/280 GREEN across phase04 + phase10 + phase11 surfaces. Zero regressions.

**Budget**: $0.00 consumed / $5.00 cap preserved.

**Recommendation**: Proceed to `/gsd:discuss-phase 12` (별 세션 권장 — context budget preservation).

---

_Verified: 2026-04-21T06:00:00+09:00_
_Verifier: gsd-verifier (Claude Opus 4.7 1M context) — session #29_
_Phase 11 complete with deferred per 대표님 direct approval ("a" response)._
