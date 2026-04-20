"""Phase 9.1 acceptance aggregator (SC 1-7).

Exits 0 only if all 7 success criteria pass. Designed to be executed as:

    python tests/phase091/phase091_acceptance.py
    echo $?   # 0 = PASS, 1 = FAIL

SC map (see 09.1-RESEARCH.md §Implementation §7):
    SC1: NotImplementedError removed from _default_*_invoker slots
    SC2: 4 new adapter classes importable
    SC3: shorts_pipeline.py ≤ 800 lines
    SC4: smoke dry-run manifest.json exists with cost_cap_usd=1.0
    SC5: skip_gates / TODO(next-session) / silent-except = 0 in 9.1 files
    SC6: Korean-first error message enforcement across 9.1 files
    SC7: CharacterRegistry load + channel_profile resolve
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

# UTF-8 safeguard for Windows cp949 per Phase 6/9 precedent.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

TARGET_FILES_HOOK = [
    "scripts/orchestrator/invokers.py",
    "scripts/orchestrator/api/nanobanana.py",
    "scripts/orchestrator/api/ken_burns.py",
    "scripts/orchestrator/character_registry.py",
    "scripts/orchestrator/voice_discovery.py",
    "scripts/smoke/phase091_stage2_to_4.py",
]

KOREAN_RE = re.compile(r"[\uAC00-\uD7A3]")


def _sc1_no_notimplemented() -> tuple[bool, str]:
    """SC1 — REQ-091-01: _default_*_invoker stubs deleted from shorts_pipeline.py.

    Plan 05 relocated the three default factories from shorts_pipeline.py into
    scripts/orchestrator/invokers.py. The AST walk rejects any residual
    _default_producer_invoker / _default_supervisor_invoker / _default_asset_sourcer
    method definitions inside the pipeline module (Pitfall 1 — orphan stubs
    would re-raise NotImplementedError on construction).
    """
    path = _REPO_ROOT / "scripts/orchestrator/shorts_pipeline.py"
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = {
        "_default_producer_invoker",
        "_default_supervisor_invoker",
        "_default_asset_sourcer",
    }
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in forbidden:
                found.append(node.name)
    if found:
        return False, f"SC1 FAIL — _default_* stubs still present in shorts_pipeline.py: {found}"
    return True, "SC1 PASS — _default_*_invoker 3 methods removed from shorts_pipeline.py"


def _sc2_adapters_importable() -> tuple[bool, str]:
    """SC2 — REQ-091-02/04/01: 4 new adapter classes importable without error."""
    try:
        from scripts.orchestrator.api.nanobanana import NanoBananaAdapter  # noqa: F401
        from scripts.orchestrator.api.ken_burns import KenBurnsLocalAdapter  # noqa: F401
        from scripts.orchestrator.invokers import (  # noqa: F401
            ClaudeAgentProducerInvoker,
            ClaudeAgentSupervisorInvoker,
        )
    except ImportError as err:
        return False, f"SC2 FAIL — adapter import: {err}"
    except Exception as err:  # noqa: BLE001 — aggregator reports, never raises
        return False, f"SC2 FAIL — unexpected {type(err).__name__}: {err}"
    return True, "SC2 PASS — 4 new adapters importable (NanoBanana / KenBurnsLocal / ClaudeAgentProducer / ClaudeAgentSupervisor)"


def _sc3_pipeline_line_count() -> tuple[bool, str]:
    """SC3 — Pitfall 8: shorts_pipeline.py must stay within 대표님's 800-line ceiling."""
    path = _REPO_ROOT / "scripts/orchestrator/shorts_pipeline.py"
    n = len(path.read_text(encoding="utf-8").splitlines())
    if n > 800:
        return False, f"SC3 FAIL — shorts_pipeline.py = {n} lines > 800 (대표님 500-800 상한 위반)"
    return True, f"SC3 PASS — shorts_pipeline.py = {n} lines (≤ 800)"


