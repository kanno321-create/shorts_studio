"""Phase 16-04 W1-MODELS TDD — VisualSpec / ClipDesign / TitleKeyword Pydantic 계약.

RED first: VisualSpec/ClipDesign/TitleKeyword 가 models.py 에 추가되기 전에는 import FAIL 로 red.
GREEN: models.py 에 4 class 추가 후 전수 green.

REQ-PROD-INT-04 (VisualSpec schema) + REQ-PROD-INT-06 (visual_spec_builder).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

# 본 import 는 W1-MODELS GREEN 이후에만 성공한다.
from scripts.orchestrator.api.models import (
    ClipDesign,
    SourcesManifest,
    TitleKeyword,
    VisualSpec,
)


# ─────────────────────────────────────────────────────────────────────────────
# TDD 9 tests — W1-MODELS acceptance
# ─────────────────────────────────────────────────────────────────────────────


class TestVisualSpecModel:
    """REQ-PROD-INT-04 — VisualSpec Pydantic v2 모델 계약 검증."""

    def test_visual_spec_valid(self, zodiac_visual_spec: dict) -> None:
        """1) zodiac-killer baseline 을 그대로 VisualSpec.model_validate 시 성공."""
        spec = VisualSpec.model_validate(zodiac_visual_spec)
        assert spec.channelName == "사건기록부"
        assert spec.accentColor == "#FF2200"
        assert spec.fontFamily == "BlackHanSans"
        assert spec.characterLeftSrc.endswith("character_assistant.png")
        assert spec.characterRightSrc.endswith("character_detective.png")
        assert len(spec.clips) >= 1

    def test_visual_spec_forbid_extra(self, zodiac_visual_spec: dict) -> None:
        """2) extra='forbid' — extraneous_field 추가 시 ValidationError."""
        polluted = dict(zodiac_visual_spec)
        polluted["extraneous_field"] = "should_fail"
        with pytest.raises(ValidationError):
            VisualSpec.model_validate(polluted)

    def test_font_family_enum(self, zodiac_visual_spec: dict) -> None:
        """6) fontFamily Literal — Pretendard 금지 (Literal[BlackHanSans/DoHyeon/NotoSansKR])."""
        bad = dict(zodiac_visual_spec)
        bad["fontFamily"] = "Pretendard"
        with pytest.raises(ValidationError):
            VisualSpec.model_validate(bad)

    def test_character_path_assertion_left(self, zodiac_visual_spec: dict) -> None:
        """7a) characterLeftSrc 가 character_assistant.png 로 끝나지 않으면 ValidationError (Q4 좌=조수)."""
        bad = dict(zodiac_visual_spec)
        bad["characterLeftSrc"] = "zodiac-killer/some_other.png"
        with pytest.raises(ValidationError):
            VisualSpec.model_validate(bad)

    def test_character_path_assertion_right(self, zodiac_visual_spec: dict) -> None:
        """7b) characterRightSrc 가 character_detective.png 로 끝나지 않으면 ValidationError (Q4 우=탐정)."""
        bad = dict(zodiac_visual_spec)
        bad["characterRightSrc"] = "zodiac-killer/villain.png"
        with pytest.raises(ValidationError):
            VisualSpec.model_validate(bad)


class TestClipDesignModel:
    """ClipDesign Pydantic v2 계약 — Pitfall 4 (movement None) + Pitfall 6 (int only)."""

    def test_clip_design_movement_none(self) -> None:
        """3) ClipDesign(movement=None) — 명시적 freeze 유효."""
        c = ClipDesign(
            type="image",
            src="x.jpg",
            durationInFrames=132,
            transition="fade",
            movement=None,
        )
        assert c.movement is None
        assert c.durationInFrames == 132

    def test_clip_design_duration_int_only(self) -> None:
        """4) durationInFrames 가 float (132.5) 일 때 ValidationError — Pitfall 6."""
        with pytest.raises(ValidationError):
            ClipDesign(
                type="image",
                src="x.jpg",
                durationInFrames=132.5,  # float 금지
                transition="fade",
            )


class TestTitleKeywordModel:
    """TitleKeyword Pydantic 계약 — HEX color 형식 검증."""

    def test_title_keyword_color_hex(self) -> None:
        """5) TitleKeyword(color='FF2200') — # prefix 없으면 ValidationError."""
        with pytest.raises(ValidationError):
            TitleKeyword(text="미제", color="FF2200")  # # missing

    def test_title_keyword_color_valid(self) -> None:
        """5b) 정상 케이스 — #RRGGBB 형식 통과."""
        t = TitleKeyword(text="살인마", color="#FF2200")
        assert t.color == "#FF2200"


