# Phase 15 Deferred Items

Out-of-scope discoveries encountered during Phase 15 execution — logged per
CLAUDE.md / GSD Rule: "Only auto-fix issues DIRECTLY caused by the current task's
changes." Not caused by Phase 15 plans; owners to triage separately.

## 1. tests/phase091/test_runway_ratios.py::test_ratio_auto_selects_first_valid

**Discovered during:** Plan 15-02 Task 15-02-02 verify pass (2026-04-21).

**Status:** Pre-existing failure — confirmed by `git stash` + re-run on clean
HEAD (before any Plan 15-02 changes applied). Unrelated to invokers.py or
encoding fix.

**Symptom:**
```
>       assert adapter.ratio == "16:9"
E       AssertionError: assert '768:1280' == '16:9'
E         - 16:9
E         + 768:1280
tests\phase091\test_runway_ratios.py:43: AssertionError
```

**Root cause (hypothesis):** `RunwayI2VAdapter` default ratio for `gen3a_turbo`
model appears to resolve to `768:1280` (pixel dimension form) instead of the
expected `16:9` (aspect ratio form). Likely a prior schema bump in
`scripts/orchestrator/api/runway_i2v.py` where ratio canonicalisation changed
format without updating the test oracle.

**Impact on Phase 15:** None. Plan 15-02 changes Claude CLI invocation path
only (`scripts/orchestrator/invokers.py`); Runway adapter is orthogonal.

**Suggested follow-up:** Phase 9.1 owner to either (a) update test oracle to
`768:1280` if the adapter change was intentional, or (b) fix adapter to emit
`16:9` if the original oracle reflects REQ-091-05 contract. Not blocking for
Phase 15 Waves 2-6.

**Proof of pre-existence:** `git stash && pytest tests/phase091/test_runway_ratios.py::test_ratio_auto_selects_first_valid` on HEAD `08954a7` (before invokers.py patch) produced identical failure → pre-existing confirmed (대표님).
