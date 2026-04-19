"""TEST-01 SC1: E2E mock pipeline TREND → COMPLETE in one pass.

Structural peer of ``tests/phase05/test_pipeline_e2e_mock.py`` but uses
Phase 7 Wave-1 mock adapters (KlingMock / RunwayMock / TypecastMock /
ElevenLabsMock / ShotstackMock) instead of bare MagicMock so the
Wave 1 mock contract is proven compatible with the Phase 5
:class:`ShortsPipeline` expectations. Any regression here diagnoses
whether the Wave 1 mocks match the real adapter duck-types expected by
the pipeline.

Assertions (CONTEXT D-1, D-6, D-15, D-22 + Research Correction 1):
  * ``dispatched_count == 13`` (13 operational gates, **not** 17)
  * ``final_gate == "COMPLETE"``
  * ``fallback_count == 0`` (happy path — no fallback insertion)
  * 14 checkpoint files on disk (13 operational + 1 COMPLETE bookend)
  * ``failures.md`` never appended (happy path never touches
    failures reservoir)
  * Real-network call count == 0 (mock adapters + fake API keys;
    D-1 satisfied structurally since mocks have no HTTP client at all)
  * Korean session id round-trips cp949/UTF-8 on Windows (D-22)
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make sibling ``mocks`` package importable via ``from mocks.kling_mock
# import KlingMock`` — mirrors Plan 07-02 precedent (Phase 5/6 tests
# intentionally live without a ``tests/__init__.py`` so we insert the
# phase07 directory rather than restructuring the wider tests/ package).
_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from scripts.orchestrator import ShortsPipeline, Verdict  # noqa: E402
from mocks.elevenlabs_mock import ElevenLabsMock  # noqa: E402
from mocks.kling_mock import KlingMock  # noqa: E402
from mocks.runway_mock import RunwayMock  # noqa: E402
from mocks.shotstack_mock import ShotstackMock  # noqa: E402
from mocks.typecast_mock import TypecastMock  # noqa: E402


def _pass_verdict() -> Verdict:
    """Canonical PASS Verdict from shorts-supervisor."""
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


def _producer_output(tmp_path: Path) -> dict:
    """Minimal producer artifact shape expected by ShortsPipeline (Phase 5
    precedent: artifact_path / prompt / duration_seconds / anchor_frame)."""
    return {
        "artifact_path": str(tmp_path / "artifact.json"),
        "prompt": "dark detective scene",
        "duration_seconds": 5,
        "anchor_frame": str(tmp_path / "a.png"),
    }


def _build_pipeline(tmp_path: Path, session_id: str) -> ShortsPipeline:
    """Construct ShortsPipeline wired with all 5 Phase 7 Wave-1 mocks.

    Note on TTS mocks: Phase 5 ``ShortsPipeline._run_voice`` (lines 411-433)
    iterates ``ctx.audio_segments`` expecting ``AudioSegment`` dataclass
    instances with a ``.path`` attribute. The Wave-1 ``TypecastMock`` /
    ``ElevenLabsMock`` return ``list[dict]`` for unit-level contract tests
    (D-18/D-19). For the E2E walk we monkey-patch the mock methods to
    return ``[]`` — mirroring the Phase 5 precedent
    (``tests/phase05/test_pipeline_e2e_mock.py:70-72``). This keeps the
    Wave-1 mocks honest to their unit contracts while letting the E2E
    exercise the full 13-gate walk without hand-rolling AudioSegment
    fixtures (Don't Hand-Roll, D-2).
    """
    producer = MagicMock(return_value=_producer_output(tmp_path))
    supervisor = MagicMock(return_value=_pass_verdict())

    typecast = TypecastMock()
    elevenlabs = ElevenLabsMock()
    # Align with Phase 5 precedent: pipeline's _run_voice expects
    # AudioSegment-shaped objects; returning [] bypasses the .path
    # attribute access while still exercising the gate dispatch.
    typecast.generate = lambda *a, **kw: []  # type: ignore[method-assign]
    elevenlabs.generate_with_timestamps = lambda *a, **kw: []  # type: ignore[method-assign]

    return ShortsPipeline(
        session_id=session_id,
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs,
        shotstack_adapter=ShotstackMock(),
        producer_invoker=producer,
        supervisor_invoker=supervisor,
        asset_sourcer_invoker=lambda prompt: tmp_path / "stock.png",
    )


def test_full_pipeline_runs_13_gates_and_completes(
    tmp_path: Path,
    _fake_env: None,
    tmp_session_id: str,
) -> None:
    """TEST-01 primary assertion: TREND → COMPLETE in one mock pass.

    Proves Research Correction 1 (13 operational dispatches, NOT 17)
    by asserting the pipeline summary explicitly.
    """
    pipeline = _build_pipeline(tmp_path, tmp_session_id)

    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        result = pipeline.run()

    assert result["session_id"] == tmp_session_id
    assert result["final_gate"] == "COMPLETE", (
        f"Expected COMPLETE, got {result['final_gate']}; result={result}"
    )
    assert result["dispatched_count"] == 13, (
        "Expected 13 operational gates dispatched (Research Correction 1), "
        f"got {result['dispatched_count']}"
    )
    assert result["fallback_count"] == 0, (
        "Happy path must NOT insert any fallback shots"
    )


def test_checkpoint_14_files_exist(
    tmp_path: Path,
    _fake_env: None,
    tmp_session_id: str,
) -> None:
    """D-6: 13 operational + 1 COMPLETE = 14 ``gate_NN.json`` files."""
    pipeline = _build_pipeline(tmp_path, tmp_session_id)

    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()

    session_dir = tmp_path / "state" / tmp_session_id
    assert session_dir.exists(), f"state dir missing: {session_dir}"
    gate_files = sorted(session_dir.glob("gate_*.json"))
    assert len(gate_files) == 14, (
        "Expected 14 checkpoint files (13 operational + COMPLETE bookend), "
        f"got {len(gate_files)}: {[f.name for f in gate_files]}"
    )


def test_failures_md_empty_on_happy_path(
    tmp_path: Path,
    _fake_env: None,
    tmp_session_id: str,
) -> None:
    """Happy path never appends to FAILURES.md (D-9 append-only reservoir)."""
    pipeline = _build_pipeline(tmp_path, tmp_session_id)

    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()

    failures_path = tmp_path / "failures.md"
    if failures_path.exists():
        text = failures_path.read_text(encoding="utf-8")
        assert "FAIL after regeneration exhausted" not in text, (
            f"Happy path accidentally appended to failures.md:\n{text}"
        )


def test_checkpoint_files_round_trip_json(
    tmp_path: Path,
    _fake_env: None,
    tmp_session_id: str,
) -> None:
    """D-6: every ``gate_NN.json`` round-trips as JSON with required keys."""
    import json

    pipeline = _build_pipeline(tmp_path, tmp_session_id)

    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()

    session_dir = tmp_path / "state" / tmp_session_id
    required = {
        "_schema",
        "session_id",
        "gate",
        "gate_index",
        "timestamp",
        "verdict",
        "artifacts",
    }
    for cp_file in sorted(session_dir.glob("gate_*.json")):
        data = json.loads(cp_file.read_text(encoding="utf-8"))
        missing = required - set(data.keys())
        assert not missing, f"{cp_file.name} missing keys: {missing}"


def test_no_real_network_via_fake_env(
    tmp_path: Path,
    _fake_env: None,
    tmp_session_id: str,
) -> None:
    """D-1: Real network call count = 0.

    Proven structurally: the 5 Wave-1 mock classes have no HTTP clients,
    so no socket can be opened. We additionally assert the 5 API key
    env-vars are set to the literal "fake" sentinel so adapter
    constructors do not raise but also never transmit a real key.
    """
    import os

    for key in (
        "KLING_API_KEY",
        "RUNWAY_API_KEY",
        "TYPECAST_API_KEY",
        "ELEVENLABS_API_KEY",
        "SHOTSTACK_API_KEY",
    ):
        assert os.environ.get(key) == "fake"

    pipeline = _build_pipeline(tmp_path, tmp_session_id)
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        result = pipeline.run()
    assert result["final_gate"] == "COMPLETE"

    # Mocks are pure-Python objects with no HTTP client attributes.
    # ShortsPipeline stores adapters as ``self.kling`` / ``self.shotstack``
    # (shorts_pipeline.py:204, 216) — not ``_adapter`` suffix.
    assert not hasattr(pipeline.kling, "_session")
    assert not hasattr(pipeline.shotstack, "_session")


def test_korean_session_id_cp949_roundtrip(
    tmp_path: Path,
    _fake_env: None,
) -> None:
    """D-22: non-ASCII session id survives atomic write on Windows cp949."""
    sid = "tst_phase07_한국어_e2e"
    pipeline = _build_pipeline(tmp_path, sid)

    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        result = pipeline.run()

    assert result["session_id"] == sid
    # State directory must exist under the Korean name (file-system
    # cp949/UTF-8 round-trip safety).
    assert (tmp_path / "state" / sid).exists(), (
        f"Korean session dir missing: {tmp_path / 'state' / sid}"
    )
