"""D-4 DAG ordering — ensure_dependencies raises on out-of-order dispatch.

``GATE_DEPS`` (scripts/orchestrator/gates.py:68-98) is the single source of
truth for runtime DAG predecessors. Key multi-parent edges:

- ``ASSEMBLY`` requires ``(VOICE, ASSETS)``.
- ``UPLOAD``   requires ``(THUMBNAIL, METADATA)``.

:class:`GateGuard.ensure_dependencies` (gate_guard.py:178-193) raises
:class:`GateDependencyUnsatisfied` when any declared predecessor is absent
from the dispatched set (IDLE is treated as satisfied by construction).

Per RESEARCH §Critical Corrections #2: the exception class name is
``GateDependencyUnsatisfied`` — NOT ``GateOrderError``. The plan prose used
that informal label; the canonical source is gates.py:150-153.
"""
from __future__ import annotations

import pytest

from scripts.orchestrator import GateDependencyUnsatisfied, GateName, Verdict
from scripts.orchestrator.gate_guard import GateGuard


def _pass() -> Verdict:
    return Verdict(
        result="PASS",
        score=90,
        evidence=[],
        semantic_feedback="",
        inspector_name="shorts-supervisor",
    )


# ---------------------------------------------------------------------------
# ASSEMBLY depends on VOICE + ASSETS.
# ---------------------------------------------------------------------------


def test_ensure_dependencies_raises_when_voice_missing():
    """ASSEMBLY without VOICE dispatched → GateDependencyUnsatisfied."""
    g = GateGuard(None, "sid_order_1")
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.ASSETS,
    ):
        g.dispatch(gate, _pass())
    with pytest.raises(GateDependencyUnsatisfied) as exc:
        g.ensure_dependencies(GateName.ASSEMBLY)
    assert "ASSEMBLY" in str(exc.value)
    assert "VOICE" in str(exc.value)


def test_ensure_dependencies_raises_when_assets_missing():
    """ASSEMBLY without ASSETS dispatched → GateDependencyUnsatisfied."""
    g = GateGuard(None, "sid_order_2")
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
    ):
        g.dispatch(gate, _pass())
    with pytest.raises(GateDependencyUnsatisfied) as exc:
        g.ensure_dependencies(GateName.ASSEMBLY)
    assert "ASSEMBLY" in str(exc.value)
    assert "ASSETS" in str(exc.value)


def test_ensure_dependencies_allows_assembly_when_both_voice_and_assets_done():
    """Happy path: both predecessors dispatched → no raise."""
    g = GateGuard(None, "sid_order_3")
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
    ):
        g.dispatch(gate, _pass())
    # Should NOT raise.
    g.ensure_dependencies(GateName.ASSEMBLY)


# ---------------------------------------------------------------------------
# UPLOAD depends on THUMBNAIL + METADATA.
# ---------------------------------------------------------------------------


def test_upload_requires_thumbnail_and_metadata_when_metadata_missing():
    """UPLOAD without METADATA dispatched → GateDependencyUnsatisfied."""
    g = GateGuard(None, "sid_order_5")
    # Dispatch up through THUMBNAIL (METADATA skipped intentionally).
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
        GateName.ASSEMBLY,
        GateName.THUMBNAIL,
    ):
        g.dispatch(gate, _pass())
    with pytest.raises(GateDependencyUnsatisfied) as exc:
        g.ensure_dependencies(GateName.UPLOAD)
    assert "UPLOAD" in str(exc.value)
    assert "METADATA" in str(exc.value)


def test_upload_requires_thumbnail_and_metadata_when_thumbnail_missing():
    """UPLOAD without THUMBNAIL dispatched → GateDependencyUnsatisfied."""
    g = GateGuard(None, "sid_order_6")
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
        GateName.ASSEMBLY,
        GateName.METADATA,
    ):
        g.dispatch(gate, _pass())
    with pytest.raises(GateDependencyUnsatisfied) as exc:
        g.ensure_dependencies(GateName.UPLOAD)
    assert "UPLOAD" in str(exc.value)
    assert "THUMBNAIL" in str(exc.value)


def test_upload_allowed_when_both_thumbnail_and_metadata_done():
    """UPLOAD happy path — both parents dispatched."""
    g = GateGuard(None, "sid_order_7")
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
        GateName.BLUEPRINT,
        GateName.SCRIPT,
        GateName.POLISH,
        GateName.VOICE,
        GateName.ASSETS,
        GateName.ASSEMBLY,
        GateName.THUMBNAIL,
        GateName.METADATA,
    ):
        g.dispatch(gate, _pass())
    # Should NOT raise.
    g.ensure_dependencies(GateName.UPLOAD)


# ---------------------------------------------------------------------------
# TREND root dependency (IDLE is the bookend, treated as satisfied).
# ---------------------------------------------------------------------------


def test_ensure_dependencies_on_first_operational_gate_trend_no_raise():
    """TREND's only dep is IDLE — gate_guard.ensure_dependencies treats IDLE
    as satisfied (see gate_guard.py:188 ``d is not GateName.IDLE``).
    """
    g = GateGuard(None, "sid_order_4")
    # No dispatches yet — TREND must still be callable since IDLE is bookend.
    g.ensure_dependencies(GateName.TREND)  # must NOT raise


# ---------------------------------------------------------------------------
# Intermediate single-parent edges (linear chain).
# ---------------------------------------------------------------------------


def test_niche_requires_trend():
    """NICHE's parent is TREND — without TREND dispatched, must raise."""
    g = GateGuard(None, "sid_order_niche")
    with pytest.raises(GateDependencyUnsatisfied):
        g.ensure_dependencies(GateName.NICHE)


def test_script_requires_blueprint():
    """SCRIPT's parent is BLUEPRINT — without it dispatched, must raise."""
    g = GateGuard(None, "sid_order_script")
    for gate in (
        GateName.TREND,
        GateName.NICHE,
        GateName.RESEARCH_NLM,
    ):
        g.dispatch(gate, _pass())
    # BLUEPRINT missing
    with pytest.raises(GateDependencyUnsatisfied):
        g.ensure_dependencies(GateName.SCRIPT)
