---
phase: 05-orchestrator-v2-write
plan: 05-02
subsystem: orchestrator
tags: [orchestrator, circuit-breaker, reliability, orch-06]
wave: 2
dependency-graph:
  requires:
    - 05-01 (exception hierarchy, pytest/phase05 scaffolding)
  provides:
    - scripts.orchestrator.circuit_breaker.CircuitBreaker
    - scripts.orchestrator.circuit_breaker.CircuitState
    - scripts.orchestrator.circuit_breaker.CircuitBreakerOpenError
  affects:
    - 05-03 (Checkpointer serialises breaker snapshots via to_dict)
    - 05-04 (GateGuard consults breaker state before permitting retries)
    - Plan 06 (Kling/Runway API adapters wrap calls with the breaker)
    - Plan 07 (run() pipeline instantiates and threads breakers per adapter)
tech-stack:
  added: []
  patterns:
    - Finite-state machine (CLOSED / OPEN / HALF_OPEN)
    - str-valued Enum for JSON-native serialisation
    - Monotonic-clock cooldown tracking (time.monotonic) decoupled from
      wall-clock ISO snapshots (datetime.now(UTC))
    - Dataclass + private leading-underscore fields for Checkpointer safety
key-files:
  created:
    - scripts/orchestrator/circuit_breaker.py
    - tests/phase05/test_circuit_breaker.py
    - tests/phase05/test_circuit_breaker_cooldown.py
  modified: []
decisions:
  - Cooldown uses time.monotonic, not datetime.now, so tests patch a single
    module-local symbol and the breaker is immune to wall-clock jumps
    (NTP sync, DST) during a long render run.
  - CircuitState inherits from str so Enum -> JSON encoding happens
    automatically; Checkpointer never needs a bespoke encoder.
  - to_dict renders opened_at as ISO-8601 with trailing 'Z' for UTC,
    matching the manifest timestamp format used elsewhere in the repo.
  - HALF_OPEN failure restarts the cooldown window at the probe timestamp
    (not the original trip time) so a flapping upstream cannot thrash
    the breaker into rapid probe loops.
  - Exception capture uses BaseException (not Exception) so that
    KeyboardInterrupt / SystemExit during a call still increment the
    failure counter -- the breaker must treat any abnormal exit as a
    signal that the adapter is unhealthy.
metrics:
  duration-minutes: 18
  tasks-completed: 2
  files-created: 3
  files-modified: 0
  tests-added: 20
  tests-passing: 20
  lines-added: 620
  completed-date: 2026-04-19
requirements-completed: [ORCH-06]
---

# Phase 05 Plan 02: CircuitBreaker Summary

One-liner: Stdlib-only CLOSED/OPEN/HALF_OPEN circuit breaker for ORCH-06 with monotonic-clock cooldown and JSON-primitive `to_dict()` snapshots so the Plan 05-03 Checkpointer can embed breaker state directly in the run manifest.

## Objective

Deliver the `CircuitBreaker` primitive required by CONTEXT D-6: every external-API adapter (Kling, Runway, voice) wraps its network call with a breaker that trips after 3 consecutive failures and stays OPEN for 300 seconds before admitting a single probe. The breaker must be serialisable by the Checkpointer and must not introduce third-party runtime dependencies beyond what the rest of the orchestrator already consumes.

## Tasks Executed

### Task 1 — TDD RED: failing test suite
**Commit:** `8fd0dce`
**Files:** `tests/phase05/test_circuit_breaker.py`, `tests/phase05/test_circuit_breaker_cooldown.py`

Two test files split by concern:

- **`test_circuit_breaker.py`** (14 tests covering state transitions) — default construction, CLOSED success/failure counting, CLOSED→OPEN threshold, OPEN short-circuit behaviour (verifying `fn` is *not* invoked), `CircuitBreakerOpenError.breaker_name` propagation, HALF_OPEN success→CLOSED, HALF_OPEN failure→OPEN, `call()` arg/kwarg forwarding, and `to_dict()` JSON-primitive contract (round-trip through `json.dumps`).
- **`test_circuit_breaker_cooldown.py`** (6 tests covering the 300-second timing contract) — default cooldown value, pre-boundary blocking at 0/299/300s, post-boundary probe admission at 300.001s, custom cooldown respect, cooldown-restart-on-failed-probe, and a regression guard asserting `time.monotonic` is the clock source (not `datetime.now`).

Time mocking uses `unittest.mock.patch` against the module-local symbol `scripts.orchestrator.circuit_breaker.time.monotonic`, making the suite wall-clock-independent.

### Task 2 — GREEN: CircuitBreaker implementation
**Commit:** `3c73cdc`
**File:** `scripts/orchestrator/circuit_breaker.py` (210 lines)

Three public symbols:

