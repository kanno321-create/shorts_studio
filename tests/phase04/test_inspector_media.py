"""Phase 4 Plan 04-07 — Media Inspector compliance tests.

Verifies:
- Exactly 2 AGENT.md under .claude/agents/inspectors/media/
- Each frontmatter: role=inspector, category=media, maxTurns=3
- Each Inspector variant prompt contains LogicQA with 5 sub_qs
- ins-mosaic body contains AF-5 + 실존 피해자 + blur/mosaic + ≥5 Korean press domain blocklist
- ins-gore body contains 유혈 + 절단 + 흉기 + ≥15 blacklist keywords
- All MUST REMEMBER at END of body (validator already enforces, but we assert header present)
- Each body contains 창작 금지 + producer_prompt (RUB-02 + RUB-06)
"""
from __future__ import annotations

import pathlib

import pytest

# Resolve repo root without relying on the function-scoped `repo_root` fixture
# (module-scoped fixtures cannot depend on function-scoped fixtures).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

MEDIA_DIR = pathlib.Path(".claude/agents/inspectors/media")

EXPECTED_SLUGS = {"ins-mosaic", "ins-gore"}

KOREAN_PRESS_DOMAINS = [
    "chosun.com",
    "joongang.co.kr",
    "donga.com",
    "hani.co.kr",
    "mbc.co.kr",
    "kbs.co.kr",
    "sbs.co.kr",
    "jtbc.co.kr",
    "news.naver.com",
    "news.daum.net",
]

GORE_BLACKLIST = [
    "피",
    "유혈",
    "절단",
    "흉기",
    "시체",
    "살해",
    "참수",
    "찌르다",
    "베다",
    "난자",
    "피투성이",
    "난도질",
    "토막",
    "훼손",
    "해체",
]


@pytest.fixture(scope="module")
def media_agents():
    """Return dict {slug: (meta, body, md_path)} for all media inspectors."""
    from scripts.validate.parse_frontmatter import parse_frontmatter

    root = _REPO_ROOT / MEDIA_DIR
    assert root.exists(), f"media inspector dir missing: {root}"
    out = {}
    for slug_dir in sorted(root.iterdir()):
        if not slug_dir.is_dir():
            continue
        md = slug_dir / "AGENT.md"
        assert md.exists(), f"AGENT.md missing under {slug_dir}"
        meta, body = parse_frontmatter(md)
        out[slug_dir.name] = (meta, body, md)
    return out


def test_exactly_two_media_inspectors(media_agents):
    assert set(media_agents.keys()) == EXPECTED_SLUGS, (
        f"expected exactly {EXPECTED_SLUGS}, got {set(media_agents.keys())}"
    )


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_frontmatter_role_category_maxturns(media_agents, slug):
    meta, _body, _md = media_agents[slug]
    assert meta.get("role") == "inspector", f"{slug} role must be inspector"
    assert meta.get("category") == "media", f"{slug} category must be media"
    # stdlib frontmatter parser returns raw strings; coerce for comparison
    assert int(meta.get("maxTurns")) == 3, (
        f"{slug} maxTurns must be 3, got {meta.get('maxTurns')!r}"
    )
    assert meta.get("name") == slug, f"{slug} name in frontmatter mismatch"


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_logicqa_5_sub_qs(media_agents, slug):
    _meta, body, _md = media_agents[slug]
    # All 5 sub_qs must be present
    for qid in ("q1:", "q2:", "q3:", "q4:", "q5:"):
        assert qid in body, f"{slug} body missing LogicQA {qid}"
    # And LogicQA block marker
    assert "LogicQA" in body, f"{slug} body missing 'LogicQA' marker"


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_rub02_rub06_markers(media_agents, slug):
    _meta, body, _md = media_agents[slug]
    assert "창작 금지" in body, f"{slug} body missing '창작 금지' (RUB-02)"
    assert "producer_prompt" in body, f"{slug} body missing 'producer_prompt' (RUB-06)"


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_must_remember_header_present(media_agents, slug):
    _meta, body, _md = media_agents[slug]
    assert "## MUST REMEMBER" in body, f"{slug} body missing '## MUST REMEMBER' section"


def test_mosaic_body_contains_af5_and_blocklist(media_agents):
    _meta, body, _md = media_agents["ins-mosaic"]
    assert "AF-5" in body
    assert "실존 피해자" in body
    assert ("blur" in body) or ("mosaic" in body.lower())
    # ≥5 Korean press domains listed (we require 5+)
    hits = [d for d in KOREAN_PRESS_DOMAINS if d in body]
    assert len(hits) >= 5, (
        f"ins-mosaic body must list ≥5 Korean press domains, found {len(hits)}: {hits}"
    )


def test_gore_body_contains_keywords_and_blacklist(media_agents):
    _meta, body, _md = media_agents["ins-gore"]
    # Required anchor keywords
    for k in ("유혈", "절단", "흉기"):
        assert k in body, f"ins-gore body missing '{k}'"
    # ≥15 blacklist keywords
    hits = [k for k in GORE_BLACKLIST if k in body]
    assert len(hits) >= 15, (
        f"ins-gore body must contain ≥15 blacklist keywords, found {len(hits)}: {hits}"
    )
    # Frequency heuristic wording
    assert ("빈도" in body) or ("frequency" in body.lower())


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_description_length_leq_1024(media_agents, slug):
    meta, _body, _md = media_agents[slug]
    desc = meta.get("description", "")
    assert len(desc) <= 1024, f"{slug} description {len(desc)} > 1024 (AGENT-08)"
    # And ≥3 trigger-keyword-ish tokens (rough: comma-split count)
    tokens = [t.strip() for t in desc.split(",") if len(t.strip()) >= 2]
    assert len(tokens) >= 3, f"{slug} description needs ≥3 trigger tokens, got {len(tokens)}"
