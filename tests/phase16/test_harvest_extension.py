"""Phase 16-03 W0-HARVEST — 바이너리 harvest 확장 검증.

5 바이너리 (1 mp4 + 4 png) + 2 README + sha256 manifest 검증.
shorts_naberal source 무결성 (read-only one-way) 확인.

Plan 16-03 Task 16-03-W0-HARVEST 검증.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HARVEST_ROOT = REPO_ROOT / ".preserved" / "harvested" / "video_pipeline_raw"
SIG_DIR = HARVEST_ROOT / "signatures"
CHAR_DIR = HARVEST_ROOT / "characters"
MANIFEST = HARVEST_ROOT / "harvest_extension_manifest.json"

SOURCE_PREFIX = Path("C:/Users/PC/Desktop/shorts_naberal/output/_shared")

EXPECTED_FILES = {
    "signatures/incidents_intro_v4_silent_glare.mp4": SOURCE_PREFIX / "signatures" / "incidents_intro_v4_silent_glare.mp4",
    "characters/incidents_detective_longform_a.png": SOURCE_PREFIX / "characters" / "incidents_detective_longform_a.png",
    "characters/incidents_detective_longform_b.png": SOURCE_PREFIX / "characters" / "incidents_detective_longform_b.png",
    "characters/incidents_assistant_jp_a.png": SOURCE_PREFIX / "characters" / "incidents_assistant_jp_a.png",
    "characters/incidents_zunda_shihtzu_a.png": SOURCE_PREFIX / "characters" / "incidents_zunda_shihtzu_a.png",
}


class TestHarvestExtensionFiles:
    """5 바이너리 파일 존재 검증."""

    def test_signatures_dir_exists(self):
        assert SIG_DIR.exists() and SIG_DIR.is_dir()

    def test_characters_dir_exists(self):
        assert CHAR_DIR.exists() and CHAR_DIR.is_dir()

    def test_intro_signature_exists(self):
        p = SIG_DIR / "incidents_intro_v4_silent_glare.mp4"
        assert p.exists(), f"intro mp4 missing: {p}"
        assert p.stat().st_size > 1_500_000, f"intro mp4 too small: {p.stat().st_size}"

    @pytest.mark.parametrize("png_name", [
        "incidents_detective_longform_a.png",
        "incidents_detective_longform_b.png",
        "incidents_assistant_jp_a.png",
        "incidents_zunda_shihtzu_a.png",
    ])
    def test_character_png_exists(self, png_name):
        p = CHAR_DIR / png_name
        assert p.exists(), f"character PNG missing: {p}"
        assert p.stat().st_size > 100_000, f"character PNG too small: {p.stat().st_size}"


class TestHarvestManifest:
    """sha256 manifest 검증."""

    def test_manifest_exists(self):
        assert MANIFEST.exists(), f"manifest missing: {MANIFEST}"

    def test_manifest_has_five_entries(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        file_entries = {k: v for k, v in data.items() if not k.startswith("_")}
        assert len(file_entries) == 5, f"expected 5 entries, got {len(file_entries)}"

    def test_manifest_entries_match_files(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for rel in EXPECTED_FILES:
            assert rel in data, f"manifest missing key: {rel}"
            assert "sha256" in data[rel], f"sha256 field missing for {rel}"
            assert "size_bytes" in data[rel], f"size_bytes field missing for {rel}"

    def test_manifest_sha256_matches_actual(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for rel, meta in data.items():
            if rel.startswith("_"):
                continue
            p = HARVEST_ROOT / rel
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            assert meta["sha256"] == actual, f"sha256 drift: {rel}"


class TestHarvestReadmes:
    """README 2 개 존재 검증."""

    def test_signatures_readme_exists(self):
        p = SIG_DIR / "README.md"
        assert p.exists() and p.stat().st_size > 500

    def test_characters_readme_exists(self):
        p = CHAR_DIR / "README.md"
        assert p.exists() and p.stat().st_size > 500

    def test_signatures_readme_mentions_veo_policy(self):
        text = (SIG_DIR / "README.md").read_text(encoding="utf-8")
        assert "Veo" in text and ("금기" in text or "forbid" in text or "재호출" in text)

    def test_characters_readme_mentions_character_layout(self):
        text = (CHAR_DIR / "README.md").read_text(encoding="utf-8")
        assert "탐정" in text and "왓슨" in text or "assistant" in text


class TestSourceIntactness:
    """CLAUDE.md 금기 #6 — shorts_naberal source 무결성.

    source 파일이 존재하면 sha256 비교, 없으면 skip (CI 환경 대응).
    """

    @pytest.mark.parametrize("rel,src", list(EXPECTED_FILES.items()))
    def test_source_sha256_unchanged(self, rel, src):
        if not src.exists():
            pytest.skip(f"source not available (CI / detached env): {src}")
        dst = HARVEST_ROOT / rel
        if not dst.exists():
            pytest.skip(f"harvest dst missing (earlier test caught): {dst}")
        src_hash = hashlib.sha256(src.read_bytes()).hexdigest()
        dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()
        assert src_hash == dst_hash, f"source != harvest copy: {rel}"
