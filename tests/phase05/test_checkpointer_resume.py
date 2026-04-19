"""Resume + dispatched_gates + session-isolation tests for Checkpointer.

Covers plan 05-03 Task 1 behaviors 5-7 + non-existent session edge cases
(the two failure modes Plan 07 pipeline MUST handle on startup: no prior
run at all, and a session dir that exists but is empty / corrupt).
"""
from __future__ import annotations

from scripts.orchestrator.checkpointer import Checkpoint, Checkpointer


def _make_cp(gate: str, idx: int, session_id: str = "s1") -> Checkpoint:
    return Checkpoint(
        session_id=session_id,
        gate=gate,
        gate_index=idx,
        timestamp=f"2026-04-19T{idx:02d}:00:00+00:00",
        verdict={
            "result": "PASS",
            "score": 90,
            "evidence": [],
            "semantic_feedback": "",
            "inspector_name": "shorts-supervisor",
        },
        artifacts={},
    )


def test_resume_returns_minus_one_for_nonexistent_session(tmp_state_dir):
    """Behavior 5a: resume() on never-created session dir returns -1."""
    c = Checkpointer(tmp_state_dir)
    assert c.resume("never-existed") == -1


def test_resume_returns_minus_one_for_empty_directory(tmp_state_dir):
    """Behavior 5b: resume() on empty session dir also returns -1.

    Matters because mkdir(parents=True, exist_ok=True) in save() creates
    the dir — a crash between mkdir and os.replace would leave the dir
    alive but empty. Resume must not misread this as "gate 0 completed".
    """
    c = Checkpointer(tmp_state_dir)
    (tmp_state_dir / "s1").mkdir(parents=True)
    assert c.resume("s1") == -1


def test_resume_returns_highest_gate_index(tmp_state_dir):
    """Behavior 6: resume() returns the maximum gate_index seen on disk.

    With saves at gates 0, 1, 2, 8, resume returns 8 (not 2, not 4, not
    count-of-files). Plan 07 uses this to advance to GateName(8+1=9).
    """
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp("IDLE", 0))
    c.save(_make_cp("TREND", 1))
    c.save(_make_cp("NICHE", 2))
    c.save(_make_cp("ASSETS", 8))
    assert c.resume("s1") == 8


def test_resume_not_confused_by_non_gate_files(tmp_state_dir):
    """Junk files and malformed gate filenames are silently ignored."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp("TREND", 1))
    # Drop files that are not valid gate checkpoints
    (tmp_state_dir / "s1" / "debug.log").write_text("noise")
    (tmp_state_dir / "s1" / "gate_NOT_INT.json").write_text("{}")
    assert c.resume("s1") == 1


def test_dispatched_gates_empty(tmp_state_dir):
    """Behavior 7a: dispatched_gates() on missing session returns empty set."""
    c = Checkpointer(tmp_state_dir)
    assert c.dispatched_gates("nobody") == set()


def test_dispatched_gates_collects_names(tmp_state_dir):
    """Behavior 7b: dispatched_gates() reconstructs the Plan 04 set from disk."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp("IDLE", 0))
    c.save(_make_cp("TREND", 1))
    c.save(_make_cp("NICHE", 2))
    assert c.dispatched_gates("s1") == {"IDLE", "TREND", "NICHE"}


def test_dispatched_gates_skips_corrupt_json(tmp_state_dir):
    """Corrupt JSON in session dir should not brick resume."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp("TREND", 1))
    # Drop a corrupt gate file (well-formed filename, bad JSON)
    (tmp_state_dir / "s1" / "gate_05.json").write_text("{not json")
    assert c.dispatched_gates("s1") == {"TREND"}


def test_load_returns_none_for_missing_gate(tmp_state_dir):
    """Checkpointer.load returns None when the target file is absent."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp("TREND", 1))
    assert c.load("s1", 99) is None
    assert c.load("never-existed", 1) is None
    loaded = c.load("s1", 1)
    assert loaded is not None
    assert loaded["gate"] == "TREND"
    assert loaded["_schema"] == 1


def test_sessions_isolated(tmp_state_dir):
    """Two independent sessions must not leak state into each other."""
    c = Checkpointer(tmp_state_dir)
    c.save(_make_cp("TREND", 1, session_id="s1"))
    c.save(_make_cp("NICHE", 2, session_id="s2"))
    assert c.resume("s1") == 1
    assert c.resume("s2") == 2
    assert c.dispatched_gates("s1") == {"TREND"}
    assert c.dispatched_gates("s2") == {"NICHE"}
