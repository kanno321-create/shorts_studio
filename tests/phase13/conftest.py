"""Phase 13 공용 pytest fixtures — tests/phase13/ 전체가 재사용.

Tier 2 (``@pytest.mark.live_smoke``) 테스트는 ``--run-live`` CLI flag 없이
실행 시 자동 skip — 실 API 과금 방지 (CLAUDE.md 금기 #8 일일 업로드 배제).
pytest 표준 hook (``pytest_addoption`` + ``pytest_collection_modifyitems``)
은 Phase 14 에서 적용된 적 없는 신규 패턴 — Phase 13 live_smoke 특유 요구.

Phase 14 ``tests/adapters/conftest.py`` 의 ``repo_root`` + sys.path 패턴을
승계.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Phase 5/14 precedent — repo_root 확보 + sys.path 보강.
# tests/phase13/conftest.py -> parents[2] = studios/shorts/
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def pytest_addoption(parser):
    """Add ``--run-live`` flag to enable live_smoke tier (Phase 13 opt-in)."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help=(
            "Run live_smoke-marked tests (Phase 13 Tier 2). "
            "실 API 과금 — 대표님 승인 후 1회만 사용."
        ),
    )


def pytest_collection_modifyitems(config, items):
    """Skip ``live_smoke`` tests unless ``--run-live`` is explicitly passed.

    Wave 0~5 default invocation 에서 실 과금 trigger 를 구조적으로 차단.
    CLAUDE.md 금기 #8 (일일 업로드 금지) 및 $5 cap 사전 방어선.
    """
    if config.getoption("--run-live"):
        return
    skip_live = pytest.mark.skip(reason="--run-live 미지정 — Tier 2 skipped")
    for item in items:
        if "live_smoke" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Phase 14 conftest 와 동일 계약 — studios/shorts/ 루트."""
    return REPO_ROOT


@pytest.fixture
def tmp_evidence_dir(tmp_path, monkeypatch):
    """Temporary evidence dir + ``SHORTS_PUBLISH_LOCK_PATH`` override.

    Wave 2/4 live 테스트가 ``.planning/phases/13-*/evidence/`` 대신 tmp 를
    쓰도록 유도 — 실제 evidence dir 에 테스트 fixture 오염 방지.
    publish_lock 또한 tmp 경로로 redirect — 실 48h+ 카운터 소진 차단
    (RESEARCH §Pitfall 5 + Phase 8 D-06 override 계약).
    """
    evidence = tmp_path / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    lock_path = tmp_path / "phase13_smoke_lock.json"
    monkeypatch.setenv("SHORTS_PUBLISH_LOCK_PATH", str(lock_path))
    return evidence


@pytest.fixture
def fixtures_dir() -> Path:
    """``tests/phase13/fixtures/`` 경로 — golden JSON 4종."""
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fake_claude_cli_output():
    """Mock producer JSON output — schema 검증용 최소 페이로드.

    Wave 1/4 의 evidence-shape 테스트가 본 fixture 를 이용하여 실제
    Claude CLI 호출 없이 producer_output 구조를 검증 가능.
    """
    return {
        "gate": "TREND",
        "verdict": "PASS",
        "decisions": [
            {"id": "D-01", "value": "k-pop 최신 앨범 이슈", "confidence": 0.9}
        ],
        "artifacts": {"producer_output": {"niche": "k-pop", "source": "reddit"}},
        "raw_response": "{'gate': 'TREND', 'verdict': 'PASS', ...}",
    }
