"""SMOKE-05 Tier 1 evidence-shape tests — mock only, always-run.

본 테스트는 ``@pytest.mark.live_smoke`` 없이 실행되어 매 commit pytest
default 에 포함됩니다. 실 API 호출 0회.

Wave 1~4 가 공통 import 할 ``BudgetCounter`` + ``BudgetExceededError`` 계약을
검증합니다. Phase 9.1 ``_check_cost_cap`` 의 file-persisted 확장.
"""
from __future__ import annotations

import json

import pytest

from scripts.smoke.budget_counter import BudgetCounter, BudgetExceededError


def test_initial_state(tmp_path):
    """Test 1 — 초기 상태 확인 (cap, total=0, entries=[])."""
    counter = BudgetCounter(cap_usd=5.00, evidence_path=tmp_path / "budget.json")
    assert counter.cap_usd == 5.00
    assert counter.total_usd == 0.0
    assert counter.entries == []


def test_charge_records_entry_with_timestamp(tmp_path):
    """Test 2 — charge 가 provider/amount/cumulative/timestamp 를 기록."""
    counter = BudgetCounter(cap_usd=5.00, evidence_path=tmp_path / "budget.json")
    counter.charge("kling", 0.35)
    assert counter.total_usd == 0.35
    assert len(counter.entries) == 1
    entry = counter.entries[0]
    assert entry["provider"] == "kling"
    assert entry["amount_usd"] == 0.35
    assert entry["cumulative_usd"] == 0.35
    assert "timestamp" in entry
    # ISO8601 sanity — datetime.isoformat 는 'T' 구분자 포함
    assert "T" in entry["timestamp"]


def test_charge_overage_raises_and_preserves_state(tmp_path):
    """Test 3 — 초과 시 BudgetExceededError + atomic (부분 entry 금지)."""
    counter = BudgetCounter(cap_usd=5.00, evidence_path=tmp_path / "budget.json")
    counter.charge("kling", 4.99)
    with pytest.raises(BudgetExceededError) as exc_info:
        counter.charge("runway", 0.02)
    msg = str(exc_info.value)
    assert "5.00" in msg
    assert "runway" in msg
    assert "대표님" in msg
    # Atomic — 초과 호출은 append 되지 않음
    assert len(counter.entries) == 1
    assert counter.total_usd == 4.99


def test_zero_cost_claude_cli_entry_allowed(tmp_path):
    """Test 4 — $0.00 ledger 항목 허용 (Research Q#4 — Max 구독).

    Claude CLI 호출은 Max 구독 inclusive 이므로 $0 이지만 ledger 완전성을
    위해 entry 는 기록해야 한다.
    """
    counter = BudgetCounter(cap_usd=5.00, evidence_path=tmp_path / "budget.json")
    counter.charge("claude_cli", 0.00, metadata={"note": "Max subscription"})
    assert counter.total_usd == 0.0
    assert counter.entries[0]["provider"] == "claude_cli"
    assert counter.entries[0]["amount_usd"] == 0.0
    assert counter.entries[0]["metadata"] == {"note": "Max subscription"}


def test_persist_writes_valid_json(tmp_path):
    """Test 5 — persist 가 5 key + Korean-readable JSON 을 write."""
    evidence_path = tmp_path / "budget.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence_path)
    counter.charge("kling", 0.35, metadata={"설명": "I2V 5초 클립"})
    counter.charge("typecast", 0.12)
    result_path = counter.persist()
    assert result_path == evidence_path
    assert evidence_path.exists()
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    for key in ("cap_usd", "total_usd", "breached", "entry_count", "entries"):
        assert key in payload
    assert payload["entry_count"] == 2
    assert payload["breached"] is False
    # ensure_ascii=False — Korean metadata readable
    raw_text = evidence_path.read_text(encoding="utf-8")
    assert "설명" in raw_text


def test_metadata_dict_preserved(tmp_path):
    """Test 6 — metadata dict round-trips."""
    counter = BudgetCounter(cap_usd=5.00, evidence_path=tmp_path / "budget.json")
    counter.charge("typecast", 0.12, metadata={"chars": 1000, "voice": "ko-KR-Female"})
    assert counter.entries[-1]["metadata"]["chars"] == 1000
    assert counter.entries[-1]["metadata"]["voice"] == "ko-KR-Female"
