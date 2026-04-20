"""Claude Code CLI wiring (REQ-091-01, Phase 9.1 architecture fix 2026-04-20).

Replaces :meth:`ShortsPipeline._default_producer_invoker` /
``_default_supervisor_invoker`` / ``_default_asset_sourcer``
(NotImplementedError since Phase 5) with Claude Code CLI subprocess
invokers.

대표님 Claude Code Max 구독 — ``anthropic`` Python SDK (usage-based
billing) 직접 호출 금지 (memory: project_claude_code_max_no_api_key).
Max 구독 인증은 ``claude`` CLI 가 담당 → subprocess 로 재사용.

Architecture
------------
* Producer (per-gate content generation) → ``claude --print
  --append-system-prompt <AGENT.md body> --json-schema ...``
* Supervisor (Verdict judgment) → 동일 CLI, schema 는 ``{"verdict":
  "PASS"|"FAIL"|"RETRY"}`` 만 강제
* Asset sourcer (script → anchor image path) → NanoBananaAdapter

Contract
--------
* Producer invoker signature: ``(agent_name, gate, inputs) -> dict``
* Supervisor invoker signature: ``(gate, output: dict) -> Verdict``
  (``Verdict`` is the enum from :mod:`scripts.orchestrator.state`)
* Asset sourcer signature: ``(prompt: str) -> Path``

JSON enforcement
----------------
Claude Code CLI 의 ``--json-schema`` 플래그가 구조적 출력을 강제.
Anthropic API 의 response_format 대체 (Phase 9.1 original code 의
triple defense 보다 단일 flag 로 간결).

Korean-first errors per 나베랄 감마 tone (대표님 전용).
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = [
    "CLAUDE_CLI_BIN",
    "DEFAULT_TIMEOUT_S",
    "load_agent_system_prompt",
    "ClaudeAgentProducerInvoker",
    "ClaudeAgentSupervisorInvoker",
    "make_default_producer_invoker",
    "make_default_supervisor_invoker",
    "make_default_asset_sourcer",
    # Phase 11 Option D retry-with-nudge (F-D2-EXCEPTION-01 defense-in-depth)
    "_MAX_NUDGE_ATTEMPTS",
    "_JSON_NUDGE_PROMPT_KO",
]

# CLI binary name (resolved via shutil.which at call time)
CLAUDE_CLI_BIN = "claude"

# subprocess timeout per invocation. Phase 10 tuning 가능.
DEFAULT_TIMEOUT_S = 180

_PRODUCER_JSON_SCHEMA = '{"type":"object"}'
_SUPERVISOR_JSON_SCHEMA = (
    '{"type":"object","required":["verdict"],'
    '"properties":{"verdict":{"type":"string","enum":["PASS","FAIL","RETRY"]}}}'
)

_MISSING_CLI_MSG = (
    "claude CLI 를 PATH 에서 찾을 수 없습니다 — 대표님 Claude Code 설치 상태 "
    "확인 필요 (memory: project_claude_code_max_no_api_key)."
)


def load_agent_system_prompt(agent_dir: Path) -> tuple[str, dict]:
    """Parse ``AGENT.md`` into ``(body, frontmatter)``.

    Strips a YAML frontmatter block bounded by ``---\\n`` markers.
    Returns an empty dict when no frontmatter is present.

    Raises:
        FileNotFoundError: ``AGENT.md`` is missing from ``agent_dir``.
        RuntimeError: PyYAML not importable (Phase 6 dependency pin,
            Korean-first error on violation).
    """
    path = Path(agent_dir) / "AGENT.md"
    if not path.exists():
        raise FileNotFoundError(
            f"AGENT.md 파일 없음: {path} — "
            f"Phase 4 에이전트 정의 확인 필요 (대표님)"
        )
    content = path.read_text(encoding="utf-8")
    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            try:
                import yaml
            except ImportError as err:  # pragma: no cover — dep pinned
                raise RuntimeError(
                    "PyYAML 미설치 — 대표님 uv pip install pyyaml 후 재시도"
                ) from err
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return body, frontmatter
    return content.strip(), {}


def _resolve_cli_path(explicit: str | None = None) -> str:
    """Resolve ``claude`` CLI absolute path; raise Korean ValueError if missing."""
    if explicit:
        return explicit
    found = shutil.which(CLAUDE_CLI_BIN)
    if not found:
        raise ValueError(_MISSING_CLI_MSG)
    return found


def _invoke_claude_cli_once(
    system_prompt: str,
    user_prompt: str,
    json_schema: str,
    cli_path: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> str:
    """Run ``claude --print`` via stdin piping and return stdout (single attempt).

    Claude CLI 2.1.112 canonical form: user_prompt flows through
    stdin (``--input-format text`` is the default). The legacy
    positional ``user_prompt`` argv slot was removed by the CLI —
    attempting to pass it raises "Input must be provided either
    through stdin or as a prompt argument when using --print"
    (D10-PIPELINE-DEF-01 error #5, Phase 11 PIPELINE-01 D-01/D-02).

    Args unchanged (D-04 test-seam preservation). Raises unchanged
    (Korean-first RuntimeError on timeout / rc!=0 / empty stdout).

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


# Nudge message injected on retry when first attempt returned non-JSON
# (Phase 11 F-D2-EXCEPTION-01 교훈 — Option D defense-in-depth).
_JSON_NUDGE_PROMPT_KO = (
    "직전 응답은 JSON이 아니었습니다. JSON 객체만 출력하세요. "
    "설명/질문 금지."
)

# Max total attempts for _invoke_claude_cli retry-with-nudge wrapper
# (1 initial + 2 nudge retries = 3 total per Task 3 spec).
_MAX_NUDGE_ATTEMPTS = 3


def _looks_like_json(text: str) -> bool:
    """Cheap prefix check — valid JSON response starts with ``{`` or ``[``."""
    if not text:
        return False
    stripped = text.lstrip()
    if not stripped:
        return False
    first = stripped[0]
    return first in ("{", "[")


def _invoke_claude_cli(
    system_prompt: str,
    user_prompt: str,
    json_schema: str,
    cli_path: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    agent_label: str = "claude-cli",
) -> str:
    """Retry-with-JSON-nudge wrapper around :func:`_invoke_claude_cli_once`.

    Phase 11 F-D2-EXCEPTION-01 defense-in-depth (대표님 session #29 Option D):
    when the first attempt returns text that does not look like JSON, we
    re-invoke the CLI with a short Korean nudge prepended to the user
    prompt — up to ``_MAX_NUDGE_ATTEMPTS`` (3 total) attempts. If every
    attempt still fails to yield JSON (or raises RuntimeError), the last
    RuntimeError / best-effort stdout surfaces to the caller.

    The signature is kept source-compatible with ``_invoke_claude_cli_once``
    plus an optional ``agent_label`` used only for diagnostic logging. All
    existing test seams (``cli_runner`` injection at
    ``ClaudeAgentProducerInvoker`` / ``ClaudeAgentSupervisorInvoker``)
    continue to bypass this wrapper — only the production default path
    goes through retry.

    Args:
        system_prompt: AGENT.md body (Phase 4 agent definition).
        user_prompt: JSON-encoded input payload.
        json_schema: JSON schema string enforcing structured output.
        cli_path: Absolute path to ``claude`` binary.
        timeout_s: subprocess timeout in seconds.
        agent_label: producer/supervisor name for log lines (default
            ``"claude-cli"`` when wrapped by the low-level call).

    Returns:
        stdout text that passes the :func:`_looks_like_json` prefix check
        on some attempt 1..3. Raises :class:`RuntimeError` if all attempts
        fail.
    """
    last_err: Exception | None = None
    last_stdout: str | None = None
    for attempt in range(1, _MAX_NUDGE_ATTEMPTS + 1):
        # Prepend a nudge on retries 2+. The initial prompt is unchanged.
        effective_prompt = (
            user_prompt
            if attempt == 1
            else f"{_JSON_NUDGE_PROMPT_KO}\n\n{user_prompt}"
        )
        try:
            stdout = _invoke_claude_cli_once(
                system_prompt=system_prompt,
                user_prompt=effective_prompt,
                json_schema=json_schema,
                cli_path=cli_path,
                timeout_s=timeout_s,
            )
        except RuntimeError as err:
            last_err = err
            last_stdout = None
            if attempt < _MAX_NUDGE_ATTEMPTS:
                logger.warning(
                    "[invoker] %s CLI 오류 재시도 %d/%d (대표님): %s",
                    agent_label, attempt, _MAX_NUDGE_ATTEMPTS, err,
                )
                continue
            # Exhausted — re-raise the last error verbatim.
            raise
        # CLI returned something — check if it looks like JSON.
        last_stdout = stdout
        if _looks_like_json(stdout):
            if attempt > 1:
                logger.info(
                    "[invoker] %s JSON 복구 성공 (시도 %d/%d, 대표님)",
                    agent_label, attempt, _MAX_NUDGE_ATTEMPTS,
                )
            return stdout
        # Non-JSON output — schedule retry with nudge.
        if attempt < _MAX_NUDGE_ATTEMPTS:
            logger.warning(
                "[invoker] %s JSON 미준수 재시도 %d/%d (대표님) — head=%r",
                agent_label, attempt, _MAX_NUDGE_ATTEMPTS, stdout[:120],
            )
            continue
        # Final attempt also non-JSON — raise synthesising error.
        raise RuntimeError(
            f"{agent_label} JSON 미준수 재시도 {_MAX_NUDGE_ATTEMPTS}회 모두 실패 "
            f"(대표님): head={stdout[:120]!r}"
        )
    # Unreachable — the for-loop either returns or raises.
    _tail = last_stdout[:120] if last_stdout else None
    raise RuntimeError(  # pragma: no cover
        f"{agent_label} retry 루프 이탈 (대표님): "
        f"last_err={last_err!r} last_stdout={_tail!r}"
    )


class ClaudeAgentProducerInvoker:
    """Callable invoker: ``(agent_name, gate, inputs) -> dict``.

    Resolves the per-producer system prompt from
    ``agent_dir_root / <agent_name> / AGENT.md``, invokes ``claude
    --print`` via subprocess with ``--append-system-prompt`` +
    ``--json-schema {"type":"object"}``, and returns the parsed dict.

    Uses Claude Code Max 구독 인증 (no API key). Tests inject a
    ``cli_runner`` callable; production passes ``None`` and the real
    subprocess call is used.
    """

    def __init__(
        self,
        agent_dir_root: Path,
        circuit_breaker=None,
        cli_path: str | None = None,
        cli_runner: Callable | None = None,
    ) -> None:
        self.agent_dir_root = Path(agent_dir_root)
        self.circuit_breaker = circuit_breaker
        self._cli_path = _resolve_cli_path(cli_path)
        # cli_runner = test seam; signature mirrors _invoke_claude_cli
        self._cli_runner = cli_runner or _invoke_claude_cli

    def __call__(self, agent_name: str, gate: str, inputs: dict) -> dict:
        agent_dir = self.agent_dir_root / agent_name
        if not agent_dir.exists():
            raise FileNotFoundError(
                f"Agent 디렉토리 없음: {agent_dir} — "
                f"Phase 4 AGENT.md 확인 (대표님)"
            )
        body, _ = load_agent_system_prompt(agent_dir)
        user_payload = json.dumps(
            {"gate": gate, "inputs": inputs}, ensure_ascii=False
        )

        def _call():
            return self._cli_runner(
                system_prompt=body,
                user_prompt=user_payload,
                json_schema=_PRODUCER_JSON_SCHEMA,
                cli_path=self._cli_path,
            )

        stdout = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as err:
            logger.error(
                "[invoker] producer '%s' JSON parse 실패: %s — head=%r",
                agent_name, err, stdout[:200],
            )
            raise RuntimeError(
                f"Producer '{agent_name}' JSON 미준수 (대표님): {err}"
            ) from err


class ClaudeAgentSupervisorInvoker:
    """Callable invoker: ``(gate, output: dict) -> Verdict``.

    The returned ``Verdict`` is the enum from
    :mod:`scripts.orchestrator.state` (``Verdict.PASS`` /
    ``Verdict.FAIL`` / ``Verdict.RETRY``). Enum identity (``is``) is
    the stable comparison surface for callers.

    ``gate`` may be a :class:`GateName` enum or a bare string — we
    read ``.name`` when present and fall back to ``str(gate)``.
    """

    def __init__(
        self,
        agent_dir: Path,
        circuit_breaker=None,
        cli_path: str | None = None,
        cli_runner: Callable | None = None,
    ) -> None:
        self.agent_dir = Path(agent_dir)
        self.circuit_breaker = circuit_breaker
        self._cli_path = _resolve_cli_path(cli_path)
        self._cli_runner = cli_runner or _invoke_claude_cli
        self._system, _ = load_agent_system_prompt(self.agent_dir)

    def __call__(self, gate, output: dict):
        # Lazy import to avoid a cycle.
        from .state import Verdict

        gate_name = getattr(gate, "name", str(gate))
        # --- Phase 12 AGENT-STD-03 (D-A4-04): compress producer_output ---
        # Avoids Phase 11 smoke 2차 "프롬프트가 너무 깁니다" (rc=1). See
        # :func:`_compress_producer_output` for the summary-only contract.
        output = _compress_producer_output(output)
        # -----------------------------------------------------------------
        user_payload = json.dumps(
            {"gate": gate_name, "producer_output": output},
            ensure_ascii=False,
        )

        def _call():
            return self._cli_runner(
                system_prompt=self._system,
                user_prompt=user_payload,
                json_schema=_SUPERVISOR_JSON_SCHEMA,
                cli_path=self._cli_path,
            )

        stdout = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        parsed = json.loads(stdout)
        verdict_str = (parsed.get("verdict") or "").upper()
        try:
            return Verdict[verdict_str]
        except KeyError as err:
            raise RuntimeError(
                f"Supervisor verdict 파싱 실패: {verdict_str!r} (대표님)"
            ) from err


# =======================================================================
# Factories consumed by ShortsPipeline ctor
# =======================================================================


def make_default_producer_invoker(
    agent_dir_root: Path,
    circuit_breaker=None,
) -> ClaudeAgentProducerInvoker:
    """Factory: construct the Claude CLI-backed producer invoker."""
    return ClaudeAgentProducerInvoker(
        agent_dir_root, circuit_breaker=circuit_breaker
    )


def make_default_supervisor_invoker(
    agent_dir: Path,
    circuit_breaker=None,
) -> ClaudeAgentSupervisorInvoker:
    """Factory: construct the Claude CLI-backed supervisor invoker."""
    return ClaudeAgentSupervisorInvoker(
        agent_dir, circuit_breaker=circuit_breaker
    )


def make_default_asset_sourcer(
    nanobanana_adapter,
    character_registry,
) -> Callable[[str], Path]:
    """Return a ``(prompt: str) -> Path`` callable.

    Phase 9.1 uses the simplest possible resolution: prompt passthrough
    to :meth:`NanoBananaAdapter.generate_scene`. Phase 10 adds character
    name extraction and anchor composition via ``character_registry``.
    The registry parameter is accepted now for signature stability so
    Phase 10 can wire character resolution without a breaking change.
    """
    # character_registry reserved for Phase 10 character-name resolution.
    _ = character_registry

    def _source(prompt: str) -> Path:
        return nanobanana_adapter.generate_scene(prompt)

    return _source


# ============================================================================
# Phase 12 AGENT-STD-03: Supervisor producer_output compression (D-A4-01~04)
# ============================================================================
# Context: Phase 11 live smoke 2차 attempt saw GATE 2 supervisor CLI return
# rc=1 with "프롬프트가 너무 깁니다" (prompt too long) when the Producer output
# accumulated large decisions[]/evidence[] arrays plus verbose semantic_feedback
# + raw_response prose. Sending the raw dict to Claude CLI body exceeded the
# context budget. D-A4-04 mandates summary-only compression at the Supervisor
# invoker entry point — the full producer_output is still preserved upstream
# (rubric aggregation, downstream fan-out, logging) because this function is
# invoked ONLY on the Supervisor CLI prompt path.

_COMPRESS_CHAR_BUDGET = 2000  # D-A4-01 default — decisions/evidence char budget


def _compress_producer_output(output: dict) -> dict:
    """Compress producer_output to summary-only form for Supervisor CLI prompt.

    D-A4-01 contract:
      - Preserve: ``gate``, ``verdict``, ``error_codes[]`` (전수 — never truncated)
      - Truncate: ``decisions[]`` OR ``evidence[]`` — severity_desc → score_asc
        sorted when severity is present, then collected front-to-back until the
        per-entry JSON byte budget ``_COMPRESS_CHAR_BUDGET`` is exhausted.
        If any entries remain uncollected, add ``_truncated`` meta string.
      - Drop: verbose prose (``raw_response``, full ``semantic_feedback``)
      - Keep: a short ``semantic_feedback_prefix`` (first 200 chars) if the
        raw field is a string — preserves a minimal context hint for the
        Supervisor without the full verbose body.

    Pitfall 4 mitigation (RESEARCH §Pitfalls #4): Inspector rubric-schema.json
    uses ``evidence[]`` as the primary key while D-A4-01 wording assumes
    ``decisions[]``. We fall back across both — whichever is a non-empty list
    is chosen as the compression source.

    Args:
        output: Raw producer_output dict from Producer/Inspector invoker.

    Returns:
        Compressed dict with summary-only shape, suitable for the Claude CLI
        ``--print`` body. The original ``output`` argument is not mutated.
    """
    compressed: dict = {
        "gate": output.get("gate"),
        "verdict": output.get("verdict"),
        "error_codes": list(output.get("error_codes", [])),
    }

    # Keep short semantic_feedback prefix (drop full verbose body)
    sf = output.get("semantic_feedback")
    if sf and isinstance(sf, str):
        compressed["semantic_feedback_prefix"] = sf[:200]

    # Pitfall 4: decisions[] OR evidence[] 2-key fallback
    source_key: str | None = None
    source_list: list = []
    for key in ("decisions", "evidence"):
        val = output.get(key, [])
        if isinstance(val, list) and val:
            source_key = key
            source_list = val
            break

    if not source_list:
        return compressed

    # severity_desc → score_asc sort when severity is present
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    has_severity = any(
        isinstance(d, dict) and "severity" in d for d in source_list
    )

    def _sort_key(d: dict) -> tuple[int, float]:
        s_rank = sev_rank.get(d.get("severity", "low"), 3)
        score = d.get("score", 9999)
        score_val = score if isinstance(score, (int, float)) else 9999
        return (s_rank, score_val)

    if has_severity:
        sorted_source = sorted(source_list, key=_sort_key)
    else:
        sorted_source = list(source_list)

    # char budget collection (JSON-serialised byte size per entry)
    kept: list = []
    char_used = 0
    for d in sorted_source:
        entry_size = len(json.dumps(d, ensure_ascii=False))
        if char_used + entry_size > _COMPRESS_CHAR_BUDGET:
            break
        kept.append(d)
        char_used += entry_size

    # Guarantee at least 1 entry (the highest-priority one) even if it
    # exceeds the budget alone — otherwise Supervisor loses all context.
    if not kept and sorted_source:
        kept.append(sorted_source[0])

    assert source_key is not None  # invariant: source_list non-empty ⇒ key set
    compressed[source_key] = kept
    if len(kept) < len(source_list):
        compressed["_truncated"] = (
            f"{len(source_list) - len(kept)} more {source_key} entries truncated "
            f"(char budget {_COMPRESS_CHAR_BUDGET} exceeded, severity-sorted)"
        )

    return compressed
