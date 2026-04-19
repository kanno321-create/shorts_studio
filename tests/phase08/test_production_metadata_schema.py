"""Wave 4 PUB-04 — 4-field schema + checksum contract.

Per Plan 08-05 Task 8-05-01 + CONTEXT D-08 + RESEARCH §Pattern 5:
- ProductionMetadata TypedDict has exactly 4 fields: {script_seed,
  assets_origin, pipeline_version, checksum}. These match the Phase 4
  ins-platform-policy enforcement contract. Any rename or field drift
  breaks the Phase 9 analytics regex r'<!-- production_metadata\\n(\\{.*?\\})\\n-->'.
- PIPELINE_VERSION = "1.0.0" is the Phase 8 shipping version.
- compute_checksum streams the mp4 in 64KB chunks (memory-safe for
  the 10-30MB Shorts case + future-proof for larger files).
- inject_into_description appends a single HTML comment block at end
  of the description with ensure_ascii=False so Korean roundtrips.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.publisher.production_metadata import (
    PIPELINE_VERSION,
    ProductionMetadata,
    compute_checksum,
    inject_into_description,
)


def test_pipeline_version_is_1_0_0():
    assert PIPELINE_VERSION == "1.0.0"


def test_production_metadata_typed_dict_has_four_keys():
    keys = set(ProductionMetadata.__annotations__.keys())
    assert keys == {"script_seed", "assets_origin", "pipeline_version", "checksum"}, (
        f"PUB-04 4-field invariant broken: {keys}"
    )


def test_compute_checksum_streams_1_byte_file(sample_mp4_path):
    result = compute_checksum(sample_mp4_path)
    # sha256 of b"0" = '5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9'
    assert result == "sha256:5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"


def test_compute_checksum_10mb_file_streams_correctly(tmp_path):
    big = tmp_path / "big.mp4"
    big.write_bytes(b"x" * (10 * 1024 * 1024))
    result = compute_checksum(big)
    expected = hashlib.sha256(b"x" * (10 * 1024 * 1024)).hexdigest()
    assert result == f"sha256:{expected}"


def test_compute_checksum_returns_sha256_prefix():
    """Format: 'sha256:<64-hex>' — the prefix is load-bearing for audit logs."""
    from pathlib import Path as _P
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
        tf.write(b"abc")
        tf_path = _P(tf.name)
    try:
        result = compute_checksum(tf_path)
        assert result.startswith("sha256:")
        assert len(result.removeprefix("sha256:")) == 64
    finally:
        tf_path.unlink()


def test_inject_into_description_appends_html_comment():
    meta = {"script_seed": "s1", "assets_origin": "kling:primary",
            "pipeline_version": "1.0.0", "checksum": "sha256:abc"}
    out = inject_into_description("desc", meta)
    assert out.startswith("desc\n<!-- production_metadata\n")
    assert out.endswith("\n-->")
    assert '"script_seed":"s1"' in out


def test_inject_into_description_preserves_korean():
    meta = {"script_seed": "미제사건_ep7", "assets_origin": "kling:primary",
            "pipeline_version": "1.0.0", "checksum": "sha256:abc"}
    out = inject_into_description("설명", meta)
    assert "미제사건_ep7" in out, "ensure_ascii=False must preserve Korean"
    assert "설명" in out


def test_inject_rejects_missing_fields():
    with pytest.raises(ValueError) as exc_info:
        inject_into_description("desc", {"script_seed": "s"})
    assert "PUB-04 schema violation" in str(exc_info.value)
    assert "assets_origin" in str(exc_info.value)


def test_inject_rejects_three_of_four_fields():
    with pytest.raises(ValueError):
        inject_into_description("desc", {
            "script_seed": "s", "assets_origin": "a", "pipeline_version": "1.0.0",
        })   # missing checksum
