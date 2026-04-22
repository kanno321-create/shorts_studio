"""Phase 16 — shared pytest fixtures.

Phase 16 실행 (Remotion / faster-whisper / visual_spec / channel bible imprint)
테스트 모듈이 공용으로 사용하는 fixture. Phase 9.1 conftest 패턴 차용.

Exposes 4 fixtures:
    harvest_root          — `.preserved/harvested/` 루트 Path (읽기 전용 전제)
    zodiac_visual_spec    — baseline_specs_raw/zodiac-killer/visual_spec.json dict
    memory_dir            — `.claude/memory/` 루트 Path
    repo_root             — 레포지토리 루트 Path

Design:
    - session-scoped (변경 없음, I/O 최소)
    - UTF-8 safeguard (Windows cp949 방지, phase091 precedent)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# UTF-8 safeguard for Windows cp949 per Phase 6/9.1 precedent.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# tests/phase16/conftest.py -> parents[2] = studios/shorts/
REPO_ROOT = Path(__file__).resolve().parents[2]
HARVEST_ROOT = REPO_ROOT / ".preserved" / "harvested"
MEMORY_ROOT = REPO_ROOT / ".claude" / "memory"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root (studios/shorts/)."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def harvest_root() -> Path:
    """`.preserved/harvested/` root — read-only harvest SSOT.

    Phase 3 HARVEST 단계 이후 chmod -w / attrib +R 처리됨. 본 fixture 는
    테스트가 harvested 원본을 READ 만 수행함을 전제 (CLAUDE.md 금기 #6).
    """
    assert HARVEST_ROOT.exists(), (
        f".preserved/harvested/ 미존재: {HARVEST_ROOT} — Phase 3 HARVEST 재실행 필요"
    )
    return HARVEST_ROOT


@pytest.fixture(scope="session")
def zodiac_visual_spec(harvest_root: Path) -> dict:
    """zodiac-killer baseline visual_spec.json 로드 (read-only).

    Phase 16-04 Wave 0 W0-SCHEMAS 가 이 baseline 대비 jsonschema 검증 수행.
    """
    path = harvest_root / "baseline_specs_raw" / "zodiac-killer" / "visual_spec.json"
    assert path.exists(), f"baseline visual_spec 미존재: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def memory_dir() -> Path:
    """`.claude/memory/` root — Plan 16-01 박제 메모리 전수 위치."""
    assert MEMORY_ROOT.exists(), f".claude/memory/ 미존재: {MEMORY_ROOT}"
    return MEMORY_ROOT
