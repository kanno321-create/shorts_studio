"""scripts.hc_checks — namespace for rewritten Health-Check functions.

Phase 5 Plan 08 fills this package with hc_checks.py — rewritten from the
1129-line baseline at .preserved/harvested/hc_checks_raw/hc_checks.py
(Tier 3 immutable, attrib +R). The rewrite MUST preserve all 13 public
signatures in __all__:

    HCResult, check_hc_1, check_hc_2, check_hc_3, check_hc_4, check_hc_5,
    check_hc_6, check_hc_6_5_cross_slug, check_hc_7,
    check_hc_12_text_screenshot, check_hc_13_compliance,
    check_hc_14_no_direct_link, run_all_hc_checks

Plus 3 semi-public helpers callable as module attributes:
    check_hc_8_diagnostic_five (stub; out of scope Phase 5)
    check_hc_9_pipeline_order  (preserve)
    check_hc_10_inspector_coverage  (requires GATE_INSPECTORS export from
                                     scripts.orchestrator — Plan 07 wires)

Plan 08 adds CircuitBreaker protection around _ffprobe_duration() subprocess
calls and integrates with the new OrchestratorError hierarchy where
applicable (PASS verdicts still return HCResult; FAIL paths may optionally
raise to the orchestrator).

No imports at this layer — populated by Plan 08.
"""
from __future__ import annotations
