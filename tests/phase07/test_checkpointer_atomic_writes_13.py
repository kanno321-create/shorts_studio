"""D-6: Checkpointer atomic write verification during E2E.

Asserts that one full TREND → COMPLETE walk writes exactly 14 ``gate_NN.json``
files (13 operational + 1 COMPLETE), each via ``os.replace`` (Windows-safe
atomic), with correct schema, ISO-8601 timestamps, round-trip serialization,
no leftover ``.tmp`` residue, and a valid highest-gate-index resume invariant.

Count note: the COMPLETE transition saves its own checkpoint in
``shorts_pipeline.py:674-688`` (gate_index=14). So end-to-end we see 14 files,
NOT 13 — one per operational gate PLUS the final COMPLETE marker.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.orchestrator import AudioSegment, ShortsPipeline, Verdict

# Phase 7 mocks live at tests/phase07/mocks/. See test_mock_kling_adapter.py:12-19.
_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.elevenlabs_mock import ElevenLabsMock  # noqa: E402
from mocks.kling_mock import KlingMock  # noqa: E402
from mocks.runway_mock import RunwayMock  # noqa: E402
from mocks.shotstack_mock import ShotstackMock  # noqa: E402
from mocks.typecast_mock import TypecastMock  # noqa: E402


def _pass() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


def _producer_output(tmp_path: Path) -> dict:
    return {
        "artifact_path": str(tmp_path / "art.json"),
        "prompt": "mock prompt",
        "duration_seconds": 5,
        "anchor_frame": str(tmp_path / "anchor.png"),
        "scenes": [
            {
                "prompt": "scene",
                "duration_seconds": 5,
                "anchor_frame": str(tmp_path / "anchor.png"),
            }
        ],
    }


def _run_pipeline(tmp_path: Path, session_id: str):
    """Run the pipeline end-to-end with all external I/O mocked out."""
    producer = MagicMock(return_value=_producer_output(tmp_path))
    pipeline = ShortsPipeline(
        session_id=session_id,
        state_root=tmp_path / "state",
        failures_path=tmp_path / "failures.md",
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=TypecastMock(),
        elevenlabs_adapter=ElevenLabsMock(),
        shotstack_adapter=ShotstackMock(),
        producer_invoker=producer,
        supervisor_invoker=MagicMock(return_value=_pass()),
        asset_sourcer_invoker=lambda p: tmp_path / "still.png",
    )
    audio_seg = AudioSegment(
        index=0, start=0.0, end=3.0, duration=3.0, path=tmp_path / "mock.wav",
    )
    with patch.object(pipeline.timeline, "align", return_value=[]), \
         patch.object(pipeline.timeline, "insert_transition_shots", return_value=[]), \
         patch.object(pipeline.typecast, "generate", return_value=[audio_seg]):
        result = pipeline.run()
    return pipeline, result


# ---------------------------------------------------------------------------
# File count + filename format
# ---------------------------------------------------------------------------


def test_14_checkpoint_files_written(tmp_path: Path, _fake_env: None):
    """13 operational gates + 1 COMPLETE = 14 ``gate_NN.json`` files on disk."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_count")
    session_dir = tmp_path / "state" / "sid_cp_count"
    files = sorted(session_dir.glob("gate_*.json"))
    assert len(files) == 14, (
        f"Expected 14 checkpoint files (13 operational + COMPLETE), got {len(files)}: "
        f"{[f.name for f in files]}"
    )


