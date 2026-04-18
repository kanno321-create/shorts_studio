"""Phase 4 Plan 05 — Compliance Inspector 3 AGENT.md structural/content/style tests.

Covers ins-license / ins-platform-policy / ins-safety.

Validates:
- Frontmatter fields (role=inspector, category=compliance, maxTurns=3)
- Prompt body required keywords per inspector
- MUST REMEMBER located in final 40% of body (AGENT-09)
- 창작 금지 (RUB-02) + producer_prompt leak clause (RUB-06) present
- ins-safety blocklist >= 15 entries across 4 axes
"""
from __future__ import annotations

import pathlib

import pytest

COMPLIANCE_ROOT = pathlib.Path(".claude/agents/inspectors/compliance")

AGENTS = [
    "ins-license",
    "ins-platform-policy",
    "ins-safety",
]


# Resolve repo root once at import time so the module-scoped fixture does not
# depend on the function-scoped `repo_root` fixture (avoids ScopeMismatch).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def agent_files():
    out = {}
    for name in AGENTS:
        p = _REPO_ROOT / COMPLIANCE_ROOT / name / "AGENT.md"
        assert p.exists(), f"{name}/AGENT.md missing at {p}"
        out[name] = p
    return out


@pytest.mark.parametrize("name", AGENTS)
def test_frontmatter_shape(name, agent_files, agent_md_loader):
    meta, body = agent_md_loader(str(agent_files[name]))
    assert meta.get("name") == name, f"{name}: name mismatch {meta.get('name')!r}"
    assert meta.get("role") == "inspector", f"{name}: role must be inspector"
    assert meta.get("category") == "compliance", f"{name}: category must be compliance"
    # maxTurns stored as str by the stdlib parser — accept either
    mt = meta.get("maxTurns")
    assert str(mt) == "3", f"{name}: maxTurns must be 3, got {mt!r}"
    assert "version" in meta, f"{name}: version field missing"


@pytest.mark.parametrize("name", AGENTS)
def test_description_length_and_triggers(name, agent_files, agent_md_loader):
    meta, _ = agent_md_loader(str(agent_files[name]))
    desc = meta.get("description", "")
    assert len(desc) <= 1024, f"{name}: description {len(desc)} > 1024 (AGENT-08)"
    # at least 3 comma-separated trigger-like tokens
    candidates = [t.strip() for t in desc.split(",") if len(t.strip()) >= 2]
    assert len(candidates) >= 3, f"{name}: only {len(candidates)} trigger tokens"


@pytest.mark.parametrize("name", AGENTS)
def test_must_remember_position(name, agent_files, agent_md_loader):
    _, body = agent_md_loader(str(agent_files[name]))
    lines = body.splitlines()
    idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("## MUST REMEMBER"):
            idx = i
            break
    assert idx >= 0, f"{name}: MUST REMEMBER header missing"
    ratio = (len(lines) - idx) / len(lines)
    assert ratio <= 0.4, (
        f"{name}: MUST REMEMBER at line {idx}/{len(lines)} "
        f"(ratio_from_end={ratio:.2f}) > 0.4 (AGENT-09)"
    )


@pytest.mark.parametrize("name", AGENTS)
def test_must_remember_contains_required_clauses(name, agent_files, agent_md_loader):
    _, body = agent_md_loader(str(agent_files[name]))
    must_section = body.split("## MUST REMEMBER", 1)[1]
    assert "창작 금지" in must_section, f"{name}: RUB-02 clause missing"
    assert "producer_prompt" in must_section, f"{name}: RUB-06 clause missing"
    assert "rubric" in must_section.lower() or "RUB-04" in must_section, (
        f"{name}: RUB-04 clause missing"
    )


def test_ins_license_required_keywords(agent_files):
    body = agent_files["ins-license"].read_text("utf-8")
    required = ["KOMCA", "K-pop", "AF-13", "AF-4", "BTS", "Epidemic Sound"]
    missing = [k for k in required if k not in body]
    assert not missing, f"ins-license missing keywords: {missing}"
    # Full 10 K-pop artists from §5.5 line 1162
    kpop_artists = ["BTS", "BLACKPINK", "NewJeans", "IVE", "aespa",
                    "LE SSERAFIM", "Stray Kids", "SEVENTEEN", "NCT", "TWICE"]
    missing_artists = [a for a in kpop_artists if a not in body]
    assert not missing_artists, f"ins-license missing K-pop artists: {missing_artists}"
    # royalty-free whitelist 4 domains (at least)
    for wl in ["Epidemic Sound", "Artlist", "YouTube Audio", "Free Music Archive"]:
        assert wl in body, f"ins-license missing whitelist entry: {wl}"
    # af_bank.json reference
    assert "af_bank.json" in body, "ins-license must reference af_bank.json"


def test_ins_platform_policy_required_keywords(agent_files):
    body = agent_files["ins-platform-policy"].read_text("utf-8")
    required = ["명예훼손", "아동복지법", "공소제기", "초상권",
                "Inauthentic", "3 템플릿", "Human signal"]
    missing = [k for k in required if k not in body]
    assert not missing, f"ins-platform-policy missing keywords: {missing}"
    # Jaccard threshold mentioned
    assert "Jaccard" in body, "ins-platform-policy must mention Jaccard"
    assert "0.7" in body, "ins-platform-policy must cite 0.7 threshold"


def test_ins_safety_required_axes_and_blocklist(agent_files):
    body = agent_files["ins-safety"].read_text("utf-8")
    # 4 axes
    for axis in ["지역", "세대", "정치", "젠더"]:
        assert axis in body, f"ins-safety missing axis: {axis}"
    # ins-gore role separation mentioned (overlap avoidance)
    assert "ins-gore" in body, "ins-safety must reference ins-gore for role separation"


def test_ins_safety_blocklist_min_15_entries(agent_files):
    """Count distinct blocklist tokens across 4 axes — must >= 15."""
    body = agent_files["ins-safety"].read_text("utf-8")
    # Sample of representative tokens we expect in seed blocklist
    expected_tokens = [
        # 지역
        "전라디언", "홍어", "지역감정",
        # 세대
        "mz충", "꼰대", "틀딱", "급식충",
        # 정치
        "일베", "극우", "극좌", "빨갱이",
        # 젠더
        "김치녀", "한남충", "된장녀", "페미충", "메갈",
    ]
    hits = [t for t in expected_tokens if t in body]
    assert len(hits) >= 15, (
        f"ins-safety seed blocklist coverage only {len(hits)}/16+ "
        f"(found: {hits})"
    )
