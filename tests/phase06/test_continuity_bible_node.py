"""WIKI-02: channel_identity.md contains all 5 D-10 components textually.

Plan 02 Task 2 authors wiki/continuity_bible/channel_identity.md with the
D-10 canonical 5 구성요소 (a) through (e). This test file greps the
file contents and asserts every required textual anchor is present so
downstream Plan 06 pydantic serialization and Plan 03/04/05 NotebookLM
upload both reference the same single-source-of-truth.
"""
from __future__ import annotations
import re
from pathlib import Path


def test_channel_identity_contains_d10_header(repo_root: Path):
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    assert "5 구성요소" in text, "D-10 '5 구성요소' literal header missing"


def test_channel_identity_contains_all_five_subsections(repo_root: Path):
    """D-10 (a) through (e) all present as ### headers."""
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    for letter in ["(a)", "(b)", "(c)", "(d)", "(e)"]:
        pattern = re.compile(rf"^### {re.escape(letter)}", re.MULTILINE)
        assert pattern.search(text), f"D-10 subsection {letter} missing"


def test_channel_identity_color_palette_has_hex_values(repo_root: Path):
    """D-10 (a) requires HEX 3-5 colors."""
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    hex_matches = re.findall(r"#[0-9A-Fa-f]{6}", text)
    assert len(hex_matches) >= 3, f"D-10 (a) needs >=3 HEX colors, found {len(hex_matches)}"
    assert len(hex_matches) <= 10, f"Suspiciously many HEX values ({len(hex_matches)})"


def test_channel_identity_lens_has_focal_length(repo_root: Path):
    """D-10 (b) requires focal length in mm."""
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    assert re.search(r"\b\d{2,3}\s*mm\b", text), "D-10 (b) focal length mm missing"


def test_channel_identity_visual_style_locked(repo_root: Path):
    """D-10 (c) requires one of [photorealistic, cinematic, documentary] locked."""
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    assert any(s in text for s in ["photorealistic", "cinematic", "documentary"]), (
        "D-10 (c) visual_style literal missing"
    )


def test_channel_identity_korean_senior_audience(repo_root: Path):
    """D-10 (d) requires Korean senior audience descriptor (D-16)."""
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    assert "시니어" in text or "50-65" in text, "D-10 (d) Korean senior audience context missing"


def test_channel_identity_bgm_mood_presets(repo_root: Path):
    """D-10 (e) requires all 3 BGM presets: ambient, tension, uplift."""
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    text = p.read_text(encoding="utf-8")
    for preset in ["ambient", "tension", "uplift"]:
        assert preset in text, f"D-10 (e) preset '{preset}' missing"


def test_channel_identity_source_notebook_is_channel_bible(repo_root: Path):
    """source_notebook should point at naberal-shorts-channel-bible (D-4/D-8)."""
    from scripts.wiki.frontmatter import parse_frontmatter
    p = repo_root / "wiki" / "continuity_bible" / "channel_identity.md"
    fm = parse_frontmatter(p)
    assert fm["source_notebook"] == "naberal-shorts-channel-bible", (
        f"continuity_bible node must source from channel-bible notebook (D-4), got {fm['source_notebook']}"
    )
