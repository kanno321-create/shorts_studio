# Phase 04 Deferred Items

## 04-03 → cross-plan observation (not own-scope)

**Issue:** `tests/phase04/test_inspector_compliance.py` (created by a parallel plan — likely 04-05 or 04-06 compliance inspectors) uses a module-scoped fixture `agent_files(repo_root)` that requests the function-scoped `repo_root` fixture from `conftest.py`. Pytest raises `ScopeMismatch` for all 16 parametrized tests in that file.

**Observed:** 2026-04-19, during Plan 04-03 execution.

**Why deferred:** Scope boundary. Plan 04-03 owns only `test_inspector_content.py` + `test_ins_korean_naturalness.py` (both PASS, 16/16). The compliance-test fixture bug belongs to the parallel plan that authored `test_inspector_compliance.py`.

**Fix suggestion (for owning plan):** Either change the `agent_files` fixture in `test_inspector_compliance.py` to function scope, or promote `repo_root` in `conftest.py` to session scope.

**Status:** Phase 4 test suite overall: **115 passed, 16 errors (unrelated scope mismatch)**. Plan 04-03 own tests: 16/16 PASS.

---

## 04-04 → cross-plan observation (not own-scope)

**Issue:** `tests/phase04/test_ins_korean_naturalness.py::test_negative_10_at_least_9_fail` FAILS — detects only 7/10 negative Korean samples as FAIL (threshold is ≥9/10). Samples kor-neg-03 / kor-neg-06 / kor-neg-09 return PASS.

**Observed:** 2026-04-19, during Plan 04-04 execution (regression check after Task 2 commit).

**Why deferred:** Scope boundary. Plan 04-04 owns Style category (ins-tone-brand + ins-readability + ins-thumbnail-hook). The Korean speech register regex / sample-labeling logic belongs to Plan 04-03 (Content category, ins-korean-naturalness).

**Fix suggestion (for owning plan 04-03):** Re-audit kor-neg-03 / 06 / 09 samples against regex bank in §5.3 RESEARCH.md. Either fix sample categorization or extend regex bank (foreign_word_overuse or informal_in_hao) so 9/10 negatives flag FAIL.

**Status (Plan 04-04 own tests):** `tests/phase04/test_inspector_style.py` → 13/13 PASS in 0.09s. `validate_all_agents --path .claude/agents/inspectors/style` → OK: 3 agent(s) validated.
