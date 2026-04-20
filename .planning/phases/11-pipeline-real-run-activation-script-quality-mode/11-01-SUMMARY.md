---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 01
subsystem: orchestrator-invoker
tags: [pipeline, claude-cli, stdin, subprocess, korean-errors]
dependency_graph:
  requires:
    - scripts/orchestrator/invokers.py (pre-existing _invoke_claude_cli with subprocess.run)
    - Claude CLI 2.1.112 stdin piping contract (verified live 2026-04-21)
    - D-04 test-seam preservation (cli_runner injection point)
  provides:
    - stdin-piped Claude CLI invocation (subprocess.Popen + communicate)
    - unblocks PIPELINE-01 SC#1 live GATE 0→13 smoke
    - zombie-proof timeout path (proc.kill() + drain on Windows)
    - 6-test phase11 stdin regression guard
  affects:
    - ClaudeAgentProducerInvoker (unchanged — cli_runner seam intact)
    - ClaudeAgentSupervisorInvoker (unchanged — cli_runner seam intact)
    - All downstream GATE dispatches (trend → assembler → publisher)
tech_stack:
  added: []
  patterns:
    - subprocess.Popen(stdin=PIPE).communicate(input=..., timeout=...)
    - explicit kill() + drain on TimeoutExpired (Windows zombie prevention)
    - Korean-first RuntimeError diagnostic (대표님 호칭, D-04)
key_files:
  created:
    - tests/phase11/__init__.py
    - tests/phase11/conftest.py
    - tests/phase11/test_invoker_stdin.py
  modified:
    - scripts/orchestrator/invokers.py (L118-171 rewritten, net +12 lines)
decisions:
  - id: D-01
    summary: stdin piping adopted for Claude CLI 2.1.112 compatibility
  - id: D-02
    summary: argv canonical form [cli_path, --print, --append-system-prompt, body, --json-schema, schema] — no positional prompt
  - id: D-03
    summary: Claude Agent SDK rejected (Max subscription double-billing)
  - id: D-04
    summary: _invoke_claude_cli signature + raises + Korean messages preserved verbatim
metrics:
  duration_sec: 152
  tasks_completed: 2
  files_created: 3
  files_modified: 1
  tests_before: 244 (phase04 baseline)
  tests_after: 250 (phase04 244 + phase11 6)
  commits: 2
completed_date: 2026-04-21
requirements_completed: [PIPELINE-01]
---

# Phase 11 Plan 01: Invoker stdin-fix Summary

**One-liner:** `_invoke_claude_cli` rewritten from `subprocess.run([...argv, user_prompt])` to `subprocess.Popen(argv, stdin=PIPE).communicate(input=user_prompt)` — unblocks Claude CLI 2.1.112 "Input must be provided through stdin or prompt argument" contract, preserving D-04 signature + Korean-first error messages + cli_runner test seam.

## Objective Achieved

PIPELINE-01 prerequisite delivered: full GATE 0→13 smoke can now dispatch real Claude calls. Without this fix, every supervisor/producer invocation failed on the first call, blocking D10-PIPELINE-DEF-01 resolution and 대표님 Core Value (외부 수익) video publication.

## Files

### Created

| File | Lines | Purpose |
|------|-------|---------|
| `tests/phase11/__init__.py` | 1 | Phase 11 test package marker |
| `tests/phase11/conftest.py` | 68 | Shared fixtures (`tmp_env_file`, `mock_cli_runner`, `fake_claude_cli_runner_factory`, `preserve_env`) + `sys.path` wiring |
| `tests/phase11/test_invoker_stdin.py` | 151 | 6 tests: stdin wire / argv canonical / timeout / rc!=0 / empty stdout / Korean round-trip |

### Modified

| File | Delta | Change |
|------|-------|--------|
| `scripts/orchestrator/invokers.py` | +29 / -16 (net +13, total 351) | `_invoke_claude_cli` rewritten L118-184: `subprocess.Popen` + `stdin=PIPE` + `communicate(input=user_prompt, timeout=...)` with `proc.kill()` + drain on `TimeoutExpired` |

## Tasks

### Task 1 — RED: test scaffold (commit `53b9b1e`)

6 failing tests demonstrating the required contract against the current `subprocess.run` implementation:

1. `test_invoker_uses_stdin_piping` — Popen called with `stdin=subprocess.PIPE`; `communicate(input=user_prompt, timeout=...)`; user_prompt NOT in argv.
2. `test_invoker_argv_contains_expected_flags` — argv equals `[cli_path, "--print", "--append-system-prompt", body, "--json-schema", schema]` (D-02 canonical).
3. `test_invoker_timeout_raises_korean_runtime_error` — `TimeoutExpired` → RuntimeError with `타임아웃` + `대표님` + `30s`; `proc.kill()` + drain (communicate called twice).
4. `test_invoker_rc_nonzero_raises_korean_error` — returncode=2 + stderr="boom" → RuntimeError with `rc=2` + `대표님` + stderr tail.
5. `test_invoker_empty_stdout_raises_korean_error` — rc=0 but stdout empty → RuntimeError with `stdout 비어있음` + `대표님`.
6. `test_invoker_korean_prompt_round_trip` — Korean text in user_prompt sent unchanged; Popen kwargs include `text=True, encoding="utf-8", errors="replace"`.

