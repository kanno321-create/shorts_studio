---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/orchestrator/invokers.py
  - tests/phase11/__init__.py
  - tests/phase11/conftest.py
  - tests/phase11/test_invoker_stdin.py
autonomous: true
requirements: [PIPELINE-01]
must_haves:
  truths:
    - "`_invoke_claude_cli` sends user_prompt through stdin (not argv) per D-01/D-02"
    - "Claude CLI 2.1.112 canonical argv contains `--print`, `--append-system-prompt`, `--json-schema` — no positional prompt"
    - "Timeout / rc!=0 / empty stdout error paths preserved with Korean-first messages + `대표님` appellation (D-04)"
    - "Existing `cli_runner` test seam (ClaudeAgentProducerInvoker / ClaudeAgentSupervisorInvoker) unchanged — MagicMock paths keep working"
    - "UTF-8 encoding + errors='replace' preserved so Korean text in AGENT.md / user_prompt round-trips cleanly on Windows cp949 default console"
    - "Zombie subprocess avoided on timeout via explicit `proc.kill()` + `proc.communicate()` drain"
  artifacts:
    - path: "scripts/orchestrator/invokers.py"
      provides: "stdin-piped Claude CLI invocation, D-04 signature preserved"
      contains: "subprocess.Popen, stdin=subprocess.PIPE, proc.communicate(input=user_prompt"
    - path: "tests/phase11/__init__.py"
      provides: "test dir marker"
      min_lines: 1
    - path: "tests/phase11/conftest.py"
      provides: "fixtures: tmp_env_file, mock_cli_runner, fake_claude_cli_runner_factory"
      contains: "fake_claude_cli_runner_factory"
    - path: "tests/phase11/test_invoker_stdin.py"
      provides: "6 tests covering stdin wire / timeout / rc!=0 / empty stdout / Korean round-trip / seam compat"
      min_lines: 120
  key_links:
    - from: "scripts/orchestrator/invokers.py::_invoke_claude_cli"
      to: "subprocess.Popen + communicate(input=user_prompt)"
      via: "stdin=PIPE + text=True + encoding='utf-8' + errors='replace'"
      pattern: "stdin=subprocess\\.PIPE"
    - from: "ClaudeAgentProducerInvoker.__init__"
      to: "cli_runner test seam"
      via: "unchanged parameter signature"
      pattern: "cli_runner: Callable\\[\\.\\.\\.\\] \\| None"
---

<objective>
PIPELINE-01: Rewrite `_invoke_claude_cli` to use `subprocess.Popen(stdin=PIPE).communicate(input=user_prompt)` instead of passing `user_prompt` as an argv positional. Claude CLI 2.1.112 rejects the positional form with "Input must be provided either through stdin or as a prompt argument when using --print" — this was the #5 error in the D10-PIPELINE-DEF-01 chain blocking full-pipeline smoke.

Purpose: Unlock GATE 0→13 real-run dispatch. Producer / Supervisor invokers flow through `_invoke_claude_cli`; without this fix, every Claude call in the pipeline fails before reaching any supervisor verdict.

Output:
- `scripts/orchestrator/invokers.py` with stdin piping
- `tests/phase11/__init__.py` + `tests/phase11/conftest.py` + `tests/phase11/test_invoker_stdin.py` (6 tests GREEN)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md
@scripts/orchestrator/invokers.py
@.claude/memory/project_claude_code_max_no_api_key.md

<interfaces>
<!-- Current _invoke_claude_cli signature (unchanged per D-04) -->

From scripts/orchestrator/invokers.py (L118-171, target of rewrite):
```python
def _invoke_claude_cli(
    system_prompt: str,
    user_prompt: str,
    json_schema: str,
    cli_path: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> str:
    """Run ``claude --print`` and return stdout.

    Args:
        system_prompt: AGENT.md body (Phase 4 agent definition).
        user_prompt: JSON-encoded input payload (producer/supervisor).
        json_schema: JSON schema string enforcing structured output.
        cli_path: Absolute path to ``claude`` binary.
        timeout_s: subprocess timeout in seconds.

    Returns:
        stdout text (JSON string per ``--json-schema`` contract).

    Raises:
        RuntimeError: non-zero exit code, timeout, or stdout empty
            (Korean-first diagnostic).
    """
```

