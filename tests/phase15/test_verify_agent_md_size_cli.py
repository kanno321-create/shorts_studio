"""SPC-03 — verify_agent_md_size.py CLI contract.

Plan 15-03 Task 3 populate. 6 tests asserting argparse + exit code contract +
real repo scan. Reuses ``scripts/validate/verify_agent_md_size.py`` via
``main(argv)`` direct call (avoids subprocess overhead, preserves stdout capture).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validate"))

from verify_agent_md_size import main, CHAR_LIMIT  # noqa: E402


def _make_agent_tree(root: Path, sizes: dict[str, int]) -> None:
    """Build a fake .claude/agents/ tree with agents of given body-char sizes.

    Args:
        root: base directory (e.g. ``tmp_path``).
        sizes: mapping {"producers/a": 5000, "supervisor/b": 2000}. Each value
            is the **body char** target — the fixture generates frontmatter +
            body with exactly that char count (ASCII filler).
    """
    agents = root / ".claude" / "agents"
    for rel, body_chars in sizes.items():
        agent_dir = agents / rel
        agent_dir.mkdir(parents=True, exist_ok=True)
        body = "x" * body_chars
        (agent_dir / "AGENT.md").write_text(
            f"---\nname: {rel}\n---\n\n{body}\n",
            encoding="utf-8",
        )


def test_cli_exit_0_when_all_under_ceiling(tmp_path: Path) -> None:
    """All agents under ceiling → exit 0."""
    _make_agent_tree(tmp_path, {
        "producers/small-a": 1000,
        "producers/small-b": 2000,
        "supervisor/small-c": 500,
    })
    rc = main([
        "--ceiling", "5000",
        "--agents-root", str(tmp_path / ".claude" / "agents"),
    ])
    assert rc == 0, "전원 under ceiling 이어야 하나 rc != 0 (대표님)"


def test_cli_exit_1_when_over_ceiling(tmp_path: Path, capsys) -> None:
    """Any agent over ceiling → exit 1 + violator 이름 출력."""
    _make_agent_tree(tmp_path, {
        "producers/fat-a": 9000,
        "producers/slim-b": 1000,
    })
    rc = main([
        "--ceiling", "5000",
        "--agents-root", str(tmp_path / ".claude" / "agents"),
    ])
    assert rc == 1, "violator 존재 시 rc=1 이어야 함 (대표님)"
    captured = capsys.readouterr()
    assert "fat-a" in captured.out, (
        f"violator 이름 'fat-a' 출력 누락: {captured.out!r}"
    )


def test_cli_default_ceiling_18000() -> None:
    """Default CHAR_LIMIT = 18000 (drift-only guard, 0 breaking change)."""
    assert CHAR_LIMIT == 18000, (
        f"CHAR_LIMIT = {CHAR_LIMIT}, 18000 이어야 함 (Research Open Q2 결정)"
    )


def test_cli_custom_ceiling_via_arg(tmp_path: Path) -> None:
    """--ceiling N override 적용 — 5000 으로 낮추면 현실적 producer 위반."""
    _make_agent_tree(tmp_path, {
        "producers/big": 6000,
    })
    rc_low = main([
        "--ceiling", "5000",
        "--agents-root", str(tmp_path / ".claude" / "agents"),
    ])
    rc_high = main([
        "--ceiling", "7000",
        "--agents-root", str(tmp_path / ".claude" / "agents"),
    ])
    assert rc_low == 1 and rc_high == 0, (
        f"ceiling override 반영 실패: low={rc_low}, high={rc_high}"
    )


def test_cli_scans_producer_and_supervisor(tmp_path: Path, capsys) -> None:
    """producers/ + supervisor/ 두 디렉토리 모두 스캔."""
    _make_agent_tree(tmp_path, {
        "producers/prod-a": 9000,
        "supervisor/sup-a": 9000,
    })
    rc = main([
        "--ceiling", "5000",
        "--agents-root", str(tmp_path / ".claude" / "agents"),
    ])
    assert rc == 1
    captured = capsys.readouterr()
    assert "prod-a" in captured.out
    assert "sup-a" in captured.out, (
        f"supervisor/ 스캔 누락: {captured.out!r}"
    )


def test_cli_real_repo_under_18000() -> None:
    """실제 repo 의 producer 14 + supervisor 1 모두 18000 chars 이하 (2026-04-22 baseline)."""
    rc = main([
        "--ceiling", "18000",
        "--agents-root", str(REPO_ROOT / ".claude" / "agents"),
    ])
    assert rc == 0, (
        "real repo AGENT.md 중 18000 chars 초과 violator 존재 (대표님) — "
        "Plan 15-03 baseline 훼손."
    )
