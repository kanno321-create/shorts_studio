"""Round-trip + atomic write + idempotency + sha256 tests for Checkpointer.

Covers plan 05-03 Task 1 behaviors 1-4, 8-10 + Korean evidence preservation.
Each test uses the ``tmp_state_dir`` fixture from conftest.py (plan 01) for
isolation; no test touches the real ``state/`` directory.
"""
from __future__ import annotations

import json

from scripts.orchestrator.checkpointer import Checkpoint, Checkpointer, sha256_file


def _make_cp(gate_name: str = "TREND", gate_index: int = 1) -> Checkpoint:
    """Factory for a fully-populated Checkpoint with canonical Verdict shape."""
    return Checkpoint(
        session_id="20260419-test",
        gate=gate_name,
        gate_index=gate_index,
        timestamp="2026-04-19T14:35:40.123456+00:00",
        verdict={
            "result": "PASS",
            "score": 88,
            "evidence": [],
            "semantic_feedback": "",
            "inspector_name": "shorts-supervisor",
        },
        artifacts={
            "path": "state/20260419-test/trend.json",
            "sha256": "a" * 64,
        },
    )


def test_save_creates_file(tmp_state_dir):
    """Behavior 1: Checkpointer.save writes gate_{n:02d}.json at session path."""
    c = Checkpointer(tmp_state_dir)
    target = c.save(_make_cp())
    assert target.exists()
    assert target.name == "gate_01.json"  # zero-padded (behavior 10)
    assert target.parent.name == "20260419-test"


def test_no_tmp_file_left_behind(tmp_state_dir):
    """Behavior 2: atomic write — os.replace removes the .tmp intermediate."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp())
    tmp_files = list((tmp_state_dir / "20260419-test").glob("*.tmp"))
    assert tmp_files == [], f"os.replace() did not clean up: {tmp_files}"


def test_schema_version_embedded(tmp_state_dir):
    """Behavior 3: loaded JSON contains _schema: 1 for forward compatibility."""
    c = Checkpointer(tmp_state_dir)
    target = c.save(_make_cp())
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["_schema"] == 1
    assert Checkpointer.SCHEMA_VERSION == 1


def test_round_trip_preserves_all_fields(tmp_state_dir):
    """Behavior 4: save → load cycle preserves every Checkpoint field."""
    c = Checkpointer(tmp_state_dir)
    original = _make_cp()
    target = c.save(original)
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded["session_id"] == original.session_id
    assert loaded["gate"] == original.gate
    assert loaded["gate_index"] == original.gate_index
    assert loaded["timestamp"] == original.timestamp
    assert loaded["verdict"] == original.verdict
    assert loaded["artifacts"] == original.artifacts


def test_korean_evidence_preserved(tmp_state_dir):
    """ensure_ascii=False — Korean semantic_feedback must survive verbatim.

    This matters because pipeline debugging uses ``grep`` on state files;
    escaped \\uXXXX sequences would be unreadable.
    """
    c = Checkpointer(tmp_state_dir)
    cp = _make_cp()
    cp.verdict["semantic_feedback"] = "탐정님의 대사가 해요체로 이탈하고 있습니다"
    target = c.save(cp)
    raw = target.read_text(encoding="utf-8")
    assert "탐정님" in raw, "Korean characters must not be escaped to \\uXXXX"
    loaded = json.loads(raw)
    assert loaded["verdict"]["semantic_feedback"] == cp.verdict["semantic_feedback"]


def test_zero_padded_filenames(tmp_state_dir):
    """Behavior 10: gate_index {3, 14} → 'gate_03.json', 'gate_14.json'.

    Zero-padding guarantees lexicographic sort matches numeric sort — Plan
    04 resume iteration over sorted(glob) depends on this.
    """
    c = Checkpointer(tmp_state_dir)
    target = c.save(_make_cp(gate_index=3))
    assert target.name == "gate_03.json"
    target = c.save(_make_cp(gate_index=14))
    assert target.name == "gate_14.json"
    target = c.save(_make_cp(gate_index=0))
    assert target.name == "gate_00.json"


def test_idempotent_overwrite(tmp_state_dir):
    """Behavior 8: same (session_id, gate_index) overwrites — no duplicates.

    Second write's content wins (os.replace is defined to replace). This
    is the recovery path when a gate re-dispatches after transient fail.
    """
    c = Checkpointer(tmp_state_dir)
    cp = _make_cp()
    c.save(cp)
    cp.verdict["score"] = 99
    c.save(cp)  # same session_id + gate_index → overwrites
    files = list((tmp_state_dir / "20260419-test").glob("gate_01.json"))
    assert len(files) == 1
    loaded = json.loads(files[0].read_text(encoding="utf-8"))
    assert loaded["verdict"]["score"] == 99  # latest write wins


def test_sha256_file_stable(tmp_path):
    """Behavior 9: sha256_file is deterministic + matches known stdlib digest.

    Known SHA256("hello world") = b94d27b9934d3e08... — if this fails, the
    bug is in stdlib hashlib, not our wrapper (canary for env corruption).
    """
    target = tmp_path / "probe.bin"
    target.write_bytes(b"hello world")
    h1 = sha256_file(target)
    h2 = sha256_file(target)
    assert h1 == h2
    assert len(h1) == 64  # hex digest length
    assert h1 == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_sha256_streaming_large_file(tmp_path):
    """Verify chunk streaming works on file larger than single chunk (65536)."""
    target = tmp_path / "big.bin"
    target.write_bytes(b"A" * 200_000)  # 3+ chunks
    digest = sha256_file(target)
    assert len(digest) == 64
    # Deterministic repeat
    assert digest == sha256_file(target)


def test_load_returns_dict_with_schema(tmp_state_dir):
    """Complementary to round-trip: Checkpointer.load returns dict + _schema."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp(gate_name="NICHE", gate_index=2))
    loaded = c.load("20260419-test", 2)
    assert loaded is not None
    assert loaded["_schema"] == 1
    assert loaded["gate"] == "NICHE"
    assert loaded["gate_index"] == 2
