"""GATE integration tests for the rewritten ``scripts.hc_checks``.

Proves that the Plan 07 ``GATE_INSPECTORS`` re-export + the Plan 08 lazy
import inside ``check_hc_10_inspector_coverage`` wire together without a
circular dependency, and that the 13 public symbols are visible from the
``scripts.hc_checks`` package namespace (per the baseline ``__all__``).

Mapping covered (per RESEARCH line 977):
    SCRIPT   -> HC-2, HC-7, HC-9
    POLISH   -> HC-7
    VOICE    -> HC-3
    ASSETS   -> HC-6, HC-6.5, HC-12
    ASSEMBLY -> HC-1
    METADATA -> HC-13, HC-14
    MONITOR  -> HC-4, HC-5
    COMPLETE -> run_all_hc_checks()
"""
from __future__ import annotations

from pathlib import Path

from scripts.hc_checks.hc_checks import (
    HCResult,
    check_hc_8_diagnostic_five,
    check_hc_10_inspector_coverage,
)
from scripts.orchestrator import GATE_INSPECTORS, GateName


def test_hc_10_uses_gate_inspectors_lazy_import(tmp_path: Path) -> None:
    """HC-10 pulls from scripts.orchestrator.GATE_INSPECTORS via lazy import.

    This test asserts the lazy import works (i.e. check_hc_10 returns a
    result and does not raise ImportError). With no ``gate_results/``
    directory the verdict is SKIP -- the point is that the call completed
    without an import-time or runtime failure.
    """
    result = check_hc_10_inspector_coverage(tmp_path)
    assert isinstance(result, HCResult)
    assert result.hc_id == "HC-10"
    # tmp_path has no gate_results/ -> SKIP is the expected outcome here.
    assert result.verdict == "SKIP"


def test_hc_10_fails_when_expected_inspectors_missing(tmp_path: Path) -> None:
    """HC-10 actually consults GATE_INSPECTORS once gate_results/ is present.

    Phase 5 GATE_INSPECTORS["SCRIPT"] contains at least one inspector name.
    With an empty gate_results/ directory, HC-10 must FAIL (missing expected
    inspectors), proving the lazy import actually reads the constant.
    """
    (tmp_path / "gate_results").mkdir()
    result = check_hc_10_inspector_coverage(tmp_path)
    assert result.hc_id == "HC-10"
    # With GATE_INSPECTORS["SCRIPT"] non-empty and 0 executed -> FAIL
    assert result.verdict == "FAIL"
    # Evidence mentions the missing inspectors (lazy import succeeded).
    assert "missing" in result.evidence
    assert len(result.evidence["missing"]) >= 1


def test_hc_10_passes_when_all_script_inspectors_executed(tmp_path: Path) -> None:
    """HC-10 returns PASS when every SCRIPT inspector has a result file."""
    gate_results = tmp_path / "gate_results"
    gate_results.mkdir()
    # Discover the expected SCRIPT inspectors via the same lazy import path
    # that HC-10 uses. Phase 5 uses uppercase keys ("SCRIPT").
    expected = GATE_INSPECTORS.get("SCRIPT") or GATE_INSPECTORS.get("script") or []
    assert expected, "GATE_INSPECTORS[SCRIPT] should be non-empty"
    for ins_name in expected:
        (gate_results / f"{ins_name}.json").write_text("{}", encoding="utf-8")
    result = check_hc_10_inspector_coverage(tmp_path)
    assert result.verdict == "PASS"
    assert result.evidence["count"] == len(expected)


def test_gate_inspectors_coverage_complete() -> None:
    """Every operational gate has at least one inspector (per Plan 07)."""
    operational = [g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)]
    for g in operational:
        assert g.name in GATE_INSPECTORS, f"{g.name} missing from GATE_INSPECTORS"
        assert len(GATE_INSPECTORS[g.name]) >= 1, f"{g.name} has empty inspector list"


def test_hc_8_returns_skip(tmp_path: Path) -> None:
    """Phase 50-03 SKIP stub preserved per RESEARCH line 964.

    With ``script.json`` present, HC-8 reaches the Phase 50-03 deferred-stub
    branch and returns SKIP with the "Plan 50-03 Wave 3e" detail message.
    """
    (tmp_path / "script.json").write_text("{}", encoding="utf-8")
    result = check_hc_8_diagnostic_five(tmp_path)
    assert result.verdict == "SKIP"
    assert "50-03" in result.detail or "wired" in result.detail.lower()
    assert result.evidence.get("plan") == "50-03"


def test_no_circular_import_from_shorts_pipeline() -> None:
    """orchestrator.shorts_pipeline must NOT import hc_checks at module top.

    Prevents a circular dependency between the orchestrator keystone and the
    hc_checks package. HC-10 uses a lazy ``from scripts.orchestrator import
    GATE_INSPECTORS`` inside the function body precisely so the orchestrator
    never has to know about hc_checks at import time.
    """
    import scripts.orchestrator.shorts_pipeline as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    top_of_module = "\n".join(src.split("\n")[:80])  # import block is near top
    assert "from scripts.hc_checks" not in top_of_module, (
        "Circular import risk: remove hc_checks from shorts_pipeline top-level imports"
    )
    assert "import scripts.hc_checks" not in top_of_module, (
        "Circular import risk: remove hc_checks from shorts_pipeline top-level imports"
    )


def test_public_symbols_from_init() -> None:
    """scripts.hc_checks __init__ re-exports 13 public names (baseline __all__)."""
    import scripts.hc_checks as pkg

    expected = [
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
    for name in expected:
        assert hasattr(pkg, name), f"{name} missing from scripts.hc_checks.__init__"
    # __all__ matches baseline (length 13)
    assert len(pkg.__all__) == 13
    assert set(pkg.__all__) == set(expected)


def test_no_top_level_orchestrator_import_in_hc_checks() -> None:
    """hc_checks.py must NOT import scripts.orchestrator at module top.

    The HC-10 lazy import is the only allowed consumer; a module-top import
    would reintroduce the circular dependency this plan removed.
    """
    import scripts.hc_checks.hc_checks as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    top_of_module = "\n".join(src.split("\n")[:80])  # import block is near top
    assert "from scripts.orchestrator" not in top_of_module, (
        "hc_checks.py must not import scripts.orchestrator at module top"
    )
    assert "import scripts.orchestrator" not in top_of_module, (
        "hc_checks.py must not import scripts.orchestrator at module top"
    )
