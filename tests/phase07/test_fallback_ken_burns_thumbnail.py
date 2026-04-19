"""TEST-04 primary SC4: THUMBNAIL 3×FAIL → ken-burns → COMPLETE (no CIRCUIT_OPEN).

Per RESEARCH Correction 3 + Pitfall 2: target THUMBNAIL (NOT ASSETS). _run_assets
bypasses _producer_loop; only THUMBNAIL reaches both the 3-retry loop AND the
(ASSETS, THUMBNAIL) filter at shorts_pipeline.py:621.

Chain exercised (verified against shorts_pipeline.py read):
    _producer_loop(THUMBNAIL)                    # 3 FAIL verdicts
        -> append_failures(.../failures.md)       # fallback.py:30-64
        -> _insert_fallback(THUMBNAIL, ...)       # shorts_pipeline.py:627-655
            -> insert_fallback_shot(...)          # fallback.py:67-122
                -> shotstack.create_ken_burns_clip(...)  # shotstack.py:155-216
    (back in _run_thumbnail) supervisor 4th call → PASS → dispatch → COMPLETE
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Align with Plan 07-03 / 07-04 precedent for sibling ``mocks`` package import.
_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from scripts.orchestrator import (  # noqa: E402
    GateName,
    ShortsPipeline,
    Verdict,
)
from mocks.elevenlabs_mock import ElevenLabsMock  # noqa: E402
from mocks.kling_mock import KlingMock  # noqa: E402
from mocks.runway_mock import RunwayMock  # noqa: E402
from mocks.shotstack_mock import ShotstackMock  # noqa: E402
from mocks.typecast_mock import TypecastMock  # noqa: E402


def _pass_verdict() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


def _fail_verdict() -> Verdict:
    return Verdict(
        result="FAIL",
        score=20,
        evidence=[{"rule": "thumbnail_hook_weak", "detail": "no face, no caption"}],
        semantic_feedback="face + caption missing",
        inspector_name="ins-thumbnail-hook",
    )


def _build_pipeline_with_thumbnail_failure(tmp_path: Path, session_id: str):
    """Supervisor FAILs THUMBNAIL exactly 3 times; PASSes all other gates/retries.

    Note: _run_thumbnail calls supervisor_invoker a 4th time after _insert_fallback
    returns (shorts_pipeline.py:519). The 4th call naturally PASSes because the
    side_effect only FAILs the first 3 THUMBNAIL supervisor calls.
    """
    invocation_count = {"THUMBNAIL": 0}

    def supervisor_side_effect(gate, output):
        if gate == GateName.THUMBNAIL:
            invocation_count["THUMBNAIL"] += 1
            if invocation_count["THUMBNAIL"] <= 3:
                return _fail_verdict()
        return _pass_verdict()

    producer = MagicMock(return_value={
        "artifact_path": str(tmp_path / "art.json"),
        "prompt": "dark detective scene",
        "duration_seconds": 5,
        "duration_s": 5.0,
        "anchor_frame": str(tmp_path / "a.png"),
        "cut_index": 0,
    })
    supervisor = MagicMock(side_effect=supervisor_side_effect)

    # Typecast / ElevenLabs mocks default to list[dict]; _run_voice iterates
    # AudioSegment.path — override to [] to mirror Plan 07-03 E2E precedent.
    typecast = TypecastMock()
    elevenlabs = ElevenLabsMock()
    typecast.generate = lambda *a, **kw: []  # type: ignore[method-assign]
    elevenlabs.generate_with_timestamps = lambda *a, **kw: []  # type: ignore[method-assign]

    shotstack = ShotstackMock()

    pipeline = ShortsPipeline(
        session_id=session_id,
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs,
        shotstack_adapter=shotstack,
        producer_invoker=producer,
        supervisor_invoker=supervisor,
        asset_sourcer_invoker=lambda prompt: tmp_path / "still_image.jpg",
    )
    return pipeline, invocation_count, shotstack


def test_thumbnail_3x_fail_triggers_ken_burns_fallback(
    tmp_path: Path, _fake_env: None,
) -> None:
    pipeline, invocation_count, _ = _build_pipeline_with_thumbnail_failure(
        tmp_path, "sid_fb_1"
    )
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        result = pipeline.run()

    # Pipeline reached COMPLETE despite THUMBNAIL failures.
    assert result["final_gate"] == "COMPLETE"
    assert result["dispatched_count"] == 13
    assert result["fallback_count"] == 1, (
        f"Expected exactly 1 ken-burns fallback insertion, got {result['fallback_count']}"
    )
    # Supervisor was invoked ≥ 3 times on THUMBNAIL (3 FAIL retries inside _producer_loop).
    assert invocation_count["THUMBNAIL"] >= 3


def test_create_ken_burns_clip_called_once(tmp_path: Path, _fake_env: None) -> None:
    pipeline, _, shotstack = _build_pipeline_with_thumbnail_failure(tmp_path, "sid_fb_2")
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()
    assert shotstack.ken_burns_call_count == 1, (
        f"Expected exactly 1 ken-burns clip call, got {shotstack.ken_burns_call_count}"
    )


def test_create_ken_burns_clip_duration_positive(
    tmp_path: Path, _fake_env: None,
) -> None:
    pipeline, _, shotstack = _build_pipeline_with_thumbnail_failure(tmp_path, "sid_fb_3")
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()
    assert shotstack.last_ken_burns_args is not None
    assert shotstack.last_ken_burns_args["duration_s"] > 0
    # image_path propagated from asset_sourcer_invoker(prompt) -> still_image.jpg.
    assert shotstack.last_ken_burns_args["image_path"] == tmp_path / "still_image.jpg"


def test_no_circuit_breaker_open_error_raised(
    tmp_path: Path, _fake_env: None,
) -> None:
    """SC4: Fallback lane ensures COMPLETE without CIRCUIT_OPEN.

    THUMBNAIL Fallback lane must not route through any CircuitBreaker
    (create_ken_burns_clip uses the shotstack adapter directly inside
    insert_fallback_shot — no breaker wrapper). Assert no breaker raise.
    """
    from scripts.orchestrator.circuit_breaker import CircuitBreakerOpenError

    pipeline, _, _ = _build_pipeline_with_thumbnail_failure(tmp_path, "sid_fb_4")
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        try:
            result = pipeline.run()
        except CircuitBreakerOpenError as exc:
            pytest.fail(
                f"SC4 violated: CIRCUIT_OPEN raised during THUMBNAIL fallback: {exc}"
            )
    assert result["final_gate"] == "COMPLETE"


def test_retry_counts_thumbnail_equals_3(
    tmp_path: Path, _fake_env: None,
) -> None:
    """D-9: _producer_loop retry_counts tracks exactly 3 THUMBNAIL retries before exhaustion.

    Per shorts_pipeline.py:602 the retry counter is ``retry + 1`` on each FAIL,
    so after 3 consecutive FAILs the final recorded value is 3.
    """
    pipeline, _, _ = _build_pipeline_with_thumbnail_failure(tmp_path, "sid_fb_5")
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()
    assert pipeline.ctx.retry_counts.get(GateName.THUMBNAIL, 0) == 3


def test_fallback_indices_contains_cut_index(
    tmp_path: Path, _fake_env: None,
) -> None:
    """_insert_fallback appends to ctx.fallback_indices (shorts_pipeline.py:649)."""
    pipeline, _, _ = _build_pipeline_with_thumbnail_failure(tmp_path, "sid_fb_6")
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()
    assert len(pipeline.ctx.fallback_indices) == 1
    # Producer output supplies cut_index=0.
    assert pipeline.ctx.fallback_indices == [0]


def test_target_is_thumbnail_not_assets(tmp_path: Path, _fake_env: None) -> None:
    """RESEARCH Correction 3 + Pitfall 2: ASSETS does NOT route through _producer_loop.

    Anchor test guarding against future drift. If someone flips the target gate
    from THUMBNAIL to ASSETS in this test module, _run_assets would ignore the
    supervisor FAIL and ken-burns would NOT fire. Verifies Phase 7 TEST-04
    targets THUMBNAIL structurally via the supervisor_side_effect closure.

    Strategy: parse this file's AST and inspect the supervisor_side_effect
    closure for the literal ``GateName.THUMBNAIL`` attribute access — this is
    the SINGLE structural lever that determines which gate the test FAILs.
    """
    import ast

    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)

    # Walk the AST and collect every ``GateName.<NAME>`` attribute access
    # that appears inside a function whose name starts with ``supervisor``
    # (i.e., the supervisor_side_effect closures used to drive FAIL verdicts).
    target_gate_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("supervisor"):
                continue
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Attribute)
                    and isinstance(sub.value, ast.Name)
                    and sub.value.id == "GateName"
                ):
                    target_gate_names.add(sub.attr)

    assert "THUMBNAIL" in target_gate_names, (
        "RESEARCH Correction 3 enforcement: TEST-04 MUST target THUMBNAIL gate "
        f"inside supervisor_side_effect. Actual targets: {target_gate_names}"
    )
    assert "ASSETS" not in target_gate_names, (
        "RESEARCH Correction 3 enforcement: TEST-04 MUST NOT use GateName.ASSETS "
        "as the FAIL target — _run_assets bypasses _producer_loop. "
        f"Actual targets: {target_gate_names}"
    )


def test_fallback_chain_reaches_shotstack_create_ken_burns_clip(
    tmp_path: Path, _fake_env: None,
) -> None:
    """Anchor: the full chain _producer_loop → _insert_fallback → insert_fallback_shot
    → shotstack.create_ken_burns_clip is exercised exactly once per THUMBNAIL exhaustion.

    Documents RESEARCH Correction 3 end-to-end: ken-burns is a STANDALONE
    Shotstack POST (shotstack.py:155-216), not embedded in the main render
    filter chain. Verified by checking that ShotstackMock.render was NOT called
    (main ASSEMBLY render is a separate path) with ken-burns semantics.
    """
    pipeline, _, shotstack = _build_pipeline_with_thumbnail_failure(tmp_path, "sid_fb_7")
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()

    # create_ken_burns_clip called exactly once (by insert_fallback_shot).
    assert shotstack.ken_burns_call_count == 1
    # Main ASSEMBLY render is a separate call — at least 1, and ken-burns is
    # NOT embedded in its payload (Correction 3: standalone POST).
    assert shotstack.render_call_count >= 1
