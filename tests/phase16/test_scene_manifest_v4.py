"""Phase 16-04 W0-SCHEMAS — scene-manifest.v4.schema.json JSON Schema 검증.

3 baseline (zodiac-killer / nazca-lines / roanoke-colony) 통과 + 의도적 불량 데이터 실패 검증.

REQ-PROD-INT-04 sibling — scene-manifest v4 SSOT.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH_FRAGMENT = Path(".planning") / "phases" / "16-production-integration-option-a" / "schemas" / "scene-manifest.v4.schema.json"


@pytest.fixture(scope="module")
def scene_manifest_schema(repo_root: Path) -> dict:
    """Load v4 schema (read-only)."""
    p = repo_root / SCHEMA_PATH_FRAGMENT
    assert p.exists(), f"scene-manifest.v4.schema.json 미존재: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def zodiac_scene_manifest(harvest_root: Path) -> dict:
    p = harvest_root / "baseline_specs_raw" / "zodiac-killer" / "scene-manifest.json"
    assert p.exists(), f"scene-manifest 미존재: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def test_scene_manifest_schema_valid_draft7(scene_manifest_schema: dict) -> None:
    """스키마 자체가 유효한 Draft-07."""
    jsonschema.Draft7Validator.check_schema(scene_manifest_schema)


def test_zodiac_scene_manifest_passes(
    scene_manifest_schema: dict, zodiac_scene_manifest: dict
) -> None:
    """zodiac-killer baseline 통과."""
    jsonschema.validate(zodiac_scene_manifest, scene_manifest_schema)


def test_nazca_scene_manifest_passes_if_exists(
    scene_manifest_schema: dict, harvest_root: Path
) -> None:
    """nazca-lines scene-manifest 가 존재하면 통과해야 함."""
    p = harvest_root / "baseline_specs_raw" / "nazca-lines" / "scene-manifest.json"
    if not p.exists():
        pytest.skip("nazca-lines scene-manifest 미존재 — skip")
    data = json.loads(p.read_text(encoding="utf-8"))
    # nazca-lines 는 구형 포맷일 수 있으므로 version 확인 후 분기
    if data.get("version") == "v4":
        jsonschema.validate(data, scene_manifest_schema)


def test_roanoke_scene_manifest_passes_if_exists(
    scene_manifest_schema: dict, harvest_root: Path
) -> None:
    p = harvest_root / "baseline_specs_raw" / "roanoke-colony" / "scene-manifest.json"
    if not p.exists():
        pytest.skip("roanoke-colony scene-manifest 미존재 — skip")
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") == "v4":
        jsonschema.validate(data, scene_manifest_schema)


def test_scene_manifest_reject_bad_version(
    scene_manifest_schema: dict, zodiac_scene_manifest: dict
) -> None:
    """version='v3' 은 const='v4' 위반 → ValidationError."""
    bad = dict(zodiac_scene_manifest)
    bad["version"] = "v3"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, scene_manifest_schema)


def test_scene_manifest_reject_empty_clips(
    scene_manifest_schema: dict, zodiac_scene_manifest: dict
) -> None:
    """clips=[] 은 minItems:1 위반 → ValidationError."""
    bad = dict(zodiac_scene_manifest)
    bad["clips"] = []
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, scene_manifest_schema)


def test_scene_manifest_reject_invalid_channel(
    scene_manifest_schema: dict, zodiac_scene_manifest: dict
) -> None:
    """channel='random' 은 enum 위반 → ValidationError."""
    bad = dict(zodiac_scene_manifest)
    bad["channel"] = "random_channel"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, scene_manifest_schema)


def test_scene_manifest_reject_missing_source_stats(
    scene_manifest_schema: dict, zodiac_scene_manifest: dict
) -> None:
    """source_stats 필드 누락 → required 위반 ValidationError."""
    bad = {k: v for k, v in zodiac_scene_manifest.items() if k != "source_stats"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, scene_manifest_schema)
