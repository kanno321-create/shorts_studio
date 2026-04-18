---
phase: 4
slug: agent-team-design
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
completed: 2026-04-19
---

# Phase 4 — Validation Strategy

> 29 agents + rubric schema 검증. pytest + harness-audit 혼합.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + harness-audit (existing skill) + Python stdlib jsonschema validator |
| **Config file** | `tests/conftest.py` (Wave 0 installs) |
| **Quick run command** | `pytest tests/phase4/ -q --tb=short` |
| **Full suite command** | `pytest tests/phase4/ -v && python -m harness_audit .claude/agents/` |
| **Estimated runtime** | ~20s quick / ~60s full |

---

## Sampling Rate

- **After every plan commit:** Run `pytest tests/phase4/test_<agent>.py`
- **After every Wave:** Run `pytest tests/phase4/`
- **Before verify-work:** Full suite + harness-audit must be green

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 4-01-01 | 01 | 0 | RUB-04 | schema | `python -c "import json,jsonschema; jsonschema.validate(json.load(open('.claude/agents/_shared/rubric-schema.json')), <meta>)"` | ✅ |
| 4-01-02 | 01 | 0 | AGENT-07,08,09 | template | `test -f .claude/agents/_shared/agent-template.md && grep -c "MUST REMEMBER" .claude/agents/_shared/agent-template.md` (≥1) | ✅ |
| 4-01-03 | 01 | 0 | COMPLY-01~06 | bank | `test -f tests/phase4/fixtures/af_bank.json && python -c "import json; assert len(json.load(open('tests/phase4/fixtures/af_bank.json')))>=10"` | ✅ |
| 4-02-01 | 02 | 1 | AGENT-04 struct | agent-count | `ls .claude/agents/inspectors/structural/*/AGENT.md \| wc -l` (=3) | ✅ |
| 4-03-01 | 03 | 1 | AGENT-04 content + CONTENT | agent-count | `ls .claude/agents/inspectors/content/*/AGENT.md \| wc -l` (=3) | ✅ |
| 4-03-02 | 03 | 1 | CONTENT-02 Korean | smoke | `pytest tests/phase4/test_ins_korean_naturalness.py` — 10 samples, ≥9 FAIL | ✅ |
| 4-04-01 | 04 | 1 | AGENT-04 style | agent-count | `ls .claude/agents/inspectors/style/*/AGENT.md \| wc -l` (=3) | ✅ |
| 4-05-01 | 05 | 2 | AGENT-04 compl + COMPLY | agent-count | `ls .claude/agents/inspectors/compliance/*/AGENT.md \| wc -l` (=3) | ✅ |
| 4-05-02 | 05 | 2 | COMPLY-01~06 + AF-4/5/13 | smoke | `pytest tests/phase4/test_compliance_blocks.py` — 100% block rate | ✅ |
| 4-06-01 | 06 | 2 | AGENT-04 tech | agent-count | `ls .claude/agents/inspectors/technical/*/AGENT.md \| wc -l` (=3) | ✅ |
| 4-07-01 | 07 | 2 | AGENT-04 media | agent-count | `ls .claude/agents/inspectors/media/*/AGENT.md \| wc -l` (=2) | ✅ |
| 4-08-01 | 08 | 3 | AGENT-01,02 | agent-count | `ls .claude/agents/producers/*/AGENT.md \| wc -l` (≥9 Producer core+3단) | ✅ |
| 4-09-01 | 09 | 4 | AGENT-03,05 | agent-count | `ls .claude/agents/producers/*/AGENT.md .claude/agents/supervisors/*/AGENT.md \| wc -l` (supervisor=1, support=5) | ✅ |
| 4-10-01 | 10 | 5 | AGENT-07,08,09 | harness-audit | `python -m scripts.harness_audit --path .claude/agents/ --strict` (exit 0) | ✅ |
| 4-10-02 | 10 | 5 | RUB-06 GAN | contamination | `grep -rE "producer_prompt\|producer_system" .claude/agents/inspectors/` (=0) | ✅ |
| 4-10-03 | 10 | 5 | RUB-01 LogicQA | schema | `pytest tests/phase4/test_logicqa_schema.py` all PASS | ✅ |

---

## Wave 0 Requirements

- [x] `.claude/agents/_shared/rubric-schema.json` — draft-07 compliant, covers verdict/score/evidence[]/semantic_feedback
- [x] `.claude/agents/_shared/agent-template.md` — reusable template with MUST REMEMBER at end
- [x] `tests/conftest.py` — shared fixtures
- [x] `tests/phase4/fixtures/af_bank.json` — AF-4 (voice clone), AF-5 (real face), AF-13 (K-pop) sample bank (10+ each)
- [x] `tests/phase4/fixtures/korean_speech_samples.json` — 존댓말/반말 혼용 10 samples
- [x] `tests/phase4/test_rubric_schema.py` — validates any AGENT.md output conforms
- [x] `scripts/harness_audit.py` — enforces ≤500 lines + description ≤1024 chars + MUST REMEMBER position

---

## Manual-Only Verifications

*None — all Phase 4 checks automatable via pytest + grep + line-count.*

---

## Validation Sign-Off

- [x] All 34 REQs have at least one `<automated>` test
- [x] Sampling continuity preserved
- [x] Wave 0 covers all shared infrastructure
- [x] `nyquist_compliant: true` set after Wave 0 complete (Plan 10 Wave 5, 2026-04-19)

**Approval:** ✅ Plan 10 Wave 5 — 244/244 pytest PASS, harness_audit score 100, validate_all_agents 32/32 OK, grep_gan_contamination 17/17 clean (2026-04-19)
