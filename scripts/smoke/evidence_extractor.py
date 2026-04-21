"""Phase 13 Evidence Extractor — state/<sid>/gate_*.json → evidence JSON.

Wave 1/4 공용 유틸. Wave 4 Full E2E (phase13_live_smoke.py) 가 live run 종료
후 본 모듈을 호출하여 producer_output + supervisor_output aggregated evidence
JSON 2종을 ``.planning/phases/13-live-smoke/evidence/`` 에 anchor 한다.

Contract (Wave 2/4 가 의존)
---------------------------
- ``extract_producer_output(session_id)`` → producer_output 집계 JSON Path
    반환 (shape: session_id / timestamp / producer_gates / gate_count_with_producer)
- ``extract_supervisor_output(session_id)`` → supervisor rc=1 재현 0회 증거 JSON
    Path 반환 (shape: session_id / timestamp / supervisor_calls / rc1_count /
    compression_ratio_avg)
- ``OPERATIONAL_GATES`` — 13 operational gate 리스트 (IDLE/COMPLETE 제외).
    phase11_full_run.py ``_OPERATIONAL_GATES`` + CLAUDE.md §Pipeline 과 1:1.
- ``rc1_count(log)`` — Phase 11 SC#1 empirical 검증 helper. supervisor log
    문자열에서 "프롬프트가 너무 깁니다" 재현 횟수 count.

Design (CLAUDE.md 금기 #2/#3 준수)
--------------------------------
- 손상된 checkpoint 파일 발견 시 ``logger.warning`` 로 명시 기록 후 해당
    gate 만 skip — 전체 evidence 생성은 진행 (graceful degradation).
  try/except 침묵 폴백은 없음.
- 미완성 wiring 표식 (금기 #2) 없음. 모든 branch 는 완성된 행동을 수행
    — 빈 입력은 logger.info 로 기록 후 empty evidence 로 graceful return.
- Pitfall 6 (CWD): evidence_dir 은 ``mkdir(parents=True, exist_ok=True)``
    으로 idempotent 생성.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from statistics import mean

logger = logging.getLogger("smoke.evidence_extractor")

# =============================================================================
# Public contract constants
# =============================================================================

# 13 operational gates — IDLE + COMPLETE 는 checkpoint 생성 대상 아님.
# CLAUDE.md §Pipeline (L19) 과 gate_guard._OPERATIONAL_GATES 와 동기화.
OPERATIONAL_GATES: list[str] = [
    "TREND",
    "NICHE",
    "RESEARCH_NLM",
    "BLUEPRINT",
    "SCRIPT",
    "POLISH",
    "VOICE",
    "ASSETS",
    "ASSEMBLY",
    "THUMBNAIL",
    "METADATA",
    "UPLOAD",
    "MONITOR",
]

# Default evidence directory — Phase 13 anchor root.
# tests/phase13/ 테스트는 ``tmp_evidence_dir`` fixture 로 override.
_DEFAULT_EVIDENCE_DIR = Path(".planning/phases/13-live-smoke/evidence")


# =============================================================================
# Internal helpers (금기 #3 — 침묵 폴백 없이 logger.warning + empty default)
# =============================================================================


def _iter_gate_files(session_id: str, state_root: Path) -> list[Path]:
    """Return sorted ``state/<sid>/gate_*.json`` paths; ``[]`` if missing dir.

    session_dir 부재는 정상적 "not-yet-run" 상태 — logger.info 로만 기록하고
    빈 리스트 반환. 금기 #3: 예외를 집어삼키지 않으며, 디렉토리 부재는
    정상 제어 흐름이므로 raise 대상이 아님.
    """
    session_dir = state_root / session_id
    if not session_dir.exists():
        logger.info(
            "[evidence] session_dir 부재 — extraction skipped: %s (대표님)",
            session_dir,
        )
        return []
    return sorted(session_dir.glob("gate_*.json"))


def _load_gate(path: Path) -> dict:
    """Load a single gate checkpoint JSON; return ``{}`` on corruption.

    손상/권한 실패 시 logger.warning 로 명시 기록 — 전체 evidence 생성을 막지
    않음 (graceful degradation). CLAUDE.md 금기 #3 준수 — silent fallback 이
    아니며 WARNING 레벨로 audit-trail 보존.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        logger.warning(
            "[evidence] gate checkpoint 로드 실패 %s (대표님): %s",
            path,
            err,
        )
        return {}


# =============================================================================
# Public API
# =============================================================================


