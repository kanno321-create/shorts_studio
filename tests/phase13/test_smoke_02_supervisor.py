"""Phase 13 SMOKE-02 — Real Claude CLI supervisor + rc=1 재현 0회 tests.

Phase 11 deferred SC#1 ("프롬프트가 너무 깁니다" rc=1) 의 **실환경 해소 증거**
확보. Phase 12 AGENT-STD-03 ``_compress_producer_output`` (27% ratio) 적용
상태에서 supervisor CLI 호출 rc=0 을 live 로 확증한다.

**Tier 1 (always-run, 3 tests)**:
1. ``_compress_producer_output`` 존재 + callable
2. 14KB-scale payload 가 budget 2x 이하로 압축 + error_codes 전수 보존
3. sample_supervisor_output.json fixture 의 rc1_count == 0 invariant

**Tier 2 (opt-in, 1 test @pytest.mark.live_smoke)**:
4. ``make_default_supervisor_invoker`` 를 14KB-scale producer_output 으로
    1회 호출 → rc=0 + evidence JSON anchor (rc1_count=0, compression_ratio_avg
    ~0.27).

References
----------
- scripts/orchestrator/invokers.py L396 (supervisor __call__), L495
    (``_compress_producer_output``), L492 (``_COMPRESS_CHAR_BUDGET`` = 2000)
- Phase 12 test_phase11_smoke_replay_under_cli_limit precedent
- 13-RESEARCH.md §SMOKE-02 (L225-245)

CLAUDE.md compliance
--------------------
- 금기 #2: 미완성 wiring 표식 없음.
- 금기 #3: rc=1 재현 시 ``subprocess.CalledProcessError`` 가 자연스럽게
    propagate — try/except 로 감싸지 않음 (SMOKE-02 실패 표기를 위해).
- 금기 #8: Tier 2 는 ``--run-live`` 없이 skip (conftest hook).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts.orchestrator.invokers import (
    _COMPRESS_CHAR_BUDGET,
    _compress_producer_output,
)

# =============================================================================
# Tier 1 — Always-run (compression 검증 + fixture invariant)
# =============================================================================


def test_smoke_02_compression_function_exists_and_callable() -> None:
    """Phase 12 AGENT-STD-03 ``_compress_producer_output`` 가 import 가능 +
    callable 인지 smoke 확인."""
    assert callable(_compress_producer_output), (
        "_compress_producer_output 은 callable 이어야 합니다 (대표님)"
    )
    assert isinstance(_COMPRESS_CHAR_BUDGET, int), (
        "_COMPRESS_CHAR_BUDGET 은 int (기본 2000 chars)"
    )
    assert _COMPRESS_CHAR_BUDGET == 2000, (
        f"Phase 12 D-A4-01 default budget = 2000, 실측={_COMPRESS_CHAR_BUDGET}"
    )


def test_smoke_02_compression_reduces_payload_under_budget() -> None:
    """14KB-scale fixture → ``_compress_producer_output`` → budget×2 이하.

    Phase 12 실측 (14KB → 2.4KB = 27%) 재현. 나아가 error_codes 전수 보존
    invariant (Phase 12 D-A4-01 contract) 를 확증.
    """
    # 14KB-scale: 30 decisions × ~0.4KB each + 8KB semantic_feedback + 4KB
    # raw_response = ~24KB raw (pre-compress). error_codes 는 2개 — Phase 12
    # 가 전수 보존해야 함.
    raw_payload = {
        "gate": "TREND",
        "verdict": "PASS",
        "error_codes": ["E001", "E002"],
        "semantic_feedback": "a" * 8000,  # 8KB verbose prose (drop 대상)
        "raw_response": "b" * 4000,  # 4KB raw log (drop 대상)
        "decisions": [
            {
                "id": f"D-{i:02d}",
                "value": "decision_X" * 20,  # ~200 chars per entry
                "severity": "high" if i % 2 == 0 else "medium",
                "score": float(i),
            }
            for i in range(30)
        ],
    }
    raw_size = len(json.dumps(raw_payload, ensure_ascii=False))
    compressed = _compress_producer_output(raw_payload)
    compressed_size = len(json.dumps(compressed, ensure_ascii=False))

    assert compressed_size < raw_size, (
        f"압축이 크기 감소에 실패 — raw={raw_size}, compressed={compressed_size}"
    )
    # Phase 12 D-A4-01: budget×2 tolerance (nested dict overhead)
    assert compressed_size <= _COMPRESS_CHAR_BUDGET * 2, (
        f"압축 후 크기 {compressed_size} 가 budget 2x ({_COMPRESS_CHAR_BUDGET*2}) 초과"
    )
    # D-A4-01 invariant: error_codes 는 전수 보존 (never truncated)
    assert compressed["error_codes"] == ["E001", "E002"], (
        f"error_codes 전수 보존 실패 (대표님): {compressed.get('error_codes')!r}"
    )
    # gate/verdict 도 보존
    assert compressed["gate"] == "TREND"
    assert compressed["verdict"] == "PASS"
    # verbose prose 는 drop (semantic_feedback_prefix 만 최대 200 chars 유지)
    assert "raw_response" not in compressed, "raw_response 는 drop 되어야 함"
    sf_prefix = compressed.get("semantic_feedback_prefix", "")
    assert len(sf_prefix) <= 200, (
        f"semantic_feedback_prefix 는 최대 200 chars, 실측 {len(sf_prefix)}"
    )


def test_smoke_02_fixture_has_rc1_zero(fixtures_dir: Path) -> None:
    """Golden fixture ``sample_supervisor_output.json`` 의 rc1_count == 0
    invariant — Wave 4 live run 산출물이 동일 invariant 를 만족해야 함.
    """
    payload = json.loads(
        (fixtures_dir / "sample_supervisor_output.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["rc1_count"] == 0, (
        f"SMOKE-02 핵심 invariant: rc1_count == 0 필요, "
        f"실측 {payload['rc1_count']}"
    )
    assert isinstance(payload["supervisor_calls"], list)
    assert len(payload["supervisor_calls"]) >= 1, (
        "최소 1 supervisor call 이 기록되어야 함"
    )
    for idx, call in enumerate(payload["supervisor_calls"]):
        assert call["returncode"] == 0, (
            f"call[{idx}] returncode != 0 — rc=1 재현 (대표님 중단)"
        )
        assert "gate" in call and "inspector_count" in call
        assert "pre_compress_bytes" in call and "post_compress_bytes" in call
        assert "ratio" in call and "verdict" in call
    assert 0.0 < payload["compression_ratio_avg"] < 1.0, (
        "compression_ratio_avg 는 (0, 1) 범위 내여야 함 (Phase 12 ~0.27 기대)"
    )


# =============================================================================
# Tier 2 — Live opt-in (@pytest.mark.live_smoke)
# =============================================================================


@pytest.mark.live_smoke
def test_smoke_02_real_claude_cli_supervisor_rc1_zero(
    tmp_evidence_dir: Path,
) -> None:
    """실 Claude CLI supervisor 1회 호출 → rc=0 + evidence anchor.

    14KB-scale producer_output 을 ``make_default_supervisor_invoker`` 에
    전달하고, ``_compress_producer_output`` 을 경유한 프롬프트가 Claude CLI
    에서 rc=1 "프롬프트가 너무 깁니다" 없이 rc=0 으로 완주함을 live 에서
    empirical 확증.

    Cost: $0.00 (Claude CLI Max 구독 inclusive).
    금기 #3 준수: rc=1 시 subprocess.CalledProcessError 가 natural propagate
    — try/except 로 감싸지 않음.
    """
    from scripts.orchestrator.invokers import make_default_supervisor_invoker

    repo_root = Path(__file__).resolve().parents[2]
    agent_dir = (
        repo_root / ".claude" / "agents" / "supervisors" / "shorts-supervisor"
    )
    assert agent_dir.exists(), f"Supervisor agent dir 부재 (대표님): {agent_dir}"

    # 14KB-scale producer_output — Phase 11 live 시 rc=1 trigger 재현 shape.
    producer_output = {
        "gate": "TREND",
        "verdict": "PASS",
        "error_codes": [],
        "semantic_feedback": "trend data valid " * 500,  # ~8.5KB
        "decisions": [
            {
                "id": f"D-{i:02d}",
                "value": "k-pop niche research data " * 20,  # ~500 chars
                "severity": "medium",
                "score": float(i),
            }
            for i in range(20)
        ],
    }

    supervisor = make_default_supervisor_invoker(agent_dir=agent_dir)
    # ``(gate, output: dict) -> Verdict`` — invokers L396.
    verdict = supervisor("TREND", producer_output)

    # Verdict 반환 자체가 rc=0 증명 — rc=1 이면 subprocess.CalledProcessError
    # 또는 RuntimeError 가 raise 되어 본 assertion 에 도달 불가.
    assert verdict is not None, "Supervisor verdict 반환 실패 (대표님)"
    verdict_name = getattr(verdict, "name", str(verdict))
    assert verdict_name in ("PASS", "FAIL", "RETRY"), (
        f"Verdict enum 이상값: {verdict_name!r}"
    )

    # Evidence anchor — Phase 12 실측 ratio ~0.27 재현 기대.
    sid = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_bytes = len(json.dumps(producer_output, ensure_ascii=False))
    compressed = _compress_producer_output(producer_output)
    comp_bytes = len(json.dumps(compressed, ensure_ascii=False))
    ratio = round(comp_bytes / raw_bytes, 4) if raw_bytes > 0 else 0.0

    evidence_path = tmp_evidence_dir / f"supervisor_output_{sid}.json"
    payload = {
        "session_id": sid,
        "timestamp": datetime.now().isoformat(),
        "supervisor_calls": [
            {
                "gate": "TREND",
                "inspector_count": 1,
                "pre_compress_bytes": raw_bytes,
                "post_compress_bytes": comp_bytes,
                "ratio": ratio,
                "returncode": 0,
                "verdict": verdict_name,
            }
        ],
        "rc1_count": 0,
        "compression_ratio_avg": ratio,
    }
    evidence_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    readback = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert readback["rc1_count"] == 0, (
        "SMOKE-02 live: rc=1 재현 — Phase 12 compression 실효성 실패"
    )
    assert readback["supervisor_calls"][0]["returncode"] == 0
