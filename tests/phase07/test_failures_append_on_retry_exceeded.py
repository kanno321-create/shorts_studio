"""TEST-04 secondary: FAILURES.md append-only format + Hook compatibility.

Phase 6 check_failures_append_only Hook basename-matches 'FAILURES.md' (uppercase)
per .claude/hooks/pre_tool_use.py:184. Phase 7 tests use 'failures.md' (lowercase)
via tmp_path — basename is 'failures.md', NOT 'FAILURES.md' — so the Hook does
not fire. This proves:
  - append_failures writes the documented marker format (fallback.py:30-64)
  - Writes use 'a' (append) mode — subsequent runs preserve prior content
  - Content contains 'THUMBNAIL FAIL after regeneration exhausted' heading
  - <!-- session:... gate:THUMBNAIL ts:... --> marker present
  - Hook compatibility: basename lowercase bypass-by-naming contract
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Align with Plan 07-03 / 07-04 / 07-06-a precedent for sibling ``mocks`` import.
_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from scripts.orchestrator import GateName, ShortsPipeline, Verdict  # noqa: E402
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


def _run_pipeline_with_thumbnail_fail(tmp_path: Path, session_id: str) -> Path:
    """Run pipeline with THUMBNAIL failing 3 times; return the failures.md Path.

    Reuses the Plan 07-06-a side_effect pattern but keeps this file
    self-contained (no cross-test import).
    """
    invocation = {"n": 0}

    def supervisor_side_effect(gate, output):
        if gate == GateName.THUMBNAIL:
            invocation["n"] += 1
            if invocation["n"] <= 3:
                return _fail_verdict()
        return _pass_verdict()

    producer = MagicMock(return_value={
        "artifact_path": str(tmp_path / "a.json"),
        "prompt": "p",
        "duration_seconds": 5,
        "duration_s": 5.0,
        "anchor_frame": str(tmp_path / "a.png"),
        "cut_index": 0,
    })
    failures_path = tmp_path / "failures.md"

    # Align with Plan 07-03 E2E: pipeline._run_voice iterates AudioSegment.path
    # — Wave-1 mocks return list[dict] for unit contract. Override to [].
    typecast = TypecastMock()
    elevenlabs = ElevenLabsMock()
    typecast.generate = lambda *a, **kw: []  # type: ignore[method-assign]
    elevenlabs.generate_with_timestamps = lambda *a, **kw: []  # type: ignore[method-assign]

    pipeline = ShortsPipeline(
        session_id=session_id,
        state_root=tmp_path / "state",
        failures_path=failures_path,
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs,
        shotstack_adapter=ShotstackMock(),
        producer_invoker=producer,
        supervisor_invoker=MagicMock(side_effect=supervisor_side_effect),
        asset_sourcer_invoker=lambda p: tmp_path / "still_image.jpg",
    )
    with patch.object(pipeline.timeline, "align", return_value=[]), patch.object(
        pipeline.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline.run()
    return failures_path


def test_failures_file_exists_after_retry_exhaustion(
    tmp_path: Path, _fake_env: None,
) -> None:
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_1")
    assert fp.exists(), f"append_failures did not create {fp}"


def test_failures_contains_thumbnail_exhausted_marker(
    tmp_path: Path, _fake_env: None,
) -> None:
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_2")
    content = fp.read_text(encoding="utf-8")
    assert "THUMBNAIL FAIL after regeneration exhausted" in content, (
        f"Expected heading missing.\nContent:\n{content}"
    )


def test_failures_contains_session_marker_comment(
    tmp_path: Path, _fake_env: None,
) -> None:
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_3")
    content = fp.read_text(encoding="utf-8")
    # fallback.py:56 format: <!-- session:sid_fa_3 gate:THUMBNAIL ts:... -->
    pattern = re.compile(r"<!--\s*session:sid_fa_3\s+gate:THUMBNAIL\s+ts:")
    assert pattern.search(content), (
        f"Session marker missing.\nContent:\n{content}"
    )


def test_failures_contains_evidence_summary(
    tmp_path: Path, _fake_env: None,
) -> None:
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_4")
    content = fp.read_text(encoding="utf-8")
    assert "Evidence (first 3):" in content
    # Evidence rule + detail propagated from _fail_verdict().
    assert "thumbnail_hook_weak" in content
    assert "no face, no caption" in content


def test_failures_contains_semantic_feedback(
    tmp_path: Path, _fake_env: None,
) -> None:
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_4b")
    content = fp.read_text(encoding="utf-8")
    assert "Semantic feedback:" in content
    assert "face + caption missing" in content


def test_failures_file_basename_is_lowercase_hook_bypass(
    tmp_path: Path, _fake_env: None,
) -> None:
    """Hook check_failures_append_only matches basename 'FAILURES.md' only.

    Phase 7 uses 'failures.md' (lowercase) via tmp_path — Hook does not fire
    on this filename (pre_tool_use.py:184 case-sensitive basename match).
    This test documents the bypass-by-naming contract.
    """
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_5")
    # basename MUST be lowercase to avoid tripping the Hook during test runs.
    assert fp.name == "failures.md"
    assert fp.name != "FAILURES.md"
    # Path must be inside tmp_path (no bleed into real .claude/failures/).
    assert tmp_path in fp.parents


def test_failures_write_is_append_only(
    tmp_path: Path, _fake_env: None,
) -> None:
    """fallback.py:63 uses open('a', ...). Subsequent append preserves prior content."""
    fp = _run_pipeline_with_thumbnail_fail(tmp_path, "sid_fa_6a")
    initial = fp.read_text(encoding="utf-8")

    # Run again with a different session id — should APPEND, not truncate.
    # Note: pipeline writes to the SAME failures.md path each time. We use a
    # fresh tmp subdir for state so the second run doesn't collide on state.
    state_root_b = tmp_path / "state_b"
    failures_path = fp  # reuse same failures.md (the invariant under test)

    invocation = {"n": 0}

    def supervisor_side_effect(gate, output):
        if gate == GateName.THUMBNAIL:
            invocation["n"] += 1
            if invocation["n"] <= 3:
                return _fail_verdict()
        return _pass_verdict()

    producer = MagicMock(return_value={
        "artifact_path": str(tmp_path / "a.json"),
        "prompt": "p", "duration_seconds": 5, "duration_s": 5.0,
        "anchor_frame": str(tmp_path / "a.png"), "cut_index": 0,
    })
    typecast = TypecastMock()
    elevenlabs = ElevenLabsMock()
    typecast.generate = lambda *a, **kw: []  # type: ignore[method-assign]
    elevenlabs.generate_with_timestamps = lambda *a, **kw: []  # type: ignore[method-assign]

    pipeline2 = ShortsPipeline(
        session_id="sid_fa_6b",
        state_root=state_root_b,
        failures_path=failures_path,
        kling_adapter=KlingMock(),
        runway_adapter=RunwayMock(),
        typecast_adapter=typecast,
        elevenlabs_adapter=elevenlabs,
        shotstack_adapter=ShotstackMock(),
        producer_invoker=producer,
        supervisor_invoker=MagicMock(side_effect=supervisor_side_effect),
        asset_sourcer_invoker=lambda p: tmp_path / "still_image.jpg",
    )
    with patch.object(pipeline2.timeline, "align", return_value=[]), patch.object(
        pipeline2.timeline, "insert_transition_shots", return_value=[]
    ):
        pipeline2.run()

    after = fp.read_text(encoding="utf-8")
    assert after.startswith(initial), (
        "append_failures unexpectedly truncated prior content"
    )
    assert "session:sid_fa_6a" in after
    assert "session:sid_fa_6b" in after
    assert len(after) > len(initial)


def test_failures_write_mode_is_append_grep_proof(
    tmp_path: Path, _fake_env: None,
) -> None:
    """Structural proof: fallback.py uses open(..., 'a', ...) — NOT 'w'.

    Grep the canonical fallback.py source; the only open() call in
    append_failures must use 'a' mode. This locks the contract at the source
    level so Plan 07-06 stays robust even if the test pipeline run is
    restructured later.
    """
    import scripts.orchestrator.fallback as fb

    src = Path(fb.__file__).read_text(encoding="utf-8")
    # The append_failures body must use 'a' mode exactly once.
    assert ".open(\"a\"" in src or ".open('a'" in src, (
        f"fallback.py append_failures must use open('a', ...) append mode"
    )
    # And must NOT use 'w' mode (that would truncate).
    # Strict: search for any open(..., 'w'...) or .open("w"...) patterns.
    w_pattern = re.compile(r"\.open\(\s*['\"]w['\"]")
    assert not w_pattern.search(src), (
        "fallback.py must NOT use truncate-mode 'w' — found a w-mode open()."
    )
