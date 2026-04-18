# Phase 04 Deferred Items

Pre-existing issues discovered during plan execution that are **out of scope** per SCOPE BOUNDARY rule.
These will be addressed in the originating plan or a follow-up, not by the plan that discovered them.

## Discovered by plan 04-04 (2026-04-19)

### 1. `tests/phase04/test_ins_korean_naturalness.py::test_negative_10_at_least_9_fail` FAILS

- **Current state:** 7/10 negative samples FAIL (threshold is ≥9/10).
- **Originating plan:** 04-03 (Content Inspector Wave 1b — ins-korean-naturalness).
- **Reason out of scope for 04-04:** Plan 04-04 ships Style category inspectors only (ins-tone-brand, ins-readability, ins-thumbnail-hook). The Korean speech register simulation lives in `ins-korean-naturalness` (Content category) or in the test harness stub — both owned by 04-03.
- **Sample gaps observed:** kor-neg-03, kor-neg-06, kor-neg-09 all returned PASS (should be FAIL). Likely regex bank or sample-labeling mismatch in 04-03's simulation or samples.
- **Action:** Plan 04-03 (or a follow-up) to fix either the regex bank or sample categorization so 9/10 negatives are detected.
