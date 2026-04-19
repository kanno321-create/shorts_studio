"""Anchor test for the '13 operational gates' invariant (Correction 1 guard).

RESEARCH Open Q2 + §Critical CONTEXT.md Corrections #1 explicitly recommend this
file to prevent the CONTEXT '17 GATE' misconception from silently reappearing.

The original 07-CONTEXT.md said "17 = 12 + 5 sub-gate" but the real source
(``scripts/orchestrator/gate_guard.py:94-96``) enforces exactly 13 operational
gates (TREND..MONITOR). This test locks that truth against future drift in
*either* direction: if it ever needs to be updated to 17 OR to 12, something
is very wrong — investigate immediately, do NOT patch the test.

Lock: the ``_OPERATIONAL_GATES`` frozenset is the canonical set;
``GATE_INSPECTORS`` has the same 13 keys. Both must agree.
"""
from __future__ import annotations

from scripts.orchestrator import GateName
from scripts.orchestrator.gate_guard import _OPERATIONAL_GATES
from scripts.orchestrator.shorts_pipeline import GATE_INSPECTORS


# Canonical 13 gate names in IntEnum numeric order (gates.py:40-54).
OPERATIONAL_GATE_NAMES = [
    "TREND",
    "NICHE",
    "RESEARCH_NLM",
    "BLUEPRINT",
    "SCRIPT",
    "POLISH",
    "VOICE",
    "ASSETS",
    "ASSEMBLY",
    "THUMBNAIL",
    "METADATA",
    "UPLOAD",
    "MONITOR",
]


def test_operational_gates_count_equals_13():
    """Correction 1 primary anchor: 13 operational gates (TREND..MONITOR), NOT 17."""
    operational = [g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]
    assert len(operational) == 13, (
        f"RESEARCH Correction 1 violated. GateName has {len(operational)} operational "
        f"members (expected 13). Values: {[g.name for g in operational]}. "
        "Check scripts/orchestrator/gates.py IntEnum definition."
    )


def test_operational_gates_frozenset_size_is_13():
    """The _OPERATIONAL_GATES frozenset in gate_guard.py (line 94-96) must be size 13."""
    assert len(_OPERATIONAL_GATES) == 13, (
        f"_OPERATIONAL_GATES frozenset has {len(_OPERATIONAL_GATES)} members (expected 13). "
        "This is the ANCHOR constant that Correction 1 protects."
    )


def test_the_number_is_thirteen_not_seventeen():
    """Explicit anti-regression guard against the CONTEXT '17 GATE' misconception.

    If this test ever needs to be updated to 17, the GateName IntEnum has been
    extended incorrectly OR someone re-introduced 'sub-gates' into the
    operational set. Inspector/producer internal rubric checks are NOT
    operational gates — they do not participate in GateGuard.dispatch.
    """
    operational_count = sum(
        1 for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)
    )
    assert operational_count != 17, (
        "Operational gate count drifted to 17 — investigate. "
        "CONTEXT '17 = 12 + 5 sub-gate' was FALSIFIED by research §Critical Corrections #1."
    )
    assert operational_count != 12, (
        "Operational gate count drifted to 12 — IntEnum broken. "
        "Either a gate was removed or IDLE/COMPLETE were miscounted."
    )
    assert operational_count == 13


def test_operational_gate_names_in_canonical_order():
    """D-4: IntEnum numeric ordering matches canonical 13-gate sequence TREND..MONITOR."""
    operational = [g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]
    operational.sort(key=lambda g: int(g))
    assert [g.name for g in operational] == OPERATIONAL_GATE_NAMES


def test_idle_and_complete_are_bookends():
    """IDLE(0) and COMPLETE(14) must be the only non-operational members."""
    non_operational = [g for g in GateName if g in (GateName.IDLE, GateName.COMPLETE)]
    assert len(non_operational) == 2
    assert int(GateName.IDLE) == 0
    assert int(GateName.COMPLETE) == 14


def test_gate_inspectors_has_13_keys():
    """shorts_pipeline.py GATE_INSPECTORS must cover exactly 13 operational gates."""
    assert len(GATE_INSPECTORS) == 13, (
        f"GATE_INSPECTORS has {len(GATE_INSPECTORS)} keys; must be 13"
    )
    assert set(GATE_INSPECTORS.keys()) == set(OPERATIONAL_GATE_NAMES), (
        f"GATE_INSPECTORS keys {sorted(GATE_INSPECTORS.keys())} "
        f"do not match canonical 13 {sorted(OPERATIONAL_GATE_NAMES)}"
    )


def test_operational_gates_frozenset_matches_gate_inspectors():
    """_OPERATIONAL_GATES and GATE_INSPECTORS are redundant — must stay in sync.

    Both are derived from the same truth (GateName minus IDLE/COMPLETE). If they
    disagree, one of them drifted.
    """
    frozenset_names = {g.name for g in _OPERATIONAL_GATES}
    inspector_names = set(GATE_INSPECTORS.keys())
    assert frozenset_names == inspector_names == set(OPERATIONAL_GATE_NAMES), (
        "Two operational-gate sources-of-truth disagree. "
        f"_OPERATIONAL_GATES={sorted(frozenset_names)} "
        f"GATE_INSPECTORS={sorted(inspector_names)} "
        f"canonical={sorted(OPERATIONAL_GATE_NAMES)}"
    )
