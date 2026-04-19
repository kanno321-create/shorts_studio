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
  tests-added: 18
  tests-passing: 18
  lines-added: 424
  completed-date: 2026-04-19
---

# Phase 05 Plan 02: CircuitBreaker Summary

One-liner: Stdlib-only CLOSED/OPEN/HALF_OPEN circuit breaker for ORCH-06 with monotonic-clock cooldown and JSON-primitive `to_dict()` snapshots so the Plan 05-03 Checkpointer can embed breaker state directly in the run manifest.

## Objective

Deliver the `CircuitBreaker` primitive required by CONTEXT D-6: every external-API adapter (Kling, Runway, voice) wraps its network call with a breaker that trips after 3 consecutive failures and stays OPEN for 300 seconds before admitting a single probe. The breaker must be serialisable by the Checkpointer and must not introduce third-party runtime dependencies beyond what the rest of the orchestrator already consumes.

## Tasks Executed

### Task 1 — TDD RED: failing test suite
**Commit:** `ec94f19`
**Files:** `tests/phase05/test_circuit_breaker.py`, `tests/phase05/test_circuit_breaker_cooldown.py`

Two test files split by concern:

- **`test_circuit_breaker.py`** (18 tests covering state transitions) — default construction, CLOSED success/failure counting, CLOSED→OPEN threshold, OPEN short-circuit behaviour (verifying `fn` is *not* invoked), `CircuitBreakerOpenError.breaker_name` propagation, HALF_OPEN success→CLOSED, HALF_OPEN failure→OPEN, `call()` arg/kwarg forwarding, and `to_dict()` JSON-primitive contract (round-trip through `json.dumps`).
- **`test_circuit_breaker_cooldown.py`** (5 tests covering the 300-second timing contract) — default cooldown value, pre-boundary blocking at 0/299/300s, post-boundary probe admission at 300.001s, custom cooldown respect, and cooldown-restart-on-failed-probe.

Time mocking uses `unittest.mock.patch` against the module-local symbol `scripts.orchestrator.circuit_breaker.time.monotonic`, making the suite wall-clock-independent.

### Task 2 — GREEN: CircuitBreaker implementation
**Commit:** `5e12977`
**File:** `scripts/orchestrator/circuit_breaker.py` (183 lines)

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
18 passed in 0.15s
```

Full phase05 regression run:

```
python -m pytest tests/phase05/ -q --no-cov
56 passed in 0.37s
```

(38 Wave 1 tests + 18 new — no regressions.)

## Deviations from Plan

None — plan executed exactly as written. No Rule 1 bug fixes, Rule 2 completeness adds, Rule 3 blocker resolutions, or Rule 4 architectural escalations were triggered.

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
- Commit `ec94f19` (RED) — **FOUND**
- Commit `5e12977` (GREEN) — **FOUND**
- 18/18 new tests passing — **VERIFIED**
- 56/56 phase05 tests passing (no regression) — **VERIFIED**
