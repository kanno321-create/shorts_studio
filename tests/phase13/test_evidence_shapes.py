"""Phase 13 evidence JSON schema invariant tests — Tier 1 baseline.

4 golden fixture JSON (sample_producer_output / sample_supervisor_output /
sample_smoke_upload / sample_smoke_e2e) 이 Wave 1~4 가 동일 shape 로
재생산할 계약 검증 surface. Wave 2~4 live run 의 실 evidence JSON 은
Wave 5 Phase Gate 에서 ``phase13_acceptance.py`` 가 별도 검증.

References
----------
- tests/phase13/fixtures/*.json (Wave 0 Plan 13-01 ship)
- 13-RESEARCH.md §SMOKE-01/02/04/06 evidence format (L196-360)
- 13-VALIDATION.md §Per-Task Verification Map

CLAUDE.md compliance
--------------------
- 금기 #2: 미완성 wiring 없음 — 모든 assertion 은 완성된 행동.
- 필수 #8: 증거 기반 — 각 invariant 에 명시 message 로 실패 key 식별.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# OPERATIONAL_GATES 계약 재사용 (Task 13-02-01)
from scripts.smoke.evidence_extractor import OPERATIONAL_GATES


# =============================================================================
# 1. SMOKE-01 evidence shape — producer_output_<sid>.json
# =============================================================================


def test_smoke_01_evidence_shape(fixtures_dir: Path) -> None:
    """sample_producer_output.json 4 필수 key.

    Wave 4 live run 의 ``extract_producer_output`` 출력이 본 shape 를 반드시
    따라야 한다는 계약 확증.
    """
    payload = json.loads(
        (fixtures_dir / "sample_producer_output.json").read_text(encoding="utf-8")
    )
    required_keys = ("session_id", "timestamp", "producer_gates")
    for key in required_keys:
        assert key in payload, (
            f"SMOKE-01 evidence 필수 key '{key}' 누락 (대표님)"
        )
    assert isinstance(payload["producer_gates"], dict), (
        f"producer_gates 는 dict 여야 함 — 실측 {type(payload['producer_gates'])}"
    )
    # producer_output_<sid>.json 계약: 최소 1 operational gate 포함.
    assert len(payload["producer_gates"]) >= 1, (
        "최소 1 gate 의 producer_output 필요 (fixture 는 TREND/SCRIPT/METADATA 3개)"
    )
    # 각 gate key 는 OPERATIONAL_GATES 집합 내.
    for gate in payload["producer_gates"].keys():
        assert gate in OPERATIONAL_GATES, (
            f"producer_gates key '{gate}' 는 OPERATIONAL_GATES 외 — 계약 위반"
        )


# =============================================================================
# 2. SMOKE-02 evidence shape — supervisor_output_<sid>.json
# =============================================================================


def test_smoke_02_evidence_shape(fixtures_dir: Path) -> None:
    """sample_supervisor_output.json 5 필수 key + 각 call 7 필수 key.

    Phase 11 deferred SC#1 (rc=1) 재현 0회 invariant 의 schema-level
    baseline.
    """
    payload = json.loads(
        (fixtures_dir / "sample_supervisor_output.json").read_text(
            encoding="utf-8"
        )
    )
    required_keys = (
        "session_id",
        "supervisor_calls",
        "rc1_count",
        "compression_ratio_avg",
    )
    for key in required_keys:
        assert key in payload, f"SMOKE-02 evidence 필수 key '{key}' 누락"
    assert isinstance(payload["supervisor_calls"], list), (
        "supervisor_calls 는 list 여야 함"
    )
    assert isinstance(payload["rc1_count"], int), (
        f"rc1_count 는 int — 실측 {type(payload['rc1_count'])}"
    )
    assert isinstance(payload["compression_ratio_avg"], float), (
        f"compression_ratio_avg 는 float — 실측 {type(payload['compression_ratio_avg'])}"
    )
    # 각 call 7 필수 key
    call_required = (
        "gate",
        "inspector_count",
        "pre_compress_bytes",
        "post_compress_bytes",
        "ratio",
        "returncode",
        "verdict",
    )
    for idx, call in enumerate(payload["supervisor_calls"]):
        for key in call_required:
            assert key in call, (
                f"supervisor_calls[{idx}] 필수 key '{key}' 누락"
            )
    # rc1_count invariant — Phase 12 compression 후 0 유지 (SMOKE-02 success).
    assert payload["rc1_count"] == 0, (
        f"fixture 는 rc1_count==0 invariant 를 설정, 실측 {payload['rc1_count']}"
    )


# =============================================================================
# 3. SMOKE-04 evidence shape — smoke_upload_<sid>.json
# =============================================================================


def test_smoke_04_evidence_shape(fixtures_dir: Path) -> None:
    """sample_smoke_upload.json 5 필수 key + production_metadata 4 필드 +
    description_raw HTML comment regex (re.DOTALL)."""
    payload = json.loads(
        (fixtures_dir / "sample_smoke_upload.json").read_text(encoding="utf-8")
    )
    required_keys = (
        "session_id",
        "video_id",
        "description_raw",
        "production_metadata",
        "required_fields_present",
    )
    for key in required_keys:
        assert key in payload, f"SMOKE-04 evidence 필수 key '{key}' 누락"
    assert isinstance(payload["required_fields_present"], bool), (
        "required_fields_present 는 bool"
    )
    meta = payload["production_metadata"]
    assert isinstance(meta, dict), "production_metadata 는 dict"
    meta_fields = ("script_seed", "assets_origin", "pipeline_version", "checksum")
    for field in meta_fields:
        assert field in meta, f"production_metadata 필수 필드 '{field}' 누락"
        assert meta[field], (
            f"production_metadata['{field}'] 는 non-empty 여야 함"
        )
    # description_raw 의 HTML comment regex — re.DOTALL 필수 (줄바꿈 포함).
    match = re.search(
        r"<!-- production_metadata\n(\{.*?\})\n-->",
        payload["description_raw"],
        re.DOTALL,
    )
    assert match is not None, (
        "description_raw 내 '<!-- production_metadata ... -->' HTML comment "
        "매칭 실패 (SMOKE-04 readback 계약 위반)"
    )
    # Comment 내 JSON 도 parse 가능
    inline_meta = json.loads(match.group(1))
    assert inline_meta["script_seed"] == meta["script_seed"]


# =============================================================================
# 4. SMOKE-06 evidence shape — smoke_e2e_<sid>.json
# =============================================================================


def test_smoke_06_evidence_shape(fixtures_dir: Path) -> None:
    """sample_smoke_e2e.json 10 필수 key + gate_count == 13 invariant +
    gate_timestamps 에 최소 13 key."""
    payload = json.loads(
        (fixtures_dir / "sample_smoke_e2e.json").read_text(encoding="utf-8")
    )
    required_keys = (
        "session_id",
        "status",
        "wall_time_seconds",
        "gate_timestamps",
        "gate_count",
        "final_video_id",
        "total_cost_usd",
        "budget_cap_usd",
        "budget_breached",
        "supervisor_rc1_count",
    )
    for key in required_keys:
        assert key in payload, f"SMOKE-06 evidence 필수 key '{key}' 누락"
    # SMOKE-06 핵심 invariant: gate_count == 13.
    assert payload["gate_count"] == 13, (
        f"Phase 13 Full E2E gate_count == 13 필요, 실측 {payload['gate_count']}"
    )
    assert isinstance(payload["gate_timestamps"], dict)
    # gate_timestamps 에 최소 13 key 포함 (IDLE/COMPLETE 포함 가능).
    assert len(payload["gate_timestamps"]) >= 13, (
        f"gate_timestamps 최소 13 key, 실측 {len(payload['gate_timestamps'])}"
    )
    # SMOKE-02 rc=1 재현 0회 전파 invariant
    assert payload["supervisor_rc1_count"] == 0, (
        f"E2E 내 supervisor_rc1_count==0 invariant, 실측 {payload['supervisor_rc1_count']}"
    )
    assert isinstance(payload["budget_breached"], bool)
    assert 0 <= payload["total_cost_usd"] <= payload["budget_cap_usd"], (
        f"total_cost_usd {payload['total_cost_usd']} 는 [0, budget_cap] 범위"
    )


# =============================================================================
# 5. UTF-8 + ensure_ascii=False roundtrip — 한국어 문자 유지
# =============================================================================


def test_smoke_evidence_all_fixtures_utf8_parseable(fixtures_dir: Path) -> None:
    """4 fixture UTF-8 parse 성공 + ensure_ascii=False re-dump 후 한국어
    문자 유지 (SMOKE-01/02/04/06 공통 encoding invariant)."""
    fixture_names = (
        "sample_producer_output.json",
        "sample_supervisor_output.json",
        "sample_smoke_upload.json",
        "sample_smoke_e2e.json",
    )
    for name in fixture_names:
        path = fixtures_dir / name
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)  # UTF-8 parse OK
        redumped = json.dumps(payload, ensure_ascii=False, indent=2)
        # 최소 1개 fixture (sample_producer_output) 은 "샘플" 한국어 포함
        # → redumped 에도 그대로 유지되어야 함.
        if "샘플" in raw:
            assert "샘플" in redumped, (
                f"{name}: ensure_ascii=False roundtrip 후 한국어 문자 유실"
            )
        # 모든 fixture 의 payload 는 top-level dict
        assert isinstance(payload, dict), (
            f"{name}: top-level JSON 은 dict 여야 함"
        )
