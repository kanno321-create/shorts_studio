"""Phase 16-03 — CLAUDE.md forbid-11 강제: Veo API 재호출 0건 검증.

Phase 16 는 기존 Veo 자산 (incidents_intro_v4_silent_glare.mp4) 을
**재사용만** 허용. scripts/orchestrator/ 및 remotion/ 트리 안에
VeoClient / veo_i2v.generate / 'import .*veo' 호출이 0건이어야 한다.

강화된 grep: Veo 3.1 Lite / veo3.1 / google.veo 등 변종 포함.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SIG_MP4 = REPO_ROOT / ".preserved" / "harvested" / "video_pipeline_raw" / "signatures" / "incidents_intro_v4_silent_glare.mp4"

# 검사 대상 디렉토리 (Phase 16 scope)
SCAN_PATHS = [
    REPO_ROOT / "scripts" / "orchestrator" / "subtitle",
    REPO_ROOT / "scripts" / "orchestrator" / "api" / "subtitle_producer.py",
    REPO_ROOT / "scripts" / "orchestrator" / "api" / "remotion_renderer.py",
    REPO_ROOT / "remotion" / "src",
]

# Veo 금지 패턴 (변종 포함)
VEO_FORBIDDEN_PATTERNS = [
    r"VeoClient",
    r"veo_i2v\.generate",
    r"veo_generate",
    r"\bimport\s+veo\b",
    r"\bfrom\s+veo\b",
    r"veo3\.1",
    r"google\.veo",
    r"veo_api\.",
    r"veo\.generate",
]


class TestSignatureReuseAssetPresent:
    """Intro signature 자산이 재사용 가능한 위치에 존재."""

    def test_incidents_intro_v4_present(self):
        assert SIG_MP4.exists(), f"intro signature missing: {SIG_MP4}"
        assert SIG_MP4.stat().st_size > 1_500_000, "intro signature mp4 too small"


class TestNoVeoCallsInPhase16Scope:
    """Phase 16 code scope 에서 Veo API 호출 0건 검증."""

    def _collect_files(self) -> list[Path]:
        files: list[Path] = []
        for p in SCAN_PATHS:
            if not p.exists():
                continue
            if p.is_file():
                if p.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".json"):
                    files.append(p)
            else:
                for ext in ("*.py", "*.ts", "*.tsx"):
                    files.extend(p.rglob(ext))
        return files

    @pytest.mark.parametrize("pattern", VEO_FORBIDDEN_PATTERNS)
    def test_no_veo_pattern_match(self, pattern):
        """각 금지 패턴에 대해 전수 파일 grep → 0 matches."""
        files = self._collect_files()
        assert files, "no files scanned — check SCAN_PATHS"

        matches: list[str] = []
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for m in re.finditer(pattern, text):
                line_no = text[: m.start()].count("\n") + 1
                matches.append(f"{f}:{line_no}: {text.splitlines()[line_no-1][:100]}")

        assert not matches, (
            f"Veo 금지 패턴 '{pattern}' 감지 ({len(matches)}건) — CLAUDE.md forbid-11 위반:\n"
            + "\n".join(matches[:10])
        )

    def test_subtitle_module_has_no_veo_import(self):
        """scripts/orchestrator/subtitle/ 전체에 veo import 없음."""
        sub_dir = REPO_ROOT / "scripts" / "orchestrator" / "subtitle"
        assert sub_dir.exists()
        for py in sub_dir.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace").lower()
            assert "import veo" not in text, f"{py}: veo import 검출"
            assert "from veo" not in text, f"{py}: veo module import 검출"

    def test_remotion_src_has_no_veo_reference(self):
        """remotion/src 내 tsx 파일 전수에 Veo 참조 없음."""
        rem_src = REPO_ROOT / "remotion" / "src"
        if not rem_src.exists():
            pytest.skip("remotion/src missing")
        for tsx in rem_src.rglob("*.tsx"):
            text = tsx.read_text(encoding="utf-8", errors="replace")
            # OutroCard.tsx 는 outro_signature.mp4 언급 OK (legacy context)
            # 하지만 Veo API 호출/import 는 금지
            assert "VeoClient" not in text, f"{tsx}: VeoClient 검출"
            assert "veo_i2v" not in text, f"{tsx}: veo_i2v 검출"


class TestOutroCardProgrammaticNoMp4(pytest.__class__ if False else object):
    """OutroCard.tsx 는 외부 mp4 의존 없는 프로그램적 구현이어야 함."""

    def test_outro_card_has_no_staticfile_mp4(self):
        p = REPO_ROOT / "remotion" / "src" / "components" / "OutroCard.tsx"
        assert p.exists()
        text = p.read_text(encoding="utf-8")
        # OffthreadVideo 나 outro_signature.mp4 staticFile 호출 없음 (프로그램적)
        assert "OffthreadVideo" not in text, "OutroCard 에 OffthreadVideo 사용됨"
        assert "outro_signature" not in text, "OutroCard 에 outro_signature 언급됨"

    def test_outro_card_uses_remotion_primitives(self):
        p = REPO_ROOT / "remotion" / "src" / "components" / "OutroCard.tsx"
        text = p.read_text(encoding="utf-8")
        # 프로그램적 Remotion 컴포넌트: AbsoluteFill + interpolate/spring
        assert "AbsoluteFill" in text
        assert "interpolate" in text or "spring" in text


class TestHarvestManifestVeoPolicyNote:
    """harvest_extension_manifest.json 에 Veo policy 언급 있음."""

    def test_manifest_mentions_veo_policy(self):
        import json
        p = REPO_ROOT / ".preserved" / "harvested" / "video_pipeline_raw" / "harvest_extension_manifest.json"
        assert p.exists()
        data = json.loads(p.read_text(encoding="utf-8"))
        meta = data.get("_metadata", {})
        veo_policy = str(meta.get("veo_policy", ""))
        assert "Veo" in veo_policy or "veo" in veo_policy or "forbid" in veo_policy.lower()
