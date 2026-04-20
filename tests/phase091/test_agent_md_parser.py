"""RED stub for REQ-091-01 — Wave 2 AGENT.md YAML-frontmatter parser.

Frozen contract: `load_agent_system_prompt(agent_dir: Path) -> tuple[str, dict]`.
"""
from __future__ import annotations

from pathlib import Path


def test_parser_importable() -> None:
    """REQ-091-01: load_agent_system_prompt is importable."""
    from scripts.orchestrator.invokers import load_agent_system_prompt  # noqa: F401


def test_parser_strips_yaml_frontmatter(fake_agent_md_dir: Path) -> None:
    """REQ-091-01: body is pure markdown (no YAML), frontmatter dict parses maxTurns=3."""
    from scripts.orchestrator.invokers import load_agent_system_prompt

    body, fm = load_agent_system_prompt(fake_agent_md_dir)
    assert "maxTurns" not in body, (
        "frontmatter must not leak into body injected as Claude system prompt"
    )
    assert fm.get("maxTurns") == 3
    assert "fake-producer" in body  # body markdown preserved


def test_parser_handles_no_frontmatter(tmp_path: Path) -> None:
    """REQ-091-01: missing frontmatter returns empty dict, full body preserved."""
    from scripts.orchestrator.invokers import load_agent_system_prompt

    d = tmp_path / "no-fm-producer"
    d.mkdir()
    (d / "AGENT.md").write_text(
        "# no-fm-producer\n\nBody without frontmatter.\n",
        encoding="utf-8",
    )
    body, fm = load_agent_system_prompt(d)
    assert fm == {}
    assert "Body without frontmatter" in body
