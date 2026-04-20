# Phase 9.1 — Deferred Items

Items discovered during execution that are OUT OF SCOPE for the current plan
and logged here per execute-plan.md deviation rules (SCOPE BOUNDARY).

---

## 1. Runway VALID_RATIOS_BY_MODEL drift vs live API

**Discovered:** 2026-04-20 Plan 09.1-06 live smoke run (세션 #24 YOLO)
**File:** `scripts/orchestrator/api/runway_i2v.py` §50-53
**Severity:** Medium — wrong values advertised, API rejects with 400.
**Current state (Plan 04 landed):**

```python
VALID_RATIOS_BY_MODEL: dict[str, list[str]] = {
    "gen3a_turbo": ["16:9", "9:16", "768:1280", "1280:768"],
    "gen4.5": ["720:1280"],
}
```

**Observed live (HTTP 400 from `api.dev.runwayml.com/v1/image_to_video`):**

```
{'error': '`ratio` must be one of: 768:1280, 1280:768.', 'docUrl': '...'}
```

I.e. the `gen3a_turbo` I2V endpoint rejects `"16:9"` and `"9:16"` despite
them being advertised by the adapter's constant. Only pixel-dimension
ratios (`768:1280`, `1280:768`) are accepted.

**Impact on Plan 09.1-06:** mitigated in-place (Rule 1 auto-fix — smoke
CLI hardcodes `ratio="768:1280"` with an inline comment referencing this
deferred item). Live smoke run succeeded after the fix.

**Resolution target:** Plan 09.1-07 (Phase Gate aggregator) OR a Phase 10
Runway adapter patch. Fix = remove the two string-ratio entries from the
`gen3a_turbo` list, leaving only `["768:1280", "1280:768"]`; update
`DEFAULT_RATIO` accordingly (probably `"768:1280"` for the 9:16 vertical
Shorts default). Update `tests/phase091/test_runway_ratios.py` matchers.

**NOT fixed in Plan 09.1-06** because:
1. The adapter constant touches multiple tests (`test_runway_ratios.py`)
   that pin the current list — changing it is a Wave 1 regression surface.
2. Plan 09.1-06 scope is "smoke test harness + hook hygiene", not
   adapter remediation.
3. The inline Rule-1 fix in the smoke CLI unblocks the deliverable
   ("Live run: exit 0") without propagating the drift to production
   callers.

---