def extract_producer_output(
    session_id: str,
    state_root: Path = Path("state"),
    evidence_dir: Path = _DEFAULT_EVIDENCE_DIR,
) -> Path:
    """Aggregate producer_output across 13 operational gates → evidence JSON.

    각 ``state/<sid>/gate_NN.json`` 의 ``artifacts.producer_output`` (Wave 4
    live run 이 richer artifacts 를 기록할 때 자동으로 collect 됨) 을 수집.
    OPERATIONAL_GATES 외 gate 는 skip.

    Args:
        session_id: Pipeline session identifier (예: ``"20260421_034724"``).
        state_root: checkpointer root. 기본 ``Path("state")`` — CWD 기준.
        evidence_dir: 출력 anchor 디렉토리. 기본 Phase 13 evidence 경로.

    Returns:
        작성된 evidence JSON 의 :class:`pathlib.Path`. 파일명은
        ``producer_output_<session_id>.json``.
    """
    producer_gates: dict[str, dict] = {}
    for gate_file in _iter_gate_files(session_id, state_root):
        payload = _load_gate(gate_file)
        if not payload:
            continue
        gate_name = payload.get("gate")
        if gate_name not in OPERATIONAL_GATES:
            continue
        artifacts = payload.get("artifacts", {})
        if not isinstance(artifacts, dict):
            continue
        producer_output = artifacts.get("producer_output")
        if producer_output is None:
            # 해당 gate 는 producer_output 을 artifacts 에 기록하지 않음 —
            # path/sha256 만 있는 경우가 정상 (gate_guard.dispatch L149-155).
            continue
        producer_gates[gate_name] = producer_output

    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_path = evidence_dir / f"producer_output_{session_id}.json"
    payload = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "producer_gates": producer_gates,
        "gate_count_with_producer": len(producer_gates),
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "[evidence] producer_output 집계 → %s (gates=%d)",
        out_path,
        len(producer_gates),
    )
    return out_path


def extract_supervisor_output(
    session_id: str,
    state_root: Path = Path("state"),
    evidence_dir: Path = _DEFAULT_EVIDENCE_DIR,
) -> Path:
    """Aggregate supervisor compression metrics → evidence JSON.

    Phase 12 AGENT-STD-03 ``_compress_producer_output`` 가 적용된 상태에서
    Phase 11 deferred SC#1 ("프롬프트가 너무 깁니다" rc=1) 재현 0회 를 증명
    하기 위한 evidence. checkpointer artifacts 의 ``supervisor`` sub-dict
    (``{pre_compress_bytes, post_compress_bytes, returncode, inspector_count,
    verdict}``) 를 순회하여 rc1_count + compression_ratio_avg 계산.

    Returns:
        작성된 evidence JSON Path. 파일명은
        ``supervisor_output_<session_id>.json``.
    """
    supervisor_calls: list[dict] = []
    for gate_file in _iter_gate_files(session_id, state_root):
        payload = _load_gate(gate_file)
        if not payload:
            continue
        gate_name = payload.get("gate")
        if gate_name not in OPERATIONAL_GATES:
            continue
        artifacts = payload.get("artifacts", {})
        if not isinstance(artifacts, dict):
            continue
        supervisor = artifacts.get("supervisor")
        if not isinstance(supervisor, dict):
            continue

        pre = int(supervisor.get("pre_compress_bytes", 0))
        post = int(supervisor.get("post_compress_bytes", 0))
        ratio = round(post / pre, 4) if pre > 0 else 0.0
        call_entry = {
            "gate": gate_name,
            "inspector_count": int(supervisor.get("inspector_count", 0)),
            "pre_compress_bytes": pre,
            "post_compress_bytes": post,
            "ratio": ratio,
            "returncode": int(supervisor.get("returncode", 0)),
            "verdict": supervisor.get("verdict", ""),
        }
        supervisor_calls.append(call_entry)

    rc1_count_val = sum(1 for c in supervisor_calls if c["returncode"] == 1)
    ratios = [c["ratio"] for c in supervisor_calls if c["pre_compress_bytes"] > 0]
    compression_ratio_avg = round(mean(ratios), 4) if ratios else 0.0

    evidence_dir.mkdir(parents=True, exist_ok=True)
    out_path = evidence_dir / f"supervisor_output_{session_id}.json"
    payload = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "supervisor_calls": supervisor_calls,
        "rc1_count": rc1_count_val,
        "compression_ratio_avg": compression_ratio_avg,
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "[evidence] supervisor_output 집계 → %s (calls=%d, rc1=%d, avg_ratio=%.4f)",
        out_path,
        len(supervisor_calls),
        rc1_count_val,
        compression_ratio_avg,
    )
    return out_path


def rc1_count(log: str) -> int:
    """Count Phase 11 "프롬프트가 너무 깁니다" reproductions in a log string.

    Phase 12 ``_compress_producer_output`` 적용 후 Wave 1/4 supervisor live
    run 이 rc=1 재현 0회 를 달성함을 empirical 로 증명할 때 사용. 단순
    substring occurrence count — locale 의존성 없음.

    Args:
        log: 대상 로그 문자열 (supervisor stdout/stderr 통합).

    Returns:
        "프롬프트가 너무 깁니다" 문구의 non-overlapping 출현 횟수.
    """
    if not log:
        return 0
    return log.count("프롬프트가 너무 깁니다")
