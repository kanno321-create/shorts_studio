"""scripts.hc_checks -- namespace for rewritten Health-Check functions.

Phase 5 Plan 08 rewrote the 1129-line baseline at
``.preserved/harvested/hc_checks_raw/hc_checks.py`` (Tier 3 immutable) into
this package, preserving all 13 public signatures from the baseline
``__all__``. Modifications vs. baseline (per CONTEXT D-18 and RESEARCH
line 967):

1. Import path: ``scripts.orchestrator.hc_checks`` -> ``scripts.hc_checks.hc_checks``.
2. HC-10 lazy-imports ``GATE_INSPECTORS`` from ``scripts.orchestrator`` (not
   ``scripts.orchestrator.harness``) to avoid circular dependency.
3. ``_ffprobe_duration`` now takes an explicit ``timeout_s`` parameter
   (CircuitBreaker-compatible).
4. HC-8 remains a SKIP placeholder (Phase 50-03 Wave 3e wiring deferred,
   out of scope Phase 5 per RESEARCH line 964).

Plus 3 semi-public helpers callable as module attributes:

    check_hc_8_diagnostic_five (stub; out of scope Phase 5)
    check_hc_9_pipeline_order  (preserved)
    check_hc_10_inspector_coverage  (requires GATE_INSPECTORS export from
                                     scripts.orchestrator -- Plan 07 wires)
"""
from __future__ import annotations

from .hc_checks import (
    HCResult,
    check_hc_1,
    check_hc_2,
    check_hc_3,
    check_hc_4,
    check_hc_5,
    check_hc_6,
    check_hc_6_5_cross_slug,
    check_hc_7,
    check_hc_12_text_screenshot,
    check_hc_13_compliance,
    check_hc_14_no_direct_link,
    run_all_hc_checks,
)

__all__ = [
    "HCResult",
    "check_hc_1",
    "check_hc_2",
    "check_hc_3",
    "check_hc_4",
    "check_hc_5",
    "check_hc_6",
    "check_hc_6_5_cross_slug",
    "check_hc_7",
    "check_hc_12_text_screenshot",
    "check_hc_13_compliance",
    "check_hc_14_no_direct_link",
    "run_all_hc_checks",
]