From scripts/orchestrator/invokers.py (L174-234) — ClaudeAgentProducerInvoker uses `cli_runner` seam:
```python
class ClaudeAgentProducerInvoker:
    def __init__(
        self,
        agent_dir_root: Path,
        circuit_breaker: CircuitBreaker | None = None,
        cli_runner: Callable[..., str] | None = None,  # <-- test seam, DO NOT change
        cli_path: str | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
```

Error message format (D-04 — preserve verbatim):
- `"claude CLI 타임아웃 ({timeout_s}s 초과, 대표님): {err}"`
- `"claude CLI 실패 (rc={proc.returncode}, 대표님): {stderr_tail}"`
- `"claude CLI stdout 비어있음 — --json-schema 응답 미수신 (대표님)"`
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Wave 0 test scaffold + 6 RED tests for stdin invoker</name>
  <files>tests/phase11/__init__.py, tests/phase11/conftest.py, tests/phase11/test_invoker_stdin.py</files>
  <read_first>
    - scripts/orchestrator/invokers.py (L118-171 current _invoke_claude_cli + L174-234 ClaudeAgentProducerInvoker for cli_runner seam)
    - tests/phase10/conftest.py (fixture style reference — tmp_git_repo pattern)
    - tests/phase10/test_skill_patch_counter.py (L1-60 test structure reference)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md (D-01, D-02, D-04)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 1 + §Pitfall 3
  </read_first>
  <behavior>
    - Test 1 `test_invoker_uses_stdin_piping`: patches subprocess.Popen → asserts `stdin=subprocess.PIPE` + argv does NOT contain user_prompt positional + `communicate(input=user_prompt, timeout=timeout_s)` called
    - Test 2 `test_invoker_argv_contains_expected_flags`: argv == `[cli_path, "--print", "--append-system-prompt", body, "--json-schema", schema]` (no trailing user_prompt)
    - Test 3 `test_invoker_timeout_raises_korean_runtime_error`: Popen.communicate raises TimeoutExpired → RuntimeError message contains `"타임아웃"` AND `"대표님"` AND timeout value; proc.kill() + drain called
    - Test 4 `test_invoker_rc_nonzero_raises_korean_error`: returncode=2 + stderr="boom" → RuntimeError message contains `"rc=2"` AND `"대표님"` AND truncated stderr tail
    - Test 5 `test_invoker_empty_stdout_raises_korean_error`: stdout="" → RuntimeError message contains `"stdout 비어있음"` AND `"대표님"`
    - Test 6 `test_invoker_korean_prompt_round_trip`: user_prompt with Korean chars (`"나베랄 감마 테스트 {대표님}"`) sent unchanged via communicate(input=...); Popen invoked with `text=True, encoding="utf-8", errors="replace"`
  </behavior>
  <action>
    Create `tests/phase11/__init__.py` with single comment line:
    ```python
    """Phase 11 test package — PIPELINE-01..04 + SCRIPT-01 + AUDIT-05."""
    ```

    Create `tests/phase11/conftest.py`:
    ```python
    """Phase 11 shared fixtures."""
    from __future__ import annotations

    import os
    from pathlib import Path
    from typing import Callable
    from unittest.mock import MagicMock

    import pytest


    @pytest.fixture
    def tmp_env_file(tmp_path: Path) -> Path:
        """Returns a Path to an empty tmp `.env` — tests fill contents as needed."""
        env_path = tmp_path / ".env"
        env_path.write_text("", encoding="utf-8")
        return env_path


    @pytest.fixture
    def mock_cli_runner() -> MagicMock:
        """Drop-in replacement for `cli_runner` test seam (returns canned JSON)."""
        runner = MagicMock()
        runner.return_value = '{"status": "ok"}'
        return runner


    @pytest.fixture
    def fake_claude_cli_runner_factory() -> Callable[[str], MagicMock]:
        """Builds a cli_runner that returns a given canned JSON payload."""
        def _build(payload: str) -> MagicMock:
            runner = MagicMock()
            runner.return_value = payload
            return runner
        return _build


    @pytest.fixture
    def preserve_env():
        """Restore os.environ after test — prevents _load_dotenv_if_present leakage."""
        saved = dict(os.environ)
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(saved)
    ```

    Create `tests/phase11/test_invoker_stdin.py`:
    ```python
    """PIPELINE-01 stdin-piped Claude CLI invocation tests (6 cases)."""
    from __future__ import annotations

    import subprocess
    from unittest.mock import MagicMock, patch

    import pytest

    from scripts.orchestrator.invokers import _invoke_claude_cli


    def _make_popen_mock(stdout: str = '{"ok": true}', stderr: str = "", returncode: int = 0):
        proc = MagicMock()
        proc.communicate.return_value = (stdout, stderr)
        proc.returncode = returncode
        return proc


    def test_invoker_uses_stdin_piping():
        """Popen invoked with stdin=PIPE; user_prompt passed via communicate(input=...)."""
        with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
            popen_cls.return_value = _make_popen_mock()
            _invoke_claude_cli(
                system_prompt="SYS",
                user_prompt="USER_PROMPT_MARKER",
                json_schema='{"type":"object"}',
                cli_path="/fake/claude",
                timeout_s=30,
            )
            call = popen_cls.call_args
            # argv is first positional arg
            argv = call.args[0]
            assert "USER_PROMPT_MARKER" not in argv, "user_prompt MUST NOT be in argv"
            assert call.kwargs["stdin"] is subprocess.PIPE
            assert call.kwargs["stdout"] is subprocess.PIPE
            assert call.kwargs["stderr"] is subprocess.PIPE
            proc = popen_cls.return_value
            proc.communicate.assert_called_once_with(input="USER_PROMPT_MARKER", timeout=30)


    def test_invoker_argv_contains_expected_flags():
        """argv matches D-02 canonical form (no positional prompt)."""
        with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
            popen_cls.return_value = _make_popen_mock()
            _invoke_claude_cli(
                system_prompt="SYS_BODY",
                user_prompt="u",
                json_schema='{"type":"object"}',
                cli_path="/fake/claude",
            )
            argv = popen_cls.call_args.args[0]
            assert argv == [
                "/fake/claude",
                "--print",
                "--append-system-prompt", "SYS_BODY",
                "--json-schema", '{"type":"object"}',
            ]


    def test_invoker_timeout_raises_korean_runtime_error():
        """TimeoutExpired → RuntimeError with Korean diagnostic + 대표님 + proc.kill()+drain."""
        with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
            proc = MagicMock()
            proc.communicate.side_effect = [
                subprocess.TimeoutExpired(cmd="claude", timeout=30),
                ("", ""),  # drain call after kill
            ]
            popen_cls.return_value = proc
            with pytest.raises(RuntimeError) as exc:
                _invoke_claude_cli(
                    system_prompt="s", user_prompt="u", json_schema="{}",
                    cli_path="/fake/claude", timeout_s=30,
                )
            msg = str(exc.value)
            assert "타임아웃" in msg
            assert "대표님" in msg
            assert "30s" in msg
            proc.kill.assert_called_once()
            # communicate called twice: initial + drain
            assert proc.communicate.call_count == 2


    def test_invoker_rc_nonzero_raises_korean_error():
        """returncode!=0 → RuntimeError with rc + 대표님 + stderr tail (last 500)."""
        with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
            popen_cls.return_value = _make_popen_mock(stdout="", stderr="boom detail", returncode=2)
            with pytest.raises(RuntimeError) as exc:
                _invoke_claude_cli(
                    system_prompt="s", user_prompt="u", json_schema="{}",
                    cli_path="/fake/claude",
                )
            msg = str(exc.value)
            assert "rc=2" in msg
            assert "대표님" in msg
            assert "boom detail" in msg


    def test_invoker_empty_stdout_raises_korean_error():
        """rc=0 but stdout empty → RuntimeError with stdout diagnostic + 대표님."""
        with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
            popen_cls.return_value = _make_popen_mock(stdout="", stderr="", returncode=0)
            with pytest.raises(RuntimeError) as exc:
                _invoke_claude_cli(
                    system_prompt="s", user_prompt="u", json_schema="{}",
                    cli_path="/fake/claude",
                )
            msg = str(exc.value)
            assert "stdout 비어있음" in msg
            assert "대표님" in msg


    def test_invoker_korean_prompt_round_trip():
        """Korean chars in user_prompt passed through; Popen kwargs include utf-8 encoding."""
        korean_prompt = "나베랄 감마 테스트 {대표님} — 한국어 왕복"
        with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
            popen_cls.return_value = _make_popen_mock(stdout='{"reply":"ok"}')
            out = _invoke_claude_cli(
                system_prompt="시스템", user_prompt=korean_prompt, json_schema="{}",
                cli_path="/fake/claude",
            )
            assert out == '{"reply":"ok"}'
            kwargs = popen_cls.call_args.kwargs
            assert kwargs.get("text") is True
            assert kwargs.get("encoding") == "utf-8"
            assert kwargs.get("errors") == "replace"
            popen_cls.return_value.communicate.assert_called_once()
            assert popen_cls.return_value.communicate.call_args.kwargs["input"] == korean_prompt
    ```

    Expected state after this task: all 6 tests **RED** (imports work, but current invokers.py still uses `subprocess.run` with positional prompt — assertions in Test 1 & 2 fail).
  </action>
  <verify>
    <automated>pytest tests/phase11/test_invoker_stdin.py -v --tb=short 2>&1 | tail -40</automated>
  </verify>
  <acceptance_criteria>
    - `tests/phase11/__init__.py` exists
    - `tests/phase11/conftest.py` exists and contains `tmp_env_file`, `mock_cli_runner`, `fake_claude_cli_runner_factory`, `preserve_env` fixtures
    - `tests/phase11/test_invoker_stdin.py` exists with exactly 6 `def test_` functions
    - `pytest tests/phase11/test_invoker_stdin.py --collect-only -q` lists 6 tests
    - Running the tests produces RED (test_invoker_uses_stdin_piping + test_invoker_argv_contains_expected_flags fail because current invoker passes user_prompt as argv positional — expected)
  </acceptance_criteria>
  <done>3 test-scaffold files committed; 6 RED tests collected and run (2 fail on positional-argv, 4 fail on Popen patch name mismatch — all expected before Task 2 GREEN).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Rewrite _invoke_claude_cli to stdin piping — GREEN all 6 tests</name>
  <files>scripts/orchestrator/invokers.py</files>
  <read_first>
    - scripts/orchestrator/invokers.py (FULL FILE — L1-292; must understand cli_runner seam at L187, L234, L252, L292)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 1 (lines 541-599)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-01, D-02, D-03, D-04
    - tests/phase11/test_invoker_stdin.py (just-created, provides exact expectations)
  </read_first>
  <behavior>
    - After rewrite, all 6 tests in test_invoker_stdin.py PASS
    - `_invoke_claude_cli` signature unchanged (system_prompt, user_prompt, json_schema, cli_path, timeout_s=DEFAULT_TIMEOUT_S) → str
    - ClaudeAgentProducerInvoker / ClaudeAgentSupervisorInvoker classes untouched (D-04)
    - All existing tests in tests/phase04/+ tests/phase05/ use the `cli_runner` test seam (bypass subprocess entirely), so zero direct patches expected. Hard-precondition grep in action step asserts zero hits; if any found, task FAILS immediately — no silent migration (per RESEARCH §Pattern 1).
  </behavior>
  <action>
    Replace lines 118-171 of `scripts/orchestrator/invokers.py` with the stdin-piping version. Preserve the exact docstring intent + signature. D-04 mandates identical Korean error messages.

    EXACT REPLACEMENT BODY (copy verbatim):
    ```python
    def _invoke_claude_cli(
        system_prompt: str,
        user_prompt: str,
        json_schema: str,
        cli_path: str,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> str:
        """Run ``claude --print`` via stdin piping and return stdout.

        Claude CLI 2.1.112 canonical form: user_prompt flows through
        stdin (``--input-format text`` is the default). The legacy
        positional ``user_prompt`` argv slot was removed by the CLI —
        attempting to pass it raises "Input must be provided either
        through stdin or as a prompt argument when using --print"
        (D10-PIPELINE-DEF-01 error #5).

        Args unchanged (D-04 test-seam preservation). Raises unchanged
        (Korean-first RuntimeError on timeout / rc!=0 / empty stdout).
        """
        cmd = [
            cli_path,
            "--print",
            "--append-system-prompt", system_prompt,
            "--json-schema", json_schema,
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            stdout, stderr = proc.communicate(input=user_prompt, timeout=timeout_s)
        except subprocess.TimeoutExpired as err:
            # Explicit reap — prevents zombie on Windows + drains pipes.
            proc.kill()
            proc.communicate()
            raise RuntimeError(
                f"claude CLI 타임아웃 ({timeout_s}s 초과, 대표님): {err}"
            ) from err
        if proc.returncode != 0:
            stderr_tail = (stderr or "")[-500:]
            raise RuntimeError(
                f"claude CLI 실패 (rc={proc.returncode}, 대표님): {stderr_tail}"
            )
        if not stdout or not stdout.strip():
            raise RuntimeError(
                "claude CLI stdout 비어있음 — --json-schema 응답 미수신 (대표님)"
            )
        return stdout.strip()
    ```

    Ensure `import subprocess` already present at top of file (it is — L118 of current file uses subprocess.run).

    After edit, verify no regression:
    ```
    pytest tests/phase11/test_invoker_stdin.py -v         # 6 GREEN
    pytest tests/phase04/ -q                              # 244/244 GREEN (seam-only tests)
    ```

    # Pre-condition grep (hard fail if hits found — manual migration required)
    ```
    grep -rn "patch.*scripts\.orchestrator\.invokers\.subprocess\.run" tests/ 2>/dev/null
    ```
    # Expected: zero hits per RESEARCH §Pattern 1 (all tests use cli_runner seam).
    # If hits found: FAIL task immediately. Report file:line list. Executor must
    # stop and escalate — do NOT attempt silent migration. Manual migration pattern:
    #   patch("scripts.orchestrator.invokers.subprocess.run") → patch("scripts.orchestrator.invokers.subprocess.Popen")
    #   mock.return_value.stdout/.stderr/.returncode → mock.return_value.communicate.return_value = (stdout, stderr); mock.return_value.returncode = rc
  </action>
  <verify>
    <automated>pytest tests/phase11/test_invoker_stdin.py tests/phase04/ -q 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "stdin=subprocess.PIPE" scripts/orchestrator/invokers.py` returns at least 1 match
    - `grep -n "subprocess.Popen" scripts/orchestrator/invokers.py` returns at least 1 match
    - `grep -c "user_prompt" scripts/orchestrator/invokers.py` — user_prompt appears in function signature + communicate call + docstring, NOT in `cmd = [...]` list. Run `grep -A 10 "cmd = \[" scripts/orchestrator/invokers.py` and confirm no `user_prompt` inside the `cmd` list braces.
    - `grep -n "타임아웃\|대표님\|stdout 비어있음" scripts/orchestrator/invokers.py` returns ≥3 matches (Korean error messages preserved)
    - `grep -rn "patch.*scripts\.orchestrator\.invokers\.subprocess\.run" tests/` returns 0 hits (hard precondition — per RESEARCH §Pattern 1, all invoker tests use cli_runner seam; any hit = immediate task FAIL)
    - `pytest tests/phase11/test_invoker_stdin.py -v` → 6 passed
    - `pytest tests/phase04/ -q` → 244/244 passed (zero regression)
  </acceptance_criteria>
  <done>6 stdin-invoker tests GREEN + 244/244 phase04 regression preserved + grep confirms positional user_prompt removed from argv.</done>
</task>

</tasks>

<verification>
**Per-plan verify (post both tasks):**
```bash
pytest tests/phase11/test_invoker_stdin.py -v       # 6/6 GREEN
pytest tests/phase04/ -q                             # 244/244 baseline preserved
python -c "print(sum(1 for _ in open('scripts/orchestrator/invokers.py', encoding='utf-8')))"  # line count within cap
```

**PIPELINE-01 SC#1 linkage:** This plan delivers the prerequisite for Plan 11-06 live smoke. Without stdin piping, GATE 1 (TREND) fails on the first Claude call.
</verification>

<success_criteria>
- [ ] `subprocess.Popen(stdin=PIPE)` replaces `subprocess.run` in `_invoke_claude_cli`
- [ ] argv contains `--print`, `--append-system-prompt`, `--json-schema` — NO user_prompt positional
- [ ] Korean-first error messages preserved verbatim (타임아웃 / 대표님 / stdout 비어있음)
- [ ] `proc.kill()` + drain on TimeoutExpired (zombie prevention)
- [ ] 6 tests in `tests/phase11/test_invoker_stdin.py` all GREEN
- [ ] 244/244 phase04 regression baseline preserved
- [ ] cli_runner test seam unchanged (ClaudeAgentProducerInvoker / ClaudeAgentSupervisorInvoker signatures intact)
</success_criteria>

<output>
After completion, create `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-01-SUMMARY.md` with:
- Files modified + net line deltas
- Test count before/after (244 → 250)
- Any existing test migrations performed (expected: zero)
- Confirmation that 대표님 Korean messages + cli_runner seam preserved
</output>
