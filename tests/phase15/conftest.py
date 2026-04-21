"""Phase 15 fixtures — reuses Phase 11 Popen mock + Phase 13 state layout.

대표님을 위한 Wave 0 test 인프라. 하류 Wave 1~6 plan 전원이 이 fixture
모듈을 import 하여 mock-based 재현 / contract 테스트 / resume 시나리오
테스트를 구성합니다.

Fixtures:
    mock_popen: MagicMock ``subprocess.Popen`` 대체 — ``communicate``
        호출이 (stdout, stderr) tuple 을 반환하는 factory.
    tmp_agent_md: 10KB+ 한국어 AGENT.md body 를 tmp_path 에 기록 후
        Path 반환. SPC-01 재현 payload.
    fake_state_dir: ``tmp_path/state/<session_id>/`` 구조 + 14 gate
        stub JSON 파일. Wave 3 UFL-01/02/03 resume 테스트 재사용.

References:
    - tests/phase11/test_invoker_stdin.py::_make_popen_mock (동일 pattern)
    - tests/phase13/conftest.py (repo_root + sys.path 보강 패턴)
    - .planning/phases/15-.../15-RESEARCH.md §Phase 13 failure evidence
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Phase 13/14 precedent — repo_root 확보 + sys.path 보강
# tests/phase15/conftest.py -> parents[2] = studios/shorts/
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# 10KB+ 한국어 AGENT.md body — SPC-01 재현 임계값 상회 payload (대표님).
# 51 chars × 200 반복 ≈ 10200 chars (cp949 인코딩 시 bytes 더 큼).
KOREAN_FILLER = "대표님이 원하시는 최고 품질의 영상 제작 지침서입니다. " * 200


@pytest.fixture
def mock_popen():
    """Factory fixture — MagicMock subprocess.Popen 대체.

    Returns:
        ``_make(stdout, stderr, returncode) -> MagicMock`` factory callable.
        테스트 측에서 rc / stdout / stderr 를 명시하여 호출합니다.
    """
    def _make(
        stdout: str = '{"ok":true}',
        stderr: str = "",
        returncode: int = 0,
    ) -> MagicMock:
        proc = MagicMock()
        proc.communicate.return_value = (stdout, stderr)
        proc.returncode = returncode
        return proc
    return _make


@pytest.fixture
def tmp_agent_md(tmp_path: Path) -> Path:
    """10KB+ 한국어 AGENT.md body — SPC-01 재현용 fixture.

    대표님 Phase 13 live smoke 에서 shorts-supervisor AGENT.md body
    (10591 chars) 가 ``--append-system-prompt`` argv 로 전달될 때
    rc=1 재현. Wave 0 에서는 path 반환만 검증 (mock-based).
    """
    agent = tmp_path / "fake_agent.md"
    agent.write_text(KOREAN_FILLER, encoding="utf-8")
    assert len(agent.read_text(encoding="utf-8")) >= 10_000, (
        "fixture 가 10KB 미달 (대표님) — KOREAN_FILLER 반복 수 부족"
    )
    return agent


@pytest.fixture
def fake_state_dir(tmp_path: Path) -> Path:
    """state/<sid>/ with gate_00..gate_13 stubs — UFL-01/02/03 재사용.

    Wave 3 revision 시나리오에서 특정 ``gate_N.json`` 삭제 후
    ``Checkpointer.resume`` 이 N-1 로 되돌아가는지 테스트하기 위한
    사전 상태 구축. 14 개 operational gate (TREND..MONITOR)
    verdict=PASS stub.
    """
    sid = "fake_session_20260422"
    state = tmp_path / "state" / sid
    state.mkdir(parents=True)
    for idx in range(14):
        (state / f"gate_{idx:02d}.json").write_text(
            json.dumps({"gate": f"G{idx}", "verdict": "PASS"}),
            encoding="utf-8",
        )
    return state
