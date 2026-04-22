"""Phase 16-04 W1-MODELS — SourcesManifest Pydantic 계약 상세 검증.

output/<episode>/sources/ 디렉토리 의 manifest shape 강제:
  - scene_sources_count >= 5 (Pitfall 5)
  - real_ratio [0.0, 1.0]
  - veo_supplement_count <= 2 (feedback_veo_supplementary_only)
  - signature_reuse_count <= 2
  - outro_signature Optional (Plan 16-03 Option A 프로그램적 outro)
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from scripts.orchestrator.api.models import SourcesManifest


def _base() -> dict:
    return {
        "character_detective": "output/ep/sources/character_detective.png",
        "character_assistant": "output/ep/sources/character_assistant.png",
        "intro_signature": "output/ep/sources/intro_signature.mp4",
        "outro_signature": None,
        "scene_sources": [
            "output/ep/sources/b01.jpg",
            "output/ep/sources/b02.jpg",
            "output/ep/sources/b03.jpg",
            "output/ep/sources/b04.jpg",
            "output/ep/sources/b05.jpg",
        ],
        "scene_sources_count": 5,
        "real_image_count": 4,
        "veo_supplement_count": 1,
        "signature_reuse_count": 1,
        "real_ratio": 0.8,
    }


def test_sources_manifest_happy_path() -> None:
    """정상 케이스: scene_sources=5, real_ratio=0.8, outro_signature=None."""
    m = SourcesManifest.model_validate(_base())
    assert m.scene_sources_count == 5
    assert m.real_ratio == 0.8
    assert m.outro_signature is None


def test_scene_sources_under_5_fails() -> None:
    """scene_sources 4개 → ValidationError (Pitfall 5 min_length=5)."""
    bad = _base()
    bad["scene_sources"] = bad["scene_sources"][:4]
    bad["scene_sources_count"] = 4
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)


def test_scene_sources_count_under_5_fails_even_if_list_ok() -> None:
    """scene_sources_count=4 (ge=5 위반) → ValidationError."""
    bad = _base()
    bad["scene_sources_count"] = 4
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)


def test_real_ratio_over_1_fails() -> None:
    """real_ratio=1.5 → ValidationError (le=1.0)."""
    bad = _base()
    bad["real_ratio"] = 1.5
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)


def test_real_ratio_negative_fails() -> None:
    """real_ratio=-0.1 → ValidationError (ge=0.0)."""
    bad = _base()
    bad["real_ratio"] = -0.1
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)


def test_veo_supplement_over_2_fails() -> None:
    """veo_supplement_count=3 → ValidationError (le=2, feedback_veo_supplementary_only)."""
    bad = _base()
    bad["veo_supplement_count"] = 3
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)


def test_signature_reuse_over_2_fails() -> None:
    """signature_reuse_count=3 → ValidationError (le=2, intro+outro max)."""
    bad = _base()
    bad["signature_reuse_count"] = 3
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)


def test_outro_signature_optional_none_accepted() -> None:
    """outro_signature=None 명시적 허용 (Plan 16-03 Option A 프로그램적 outro)."""
    m = SourcesManifest.model_validate(_base())
    assert m.outro_signature is None


def test_outro_signature_string_accepted() -> None:
    """outro_signature='path/to/outro.mp4' 도 허용."""
    d = _base()
    d["outro_signature"] = "output/ep/sources/outro_signature.mp4"
    m = SourcesManifest.model_validate(d)
    assert m.outro_signature == "output/ep/sources/outro_signature.mp4"


def test_extra_field_forbidden() -> None:
    """model_config extra='forbid' 확인."""
    bad = _base()
    bad["unknown_field"] = "nope"
    with pytest.raises(ValidationError):
        SourcesManifest.model_validate(bad)
