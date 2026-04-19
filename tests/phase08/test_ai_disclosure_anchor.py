"""Wave 3 PUB-01 ANCHOR A — containsSyntheticMedia=True HARDCODED.

Phase 7 Correction 3 precedent: AST-based anchor immune to narrative-text
false-positives. RESEARCH Pitfall 6 correction: canonical YouTube Data API v3
field is ``status.containsSyntheticMedia`` (added 2024-10-30). The AGENT.md
spec's custom ``syntheticMedia`` key must NEVER appear paired with False in
any scripts/publisher/*.py file — this test guards against both names.

Four ANCHOR A steps enforced:
1. AST parse of ai_disclosure.py -> dict literal containsSyntheticMedia: True.
2. grep scan scripts/publisher/*.py for containsSyntheticMedia...False -> 0.
3. grep scan scripts/publisher/*.py for syntheticMedia...False        -> 0.
4. runtime call build_status_block() -> containsSyntheticMedia is True.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from scripts.publisher.exceptions import AIDisclosureViolation
from scripts.publisher.ai_disclosure import (
    build_status_block,
    assert_synthetic_media_true,
)


_PUBLISHER_DIR = Path("scripts/publisher")
_AI_DISCLOSURE_PY = _PUBLISHER_DIR / "ai_disclosure.py"


def test_build_status_returns_true_at_runtime():
    block = build_status_block()
    assert block["containsSyntheticMedia"] is True


def test_build_status_not_parametrised_by_signature():
    """Function signature MUST NOT expose containsSyntheticMedia as a parameter."""
    import inspect
    sig = inspect.signature(build_status_block)
    assert "containsSyntheticMedia" not in sig.parameters
    assert "synthetic_media" not in sig.parameters


def test_ai_disclosure_contains_literal_true_for_synthetic_media():
    """ANCHOR A step 1: AST parse — dict literal {..."containsSyntheticMedia": True...}."""
    source = _AI_DISCLOSURE_PY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found_true = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant)
                        and key.value == "containsSyntheticMedia"
                        and isinstance(value, ast.Constant)
                        and value.value is True):
                    found_true = True
    assert found_true, (
        "ANCHOR A failure: no dict literal with 'containsSyntheticMedia': True "
        "found via AST walk of scripts/publisher/ai_disclosure.py"
    )


def test_zero_false_literal_for_contains_synthetic_media_in_publisher_dir():
    """ANCHOR A step 2: grep-style scan across scripts/publisher/*.py.

    Match containsSyntheticMedia followed (within 20 chars) by False — 0 hits required.
    """
    false_rx = re.compile(
        r"containsSyntheticMedia[^=]{0,20}=\s*False|"
        r"containsSyntheticMedia[^:]{0,5}:\s*False"
    )
    violations = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        for m in false_rx.finditer(text):
            violations.append(f"{py}:{m.group(0)}")
    assert not violations, f"ANCHOR A violation: {violations}"


def test_zero_false_literal_for_custom_synthetic_media_key():
    """ANCHOR A step 3: also scan for the AGENT.md's custom ``syntheticMedia`` key
    with False — Pitfall 6 defense. Uses negative lookbehind to exclude
    ``containsSyntheticMedia`` (already covered by step 2) and ``insyntheticMedia``
    (not a real token)."""
    false_rx = re.compile(
        r"(?<!ins)(?<!contains)syntheticMedia[^=]{0,20}=\s*False|"
        r"(?<!ins)(?<!contains)syntheticMedia[^:]{0,5}:\s*False"
    )
    violations = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        for m in false_rx.finditer(text):
            violations.append(f"{py}:{m.group(0)}")
    assert not violations, f"ANCHOR A violation (custom key): {violations}"


def test_assert_synthetic_media_true_passes_on_true():
    assert_synthetic_media_true({"containsSyntheticMedia": True})


def test_assert_synthetic_media_true_raises_on_false():
    with pytest.raises(AIDisclosureViolation):
        assert_synthetic_media_true({"containsSyntheticMedia": False})


def test_assert_synthetic_media_true_raises_on_missing():
    with pytest.raises(AIDisclosureViolation):
        assert_synthetic_media_true({})


def test_assert_synthetic_media_true_raises_on_truthy_non_true():
    """containsSyntheticMedia is not True (it's 1) → must raise (strict identity check)."""
    with pytest.raises(AIDisclosureViolation):
        assert_synthetic_media_true({"containsSyntheticMedia": 1})
