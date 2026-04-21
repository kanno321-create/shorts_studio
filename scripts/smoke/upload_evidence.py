"""Phase 13 Upload Evidence — SMOKE-04 videos.list readback + production_metadata regex + evidence anchor.

Wave 2/4 공용 유틸 대표님. 금기 #5 Selenium 금지 준수 —
``googleapiclient.discovery.build('youtube', 'v3').videos().list`` 공식 경로만 호출.

계약
====
- :data:`PRODUCTION_METADATA_REGEX` 는 Phase 8 PUB-04 D-08 inject_into_description 포맷
  (``"\\n<!-- production_metadata\\n" + compact_json + "\\n-->"``) 와 정확 일치.
  ``re.DOTALL`` flag 필수 — description_raw 의 ``\\n`` 경유 JSON 본문 매칭.
- :data:`REQUIRED_METADATA_FIELDS` 는 production_metadata.py 의 TypedDict
  (``script_seed``, ``assets_origin``, ``pipeline_version``, ``checksum``) 순서를 승계 —
  D-08 계약. 개수는 정확히 4.
- :func:`anchor_upload_evidence` 는 ``videos.list(part='snippet,status', id=video_id)``
  를 호출 후 description readback → regex parse → 4 필드 presence 확인 →
  evidence JSON (5 key) write → 반환. Caller 가
  ``evidence["required_fields_present"]`` 에 기반하여 assertion 수행.

SSOT 금기 #2: 미완성 wiring 표식 (T**O**D**O**) 없음 — 모든 branch 완성.
금기 #3: 침묵 폴백 없음 — videos.list empty → RuntimeError 명시적 raise,
JSONDecodeError → logger.warning + empty dict (계약된 graceful default).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Phase 8 PUB-04 D-08 포맷 규약 — re.DOTALL 필수 (multi-line JSON payload).
PRODUCTION_METADATA_REGEX = re.compile(
    r"<!-- production_metadata\n(\{.*?\})\n-->",
    re.DOTALL,
)

# D-08 TypedDict 순서 그대로 — 변경 시 production_metadata.py 동반 수정 필요.
REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
    "script_seed",
    "assets_origin",
    "pipeline_version",
    "checksum",
)


def _parse_production_metadata(description_raw: str) -> dict[str, Any]:
    """description 에서 production_metadata HTML comment JSON 추출.

    Parameters
    ----------
    description_raw
        YouTube videos.list 의 ``items[0].snippet.description`` 원문.

    Returns
    -------
    dict
        HTML comment 부재 → ``{}`` (caller 가 required_fields_present 로 판정).
        JSON decode 실패 → logger.warning + ``{}``.
    """
    match = PRODUCTION_METADATA_REGEX.search(description_raw)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        # 금기 #3 준수 — 침묵 아님, 명시적 WARNING + 계약된 empty default.
        logger.warning(
            "[upload_evidence] production_metadata JSON decode 실패 대표님: %s",
            exc,
        )
        return {}


def anchor_upload_evidence(
    youtube,
    video_id: str,
    session_id: str,
    evidence_dir: Path = Path(".planning/phases/13-live-smoke/evidence"),
) -> dict[str, Any]:
    """YouTube videos.list readback + production_metadata regex parse + evidence anchor.

    Parameters
    ----------
    youtube
        ``googleapiclient.discovery.build('youtube', 'v3', credentials=...)`` 결과
        (또는 동일 contract 를 만족하는 MockYouTube). 금기 #5: Selenium 금지 —
        본 함수는 오직 googleapiclient 공식 경로만 호출.
    video_id
        videos.insert 가 반환한 YouTube video id.
    session_id
        smoke 세션 식별자 (timestamp 포맷 권장, 예: ``"20260421_153000"``).
    evidence_dir
        evidence JSON 저장 경로. 기본값은 Phase 13 정식 디렉토리,
        테스트에서는 ``tmp_evidence_dir`` fixture 경유 tmp 경로 주입.

    Returns
    -------
    dict
        5 key evidence payload (+ diagnostic ``missing_fields``):
        ``session_id``, ``video_id``, ``description_raw``,
        ``production_metadata``, ``required_fields_present``.

    Raises
    ------
    RuntimeError
        ``videos.list`` 가 빈 items 를 반환하면 — 업로드 실패 혹은 이미 삭제됨.

    Notes
    -----
    caller 가 ``evidence["required_fields_present"]`` 를 assertion 해야 4 필드
    readback 성공을 보장. 본 함수 내부는 warning 만 기록 (graceful degradation).
    """
    resp = youtube.videos().list(part="snippet,status", id=video_id).execute()
    items = resp.get("items") or []
    if not items:
        raise RuntimeError(
            f"videos.list returned empty for {video_id} 대표님 — "
            "업로드 실패 혹은 이미 삭제된 video_id 입니다."
        )

    description_raw = items[0].get("snippet", {}).get("description", "")
    metadata = _parse_production_metadata(description_raw)
    missing = [f for f in REQUIRED_METADATA_FIELDS if not metadata.get(f)]
    required_fields_present = len(missing) == 0

    evidence: dict[str, Any] = {
        "session_id": session_id,
        "video_id": video_id,
        "description_raw": description_raw,
        "production_metadata": metadata,
        "required_fields_present": required_fields_present,
        "missing_fields": missing,
        "readback_timestamp": datetime.now().isoformat(),
    }

    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"smoke_upload_{session_id}.json"
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "[upload_evidence] smoke_upload → %s (missing=%s, 대표님)",
        evidence_path,
        missing,
    )
    return evidence


__all__ = [
    "PRODUCTION_METADATA_REGEX",
    "REQUIRED_METADATA_FIELDS",
    "anchor_upload_evidence",
]
