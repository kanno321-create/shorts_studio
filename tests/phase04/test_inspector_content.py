"""Structural compliance tests for 3 Content Inspectors (Plan 04-03).

Verifies:
- Exactly 3 AGENT.md files under .claude/agents/inspectors/content/
- role=inspector, category=content for all 3
- ins-factcheck maxTurns=10 (RUB-05 exception); narrative + korean-naturalness maxTurns=3
- LogicQA block with 5 sub_qs in all 3 prompt bodies
- ins-narrative-quality body contains "3초 hook" + "질문형" + ("숫자" or "고유명사")
- ins-factcheck body contains "citation" + ("source-grounded" OR "NotebookLM")
- ins-korean-naturalness body contains 하오체 (하오|이오|구려|다네) + 해요체 (해요|에요|지요) regex chars
- All MUST REMEMBER contains 창작 금지 + producer_prompt

Follows test_inspector_structural.py pattern from Plan 04-02.
"""
from __future__ import annotations

import pathlib

CONTENT_ROOT = pathlib.Path(".claude/agents/inspectors/content")
EXPECTED_AGENTS = {"ins-factcheck", "ins-narrative-quality", "ins-korean-naturalness"}


def _content_agent_paths():
    """Return sorted list of AGENT.md files under inspectors/content/."""
    return sorted(CONTENT_ROOT.rglob("AGENT.md"))


def test_exactly_three_content_inspectors_exist():
    paths = _content_agent_paths()
    assert len(paths) == 3, f"expected 3 content inspectors, got {len(paths)}: {paths}"
    slugs = {p.parent.name for p in paths}
    assert slugs == EXPECTED_AGENTS, f"expected {EXPECTED_AGENTS}, got {slugs}"


def test_all_three_have_role_inspector_category_content(agent_md_loader):
    for slug in EXPECTED_AGENTS:
        meta, _ = agent_md_loader(str(CONTENT_ROOT / slug / "AGENT.md"))
        assert meta.get("role") == "inspector", f"{slug}: role != inspector ({meta.get('role')!r})"
        assert meta.get("category") == "content", f"{slug}: category != content ({meta.get('category')!r})"
        assert meta.get("name") == slug, f"{slug}: frontmatter name mismatch ({meta.get('name')!r})"


def test_maxturns_per_inspector(agent_md_loader):
    expected = {
        "ins-factcheck": "10",
        "ins-narrative-quality": "3",
        "ins-korean-naturalness": "3",
    }
    for slug, want in expected.items():
        meta, _ = agent_md_loader(str(CONTENT_ROOT / slug / "AGENT.md"))
        got = meta.get("maxTurns")
        assert got == want, f"{slug}: maxTurns expected {want!r}, got {got!r}"


def test_all_have_logicqa_block_with_5_sub_qs(agent_md_loader):
    for slug in EXPECTED_AGENTS:
        _, body = agent_md_loader(str(CONTENT_ROOT / slug / "AGENT.md"))
        assert "LogicQA" in body, f"{slug}: LogicQA section missing"
        assert "<sub_qs>" in body, f"{slug}: <sub_qs> block missing"
        # Count q1..q5 markers present
        for qn in ("q1:", "q2:", "q3:", "q4:", "q5:"):
            assert qn in body, f"{slug}: sub-question {qn} missing from LogicQA block"


def test_narrative_quality_body_contains_content01_hook_keywords(agent_md_loader):
    _, body = agent_md_loader(str(CONTENT_ROOT / "ins-narrative-quality/AGENT.md"))
    assert "3초 hook" in body, "ins-narrative-quality: '3초 hook' keyword missing"
    assert "질문형" in body, "ins-narrative-quality: '질문형' keyword missing"
    assert ("숫자" in body) or ("고유명사" in body), (
        "ins-narrative-quality: neither '숫자' nor '고유명사' keyword present"
    )
    # Both should actually be there per plan requirement
    assert "숫자" in body and "고유명사" in body, (
        "ins-narrative-quality: both '숫자' and '고유명사' expected (CONTENT-01)"
    )


def test_factcheck_body_contains_citation_and_source_grounded_or_notebooklm(agent_md_loader):
    _, body = agent_md_loader(str(CONTENT_ROOT / "ins-factcheck/AGENT.md"))
    assert "citation" in body.lower(), "ins-factcheck: 'citation' keyword missing"
    assert ("source-grounded" in body.lower()) or ("NotebookLM" in body) or ("notebooklm" in body.lower()), (
        "ins-factcheck: neither 'source-grounded' nor 'NotebookLM' keyword present (CONTENT-04)"
    )


def test_korean_naturalness_body_contains_hao_and_haeyo_regex_chars(agent_md_loader):
    _, body = agent_md_loader(str(CONTENT_ROOT / "ins-korean-naturalness/AGENT.md"))
    # 하오체 markers (any of)
    hao_markers = ["하오", "이오", "구려", "다네"]
    hit_hao = [m for m in hao_markers if m in body]
    assert len(hit_hao) >= 3, (
        f"ins-korean-naturalness: 하오체 regex bank insufficient "
        f"(matched {len(hit_hao)}/{len(hao_markers)}: {hit_hao})"
    )
    # 해요체 markers (any of)
    hae_markers = ["해요", "에요", "지요"]
    hit_hae = [m for m in hae_markers if m in body]
    assert len(hit_hae) >= 3, (
        f"ins-korean-naturalness: 해요체 regex bank insufficient "
        f"(matched {len(hit_hae)}/{len(hae_markers)}: {hit_hae})"
    )


def test_all_must_remember_contains_forbidden_and_producer_prompt(agent_md_loader):
    for slug in EXPECTED_AGENTS:
        _, body = agent_md_loader(str(CONTENT_ROOT / slug / "AGENT.md"))
        mr_idx = body.find("## MUST REMEMBER")
        assert mr_idx != -1, f"{slug}: MUST REMEMBER section missing"
        tail = body[mr_idx:]
        assert "창작 금지" in tail, f"{slug}: MUST REMEMBER missing '창작 금지' (RUB-02)"
        assert "producer_prompt" in tail, (
            f"{slug}: MUST REMEMBER missing 'producer_prompt' (RUB-06)"
        )
