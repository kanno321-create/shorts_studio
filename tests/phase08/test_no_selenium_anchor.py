"""Wave 4 PUB-02 ANCHOR C — zero selenium / webdriver / playwright imports.

AF-8 (RESEARCH H1 Hard Constraint): Selenium 업로드 영구 금지 — YouTube ToS
위반으로 채널 정지 리스크. The ``pre_tool_use.py`` Hook already blocks
import attempts at edit time; this test is the REDUNDANT static anchor
so CI would catch a regression even if Hooks were bypassed.

Three layered checks:

1. Textual scan (regex) of top-level ``import`` / ``from`` statements.
2. AST ``ast.Import`` / ``ast.ImportFrom`` node walk (catches
   indentation-masked or nested imports that the regex misses).
3. Token-identifier scan for ANY reference to ``selenium`` / ``webdriver``
   / ``playwright`` in executable code (catches dynamic
   ``importlib.import_module("selenium")``, string literals inside
   ``eval``, etc.). Comment / docstring mentions allowed.

Scope is ``scripts/publisher/**/*.py`` ONLY. Tests themselves may mention
these names in assertions (they do).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_PUBLISHER_DIR = _REPO_ROOT / "scripts" / "publisher"
_FORBIDDEN_MODULES = ("selenium", "webdriver", "playwright")


def test_zero_top_level_selenium_imports():
    rx = re.compile(
        r"^\s*(?:import\s+(?:selenium|webdriver|playwright)"
        r"|from\s+(?:selenium|webdriver|playwright)\b)",
        re.MULTILINE,
    )
    hits: list[str] = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        for m in rx.finditer(text):
            hits.append(f"{py}:{m.group(0)}")
    assert not hits, f"ANCHOR C violation: {hits}"


def test_ast_no_forbidden_import_node():
    violations: list[str] = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in _FORBIDDEN_MODULES:
                        violations.append(f"{py}:{node.lineno}:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".", 1)[0]
                    if root in _FORBIDDEN_MODULES:
                        violations.append(f"{py}:{node.lineno}:{node.module}")
    assert not violations, f"ANCHOR C AST violation: {violations}"


def _collect_string_literal_lineset(tree: ast.AST) -> set[int]:
    """Return line numbers that belong to any string literal (incl. docstring
    constants). Used to distinguish prose mentions from executable code.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            start = node.lineno
            end = getattr(node, "end_lineno", start) or start
            for ln in range(start, end + 1):
                lines.add(ln)
    return lines


@pytest.mark.parametrize("module_name", _FORBIDDEN_MODULES)
def test_zero_string_references_to_forbidden_modules(module_name):
    """Pure-text scan — catches dynamic ``importlib.import_module(...)`` etc.

    Comment lines (``#``-prefixed) and lines that belong to any string
    literal (docstrings, ordinary strings) are allowed: we document the
    drop reason in comments/docstrings and those are NOT runnable code.
    A line is flagged only when it is NEITHER a comment NOR part of a
    string literal AND matches the forbidden module name.
    """
    rx = re.compile(rf"\b{re.escape(module_name)}\b")
    hits: list[str] = []
    for py in _PUBLISHER_DIR.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            string_lines: set[int] = set()
        else:
            string_lines = _collect_string_literal_lineset(tree)
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if line_no in string_lines:
                continue   # line is inside a string / docstring literal
            if rx.search(line):
                hits.append(f"{py}:{line_no}:{stripped[:80]}")
    assert not hits, (
        f"ANCHOR C string-ref violation for {module_name!r}: {hits}"
    )


def test_anchor_c_also_clean_in_tests_phase08():
    """Extended scope — tests/phase08/ (mocks + conftest + test files) MUST
    also be free of selenium/webdriver/playwright IMPORTS. Pure string
    references inside docstrings ARE allowed (this test's own docstring
    contains them).
    """
    tests_dir = _REPO_ROOT / "tests" / "phase08"
    violations: list[str] = []
    for py in tests_dir.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in _FORBIDDEN_MODULES:
                        violations.append(f"{py}:{node.lineno}:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".", 1)[0]
                    if root in _FORBIDDEN_MODULES:
                        violations.append(f"{py}:{node.lineno}:{node.module}")
    assert not violations, f"ANCHOR C tests/phase08 violation: {violations}"
