"""SMOKE-05 Tier 1 Budget Enforcement — mock adapter, 실 API 0회.

Wave 4 Full E2E 가 수행할 실 live run (``budget_usage.json`` 기록) 이전에
``BudgetCounter`` + ``scripts.smoke.provider_rates`` 조합의 enforcement 논리를
regression suite 에 anchor. 모든 charge 는 시뮬레이션 숫자 — 실제 Kling /
Typecast / Runway API 호출 없음 (비용 $0.00).

본 파일의 7 테스트 전수 Tier 1 (always-run, ``--run-live`` 불필요). Tier 2
(실 API) 는 Wave 4 Plan 13-05 ``phase13_live_smoke.py`` 가 별도 파일에서
``@pytest.mark.live_smoke`` 으로 관리 — 본 파일은 ``live_smoke`` marker 를
부착하지 않음 (13-04-PLAN.md acceptance_criteria 최종 조건).

CLAUDE.md 금기 #3 (try/except 침묵 폴백) 및 필수 #8 (증거 기반 보고) 를
모든 assertion 에 명시적 메시지로 적용 — 대표님 보고 시 실패 원인 추적 가능.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.smoke.budget_counter import BudgetCounter, BudgetExceededError
from scripts.smoke.provider_rates import (
    PROVIDER_RATES_USD,
    all_known_providers,
    estimate_adapter_cost,
)


# ---------------------------------------------------------------------------
# Test 1: under-cap accumulation — cumulative + entries monotonic
# ---------------------------------------------------------------------------
def test_under_cap_accumulates_correctly(tmp_path: Path) -> None:
    """Typecast $0.12 + Kling $0.35 + Nanobanana $0.04 순차 charge.

    - total_usd == 0.51 (round(..., 4) 적용)
    - entries 3건 + cumulative_usd monotonic increase
    - provider string round-trip
    """
    evidence = tmp_path / "evidence" / "budget_usage.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence)

    counter.charge("typecast", 0.12, metadata={"chars": 1000})
    counter.charge("kling", 0.35, metadata={"cut_index": 0})
    counter.charge("nanobanana", 0.04, metadata={"image_index": 0})

    assert counter.total_usd == 0.51, (
        f"누적 합계 불일치: expected $0.51, actual ${counter.total_usd}"
    )
    assert len(counter.entries) == 3, (
        f"entries 수 불일치: expected 3, actual {len(counter.entries)}"
    )
    # cumulative_usd 단조증가 검증 (Research §SMOKE-05 ledger 계약)
    cumulative = [e["cumulative_usd"] for e in counter.entries]
    assert cumulative == sorted(cumulative), (
        f"cumulative_usd 단조성 위반: {cumulative}"
    )
    # provider round-trip
    assert [e["provider"] for e in counter.entries] == [
        "typecast", "kling", "nanobanana",
    ], "provider 순서 불일치"


# ---------------------------------------------------------------------------
# Test 2: overage — BudgetExceededError + atomic ledger (실패 entry 미추가)
# ---------------------------------------------------------------------------
def test_cap_overage_raises_and_atomic(tmp_path: Path) -> None:
    """$4.99 상태에서 runway $0.02 추가 → BudgetExceededError + atomic.

    Wave 0 BudgetCounter 계약 검증:
      - charge 내부에서 projected > cap_usd 이면 raise BEFORE entries.append
      - counter.total_usd 는 실패 charge 직전 상태 유지 ($4.99)
      - error message 에 \"5.00\" + \"runway\" + \"대표님\" 포함
    """
    evidence = tmp_path / "evidence" / "budget_usage.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence)

    counter.charge("kling", 4.99, metadata={"seed": "pre-overage"})
    assert counter.total_usd == 4.99, f"선행 상태 불일치: {counter.total_usd}"
    assert len(counter.entries) == 1

    # Overage attempt — atomic raise 전 entries 미변경 보장
    with pytest.raises(BudgetExceededError) as exc_info:
        counter.charge("runway", 0.02, metadata={"note": "overage trigger"})

    msg = str(exc_info.value)
    assert "5.00" in msg, f"error msg 에 cap '5.00' 누락: {msg}"
    assert "runway" in msg, f"error msg 에 provider 'runway' 누락: {msg}"
    assert "대표님" in msg, f"error msg 에 '대표님' 존댓말 baseline 누락: {msg}"

    # Atomic invariant — 실패한 runway charge 가 entries 에 append 되면 안 됨
    assert counter.total_usd == 4.99, (
        f"atomic 위반 — 실패 charge 후 total drift: {counter.total_usd}"
    )
    assert len(counter.entries) == 1, (
        f"atomic 위반 — 실패 charge 가 entries 에 추가됨: {len(counter.entries)}"
    )
    assert counter.entries[0]["provider"] == "kling", (
        "atomic 위반 — 기존 kling entry 손상"
    )


# ---------------------------------------------------------------------------
# Test 3: claude_cli $0.00 ledger entry allowed (Max 구독 완결성)
# ---------------------------------------------------------------------------
def test_zero_cost_claude_cli_ledger_entry_allowed(tmp_path: Path) -> None:
    """Max 구독 inclusive 인 claude_cli 의 $0.00 charge 도 ledger 에 기록.

    Research Open Q #4 채택 — 과금액이 $0 이어도 entry 를 추가하여 어떤
    adapter 가 몇 번 호출되었는지 감사 가능 (필수 #8 증거 기반).
    """
    evidence = tmp_path / "evidence" / "budget_usage.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence)

    counter.charge(
        "claude_cli",
        0.00,
        metadata={"reason": "Max 구독 — 비과금 엔트리 (대표님 감사 trail)"},
    )

    assert len(counter.entries) == 1, "$0 claude_cli entry 미추가"
    entry = counter.entries[0]
    assert entry["provider"] == "claude_cli"
    assert entry["amount_usd"] == 0.0, (
        f"$0 entry amount_usd 오류: {entry['amount_usd']}"
    )
    assert entry["cumulative_usd"] == 0.0, (
        f"$0 entry cumulative_usd 오류: {entry['cumulative_usd']}"
    )
    # metadata round-trip (한국어 포함)
    assert "Max 구독" in entry["metadata"]["reason"]
    assert "대표님" in entry["metadata"]["reason"]
    assert counter.total_usd == 0.0


# ---------------------------------------------------------------------------
# Test 4: full-run simulation (Research §SMOKE-05 expected scenario)
# ---------------------------------------------------------------------------
def test_full_run_simulation_under_cap(tmp_path: Path) -> None:
    """Research §SMOKE-05 expected scenario — nanobanana 1 + kling 8 + typecast 1.

    - 총액 = $0.04 + ($0.35 × 8) + $0.12 = $2.96
    - Research Expected total $1.50~$3.00 범위 내
    - entries 10개 (1 + 8 + 1)
    """
    evidence = tmp_path / "evidence" / "budget_usage.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence)

    # Thumbnail 1 image
    counter.charge("nanobanana", estimate_adapter_cost("nanobanana", 1))
    # 8 Kling 5s cuts
    for cut_index in range(8):
        counter.charge(
            "kling",
            estimate_adapter_cost("kling", 1),
            metadata={"cut_index": cut_index},
        )
    # Typecast 1 voiceover (1K chars)
    counter.charge("typecast", estimate_adapter_cost("typecast", 1))

    assert counter.total_usd == 2.96, (
        f"expected scenario 총액 불일치: expected $2.96, actual "
        f"${counter.total_usd}"
    )
    assert 1.50 <= counter.total_usd <= 3.00, (
        f"Research Expected total 범위 이탈: ${counter.total_usd} "
        f"(기대 $1.50~$3.00)"
    )
    assert counter.total_usd < 5.00, "cap 침범"
    assert len(counter.entries) == 10, (
        f"entries 수 불일치: expected 10, actual {len(counter.entries)}"
    )


# ---------------------------------------------------------------------------
# Test 5: persist evidence schema — 5 top-level keys + 5 entry keys
# ---------------------------------------------------------------------------
def test_persist_evidence_shape_5_keys(tmp_path: Path) -> None:
    """``counter.persist()`` JSON schema (Wave 4 Plan 06 이 재사용할 계약).

    - Top-level keys: cap_usd, total_usd, breached, entry_count, entries
    - Each entry: timestamp, provider, amount_usd, cumulative_usd, metadata
    """
    evidence = tmp_path / "evidence" / "budget_usage.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence)

    counter.charge("kling", 0.35, metadata={"cut_index": 0})
    counter.charge("typecast", 0.12, metadata={"chars": 1000})

    persisted_path = counter.persist()
    assert persisted_path == evidence
    assert evidence.exists(), f"evidence file 미생성: {evidence}"

    payload = json.loads(evidence.read_text(encoding="utf-8"))

    # Top-level 5 keys
    expected_top_keys = {
        "cap_usd", "total_usd", "breached", "entry_count", "entries",
    }
    assert set(payload.keys()) == expected_top_keys, (
        f"top-level keys 불일치: expected {expected_top_keys}, "
        f"actual {set(payload.keys())}"
    )
    assert payload["cap_usd"] == 5.00
    assert payload["total_usd"] == 0.47
    assert payload["breached"] is False
    assert payload["entry_count"] == 2
    assert len(payload["entries"]) == 2

    # Each entry: 5 keys
    expected_entry_keys = {
        "timestamp", "provider", "amount_usd", "cumulative_usd", "metadata",
    }
    for idx, entry in enumerate(payload["entries"]):
        assert set(entry.keys()) == expected_entry_keys, (
            f"entry[{idx}] keys 불일치: expected {expected_entry_keys}, "
            f"actual {set(entry.keys())}"
        )


# ---------------------------------------------------------------------------
# Test 6: provider_rates integration — counter + rates SSOT 연동
# ---------------------------------------------------------------------------
def test_provider_rates_integration(tmp_path: Path) -> None:
    """``counter.charge("kling", estimate_adapter_cost("kling", 8))`` = $2.80.

    Wave 4 ``phase13_live_smoke.py`` 가 사용할 import 경로 정합성 확인.
    """
    evidence = tmp_path / "evidence" / "budget_usage.json"
    counter = BudgetCounter(cap_usd=5.00, evidence_path=evidence)

    # rates SSOT 에서 꺼낸 값으로 직접 charge
    kling_cost = estimate_adapter_cost("kling", 8)
    assert kling_cost == 2.80, (
        f"estimate_adapter_cost('kling', 8) 오류: expected $2.80, "
        f"actual ${kling_cost}"
    )
    counter.charge("kling", kling_cost, metadata={"cuts": 8})

    assert counter.total_usd == 2.80
    assert counter.entries[0]["amount_usd"] == 2.80
    assert counter.entries[0]["provider"] == "kling"

    # PROVIDER_RATES_USD 8 key invariant (Wave 4 가 의존)
    known = all_known_providers()
    assert len(known) >= 8, f"rates table 키 수 부족: {known}"
    assert "claude_cli" in known, "claude_cli rates entry 누락 (Max 구독 완결성)"
    assert PROVIDER_RATES_USD["claude_cli"] == 0.00, (
        f"claude_cli 단가 drift: {PROVIDER_RATES_USD['claude_cli']}"
    )
    # Wave 4 가 의존하는 8 adapter 전수 존재
    for required in (
        "claude_cli", "notebooklm", "youtube_api",
        "nanobanana", "kling", "runway", "typecast", "elevenlabs",
    ):
        assert required in PROVIDER_RATES_USD, (
            f"required adapter '{required}' rates table 누락"
        )


# ---------------------------------------------------------------------------
# Test 7: unknown provider → KeyError (금기 #3 silent fallback 방지)
# ---------------------------------------------------------------------------
def test_unknown_provider_in_rates_raises_keyerror() -> None:
    """``estimate_adapter_cost("fake_provider")`` → KeyError.

    CLAUDE.md 금기 #3 (try/except 침묵 폴백) 직접 검증 — silent $0 fallback
    이 반환되면 오타 provider (e.g. \"klin\") 가 $0 로 기록되어 실 과금
    drift 를 은폐. 본 test 가 GREEN 이어야만 Wave 4 가 안전하게 rates
    SSOT 를 사용 가능.
    """
    with pytest.raises(KeyError) as exc_info:
        estimate_adapter_cost("fake_provider")
    assert "fake_provider" in str(exc_info.value), (
        f"KeyError message 에 provider 이름 누락: {exc_info.value}"
    )

    # 오타 시나리오도 동일하게 KeyError
    with pytest.raises(KeyError):
        estimate_adapter_cost("klin")  # "kling" 오타

    # 대소문자 민감 — "Kling" 도 미등록으로 간주 (grep 가능성 보장)
    with pytest.raises(KeyError):
        estimate_adapter_cost("Kling")
