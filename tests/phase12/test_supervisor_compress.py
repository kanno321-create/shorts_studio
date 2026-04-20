"""AGENT-STD-03 — ``_compress_producer_output()`` + SupervisorInvoker replay.

Plan 12-07 pytest coverage of the Supervisor prompt-compression path that
closes Phase 11 smoke 2차 attempt "프롬프트가 너무 깁니다" (rc=1) gap.

Tests
-----
1. test_compression_ratio_over_40pct — raw → compressed byte reduction
2. test_critical_decisions_preserved — severity_desc ordering preserves critical first
3. test_error_codes_always_preserved — error_codes[] never truncated (전수)
4. test_raw_response_dropped — verbose raw_response is dropped from compressed
5. test_phase11_smoke_replay_under_cli_limit — end-to-end via MockClaudeCLI,
   compressed user_prompt length under Claude CLI context limit approximation

Issue #3 invariant (verified 2026-04-21):
``ClaudeAgentSupervisorInvoker.__init__`` at invokers.py L383-393 accepts
``cli_runner: Callable | None = None`` kwarg — the test seam already exists.
Test 5 relies on this; a TypeError there would indicate Plan 07 Task 2 broke
the signature (Issue #3 invariant guard).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).parent))  # mocks/ module resolution

from scripts.orchestrator.invokers import _compress_producer_output  # noqa: E402
from mocks.mock_claude_cli import MockClaudeCLI  # noqa: E402


@pytest.fixture
def oversized_fixture() -> dict:
    """Load Phase 11 smoke 2차 replay fixture (8~15 KB)."""
    p = (
        REPO_ROOT
        / "tests"
        / "phase12"
        / "fixtures"
        / "producer_output_gate2_oversized.json"
    )
    return json.loads(p.read_text(encoding="utf-8"))


def test_compression_ratio_over_40pct(oversized_fixture):
    """Compressed byte size < 60% of raw (압축률 > 40%)."""
    raw_json = json.dumps(oversized_fixture, ensure_ascii=False)
    compressed = _compress_producer_output(oversized_fixture)
    compressed_json = json.dumps(compressed, ensure_ascii=False)
    ratio = len(compressed_json) / len(raw_json)
    assert ratio < 0.60, (
        f"compression ratio = {ratio:.2%} "
        f"(compressed {len(compressed_json)} / raw {len(raw_json)} bytes) — "
        f"expected <60% per D-A4-01 char budget {2000}"
    )


def test_critical_decisions_preserved(oversized_fixture):
    """``severity=critical`` decisions land at the front after severity_desc sort."""
    has_critical_in_raw = any(
        d.get("severity") == "critical"
        for d in oversized_fixture.get("decisions", [])
    )
    assert has_critical_in_raw, "fixture missing critical severity — 합성 스펙 위반"

    compressed = _compress_producer_output(oversized_fixture)
    kept = compressed.get("decisions") or compressed.get("evidence") or []
    assert len(kept) > 0, "no decisions kept after compression"

    first_severity = kept[0].get("severity")
    assert first_severity == "critical", (
        f"critical not first after severity_desc sort: got {first_severity!r}, "
        f"all kept severities: {[d.get('severity') for d in kept]}"
    )


def test_error_codes_always_preserved(oversized_fixture):
    """``error_codes[]`` is copied verbatim — 전수 보존, never truncated."""
    compressed = _compress_producer_output(oversized_fixture)
    assert compressed["error_codes"] == oversized_fixture["error_codes"]


def test_raw_response_dropped(oversized_fixture):
    """Verbose ``raw_response`` is dropped from the compressed payload."""
    assert "raw_response" in oversized_fixture, (
        "fixture precondition: raw_response must be present to test drop"
    )
    compressed = _compress_producer_output(oversized_fixture)
    assert "raw_response" not in compressed, (
        f"raw_response leaked into compressed: keys={list(compressed.keys())}"
    )


def test_phase11_smoke_replay_under_cli_limit(oversized_fixture):
    """MockClaudeCLI round-trip: compressed ``user_prompt`` below CLI context limit.

    Issue #3 invariant guard (2026-04-21): ``ClaudeAgentSupervisorInvoker.__init__``
    at invokers.py L383-393 already accepts ``cli_runner: Callable | None = None``.
    Constructing with ``cli_runner=mock`` must not raise TypeError — if it does,
    Plan 07 Task 2 regressed the signature.
    """
    from scripts.orchestrator.invokers import ClaudeAgentSupervisorInvoker

    # supervisor AGENT.md는 .claude/agents/supervisor/shorts-supervisor/ 경로.
    agent_dir = REPO_ROOT / ".claude" / "agents" / "supervisor" / "shorts-supervisor"
    if not agent_dir.exists():
        # Fallback — use any inspector dir (AGENT.md body content is not
        # asserted; we only need load_agent_system_prompt to succeed).
        agent_dir = (
            REPO_ROOT
            / ".claude"
            / "agents"
            / "inspectors"
            / "structural"
            / "ins-schema-integrity"
        )
    assert agent_dir.exists(), f"no agent dir available for test: {agent_dir}"

    mock = MockClaudeCLI()
    # Supervisor JSON schema requires {verdict: PASS|FAIL|RETRY}
    mock.seed({"verdict": "RETRY"})

    # Issue #3: cli_runner kwarg must exist here.
    invoker = ClaudeAgentSupervisorInvoker(
        agent_dir=agent_dir,
        circuit_breaker=None,
        cli_runner=mock,
    )

    class FakeGate:
        name = "SCRIPT"

    verdict = invoker(FakeGate(), oversized_fixture)

    assert mock.last_user_prompt is not None, "mock.last_user_prompt not captured"
    payload_size = len(mock.last_user_prompt)

    # Claude CLI context limit approximation (body after --append-system-prompt).
    # Empirical 2026-04-21: raw fixture ~14 KB + system prompt triggered
    # "프롬프트가 너무 깁니다" at rc=1. 10_000 chars is a conservative ceiling
    # that the compressed path must stay under.
    CLI_LIMIT = 10_000
    assert payload_size < CLI_LIMIT, (
        f"compressed user_prompt = {payload_size} chars > CLI limit {CLI_LIMIT}. "
        f"Phase 11 smoke 2차 '프롬프트가 너무 깁니다' 재발 위험"
    )
    assert verdict is not None, "verdict parse failed — MockClaudeCLI seed schema mismatch"
