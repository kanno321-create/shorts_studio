# Phase 5 — Deferred Items

Out-of-scope discoveries logged during plan execution. These are NOT bugs in
the current plan; they are pre-existing gaps or desirable tightening that
fall outside the active plan's acceptance criteria.

## AF-8 selenium regex submodule gap (discovered in Plan 05-09)

**Location:** `.claude/deprecated_patterns.json` entry #5

**Current regex:** `\bimport\s+selenium\b|\bfrom\s+selenium\s+import`

**What it catches:**
- `import selenium`
- `import selenium as drv`
- `from selenium import webdriver`

**What it misses:**
- `from selenium.webdriver import Chrome`
- `from selenium.common import exceptions`
- `from selenium.webdriver.common.by import By`

**Why deferred:** Plan 05-09 scope is hook test coverage, not regex tightening.
Plan 01 shipped `.claude/deprecated_patterns.json` verbatim per RESEARCH §10.
Changing the regex in-flight would violate the Plan 05-09 instruction "No
changes to .claude/deprecated_patterns.json (Plan 01 already shipped it)".

**Regression pin:** `tests/phase05/test_hook_selenium_block.py::test_from_selenium_submodule_allowed`
pins the current behavior so the gap is explicit in the test suite. If a future
phase tightens the regex to cover `from selenium\.` submodule imports, that
test must be updated to expect `deny`.

**Proposed future regex:** `\bimport\s+selenium\b|\bfrom\s+selenium(\.[a-z_]+)*\s+import`

**Owner:** Future Phase 5+ plan or follow-up maintenance PR.
