"""Phase 13 Plan 05 Task 02 — SMOKE-06 Tier 1 smoke_e2e fixture invariants.

Tier 1 전용 (live_smoke marker 미부착 — 실 API 호출 0회). 대표님, 본 테스트는
Wave 4 ``phase13_live_smoke.py`` 가 live run 에서 생성할 ``smoke_e2e_<sid>.json``
의 shape 을 golden fixture (``tests/phase13/fixtures/sample_smoke_e2e.json``)
에 대해 선제적으로 lock — runner 가 반드시 따라야 할 evidence 계약.

검증 invariants:
    1. 13 operational gate timestamps 존재 (CLAUDE.md §Pipeline 1:1)
    2. final_video_id non-empty string
    3. total_cost_usd ≤ budget_cap_usd (SMOKE-05 cap)
    4. budget_cap_usd == 5.00 (Phase 13 SC#5 hard lock)
    5. budget_breached is False
    6. supervisor_rc1_count == 0 (Phase 12 AGENT-STD-03 compression 성과)
    7. status == "OK" + wall_time_seconds > 0
    8. filename regex 계약 — ``smoke_e2e_<YYYYMMDD>_<HHMMSS>.json``

금기 #2: 미완성 wiring 표식 없음 — 모든 test 완성 + assertion 구체적.
필수 #7: 한국어 존댓말 baseline — assertion 메시지에 "대표님" 포함.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def test_smoke_e2e_fixture_has_13_gate_timestamps(fixtures_dir: Path) -> None:
    """Invariant 1 — 13 operational gate + IDLE/COMPLETE bookend 존재 (≥13).

    sample_smoke_e2e.json 의 gate_timestamps dict 는 Research §SMOKE-06
    Full E2E Example (13-RESEARCH.md L340-358) 에 따라 IDLE + 12 operational
    + COMPLETE = 14 entry 이거나 13 operational 만. fixture 현재 shape 은
    13 entry (IDLE + 11 operational + COMPLETE) — ``gate_count`` 필드 는
    정확히 13 으로 고정.
    """
    payload = json.loads(
        (fixtures_dir / "sample_smoke_e2e.json").read_text(encoding="utf-8")
    )
    assert payload["gate_count"] == 13, (
        f"SMOKE-06 대표님: gate_count 는 13 (operational) 이어야 합니다 — "
        f"실제값 {payload['gate_count']}"
    )
    assert len(payload["gate_timestamps"]) >= 13, (
        f"SMOKE-06 대표님: gate_timestamps 는 ≥13 key 이어야 합니다 — "
        f"실제 {len(payload['gate_timestamps'])}"
    )


def test_smoke_e2e_fixture_has_final_video_id(fixtures_dir: Path) -> None:
    """Invariant 2 — final_video_id 는 non-empty 11-char YouTube video id."""
    payload = json.loads(
        (fixtures_dir / "sample_smoke_e2e.json").read_text(encoding="utf-8")
    )
    video_id = payload["final_video_id"]
    assert isinstance(video_id, str), (
        f"SMOKE-06 대표님: final_video_id 는 str 이어야 합니다 — "
        f"실제 type {type(video_id).__name__}"
    )
    assert len(video_id) > 0, (
        "SMOKE-06 대표님: final_video_id 가 비어있으면 안 됩니다 "
        "(cleanup 전 anchor 필수)"
    )
    # YouTube video_id 는 11 chars [A-Za-z0-9_-] 포맷.
    assert re.match(r"^[A-Za-z0-9_-]{11}$", video_id), (
        f"SMOKE-06 대표님: final_video_id 포맷 위반 — {video_id}"
    )


def test_smoke_e2e_fixture_under_budget_cap(fixtures_dir: Path) -> None:
    """Invariant 3/4 — total_cost_usd ≤ budget_cap_usd + cap=$5.00 lock."""
    payload = json.loads(
        (fixtures_dir / "sample_smoke_e2e.json").read_text(encoding="utf-8")
    )
    total_cost = payload["total_cost_usd"]
    cap_usd = payload["budget_cap_usd"]
    assert total_cost <= cap_usd, (
        f"SMOKE-05 대표님: 예산 초과 발생 — total=${total_cost:.2f} > "
        f"cap=${cap_usd:.2f}"
    )
    assert cap_usd == 5.00, (
        f"SMOKE-05 대표님: budget_cap_usd 는 Phase 13 SC#5 에 의해 $5.00 "
        f"하드 락 — 실제값 ${cap_usd:.2f}"
    )
    assert payload["budget_breached"] is False, (
        "SMOKE-05 대표님: budget_breached 는 False 이어야 Phase 13 완료 조건"
    )


def test_smoke_e2e_fixture_supervisor_rc1_zero(fixtures_dir: Path) -> None:
    """Invariant 5 — supervisor rc=1 재현 0회 (Phase 12 AGENT-STD-03 성과).

    Phase 11 deferred SC#1 ("프롬프트가 너무 깁니다") 가 Phase 12
    ``_compress_producer_output`` (27% ratio) 로 구조적 해소됨을 재확인 —
    live run 이 반드시 rc1_count==0 달성해야 SMOKE-02 완결.
    """
    payload = json.loads(
        (fixtures_dir / "sample_smoke_e2e.json").read_text(encoding="utf-8")
    )
    assert payload["supervisor_rc1_count"] == 0, (
        f"SMOKE-02 대표님: supervisor rc=1 재현 {payload['supervisor_rc1_count']}회 — "
        "Phase 12 AGENT-STD-03 compression 실패 가능성 (대표님 점검 필요)"
    )


def test_smoke_e2e_fixture_status_ok(fixtures_dir: Path) -> None:
    """Invariant 6 — status == "OK" + wall_time_seconds > 0 (실제 runtime)."""
    payload = json.loads(
        (fixtures_dir / "sample_smoke_e2e.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "OK", (
        f"SMOKE-06 대표님: status 는 'OK' 이어야 Phase 13 완료 조건 — "
        f"실제값 '{payload['status']}'"
    )
    assert payload["wall_time_seconds"] > 0, (
        f"SMOKE-06 대표님: wall_time_seconds 는 >0 이어야 합니다 "
        f"(live run 실제 수행 증거) — 실제값 {payload['wall_time_seconds']}"
    )


def test_smoke_e2e_evidence_dir_glob_pattern() -> None:
    """Invariant 7 — filename 계약: ``smoke_e2e_<YYYYMMDD>_<HHMMSS>.json``.

    Wave 4 runner (``phase13_live_smoke.py``) 가 반드시
    ``datetime.now().strftime("%Y%m%d_%H%M%S")`` 포맷 session_id 로 evidence
    파일명을 생성해야 함을 lock. Wave 5 Phase Gate 가 glob 으로 evidence 를
    수집할 때 본 계약을 전제.
    """
    pattern = re.compile(r"^smoke_e2e_\d{8}_\d{6}\.json$")
    # Valid examples
    assert pattern.match("smoke_e2e_20260421_223807.json") is not None, (
        "SMOKE-06 대표님: 기본 timestamp format 매칭 실패"
    )
    assert pattern.match("smoke_e2e_20260421_000000.json") is not None, (
        "SMOKE-06 대표님: 자정 timestamp format 매칭 실패"
    )
    # Invalid examples — 계약 위반 감지 확인.
    assert pattern.match("smoke_e2e_2026421_223807.json") is None, (
        "SMOKE-06 대표님: 8자리 미만 date 는 reject 해야 합니다"
    )
    assert pattern.match("smoke_e2e_20260421.json") is None, (
        "SMOKE-06 대표님: time suffix 없는 포맷 은 reject 해야 합니다"
    )
    assert pattern.match("smoke_e2e_sample.json") is None, (
        "SMOKE-06 대표님: 비-timestamp session_id 는 reject 해야 합니다"
    )
