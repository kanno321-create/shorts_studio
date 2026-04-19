"""Wave 4 PUB-04 — HTML comment regex roundtrip compatibility.

Per Plan 08-05 Task 8-05-01 + CONTEXT D-08:
Phase 4 ins-platform-policy uses r'<!-- production_metadata\\n(\\{.*?\\})\\n-->'
(DOTALL). This test locks our injection format round-trip compatible with
that regex so Phase 9 analytics can parse every uploaded video's metadata.
"""
from __future__ import annotations

import json
import re

from scripts.publisher.production_metadata import inject_into_description


def test_html_comment_matches_ins_platform_policy_regex():
    """Phase 9 analytics regex r'<!-- production_metadata\\n(\\{.*?\\})\\n-->' DOTALL."""
    meta = {"script_seed": "s1", "assets_origin": "kling:primary",
            "pipeline_version": "1.0.0", "checksum": "sha256:abc123"}
    desc = inject_into_description("original description", meta)
    rx = re.compile(r"<!-- production_metadata\n(\{.*?\})\n-->", re.DOTALL)
    m = rx.search(desc)
    assert m is not None, f"Phase 9 analytics regex cannot parse: {desc!r}"
    parsed = json.loads(m.group(1))
    assert parsed["script_seed"] == "s1"
    assert parsed["checksum"] == "sha256:abc123"


def test_html_comment_is_last_element_of_description():
    """PUB-04 spec: metadata appended at end (Phase 9 parses from tail)."""
    desc = inject_into_description("A\nB\nC", {
        "script_seed": "s", "assets_origin": "a",
        "pipeline_version": "1.0.0", "checksum": "sha256:a",
    })
    assert desc.rstrip().endswith("-->")


def test_separators_are_compact_no_spaces():
    """separators=(',', ':') — no trailing spaces (bytes-count conservative)."""
    desc = inject_into_description("", {
        "script_seed": "s", "assets_origin": "a",
        "pipeline_version": "1.0.0", "checksum": "sha256:a",
    })
    assert '", "' not in desc
    assert '": "' not in desc
    assert '":"' in desc


def test_multiple_injections_do_not_duplicate_brackets():
    """Idempotency not required, but must not malform JSON."""
    meta = {"script_seed": "s", "assets_origin": "a",
            "pipeline_version": "1.0.0", "checksum": "sha256:a"}
    once = inject_into_description("d", meta)
    twice = inject_into_description(once, meta)
    assert len(re.findall(r"<!-- production_metadata", twice)) == 2


def test_original_description_text_preserved_exactly():
    """PUB-04: description body unchanged — only append at tail."""
    original = "Line 1\nLine 2\nLine 3 with 한국어"
    meta = {"script_seed": "s", "assets_origin": "a",
            "pipeline_version": "1.0.0", "checksum": "sha256:a"}
    out = inject_into_description(original, meta)
    assert out.startswith(original)


def test_roundtrip_json_parses_without_error():
    meta = {"script_seed": "seed_007", "assets_origin": "runway:fallback",
            "pipeline_version": "1.0.0",
            "checksum": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    desc = inject_into_description("desc", meta)
    rx = re.compile(r"<!-- production_metadata\n(\{.*?\})\n-->", re.DOTALL)
    parsed = json.loads(rx.search(desc).group(1))
    assert parsed == meta