| Symbol | Purpose |
|---|---|
| `CircuitState(str, Enum)` | `CLOSED` / `OPEN` / `HALF_OPEN` — `str` parent means `.value` serialises natively. |
| `CircuitBreakerOpenError(RuntimeError)` | Carries `breaker_name` and `cooldown_remaining` for the failure journal (ORCH-04). |
| `CircuitBreaker` (dataclass) | `call(fn, *args, **kwargs)`, `to_dict()`, public `name` / `max_failures` / `cooldown_seconds` / `state` / `failure_count`. |

Internal state splits monotonic and wall-clock timestamps:
- `_opened_at_monotonic` drives the cooldown boundary check.
- `_opened_at_wall` (UTC `datetime`) is rendered to ISO-8601 by `to_dict()` for Checkpointer snapshots.

Failure handling uses `except BaseException` so `KeyboardInterrupt` / `SystemExit` still register as adapter failures — the breaker's job is to note abnormal exits of any kind.

## Verification

```
python -m pytest tests/phase05/test_circuit_breaker.py tests/phase05/test_circuit_breaker_cooldown.py -q --no-cov
20 passed in 0.08s
```

Full phase05 regression run (Plan 05-02 scope only — sibling Wave 2 test files from Plan 05-03 / 05-04 excluded because those plans are still in flight):

```
python -m pytest tests/phase05/ -q --no-cov \
  --ignore=tests/phase05/test_checkpointer_resume.py \
  --ignore=tests/phase05/test_checkpointer_roundtrip.py
38 passed in 0.08s
```

(18 Wave 1 tests + 20 new — no regressions.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Cooldown boundary admitted a probe at exactly `cooldown_seconds`**
- **Found during:** Task 2 verification (`pytest tests/phase05/test_circuit_breaker_cooldown.py`)
- **Issue:** Initial implementation guarded the OPEN state with `remaining > 0`. At elapsed = 300.0s, `remaining` evaluates to 0.0, so the breaker transitioned to HALF_OPEN and invoked `fn`. `test_open_breaker_blocks_before_cooldown_elapses` asserts the breaker must still be blocked at exactly the boundary (strict `>` semantics — the cooldown is a minimum dwell time, not a deadline).
- **Fix:** Changed the guard to `remaining >= 0`, so the probe is admitted only once more than `cooldown_seconds` have strictly elapsed. Added a block comment pointing to the test suite and CONTEXT D-6 to prevent regression.
- **Files modified:** `scripts/orchestrator/circuit_breaker.py` (lines 110-117)
- **Commit:** `f2b42b1`
- **Verification:** 20/20 CircuitBreaker tests pass, full phase05 suite (38 tests) green.

**Total deviations:** 1 auto-fix (1 boundary-semantics bug). **Impact:** Strict `>` boundary matches the CONTEXT D-6 contract and test-suite intent; no behavioural regression for any call path other than the exactly-at-boundary case, which was already specified as blocked.

## Parallel-Wave Protocol Compliance

- All commits used `git commit --no-verify` per the Wave 2 orchestrator instruction (avoids hook contention with sibling Plan 05-03 Checkpointer and Plan 05-04 GateGuard running concurrently).
- No files touched outside the assigned scope (`scripts/orchestrator/circuit_breaker.py`, `tests/phase05/test_circuit_breaker.py`, `tests/phase05/test_circuit_breaker_cooldown.py`).
- `scripts/orchestrator/__init__.py` left untouched to eliminate merge risk with siblings — consumers import directly from `scripts.orchestrator.circuit_breaker`.

## Downstream Consumer Checklist

For Plan 05-03 (Checkpointer):
- Call `breaker.to_dict()` and embed the result under `breakers.<name>` in the manifest — values are already JSON-safe.
- On restore, reconstruct with `CircuitBreaker(name, max_failures, cooldown_seconds)` and set `state`, `failure_count` from the snapshot (public fields).

For Plan 05-04 (GateGuard):
- Import `CircuitBreakerOpenError` and treat it as a non-retryable gate failure (the breaker is already enforcing its own cooldown).

For Plan 06 (API adapters):
- Instantiate one breaker per upstream (`CircuitBreaker("kling")`, `CircuitBreaker("runway")`) and wrap network calls via `breaker.call(http_post, url, ...)`.
- `tenacity` retries for transient 5xx inside CLOSED remain a caller concern — wrap the retried callable, then hand the whole thing to `breaker.call()`.

## Known Stubs

None.

## Self-Check: PASSED

- `scripts/orchestrator/circuit_breaker.py` — **FOUND**
- `tests/phase05/test_circuit_breaker.py` — **FOUND**
- `tests/phase05/test_circuit_breaker_cooldown.py` — **FOUND**
- Commit `8fd0dce` (Task 1 — RED tests) — **FOUND**
- Commit `3c73cdc` (Task 2 — GREEN implementation) — **FOUND**
- Commit `f2b42b1` (Rule 1 fix — strict cooldown boundary) — **FOUND**
- Commit `c13c219` (docs metadata — STATE + ROADMAP + REQUIREMENTS + SUMMARY) — **FOUND**
- 20/20 new CircuitBreaker tests passing — **VERIFIED**
- 38/38 phase05 tests passing (18 Wave 1 + 20 new, no regression) — **VERIFIED**
