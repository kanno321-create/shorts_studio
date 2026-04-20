"""Claude Agent SDK wiring (REQ-091-01, Phase 9.1).

Replaces :meth:`ShortsPipeline._default_producer_invoker` /
``_default_supervisor_invoker`` / ``_default_asset_sourcer``
(NotImplementedError since Phase 5) with real Anthropic SDK-backed
invokers.

Architecture
------------
* Producer (per-gate content generation) → Claude Sonnet 4.6
* Supervisor (Verdict judgment) → Claude Opus 4.6
* Asset sourcer (script → anchor image path) → NanoBananaAdapter

All three invokers honour the existing DI contract. Tests pass
``MagicMock`` invokers unchanged (Phase 7 regression preserved).

Contract
--------
* Producer invoker signature: ``(agent_name, gate, inputs) -> dict``
* Supervisor invoker signature: ``(gate, output: dict) -> Verdict``
  (``Verdict`` is the enum from :mod:`scripts.orchestrator.state`)
* Asset sourcer signature: ``(prompt: str) -> Path``

JSON enforcement (Pitfall 1)
----------------------------
Anthropic's SDK has no native ``response_format=json`` parameter. We
use a triple defence: (a) system prompt terminator instruction in
Korean, (b) assistant prefill ``{`` message, (c) client-side
``json.loads`` with prefill reassembly (``'{' + response.content[...].text``).

Korean-first errors per 나베랄 감마 tone (대표님 전용).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = [
    "PRODUCER_MODEL",
    "SUPERVISOR_MODEL",
    "load_agent_system_prompt",
    "ClaudeAgentProducerInvoker",
    "ClaudeAgentSupervisorInvoker",
    "make_default_producer_invoker",
    "make_default_supervisor_invoker",
    "make_default_asset_sourcer",
]

PRODUCER_MODEL = "claude-sonnet-4-6-20260301"
SUPERVISOR_MODEL = "claude-opus-4-6-20260320"

_JSON_INSTRUCTION = (
    "\n\nCRITICAL: 반드시 단일 valid JSON 객체로만 응답하세요. "
    "markdown code fence, preamble, commentary 전부 금지. "
    "준수 불가 시 {\"error\": \"<사유>\"} 로 응답."
)

_MISSING_KEY_MSG = (
    "ANTHROPIC_API_KEY 미설정 — 대표님 .env 에 추가 후 재시도하세요. "
    "현재 mock 모드에서만 호출 가능합니다 "
    "(tests/phase091/ MagicMock client 주입 경로 사용 중)."
)


def load_agent_system_prompt(agent_dir: Path) -> tuple[str, dict]:
    """Parse ``AGENT.md`` into ``(body, frontmatter)``.

    Strips a YAML frontmatter block bounded by ``---\\n`` markers.
    Returns an empty dict when no frontmatter is present.

    Raises:
        FileNotFoundError: ``AGENT.md`` is missing from ``agent_dir``.
        RuntimeError: PyYAML not importable (should never happen —
            Phase 6 pinned the dependency; raised with Korean guidance).
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


def _build_client(explicit):
    """Return an Anthropic client, raising a Korean ValueError on import
    or auth setup failure.

    ``Anthropic()`` itself does NOT raise on missing API key — it defers
    authentication to the first real call. We therefore only catch the
    (rare) construction failure here; a missing key surfaces when the
    invoker is actually called against the live API.
    """
    if explicit is not None:
        return explicit
    try:
        from anthropic import Anthropic
        return Anthropic(max_retries=0)
    except Exception as err:  # ImportError, runtime errors — Hook 3종 noisy
        raise ValueError(_MISSING_KEY_MSG) from err


def _reassemble_prefill(content_blocks) -> str:
    """Restore the assistant ``{`` prefill to form the complete JSON text.

    Pitfall 1 defence — the Anthropic SDK does NOT echo the assistant
    prefill back in ``response.content``. ``json.loads`` on the raw
    text would fail on the leading ``"key": "value"}`` fragment.
    """
    body = "".join(
        getattr(b, "text", "")
        for b in content_blocks
        if hasattr(b, "text") and getattr(b, "text", None)
    )
    return "{" + body


class ClaudeAgentProducerInvoker:
    """Callable invoker: ``(agent_name, gate, inputs) -> dict``.

    Resolves the per-producer system prompt from
    ``agent_dir_root / <agent_name> / AGENT.md``, injects the JSON
    enforcement suffix, calls Claude Sonnet 4.6 with a ``{`` prefill,
    reassembles the response, and returns the parsed dict.

    Tests inject a ``client`` MagicMock; production passes ``None`` and
    an ``Anthropic()`` instance is built lazily.
    """

    def __init__(
        self,
        agent_dir_root: Path,
        circuit_breaker=None,
        client=None,
    ) -> None:
        self.agent_dir_root = Path(agent_dir_root)
        self.circuit_breaker = circuit_breaker
        self.client = _build_client(client)

    def __call__(self, agent_name: str, gate: str, inputs: dict) -> dict:
        agent_dir = self.agent_dir_root / agent_name
        if not agent_dir.exists():
            raise FileNotFoundError(
                f"Agent 디렉토리 없음: {agent_dir} — "
                f"Phase 4 AGENT.md 확인 (대표님)"
            )
        body, _ = load_agent_system_prompt(agent_dir)
        system_full = body + _JSON_INSTRUCTION
        user_payload = json.dumps(
            {"gate": gate, "inputs": inputs}, ensure_ascii=False
        )

        def _call():
            return self.client.messages.create(
                model=PRODUCER_MODEL,
                max_tokens=4096,
                system=system_full,
                messages=[
                    {"role": "user", "content": user_payload},
                    {"role": "assistant", "content": "{"},
                ],
                temperature=0.3,
            )

        resp = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        text = _reassemble_prefill(resp.content)
        try:
            return json.loads(text)
        except json.JSONDecodeError as err:
            logger.error(
                "[invoker] producer '%s' JSON parse 실패: %s — head=%r",
                agent_name, err, text[:200],
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
        client=None,
    ) -> None:
        self.agent_dir = Path(agent_dir)
        self.circuit_breaker = circuit_breaker
        self.client = _build_client(client)
        self._system, _ = load_agent_system_prompt(self.agent_dir)
        self._system_full = self._system + _JSON_INSTRUCTION

    def __call__(self, gate, output: dict):
        # Lazy import to avoid a cycle: state.py → invokers.py import
        # chain stays acyclic even when the pipeline imports both.
        from .state import Verdict

        gate_name = getattr(gate, "name", str(gate))
        user_payload = json.dumps(
            {"gate": gate_name, "producer_output": output},
            ensure_ascii=False,
        )

        def _call():
            return self.client.messages.create(
                model=SUPERVISOR_MODEL,
                max_tokens=512,
                system=self._system_full,
                messages=[
                    {"role": "user", "content": user_payload},
                    {"role": "assistant", "content": "{"},
                ],
                temperature=0.0,
            )

        resp = (
            self.circuit_breaker.call(_call)
            if self.circuit_breaker is not None
            else _call()
        )
        text = _reassemble_prefill(resp.content)
        parsed = json.loads(text)
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
    """Factory: construct the SDK-backed producer invoker."""
    return ClaudeAgentProducerInvoker(
        agent_dir_root, circuit_breaker=circuit_breaker
    )


def make_default_supervisor_invoker(
    agent_dir: Path,
    circuit_breaker=None,
) -> ClaudeAgentSupervisorInvoker:
    """Factory: construct the SDK-backed supervisor invoker."""
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
