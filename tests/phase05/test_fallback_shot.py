"""ORCH-12 regeneration loop + Fallback tests (Plan 07).

Scenarios:

1. ``test_regen_3_then_fallback_for_assets`` — ASSETS gate: 3 failing
   Supervisor verdicts trigger ken-burns Fallback insertion; FAILURES.md
   gets an append entry; ``fallback_indices`` grows by 1.
2. ``test_regen_3_raises_for_non_fallback_gate`` — SCRIPT gate: 3 FAILs
   raise :class:`RegenerationExhausted` (no fallback lane).
3. ``test_regen_pass_first_try_no_failures`` — a PASS verdict on the
   first attempt short-circuits the loop; FAILURES.md is not created.
4. ``test_append_failures_is_append_only`` — direct call to
   :func:`append_failures`: existing file content survives the append.
5. ``test_dedupe_fallback_key_stable`` — key generation is deterministic
   per (session, gate, cut).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.orchestrator import (
    GateName,
    RegenerationExhausted,
    ShortsPipeline,
    Verdict,
)
from scripts.orchestrator.fallback import (
    append_failures,
    dedupe_fallback_key,
)


def _fail_verdict() -> Verdict:
    return Verdict(
        result="FAIL",
        score=30,
        evidence=[{"rule": "X", "detail": "bad"}],
        semantic_feedback="bad",
        inspector_name="shorts-supervisor",
    )


def _pass_verdict() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


@pytest.fixture
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        monkeypatch.setenv(var, "fake")


def _pipeline_always_fail(
    tmp_path: Path, shotstack: MagicMock | None = None
) -> ShortsPipeline:
    """Build a pipeline whose Supervisor always returns FAIL."""

    ss = shotstack or MagicMock()
    ss.create_ken_burns_clip.return_value = tmp_path / "kenburns.mp4"
    return ShortsPipeline(
        session_id="fb_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=MagicMock(),
        runway_adapter=MagicMock(),
        typecast_adapter=MagicMock(),
        elevenlabs_adapter=MagicMock(),
        shotstack_adapter=ss,
        producer_invoker=MagicMock(
            return_value={"prompt": "failing scene", "duration_s": 5.0}
        ),
        supervisor_invoker=lambda g, o: _fail_verdict(),
        asset_sourcer_invoker=lambda prompt: tmp_path / "stock.png",
    )


def test_regen_3_then_fallback_for_assets(
    tmp_path: Path, _fake_env: None
) -> None:
    """ASSETS regeneration exhaustion -> ken-burns Fallback + FAILURES append."""

    shotstack = MagicMock()
    kenburns_path = tmp_path / "kenburns.mp4"
    shotstack.create_ken_burns_clip.return_value = kenburns_path

    pipeline = _pipeline_always_fail(tmp_path, shotstack=shotstack)
    result = pipeline._producer_loop(
        GateName.ASSETS,
        lambda: {"prompt": "p", "duration_s": 5.0, "cut_index": 0},
    )

    assert result["is_fallback"] is True
    assert result["path"] == kenburns_path
    failures_content = (tmp_path / "failures.md").read_text(encoding="utf-8")
    assert "ASSETS" in failures_content
    assert "FAIL after regeneration exhausted" in failures_content
    # fallback_indices tracks the cut index per RESEARCH line 862
    assert 0 in pipeline.ctx.fallback_indices


def test_regen_3_raises_for_non_fallback_gate(
    tmp_path: Path, _fake_env: None
) -> None:
    """SCRIPT gate: regeneration exhaustion raises RegenerationExhausted."""

    pipeline = ShortsPipeline(
        session_id="raise_test",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=MagicMock(),
        runway_adapter=MagicMock(),
        typecast_adapter=MagicMock(),
        elevenlabs_adapter=MagicMock(),
        shotstack_adapter=MagicMock(),
        producer_invoker=MagicMock(return_value={}),
        supervisor_invoker=lambda g, o: _fail_verdict(),
        asset_sourcer_invoker=lambda p: Path("/tmp/x"),
    )
    with pytest.raises(RegenerationExhausted):
        pipeline._producer_loop(GateName.SCRIPT, lambda: {})


def test_regen_pass_first_try_no_failures(
    tmp_path: Path, _fake_env: None
) -> None:
    """PASS on first attempt short-circuits loop; no FAILURES.md created."""

    pipeline = ShortsPipeline(
        session_id="ok",
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=MagicMock(),
        runway_adapter=MagicMock(),
        typecast_adapter=MagicMock(),
        elevenlabs_adapter=MagicMock(),
        shotstack_adapter=MagicMock(),
        producer_invoker=MagicMock(return_value={"good": True}),
        supervisor_invoker=lambda g, o: _pass_verdict(),
        asset_sourcer_invoker=lambda p: Path("/tmp/x"),
    )
    result = pipeline._producer_loop(GateName.SCRIPT, lambda: {"good": True})
    assert result == {"good": True}
    failures_file = tmp_path / "failures.md"
    # file may not exist, or if created by a sibling run must not reference SCRIPT FAIL
    if failures_file.exists():
        assert "FAIL" not in failures_file.read_text(encoding="utf-8")


def test_append_failures_is_append_only(tmp_path: Path) -> None:
    """FAIL-01 contract: append_failures NEVER truncates existing content."""

    path = tmp_path / "failures.md"
    path.write_text("EXISTING CONTENT\n", encoding="utf-8")
    append_failures(path, "s1", "TREND", [], "")
    content = path.read_text(encoding="utf-8")
    assert "EXISTING CONTENT" in content
    assert "TREND" in content


def test_append_failures_truncates_evidence_to_first_3(tmp_path: Path) -> None:
    """Appended entry summarises only the first 3 evidence items."""

    path = tmp_path / "failures.md"
    evidence = [
        {"rule": "R1", "detail": "one"},
        {"rule": "R2", "detail": "two"},
        {"rule": "R3", "detail": "three"},
        {"rule": "R4", "detail": "FOUR-SHOULD-NOT-APPEAR"},
    ]
    append_failures(path, "sX", "NICHE", evidence, "narrative")
    content = path.read_text(encoding="utf-8")
    assert "R1" in content
    assert "R2" in content
    assert "R3" in content
    assert "FOUR-SHOULD-NOT-APPEAR" not in content


def test_dedupe_fallback_key_stable() -> None:
    """dedupe_fallback_key format is deterministic."""

    assert dedupe_fallback_key("s1", "ASSETS", 0) == "s1:ASSETS:0"
    assert dedupe_fallback_key("s2", "THUMBNAIL", 5) == "s2:THUMBNAIL:5"
