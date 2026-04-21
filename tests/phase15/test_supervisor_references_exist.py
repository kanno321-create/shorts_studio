"""SPC-02 — Progressive Disclosure @references/ link integrity.

Plan 15-03 Task 3 populate. 3 tests verifying that:
  1. references/supervisor_variant.md 실존 + frontmatter `status: ready`
  2. references/inspector_paths.md 실존
  3. AGENT.md body 가 두 @references/ 링크 모두 포함 (dangling link 방지)
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR_DIR = (
    REPO_ROOT
    / ".claude"
    / "agents"
    / "supervisor"
    / "shorts-supervisor"
)
AGENT_MD = SUPERVISOR_DIR / "AGENT.md"
VARIANT_MD = SUPERVISOR_DIR / "references" / "supervisor_variant.md"
PATHS_MD = SUPERVISOR_DIR / "references" / "inspector_paths.md"


def test_supervisor_variant_exists() -> None:
    """references/supervisor_variant.md 실존 + frontmatter status: ready."""
    assert VARIANT_MD.exists(), (
        f"{VARIANT_MD} 부재 — Progressive Disclosure 분리 실패 (대표님)"
    )
    text = VARIANT_MD.read_text(encoding="utf-8")
    assert "status: ready" in text, (
        "frontmatter 'status: ready' 부재 — Wave 0 상태 표식 누락"
    )
    # byte size 검증 (plan acceptance: ≥ 3000 bytes)
    size = len(text.encode("utf-8"))
    assert size >= 3000, (
        f"supervisor_variant.md size = {size} bytes, 하한 3000 미달 (대표님)"
    )


def test_inspector_paths_exists() -> None:
    """references/inspector_paths.md 실존 + byte size ≥ 1200."""
    assert PATHS_MD.exists(), (
        f"{PATHS_MD} 부재 — Progressive Disclosure 분리 실패 (대표님)"
    )
    text = PATHS_MD.read_text(encoding="utf-8")
    size = len(text.encode("utf-8"))
    assert size >= 1200, (
        f"inspector_paths.md size = {size} bytes, 하한 1200 미달 (대표님)"
    )
    # 17 inspector 경로 모두 포함
    expected_inspectors = (
        "ins-blueprint-compliance",
        "ins-timing-consistency",
        "ins-schema-integrity",
        "ins-factcheck",
        "ins-narrative-quality",
        "ins-korean-naturalness",
        "ins-tone-brand",
        "ins-readability",
        "ins-thumbnail-hook",
        "ins-license",
        "ins-platform-policy",
        "ins-safety",
        "ins-audio-quality",
        "ins-render-integrity",
        "ins-subtitle-alignment",
        "ins-mosaic",
        "ins-gore",
    )
    missing = [name for name in expected_inspectors if name not in text]
    assert not missing, (
        f"inspector_paths.md 에서 17 Inspector 중 {missing} 누락 (대표님)"
    )


def test_agent_md_links_references() -> None:
    """AGENT.md 가 @references/ 2 링크 모두 포함 (dangling link 방지)."""
    text = AGENT_MD.read_text(encoding="utf-8")
    assert "@references/supervisor_variant.md" in text, (
        "AGENT.md 에 @references/supervisor_variant.md 링크 부재 (대표님)"
    )
    assert "@references/inspector_paths.md" in text, (
        "AGENT.md 에 @references/inspector_paths.md 링크 부재 (대표님)"
    )
