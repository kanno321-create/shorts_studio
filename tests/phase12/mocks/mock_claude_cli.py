"""MockClaudeCLI — Phase 7 MockKling 패턴 복제. Plan 07 supervisor compression 테스트 seam.

실제 `_invoke_claude_cli` signature (scripts/orchestrator/invokers.py L213-220):
    (system_prompt, user_prompt, json_schema, cli_path,
     timeout_s=DEFAULT_TIMEOUT_S, agent_label="claude-cli")

`ClaudeAgentSupervisorInvoker._call` (L406-412) 호출 시 4개 kwargs 만 전달 —
`timeout_s` / `agent_label` 은 default 사용.
MockClaudeCLI 는 `*args, **kwargs` 로 전면 수용하여 real signature 변동 시 TypeError 회피.
"""

from __future__ import annotations

import json
from typing import Any


class MockClaudeCLI:
    """Callable replacement for ``_invoke_claude_cli``.

    Usage in tests::

        mock = MockClaudeCLI()
        mock.seed({"verdict": "PASS"})
        invoker = ClaudeAgentSupervisorInvoker(..., cli_runner=mock)
        verdict = invoker(GateName.SCRIPT, producer_output)
        assert mock.last_user_prompt is not None
    """

    def __init__(self) -> None:
        self._seeded: str = json.dumps({"verdict": "PASS"})
        self.last_user_prompt: str | None = None
        self.last_system_prompt: str | None = None
        self.last_kwargs: dict | None = None
        self.call_count: int = 0

    def seed(self, response: Any) -> None:
        """Prepare the next return value — accepts str or JSON-serialisable object."""
        self._seeded = response if isinstance(response, str) else json.dumps(response)

    def __call__(self, *args: Any, **kwargs: Any) -> str:
        """Defensive signature — accepts both positional and keyword form.

        Caller (`ClaudeAgentSupervisorInvoker._call`) uses kwargs::

            self._cli_runner(system_prompt=..., user_prompt=...,
                             json_schema=..., cli_path=...)

        But future callers may use positional. Extract key fields from either.
        """
        self.last_kwargs = dict(kwargs)
        self.last_system_prompt = (
            kwargs.get("system_prompt") if "system_prompt" in kwargs
            else (args[0] if len(args) >= 1 else None)
        )
        self.last_user_prompt = (
            kwargs.get("user_prompt") if "user_prompt" in kwargs
            else (args[1] if len(args) >= 2 else None)
        )
        self.call_count += 1
        return self._seeded