def test_checkpoint_filenames_are_zero_padded(tmp_path: Path, _fake_env: None):
    """All files follow ``gate_NN.json`` with a 2-digit zero-padded index."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_names")
    session_dir = tmp_path / "state" / "sid_cp_names"
    pattern = re.compile(r"gate_(\d{2})\.json$")
    files = list(session_dir.glob("gate_*.json"))
    assert files, "session directory contains no gate_*.json files"
    for f in files:
        m = pattern.match(f.name)
        assert m, f"Unexpected filename: {f.name} (must be gate_NN.json zero-padded)"


# ---------------------------------------------------------------------------
# Schema / content integrity
# ---------------------------------------------------------------------------


def test_checkpoint_json_has_required_keys(tmp_path: Path, _fake_env: None):
    """Every checkpoint has the D-5 canonical keys."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_schema")
    session_dir = tmp_path / "state" / "sid_cp_schema"
    required = {
        "_schema",
        "session_id",
        "gate",
        "gate_index",
        "timestamp",
        "verdict",
        "artifacts",
    }
    for f in session_dir.glob("gate_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        missing = required - set(data.keys())
        assert not missing, f"{f.name} missing keys: {missing}"
        assert data["_schema"] == 1, f"{f.name} _schema != 1"
        assert data["session_id"] == "sid_cp_schema"


def test_timestamp_field_is_iso8601(tmp_path: Path, _fake_env: None):
    """ISO-8601 UTC timestamps (gate_guard writes with datetime.now(timezone.utc).isoformat())."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_iso")
    session_dir = tmp_path / "state" / "sid_cp_iso"
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    for f in session_dir.glob("gate_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        assert iso_pattern.match(data["timestamp"]), (
            f"{f.name} timestamp {data['timestamp']!r} is not ISO-8601 prefixed"
        )


# ---------------------------------------------------------------------------
# Atomic write guarantees
# ---------------------------------------------------------------------------


def test_no_tmp_files_left_after_run(tmp_path: Path, _fake_env: None):
    """``os.replace`` is atomic — no ``.tmp`` residue after a clean run."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_tmp")
    session_dir = tmp_path / "state" / "sid_cp_tmp"
    leftover = list(session_dir.glob("*.tmp"))
    assert leftover == [], f"Atomic write residue found: {leftover}"


# ---------------------------------------------------------------------------
# Resume invariant
# ---------------------------------------------------------------------------


def test_highest_gate_index_is_14_complete(tmp_path: Path, _fake_env: None):
    """Resume invariant: ``Checkpointer.resume(session_id)`` returns 14 (COMPLETE)."""
    pipeline, _ = _run_pipeline(tmp_path, "sid_cp_max")
    assert pipeline.checkpointer.resume("sid_cp_max") == 14, (
        "Checkpointer.resume should return the COMPLETE (14) index on a clean finish"
    )


def test_dispatched_gates_reconstructs_all_13_operational(
    tmp_path: Path, _fake_env: None,
):
    """``dispatched_gates(session_id)`` must reconstruct all 13 operational names."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_reconstruct")
    from scripts.orchestrator import Checkpointer
    cp = Checkpointer(tmp_path / "state")
    dispatched = cp.dispatched_gates("sid_cp_reconstruct")
    # 13 operational + COMPLETE (saved by _transition_to_complete) = 14 entries.
    # verify_all_dispatched checks the 13 operational; filesystem also carries COMPLETE.
    operational_names = {
        "TREND", "NICHE", "RESEARCH_NLM", "BLUEPRINT", "SCRIPT", "POLISH",
        "VOICE", "ASSETS", "ASSEMBLY", "THUMBNAIL", "METADATA", "UPLOAD", "MONITOR",
    }
    assert operational_names.issubset(dispatched), (
        f"Missing from reconstructed set: {operational_names - dispatched}"
    )
    assert "COMPLETE" in dispatched, "COMPLETE checkpoint not persisted"


def test_round_trip_deserialization_is_stable(
    tmp_path: Path, _fake_env: None,
):
    """Byte-level sanity: serialized checkpoint round-trips through json.loads/dumps."""
    _, _ = _run_pipeline(tmp_path, "sid_cp_roundtrip")
    session_dir = tmp_path / "state" / "sid_cp_roundtrip"
    files = sorted(session_dir.glob("gate_*.json"))
    assert files, "no checkpoints written"
    for f in files:
        raw = f.read_text(encoding="utf-8")
        data = json.loads(raw)
        reserialized = json.dumps(data, ensure_ascii=False, indent=2)
        # Re-parse the re-serialized form — must match the original dict.
        assert json.loads(reserialized) == data, (
            f"{f.name} round-trip mismatch"
        )
        # gate_index must match the filename's numeric suffix.
        m = re.match(r"gate_(\d{2})\.json$", f.name)
        assert m and data["gate_index"] == int(m.group(1)), (
            f"{f.name} gate_index {data['gate_index']} != filename index {m.group(1) if m else '?'}"
        )
