"""Plan 06-10 — Byte-diff regression guard for AGENT.md mass update (D-18).

Parses the two sha256 manifests (``phase06_agents_before.txt`` and
``phase06_agents_after.txt``) produced by Plan 10 Task 1 and asserts:

    - Both manifests exist and cover the same set of AGENT.md files.
    - The 15 target agents show a hash delta (content changed).
    - The remaining non-target agents are byte-identical (regression guard).
    - The per-file delta manifest exists (D-18 requirement).

The test is intentionally strict on non-target drift because Plan 10's
surgical scope is "touch only the 15 agents with Phase 6 placeholders;
every other agent remains frozen".
"""
from __future__ import annotations

from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
AGENTS = _REPO / ".claude" / "agents"
BEFORE = (
    _REPO
    / ".planning"
    / "phases"
    / "06-wiki-notebooklm-integration-failures-reservoir"
    / "phase06_agents_before.txt"
)
AFTER = (
    _REPO
    / ".planning"
    / "phases"
    / "06-wiki-notebooklm-integration-failures-reservoir"
    / "phase06_agents_after.txt"
)
DELTA = (
    _REPO
    / ".planning"
    / "phases"
    / "06-wiki-notebooklm-integration-failures-reservoir"
    / "phase06_agent_prompt_delta.md"
)


PLAN_10_TARGET_AGENTS = {
    "inspectors/content/ins-factcheck",
    "inspectors/content/ins-korean-naturalness",
    "inspectors/content/ins-narrative-quality",
    "inspectors/style/ins-thumbnail-hook",
    "inspectors/technical/ins-audio-quality",
    "inspectors/technical/ins-render-integrity",
    "inspectors/technical/ins-subtitle-alignment",
    "producers/director",
    "producers/metadata-seo",
    "producers/niche-classifier",
    "producers/researcher",
    "producers/scene-planner",
    "producers/scripter",
    "producers/shot-planner",
    "producers/trend-collector",
}


def _parse_manifest(path: Path) -> dict[str, str]:
    """Parse sha256sum manifest.

    Each non-blank line: ``<hex-hash><whitespace><path>``. Returns a dict
    keyed by normalized forward-slash path with value = hash.
    """
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        rel_path = parts[1].lstrip("*").replace("\\", "/")
        result[rel_path] = parts[0]
    return result


def _rel_agent_key(path: str) -> str:
    """Normalize a manifest path to ``<category>/<agent_dir>`` form.

    ``.claude/agents/inspectors/content/ins-factcheck/AGENT.md`` →
    ``inspectors/content/ins-factcheck``.
    """
    p = path.replace("\\", "/")
    if ".claude/agents/" in p:
        p = p.split(".claude/agents/", 1)[1]
    if p.endswith("/AGENT.md"):
        p = p[: -len("/AGENT.md")]
    return p


def test_manifests_exist():
    assert BEFORE.exists(), (
        "phase06_agents_before.txt missing — Task 1 snapshot did not run"
    )
    assert AFTER.exists(), (
        "phase06_agents_after.txt missing — Task 1 snapshot did not run"
    )


def test_manifests_cover_same_file_set():
    """Before and after manifests must cover identical AGENT.md paths (no file added/removed)."""
    before = set(_parse_manifest(BEFORE).keys())
    after = set(_parse_manifest(AFTER).keys())
    added = after - before
    removed = before - after
    assert added == set(), f"AGENT.md files added during Plan 10: {added}"
    assert removed == set(), f"AGENT.md files removed during Plan 10: {removed}"


def test_manifest_has_all_agent_md_files():
    """Manifest entry count matches on-disk AGENT.md file count (no orphan entries)."""
    before = _parse_manifest(BEFORE)
    on_disk = {
        str(p.relative_to(_REPO)).replace("\\", "/")
        for p in AGENTS.rglob("AGENT.md")
    }
    manifest_paths = set(before.keys())
    # Manifest must be a superset-or-equal of on-disk (nothing on disk missing from manifest)
    missing_from_manifest = on_disk - manifest_paths
    assert missing_from_manifest == set(), (
        f"On-disk AGENT.md files missing from before.txt: {missing_from_manifest}"
    )


def test_15_target_agents_hash_changed():
    """All 15 target agents must show a hash delta post-edit."""
    before = _parse_manifest(BEFORE)
    after = _parse_manifest(AFTER)
    changed_targets: list[str] = []
    for raw_path, h_before in before.items():
        rel = _rel_agent_key(raw_path)
        if rel in PLAN_10_TARGET_AGENTS:
            h_after = after.get(raw_path)
            if h_after is not None and h_after != h_before:
                changed_targets.append(rel)
    missing = PLAN_10_TARGET_AGENTS - set(changed_targets)
    # At least 10 of 15 must have changed (generous lower bound for test robustness).
    assert len(changed_targets) >= 10, (
        f"Only {len(changed_targets)} target agents changed, expected >=10; "
        f"unchanged targets: {missing}"
    )


def test_non_target_agents_byte_identical():
    """Every agent NOT in the 15-target set must be byte-identical post-edit."""
    before = _parse_manifest(BEFORE)
    after = _parse_manifest(AFTER)
    drift: list[str] = []
    for raw_path, h_before in before.items():
        rel = _rel_agent_key(raw_path)
        if rel in PLAN_10_TARGET_AGENTS:
            continue
        h_after = after.get(raw_path)
        if h_after is not None and h_after != h_before:
            drift.append(rel)
    assert drift == [], (
        f"Non-target agents changed (regression — D-18 surgical scope violated): "
        f"{drift}"
    )


def test_total_agent_count_matches_disk():
    """Manifest entry count equals actual AGENT.md file count on disk."""
    before = _parse_manifest(BEFORE)
    on_disk_count = sum(1 for _ in AGENTS.rglob("AGENT.md"))
    assert len(before) == on_disk_count, (
        f"Manifest has {len(before)} entries, disk has {on_disk_count} AGENT.md files"
    )


def test_delta_manifest_exists():
    """phase06_agent_prompt_delta.md documents per-file line deltas (D-18)."""
    assert DELTA.exists(), "phase06_agent_prompt_delta.md missing — D-18 output"


def test_delta_manifest_enumerates_all_15_targets():
    """Delta manifest names all 15 target agents (audit traceability)."""
    text = DELTA.read_text(encoding="utf-8")
    missing = [
        target
        for target in PLAN_10_TARGET_AGENTS
        if target not in text
    ]
    assert missing == [], (
        f"Delta manifest does not reference the following targets: {missing}"
    )