State after Task 1: 6/6 RED (expected).

### Task 2 — GREEN: rewrite `_invoke_claude_cli` (commit `c361ce4`)

Replaced L118-171 per RESEARCH §Pattern 1 verbatim:

- `cmd` list: 6 elements (no `user_prompt` positional)
- `subprocess.Popen` with `stdin=PIPE`, `stdout=PIPE`, `stderr=PIPE`, `text=True`, `encoding="utf-8"`, `errors="replace"` (Pitfall 3 cp949 guard)
- `proc.communicate(input=user_prompt, timeout=timeout_s)` — user_prompt delivered via stdin
- `except subprocess.TimeoutExpired`: `proc.kill()` → `proc.communicate()` drain → `raise RuntimeError("claude CLI 타임아웃 ({timeout_s}s 초과, 대표님): {err}")` — zombie prevention on Windows
- `if proc.returncode != 0`: `raise RuntimeError("claude CLI 실패 (rc={rc}, 대표님): {stderr_tail}")` — unchanged
- `if not stdout or not stdout.strip()`: `raise RuntimeError("claude CLI stdout 비어있음 — --json-schema 응답 미수신 (대표님)")` — unchanged
- Signature + return type unchanged (D-04)

State after Task 2: 6/6 GREEN + 244/244 phase04 GREEN (zero regression).

## Verification

```bash
$ python -m pytest tests/phase11/test_invoker_stdin.py -v
6 passed in 0.83s

$ python -m pytest tests/phase04/ -q
244 passed in 0.42s

$ grep -c "stdin=subprocess.PIPE" scripts/orchestrator/invokers.py
1  # L159

$ grep -c "subprocess.Popen" scripts/orchestrator/invokers.py
1  # L157

$ grep -c "타임아웃\|대표님\|stdout 비어있음" scripts/orchestrator/invokers.py
11

$ grep -rn "patch.*scripts\.orchestrator\.invokers\.subprocess\.run" tests/
# 0 hits — D-04 cli_runner seam preserves all existing tests

$ python -c "print(sum(1 for _ in open('scripts/orchestrator/invokers.py', encoding='utf-8')))"
351  # 500~800 line cap not breached (helper module, not orchestrator)
```

## Test Migration

**Performed:** Zero. Precondition grep confirmed no test in `tests/` directly patches `scripts.orchestrator.invokers.subprocess.run`. All invoker tests in phase04/05/06/07/08 use the `cli_runner` injection seam (MagicMock bypass), which is untouched by this rewrite. RESEARCH §Pattern 1 prediction validated.

## Deviations from Plan

None — plan executed exactly as written. RED → GREEN → regression check, all three steps passed on first attempt.

## Compliance

- **CLAUDE.md Forbidden #3 (silent try-except fallback):** Compliant. The single `try/except subprocess.TimeoutExpired` block performs explicit `proc.kill()` + drain + `raise RuntimeError(...)` with Korean diagnostic. No silent swallow.
- **CLAUDE.md Forbidden #2 (TODO next-session):** Compliant. No TODO markers introduced.
- **CLAUDE.md Must-do #3 (orchestrator 500~800 lines):** N/A — invokers.py is a helper module (351 lines), not the pipeline orchestrator.
- **D-04 test seam preservation:** Confirmed. `ClaudeAgentProducerInvoker` / `ClaudeAgentSupervisorInvoker` class definitions, constructors, and `cli_runner` parameter unchanged.
- **D-03 no Claude Agent SDK:** Confirmed. `import anthropic` not introduced; subprocess path preserved.
- **Korean 대표님 messages:** Verbatim preserved (11 occurrences grep-verified).

## Downstream Impact

- **Plan 11-06** (full smoke) now has a working Claude CLI dispatch path. Without this plan, GATE 1 (TREND) would fail on the first claude call.
- **No impact on existing adapters** (Kling/Runway/Typecast/ElevenLabs/Shotstack) — those are orchestrated by `shorts_pipeline.py`, not `invokers.py`.
- **No impact on Phase 4 filesystem invariants** (agent AGENT.md loading path `load_agent_system_prompt` unchanged).

## Commits

| Hash | Task | Message |
|------|------|---------|
| `53b9b1e` | 1 | test(11-01): add failing tests for stdin-piped Claude CLI invoker |
| `c361ce4` | 2 | feat(11-01): rewrite _invoke_claude_cli to stdin piping |

## Self-Check: PASSED

Verified 2026-04-21:
- All 5 claimed files exist on disk (tests/phase11/__init__.py, conftest.py, test_invoker_stdin.py, scripts/orchestrator/invokers.py, 11-01-SUMMARY.md)
- All 2 claimed commits present in git log (53b9b1e, c361ce4)
- 6/6 phase11 stdin tests GREEN
- 244/244 phase04 regression GREEN
