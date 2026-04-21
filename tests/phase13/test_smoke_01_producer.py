"""Phase 13 SMOKE-01 — Real Claude CLI producer 호출 + evidence anchor tests.

**Tier 1 (always-run, 3 tests)**: evidence extractor shape + fixture schema
invariants. 실 Claude CLI 호출 없음 — fake checkpoint 파일을 tmp_path 에
생성하고 extract_producer_output 이 producer_gates 를 올바르게 집계하는지
검증.

**Tier 2 (opt-in via --run-live, 1 test)**: ``make_default_producer_invoker``
를 실 Claude CLI Max 구독으로 1회 호출 후 `evidence/producer_output_*.json`
파일 write + schema 준수 검증. --run-live flag 없이 자동 skip (conftest
pytest_collection_modifyitems).

References
----------
- 13-RESEARCH.md §SMOKE-01 (L190-223) — evidence shape
- scripts/smoke/evidence_extractor.py (Task 13-02-01)
- scripts/orchestrator/invokers.py L334 — producer __call__ signature
    ``(agent_name: str, gate: str, inputs: dict) -> dict``

CLAUDE.md compliance
--------------------
- 금기 #2: 미완성 wiring 표식 없음 — 모든 branch 완성.
- 금기 #3: Tier 2 실패 시 pytest 가 rc≠0 로 전파 — try/except 로 감싸지
    않음 (SMOKE-01 deferred 표기를 위해).
- 금기 #8: @pytest.mark.live_smoke 미지정 테스트는 실 CLI 호출 금지 —
    Tier 1 은 fake checkpoint + tmp_path 만 사용.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts.smoke.evidence_extractor import (
    OPERATIONAL_GATES,
    extract_producer_output,
)

# =============================================================================
# Tier 1 — Always-run (fake checkpoint + fixture schema)
# =============================================================================


def test_smoke_01_fixture_has_required_keys(fixtures_dir: Path) -> None:
    """Golden fixture ``sample_producer_output.json`` invariants — 4 keys.

    Wave 4 Full E2E 가 생성할 evidence JSON 이 동일 shape 를 따라야 함을
    본 test 가 baseline 으로 강제한다.
    """
    payload = json.loads(
        (fixtures_dir / "sample_producer_output.json").read_text(encoding="utf-8")
    )
    assert "session_id" in payload, "fixture 필수 key 'session_id' 누락"
    assert "timestamp" in payload, "fixture 필수 key 'timestamp' 누락"
    assert isinstance(payload["producer_gates"], dict), (
        "producer_gates 는 dict 여야 합니다 (gate→output mapping)"
    )
    assert "TREND" in payload["producer_gates"], (
        "SMOKE-01: 최소 TREND gate 는 producer_output 포함해야 함"
    )


def test_smoke_01_extractor_handles_missing_state_dir(
    tmp_path: Path, tmp_evidence_dir: Path
) -> None:
    """존재하지 않는 session_id → empty producer_gates + 파일 생성 (graceful).

    Phase 11 precedent: state/<sid>/ 부재는 pre-billing abort 시 정상 상태 —
    evidence JSON 은 빈 produces_gates 로라도 생성되어야 downstream
    aggregator 가 missing-file 로 헷갈리지 않음.
    """
    out_path = extract_producer_output(
        session_id="does_not_exist_sid",
        state_root=tmp_path / "state",
        evidence_dir=tmp_evidence_dir,
    )
    assert out_path.exists(), "evidence JSON 파일이 생성되어야 합니다"
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["producer_gates"] == {}, (
        "session_dir 부재 시 producer_gates 는 빈 dict 여야 함"
    )
    assert payload["gate_count_with_producer"] == 0
    assert payload["session_id"] == "does_not_exist_sid"


def test_smoke_01_extractor_aggregates_real_checkpoints(
    tmp_path: Path, tmp_evidence_dir: Path
) -> None:
    """Fake ``state/<sid>/gate_01.json`` 작성 → TREND producer_output 집계 검증.

    Wave 4 live run 이 checkpointer artifacts 에 ``producer_output`` 을
    기록했을 때 extract_producer_output 이 올바르게 수집하는 계약을
    검증한다.
    """
    sid = "20260421_test_smoke01"
    state_root = tmp_path / "state"
    session_dir = state_root / sid
    session_dir.mkdir(parents=True)
    # Checkpointer payload shape (gate_guard.dispatch L157-164) — artifacts 에
    # Wave 4 live wiring 이 producer_output 을 추가하는 것을 simulate.
    fake_cp = {
        "_schema": "gate_state_v1",
        "session_id": sid,
        "gate": "TREND",
        "gate_index": 1,
        "timestamp": datetime.now().isoformat(),
        "verdict": {"result": "PASS", "evidence": []},
        "artifacts": {
            "path": "output/trend.json",
            "sha256": "sha256:deadbeef",
            "producer_output": {
                "niche": "k-pop",
                "source": "reddit",
                "confidence": 0.91,
            },
        },
    }
    (session_dir / "gate_01.json").write_text(
        json.dumps(fake_cp, ensure_ascii=False), encoding="utf-8"
    )

    out_path = extract_producer_output(
        session_id=sid,
        state_root=state_root,
        evidence_dir=tmp_evidence_dir,
    )
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["gate_count_with_producer"] == 1
    assert "TREND" in payload["producer_gates"]
    assert payload["producer_gates"]["TREND"]["niche"] == "k-pop"
    assert payload["producer_gates"]["TREND"]["confidence"] == 0.91
    # 13 operational gate 계약 재확인 (정확히 13)
    assert len(OPERATIONAL_GATES) == 13


# =============================================================================
# Tier 2 — Live opt-in (@pytest.mark.live_smoke, skipped without --run-live)
# =============================================================================


@pytest.mark.live_smoke
def test_smoke_01_real_claude_cli_producer_call_and_anchor(
    tmp_evidence_dir: Path,
) -> None:
    """실 Claude CLI Max 구독으로 producer 1회 호출 → evidence anchor.

    Wave 4 Full E2E 가 trigger 하여 SMOKE-01 "producer_output evidence 실존
    + shape 준수" 를 empirical 확증. --run-live flag 없이 conftest 가
    자동 skip.

    Cost: $0.00 (Claude CLI Max 구독 inclusive —
    project_claude_code_max_no_api_key.md)
    Retry: max 3 (invokers.py _MAX_NUDGE_ATTEMPTS) — retry 정책 Research
    Open Q#2.
    """
    # Lazy import — Tier 1 collection 시 agent_dir 경로 의존성 부재로도
    # collection 실패 방지.
    from scripts.orchestrator.invokers import make_default_producer_invoker

    repo_root = Path(__file__).resolve().parents[2]
    agent_dir_root = repo_root / ".claude" / "agents" / "producers"
    assert agent_dir_root.exists(), (
        f"Producer agent root 부재 (대표님): {agent_dir_root}"
    )

    producer = make_default_producer_invoker(agent_dir_root=agent_dir_root)
    # ``(agent_name: str, gate: str, inputs: dict) -> dict`` — invokers L334.
    result = producer(
        agent_name="trend-collector",
        gate="TREND",
        inputs={"seed_topic": "Phase 13 SMOKE-01 liveness ping (대표님)"},
    )
    assert isinstance(result, dict), "Producer 반환은 dict 여야 합니다"
    # Producer JSON 필수 필드 — schema 는 agent 별 다양하므로 느슨한 체크.
    assert any(k in result for k in ("verdict", "gate", "decisions", "artifacts")), (
        f"Producer 응답에 최소 하나의 표준 필드 필요: {list(result.keys())}"
    )

    # Evidence anchor — tmp_evidence_dir 에 write (실제 .planning evidence/
    # 경로는 Wave 5 Phase Gate 가 명시 copy).
    sid = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_path = tmp_evidence_dir / f"producer_output_{sid}.json"
    payload = {
        "session_id": sid,
        "timestamp": datetime.now().isoformat(),
        "producer_gates": {"TREND": result},
        "gate_count_with_producer": 1,
    }
    evidence_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    assert evidence_path.exists(), "evidence JSON write 실패"

    readback = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert "TREND" in readback["producer_gates"], (
        "SMOKE-01 live anchor: TREND gate 누락"
    )
    assert readback["gate_count_with_producer"] == 1
