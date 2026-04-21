"""SPC-02 — shorts-supervisor AGENT.md body size + schema invariants.

Plan 15-03 Task 3 populate. 4 hard-cap / structure tests on the post-compression
AGENT.md body. Target: body stripped chars < 7000 (달성 5712, 대표님).

Invariants tracked:
  1. body stripped chars < 7000 — SPC-02 hard ceiling
  2. 5 headers (## Purpose / ## Inputs / ## Outputs / ## Prompt / ## Contract)
     — AGENT-STD-01 Markdown-flavor mirror (supervisor variant, XML block
     excluded from Phase 12 verifier scope).
  3. MUST REMEMBER block positioned within last 30% of body — AGENT-09 RoPE
     end-position invariant.
  4. Frontmatter keys (name, description, version, role, category, maxTurns)
     preserved — downstream invokers.py parse contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_MD = (
    REPO_ROOT
    / ".claude"
    / "agents"
    / "supervisor"
    / "shorts-supervisor"
    / "AGENT.md"
)


def _read_body_stripped() -> str:
    text = SUPERVISOR_MD.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    body = parts[2] if len(parts) >= 3 else text
    return body.strip()


def test_body_under_7000_chars() -> None:
    """SPC-02 hard cap — stripped body chars < 7000 (target 6000)."""
    body = _read_body_stripped()
    assert len(body) < 7000, (
        f"shorts-supervisor AGENT.md body = {len(body)} chars, "
        f"exceeds SPC-02 ceiling 7000 (대표님). "
        f"Progressive Disclosure split 필요 — references/ 로 추가 분리."
    )


def test_five_block_schema_preserved() -> None:
    """AGENT-STD-01 5 Markdown headers 모두 등장."""
    text = SUPERVISOR_MD.read_text(encoding="utf-8")
    required = (
        "## Purpose",
        "## Inputs",
        "## Outputs",
        "## Prompt",
        "## Contract",
    )
    missing = [h for h in required if h not in text]
    assert not missing, (
        f"shorts-supervisor AGENT.md missing headers {missing} "
        f"after SPC-02 split — 5-block schema 훼손 (대표님)."
    )


def test_must_remember_at_end() -> None:
    """MUST REMEMBER block 은 body 의 마지막 30% 안에 위치 (AGENT-09 RoPE)."""
    body = _read_body_stripped()
    idx = body.find("MUST REMEMBER")
    assert idx != -1, "MUST REMEMBER block 부재 (AGENT-09 RoPE 훼손)"
    position_ratio = idx / len(body)
    assert position_ratio >= 0.70, (
        f"MUST REMEMBER block at {position_ratio:.0%} of body — "
        f"AGENT-09 요구사항 last 30% 기준 위반 (대표님). "
        f"idx={idx}, body_len={len(body)}"
    )


@pytest.mark.parametrize(
    "key",
    ["name:", "description:", "version:", "role:", "category:", "maxTurns:"],
)
def test_frontmatter_intact(key: str) -> None:
    """Frontmatter YAML keys 보존 — downstream invokers.py parse 의존."""
    text = SUPERVISOR_MD.read_text(encoding="utf-8")
    # frontmatter = first fenced block between '---' markers
    parts = text.split("---", 2)
    assert len(parts) >= 3, "frontmatter delimiter '---' 쌍 부재"
    frontmatter = parts[1]
    assert key in frontmatter, (
        f"frontmatter key {key!r} 부재 — 압축 중 훼손 (대표님)"
    )