def _sc4_smoke_manifest() -> tuple[bool, str]:
    """SC4 — REQ-091-07: Stage 2→4 smoke manifest exists with $1 cost cap honored."""
    path = _REPO_ROOT / "output/phase091_smoke/manifest.json"
    if not path.exists():
        return False, f"SC4 FAIL — smoke manifest missing: {path}"
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return False, f"SC4 FAIL — manifest JSON invalid: {err}"
    if m.get("cost_cap_usd") != 1.0:
        return False, f"SC4 FAIL — cost_cap_usd = {m.get('cost_cap_usd')}, expected 1.0"
    total = m.get("total_usd", 2.0)
    if total > 1.0:
        return False, f"SC4 FAIL — total_usd = {total} > 1.0"
    mode = m.get("mode", "unknown")
    return True, f"SC4 PASS — manifest mode={mode} total_usd=${total:.2f} cap=$1.00"


def _sc5_hook_hygiene() -> tuple[bool, str]:
    """SC5 — Hook 3종 contract on the 6 Phase 9.1 target files.

    - skip_gates substring → 0 hits
    - TODO(next-session) substring → 0 hits
    - silent except (handler body == [Pass]) → 0 hits via AST walk
    """
    violations: list[str] = []
    for rel in TARGET_FILES_HOOK:
        path = _REPO_ROOT / rel
        if not path.exists():
            violations.append(f"{rel}: MISSING")
            continue
        content = path.read_text(encoding="utf-8")
        if "skip_gates" in content:
            violations.append(f"{rel}: skip_gates")
        if "TODO(next-session)" in content:
            violations.append(f"{rel}: TODO(next-session)")
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    for handler in node.handlers:
                        if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                            violations.append(f"{rel}:{handler.lineno}: silent-except")
        except SyntaxError as err:
            violations.append(f"{rel}: parse error {err}")
    if violations:
        return False, f"SC5 FAIL — {len(violations)} hits: {violations[:5]}"
    return True, f"SC5 PASS — 0 hits across {len(TARGET_FILES_HOOK)} files (skip_gates / TODO(next-session) / silent-except)"


def _sc6_korean_errors() -> tuple[bool, str]:
    """SC6 — Korean-first enforcement across Phase 9.1 source files.

    Best-effort: counts how many of the 6 target files contain at least one
    Korean grapheme (AC00–D7A3 range) anywhere in the file. Threshold is 5/6
    — allows one pure-boilerplate file to slip while guaranteeing the
    adapter/invoker/registry/smoke modules carry 대표님-facing Korean
    messaging (Pitfall 9).
    """
    korean_hits = 0
    detail: list[str] = []
    for rel in TARGET_FILES_HOOK:
        path = _REPO_ROOT / rel
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if KOREAN_RE.search(content):
            korean_hits += 1
            detail.append(Path(rel).name)
    if korean_hits < 5:
        return False, f"SC6 FAIL — only {korean_hits}/{len(TARGET_FILES_HOOK)} files contain Korean strings ({detail})"
    return True, f"SC6 PASS — {korean_hits}/{len(TARGET_FILES_HOOK)} files carry Korean-first messaging"


def _sc7_character_registry() -> tuple[bool, str]:
    """SC7 — REQ-091-03: CharacterRegistry load + channel_profile reference resolves."""
    try:
        from scripts.orchestrator.character_registry import CharacterRegistry
        registry = CharacterRegistry().load()
        names = registry.list_all()
        if "channel_profile" not in names:
            return False, f"SC7 FAIL — channel_profile not in registry: {names}"
        ref = registry.get_reference_path("channel_profile")
        if not ref.exists():
            return False, f"SC7 FAIL — ref file missing: {ref}"
    except Exception as err:  # noqa: BLE001 — aggregator reports, never raises
        return False, f"SC7 FAIL — load raised {type(err).__name__}: {err}"
    return True, f"SC7 PASS — channel_profile resolves to {ref.name}"


def main() -> int:
    checks = [
        _sc1_no_notimplemented,
        _sc2_adapters_importable,
        _sc3_pipeline_line_count,
        _sc4_smoke_manifest,
        _sc5_hook_hygiene,
        _sc6_korean_errors,
        _sc7_character_registry,
    ]
    results: list[tuple[bool, str]] = []
    for fn in checks:
        ok, msg = fn()
        results.append((ok, msg))
        prefix = "OK  " if ok else "FAIL"
        print(f"[{prefix}] {msg}")

    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print()
    if passed == total:
        print(f"Phase 9.1 acceptance: ALL_PASS ({passed}/{total} SC green)")
        return 0
    print(f"Phase 9.1 acceptance: FAIL ({passed}/{total} SC green — {total - passed} FAIL)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
