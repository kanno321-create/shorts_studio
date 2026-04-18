"""Phase 4 Plan 06 — Technical Inspector 3 compliance tests (Wave 2b).

Verifies 3 Technical Inspector AGENT.md files:
  - .claude/agents/inspectors/technical/ins-audio-quality/AGENT.md
  - .claude/agents/inspectors/technical/ins-render-integrity/AGENT.md
  - .claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md

Covers:
  - Structural: frontmatter shape (role=inspector, category=technical, maxTurns=3).
  - LogicQA: 5 sub_qs present in prompt body (RUB-01).
  - Content keywords:
      * ins-subtitle-alignment → WhisperX + kresnik + 50 (SUBT-01 + SUBT-03).
      * ins-render-integrity → 9:16 + 1080×1920 (or 1080x1920) + 59 + Remotion.
      * ins-audio-quality → -3 dBFS + silence.
  - MUST REMEMBER positioned at file end (AGENT-09).
  - 창작 금지 (RUB-02) + producer_prompt 읽기 금지 (RUB-06) invariants present.
  - validate_all_agents passes (AGENT-07/08/09).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

TECHNICAL_ROOT = pathlib.Path(".claude/agents/inspectors/technical")
INSPECTOR_NAMES = [
    "ins-audio-quality",
    "ins-render-integrity",
    "ins-subtitle-alignment",
]


@pytest.fixture
def agent_paths(repo_root):
    paths = {name: repo_root / TECHNICAL_ROOT / name / "AGENT.md" for name in INSPECTOR_NAMES}
    for name, p in paths.items():
        assert p.exists(), f"{name}: AGENT.md missing at {p}"
    return paths


# ---------------------------------------------------------------------------
# Structural checks — frontmatter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_frontmatter_role_inspector(name, agent_paths, agent_md_loader):
    meta, _ = agent_md_loader(str(agent_paths[name]))
    assert meta.get("role") == "inspector", (
        f"{name}: role must be 'inspector', got {meta.get('role')!r}"
    )


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_frontmatter_category_technical(name, agent_paths, agent_md_loader):
    meta, _ = agent_md_loader(str(agent_paths[name]))
    assert meta.get("category") == "technical", (
        f"{name}: category must be 'technical', got {meta.get('category')!r}"
    )


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_frontmatter_maxturns_three(name, agent_paths, agent_md_loader):
    meta, _ = agent_md_loader(str(agent_paths[name]))
    mt = meta.get("maxTurns")
    # frontmatter parser returns strings — compare as string too
    assert str(mt) == "3", f"{name}: maxTurns must be 3, got {mt!r}"


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_frontmatter_name_matches_dir(name, agent_paths, agent_md_loader):
    meta, _ = agent_md_loader(str(agent_paths[name]))
    assert meta.get("name") == name, (
        f"{name}: frontmatter name mismatch — got {meta.get('name')!r}"
    )


# ---------------------------------------------------------------------------
# LogicQA — 5 sub_qs structure (RUB-01)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_logicqa_main_q_present(name, agent_paths, agent_md_loader):
    _, body = agent_md_loader(str(agent_paths[name]))
    assert "<main_q>" in body and "</main_q>" in body, (
        f"{name}: LogicQA main_q block missing (RUB-01)"
    )


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_logicqa_five_sub_qs(name, agent_paths, agent_md_loader):
    _, body = agent_md_loader(str(agent_paths[name]))
    # Require q1..q5 tokens (RUB-01 5 sub-q enforcement)
    for token in ("q1:", "q2:", "q3:", "q4:", "q5:"):
        assert token in body, (
            f"{name}: LogicQA sub-question {token!r} missing (need 5 sub_qs, RUB-01)"
        )


# ---------------------------------------------------------------------------
# Content keywords (plan must-haves)
# ---------------------------------------------------------------------------


def test_audio_quality_keywords(agent_paths):
    body = agent_paths["ins-audio-quality"].read_text("utf-8")
    assert "-3" in body, "ins-audio-quality: '-3' missing (peak dBFS threshold)"
    assert "dBFS" in body, "ins-audio-quality: 'dBFS' missing"
    assert "silence" in body, "ins-audio-quality: 'silence' missing"


def test_render_integrity_keywords(agent_paths):
    body = agent_paths["ins-render-integrity"].read_text("utf-8")
    assert "9:16" in body, "ins-render-integrity: '9:16' missing (aspect ratio)"
    assert ("1080×1920" in body) or ("1080x1920" in body), (
        "ins-render-integrity: '1080×1920' or '1080x1920' missing (resolution)"
    )
    assert "59" in body, "ins-render-integrity: '59' missing (duration ceiling)"
    assert "Remotion" in body, "ins-render-integrity: 'Remotion' missing"


def test_subtitle_alignment_keywords(agent_paths):
    body = agent_paths["ins-subtitle-alignment"].read_text("utf-8")
    assert "WhisperX" in body, "ins-subtitle-alignment: 'WhisperX' missing (SUBT-01)"
    assert "kresnik" in body, "ins-subtitle-alignment: 'kresnik' missing (SUBT-01 model)"
    assert "50" in body, "ins-subtitle-alignment: '50' missing (±50ms SUBT-03)"
    assert "word-level" in body, "ins-subtitle-alignment: 'word-level' missing"


# ---------------------------------------------------------------------------
# MUST REMEMBER + invariants (AGENT-09 / RUB-02 / RUB-06)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_must_remember_at_end(name, agent_paths):
    body = agent_paths[name].read_text("utf-8")
    lines = body.splitlines()
    total = len(lines)
    mr_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("## MUST REMEMBER"):
            mr_idx = i
            break
    assert mr_idx != -1, f"{name}: '## MUST REMEMBER' header missing (AGENT-09)"
    ratio_from_end = (total - mr_idx) / total
    assert ratio_from_end <= 0.4, (
        f"{name}: MUST REMEMBER at line {mr_idx}/{total} "
        f"(ratio_from_end={ratio_from_end:.2f} > 0.4, AGENT-09 RoPE violation)"
    )


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_must_remember_contains_prohibition_invariants(name, agent_paths):
    body = agent_paths[name].read_text("utf-8")
    # Isolate MUST REMEMBER section
    idx = body.find("## MUST REMEMBER")
    assert idx != -1, f"{name}: MUST REMEMBER header missing"
    mr_section = body[idx:]
    assert "창작 금지" in mr_section, (
        f"{name}: '창작 금지' (RUB-02) missing in MUST REMEMBER"
    )
    assert "producer_prompt" in mr_section, (
        f"{name}: 'producer_prompt' (RUB-06) missing in MUST REMEMBER"
    )
    assert "RUB-02" in mr_section, f"{name}: RUB-02 citation missing"
    assert "RUB-06" in mr_section, f"{name}: RUB-06 citation missing"
    assert "maxTurns" in mr_section, f"{name}: maxTurns invariant missing (RUB-05)"
    assert "rubric" in mr_section.lower(), f"{name}: rubric schema invariant missing (RUB-04)"


@pytest.mark.parametrize("name", INSPECTOR_NAMES)
def test_phase4_spec_only_invariant(name, agent_paths):
    """Phase 4 는 스펙만 정의. 실 ffmpeg/WhisperX 호출은 Phase 5 오케스트레이터."""
    body = agent_paths[name].read_text("utf-8")
    idx = body.find("## MUST REMEMBER")
    assert idx != -1
    mr_section = body[idx:]
    assert "Phase 5" in mr_section, (
        f"{name}: Phase 5 deferral statement missing in MUST REMEMBER "
        "(실 tool 호출은 Phase 5 오케스트레이터)"
    )


# ---------------------------------------------------------------------------
# External validator integration (AGENT-07/08/09)
# ---------------------------------------------------------------------------


def test_validate_all_agents_passes(repo_root):
    """Run validate_all_agents on .claude/agents/inspectors/technical — must exit 0."""
    cmd = [
        sys.executable,
        "-m",
        "scripts.validate.validate_all_agents",
        "--path",
        str(TECHNICAL_ROOT),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"validate_all_agents failed (exit {proc.returncode}):\n"
        f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )
    assert "OK: 3 agent(s) validated" in proc.stdout, (
        f"expected 3 agents validated, got:\n{proc.stdout}"
    )