class TestSourcesManifestModel:
    """SourcesManifest 계약 — Pitfall 5 (scene_sources ≥ 5) + real_ratio 범위."""

    _BASE = {
        "character_detective": "output/x/sources/character_detective.png",
        "character_assistant": "output/x/sources/character_assistant.png",
        "intro_signature": "output/x/sources/intro_signature.mp4",
        "outro_signature": None,
        "scene_sources": [
            "output/x/sources/broll01.jpg",
            "output/x/sources/broll02.jpg",
            "output/x/sources/broll03.jpg",
            "output/x/sources/broll04.jpg",
            "output/x/sources/broll05.jpg",
        ],
        "scene_sources_count": 5,
        "real_image_count": 4,
        "veo_supplement_count": 1,
        "signature_reuse_count": 1,
        "real_ratio": 0.8,
    }

    def test_sources_manifest_min_5_scene(self) -> None:
        """8) scene_sources 가 4개 (< 5) 일 때 ValidationError — Pitfall 5."""
        bad = dict(self._BASE)
        bad["scene_sources"] = bad["scene_sources"][:4]
        bad["scene_sources_count"] = 4
        with pytest.raises(ValidationError):
            SourcesManifest.model_validate(bad)

    def test_sources_manifest_real_ratio_range(self) -> None:
        """9) real_ratio=1.5 ValidationError (0.0~1.0 범위)."""
        bad = dict(self._BASE)
        bad["real_ratio"] = 1.5
        with pytest.raises(ValidationError):
            SourcesManifest.model_validate(bad)

    def test_sources_manifest_valid(self) -> None:
        """정상 케이스 — 5 scene sources, real_ratio 0.8."""
        m = SourcesManifest.model_validate(self._BASE)
        assert m.scene_sources_count == 5
        assert m.real_ratio == 0.8
        assert m.outro_signature is None  # Option A 프로그램적 outro


# ─────────────────────────────────────────────────────────────────────────────
# W1-BUILDER smoke — build() 호출 3 시나리오 (모델 Layer 에서 접근 가능한 조합만)
# ─────────────────────────────────────────────────────────────────────────────


class TestVisualSpecBuilder:
    """W1-BUILDER smoke — build() import + override path + 최소 입력."""

    def test_builder_import(self) -> None:
        """visual_spec_builder 모듈 import 가능."""
        from scripts.orchestrator.api import visual_spec_builder

        assert hasattr(visual_spec_builder, "build")
        assert hasattr(visual_spec_builder, "load_channel_preset")
        assert hasattr(visual_spec_builder, "VisualSpecBuildError")

    def test_builder_override_path(self, zodiac_visual_spec: dict) -> None:
        """build(visual_spec_override=zodiac-killer baseline) — 우회 경로 통과."""
        from scripts.orchestrator.api.visual_spec_builder import build

        result = build(
            blueprint={},
            script={},
            channel_preset={},
            sources_manifest={},
            audio_duration_s=112.83,
            episode_id="zodiac-killer",
            visual_spec_override=zodiac_visual_spec,
        )
        assert isinstance(result, VisualSpec)
        assert result.channelName == "사건기록부"

    def test_builder_minimum_blueprint(self) -> None:
        """build() — blueprint + 최소 sources_manifest 로 VisualSpec 생성."""
        from scripts.orchestrator.api.visual_spec_builder import build

        blueprint = {
            "title_display": {
                "line1": "50년 미제",
                "line2": "암호 살인마",
                "accent_words": ["미제", "살인마"],
                "accent_color": "#FF2200",
            },
        }
        script = {"title": "제목"}
        channel_preset = {
            "channelName": "사건기록부",
            "accentColor": "#FF2200",
            "fontFamily": "BlackHanSans",
            "subtitlePosition": 0.8,
            "subtitleHighlightColor": "#FFFFFF",
            "subtitleFontSize": 68,
            "hashtags_default": "#쇼츠 #범죄",
        }
        sources_manifest = {
            "scene_sources": [f"zodiac-killer/b{i}.jpg" for i in range(1, 6)],
            "intro_signature": "zodiac-killer/intro_signature.mp4",
            "outro_signature": None,
        }
        result = build(
            blueprint=blueprint,
            script=script,
            channel_preset=channel_preset,
            sources_manifest=sources_manifest,
            audio_duration_s=60.0,
            episode_id="zodiac-killer",
        )
        assert isinstance(result, VisualSpec)
        assert result.titleLine1 == "50년 미제"
        assert result.titleLine2 == "암호 살인마"
        assert result.accentColor == "#FF2200"
        assert result.durationInFrames == 1800  # 60*30
        assert len(result.clips) >= 6  # intro + 5 scenes (outro None)


# ─────────────────────────────────────────────────────────────────────────────
# 추가 안전장치 — JSON Schema 와 Pydantic 동기화 확인
# ─────────────────────────────────────────────────────────────────────────────


def test_json_schema_file_exists(repo_root: Path) -> None:
    """JSON Schema 파일이 실제 존재."""
    p = (
        repo_root
        / ".planning"
        / "phases"
        / "16-production-integration-option-a"
        / "schemas"
        / "visual-spec.v1.schema.json"
    )
    assert p.exists(), f"visual-spec.v1.schema.json 미존재: {p}"
    schema = json.loads(p.read_text(encoding="utf-8"))
    assert schema["$schema"].startswith("http://json-schema.org/draft-07")
    assert schema["additionalProperties"] is False


def test_pydantic_and_schema_both_accept_baseline(
    zodiac_visual_spec: dict, repo_root: Path
) -> None:
    """zodiac-killer baseline 이 Pydantic + JSON Schema 양쪽 통과."""
    import jsonschema

    schema_path = (
        repo_root
        / ".planning"
        / "phases"
        / "16-production-integration-option-a"
        / "schemas"
        / "visual-spec.v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(zodiac_visual_spec, schema)
    VisualSpec.model_validate(zodiac_visual_spec)
